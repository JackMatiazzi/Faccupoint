from __future__ import annotations

import sqlite3

from app.repos.docentes_repo import _connect
from app.regras.titulo import normalizar_titulo


def listar_quizzes_do_docente(id_docente_proprietario: int) -> list[tuple[int, str]]:
    conn = _connect()
    try:
        cur = conn.execute(
            """
            SELECT id_quiz, titulo FROM quizzes
            WHERE id_docente_proprietario = ?
            ORDER BY titulo COLLATE NOCASE
            """,
            (id_docente_proprietario,),
        )
        return [(int(r[0]), str(r[1])) for r in cur.fetchall()]
    finally:
        conn.close()


def buscar_quizzes_por_titulo_global(termo: str) -> list[tuple[int, int, str, str, str]]:
    termo = termo.strip()
    if not termo:
        return []
    conn = _connect()
    try:
        cur = conn.execute(
            """
            SELECT q.id_quiz, q.id_docente_proprietario, q.titulo, d.nome, d.email
            FROM quizzes q
            JOIN docentes d ON d.id_docente = q.id_docente_proprietario
            WHERE q.titulo LIKE ?
            ORDER BY q.titulo COLLATE NOCASE
            LIMIT 50
            """,
            (f"%{termo}%",),
        )
        return [
            (int(r[0]), int(r[1]), str(r[2]), str(r[3]), str(r[4]))
            for r in cur.fetchall()
        ]
    finally:
        conn.close()


def obter_quiz(id_quiz: int, id_docente_proprietario: int) -> tuple[str, str | None] | None:
    conn = _connect()
    try:
        cur = conn.execute(
            """
            SELECT titulo, descricao FROM quizzes
            WHERE id_quiz = ? AND id_docente_proprietario = ?
            """,
            (id_quiz, id_docente_proprietario),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return str(row[0]), row[1] if row[1] is not None else None
    finally:
        conn.close()


def obter_primeira_pergunta_com_alternativas(
    id_quiz: int, id_docente_proprietario: int
) -> tuple[str, str, str, int] | None:
    conn = _connect()
    try:
        cur = conn.execute(
            """
            SELECT p.id_pergunta, p.enunciado
            FROM perguntas p
            JOIN quizzes q ON q.id_quiz = p.id_quiz
            WHERE p.id_quiz = ? AND q.id_docente_proprietario = ?
            ORDER BY p.ordem, p.id_pergunta
            LIMIT 1
            """,
            (id_quiz, id_docente_proprietario),
        )
        row = cur.fetchone()
        if row is None:
            return None

        id_pergunta = int(row[0])
        enunciado = str(row[1])
        cur = conn.execute(
            """
            SELECT texto, correta
            FROM alternativas
            WHERE id_pergunta = ?
            ORDER BY id_alternativa
            LIMIT 2
            """,
            (id_pergunta,),
        )
        alts = cur.fetchall()
        if len(alts) < 2:
            return None

        alt_a = str(alts[0][0])
        alt_b = str(alts[1][0])
        idx = 0 if int(alts[0][1]) == 1 else 1
        return enunciado, alt_a, alt_b, idx
    finally:
        conn.close()


def inserir_quiz(
    id_docente_proprietario: int,
    titulo: str,
    descricao: str | None,
) -> int:
    titulo = titulo.strip()
    if not titulo:
        raise ValueError("Título vazio")
    tn = normalizar_titulo(titulo)
    desc = descricao.strip() if descricao else None
    if desc == "":
        desc = None

    conn = _connect()
    try:
        cur = conn.execute(
            """
            INSERT INTO quizzes (titulo, titulo_normalizado, descricao, id_docente_proprietario)
            VALUES (?, ?, ?, ?)
            """,
            (titulo, tn, desc, id_docente_proprietario),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def atualizar_quiz(
    id_quiz: int,
    id_docente_proprietario: int,
    titulo: str,
    descricao: str | None,
) -> None:
    titulo = titulo.strip()
    if not titulo:
        raise ValueError("Título vazio")
    tn = normalizar_titulo(titulo)
    desc = descricao.strip() if descricao else None
    if desc == "":
        desc = None

    conn = _connect()
    try:
        cur = conn.execute(
            """
            UPDATE quizzes
            SET titulo = ?, titulo_normalizado = ?, descricao = ?
            WHERE id_quiz = ? AND id_docente_proprietario = ?
            """,
            (titulo, tn, desc, id_quiz, id_docente_proprietario),
        )
        if cur.rowcount == 0:
            raise PermissionError("Quiz inexistente ou não pertence a este docente.")
        conn.commit()
    finally:
        conn.close()


def inserir_pergunta_com_duas_alternativas(
    id_quiz: int,
    enunciado: str,
    texto_a: str,
    texto_b: str,
    indice_correta: int,
) -> None:
    enunciado = enunciado.strip()
    texto_a = texto_a.strip()
    texto_b = texto_b.strip()
    if not enunciado or not texto_a or not texto_b:
        raise ValueError("Enunciado e alternativas são obrigatórios.")
    if indice_correta not in (0, 1):
        raise ValueError("Índice da correta deve ser 0 ou 1.")

    conn = _connect()
    try:
        cur = conn.execute(
            """
            INSERT INTO perguntas (id_quiz, enunciado, ordem)
            VALUES (?, ?, 1)
            """,
            (id_quiz, enunciado),
        )
        id_pergunta = int(cur.lastrowid)
        conn.execute(
            "INSERT INTO alternativas (id_pergunta, texto, correta) VALUES (?, ?, ?)",
            (id_pergunta, texto_a, 1 if indice_correta == 0 else 0),
        )
        conn.execute(
            "INSERT INTO alternativas (id_pergunta, texto, correta) VALUES (?, ?, ?)",
            (id_pergunta, texto_b, 1 if indice_correta == 1 else 0),
        )
        conn.commit()
    finally:
        conn.close()


def salvar_primeira_pergunta_com_duas_alternativas(
    id_quiz: int,
    id_docente_proprietario: int,
    enunciado: str,
    texto_a: str,
    texto_b: str,
    indice_correta: int,
) -> None:
    enunciado = enunciado.strip()
    texto_a = texto_a.strip()
    texto_b = texto_b.strip()
    if not enunciado or not texto_a or not texto_b:
        raise ValueError("Enunciado e alternativas são obrigatórios.")
    if indice_correta not in (0, 1):
        raise ValueError("Índice da correta deve ser 0 ou 1.")

    conn = _connect()
    try:
        cur = conn.execute(
            """
            SELECT p.id_pergunta
            FROM perguntas p
            JOIN quizzes q ON q.id_quiz = p.id_quiz
            WHERE p.id_quiz = ? AND q.id_docente_proprietario = ?
            ORDER BY p.ordem, p.id_pergunta
            LIMIT 1
            """,
            (id_quiz, id_docente_proprietario),
        )
        row = cur.fetchone()
        if row is None:
            cur = conn.execute(
                """
                INSERT INTO perguntas (id_quiz, enunciado, ordem)
                VALUES (?, ?, 1)
                """,
                (id_quiz, enunciado),
            )
            id_pergunta = int(cur.lastrowid)
        else:
            id_pergunta = int(row[0])
            conn.execute(
                "UPDATE perguntas SET enunciado = ?, ordem = 1 WHERE id_pergunta = ?",
                (enunciado, id_pergunta),
            )

        cur = conn.execute(
            """
            SELECT id_alternativa
            FROM alternativas
            WHERE id_pergunta = ?
            ORDER BY id_alternativa
            LIMIT 2
            """,
            (id_pergunta,),
        )
        ids = [int(r[0]) for r in cur.fetchall()]

        if len(ids) >= 1:
            conn.execute(
                "UPDATE alternativas SET texto = ?, correta = ? WHERE id_alternativa = ?",
                (texto_a, 1 if indice_correta == 0 else 0, ids[0]),
            )
        else:
            conn.execute(
                "INSERT INTO alternativas (id_pergunta, texto, correta) VALUES (?, ?, ?)",
                (id_pergunta, texto_a, 1 if indice_correta == 0 else 0),
            )

        if len(ids) >= 2:
            conn.execute(
                "UPDATE alternativas SET texto = ?, correta = ? WHERE id_alternativa = ?",
                (texto_b, 1 if indice_correta == 1 else 0, ids[1]),
            )
        else:
            conn.execute(
                "INSERT INTO alternativas (id_pergunta, texto, correta) VALUES (?, ?, ?)",
                (id_pergunta, texto_b, 1 if indice_correta == 1 else 0),
            )

        conn.commit()
    finally:
        conn.close()
