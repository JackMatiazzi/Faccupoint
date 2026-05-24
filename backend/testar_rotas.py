"""
Rodar: python -m backend.testar_rotas
Requer o servidor fora do ar (usa TestClient interno, sem porta).
"""
from __future__ import annotations

import sys

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app, raise_server_exceptions=False)

_ok = 0
_falhas = 0


def checar(descricao: str, status_esperado: int, status_recebido: int, corpo: dict | None = None) -> None:
    global _ok, _falhas
    passou = status_recebido == status_esperado
    simbolo = "ok" if passou else "FALHOU"
    print(f"  [{simbolo}] {descricao} — esperado {status_esperado}, recebido {status_recebido}")
    if not passou and corpo:
        print(f"         detalhe: {corpo.get('detail', corpo)}")
    if passou:
        _ok += 1
    else:
        _falhas += 1


def _login(email: str, pin: str) -> tuple[int, str | None]:
    r = client.post("/auth/login", json={"email": email, "pin": pin})
    token = r.json().get("token") if r.status_code == 200 else None
    return r.status_code, token


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
print("\n=== health ===")
r = client.get("/health")
checar("GET /health", 200, r.status_code)

# ---------------------------------------------------------------------------
print("\n=== auth ===")
r = client.post("/auth/login", json={"email": "nao@existe.com", "pin": "0000"})
checar("login com credencial errada -> 401", 401, r.status_code, r.json())

r = client.post("/auth/login", json={"email": "", "pin": ""})
checar("login com campos vazios -> 401 ou 422", r.status_code in (401, 422) and r.status_code or 401, r.status_code)

# ---------------------------------------------------------------------------
print("\n=== rotas protegidas sem token ===")
r = client.get("/quizzes", params={"id_docente": 1})
checar("GET /quizzes sem token -> 401", 401, r.status_code, r.json())

r = client.post("/quizzes", json={"id_docente_proprietario": 1, "titulo": "x"})
checar("POST /quizzes sem token -> 401", 401, r.status_code, r.json())

r = client.post("/sessoes", json={"id_quiz": 1})
checar("POST /sessoes sem token -> 401", 401, r.status_code, r.json())

r = client.get("/docentes")
checar("GET /docentes sem token -> 401", 401, r.status_code, r.json())

# ---------------------------------------------------------------------------
print("\n=== token invalido ===")
headers_falsos = {"Authorization": "Bearer token.invalido"}
r = client.get("/quizzes", params={"id_docente": 1}, headers=headers_falsos)
checar("GET /quizzes com token falso -> 401", 401, r.status_code, r.json())

# ---------------------------------------------------------------------------
print("\n=== login real (lê credenciais do .env via banco) ===")
print("  (se não houver docente cadastrado no banco, esses testes vão falhar — é esperado)")

import os
from dotenv import load_dotenv
load_dotenv("backend/.env")

EMAIL_TESTE = os.getenv("EMAIL_TESTE", "")
PIN_TESTE   = os.getenv("PIN_TESTE", "")

if EMAIL_TESTE and PIN_TESTE:
    status, token = _login(EMAIL_TESTE, PIN_TESTE)
    checar(f"login com {EMAIL_TESTE} -> 200", 200, status)

    if token:
        r = client.get("/quizzes", params={"id_docente": 1}, headers=_auth(token))
        checar("GET /quizzes com token valido -> 200 ou 403", r.status_code in (200, 403) and r.status_code or 200, r.status_code)
else:
    print("  (sem EMAIL_TESTE/PIN_TESTE no .env — pulando testes autenticados)")
    print("  Adicione ao backend/.env:")
    print("    EMAIL_TESTE=seu@email.com")
    print("    PIN_TESTE=1234")

# ---------------------------------------------------------------------------
print(f"\n=== resultado: {_ok} ok, {_falhas} falha(s) ===\n")
if _falhas:
    sys.exit(1)
