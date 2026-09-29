import asyncio
import csv
import io
import json
import unittest
from decimal import Decimal
from unittest.mock import AsyncMock, patch

from fastapi import WebSocketDisconnect

from backend.dominio.pergunta import validar_peso
from backend.adaptadores.entrada.http.rotas import PerguntaEntrada
from backend.adaptadores.entrada.tempo_real import rotas
from backend.adaptadores.saida.email.relatorio import _montar_csv


class PontosDecimaisTest(unittest.TestCase):
    def test_valida_virgula_ponto_e_limites(self):
        for valor in ["0,1", "0.10", 0.1]:
            self.assertEqual(validar_peso(valor), Decimal("0.1"))
        for valor in [0, -1, 100.01, "0.001", "NaN", "Infinity", True]:
            with self.subTest(valor=valor), self.assertRaises(ValueError):
                validar_peso(valor)
        entrada = PerguntaEntrada(enunciado="Teste", alternativas=[], peso="0,1")
        self.assertEqual(entrada.model_dump()["peso"], 0.1)

    def test_placar_soma_decimais_sem_residuo(self):
        codigo = "DEC234"
        pergunta = {"peso": 0.1, "alternativas": [{"correta": True}]}
        sessao = rotas.armazenamento_sessoes_ativas.criar(
            codigo=codigo, id_sessao=1, id_docente=2, id_quiz=3,
            perguntas=[pergunta, pergunta.copy()], tempo_questao=30,
        )
        self.addCleanup(rotas.armazenamento_sessoes_ativas.remover, codigo)
        aluno = rotas.Participante(apelido="Ana", ws=None, pontos=0.2, resposta_atual=0)
        sessao.participantes["Ana"] = aluno
        sessao.questao_atual = 0
        sessao.status = "rodando"
        with patch.object(rotas.asyncio, "sleep", new=AsyncMock()), patch.object(rotas, "_rodar_questao", new=AsyncMock()):
            asyncio.run(rotas._revelar_resultado(codigo))
        self.assertEqual(aluno.pontos, 0.3)

    def test_resposta_persiste_o_peso_decimal_da_pergunta(self):
        # Regressao: sem o 5o argumento de registrar_tentativa, a persistencia
        # cairia no default 1 mesmo numa pergunta de 0,1 ponto, divergindo do
        # placar em memoria (que ja usa o peso decimal certo).
        codigo = "DEC235"
        sessao = rotas.armazenamento_sessoes_ativas.criar(
            codigo=codigo, id_sessao=1, id_docente=2, id_quiz=3,
            perguntas=[{
                "id_pergunta": 40, "peso": 0.1, "enunciado": "Teste",
                "alternativas": [{"id": 1, "texto": "A", "correta": True}],
            }],
            tempo_questao=30,
        )
        self.addCleanup(rotas.armazenamento_sessoes_ativas.remover, codigo)
        participante = rotas.Participante(
            apelido="Ana", ws=None, id_participante=99, token_reconexao="t",
        )
        sessao.participantes["Ana"] = participante
        sessao.status = "rodando"
        sessao.questao_atual = 0

        ws = AsyncMock()
        ws.receive_text.side_effect = [
            json.dumps({"apelido": "Ana", "token_reconexao": "t"}),
            json.dumps({"tipo": "resposta", "indice": 0}),
            WebSocketDisconnect(code=1000),
        ]
        with patch.object(rotas, "registrar_tentativa") as registrar:
            asyncio.run(rotas.ws_aluno(ws, codigo))

        registrar.assert_called_once_with(99, 40, 1, True, 0.1)

    def test_csv_pontos_por_resposta_e_total_por_aluno(self):
        def resposta(aluno, pontos, acertou):
            return dict(aluno=aluno, pontos=Decimal(pontos), acertou=acertou, ordem=1,
                        pergunta="Teste", resposta="A" if acertou is not None else None,
                        correta="A", respondida_em=None)
        relatorio = dict(codigo="DEC234", quiz="Teste", professor="Prof", respostas=[
            resposta("Ana", "0.1", True), resposta("Ana", "0.2", True),
            resposta("Bruno", "0", False), resposta("Carla", "0", None),
        ])
        linhas = list(csv.DictReader(io.StringIO(_montar_csv(relatorio)), delimiter=";"))
        self.assertEqual([r["pontos"] for r in linhas], ["0,1", "0,2", "0", "0"])
        self.assertEqual([r["total_pontos_aluno"] for r in linhas], ["0,3", "0,3", "0", "0"])


if __name__ == "__main__":
    unittest.main()
