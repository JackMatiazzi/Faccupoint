import unittest

from fastapi.testclient import TestClient

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

    def test_protected_route_rejects_missing_token_without_database(self):
        response = self.client.get("/quizzes", params={"id_docente": 1})
        self.assertEqual(response.status_code, 401)
