import json
import os
import unittest
from unittest.mock import patch

from backend.adaptadores.saida.email import relatorio


class ResendEmailTest(unittest.TestCase):
    def test_resend_payload_with_attachment(self):
        requests = []

        class FakeResponse:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        def fake_urlopen(request, timeout):
            requests.append((request, timeout))
            return FakeResponse()

        env = {
            "RESEND_API_KEY": "re_test",
            "EMAIL_FROM": "FaccuPoint <onboarding@resend.dev>",
        }
        with patch.dict(os.environ, env, clear=False), patch(
            "backend.adaptadores.saida.email.relatorio.urllib.request.urlopen",
            side_effect=fake_urlopen,
        ):
            relatorio._enviar_por_resend(
                destino="prof@example.com",
                assunto="Resultado",
                texto="Resumo",
                anexo_nome="resultado.csv",
                anexo_conteudo=b"sala;aluno\nABC;Ana\n",
            )

        request, timeout = requests[0]
        payload = json.loads(request.data.decode("utf-8"))

        self.assertEqual(timeout, 20)
        self.assertEqual(request.full_url, "https://api.resend.com/emails")
        self.assertEqual(request.headers["Authorization"], "Bearer re_test")
        self.assertEqual(request.headers["User-agent"], "FaccuPoint/1.0")
        self.assertEqual(payload["from"], "FaccuPoint <onboarding@resend.dev>")
        self.assertEqual(payload["to"], ["prof@example.com"])
        self.assertEqual(payload["attachments"][0]["filename"], "resultado.csv")
        self.assertTrue(payload["attachments"][0]["content"])
