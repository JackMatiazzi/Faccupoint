from decimal import Decimal, InvalidOperation


def ler_pontos(texto) -> float:
    try:
        valor = Decimal(str(texto).strip().replace(",", "."))
        if not valor.is_finite() or not Decimal("0.01") <= valor <= 100:
            raise ValueError
        if valor != valor.quantize(Decimal("0.01")):
            raise ValueError
        return float(valor)
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("Informe de 0,01 a 100 pontos, com no máximo duas casas decimais.") from None


def formatar_pontos(valor) -> str:
    return format(Decimal(str(valor)).normalize(), "f").replace(".", ",")
