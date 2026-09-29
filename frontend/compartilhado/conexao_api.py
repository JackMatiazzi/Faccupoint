"""Destinos de rede definidos exclusivamente pelo operador do servidor."""

import os
import re
from urllib.parse import urlsplit


def backend_confiavel() -> str:
    url = os.environ.get("API_URL", "http://127.0.0.1:8000").strip()
    partes = urlsplit(url)
    if (partes.scheme not in ("http", "https") or not partes.hostname
            or partes.username is not None or partes.password is not None
            or partes.query or partes.fragment or partes.path not in ("", "/")):
        raise ValueError("API_URL deve ser a origem HTTP(S) do backend")
    host = partes.hostname.lower()
    if ":" in host:
        host = f"[{host}]"
    porta = partes.port
    if porta is not None and porta != (443 if partes.scheme == "https" else 80):
        host += f":{porta}"
    return f"{partes.scheme}://{host}"


def codigo_valido(codigo) -> bool:
    return isinstance(codigo, str) and re.fullmatch(r"[A-HJ-NP-Z2-9]{6}", codigo) is not None


def websocket_aluno(codigo: str) -> str:
    if not codigo_valido(codigo):
        raise ValueError("Codigo invalido")
    return backend_confiavel().replace("http", "ws", 1) + f"/ws/aluno/{codigo}"


def sessao_compativel(salva, backend: str) -> bool:
    return (isinstance(salva, dict) and salva.get("backend") == backend
            and codigo_valido(salva.get("codigo"))
            and isinstance(salva.get("apelido"), str)
            and 0 < len(salva["apelido"]) <= 20
            and isinstance(salva.get("token_reconexao"), str))
