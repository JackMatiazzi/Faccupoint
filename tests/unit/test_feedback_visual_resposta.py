import asyncio
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "frontend"))
import flet as ft
from aluno.telas import questao
from compartilhado.sistema_design.tokens import TEXT_DANGER, TEXT_SUCCESS


def _encontrar_botoes(controle, encontrados=None):
    if encontrados is None:
        encontrados = []
    if isinstance(controle, ft.ElevatedButton) and controle.text in ("A", "B", "C"):
        encontrados.append(controle)
        return encontrados
    for atributo in ("controls", "content"):
        valor = getattr(controle, atributo, None)
        if valor is None:
            continue
        alvo = valor if isinstance(valor, (list, tuple)) else [valor]
        for filho in alvo:
            _encontrar_botoes(filho, encontrados)
    return encontrados


def _cor_da_borda(botao):
    style = botao.style
    if style is None or not style.side:
        return None
    borda = style.side.get(ft.ControlState.DISABLED)
    return borda.color if borda else None


class FeedbackVisualRespostaTest(unittest.TestCase):
    def _preparar(self):
        page = SimpleNamespace(
            _mensagem_questao={
                "numero": 1, "total": 1, "tempo": 20,
                "enunciado": "Pergunta", "alternativas": ["A", "B", "C"],
            },
            _ws_queue=asyncio.Queue(), _ws_aluno=AsyncMock(), views=[],
            run_task=lambda fn, *args: self._tasks.append((fn, args)),
        )
        page.update = lambda: None
        page.views.append(questao.tela_questao(page))
        return page

    def setUp(self):
        self._tasks = []

    def test_selecionar_alternativa_destaca_ela_e_esmaece_as_outras(self):
        page = self._preparar()
        botoes = _encontrar_botoes(page.views[-1])
        self.assertEqual(len(botoes), 3)

        botoes[1].on_click(None)

        self.assertEqual(botoes[0].opacity, 0.35)
        self.assertEqual(botoes[1].opacity, 1.0)
        self.assertEqual(botoes[2].opacity, 0.35)
        self.assertTrue(all(b.disabled for b in botoes))

    def test_resultado_marca_borda_verde_na_correta_e_vermelha_na_errada(self):
        async def cenario():
            page = self._preparar()
            botoes = _encontrar_botoes(page.views[-1])
            botoes[0].on_click(None)

            consumer = next(fn for fn, args in self._tasks if fn.__name__ == "aguardar_resultado")
            running = asyncio.create_task(consumer())
            await page._ws_queue.put({"tipo": "resultado", "indices_corretos": [2], "acertou": False})
            await asyncio.sleep(0)

            self.assertEqual(_cor_da_borda(botoes[0]), TEXT_DANGER)
            self.assertEqual(_cor_da_borda(botoes[2]), TEXT_SUCCESS)
            self.assertIsNone(_cor_da_borda(botoes[1]))
            self.assertTrue(all(b.opacity == 1.0 for b in botoes))

            running.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await running

        asyncio.run(cenario())

    def test_resultado_quando_acertou_so_marca_borda_verde(self):
        async def cenario():
            page = self._preparar()
            botoes = _encontrar_botoes(page.views[-1])
            botoes[2].on_click(None)

            consumer = next(fn for fn, args in self._tasks if fn.__name__ == "aguardar_resultado")
            running = asyncio.create_task(consumer())
            await page._ws_queue.put({"tipo": "resultado", "indices_corretos": [2], "acertou": True})
            await asyncio.sleep(0)

            self.assertEqual(_cor_da_borda(botoes[2]), TEXT_SUCCESS)
            self.assertIsNone(_cor_da_borda(botoes[0]))
            self.assertIsNone(_cor_da_borda(botoes[1]))

            running.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await running

        asyncio.run(cenario())

    def test_tempo_esgotado_sem_resposta_marca_so_a_correta(self):
        async def cenario():
            page = self._preparar()
            botoes = _encontrar_botoes(page.views[-1])

            consumer = next(fn for fn, args in self._tasks if fn.__name__ == "aguardar_resultado")
            running = asyncio.create_task(consumer())
            await page._ws_queue.put({"tipo": "resultado", "indices_corretos": [1], "acertou": False})
            await asyncio.sleep(0)

            self.assertEqual(_cor_da_borda(botoes[1]), TEXT_SUCCESS)
            self.assertIsNone(_cor_da_borda(botoes[0]))
            self.assertIsNone(_cor_da_borda(botoes[2]))

            running.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await running

        asyncio.run(cenario())


if __name__ == "__main__":
    unittest.main()
