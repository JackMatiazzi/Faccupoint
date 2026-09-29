import unittest
from unittest.mock import MagicMock, patch

import psycopg2
from pydantic import ValidationError

from backend.adaptadores.entrada.http.rotas import CadastrarQuizEntrada, AtualizarQuizEntrada
from backend.adaptadores.saida.postgres import repositorio
from backend.dominio.docente import normalizar_docente


class CamposDocenteQuizTest(unittest.TestCase):
    def test_docente_invalido_nao_chega_ao_banco(self):
        for nome, email, pin in [('', 'p@example.invalid', '1234'),
                                 ('Prof', 'sem-email', '1234'),
                                 ('Prof', 'p@example.invalid', 'abc'),
                                 ('Prof', 'p@example.invalid', ''),
                                 ('Prof', 'p@example.invalid', '12345')]:
            with self.subTest(nome=nome, email=email, pin=pin), patch.object(repositorio, '_conectar') as conectar:
                with self.assertRaises(ValueError):
                    repositorio.cadastrar_docente(nome, email, pin)
                conectar.assert_not_called()

    def test_normalizacao_preserva_pin_com_zero_e_edicao_sem_troca(self):
        self.assertEqual(normalizar_docente(' Prof ', ' P@EXAMPLE.INVALID ', '0001', novo=True),
                         ('Prof', 'p@example.invalid'))
        for pin in (None, ''):
            self.assertEqual(normalizar_docente('Prof', 'p@example.invalid', pin, novo=False),
                             ('Prof', 'p@example.invalid'))

    def test_email_duplicado_vira_erro_de_validacao(self):
        conn = MagicMock()
        conn.cursor.return_value.__enter__.return_value.execute.side_effect = psycopg2.errors.UniqueViolation()
        with patch.object(repositorio, '_conectar', return_value=conn):
            with self.assertRaisesRegex(ValueError, 'email'):
                repositorio.cadastrar_docente('Prof', 'p@example.invalid', '1234')
        conn.commit.assert_not_called()
        conn.close.assert_called_once()

    def test_tempo_de_quiz_invalido_em_criacao_e_edicao(self):
        for model in (CadastrarQuizEntrada, AtualizarQuizEntrada):
            for tempo in (-1, 0, 1.5, True, 'abc'):
                with self.subTest(model=model.__name__, tempo=tempo), self.assertRaises(ValidationError):
                    model(id_docente_proprietario=1, titulo='Quiz', tempo_segundos=tempo)
            for tempo in (None, 1, 30):
                self.assertEqual(model(id_docente_proprietario=1, titulo='Quiz', tempo_segundos=tempo).tempo_segundos, tempo)

    def test_tempo_invalido_tambem_rejeitado_no_repositorio(self):
        with patch.object(repositorio, '_conectar') as conectar:
            for tempo in (0, -1, True, 1.5):
                with self.assertRaises(ValueError):
                    repositorio.cadastrar_quiz(1, 'Quiz', None, tempo)
                with self.assertRaises(ValueError):
                    repositorio.atualizar_quiz(1, 1, 'Quiz', None, tempo)
            conectar.assert_not_called()
