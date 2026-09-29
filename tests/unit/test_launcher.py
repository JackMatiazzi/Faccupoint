import os
import sys
import unittest
from contextlib import ExitStack
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock, patch

import launcher


class LauncherTest(unittest.TestCase):
    def test_professor_e_processos_recebem_a_mesma_api(self):
        for empacotado in (False, True):
            for configurada in (None, "http://127.0.0.1:8000", "https://api.example.com"):
                with self.subTest(empacotado=empacotado, api=configurada):
                    esperada = configurada or "https://faccupoint-backend.onrender.com"
                    processos = []
                    professor = []

                    def iniciar(comando, **kwargs):
                        processos.append((comando, kwargs.get("env", os.environ).get("API_URL")))
                        return Mock()

                    ft = ModuleType("flet")
                    ft.AppView = SimpleNamespace(FLET_APP="desktop")
                    ft.app = lambda **kwargs: professor.append(os.environ.get("API_URL"))
                    tela = ModuleType("professor.main")
                    tela.main = Mock()
                    janela = ModuleType("professor.janela")
                    janela.abrir_janela = lambda target: professor.append(os.environ.get("API_URL"))

                    with ExitStack() as stack:
                        stack.enter_context(patch.dict(os.environ))
                        os.environ.pop("API_URL", None)
                        if configurada is not None:
                            os.environ["API_URL"] = configurada
                        stack.enter_context(patch.object(launcher, "_FROZEN", empacotado))
                        stack.enter_context(patch.object(sys, "argv", ["launcher.py"]))
                        stack.enter_context(patch.object(sys, "path", sys.path.copy()))
                        stack.enter_context(patch.dict(sys.modules, {"flet": ft, "professor.main": tela, "professor.janela": janela}))
                        for nome in ("_matar_flet_clientes", "_matar_porta", "_matar", "_aguardar_backend", "_iniciar_keepalive"):
                            stack.enter_context(patch.object(launcher, nome))
                        stack.enter_context(patch.object(launcher, "_verificar_atualizacao", return_value=False))
                        stack.enter_context(patch.object(launcher.os, "chdir"))
                        stack.enter_context(patch("builtins.print"))
                        stack.enter_context(patch.object(launcher.subprocess, "Popen", side_effect=iniciar))
                        launcher.main()

                    local = configurada == "http://127.0.0.1:8000"
                    self.assertEqual(len(processos), 2 if local else 1)
                    self.assertIn("--run-aluno" if empacotado else "aluno.main", processos[-1][0])
                    self.assertEqual([api for _, api in processos], [esperada] * len(processos))
                    self.assertEqual(professor, [esperada])


if __name__ == "__main__":
    unittest.main()
