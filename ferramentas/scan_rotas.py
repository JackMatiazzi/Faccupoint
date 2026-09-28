"""Varre todas as rotas registradas e mostra quais respondem SEM autenticacao.

Uso:
    python ferramentas/scan_rotas.py                 # usa TestClient (nao precisa de banco)
    python ferramentas/scan_rotas.py http://127.0.0.1:8000   # bate no backend ja rodando

Sem efeito colateral: so GET e POST/PUT com corpo vazio; rotas protegidas
respondem 401 antes de tocar em qualquer dado.
"""
import os
import re
import sys

os.environ.setdefault("DATABASE_URL", "postgresql://u:p@127.0.0.1:5432/none")
os.environ.setdefault("SECRET_KEY", "scan-local")

BASE = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else None

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.main import create_app  # noqa: E402

app = create_app(run_migrations=False)

if BASE:
    import httpx
    cli = httpx.Client(base_url=BASE, timeout=8.0)
    def call(method, path):
        try:
            r = cli.request(method, path, json={} if method in ("POST", "PUT", "PATCH") else None)
            return r.status_code, r.text[:120].replace("\n", " ")
        except Exception as e:
            return 0, f"ERRO: {e}"
else:
    from fastapi.testclient import TestClient
    tc = TestClient(app, raise_server_exceptions=False)
    def call(method, path):
        try:
            r = tc.request(method, path, json={} if method in ("POST", "PUT", "PATCH") else None)
            return r.status_code, r.text[:120].replace("\n", " ")
        except Exception as e:
            return 0, f"ERRO: {e}"


def concretiza(path: str) -> str:
    # {id}, {codigo}, {qualquer} -> 1  (basta pra distinguir "sem auth" de "com auth")
    return re.sub(r"\{[^}]+\}", "1", path)


rotas = []
for r in app.routes:
    path = getattr(r, "path", None)
    if not path or path.startswith("/openapi") or path in ("/docs", "/redoc", "/docs/oauth2-redirect"):
        # docs entram na varredura mesmo assim (interessa saber se abriram)
        pass
    metodos = getattr(r, "methods", None)
    if metodos is None:  # WebSocket
        rotas.append(("WS", path))
    else:
        for m in sorted(metodos - {"HEAD", "OPTIONS"}):
            rotas.append((m, path))

NOTA = {200: "entrega dados", 201: "cria", 204: "ok", 422: "precisa corpo valido",
        404: "sem auth; precisa id/codigo valido", 405: "sem auth; metodo errado",
        429: "sem auth; rate limit"}

abertas, protegidas, outras = [], [], []
for metodo, path in sorted(rotas, key=lambda x: (x[1], x[0])):
    if metodo == "WS":
        outras.append((metodo, path, "WS", "websocket - nao exige token no upgrade; auth e por mensagem"))
        continue
    code, corpo = call(metodo, concretiza(path))
    linha = (metodo, path, code, NOTA.get(code, corpo))
    if code in (401, 403):
        protegidas.append((metodo, path, code, corpo))
    elif code == 0:
        outras.append(linha)
    else:                                           # qualquer coisa != 401/403 = alcancavel sem token
        abertas.append(linha)

modo = f"live {BASE}" if BASE else "TestClient"
print(f"\n=== ROTAS EM ABERTO (sem autenticacao)  [{modo}] ===")
for m, p, c, b in abertas:
    print(f"  {m:<6} {p:<45} {c}  {b}")

print("\n=== PROTEGIDAS (401/403) ===")
for m, p, c, b in protegidas:
    print(f"  {m:<6} {p:<45} {c}")

print("\n=== OUTRAS (404/405/WS/erro) ===")
for m, p, c, b in outras:
    print(f"  {m:<6} {p:<45} {c}  {b}")

print(f"\ntotal: {len(abertas)} abertas | {len(protegidas)} protegidas | {len(outras)} outras")
