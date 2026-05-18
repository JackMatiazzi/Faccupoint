# FaccuPoint

Prototipo funcional desenvolvido como trabalho de conclusao de curso. O objetivo do projeto e validar um fluxo simples de quiz ao vivo em sala de aula, com professor criando perguntas, abrindo uma sessao e alunos respondendo em tempo real.

O foco desta versao e entregar um sistema demonstravel, com separacao basica entre backend, frontend do professor e frontend do aluno, mantendo boas praticas adequadas a um prototipo academico.

## Tecnologias

- Backend: FastAPI
- Banco de dados: PostgreSQL
- Frontend: Flet
- Comunicacao em tempo real: WebSockets

## Escopo do prototipo

O professor pode fazer login, cadastrar quizzes, adicionar perguntas e abrir uma sala com codigo. Os alunos informam o codigo, entram no lobby, respondem as perguntas e visualizam o placar ao final.

A autenticacao usa PIN com hash e token assinado para proteger as principais rotas do professor. Essa solucao e suficiente para o prototipo, mas nao substitui uma estrategia completa de autenticacao para producao.

## Configuracao

Crie o arquivo `backend/.env` a partir de `backend/.env.example`:

```env
DATABASE_URL=postgresql://usuario:senha@host/banco?sslmode=require
DB_SCHEMA=faccupoint
APP_TIMEZONE=America/Sao_Paulo
CORS_ORIGINS=http://127.0.0.1:8000,http://localhost:8000
SECRET_KEY=troque-este-segredo-em-producao
```

O campo `SECRET_KEY` e usado para assinar os tokens de sessao do professor. Em ambiente real, ele deve ser alterado para um valor secreto e nao deve ser versionado.

Opcionalmente, para enviar relatorio por email ao final da aula:

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

Esse comando inicia o backend e abre o aplicativo do professor. O aplicativo do aluno tambem pode ser iniciado separadamente:

```bash
cd frontend/aluno
python -m app.main
```

## Observacoes de desenvolvimento

Arquivos locais como `.env`, bancos `.db`, caches `__pycache__` e builds gerados pelo Flet nao devem ser commitados. O projeto mantem esses arquivos no `.gitignore` para preservar apenas codigo-fonte, configuracoes de exemplo e documentacao.
