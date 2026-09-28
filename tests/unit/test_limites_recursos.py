import asyncio
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
from fastapi import HTTPException
from backend.adaptadores.entrada.http import rotas
from backend.infraestrutura.limites import Janela, LimitesMiddleware


class TestLimites(unittest.TestCase):
    def test_login_reserva_atomicamente(self):
        email = 'concorrencia@example.test'
        rotas._tentativas_login.pop(email, None)
        def tentar(_):
            try:
                rotas._checar_rate_limit_login(email)
                return True
            except HTTPException:
                return False
        try:
            with ThreadPoolExecutor(max_workers=20) as pool:
                self.assertEqual(sum(pool.map(tentar, range(40))), 5)
        finally:
            rotas._tentativas_login.pop(email, None)

    def test_capacidade_nao_expulsa_limites_ativos_e_expira(self):
        janela = Janela(1, segundos=60, capacidade=1)
        with patch('backend.infraestrutura.limites.time.monotonic', return_value=100):
            self.assertTrue(janela.permitir('a'))
            self.assertFalse(janela.permitir('b'))
            self.assertFalse(janela.permitir('a'))
        with patch('backend.infraestrutura.limites.time.monotonic', return_value=161):
            self.assertTrue(janela.permitir('b'))
            self.assertEqual(list(janela.dados), ['b'])

    def test_body_chunked_rejeitado_antes_da_aplicacao(self):
        async def executar():
            chamado = []
            async def app(*args): chamado.append(True)
            middleware = LimitesMiddleware(app)
            middleware.max_http = 4
            eventos = iter([{'type':'http.request','body': b'123','more_body':True},
                            {'type':'http.request','body':b'45','more_body':False}])
            async def receive(): return next(eventos)
            saida = []
            async def send(msg): saida.append(msg)
            await middleware({'type':'http','path':'/','client':('ip',1)}, receive, send)
            self.assertFalse(chamado)
            self.assertEqual(saida[0]['status'], 413)
        asyncio.run(executar())

    def test_ws_mensagem_grande_fecha_e_libera_quota(self):
        async def executar():
            async def app(scope, receive, send):
                await receive()
                await send({'type':'websocket.accept'})
                self.assertEqual((await receive())['type'], 'websocket.disconnect')
            middleware = LimitesMiddleware(app)
            middleware.max_ws = 2
            eventos = iter([{'type':'websocket.connect'}, {'type':'websocket.receive','text':'abc'}])
            async def receive(): return next(eventos)
            saida=[]
            async def send(msg): saida.append(msg)
            await middleware({'type':'websocket','client':('ip',1)}, receive, send)
            self.assertEqual(saida[-1]['code'], 1009)
            self.assertEqual(middleware.total, 0)
            self.assertEqual(middleware.ativos, {})
        asyncio.run(executar())

    def test_auth_por_ip_independe_do_email(self):
        from fastapi.testclient import TestClient
        from backend.main import create_app
        with patch.dict('os.environ', {'AUTH_REQUESTS_PER_MINUTE': '1'}):
            application = create_app(run_migrations=False)
            application.middleware_stack = application.build_middleware_stack()
            client = TestClient(application)
        with patch.object(rotas, 'buscar_docente_por_email', return_value=None):
            a = client.post('/auth/login', json={'email':'limite-a@test.local', 'pin':'1111'})
            b = client.post('/auth/login', json={'email':'limite-b@test.local', 'pin':'1111'},
                            headers={'X-Forwarded-For':'outro-ip'})
        self.assertEqual(a.status_code, 401)
        self.assertEqual(b.status_code, 429)
        rotas._tentativas_login.pop('limite-a@test.local', None)
    def test_content_length_rejeita_sem_receber_corpo(self):
        async def executar():
            async def proibido(*args): self.fail('nao deve executar')
            middleware = LimitesMiddleware(proibido)
            saida=[]
            async def send(msg): saida.append(msg)
            await middleware({'type':'http','path':'/','headers':[(b'content-length', b'65537')]}, proibido, send)
            self.assertEqual(saida[0]['status'], 413)
        asyncio.run(executar())

    def test_corpo_lento_expira(self):
        async def executar():
            async def app(*args): self.fail('nao deve executar')
            middleware = LimitesMiddleware(app)
            middleware.body_timeout = 0.01
            async def receive(): await asyncio.Event().wait()
            saida=[]
            async def send(msg): saida.append(msg)
            await middleware({'type':'http','path':'/'}, receive, send)
            self.assertEqual(saida[0]['status'], 408)
        asyncio.run(executar())

    def test_ws_binario_rejeitado_e_liberado(self):
        async def executar():
            async def app(scope, receive, send):
                self.assertEqual((await receive())['type'], 'websocket.disconnect')
            middleware = LimitesMiddleware(app)
            async def receive(): return {'type':'websocket.receive','bytes':b''}
            saida=[]
            async def send(msg): saida.append(msg)
            await middleware({'type':'websocket'}, receive, send)
            self.assertEqual(saida[0]['code'], 1003)
            self.assertEqual(middleware.total, 0)
        asyncio.run(executar())

    def test_http_quota_global_independe_ip(self):
        async def executar():
            async def app(scope, receive, send):
                await send({'type':'http.response.start','status':200})
            middleware = LimitesMiddleware(app)
            middleware.http_global = Janela(1)
            async def receive(): return {'type':'http.request','body':b''}
            saida=[]
            async def send(msg): saida.append(msg)
            for ip in ('primeiro', 'segundo'):
                await middleware({'type':'http','path':'/','client':(ip,1)}, receive, send)
            self.assertEqual([m['status'] for m in saida if 'status' in m], [200,429])
        asyncio.run(executar())
