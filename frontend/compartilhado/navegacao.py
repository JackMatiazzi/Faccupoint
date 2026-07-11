from urllib.parse import parse_qs, urlparse


def ir_para(page, rota: str) -> None:
    page._rota_esperada = rota
    page.go(rota)


def query_valor(page, nome: str) -> str:
    query = getattr(page, "query", None)
    if query is not None:
        try:
            valor = query.get(nome)
            if valor:
                return str(valor)
        except (AttributeError, KeyError):
            pass

    for origem in (getattr(page, "route", ""), getattr(page, "url", "")):
        valores = parse_qs(urlparse(origem or "").query).get(nome)
        if valores:
            return valores[0]
    return ""
