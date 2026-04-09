def normalizar_titulo(titulo: str) -> str:
    return " ".join(titulo.strip().lower().split())
