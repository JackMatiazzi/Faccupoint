import asyncio
import base64
import hashlib
import hmac
import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from fastapi import WebSocketDisconnect
from backend.adaptadores.entrada.tempo_real import rotas
from backend.infraestrutura import seguranca


class SegurancaConexoesTest(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {'SECRET_KEY': 'somente-teste-conexoes'})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.docente = (20, 'Prof', 'p@example.test', 'prof', False, 'hash-atual')
        self.token = seguranca.gerar_token_docente(20, self.docente[2], 'prof', self.docente[5])
        self.codigo = 'ABC234'
        self.sessao = rotas.armazenamento_sessoes_ativas.criar(
            codigo=self.codigo, id_sessao=10, id_docente=20, id_quiz=30,
            perguntas=[{
                'id_pergunta': 40, 'enunciado': 'Quanto e 2 + 2?',
                'alternativas': [
                    {'id': 1, 'texto': '3', 'correta': False},
                    {'id': 2, 'texto': '4', 'correta': True},
                ],
            }],
            tempo_questao=30,
        )
        self.addCleanup(rotas.armazenamento_sessoes_ativas.remover, self.codigo)

    def _participante_sem_resposta(self):
        participante = rotas.Participante(
            apelido='Ana', ws=None, id_participante=99,
            token_reconexao='token-local-de-teste', pontos=2,
        )
        self.sessao.participantes['Ana'] = participante
        self.sessao.status = 'rodando'
        self.sessao.fase = 'resultado'
        self.sessao.questao_atual = 0
        self.sessao.ultimo_resultado = {
            'tipo': 'resultado', 'indice_correto': 1,
            'indices_corretos': [1], 'contagem': {},
            'placar': [{'apelido': 'Ana', 'pontos': 2}],
        }
        return participante

    def test_revogacao_antes_de_envio_sensivel(self):
        for docente, expirado in [(None, False), ((*self.docente[:5], 'outro-hash'), False), (self.docente, True)]:
            with self.subTest(docente=docente, expirado=expirado):
                ws = AsyncMock()
                ws._faccupoint_token = self.token
                sessao = SimpleNamespace(professor_ws=ws, id_docente=20, codigo='ABC234', status='rodando')
                with patch.object(rotas, 'buscar_docente_por_id', return_value=docente), patch.object(
                    seguranca.time, 'time', return_value=10**12 if expirado else 1
                ):
                    asyncio.run(rotas._enviar_professor(sessao, {'tipo': 'resultado_professor', 'indices_corretos': [1]}))
                ws.send_json.assert_not_awaited()
                ws.close.assert_awaited_once_with(code=4008)
                self.assertIsNone(sessao.professor_ws)

    def test_professor_ocioso_e_revogado_sem_esperar_broadcast(self):
        ws = AsyncMock()
        ws.receive_text.side_effect = [json.dumps({'token': self.token}), asyncio.TimeoutError()]
        sessao = SimpleNamespace(professor_ws=None, id_docente=20, codigo='ABC234', status='rodando')
        with patch.object(rotas, 'obter_sessao', return_value=sessao), patch.object(
            rotas, 'buscar_docente_por_id', side_effect=[self.docente, self.docente, None]
        ):
            asyncio.run(rotas.ws_professor(ws, 'ABC234'))
        ws.close.assert_awaited_once_with(code=4008)
        self.assertIsNone(sessao.professor_ws)

    def test_professor_substituido_nao_apaga_conexao_nova(self):
        antigo, novo, terceiro = AsyncMock(), AsyncMock(), AsyncMock()
        sessao = SimpleNamespace(professor_ws=antigo, id_docente=20, codigo='ABC234', status='rodando')
        calls = 0
        async def receive():
            nonlocal calls
            calls += 1
            if calls == 1:
                return json.dumps({'token': self.token})
            sessao.professor_ws = terceiro
            raise WebSocketDisconnect()
        novo.receive_text.side_effect = receive
        with patch.object(rotas, 'obter_sessao', return_value=sessao), patch.object(rotas, 'buscar_docente_por_id', return_value=self.docente):
            asyncio.run(rotas.ws_professor(novo, 'ABC234'))
        antigo.close.assert_awaited_once()
        self.assertIs(sessao.professor_ws, terceiro)

    def test_reconexao_aluno_fecha_socket_antigo(self):
        antigo, novo = AsyncMock(), AsyncMock()
        p = rotas.Participante('Ana', antigo, token_reconexao='teste')
        sessao = SimpleNamespace(participantes={'Ana': p}, _lock=asyncio.Lock(), status='lobby', professor_ws=None)
        novo.receive_text.side_effect = [json.dumps({'apelido': 'Ana', 'token_reconexao': 'teste'}), WebSocketDisconnect()]
        with patch.object(rotas, 'obter_sessao', return_value=sessao), patch.object(rotas, '_restaurar_estado_aluno', new_callable=AsyncMock):
            asyncio.run(rotas.ws_aluno(novo, 'ABC234'))
        antigo.close.assert_awaited_once()

    def test_token_malformado_ou_payload_nao_objeto_rejeitado(self):
        def assinar(payload):
            body = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
            sig = hmac.new(os.environ['SECRET_KEY'].encode(), body.encode(), hashlib.sha256).digest()
            return body + '.' + base64.urlsafe_b64encode(sig).decode().rstrip('=')
        for token in [None, 1, 'x'*4097, 'nao.ascii\u2603', assinar([]), assinar(None), assinar({'exp': float('inf'), 'id_docente':20})]:
            with self.subTest(token_type=type(token).__name__):
                self.assertIsNone(seguranca.verificar_token_docente(token))

    def test_websocket_professor_rejeita_token_anterior_a_troca_pin(self):
        docente = (20, 'Professor', 'prof@exemplo.test', 'prof', False, 'hash-novo')
        token_antigo = seguranca.gerar_token_docente(20, docente[2], 'prof', 'hash-antigo')
        ws = AsyncMock()
        ws.receive_text.side_effect = [json.dumps({'token': token_antigo})]
        with patch.object(rotas, 'buscar_docente_por_id', return_value=docente):
            asyncio.run(rotas.ws_professor(ws, self.codigo))
        ws.close.assert_awaited_once_with(code=4008)
        self.assertIsNone(self.sessao.professor_ws)

    def test_professor_com_token_atual_conecta_e_pin_provisorio_nao(self):
        token = seguranca.gerar_token_docente(20, self.docente[2], 'prof', 'hash-atual')
        for provisorio in (False, True):
            with self.subTest(provisorio=provisorio):
                docente = (20, 'Professor', 'prof@exemplo.test', 'prof', provisorio, 'hash-atual')
                self.sessao.professor_ws = None
                ws = AsyncMock()
                ws.receive_text.side_effect = [json.dumps({'token': token}), WebSocketDisconnect(code=1000)]
                with patch.object(rotas, 'buscar_docente_por_id', return_value=docente):
                    asyncio.run(rotas.ws_professor(ws, self.codigo))
                if provisorio:
                    ws.close.assert_awaited_once_with(code=4008)
                else:
                    self.assertEqual(ws.send_json.call_args_list[0].args[0]['tipo'], 'conectado')

    def test_reconexao_nao_expoe_gabarito_a_quem_nao_respondeu(self):
        participante = self._participante_sem_resposta()
        ws = AsyncMock()
        asyncio.run(rotas._restaurar_estado_aluno(ws, self.sessao, participante))
        resultado = ws.send_json.call_args.args[0]
        self.assertIsNone(resultado['sua_resposta'])
        self.assertNotIn('indice_correto', resultado)
        self.assertNotIn('indices_corretos', resultado)

    def test_reconexao_preserva_gabarito_para_quem_respondeu(self):
        participante = self._participante_sem_resposta()
        participante.resposta_atual = 1
        ws = AsyncMock()
        asyncio.run(rotas._restaurar_estado_aluno(ws, self.sessao, participante))
        resultado = ws.send_json.call_args.args[0]
        self.assertEqual(resultado['indices_corretos'], [1])
        self.assertTrue(resultado['acertou'])

    def test_mensagens_invalidas_de_identificacao_sao_rejeitadas(self):
        for dados in ([], None, {'apelido': 123}, {'apelido': 'Ana', 'token_reconexao': []}):
            with self.subTest(dados=dados):
                ws = AsyncMock()
                ws.receive_text.return_value = json.dumps(dados)
                asyncio.run(rotas.ws_aluno(ws, self.codigo))
                self.assertEqual(ws.send_json.call_args.args[0]['tipo'], 'erro')
                ws.close.assert_awaited_once()
        for dados in ([], None, {'token': 123}):
            with self.subTest(professor=dados):
                ws = AsyncMock()
                ws.receive_text.return_value = json.dumps(dados)
                asyncio.run(rotas.ws_professor(ws, self.codigo))
                ws.close.assert_awaited_once_with(code=4008)

    def test_entradas_simultaneas_com_mesmo_apelido_registram_uma_vez(self):
        async def executar():
            gravando = asyncio.Event()
            liberar = asyncio.Event()
            segunda_conectada = asyncio.Event()

            async def gravar(funcao, *args):
                self.assertIs(funcao, rotas.registrar_participante_sessao)
                gravando.set()
                await liberar.wait()
                return 99

            primeira, segunda = AsyncMock(), AsyncMock()
            segunda.accept.side_effect = lambda: segunda_conectada.set()
            for ws in (primeira, segunda):
                ws.receive_text.side_effect = [json.dumps({'apelido': 'Ana'}), WebSocketDisconnect(code=1000)]
            with patch.object(rotas.asyncio, 'to_thread', side_effect=gravar) as registrar:
                tarefa1 = asyncio.create_task(rotas.ws_aluno(primeira, self.codigo))
                await asyncio.wait_for(gravando.wait(), timeout=2)
                tarefa2 = asyncio.create_task(rotas.ws_aluno(segunda, self.codigo))
                try:
                    await asyncio.wait_for(segunda_conectada.wait(), timeout=2)
                    liberar.set()
                    await asyncio.wait_for(asyncio.gather(tarefa1, tarefa2), timeout=2)
                finally:
                    liberar.set()
                    for tarefa in (tarefa1, tarefa2):
                        if not tarefa.done():
                            tarefa.cancel()
                    await asyncio.gather(tarefa1, tarefa2, return_exceptions=True)
                registrar.assert_awaited_once()
            self.assertEqual(list(self.sessao.participantes), ['Ana'])
            self.assertEqual(segunda.send_json.call_args.args[0]['tipo'], 'erro')

        asyncio.run(executar())
