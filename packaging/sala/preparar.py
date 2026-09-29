"""Gera apenas credenciais locais de teste; nunca le o .env do projeto."""
import secrets
from pathlib import Path

root = Path(__file__).resolve().parents[2] / ".local" / "sala-secrets"
root.mkdir(parents=True, exist_ok=True)
for nome in ("db_password", "db_admin_password", "token_key", "admin_pin"):
    destino = root / nome
    if not destino.exists():
        valor = f"{secrets.randbelow(10000):04d}" if nome == "admin_pin" else secrets.token_hex(32)
        destino.write_text(valor, encoding="utf-8")
print("Segredos locais preparados. Login: professor@teste.invalid; PIN em .local/sala-secrets/admin_pin")
