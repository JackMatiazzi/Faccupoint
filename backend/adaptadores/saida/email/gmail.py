"""Envio pelo Gmail via HTTPS, com autorizacao OAuth da conta remetente."""

import base64
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from email.message import EmailMessage


def _post_json(url: str, data: bytes, headers: dict) -> dict:
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        # Nao registrar respostas OAuth, tokens ou credenciais.
        etapa = "autorizacao" if "oauth2.googleapis.com" in url else "envio"
        raise RuntimeError(
            f"Gmail: falha na etapa de {etapa} (HTTP {exc.code}). "
            "Confira as credenciais, a autorizacao da conta e se a Gmail API esta ativa."
        ) from None


def enviar_por_gmail(*, destino: str, assunto: str, texto: str,
                     anexo_nome: str | None = None,
                     anexo_conteudo: bytes | None = None) -> None:
    nomes = ("GMAIL_CLIENT_ID", "GMAIL_CLIENT_SECRET", "GMAIL_REFRESH_TOKEN", "GMAIL_FROM")
    config = {nome: os.getenv(nome, "").strip() for nome in nomes}
    ausentes = [nome for nome, valor in config.items() if not valor]
    if ausentes:
        raise RuntimeError("Gmail: configuracao incompleta: " + ", ".join(ausentes))

    token = _post_json(
        "https://oauth2.googleapis.com/token",
        urllib.parse.urlencode({
            "client_id": config["GMAIL_CLIENT_ID"],
            "client_secret": config["GMAIL_CLIENT_SECRET"],
            "refresh_token": config["GMAIL_REFRESH_TOKEN"],
            "grant_type": "refresh_token",
        }).encode("ascii"),
        {"Content-Type": "application/x-www-form-urlencoded"},
    )
    if not token.get("access_token"):
        raise RuntimeError("Gmail: autorizacao nao retornou um token de acesso")

    msg = EmailMessage()
    msg["From"] = config["GMAIL_FROM"]
    msg["To"] = destino
    msg["Subject"] = assunto
    msg.set_content(texto)
    if anexo_nome and anexo_conteudo is not None:
        msg.add_attachment(anexo_conteudo, maintype="text", subtype="csv", filename=anexo_nome)
    payload = {"raw": base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")}
    result = _post_json(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
        json.dumps(payload).encode("utf-8"),
        {"Content-Type": "application/json", "Authorization": "Bearer " + token["access_token"]},
    )
    if not result.get("id"):
        raise RuntimeError("Gmail: resposta sem confirmacao de envio")
