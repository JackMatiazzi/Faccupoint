import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "frontend"))

from compartilhado.conexao_api import backend_confiavel, websocket_aluno


class AmbienteSalaIsoladoTest(unittest.TestCase):
    def test_aluno_conecta_no_endereco_interno_do_compose(self):
        # packaging/sala/compose.yaml define API_URL=http://backend:8000 pro
        # servico do aluno (nome de servico Docker, nao localhost). Isso so
        # funciona porque entrar.py/lobby.py dependem de conexao_api.py
        # (fix/conexao-alunos) em vez do cliente antigo, que ignorava a
        # variavel de ambiente e derivava o destino do hostname da pagina.
        with patch.dict(os.environ, {"API_URL": "http://backend:8000"}):
            self.assertEqual(backend_confiavel(), "http://backend:8000")
            self.assertEqual(websocket_aluno("ABC234"), "ws://backend:8000/ws/aluno/ABC234")

    def test_servico_do_aluno_inicializa_com_limites(self):
        # packaging/sala/aluno_web.py e o entrypoint usado pelo compose do
        # ambiente isolado; precisa do backend.infraestrutura.limites presente
        # na mesma arvore pra sequer importar.
        import importlib.util

        caminho = Path(__file__).resolve().parents[2] / "packaging" / "sala" / "aluno_web.py"
        spec = importlib.util.spec_from_file_location("aluno_web", caminho)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)

        from backend.infraestrutura.limites import LimitesMiddleware

        self.assertIsInstance(modulo.app, LimitesMiddleware)


if __name__ == "__main__":
    unittest.main()
