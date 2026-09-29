"""Per-process quotas. Multiple workers require a shared limiter at the proxy.
Peer address comes from ASGI; disable proxy-header trust for untrusted peers.
"""
import asyncio
import os
import threading
import time
from collections import deque


class Janela:
    def __init__(self, limite, segundos=60, capacidade=4096):
        self.limite, self.segundos, self.capacidade = limite, segundos, capacidade
        self.dados = {}
        self.lock = threading.Lock()

    def permitir(self, chave):
        agora = time.monotonic()
        with self.lock:
            for key in list(self.dados):
                fila = self.dados[key]
                while fila and fila[0] <= agora - self.segundos:
                    fila.popleft()
                if not fila:
                    del self.dados[key]
            if chave not in self.dados and len(self.dados) >= self.capacidade:
                return False
            fila = self.dados.setdefault(chave, deque())
            if len(fila) >= self.limite:
                return False
            fila.append(agora)
            return True


def _valor(nome, padrao):
    return max(1, int(os.getenv(nome, str(padrao))))


class LimitesMiddleware:
    def __init__(self, app):
        self.app = app
        self.http = Janela(_valor('HTTP_REQUESTS_PER_MINUTE', 3000))
        self.http_global = Janela(_valor('HTTP_GLOBAL_REQUESTS_PER_MINUTE', 10000), capacidade=1)
        self.body_timeout = _valor('HTTP_BODY_TIMEOUT_SECONDS', 15)
        self.allow_binary = os.getenv('WS_ALLOW_BINARY', '0') == '1'
        self.auth = Janela(_valor('AUTH_REQUESTS_PER_MINUTE', 120))
        self.aberturas = Janela(_valor('WS_CONNECTIONS_PER_MINUTE', 600))
        self.max_http = _valor('HTTP_MAX_BODY_BYTES', 65536)
        self.max_ws = _valor('WS_MAX_MESSAGE_BYTES', 16384)
        self.max_total = _valor('WS_MAX_CONNECTIONS', 1000)
        self.max_peer = _valor('WS_MAX_CONNECTIONS_PER_IP', 300)
        self.msg_limite = _valor('WS_MESSAGES_PER_MINUTE', 120)
        self.ativos = {}
        self.total = 0
        self.lock = threading.Lock()

    async def __call__(self, scope, receive, send):
        tipo = scope['type']
        if tipo not in ('http', 'websocket'):
            return await self.app(scope, receive, send)
        peer = (scope.get('client') or ('unknown',))[0]
        if tipo == 'http':
            async def rejeitar(status):
                headers = [(b'content-type', b'application/json')]
                if status == 429:
                    headers.append((b'retry-after', b'60'))
                await send({'type': 'http.response.start', 'status': status, 'headers': headers})
                await send({'type': 'http.response.body', 'body': b'{"detail":"limite de recursos excedido"}'})
            if not self.http_global.permitir('global') or not self.http.permitir(peer) or (scope['path'].startswith('/auth/') and not self.auth.permitir(peer)):
                return await rejeitar(429)
            for chave, valor in scope.get('headers', []):
                if chave.lower() == b'content-length':
                    try:
                        declarado = int(valor)
                    except ValueError:
                        return await rejeitar(400)
                    if declarado < 0:
                        return await rejeitar(400)
                    if declarado > self.max_http:
                        return await rejeitar(413)
            # One bounded buffer; empty frames cannot accumulate list overhead.
            dados = bytearray()
            prazo = time.monotonic() + self.body_timeout
            while True:
                restante = prazo - time.monotonic()
                if restante <= 0:
                    return await rejeitar(408)
                try:
                    mensagem = await asyncio.wait_for(receive(), timeout=restante)
                except asyncio.TimeoutError:
                    return await rejeitar(408)
                if mensagem['type'] == 'http.disconnect':
                    return
                parte = mensagem.get('body', b'')
                if len(dados) + len(parte) > self.max_http:
                    return await rejeitar(413)
                dados.extend(parte)
                if not mensagem.get('more_body', False):
                    break
            entregue = False
            async def corpo():
                nonlocal entregue
                if not entregue:
                    entregue = True
                    return {'type': 'http.request', 'body': bytes(dados), 'more_body': False}
                return await receive()
            return await self.app(scope, corpo, send)
        with self.lock:
            permitido = self.total < self.max_total and self.ativos.get(peer, 0) < self.max_peer
            if permitido:
                self.total += 1
                self.ativos[peer] = self.ativos.get(peer, 0) + 1
        if not permitido:
            return await send({'type': 'websocket.close', 'code': 1008})
        fechado = False
        mensagens = Janela(self.msg_limite, capacidade=1)
        async def receber():
            nonlocal fechado
            if fechado:
                return {'type': 'websocket.disconnect', 'code': 1008}
            msg = await receive()
            if msg['type'] == 'websocket.receive':
                if msg.get('bytes') is not None and not self.allow_binary:
                    fechado = True
                    await send({'type': 'websocket.close', 'code': 1003})
                    return {'type': 'websocket.disconnect', 'code': 1003}
                tamanho = len(msg.get('bytes') or b'') + len((msg.get('text') or '').encode('utf-8'))
                if tamanho > self.max_ws or not mensagens.permitir('conexao'):
                    fechado = True
                    await send({'type': 'websocket.close', 'code': 1009 if tamanho > self.max_ws else 1008})
                    return {'type': 'websocket.disconnect', 'code': 1008}
            return msg
        async def enviar(msg):
            if not fechado:
                await send(msg)
        try:
            if not self.aberturas.permitir(peer):
                return await send({'type': 'websocket.close', 'code': 1008})
            await self.app(scope, receber, enviar)
        finally:
            with self.lock:
                self.total -= 1
                self.ativos[peer] -= 1
                if not self.ativos[peer]:
                    del self.ativos[peer]
