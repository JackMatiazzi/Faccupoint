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
