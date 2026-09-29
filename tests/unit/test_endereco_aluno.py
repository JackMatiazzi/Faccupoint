import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "frontend"))
from professor.telas.sessao_professor import _origem_aluno


class EnderecoAlunoTest(unittest.TestCase):
    def test_qr_substitui_loopback_por_endereco_da_rede(self):
        for origem in ("", "http://localhost:8081", "http://127.0.0.1:8081", "http://[::1]:8081"):
            with self.subTest(origem=origem), patch.dict(os.environ, ALUNO_PUBLIC_URL=origem), patch(
                "professor.telas.sessao_professor._ip_local", return_value="192.168.1.16"
            ), patch("professor.telas.sessao_professor._PORTA_ALUNO", 8081):
                self.assertEqual(_origem_aluno(), "http://192.168.1.16:8081")

    def test_preserva_endereco_publico_configurado(self):
        with patch.dict(os.environ, ALUNO_PUBLIC_URL="https://aula.example.com/"):
            self.assertEqual(_origem_aluno(), "https://aula.example.com")
