_MAX_URL_MIDIA = 2048
_PRIVATE_PREFIXES = (
    "https://localhost",
    "https://127.",
    "https://10.",
    "https://192.168.",
    "https://172.16.",
    "https://172.17.",
    "https://172.18.",
    "https://172.19.",
    "https://172.2",
    "https://172.3",
)


def validar_link_midia(link: str | None) -> str | None:
    if not link:
        return None
    url = link.strip()
    if len(url) > _MAX_URL_MIDIA:
        raise ValueError("link_midia muito longo (max. 2048 caracteres).")
    if not url.startswith("https://"):
        raise ValueError("link_midia deve comecar com https://")
    if any(url.lower().startswith(prefixo) for prefixo in _PRIVATE_PREFIXES):
        raise ValueError("link_midia aponta para endereco interno nao permitido.")
    return url


def normalizar_pergunta(
    enunciado: str,
    alternativas: list[dict],
    link_midia: str | None,
) -> tuple[str, list[dict], str | None]:
    texto = enunciado.strip()
    alternativas_limpas = [
        {"texto": str(a.get("texto", "")).strip(), "correta": bool(a.get("correta"))}
        for a in alternativas
        if str(a.get("texto", "")).strip()
    ]
    if not texto or len(alternativas_limpas) < 2:
        raise ValueError("Preencha o enunciado e pelo menos duas alternativas.")
    if not any(a["correta"] for a in alternativas_limpas):
        raise ValueError("Marque pelo menos uma alternativa correta.")
    return texto, alternativas_limpas, validar_link_midia(link_midia)
