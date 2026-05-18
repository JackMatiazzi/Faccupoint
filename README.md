# FaccuPoint

Projeto de TCC. Um sistema de quiz ao vivo para sala de aula: o professor cria as perguntas, abre uma sessao com codigo, e os alunos entram e respondem em tempo real.

## Tecnologias

- Backend: FastAPI
- Banco de dados: PostgreSQL
- Frontend: Flet
- Comunicacao em tempo real: WebSockets

## O que funciona

O professor faz login, cadastra quizzes com perguntas, abre uma sala e compartilha o codigo com os alunos. Os alunos informam o codigo, entram no lobby, respondem as perguntas no ritmo da sessao e veem o placar no final.

A autenticacao e feita com PIN e token assinado. Serve pro prototipo — nao e o ideal pra producao, mas cumpre o papel aqui.

## Configuracao

Crie o arquivo `backend/.env` a partir de `backend/.env.example`:

```env
DATABASE_URL=postgresql://usuario:senha@host/banco?sslmode=require
DB_SCHEMA=faccupoint
APP_TIMEZONE=America/Sao_Paulo
CORS_ORIGINS=http://127.0.0.1:8000,http://localhost:8000
SECRET_KEY=troque-este-segredo-em-producao
```

Se quiser enviar relatorio por email ao fim da aula, adicione tambem:

```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=email-da-aplicacao@gmail.com
EMAIL_PASSWORD=senha-de-app
EMAIL_FROM=FaccuPoint <email-da-aplicacao@gmail.com>
EMAIL_STARTTLS=1
```

Crie tambem o arquivo `frontend/.env` a partir de `frontend/.env.example`:

```env
API_URL=http://127.0.0.1:8000
```

## Instalacao

```bash
pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt
```

## Execucao

Na raiz do projeto:

```bash
python launcher.py
```

Isso inicia o backend e abre o app do professor. O app do aluno tambem pode ser aberto separado:

```bash
cd frontend/aluno
python -m app.main
```