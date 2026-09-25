"""Autoriza somente envio e salva variaveis para o Render em .local (ignorado pelo Git)."""

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("credenciais", type=Path, help="JSON do cliente OAuth do tipo Desktop")
    parser.add_argument("--remetente", required=True, help="Gmail da conta que sera autorizada")
    args = parser.parse_args()
    from google_auth_oauthlib.flow import InstalledAppFlow

    flow = InstalledAppFlow.from_client_secrets_file(
        str(args.credenciais), ["https://www.googleapis.com/auth/gmail.send"],
        autogenerate_code_verifier=True,
    )
    creds = flow.run_local_server(
        host="127.0.0.1", port=0, timeout_seconds=300,
        access_type="offline", prompt="consent", login_hint=args.remetente,
        authorization_prompt_message="Autorize o envio na janela do navegador.",
        success_message="FaccuPoint autorizado. Pode fechar esta aba.",
    )
    if not creds.refresh_token:
        raise RuntimeError("Google nao forneceu refresh token; repita a autorizacao com consentimento.")
    pasta = Path(__file__).resolve().parents[1] / ".local" / "gmail"
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / "render.env"
    values = {
        "EMAIL_PROVIDER": "gmail",
        "GMAIL_CLIENT_ID": creds.client_id,
        "GMAIL_CLIENT_SECRET": creds.client_secret,
        "GMAIL_REFRESH_TOKEN": creds.refresh_token,
        "GMAIL_FROM": args.remetente,
    }
    destino.write_text("".join(f"{k}={v}\n" for k, v in values.items()), encoding="utf-8")
    print(f"Autorizacao salva em {destino}. Nao compartilhe o conteudo no chat ou Git.")


if __name__ == "__main__":
    main()
