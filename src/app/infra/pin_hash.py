import hashlib
import secrets

_ITERATIONS = 100_000


def hash_pin(pin: str, iterations: int = _ITERATIONS) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        pin.encode("utf-8"),
        salt,
        iterations,
    )
    return f"pbkdf2_sha256${iterations}${salt.hex()}${dk.hex()}"


def verificar_pin(pin: str, pin_hash_armazenado: str) -> bool:
    try:
        algo, it_s, salt_hex, hash_hex = pin_hash_armazenado.split("$", 3)
        if algo != "pbkdf2_sha256":
            return False
        iterations = int(it_s)
        salt = bytes.fromhex(salt_hex)
        esperado = bytes.fromhex(hash_hex)
        dk = hashlib.pbkdf2_hmac(
            "sha256",
            pin.encode("utf-8"),
            salt,
            iterations,
        )
        return secrets.compare_digest(dk, esperado)
    except (ValueError, AttributeError):
        return False
