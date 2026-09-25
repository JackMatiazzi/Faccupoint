import base64
import io
import json
import os
import unittest
import urllib.error
from email import policy
from email.parser import BytesParser
from unittest.mock import patch

from backend.adaptadores.saida.email import gmail, relatorio


class GmailEmailTest(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {
            "EMAIL_PROVIDER": "gmail", "GMAIL_CLIENT_ID": "client",
            "GMAIL_CLIENT_SECRET": "secret", "GMAIL_REFRESH_TOKEN": "refresh",
            "GMAIL_FROM": "app@example.com",
        }, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_refresh_and_send_preserve_csv_and_unicode(self):
        responses = [io.BytesIO(b'{"access_token":"access"}'), io.BytesIO(b'{"id":"message-id"}')]
        with patch.object(gmail.urllib.request, "urlopen", side_effect=responses) as send:
            relatorio._enviar_email(destino="prof@example.com", assunto="Resultado: animação",
                                    texto="Olá professor", anexo_nome="resultado.csv",
                                    anexo_conteudo="aluno;nota\nFictício;10\n".encode("utf-8-sig"))
        self.assertEqual(send.call_count, 2)
        refresh, message = [call.args[0] for call in send.call_args_list]
        self.assertEqual(refresh.full_url, "https://oauth2.googleapis.com/token")
        self.assertIn(b"grant_type=refresh_token", refresh.data)
        self.assertEqual(message.full_url, "https://gmail.googleapis.com/gmail/v1/users/me/messages/send")
        self.assertEqual(message.headers["Authorization"], "Bearer access")
        mime = BytesParser(policy=policy.default).parsebytes(base64.urlsafe_b64decode(json.loads(message.data)["raw"]))
        self.assertEqual(mime["To"], "prof@example.com")
        self.assertEqual(mime["From"], "app@example.com")
        self.assertEqual(mime["Subject"], "Resultado: animação")
        attachment = next(mime.iter_attachments())
        self.assertEqual(attachment.get_filename(), "resultado.csv")
        self.assertEqual(attachment.get_payload(decode=True), "aluno;nota\nFictício;10\n".encode("utf-8-sig"))

    def test_gmail_failure_does_not_fall_back_or_expose_tokens(self):
        error = urllib.error.HTTPError("https://oauth2.googleapis.com/token", 400, "error", {}, io.BytesIO(b'{"secret":"refresh"}'))
        with patch.object(gmail.urllib.request, "urlopen", side_effect=error), patch.object(relatorio, "_enviar_por_smtp") as smtp:
            with self.assertRaisesRegex(RuntimeError, "autorizacao.*HTTP 400") as caught:
                relatorio._enviar_email(destino="prof@example.com", assunto="Teste", texto="Teste")
        self.assertNotIn("refresh", str(caught.exception))
        smtp.assert_not_called()

    def test_incomplete_configuration_fails_before_network(self):
        os.environ.pop("GMAIL_REFRESH_TOKEN")
        with patch.object(gmail.urllib.request, "urlopen") as send:
            with self.assertRaisesRegex(RuntimeError, "GMAIL_REFRESH_TOKEN"):
                gmail.enviar_por_gmail(destino="prof@example.com", assunto="Teste", texto="Teste")
        send.assert_not_called()

    def test_report_uses_gmail_without_smtp_or_resend_configuration(self):
        report = {"email_professor": "prof@example.com", "codigo": "ABCDEF", "quiz": "Teste"}
        with patch.object(relatorio, "buscar_relatorio_sessao", return_value=report), \
             patch.object(relatorio, "_montar_texto", return_value="Resumo"), \
             patch.object(relatorio, "_nome_arquivo_csv", return_value="resultado.csv"), \
             patch.object(relatorio, "_montar_csv", return_value="quiz;nota"), \
             patch.object(relatorio, "enviar_por_gmail") as send:
            relatorio.enviar_relatorio_sessao(111)
        self.assertEqual(send.call_args.kwargs["destino"], "prof@example.com")


if __name__ == "__main__":
    unittest.main()
