import asyncio
import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "frontend"))
import flet as ft
from aluno.telas import questao


class VideoContinuoTest(unittest.TestCase):
    def test_video_nunca_aparece_pro_aluno_e_atualiza_resposta_da_questao(self):
        async def scenario():
            tasks = []
            page = SimpleNamespace(
                _mensagem_questao={"numero": 1, "total": 3, "tempo": 30,
                    "enunciado": "Primeira", "alternativas": ["A", "B"],
                    "link_midia": "https://youtu.be/abcdefghijk"},
                _ws_queue=asyncio.Queue(), _ws_aluno=AsyncMock(), views=[],
                run_task=lambda fn, *args: tasks.append((fn, args)),
            )
            page.update = lambda: None
            with patch.object(questao.ft, "WebView", side_effect=lambda **kw: ft.Container(data=kw["url"])) as player:
                view = questao.tela_questao(page)
                page.views.append(view)
                content = view.controls[0].controls[3].content
                media = content.controls[2]
                # Video nunca aparece pro aluno: sem WebView, sem aviso, container escondido.
                self.assertIsNone(media.content)
                self.assertFalse(media.visible)
                consumer = next(fn for fn, args in tasks if fn.__name__ == "aguardar_resultado")
                running = asyncio.create_task(consumer())
                await page._ws_queue.put({"tipo": "questao", "numero": 2, "total": 3,
                    "tempo": 20, "enunciado": "Segunda", "alternativas": ["C", "D", "E"],
                    "link_midia": "https://www.youtube.com/watch?v=abcdefghijk"})
                await asyncio.sleep(0)
                self.assertIs(page.views[0], view)
                self.assertIsNone(media.content)
                self.assertFalse(media.visible)
                self.assertEqual(player.call_count, 0)
                self.assertEqual(content.controls[0].content.value, "Segunda")
                self.assertEqual(len(content.controls[3].controls), 3)
                content.controls[3].controls[1].on_click(None)
                send, args = tasks[-1]
                await send(*args)
                # So confere tipo/indice: fix/protocolo-respostas-compat acrescenta
                # "numero" ao mesmo payload quando mergeada junto (conflito de merge
                # ja esperado nesse arquivo); essa branch isolada nao trata de numero.
                payload = json.loads(page._ws_aluno.send.call_args.args[0])
                self.assertEqual(payload["tipo"], "resposta")
                self.assertEqual(payload["indice"], 1)
                await page._ws_queue.put({"tipo": "questao", "numero": 3, "total": 3,
                    "tempo": 15, "enunciado": "Terceira", "alternativas": ["F", "G"],
                    "link_midia": "https://youtu.be/lmnopqrstuv"})
                await asyncio.sleep(0)
                self.assertIsNone(media.content)
                self.assertFalse(media.visible)
                self.assertEqual(player.call_count, 0)
                self.assertFalse(content.controls[3].controls[0].disabled)
                with patch.object(questao, "ir_para") as navigate:
                    await page._ws_queue.put({"tipo": "fim", "placar": []})
                    await running
                    navigate.assert_called_once_with(page, "/placar")
                self.assertIsNone(media.content)
        asyncio.run(scenario())


if __name__ == "__main__":
    unittest.main()
