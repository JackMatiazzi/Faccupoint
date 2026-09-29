import os
import unittest
from unittest.mock import patch

from frontend.compartilhado.conexao_api import (
    backend_confiavel, sessao_compativel, websocket_aluno,
)


class DestinoAlunoTest(unittest.TestCase):
    def test_destino_vem_da_configuracao_e_codigo_nao_injeta_url(self):
        with patch.dict(os.environ, {"API_URL": "https://QUIZ.example:443/"}):
            self.assertEqual(backend_confiavel(), "https://quiz.example")
            self.assertEqual(websocket_aluno("ABC234"), "wss://quiz.example/ws/aluno/ABC234")
            for codigo in ("../../admin", "ABC234?token=1", "ABC234/", None):
                with self.assertRaises(ValueError):
                    websocket_aluno(codigo)

    def test_configuracao_invalida_falha_fechada(self):
        for url in ("file:///etc/passwd", "http://user:pass@host", "http://host/path", "http://host?url=other"):
            with patch.dict(os.environ, {"API_URL": url}):
                with self.assertRaises(ValueError):
                    backend_confiavel()

    def test_sessao_legada_ou_outro_destino_nao_reutiliza_token(self):
        salva = {"codigo": "ABC234", "apelido": "Aluno", "token_reconexao": "segredo"}
        self.assertFalse(sessao_compativel(salva, "https://quiz.example"))
        salva["backend"] = "https://outro.example"
        self.assertFalse(sessao_compativel(salva, "https://quiz.example"))
        salva["backend"] = "https://quiz.example"
        self.assertTrue(sessao_compativel(salva, "https://quiz.example"))
        for invalida in ([], "texto", None, {**salva, "codigo": "../abc"}):
            self.assertFalse(sessao_compativel(invalida, "https://quiz.example"))
