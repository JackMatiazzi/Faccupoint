import unittest

from backend.dominio.sessao import Participante, Sessao


class SessionDomainTest(unittest.TestCase):
    def setUp(self):
        self.session = Sessao(
            codigo="ABC234",
            id_sessao=1,
            id_docente=10,
            id_quiz=20,
            perguntas=[{"enunciado": "P1"}, {"enunciado": "P2"}],
        )

    def test_current_question_and_answer_count(self):
        self.session.questao_atual = 0
        self.session.participantes = {
            "Ana": Participante("Ana", ws=None, resposta_atual=1),
            "Beto": Participante("Beto", ws=None, resposta_atual=1),
            "Caio": Participante("Caio", ws=None, resposta_atual=2),
        }

        self.assertEqual(self.session.pergunta_atual()["enunciado"], "P1")
        self.assertEqual(self.session.contagem_respostas(), {1: 2, 2: 1})
        self.assertTrue(self.session.todos_responderam())

    def test_empty_session_has_not_answered(self):
        self.assertFalse(self.session.todos_responderam())
