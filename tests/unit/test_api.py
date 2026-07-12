import json
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from backend.adaptadores.entrada.http import rotas
from backend.main import create_app


class ApiSmokeTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(create_app(run_migrations=False))

    def test_health_and_security_headers(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
        self.assertEqual(response.headers["x-content-type-options"], "nosniff")
        self.assertEqual(response.headers["x-frame-options"], "DENY")

    def test_endpoint_informa_versao_do_manifesto(self):
        caminho = Path(__file__).resolve().parents[2] / ".release-please-manifest.json"
        versao_esperada = str(json.loads(caminho.read_text(encoding="utf-8"))["."])

        with patch.dict("os.environ", {"APP_VERSION": ""}):
            response = self.client.get("/versao")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"versao": versao_esperada})

    def test_protected_route_rejects_missing_token_without_database(self):
        response = self.client.get("/quizzes", params={"id_docente": 1})
        self.assertEqual(response.status_code, 401)

    def test_login_rate_limit_informa_tempo_restante(self):
        email = "limite@example.com"
        rotas._tentativas_login[email] = [100.0] * rotas._MAX_TENTATIVAS_LOGIN
        try:
            with patch.object(rotas.time, "monotonic", return_value=101.0):
                with self.assertRaises(HTTPException) as contexto:
                    rotas._checar_rate_limit_login(email)

            erro = contexto.exception
            self.assertEqual(erro.status_code, 429)
            self.assertEqual(erro.headers["Retry-After"], "59")
            self.assertIn("59 segundos", erro.detail)
        finally:
            rotas._tentativas_login.pop(email, None)
