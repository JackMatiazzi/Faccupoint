import asyncio
import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "frontend"))
import flet as ft
from aluno.telas import questao


def _encontrar_botao(controle, texto):
    # Procura por texto em vez de indice fixo: fix/video-continuo-aluno (outra
    # branch, independente) reestrutura a arvore de widgets desta mesma tela;
    # navegar por posicao quebraria a cada reconciliacao de merge sem precisar.
    if isinstance(controle, ft.ElevatedButton) and controle.text == texto:
        return controle
    for atributo in ("controls", "content"):
        valor = getattr(controle, atributo, None)
        if valor is None:
            continue
        alvo = valor if isinstance(valor, (list, tuple)) else [valor]
        for filho in alvo:
            achado = _encontrar_botao(filho, texto)
            if achado is not None:
                return achado
    return None


class NumeroAposTrocarPerguntaTest(unittest.TestCase):
    def test_cliente_envia_numero_da_pergunta_atual_apos_trocar_de_pergunta(self):
        # Regressao: uma "numero" travada no valor da primeira pergunta
        # renderizada derrotaria a propria protecao que fix/protocolo-
        # respostas-compat adiciona no backend (numero != questao_atual + 1).
        async def cenario():
            tasks = []
            page = SimpleNamespace(
                _mensagem_questao={
                    "numero": 1, "total": 3, "tempo": 20,
                    "enunciado": "Primeira", "alternativas": ["A", "B"],
                },
                _ws_queue=asyncio.Queue(), _ws_aluno=AsyncMock(), views=[],
                run_task=lambda fn, *args: tasks.append((fn, args)),
            )
            page.update = lambda: None
            page.views.append(questao.tela_questao(page))

            consumer = next(fn for fn, args in tasks if fn.__name__ == "aguardar_resultado")
            running = asyncio.create_task(consumer())
            await page._ws_queue.put({
                "tipo": "questao", "numero": 2, "total": 3, "tempo": 20,
                "enunciado": "Segunda", "alternativas": ["C", "D"],
            })
            await asyncio.sleep(0)
            # Nao afirma que a tarefa terminou aqui: nesta branch isolada, uma
            # nova "questao" recria a view e retorna; com fix/video-continuo-
            # aluno tambem integrada, a mesma tarefa continua viva atualizando
            # a view no lugar. O que importa pro protocolo e so o payload
            # enviado, nao qual das duas estrategias de render esta ativa.
            try:
                botao_d = _encontrar_botao(page.views[-1], "D")
                self.assertIsNotNone(botao_d, "botao da alternativa 'D' nao encontrado na view renderizada")
                botao_d.on_click(None)

                enviar, args = tasks[-1]
                await enviar(*args)
                payload = json.loads(page._ws_aluno.send.call_args.args[0])
                self.assertEqual(payload, {"tipo": "resposta", "indice": 1, "numero": 2})
            finally:
                if not running.done():
                    running.cancel()
                    with self.assertRaises(asyncio.CancelledError):
                        await running

        asyncio.run(cenario())


if __name__ == "__main__":
    unittest.main()
