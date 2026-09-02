import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.adaptadores.entrada.http import rotas
from backend.main import create_app

_DOCENTE_EMAIL = "prof@exemplo.com"
# buscar_docente_por_email -> (id, nome, email, pin_hash, papel, precisa_trocar_pin)
_DOCENTE_FAKE = (7, "Prof", _DOCENTE_EMAIL, "hash-do-pin-atual", "prof", True)
# buscar_docente_por_id -> (id, nome, email, papel, precisa_trocar_pin, pin_hash)
_DOCENTE_POR_ID = (7, "Prof", _DOCENTE_EMAIL, "prof", True, "hash-do-pin-atual")


class TrocarPinPrimeiroAcessoTest(unittest.TestCase):
    def setUp(self):
        # /auth/trocar-pin reemite o token no fim; gerar_token_docente exige SECRET_KEY.
        # No CI nao existe backend/.env, entao definimos um valor de teste.
        segredo = patch.dict(os.environ, {"SECRET_KEY": "teste-ci"}, clear=False)
        segredo.start()
        self.addCleanup(segredo.stop)

        self.app = create_app(run_migrations=False)
        self.app.dependency_overrides[rotas.docente_trocando_pin] = lambda: {
            "id_docente": 7,
            "nome": "Prof",
            "email": _DOCENTE_EMAIL,
            "papel": "prof",
            "precisa_trocar_pin": True,
        }
        self.client = TestClient(self.app)

    def tearDown(self):
        self.app.dependency_overrides.clear()
        rotas._tentativas_login.pop(_DOCENTE_EMAIL, None)

    def _trocar(self, **corpo):
        return self.client.post("/auth/trocar-pin", json=corpo)

    @patch.object(rotas, "trocar_pin_docente", return_value="hash-novo")
    @patch.object(rotas, "verificar_pin", return_value=True)
    @patch.object(rotas, "buscar_docente_por_email", return_value=_DOCENTE_FAKE)
    def test_troca_bem_sucedida_chama_repositorio_e_devolve_token(self, _busca, _verifica, trocar):
        resposta = self._trocar(pin_atual="1111", novo_pin="2222")

        self.assertEqual(resposta.status_code, 200)
        trocar.assert_called_once_with(7, "2222")
        self.assertTrue(resposta.json().get("token"))

    @patch.object(rotas, "trocar_pin_docente")
    @patch.object(rotas, "verificar_pin", return_value=False)
    @patch.object(rotas, "buscar_docente_por_email", return_value=_DOCENTE_FAKE)
    def test_pin_atual_incorreto_retorna_401(self, _busca, _verifica, trocar):
        resposta = self._trocar(pin_atual="0000", novo_pin="2222")

        self.assertEqual(resposta.status_code, 401)
        trocar.assert_not_called()

    @patch.object(rotas, "trocar_pin_docente")
    @patch.object(rotas, "verificar_pin", return_value=True)
    @patch.object(rotas, "buscar_docente_por_email", return_value=_DOCENTE_FAKE)
    def test_novo_pin_fora_do_formato_retorna_400(self, _busca, _verifica, trocar):
        for pin in ("123", "12345", "abcd", "12a4"):
            with self.subTest(pin=pin):
                resposta = self._trocar(pin_atual="1111", novo_pin=pin)
                self.assertEqual(resposta.status_code, 400)
        trocar.assert_not_called()

    @patch.object(rotas, "trocar_pin_docente")
    @patch.object(rotas, "verificar_pin", return_value=True)
    @patch.object(rotas, "buscar_docente_por_email", return_value=_DOCENTE_FAKE)
    def test_novo_pin_igual_ao_atual_retorna_400(self, _busca, _verifica, trocar):
        resposta = self._trocar(pin_atual="1111", novo_pin="1111")

        self.assertEqual(resposta.status_code, 400)
        trocar.assert_not_called()

    @patch.object(rotas, "fingerprint_pin", return_value="fp-atual")
    @patch.object(rotas, "buscar_docente_por_id", return_value=_DOCENTE_POR_ID)
    @patch.object(
        rotas,
        "verificar_token_docente",
        return_value={"id_docente": 7, "email": _DOCENTE_EMAIL, "papel": "prof", "pv": "fp-atual"},
    )
    def test_flag_ligada_bloqueia_rota_comum_com_403(self, _token, _busca, _fp):
        resposta = self.client.get(
            "/quizzes",
            params={"id_docente": 7},
            headers={"Authorization": "Bearer qualquer-coisa"},
        )

        self.assertEqual(resposta.status_code, 403)

    @patch.object(rotas, "fingerprint_pin", return_value="fp-novo")
    @patch.object(rotas, "buscar_docente_por_id", return_value=_DOCENTE_POR_ID)
    @patch.object(
        rotas,
        "verificar_token_docente",
        return_value={"id_docente": 7, "email": _DOCENTE_EMAIL, "papel": "prof", "pv": "fp-velho"},
    )
    def test_token_com_fingerprint_desatualizado_retorna_401(self, _token, _busca, _fp):
        resposta = self.client.get(
            "/quizzes",
            params={"id_docente": 7},
            headers={"Authorization": "Bearer token-de-antes-da-troca"},
        )

        self.assertEqual(resposta.status_code, 401)


if __name__ == "__main__":
    unittest.main()
