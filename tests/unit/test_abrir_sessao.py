import unittest

from backend.adaptadores.saida.memoria.armazenamento_sessoes import (
    ArmazenamentoSessoesMemoria,
)
from backend.aplicacao.servicos.sessoes import (
    AbrirSessao,
    QuizSemPerguntas,
    SemPermissao,
)


class RepositorioSessoesFalso:
    def __init__(self):
        self.perguntas = [{"id_pergunta": 1, "alternativas": []}]
        self.proprietario = 7
        self.tempo = 45
        self.link = "https://example.com/aula.png"
        self.registros = []

    def listar_perguntas(self, id_quiz):
        return self.perguntas

    def buscar_docente(self, id_quiz):
        return self.proprietario

    def buscar_tempo(self, id_quiz):
        return self.tempo

    def buscar_link_midia(self, id_quiz):
        return self.link

    def registrar(self, codigo, id_quiz, id_docente):
        self.registros.append((codigo, id_quiz, id_docente))
        return 99


class OpenSessionTest(unittest.TestCase):
    def setUp(self):
        self.repository = RepositorioSessoesFalso()
        self.store = ArmazenamentoSessoesMemoria()
        self.use_case = AbrirSessao(self.repository, self.store)

    def test_opens_session_and_stores_state(self):
        codigo = self.use_case.executar(12, 7, 7)
        session = self.store.obter(codigo)

        self.assertRegex(codigo, r"^[A-HJ-NP-Z2-9]{6}$")
        self.assertIsNotNone(session)
        self.assertEqual(session.id_sessao, 99)
        self.assertEqual(session.tempo_questao, 45)
        self.assertEqual(session.quiz_link_midia, self.repository.link)
        self.assertEqual(self.repository.registros, [(codigo, 12, 7)])

    def test_rejects_non_owner(self):
        with self.assertRaises(SemPermissao):
            self.use_case.executar(12, 8)

    def test_rejects_quiz_without_questions(self):
        self.repository.perguntas = []
        with self.assertRaises(QuizSemPerguntas):
            self.use_case.executar(12, 7)
