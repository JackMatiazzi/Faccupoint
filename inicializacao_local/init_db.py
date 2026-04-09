import sqlite3
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def init_db() -> Path:
    root = _repo_root()
    schema_path = root / "db" / "schema.sql"
    db_path = root / "data" / "faccupoint.db"

    db_path.parent.mkdir(parents=True, exist_ok=True)

    sql = schema_path.read_text(encoding="utf-8")

    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(sql)
        conn.commit()
    finally:
        conn.close()

    return db_path


if __name__ == "__main__":
    db_file = init_db()
    print(f"Banco SQLite criado: {db_file}")
