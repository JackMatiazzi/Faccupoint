import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "frontend"))


class AmbienteSalaIsoladoTest(unittest.TestCase):
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
