
import os
import re
import json
import base64
import logging
import smtplib
import urllib.error
import urllib.request
from csv import writer
from email.message import EmailMessage
from io import StringIO

from backend.adaptadores.saida.postgres.repositorio import buscar_relatorio_sessao
from backend.infraestrutura.configuracao import load_environment

load_environment()
logger = logging.getLogger(__name__)


def _resend_api_key() -> str:
    return os.getenv("RESEND_API_KEY", "").strip() or os.getenv("resend", "").strip()


def _remetente_padrao() -> str:
    return (
        os.getenv("EMAIL_FROM", "").strip()
        or os.getenv("RESEND_FROM", "").strip()
        or os.getenv("EMAIL_USER", "").strip()
    )


def _resend_configurado() -> bool:
    return bool(_resend_api_key() and _remetente_padrao())


def _config_email() -> dict[str, str | int] | None:
    host = os.getenv("EMAIL_HOST", "").strip()
    usuario = os.getenv("EMAIL_USER", "").strip()
    senha = os.getenv("EMAIL_PASSWORD", "").strip()
    remetente = _remetente_padrao()
    porta = int(os.getenv("EMAIL_PORT", "587"))

    if not host or not usuario or not senha or not remetente:
        return None

    return {
        "host": host,
        "porta": porta,
        "usuario": usuario,
        "senha": senha,
        "remetente": remetente,
    }


def _campos_email_ausentes() -> list[str]:
    if _resend_api_key():
        campos = {
            "EMAIL_FROM ou RESEND_FROM": _remetente_padrao(),
        }
        return [nome for nome, valor in campos.items() if not valor]

    campos = {
        "EMAIL_HOST": os.getenv("EMAIL_HOST", "").strip(),
        "EMAIL_USER": os.getenv("EMAIL_USER", "").strip(),
        "EMAIL_PASSWORD": os.getenv("EMAIL_PASSWORD", "").strip(),
        "EMAIL_FROM": os.getenv("EMAIL_FROM", os.getenv("EMAIL_USER", "")).strip(),
    }
    return [nome for nome, valor in campos.items() if not valor]


def _enviar_por_smtp(
    *,
    destino: str,
    assunto: str,
    texto: str,
    anexo_nome: str | None = None,
    anexo_conteudo: bytes | None = None,
) -> None:
    config = _config_email()
    if config is None:
        ausentes = ", ".join(_campos_email_ausentes())
        raise RuntimeError(f"email incompleto: {ausentes}")

    msg = EmailMessage()
    msg["Subject"] = assunto
    msg["From"] = str(config["remetente"])
    msg["To"] = destino
    msg.set_content(texto)
    if anexo_nome and anexo_conteudo is not None:
        msg.add_attachment(
            anexo_conteudo,
            maintype="text",
            subtype="csv",
            filename=anexo_nome,
        )

    import ssl as _ssl
    with smtplib.SMTP(str(config["host"]), int(config["porta"]), timeout=15) as smtp:
        if os.getenv("EMAIL_STARTTLS", "1") == "1":
            smtp.starttls(context=_ssl.create_default_context())
        smtp.login(str(config["usuario"]), str(config["senha"]))
        smtp.send_message(msg)


def _enviar_por_resend(
    *,
    destino: str,
    assunto: str,
    texto: str,
    anexo_nome: str | None = None,
    anexo_conteudo: bytes | None = None,
) -> None:
    api_key = _resend_api_key()
    remetente = _remetente_padrao()
    if not api_key or not remetente:
        ausentes = ", ".join(_campos_email_ausentes())
        raise RuntimeError(f"email incompleto: {ausentes}")

    payload: dict[str, object] = {
        "from": remetente,
        "to": [destino],
        "subject": assunto,
        "text": texto,
    }
    if anexo_nome and anexo_conteudo is not None:
        payload["attachments"] = [
            {
                "filename": anexo_nome,
                "content": base64.b64encode(anexo_conteudo).decode("ascii"),
            }
        ]

    request = urllib.request.Request(
        "https://api.resend.com/emails",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "FaccuPoint/1.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            if response.status >= 400:
                raise RuntimeError(f"resend retornou HTTP {response.status}")
    except urllib.error.HTTPError as e:
        detalhe = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"resend retornou HTTP {e.code}: {detalhe}") from e


def _enviar_email(
    *,
    destino: str,
    assunto: str,
    texto: str,
    anexo_nome: str | None = None,
    anexo_conteudo: bytes | None = None,
) -> None:
    if _resend_configurado():
        try:
            _enviar_por_resend(
                destino=destino,
                assunto=assunto,
                texto=texto,
                anexo_nome=anexo_nome,
                anexo_conteudo=anexo_conteudo,
            )
            return
        except Exception:
            if _config_email() is None:
                raise
            logger.exception("falha ao enviar via resend, tentando smtp como fallback")

    _enviar_por_smtp(
        destino=destino,
        assunto=assunto,
        texto=texto,
        anexo_nome=anexo_nome,
        anexo_conteudo=anexo_conteudo,
    )


def enviar_email_teste(destino: str) -> None:
    _enviar_email(
        destino=destino,
        assunto="Teste de envio - FaccuPoint",
        texto="Se voce recebeu este e-mail, o envio do FaccuPoint esta configurado corretamente.\n",
    )


def _montar_texto(relatorio: dict) -> str:
    respostas_validas = [r for r in relatorio["respostas"] if r["ordem"] is not None]
    n_alunos = len({r["aluno"] for r in relatorio["respostas"]})
    total = len(respostas_validas)
    acertos = sum(1 for r in respostas_validas if r["acertou"])
    aproveitamento = (acertos / total * 100) if total else 0
    n_alunos_str = f"{n_alunos} aluno" if n_alunos == 1 else f"{n_alunos} alunos"

    linhas = [
        f"Aula encerrada: {relatorio['quiz']}",
        "",
        f"Professor: {relatorio['professor']}",
        f"Participantes: {n_alunos_str}",
        f"Aproveitamento geral: {aproveitamento:.0f}%",
        "",
        "Os detalhes completos estão no CSV em anexo.",
    ]

    return "\n".join(linhas) + "\n"


def _formatar_data_hora(valor) -> str:
    if not valor:
        return ""
    return valor.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def _milissegundos_do_dia(valor) -> int | str:
    if not valor:
        return ""
    return (
        valor.hour * 60 * 60 * 1000
        + valor.minute * 60 * 1000
        + valor.second * 1000
        + valor.microsecond // 1000
    )


def _montar_csv(relatorio: dict) -> str:
    arquivo = StringIO()
    csv = writer(arquivo, delimiter=";")
    csv.writerow([
        "sala",
        "quiz",
        "professor",
        "aluno",
        "numero_pergunta",
        "pergunta",
        "resposta_do_aluno",
        "resposta_correta",
        "resultado",
        "respondida_em",
        "respondida_em_ms",
    ])

    for r in relatorio["respostas"]:
        resultado = ""
        if not r["resposta"]:
            resultado = "nao respondeu" if r["acertou"] is not None else ""
        elif r["acertou"] is not None:
            resultado = "acertou" if r["acertou"] else "errou"
        csv.writerow([
            relatorio["codigo"],
            relatorio["quiz"],
            relatorio["professor"],
            r["aluno"],
            r["ordem"] or "",
            r["pergunta"] or "",
            r["resposta"] or "",
            r["correta"] or "",
            resultado,
            _formatar_data_hora(r["respondida_em"]),
            _milissegundos_do_dia(r["respondida_em"]),
        ])

    return arquivo.getvalue()


def _nome_arquivo_csv(relatorio: dict) -> str:
    quiz = re.sub(r"[^a-zA-Z0-9]+", "_", relatorio["quiz"].strip()).strip("_").lower()
    quiz = quiz or "quiz"
    criada_em = relatorio.get("criada_em")
    data = criada_em.strftime("%Y-%m-%d") if criada_em else "sem_data"
    return f"resultado_{quiz}_{data}.csv"


def enviar_relatorio_sessao(id_sessao: int) -> None:
    if not _resend_configurado() and _config_email() is None:
        logger.warning("email nao configurado")
        return

    relatorio = buscar_relatorio_sessao(id_sessao)
    if relatorio is None:
        logger.warning("relatorio da sala %s nao encontrado", id_sessao)
        return

    destino = relatorio["email_professor"]
    codigo = relatorio["codigo"]

    try:
        _enviar_email(
            destino=destino,
            assunto=f"Resultado: {relatorio['quiz']}",
            texto=_montar_texto(relatorio),
            anexo_nome=_nome_arquivo_csv(relatorio),
            anexo_conteudo=_montar_csv(relatorio).encode("utf-8-sig"),
        )
        logger.info("email da sala %s enviado", codigo)
    except Exception:
        logger.exception("falha ao enviar email da sala %s para %s", codigo, destino)
