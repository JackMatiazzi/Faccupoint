import os
import unittest
from unittest.mock import patch

from backend.infraestrutura.seguranca import (
    fingerprint_pin,
    gerar_hash_pin,
    gerar_token_docente,
    verificar_pin,
    verificar_token_docente,
)

_PIN_HASH = gerar_hash_pin("1234")


class SecurityTest(unittest.TestCase):
    def test_pin_hash(self):
        pin_hash = gerar_hash_pin("1234")
        self.assertTrue(verificar_pin("1234", pin_hash))
        self.assertFalse(verificar_pin("9999", pin_hash))

    def test_signed_token(self):
        with patch.dict(os.environ, {"SECRET_KEY": "test-secret-key"}, clear=False):
            token = gerar_token_docente(3, "prof@example.com", "prof", _PIN_HASH)
            payload = verificar_token_docente(token)

        self.assertIsNotNone(payload)
        self.assertEqual(payload["id_docente"], 3)
        self.assertEqual(payload["papel"], "prof")
        self.assertEqual(payload["pv"], fingerprint_pin(_PIN_HASH))

    def test_fingerprint_muda_quando_o_pin_hash_muda(self):
        outro_hash = gerar_hash_pin("1234")  # salt novo -> hash diferente
        self.assertNotEqual(fingerprint_pin(_PIN_HASH), fingerprint_pin(outro_hash))

    def test_token_adulterado_e_rejeitado(self):
        import base64
        import json

        with patch.dict(os.environ, {"SECRET_KEY": "test-secret-key"}, clear=False):
            token = gerar_token_docente(1, "prof@example.com", "prof", _PIN_HASH)

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
