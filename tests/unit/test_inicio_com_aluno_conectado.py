import os
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from backend.adaptadores.entrada.http import rotas as rotas_http
from backend.adaptadores.entrada.tempo_real import rotas
from backend.infraestrutura.seguranca import gerar_token_docente
from backend.main import create_app


class InicioComAlunoConectadoTest(unittest.TestCase):
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
        self.addCleanup(rotas.armazenamento_sessoes_ativas.remover, self.codigo)
        self.env = patch.dict(os.environ, {"SECRET_KEY": "teste-inicio-sala"})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.docente = (20, "Professor", "prof@exemplo.test", "prof", False, "hash-atual")
        self.token = gerar_token_docente(20, self.docente[2], "prof", self.docente[5])
        self.rodar_questao = AsyncMock()
        tarefa = patch.object(rotas, "_rodar_questao", new=self.rodar_questao)
        tarefa.start()
        self.addCleanup(tarefa.stop)

    def _iniciar(self):
        with patch.object(rotas_http, "buscar_docente_por_id", return_value=self.docente):
            return self.client.post(
                f"/sessoes/{self.codigo}/iniciar",
                headers={"Authorization": "Bearer " + self.token},
            )

    def test_recusa_iniciar_sem_nenhum_aluno_conectado(self):
        self.sessao.participantes["Ana"] = rotas.Participante(apelido="Ana", ws=None)

        resposta = self._iniciar()

        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(self.sessao.status, "lobby")
        self.rodar_questao.assert_not_called()

    def test_permite_iniciar_com_pelo_menos_um_aluno_conectado(self):
        self.sessao.participantes["Ana"] = rotas.Participante(apelido="Ana", ws=None)
        self.sessao.participantes["Bia"] = rotas.Participante(apelido="Bia", ws=object())

        resposta = self._iniciar()

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(self.sessao.status, "rodando")
        self.rodar_questao.assert_awaited_once_with(self.codigo)


if __name__ == "__main__":
    unittest.main()
