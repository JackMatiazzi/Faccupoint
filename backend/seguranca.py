from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time

_ITERACOES = 100_000
_TOKEN_TTL_SEGUNDOS = 8 * 60 * 60


def gerar_hash_pin(pin: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"), salt, _ITERACOES)
    return f"pbkdf2_sha256${_ITERACOES}${salt.hex()}${dk.hex()}"


def verificar_pin(pin: str, hash_armazenado: str) -> bool:
    try:
        algo, iteracoes, salt_hex, hash_hex = hash_armazenado.split("$", 3)
        if algo != "pbkdf2_sha256":
            return False
        salt = bytes.fromhex(salt_hex)
        esperado = bytes.fromhex(hash_hex)
        dk = hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"), salt, int(iteracoes))
        return secrets.compare_digest(dk, esperado)
    except (ValueError, AttributeError):
        return False


def _chave_token() -> bytes:
    segredo = os.getenv("SECRET_KEY", "REDACTED")
    return segredo.encode("utf-8")


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def gerar_token_docente(id_docente: int, email: str, papel: str) -> str:
    payload = {
        "id_docente": id_docente,
        "email": email,
        "papel": papel,
        "exp": int(time.time()) + _TOKEN_TTL_SEGUNDOS,
    }
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    assinatura = hmac.new(_chave_token(), payload_b64.encode("ascii"), hashlib.sha256).digest()
    return f"{payload_b64}.{_b64url_encode(assinatura)}"


def verificar_token_docente(token: str) -> dict | None:
    try:
        payload_b64, assinatura_b64 = token.split(".", 1)
        assinatura = _b64url_decode(assinatura_b64)
        esperada = hmac.new(_chave_token(), payload_b64.encode("ascii"), hashlib.sha256).digest()
        if not hmac.compare_digest(assinatura, esperada):
            return None
        payload = json.loads(_b64url_decode(payload_b64))
        if int(payload.get("exp", 0)) < int(time.time()):
            return None
        return payload
    except (ValueError, TypeError, json.JSONDecodeError):
        return None
