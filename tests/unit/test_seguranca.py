import os
import unittest
from unittest.mock import patch

from backend.infraestrutura.seguranca import (
    gerar_hash_pin,
    gerar_token_docente,
    verificar_pin,
    verificar_token_docente,
)


class SecurityTest(unittest.TestCase):
    def test_pin_hash(self):
        pin_hash = gerar_hash_pin("1234")
        self.assertTrue(verificar_pin("1234", pin_hash))
        self.assertFalse(verificar_pin("9999", pin_hash))

    def test_signed_token(self):
        with patch.dict(os.environ, {"SECRET_KEY": "test-secret-key"}, clear=False):
            token = gerar_token_docente(3, "prof@example.com", "prof")
            payload = verificar_token_docente(token)

        self.assertIsNotNone(payload)
        self.assertEqual(payload["id_docente"], 3)
        self.assertEqual(payload["papel"], "prof")

    def test_token_adulterado_e_rejeitado(self):
        import base64
        import json

        with patch.dict(os.environ, {"SECRET_KEY": "test-secret-key"}, clear=False):
            token = gerar_token_docente(1, "prof@example.com", "prof")

        payload_b64, assinatura = token.split(".", 1)
        padding = "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64 + padding))
        payload["papel"] = "adm"
        payload_adulterado = base64.urlsafe_b64encode(
            json.dumps(payload, separators=(",", ":")).encode()
        ).decode().rstrip("=")
        token_adulterado = f"{payload_adulterado}.{assinatura}"

        with patch.dict(os.environ, {"SECRET_KEY": "test-secret-key"}, clear=False):
            resultado = verificar_token_docente(token_adulterado)

        self.assertIsNone(resultado)
