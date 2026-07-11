import base64
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "frontend"))

from professor.telas.sessao_professor import _gerar_qrcode_b64


class QrCodeTest(unittest.TestCase):
    def test_gera_imagem_png(self):
        conteudo = base64.b64decode(
            _gerar_qrcode_b64("http://192.168.1.10:8081?codigo=ABC123")
        )

        self.assertTrue(conteudo.startswith(b"\x89PNG\r\n\x1a\n"))


if __name__ == "__main__":
    unittest.main()
