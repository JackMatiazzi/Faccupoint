import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.adaptadores.entrada.http import rotas
from backend.infraestrutura.seguranca import gerar_token_docente
from backend.main import create_app


class AutorizacaoRotasTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(run_migrations=False)
        self.client = TestClient(self.app)

    def test_rotas_privadas_rejeitam_anonimo_e_token_de_aluno(self):
        # Inventario explicito: qualquer rota nova exige uma decisao sobre acesso.
        publicas = {
            "/health", "/versao", "/auth/login", "/auth/esqueci-senha",
            "/sessoes/{codigo}", "/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc",
        }
        for rota in self.app.routes:
            if not getattr(rota, "methods", None) or rota.path in publicas:
                continue
            path = rota.path
            for nome in ("id_alvo", "id_quiz", "id_pergunta"):
                path = path.replace("{" + nome + "}", "1")
            path = path.replace("{codigo}", "ABC234")
            for metodo in rota.methods - {"HEAD", "OPTIONS"}:
                for headers in ({}, {"Authorization": "Bearer token-de-reconexao-do-aluno"}):
                    with self.subTest(path=path, metodo=metodo, headers=headers):
                        resposta = self.client.request(metodo, path, headers=headers, json={})
                        self.assertEqual(resposta.status_code, 401)

    def test_professor_nao_pode_usar_rotas_de_administrador(self):
        docente = (20, "Professor", "prof@exemplo.test", "prof", False, "hash-atual")
        with patch.dict(os.environ, {"SECRET_KEY": "segredo-local-de-teste"}), patch.object(
            rotas, "buscar_docente_por_id", return_value=docente
        ):
            token = gerar_token_docente(20, docente[2], "prof", "hash-atual")
            for metodo, path in (
                ("GET", "/docentes"), ("POST", "/docentes"),
                ("PUT", "/docentes/1"), ("DELETE", "/docentes/1"),
                ("POST", "/diagnostico/email"),
            ):
                with self.subTest(metodo=metodo, path=path):
                    resposta = self.client.request(
                        metodo, path, json={}, headers={"Authorization": "Bearer " + token}
                    )
                    self.assertEqual(resposta.status_code, 403)

    def test_professor_nao_le_gabarito_de_quiz_alheio(self):
        docente = (20, "Professor", "prof@exemplo.test", "prof", False, "hash-atual")
        with patch.dict(os.environ, {"SECRET_KEY": "segredo-local-de-teste"}), patch.object(
            rotas, "buscar_docente_por_id", return_value=docente
        ), patch.object(rotas, "buscar_docente_do_quiz", return_value=99), patch.object(
            rotas, "listar_perguntas_do_quiz"
        ) as listar:
            token = gerar_token_docente(20, docente[2], "prof", "hash-atual")
            resposta = self.client.get(
                "/quizzes/1/perguntas", headers={"Authorization": "Bearer " + token}
            )
        self.assertEqual(resposta.status_code, 403)
        listar.assert_not_called()
