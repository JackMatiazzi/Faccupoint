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
