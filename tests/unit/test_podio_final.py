import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "frontend"))
import flet as ft
from compartilhado.sistema_design.componentes.podio import construir_podio


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

    def test_top_cinco_aparecem_na_ordem_4_2_1_3_5(self):
        placar = [{"apelido": f"Aluno{i}", "pontos": 10 - i} for i in range(1, 7)]
        linha_podio = construir_podio(placar).controls[0]
        nomes = [bloco.content.controls[1].value for bloco in linha_podio.controls]
        self.assertEqual(nomes, ["Aluno4", "Aluno2", "Aluno1", "Aluno3", "Aluno5"])

    def test_podio_mostra_posicao_em_texto_sem_emoji(self):
        placar = [{"apelido": f"Aluno{i}", "pontos": 10 - i} for i in range(1, 6)]
        linha_podio = construir_podio(placar).controls[0]
        posicoes = [bloco.content.controls[0].value for bloco in linha_podio.controls]
        self.assertEqual(posicoes, ["4º", "2º", "1º", "3º", "5º"])

    def test_tres_alunos_mantem_primeiro_no_centro(self):
        placar = [{"apelido": n, "pontos": 1} for n in ("Primeiro", "Segundo", "Terceiro")]
        linha_podio = construir_podio(placar).controls[0]
        nomes = [bloco.content.controls[1].value for bloco in linha_podio.controls]
        self.assertEqual(nomes, ["Segundo", "Primeiro", "Terceiro"])

    def test_blocos_dividem_a_largura_para_caber_no_celular(self):
        placar = [{"apelido": f"Aluno{i}", "pontos": 1} for i in range(5)]
        linha_podio = construir_podio(placar).controls[0]
        self.assertTrue(all(bloco.expand and bloco.width is None for bloco in linha_podio.controls))

    def test_alunos_alem_do_top_cinco_ficam_na_lista_com_scroll(self):
        placar = [{"apelido": f"Aluno{i}", "pontos": 10 - i} for i in range(10)]
        lista_resto = construir_podio(placar).controls[1]
        self.assertEqual(lista_resto.scroll, ft.ScrollMode.AUTO)
        self.assertEqual(len(lista_resto.controls), 5)
        self.assertEqual(lista_resto.controls[0].content.controls[0].value, "6. Aluno5")


if __name__ == "__main__":
    unittest.main()
