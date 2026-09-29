import re


def normalizar_docente(nome: str, email: str, pin: str | None, *, novo: bool) -> tuple[str, str]:
    nome = nome.strip()
    email = email.strip().lower()
    if not nome:
        raise ValueError("Nome não pode ser vazio.")
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise ValueError("Email inválido.")
    if (novo or pin not in (None, "")) and (not isinstance(pin, str) or not re.fullmatch(r"[0-9]{4}", pin)):
        raise ValueError("PIN deve ter exatamente 4 dígitos.")
    return nome, email
