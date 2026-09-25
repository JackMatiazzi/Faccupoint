# Gmail API no Render

O backend usa HTTPS e somente a permissao `gmail.send`. Nao e necessario alterar o instalador.

1. No Google Cloud, crie um projeto e ative Gmail API.
2. Configure Google Auth Platform com publico Externo. Em modo Teste, adicione a conta
   remetente aos usuarios de teste. Em Data Access, adicione `https://www.googleapis.com/auth/gmail.send`.
3. Crie cliente OAuth do tipo Aplicativo para computador e baixe o JSON para `.local/gmail/credentials.json`.
4. Instale `google-auth-oauthlib` em um ambiente local e execute:

   ```powershell
   .\.local\gmail\venv\Scripts\python.exe ferramentas\autorizar_gmail.py .local\gmail\credentials.json --remetente faccupoint@gmail.com
   ```

   Troque o remetente pela conta real e autorize essa mesma conta no navegador.
   O helper salva as cinco variaveis em `.local/gmail/render.env`, ignorado pelo Git.
5. Publique o backend com o novo adaptador e configure no Render as variaveis geradas:
   `EMAIL_PROVIDER=gmail`, `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN`, `GMAIL_FROM`.
   Nao cole segredos em logs, commits ou mensagens. Credenciais Gmail nao vao ao instalador.
6. Aplique as variaveis com Save and deploy. Teste envio e recebimento, incluindo CSV.

Em modo Teste do Google OAuth, o refresh token para Gmail expira em sete dias.
Isso atende ao teste imediato, mas nao constitui configuracao permanente. Antes desse prazo,
regularize o estado de publicacao e os requisitos de verificacao aplicaveis, e reautorize a conta.
Revogacao de acesso ou troca da senha da conta tambem pode exigir nova autorizacao.

Com `EMAIL_PROVIDER=gmail`, falhas nao disparam fallback Resend/SMTP, para evitar duplicidades
ou tentativas pelo provedor errado. Sem essa opcao, o comportamento anterior e preservado.

Documentacao: https://developers.google.com/identity/protocols/oauth2
