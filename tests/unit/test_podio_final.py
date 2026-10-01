import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "frontend"))
import flet as ft
from professor.telas.sessao_professor import construir_podio


class PodioFinalTest(unittest.TestCase):
    def test_sem_respostas_mostra_mensagem(self):
        controle = construir_podio([])
        self.assertIsInstance(controle, ft.Text)
        self.assertIn("Nenhuma resposta", controle.value)

    def test_menos_de_tres_alunos_nao_quebra(self):
        placar = [{"apelido": "Ana", "pontos": 3}]
        controle = construir_podio(placar)
        linha_podio = controle.controls[0]
        self.assertEqual(len(linha_podio.controls), 1)

    def test_top_tres_aparecem_na_ordem_2_1_3(self):
        placar = [
            {"apelido": "Primeiro", "pontos": 10},
            {"apelido": "Segundo", "pontos": 8},
            {"apelido": "Terceiro", "pontos": 5},
            {"apelido": "Quarto", "pontos": 2},
        ]
        controle = construir_podio(placar)
        linha_podio = controle.controls[0]
        nomes_em_ordem_visual = [
            bloco.content.controls[1].value for bloco in linha_podio.controls
        ]
        self.assertEqual(nomes_em_ordem_visual, ["Segundo", "Primeiro", "Terceiro"])

    def test_alunos_alem_do_top_tres_ficam_na_lista_com_scroll(self):
        placar = [{"apelido": f"Aluno{i}", "pontos": 10 - i} for i in range(10)]
        controle = construir_podio(placar)
        lista_resto = controle.controls[1]
        self.assertEqual(lista_resto.scroll, ft.ScrollMode.AUTO)
        self.assertEqual(len(lista_resto.controls), 7)
        primeira_linha = lista_resto.controls[0].content.controls[0]
        self.assertEqual(primeira_linha.value, "4. Aluno3")


if __name__ == "__main__":
    unittest.main()
