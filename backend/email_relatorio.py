
import os
import re
import logging
import smtplib
from csv import writer
from email.message import EmailMessage
from io import StringIO

from dotenv import load_dotenv

from backend.banco import buscar_relatorio_sessao

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
logger = logging.getLogger(__name__)


def _config_email() -> dict[str, str | int] | None:
    host = os.getenv("EMAIL_HOST", "").strip()
    usuario = os.getenv("EMAIL_USER", "").strip()
    senha = os.getenv("EMAIL_PASSWORD", "").strip()
    remetente = os.getenv("EMAIL_FROM", usuario).strip()
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
        if r["acertou"] is not None:
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
    config = _config_email()
    if config is None:
        logger.warning("email nao configurado")
        return

    relatorio = buscar_relatorio_sessao(id_sessao)
    if relatorio is None:
        logger.warning("relatorio da sala %s nao encontrado", id_sessao)
        return

    destino = relatorio["email_professor"]
    codigo = relatorio["codigo"]

    msg = EmailMessage()
    msg["Subject"] = f"Resultado: {relatorio['quiz']}"
    msg["From"] = str(config["remetente"])
    msg["To"] = destino
    msg.set_content(_montar_texto(relatorio))
    msg.add_attachment(
        _montar_csv(relatorio).encode("utf-8-sig"),
        maintype="text",
        subtype="csv",
        filename=_nome_arquivo_csv(relatorio),
    )

    try:
        with smtplib.SMTP(str(config["host"]), int(config["porta"]), timeout=15) as smtp:
            if os.getenv("EMAIL_STARTTLS", "1") == "1":
                smtp.starttls()
            smtp.login(str(config["usuario"]), str(config["senha"]))
            smtp.send_message(msg)
        logger.info("email da sala %s enviado", codigo)
    except Exception:
        logger.exception("falha ao enviar email da sala %s para %s", codigo, destino)
