import asyncio
import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "frontend"))
from aluno.telas import questao


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
            self.assertTrue(running.done())

            nova_view = page.views[-1]
            botoes = nova_view.controls[0].controls[3].content.controls
            botao_indice_1 = botoes[3]
            botao_indice_1.on_click(None)

            enviar, args = tasks[-1]
            await enviar(*args)
            payload = json.loads(page._ws_aluno.send.call_args.args[0])
            self.assertEqual(payload, {"tipo": "resposta", "indice": 1, "numero": 2})

        asyncio.run(cenario())


if __name__ == "__main__":
    unittest.main()
