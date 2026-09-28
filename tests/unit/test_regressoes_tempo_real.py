import asyncio
import json
import time
import unittest
from unittest.mock import AsyncMock, patch

from fastapi import WebSocketDisconnect

from backend.adaptadores.entrada.tempo_real import rotas


class RegressoesTempoRealTest(unittest.TestCase):
    def setUp(self):
        self.codigo = "REG234"
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

    def _participante_em_pergunta(self):
        participante = rotas.Participante(
            apelido="Ana", ws=None, id_participante=99,
            token_reconexao="token-local-de-teste", pontos=2,
        )
        self.sessao.participantes["Ana"] = participante
        self.sessao.status = "rodando"
        self.sessao.fase = "pergunta"
        self.sessao.questao_atual = 0
        self.sessao.questao_iniciada_em = time.monotonic()
        return participante

    def _rodar(self, participante, *mensagens):
        ws = AsyncMock()
        ws.receive_text.side_effect = [
            json.dumps({"apelido": "Ana", "token_reconexao": participante.token_reconexao}),
            *(json.dumps(m) for m in mensagens),
            WebSocketDisconnect(code=1000),
        ]
        with patch.object(rotas, "registrar_tentativa") as registrar:
            asyncio.run(rotas.ws_aluno(ws, self.codigo))
        return registrar

    def _assert_persistiu_resposta_correta(self, registrar):
        # So confere os 4 primeiros argumentos: feat/pontuacao-decimal-csv
        # acrescenta um 5o (peso) quando mergeada junto: essa branch, isolada,
        # nao envolve peso e nao deve travar nem exigir atualizacao por causa dele.
        self.assertEqual(registrar.call_count, 1)
        self.assertEqual(registrar.call_args.args[:4], (99, 40, 2, True))

    def test_cliente_publicado_sem_numero_e_aceito(self):
        # Reproduz o executavel 1.2.1 publicado: nunca enviou o campo "numero".
        participante = self._participante_em_pergunta()
        registrar = self._rodar(participante, {"tipo": "resposta", "indice": 1})

        self.assertEqual(participante.resposta_atual, 1)
        self._assert_persistiu_resposta_correta(registrar)

    def test_cliente_novo_com_numero_correto_e_aceito(self):
        participante = self._participante_em_pergunta()
        registrar = self._rodar(participante, {"tipo": "resposta", "indice": 1, "numero": 1})

        self.assertEqual(participante.resposta_atual, 1)
        self._assert_persistiu_resposta_correta(registrar)

    def test_numero_de_outra_pergunta_e_rejeitado(self):
        # So passa a ser possivel quando o cliente ja manda "numero"; sem o campo
        # (cliente antigo) nao ha como o backend saber a qual pergunta a resposta
        # atrasada pertencia, e por isso ele confia no controle de fase/prazo abaixo.
        participante = self._participante_em_pergunta()
        registrar = self._rodar(participante, {"tipo": "resposta", "indice": 1, "numero": 2})

        self.assertIsNone(participante.resposta_atual)
        registrar.assert_not_called()

    def test_rejeita_resposta_fora_da_fase_pergunta(self):
        participante = self._participante_em_pergunta()
        self.sessao.fase = "resultado"
        registrar = self._rodar(participante, {"tipo": "resposta", "indice": 1})

        self.assertIsNone(participante.resposta_atual)
        registrar.assert_not_called()

    def test_resposta_apos_prazo_nao_e_persistida(self):
        participante = self._participante_em_pergunta()
        self.sessao.questao_iniciada_em = time.monotonic() - 31
        registrar = self._rodar(participante, {"tipo": "resposta", "indice": 1})

        self.assertIsNone(participante.resposta_atual)
        registrar.assert_not_called()

    def test_indice_invalido_nao_consome_resposta_valida(self):
        participante = self._participante_em_pergunta()
        invalidas = [
            {"tipo": "resposta", "indice": indice}
            for indice in (-1, 2, "1", 1.5, True, None)
        ]
        registrar = self._rodar(
            participante, *invalidas, {"tipo": "resposta", "indice": 1}, {"tipo": "resposta", "indice": 0},
        )

        self.assertEqual(participante.resposta_atual, 1)
        self._assert_persistiu_resposta_correta(registrar)


if __name__ == "__main__":
    unittest.main()
