from __future__ import annotations

import sqlite3

from app.infra.paths import db_path
from app.infra.pin_hash import hash_pin

ADM = "adm"
PROF = "prof"
PAPEIS_VALIDOS = frozenset({ADM, PROF})


def _connect():
    path = db_path()
    if not path.is_file():
        raise FileNotFoundError(
            f"Banco ausente em {path}. Rode python inicializacao_local/init_db.py"
        )
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def listar_docentes() -> list[tuple[int, str, str]]:
    conn = _connect()
    try:
        cur = conn.execute(
            "SELECT id_docente, nome, email FROM docentes ORDER BY nome COLLATE NOCASE"
        )
        return [(int(r[0]), str(r[1]), str(r[2])) for r in cur.fetchall()]
    finally:
        conn.close()


def obter_docente_por_email(email: str) -> tuple[int, str, str, str, str] | None:
    email = email.strip().lower()
    conn = _connect()
    try:
        cur = conn.execute(
            """
            SELECT id_docente, nome, email, pin_hash,
                   COALESCE(papel, 'prof') AS papel
            FROM docentes WHERE email = ?
            """,
            (email,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        p = str(row[4])
        if p == "admin":
            p = ADM
        elif p == "professor":
            p = PROF
        return int(row[0]), str(row[1]), str(row[2]), str(row[3]), p
    finally:
        conn.close()


def listar_docentes_com_papel() -> list[tuple[int, str, str, str]]:
    conn = _connect()
    try:
        cur = conn.execute(
            """
            SELECT id_docente, nome, email, COALESCE(papel, 'prof') AS papel
            FROM docentes
            ORDER BY nome COLLATE NOCASE
            """
        )
        rows = []
        for r in cur.fetchall():
            p = str(r[3])
            if p == "admin":
                p = ADM
            elif p == "professor":
                p = PROF
            rows.append((int(r[0]), str(r[1]), str(r[2]), p))
        return rows
    finally:
        conn.close()


def _normalizar_papel_db(val: str) -> str:
    v = (val or "").strip().lower()
    if v in ("admin", ADM):
        return ADM
    if v in ("professor", PROF):
        return PROF
    return v or PROF


def excluir_docente(id_alvo: int, id_admin: int) -> None:
    if id_alvo == id_admin:
        raise ValueError("Não é possível excluir o próprio usuário.")

    conn = sqlite3.connect(str(db_path()))
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        cur = conn.execute(
            "SELECT papel FROM docentes WHERE id_docente = ?", (id_admin,)
        )
        row = cur.fetchone()
        if row is None or _normalizar_papel_db(str(row[0])) != ADM:
            raise PermissionError("Apenas administrador pode excluir docentes.")

        cur = conn.execute(
            "SELECT 1 FROM docentes WHERE id_docente = ?", (id_alvo,)
        )
        if cur.fetchone() is None:
            raise ValueError("Docente não encontrado.")

        conn.execute("PRAGMA foreign_keys = OFF")

        conn.execute(
            """
            DELETE FROM tentativas WHERE id_pergunta IN (
                SELECT id_pergunta FROM perguntas WHERE id_quiz IN (
                    SELECT id_quiz FROM quizzes WHERE id_docente_proprietario = ?
                )
            )
            """,
            (id_alvo,),
        )
        conn.execute(
            """
            DELETE FROM tentativas WHERE id_participante IN (
                SELECT id_participante FROM participantes WHERE id_sessao IN (
                    SELECT id_sessao FROM sessoes
                    WHERE id_docente_anfitriao = ?
                       OR id_quiz IN (
                           SELECT id_quiz FROM quizzes WHERE id_docente_proprietario = ?
                       )
                )
            )
            """,
            (id_alvo, id_alvo),
        )
        conn.execute(
            """
            DELETE FROM alternativas WHERE id_pergunta IN (
                SELECT id_pergunta FROM perguntas WHERE id_quiz IN (
                    SELECT id_quiz FROM quizzes WHERE id_docente_proprietario = ?
                )
            )
            """,
            (id_alvo,),
        )
        conn.execute(
            """
            DELETE FROM perguntas WHERE id_quiz IN (
                SELECT id_quiz FROM quizzes WHERE id_docente_proprietario = ?
            )
            """,
            (id_alvo,),
        )
        conn.execute(
            """
            DELETE FROM participantes WHERE id_sessao IN (
                SELECT id_sessao FROM sessoes
                WHERE id_docente_anfitriao = ?
                   OR id_quiz IN (
                       SELECT id_quiz FROM quizzes WHERE id_docente_proprietario = ?
                   )
            )
            """,
            (id_alvo, id_alvo),
        )
        conn.execute(
            """
            DELETE FROM sessoes
            WHERE id_docente_anfitriao = ?
               OR id_quiz IN (
                   SELECT id_quiz FROM quizzes WHERE id_docente_proprietario = ?
               )
            """,
            (id_alvo, id_alvo),
        )
        conn.execute(
            "DELETE FROM quizzes WHERE id_docente_proprietario = ?",
            (id_alvo,),
        )
        conn.execute("DELETE FROM docentes WHERE id_docente = ?", (id_alvo,))

        conn.execute("PRAGMA foreign_keys = ON")
        conn.commit()
    finally:
        conn.close()


def inserir_docente(nome: str, email: str, pin: str, papel: str = PROF) -> None:
    nome = nome.strip()
    email = email.strip().lower()
    if papel not in PAPEIS_VALIDOS:
        raise ValueError("Papel inválido")
    pin_hash = hash_pin(pin)

    conn = _connect()
    try:
        conn.execute(
            """
            INSERT INTO docentes (nome, email, pin_hash, papel)
            VALUES (?, ?, ?, ?)
            """,
            (nome, email, pin_hash, papel),
        )
        conn.commit()
    finally:
        conn.close()
