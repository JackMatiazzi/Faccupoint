from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC = _REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from app.infra.paths import db_path
from app.repos.docentes_repo import obter_docente_por_email
from app.repos.quizzes_repo import inserir_pergunta_com_duas_alternativas, inserir_quiz

DOCENTE_EMAIL = "maria.silva@sou.faccat.br"

QUIZZES_EXEMPLO: list[tuple[str, str | None, tuple[str, str, str, int] | None]] = [
    (
        "Introdução ao SQLite",
        "Quiz de demonstração do Ciclo 1 (dados seed).",
        (
            "O SQLite precisa de um servidor separado para uso local?",
            "Não, é embutido na aplicação",
            "Sim, sempre exige PostgreSQL",
            0,
        ),
    ),
    (
        "Quiz só com título",
        None,
        None,
    ),
]


def seed_quizzes() -> tuple[int, int]:
    path = db_path()
    if not path.is_file():
        raise FileNotFoundError(
            f"Banco ausente em {path}. Rode python inicializacao_local/init_db.py"
        )

    doc = obter_docente_por_email(DOCENTE_EMAIL)
    if doc is None:
        raise RuntimeError(
            f"Sem docente {DOCENTE_EMAIL}. Rode python inicializacao_local/seed_docentes.py"
        )

    id_docente = int(doc[0])
    inseridos = 0
    duplicados = 0

    for titulo, descricao, pergunta in QUIZZES_EXEMPLO:
        try:
            qid = inserir_quiz(id_docente, titulo, descricao)
            if pergunta is not None:
                en, a, b, cor = pergunta
                inserir_pergunta_com_duas_alternativas(qid, en, a, b, cor)
            inseridos += 1
        except sqlite3.IntegrityError:
            duplicados += 1

    return inseridos, duplicados


if __name__ == "__main__":
    ins, dup = seed_quizzes()
    p = db_path()
    print(f"Inseridos {ins}, duplicados ignorados {dup}. {p}")
