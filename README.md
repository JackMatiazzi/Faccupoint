# FaccuPoint

Plataforma educacional gamificada (TCC), com foco em quizzes, pontuação e progressão. A visão do trabalho inclui backend em PostgreSQL, WebSockets e arquitetura distribuída; no **Ciclo 1** o repositório entrega um protótipo **local** em **Python + Kivy** com **SQLite**: login de docente e criação/edição de quiz.

**Requisitos:** Python 3.10+, Git, editor à escolha. SQLite via `sqlite3` da biblioteca padrão.

---

## Onde rodar

Sempre na **raiz do repositório** (pasta com este `README`, `main.py`, `db/`, `data/`). O código Python está em `src/app/` (pacote `import app`: `infra/`, `repos/`, `regras/`, `telas/`, `design_system/`).

---

## Ciclo 1.1 — Ambiente

```powershell
cd caminho\para\Faccupoint
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -c "import kivy; print(kivy.__version__)"
```

Para sair do venv: `deactivate`.

---

## Ciclo 1.2 — Banco (SQLite)

- Modelo em [`db/schema.sql`](db/schema.sql): `docentes`, `quizzes` (com `titulo_normalizado` e `UNIQUE (id_docente_proprietario, titulo_normalizado)`), `perguntas`, `alternativas`, e tabelas `sessoes`, `participantes`, `tentativas` (base para ciclos futuros).

Criar/atualizar o arquivo do banco (cria `data/` se precisar):

```powershell
python inicializacao_local/init_db.py
```

O arquivo gerado é **`data/faccupoint.db`** (geralmente não vai no Git). Se já existir um `.db` antigo, rodar de novo o `init_db` adiciona o que faltar com `IF NOT EXISTS` sem apagar dados.

- Normalização **B.3** do título: [`src/app/regras/titulo.py`](src/app/regras/titulo.py) (`normalizar_titulo`).
- Persistência de quiz: [`src/app/repos/quizzes_repo.py`](src/app/repos/quizzes_repo.py). Título duplicado para o mesmo docente gera `sqlite3.IntegrityError`.

**Sugestão para o PDF do TCC:** print do esquema no DB Browser (ou similar), trecho do DDL com a unicidade e um texto ligando DER ↔ SQL.

---

## Ciclo 1.3 — Interface (login → quiz)

Docentes têm **`papel`** no banco: `adm` (único que vê **Cadastrar outro docente**) ou `prof`. No seed, **Jackson Matiazzi** é `adm` — edite e-mail/PIN em `inicializacao_local/seed_docentes.py` se precisar.

1. (Opcional) `python inicializacao_local/seed_docentes.py`
2. (Opcional) `python inicializacao_local/seed_quizzes.py` — usa o e-mail configurado no script (ex.: Maria do seed); precisa desse docente no banco.
3. `python main.py`

Fluxo mínimo: **login** (e-mail + PIN) → **início** → **Criar / editar quiz** → salvar (título e, se quiser, primeira pergunta com duas alternativas). Dois quizzes com o mesmo título “normalizado” para o mesmo docente devem acusar duplicata.

**Sugestão para o PDF:** sequência de telas do login até salvar um quiz; citar o `ScreenManager` em [`src/app/main.py`](src/app/main.py).
