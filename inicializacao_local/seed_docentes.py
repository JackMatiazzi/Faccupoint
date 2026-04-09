from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC = _REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from app.infra.paths import db_path
from app.infra.pin_hash import hash_pin
from app.repos.docentes_repo import ADM, PROF

__all__ = ["hash_pin", "db_path", "seed_docentes", "DOCENTES_EXEMPLO"]

DOCENTES_EXEMPLO: list[tuple[str, str, str, str]] = [
    ("Jackson Matiazzi", "matiazzijackson072@gmail.com", "7584", ADM),
    ("Maria Silva", "maria.silva@sou.faccat.br", "4656", PROF),
    ("João Santos", "joao.santos@sou.faccat.br", "1234", PROF),
    ("Ana Costa", "ana.costa@sou.faccat.br", "9999", PROF),
]


def seed_docentes() -> int:
    path = db_path()
    if not path.is_file():
        raise FileNotFoundError(
            f"Banco ausente em {path}. Rode python inicializacao_local/init_db.py"
        )

    conn = sqlite3.connect(path)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        cur = conn.cursor()
        inseridos = 0
        for nome, email, pin, papel in DOCENTES_EXEMPLO:
            ph = hash_pin(pin)
            cur.execute(
                """
                INSERT INTO docentes (nome, email, pin_hash, papel)
                VALUES (?, ?, ?, ?)
                ON CONFLICT (email) DO UPDATE SET
                    nome = excluded.nome,
                    pin_hash = excluded.pin_hash,
                    papel = excluded.papel
                """,
                (nome, email.strip().lower(), ph, papel),
            )
            inseridos += cur.rowcount
        conn.commit()
        return inseridos
    finally:
        conn.close()


if __name__ == "__main__":
    n = seed_docentes()
    p = db_path()
    print(f"{n} linhas atualizadas em {p}")
