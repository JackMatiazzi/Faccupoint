import unittest

from backend.dominio.pergunta import normalizar_pergunta, validar_link_midia


class QuestionRulesTest(unittest.TestCase):
    def test_accepts_more_than_one_correct_alternative(self):
        texto, alternativas, midia = normalizar_pergunta(
            "  Selecione uma resposta aceita  ",
            [
                {"texto": " A ", "correta": True},
                {"texto": " B ", "correta": True},
                {"texto": " C ", "correta": False},
            ],
            None,
        )

        self.assertEqual(texto, "Selecione uma resposta aceita")
        self.assertEqual([a["texto"] for a in alternativas], ["A", "B", "C"])
        self.assertEqual(sum(a["correta"] for a in alternativas), 2)
        self.assertIsNone(midia)

    def test_rejects_question_without_accepted_answer(self):
        with self.assertRaisesRegex(ValueError, "alternativa correta"):
            normalizar_pergunta(
                "Pergunta",
                [
                    {"texto": "A", "correta": False},
                    {"texto": "B", "correta": False},
                ],
                None,
            )

    def test_rejects_internal_media_url(self):
        with self.assertRaisesRegex(ValueError, "endereco interno"):
            validar_link_midia("https://127.0.0.1/imagem.png")
