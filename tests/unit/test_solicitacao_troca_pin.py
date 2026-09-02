import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.adaptadores.entrada.http import rotas
from backend.main import create_app

_EMAIL = "prof@exemplo.com"
# buscar_docente_por_email -> (id, nome, email, pin_hash, papel, precisa_trocar_pin)
_DOCENTE = (9, "Prof", _EMAIL, "hash", "prof", False)
# listar_docentes -> (id, nome, email, papel, solicitou_troca_pin)
_LISTA = [
    (1, "Admin", "admin@exemplo.com", "adm", False),
    (9, "Prof", _EMAIL, "prof", True),
]


class SolicitacaoTrocaPinTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(run_migrations=False)
        self.client = TestClient(self.app)

    def tearDown(self):
        self.app.dependency_overrides.clear()
        rotas._tentativas_reset.pop(_EMAIL, None)
        rotas._tentativas_reset.pop("naoexiste@exemplo.com", None)

    @patch.object(rotas, "enviar_email_solicitacao_troca_pin")
    @patch.object(rotas, "listar_docentes", return_value=_LISTA)
    @patch.object(rotas, "marcar_solicitacao_troca_pin")
    @patch.object(rotas, "buscar_docente_por_email", return_value=_DOCENTE)
    def test_email_conhecido_marca_e_notifica_admins(self, _busca, marcar, _lista, enviar):
        resposta = self.client.post("/auth/esqueci-senha", json={"email": _EMAIL})

        self.assertEqual(resposta.status_code, 200)
        marcar.assert_called_once_with(9)
        enviar.assert_called_once()
        destinos = enviar.call_args[0][0]
        self.assertEqual(destinos, ["admin@exemplo.com"])

    @patch.object(rotas, "enviar_email_solicitacao_troca_pin")
    @patch.object(rotas, "marcar_solicitacao_troca_pin")
    @patch.object(rotas, "buscar_docente_por_email", return_value=None)
    def test_email_desconhecido_nao_marca_e_responde_ok(self, _busca, marcar, enviar):
        resposta = self.client.post("/auth/esqueci-senha", json={"email": "naoexiste@exemplo.com"})

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json(), {"ok": True})
        marcar.assert_not_called()
        enviar.assert_not_called()

    @patch.object(rotas, "listar_docentes", return_value=_LISTA)
    def test_get_docentes_expoe_flag_de_solicitacao(self, _lista):
        self.app.dependency_overrides[rotas.admin_atual] = lambda: {
            "id_docente": 1, "nome": "Admin", "email": "admin@exemplo.com",
            "papel": "adm", "precisa_trocar_pin": False,
        }

        resposta = self.client.get("/docentes")

        self.assertEqual(resposta.status_code, 200)
        por_id = {d["id_docente"]: d["solicitou_troca_pin"] for d in resposta.json()}
        self.assertTrue(por_id[9])
        self.assertFalse(por_id[1])


if __name__ == "__main__":
    unittest.main()
