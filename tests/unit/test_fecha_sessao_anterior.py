import os
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from backend.adaptadores.entrada.http import rotas as rotas_http
from backend.adaptadores.entrada.tempo_real import rotas
from backend.infraestrutura.seguranca import gerar_token_docente
from backend.main import create_app


class FechaSessaoAnteriorTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(create_app(run_migrations=False))
        self.env = patch.dict(os.environ, {"SECRET_KEY": "teste-fecha-sessao-anterior"})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.docente = (20, "Professor", "prof@exemplo.test", "prof", False, "hash-atual")
        self.token = gerar_token_docente(20, self.docente[2], "prof", self.docente[5])

        self.codigo_antigo = "OLD001"
        self.sessao_antiga = rotas.armazenamento_sessoes_ativas.criar(
            codigo=self.codigo_antigo, id_sessao=10, id_docente=20, id_quiz=30,
            perguntas=[{"id_pergunta": 1, "enunciado": "x", "alternativas": []}],
            tempo_questao=30,
        )
        self.addCleanup(rotas.armazenamento_sessoes_ativas.remover, self.codigo_antigo)
        self.aluno_ws = AsyncMock()
        self.sessao_antiga.participantes["Ana"] = rotas.Participante(apelido="Ana", ws=self.aluno_ws)

        self.codigo_de_outro_professor = "OTH001"
        self.sessao_de_outro = rotas.armazenamento_sessoes_ativas.criar(
            codigo=self.codigo_de_outro_professor, id_sessao=11, id_docente=99, id_quiz=31,
            perguntas=[{"id_pergunta": 2, "enunciado": "y", "alternativas": []}],
            tempo_questao=30,
        )
        self.addCleanup(rotas.armazenamento_sessoes_ativas.remover, self.codigo_de_outro_professor)

        self.addCleanup(rotas.armazenamento_sessoes_ativas.remover, "NOVO01")

    def _abrir_nova_sessao(self, id_quiz, id_docente_atual, id_docente_anfitriao=None):
        rotas.armazenamento_sessoes_ativas.criar(
            codigo="NOVO01", id_sessao=12, id_docente=id_docente_atual, id_quiz=id_quiz,
            perguntas=[{"id_pergunta": 3, "enunciado": "z", "alternativas": []}],
            tempo_questao=30,
        )
        return "NOVO01"

    def test_criar_nova_sessao_encerra_e_avisa_alunos_da_sessao_anterior_do_mesmo_professor(self):
        with patch.object(rotas_http, "buscar_docente_por_id", return_value=self.docente), \
             patch.object(rotas.abrir_sessao, "executar", side_effect=self._abrir_nova_sessao), \
             patch.object(rotas, "enviar_relatorio_sessao"):
            resposta = self.client.post(
                "/sessoes",
                json={"id_quiz": 40},
                headers={"Authorization": "Bearer " + self.token},
            )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json(), {"codigo": "NOVO01"})

        self.assertEqual(self.sessao_antiga.status, "encerrada")
        self.aluno_ws.send_json.assert_awaited_once_with({"tipo": "fim", "placar": [{"apelido": "Ana", "pontos": 0}]})

        self.assertEqual(self.sessao_de_outro.status, "lobby")

    def test_professor_sem_sessao_anterior_nao_afeta_ninguem(self):
        rotas.armazenamento_sessoes_ativas.remover(self.codigo_antigo)
        with patch.object(rotas_http, "buscar_docente_por_id", return_value=self.docente), \
             patch.object(rotas.abrir_sessao, "executar", side_effect=self._abrir_nova_sessao):
            resposta = self.client.post(
                "/sessoes",
                json={"id_quiz": 40},
                headers={"Authorization": "Bearer " + self.token},
            )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(self.sessao_de_outro.status, "lobby")


if __name__ == "__main__":
    unittest.main()
