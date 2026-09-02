import asyncio
import time
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from backend.adaptadores.entrada.tempo_real import rotas
from backend.main import create_app


class ReconexaoAlunoTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(create_app(run_migrations=False))
        self.codigo = "ABC234"
        self.sessao = rotas.armazenamento_sessoes_ativas.criar(
            codigo=self.codigo,
            id_sessao=10,
            id_docente=20,
            id_quiz=30,
            perguntas=[{
                "id_pergunta": 40,
                "enunciado": "Quanto e 2 + 2?",
                "alternativas": [
                    {"id": 1, "texto": "3", "correta": False},
                    {"id": 2, "texto": "4", "correta": True},
                ],
            }],
            tempo_questao=30,
        )

    def tearDown(self):
        rotas.armazenamento_sessoes_ativas.remover(self.codigo)

    def _entrar_e_obter_token(self):
        with patch.object(rotas, "registrar_participante_sessao", return_value=99):
            with self.client.websocket_connect(f"/ws/aluno/{self.codigo}") as ws:
                ws.send_json({"apelido": "Ana"})
                identificado = ws.receive_json()
                self.assertEqual(identificado["tipo"], "identificado")
                return identificado["token_reconexao"]

    def test_participante_permanece_na_sessao_apos_desconectar(self):
        self._entrar_e_obter_token()

        self.assertIn("Ana", self.sessao.participantes)
        self.assertIsNone(self.sessao.participantes["Ana"].ws)

    def test_reconecta_durante_pergunta_e_recupera_estado(self):
        token = self._entrar_e_obter_token()
        participante = self.sessao.participantes["Ana"]
        participante.pontos = 2
        participante.resposta_atual = 1
        self.sessao.status = "rodando"
        self.sessao.fase = "pergunta"
        self.sessao.questao_atual = 0
        self.sessao.questao_iniciada_em = time.monotonic() - 5

        with self.client.websocket_connect(f"/ws/aluno/{self.codigo}") as ws:
            ws.send_json({"apelido": "Ana", "token_reconexao": token})
            self.assertEqual(ws.receive_json()["tipo"], "identificado")
            estado = ws.receive_json()

            self.assertEqual(estado["tipo"], "questao")
            self.assertEqual(estado["resposta_atual"], 1)
            self.assertGreaterEqual(estado["tempo"], 24)
            self.assertLessEqual(estado["tempo"], 25)

    def test_reconecta_apos_encerramento_e_recupera_placar(self):
        token = self._entrar_e_obter_token()
        self.sessao.participantes["Ana"].pontos = 3
        self.sessao.status = "encerrada"
        self.sessao.fase = "fim"

        with self.client.websocket_connect(f"/ws/aluno/{self.codigo}") as ws:
            ws.send_json({"apelido": "Ana", "token_reconexao": token})
            self.assertEqual(ws.receive_json()["tipo"], "identificado")
            fim = ws.receive_json()

            self.assertEqual(fim["tipo"], "fim")
            self.assertEqual(fim["placar"], [{"apelido": "Ana", "pontos": 3}])

    def test_nao_permite_tomar_apelido_sem_token(self):
        self._entrar_e_obter_token()
        self.sessao.status = "rodando"

        with self.client.websocket_connect(f"/ws/aluno/{self.codigo}") as ws:
            ws.send_json({"apelido": "Ana"})
            erro = ws.receive_json()

            self.assertEqual(erro["tipo"], "erro")

    def test_resposta_correta_soma_o_peso_da_pergunta(self):
        participante = rotas.Participante(
            apelido="Ana", ws=None, resposta_atual=1, pontos=2
        )
        self.sessao.perguntas[0]["peso"] = 5
        self.sessao.perguntas.append(self.sessao.perguntas[0].copy())
        self.sessao.participantes["Ana"] = participante
        self.sessao.status = "rodando"
        self.sessao.questao_atual = 0

        with patch.object(rotas.asyncio, "sleep", new=AsyncMock()), patch.object(
            rotas, "_rodar_questao", new=AsyncMock()
        ):
            asyncio.run(rotas._revelar_resultado(self.codigo))

        self.assertEqual(participante.pontos, 7)


if __name__ == "__main__":
    unittest.main()
