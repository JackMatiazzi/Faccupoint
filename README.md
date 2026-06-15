# FaccuPoint

Projeto de TCC para aplicar quizzes ao vivo em sala de aula. O professor monta as perguntas, abre uma sala com código e acompanha as respostas dos alunos em tempo real.

## Tecnologias

- Backend: FastAPI
- Banco de dados: PostgreSQL
- Frontend: Flet
- Comunicação em tempo real: WebSockets

## O que funciona

O professor faz login, cadastra quizzes com perguntas, abre uma sala e compartilha o código com os alunos. Os alunos entram pelo código, aguardam no lobby, respondem as perguntas no ritmo da sessão e veem o placar no final.

## Configuração

Crie o arquivo `backend/.env` a partir de `backend/.env.example`:

```env
DATABASE_URL=postgresql://usuario:senha@host/banco?sslmode=require
DB_SCHEMA=faccupoint
APP_TIMEZONE=America/Sao_Paulo
CORS_ORIGINS=http://127.0.0.1:8000,http://localhost:8000
SECRET_KEY=troque-este-segredo-em-producao
```

Se quiser enviar relatório por email ao fim da aula, adicione também:

```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=email-da-aplicacao@gmail.com
EMAIL_PASSWORD=senha-de-app
EMAIL_FROM=FaccuPoint <email-da-aplicacao@gmail.com>
EMAIL_STARTTLS=1
```

Crie também o arquivo `frontend/.env` a partir de `frontend/.env.example`:

```env
API_URL=http://127.0.0.1:8000
```

## Instalação

```bash
pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt
```

## Execução

Na raiz do projeto:

```bash
python launcher.py
```

O app do aluno também pode ser aberto separado:

```bash
cd frontend
python -m aluno.main
```


## Testes

Na raiz do projeto:

```bash
python -m unittest discover -s tests -v
```
