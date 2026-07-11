
import os

import psycopg2

from backend.dominio.pergunta import normalizar_pergunta, validar_link_midia
from backend.infraestrutura.configuracao import database_url, load_environment
from backend.infraestrutura.seguranca import gerar_hash_pin

load_environment()

ADM = "adm"
PROF = "prof"
PAPEIS_VALIDOS = frozenset({ADM, PROF})
FUSO_HORARIO = os.getenv("APP_TIMEZONE", "America/Sao_Paulo")


def _conectar():
    schema = os.environ.get("DB_SCHEMA")
    connect_timeout = int(os.getenv("DB_CONNECT_TIMEOUT", "5"))
    conn = psycopg2.connect(database_url(), connect_timeout=connect_timeout)
    if schema:
        with conn.cursor() as cur:
            cur.execute("SET search_path TO %s", (schema,))
        conn.commit()
    return conn


def _normalizar_papel(val: str) -> str:
    v = (val or "").strip().lower()
    if v in ("admin", ADM):
        return ADM
    if v in ("professor", PROF, ""):
        return PROF
    raise ValueError(f"Papel desconhecido no banco: {v!r}")


def listar_docentes() -> list[tuple[int, str, str, str]]:
    conn = _conectar()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id_docente, nome, email, COALESCE(papel, 'prof') FROM docentes ORDER BY nome"
            )
            return [(int(r[0]), str(r[1]), str(r[2]), _normalizar_papel(r[3])) for r in cur.fetchall()]
    finally:
        conn.close()


def buscar_docente_por_email(email: str) -> tuple[int, str, str, str, str] | None:
    conn = _conectar()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id_docente, nome, email, pin_hash, COALESCE(papel, 'prof') FROM docentes WHERE email = %s",
                (email.strip().lower(),),
            )
            row = cur.fetchone()
            if row is None:
                return None
            return int(row[0]), str(row[1]), str(row[2]), str(row[3]), _normalizar_papel(row[4])
    finally:
        conn.close()


def buscar_docente_por_id(id_docente: int) -> tuple[int, str, str, str] | None:
    conn = _conectar()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id_docente, nome, email, COALESCE(papel, 'prof') FROM docentes WHERE id_docente = %s",
                (id_docente,),
            )
            row = cur.fetchone()
            if row is None:
                return None
            return int(row[0]), str(row[1]), str(row[2]), _normalizar_papel(row[3])
    finally:
        conn.close()


def cadastrar_docente(nome: str, email: str, pin: str, papel: str = PROF) -> None:
    if papel not in PAPEIS_VALIDOS:
        raise ValueError("Papel inválido. Use 'adm' ou 'prof'.")
    conn = _conectar()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO docentes (nome, email, pin_hash, papel) VALUES (%s, %s, %s, %s)",
                (nome.strip(), email.strip().lower(), gerar_hash_pin(pin), papel),
            )
        conn.commit()
    finally:
        conn.close()


def atualizar_docente(
    id_alvo: int,
    id_admin: int,
    nome: str,
    email: str,
    papel: str,
    pin: str | None = None,
) -> None:
    if papel not in PAPEIS_VALIDOS:
        raise ValueError("Papel inválido. Use 'adm' ou 'prof'.")
    nome = nome.strip()
    email = email.strip().lower()
    if not nome or not email:
        raise ValueError("Nome e email não podem ser vazios.")
    conn = _conectar()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT papel FROM docentes WHERE id_docente = %s", (id_admin,))
            row = cur.fetchone()
            if row is None or _normalizar_papel(row[0]) != ADM:
                raise PermissionError("Apenas administrador pode editar docentes.")
            if id_alvo == id_admin and papel != ADM:
                raise ValueError("Não é possível remover o próprio papel de administrador.")

            if pin:
                cur.execute(
                    "UPDATE docentes SET nome = %s, email = %s, papel = %s, pin_hash = %s WHERE id_docente = %s",
                    (nome, email, papel, gerar_hash_pin(pin), id_alvo),
                )
            else:
                cur.execute(
                    "UPDATE docentes SET nome = %s, email = %s, papel = %s WHERE id_docente = %s",
                    (nome, email, papel, id_alvo),
                )
            if cur.rowcount == 0:
                raise ValueError("Docente não encontrado.")
        conn.commit()
    finally:
        conn.close()


def excluir_docente(id_alvo: int, id_admin: int) -> None:
    if id_alvo == id_admin:
        raise ValueError("Não é possível excluir o próprio usuário.")
    conn = _conectar()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT papel FROM docentes WHERE id_docente = %s", (id_admin,))
            row = cur.fetchone()
            if row is None or _normalizar_papel(row[0]) != ADM:
                raise PermissionError("Apenas administrador pode excluir docentes.")
            cur.execute("SELECT 1 FROM docentes WHERE id_docente = %s", (id_alvo,))
            if cur.fetchone() is None:
                raise ValueError("Docente não encontrado.")

            cur.execute(
                """
                DELETE FROM tentativas
                WHERE id_participante IN (
                    SELECT p.id_participante
                    FROM participantes p
                    JOIN sessoes s ON s.id_sessao = p.id_sessao
                    WHERE s.id_docente_anfitriao = %s
                       OR s.id_quiz IN (
                           SELECT id_quiz FROM quizzes WHERE id_docente_proprietario = %s
                       )
                )
                """,
                (id_alvo, id_alvo),
            )
            cur.execute(
                """
                DELETE FROM participantes
                WHERE id_sessao IN (
                    SELECT id_sessao FROM sessoes
                    WHERE id_docente_anfitriao = %s
                       OR id_quiz IN (
                           SELECT id_quiz FROM quizzes WHERE id_docente_proprietario = %s
                       )
                )
                """,
                (id_alvo, id_alvo),
            )
            cur.execute(
                """
                DELETE FROM sessoes
                WHERE id_docente_anfitriao = %s
                   OR id_quiz IN (
                       SELECT id_quiz FROM quizzes WHERE id_docente_proprietario = %s
                   )
                """,
                (id_alvo, id_alvo),
            )
            cur.execute("DELETE FROM tentativas WHERE id_pergunta IN (SELECT id_pergunta FROM perguntas WHERE id_quiz IN (SELECT id_quiz FROM quizzes WHERE id_docente_proprietario = %s))", (id_alvo,))
            cur.execute("DELETE FROM alternativas WHERE id_pergunta IN (SELECT id_pergunta FROM perguntas WHERE id_quiz IN (SELECT id_quiz FROM quizzes WHERE id_docente_proprietario = %s))", (id_alvo,))
            cur.execute("DELETE FROM perguntas WHERE id_quiz IN (SELECT id_quiz FROM quizzes WHERE id_docente_proprietario = %s)", (id_alvo,))
            cur.execute("DELETE FROM quizzes WHERE id_docente_proprietario = %s", (id_alvo,))
            cur.execute("DELETE FROM docentes WHERE id_docente = %s", (id_alvo,))
        conn.commit()
    finally:
        conn.close()


def migrar_schema() -> None:
    conn = _conectar()
    try:
        with conn.cursor() as cur:
            cur.execute("ALTER TABLE quizzes ADD COLUMN IF NOT EXISTS link_midia VARCHAR")
        conn.commit()
    finally:
        conn.close()


def listar_quizzes(id_docente: int) -> list[tuple[int, str, str | None, int, int | None, str | None]]:
    conn = _conectar()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id_quiz, titulo, descricao, id_docente_proprietario, tempo_segundos, link_midia FROM quizzes WHERE id_docente_proprietario = %s ORDER BY titulo",
                (id_docente,),
            )
            return [(int(r[0]), str(r[1]), r[2], int(r[3]), r[4], r[5]) for r in cur.fetchall()]
    finally:
        conn.close()


def listar_quizzes_compartilhados(id_docente: int, termo: str = "") -> list[tuple[int, str, str | None, int, int | None, str, str | None]]:
    busca = f"%{termo.strip()}%"
    conn = _conectar()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT q.id_quiz, q.titulo, q.descricao, q.id_docente_proprietario,
                       q.tempo_segundos, d.nome, q.link_midia
                FROM quizzes q
                JOIN docentes d ON d.id_docente = q.id_docente_proprietario
                WHERE q.id_docente_proprietario <> %s
                  AND (%s = '%%' OR q.titulo ILIKE %s OR d.nome ILIKE %s)
                ORDER BY q.titulo
                LIMIT 20
                """,
                (id_docente, busca, busca, busca),
            )
            return [
                (int(r[0]), str(r[1]), r[2], int(r[3]), r[4], str(r[5]), r[6])
                for r in cur.fetchall()
            ]
    finally:
        conn.close()


def copiar_quiz(id_quiz_origem: int, id_docente_destino: int) -> int:
    conn = _conectar()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT titulo, descricao, tempo_segundos, link_midia FROM quizzes WHERE id_quiz = %s",
                (id_quiz_origem,),
            )
            quiz = cur.fetchone()
            if quiz is None:
                raise ValueError("Quiz não encontrado.")

            titulo_base = f"{quiz[0]} (cópia)"
            titulo = titulo_base
            contador = 2
            while True:
                cur.execute(
                    "SELECT 1 FROM quizzes WHERE id_docente_proprietario = %s AND titulo = %s",
                    (id_docente_destino, titulo),
                )
                if cur.fetchone() is None:
                    break
                titulo = f"{titulo_base} {contador}"
                contador += 1

            cur.execute(
                """
                INSERT INTO quizzes (titulo, descricao, id_docente_proprietario, tempo_segundos, link_midia)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id_quiz
                """,
                (titulo, quiz[1], id_docente_destino, quiz[2], quiz[3]),
            )
            id_quiz_novo = int(cur.fetchone()[0])

            cur.execute(
                "SELECT id_pergunta, enunciado, ordem, link_midia FROM perguntas WHERE id_quiz = %s ORDER BY ordem",
                (id_quiz_origem,),
            )
            perguntas = cur.fetchall()
            for pergunta in perguntas:
                cur.execute(
                    """
                    INSERT INTO perguntas (id_quiz, enunciado, ordem, link_midia)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id_pergunta
                    """,
                    (id_quiz_novo, pergunta[1], pergunta[2], pergunta[3]),
                )
                id_pergunta_nova = int(cur.fetchone()[0])

                cur.execute(
                    "SELECT texto, correta FROM alternativas WHERE id_pergunta = %s ORDER BY id_alternativa",
                    (pergunta[0],),
                )
                for alternativa in cur.fetchall():
                    cur.execute(
                        "INSERT INTO alternativas (id_pergunta, texto, correta) VALUES (%s, %s, %s)",
                        (id_pergunta_nova, alternativa[0], alternativa[1]),
                    )
        conn.commit()
        return id_quiz_novo
    finally:
        conn.close()


def buscar_tempo_quiz(id_quiz: int) -> int | None:
    conn = _conectar()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT tempo_segundos FROM quizzes WHERE id_quiz = %s", (id_quiz,))
            row = cur.fetchone()
            return int(row[0]) if row and row[0] is not None else None
    finally:
        conn.close()


def buscar_docente_do_quiz(id_quiz: int) -> int | None:
    conn = _conectar()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id_docente_proprietario FROM quizzes WHERE id_quiz = %s", (id_quiz,))
            row = cur.fetchone()
            return int(row[0]) if row else None
    finally:
        conn.close()


def registrar_sessao(codigo: str, id_quiz: int, id_docente: int) -> int:
    conn = _conectar()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO sessoes (codigo_curto, id_quiz, id_docente_anfitriao, criada_em)
                VALUES (%s, %s, %s, timezone(%s, now()))
                RETURNING id_sessao
                """,
                (codigo, id_quiz, id_docente, FUSO_HORARIO),
            )
            id_sessao = int(cur.fetchone()[0])
        conn.commit()
        return id_sessao
    finally:
        conn.close()


def atualizar_pergunta_atual_sessao(id_sessao: int, pergunta_atual: int) -> None:
    conn = _conectar()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE sessoes SET pergunta_atual = %s WHERE id_sessao = %s",
                (pergunta_atual, id_sessao),
            )
        conn.commit()
    finally:
        conn.close()


def registrar_participante_sessao(id_sessao: int, apelido: str) -> int:
    conn = _conectar()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO participantes (id_sessao, apelido)
                VALUES (%s, %s)
                RETURNING id_participante
                """,
                (id_sessao, apelido),
            )
            id_participante = int(cur.fetchone()[0])
        conn.commit()
        return id_participante
    finally:
        conn.close()


def registrar_tentativa(
    id_participante: int,
    id_pergunta: int,
    id_alternativa: int | None,
    acertou: bool,
) -> None:
    conn = _conectar()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO tentativas (
                    id_participante, id_pergunta, id_alternativa_escolhida,
                    acertou, registrada_em
                )
                VALUES (%s, %s, %s, %s, timezone(%s, now()))
                """,
                (id_participante, id_pergunta, id_alternativa, acertou, FUSO_HORARIO),
            )
        conn.commit()
    finally:
        conn.close()


def buscar_relatorio_sessao(id_sessao: int) -> dict | None:
    conn = _conectar()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT s.codigo_curto, s.criada_em, d.nome, d.email, q.titulo
                FROM sessoes s
                JOIN docentes d ON d.id_docente = s.id_docente_anfitriao
                JOIN quizzes q ON q.id_quiz = s.id_quiz
                WHERE s.id_sessao = %s
                """,
                (id_sessao,),
            )
            cabecalho = cur.fetchone()
            if cabecalho is None:
                return None

            cur.execute(
                """
                SELECT
                    p.apelido,
                    per.ordem,
                    per.enunciado,
                    alt.texto,
                    corretas.texto,
                    t.acertou,
                    t.registrada_em
                FROM participantes p
                LEFT JOIN tentativas t ON t.id_participante = p.id_participante
                LEFT JOIN perguntas per ON per.id_pergunta = t.id_pergunta
                LEFT JOIN alternativas alt ON alt.id_alternativa = t.id_alternativa_escolhida
                LEFT JOIN LATERAL (
                    SELECT string_agg(a.texto, ', ' ORDER BY a.id_alternativa) AS texto
                    FROM alternativas a
                    WHERE a.id_pergunta = per.id_pergunta
                      AND a.correta = true
                ) corretas ON true
                WHERE p.id_sessao = %s
                ORDER BY p.apelido, per.ordem
                """,
                (id_sessao,),
            )
            respostas = [
                {
                    "aluno": r[0],
                    "ordem": r[1],
                    "pergunta": r[2],
                    "resposta": r[3],
                    "correta": r[4],
                    "acertou": r[5],
                    "respondida_em": r[6],
                }
                for r in cur.fetchall()
            ]

        return {
            "codigo": cabecalho[0],
            "criada_em": cabecalho[1],
            "professor": cabecalho[2],
            "email_professor": cabecalho[3],
            "quiz": cabecalho[4],
            "respostas": respostas,
        }
    finally:
        conn.close()


def buscar_link_midia_quiz(id_quiz: int) -> str | None:
    conn = _conectar()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT link_midia FROM quizzes WHERE id_quiz = %s", (id_quiz,))
            row = cur.fetchone()
            return str(row[0]) if row and row[0] else None
    finally:
        conn.close()


def cadastrar_quiz(id_docente: int, titulo: str, descricao: str | None, tempo_segundos: int | None = None, link_midia: str | None = None) -> int:
    titulo = titulo.strip()
    if not titulo:
        raise ValueError("Título não pode ser vazio.")
    desc = descricao.strip() if descricao else None
    midia = validar_link_midia(link_midia)
    conn = _conectar()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO quizzes (titulo, descricao, id_docente_proprietario, tempo_segundos, link_midia) VALUES (%s, %s, %s, %s, %s) RETURNING id_quiz",
                (titulo, desc, id_docente, tempo_segundos, midia),
            )
            id_quiz = int(cur.fetchone()[0])
        conn.commit()
        return id_quiz
    finally:
        conn.close()


def atualizar_quiz(id_quiz: int, id_docente: int, titulo: str, descricao: str | None, tempo_segundos: int | None = None, link_midia: str | None = None) -> None:
    titulo = titulo.strip()
    if not titulo:
        raise ValueError("Título não pode ser vazio.")
    desc = descricao.strip() if descricao else None
    midia = validar_link_midia(link_midia)
    conn = _conectar()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE quizzes SET titulo = %s, descricao = %s, tempo_segundos = %s, link_midia = %s WHERE id_quiz = %s AND id_docente_proprietario = %s",
                (titulo, desc, tempo_segundos, midia, id_quiz, id_docente),
            )
            if cur.rowcount == 0:
                raise PermissionError("Quiz não encontrado ou não pertence a este docente.")
        conn.commit()
    finally:
        conn.close()


def listar_perguntas_do_quiz(id_quiz: int) -> list[dict]:
    conn = _conectar()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    p.id_pergunta,
                    p.enunciado,
                    p.ordem,
                    p.link_midia,
                    a.id_alternativa,
                    a.texto,
                    a.correta
                FROM perguntas p
                LEFT JOIN alternativas a ON a.id_pergunta = p.id_pergunta
                WHERE p.id_quiz = %s
                ORDER BY p.ordem, a.id_alternativa
                """,
                (id_quiz,),
            )
            perguntas: dict[int, dict] = {}
            for row in cur.fetchall():
                id_pergunta = int(row[0])
                pergunta = perguntas.setdefault(id_pergunta, {
                    "id_pergunta": id_pergunta,
                    "enunciado": row[1],
                    "ordem": row[2],
                    "link_midia": row[3],
                    "alternativas": [],
                })
                if row[4] is not None:
                    pergunta["alternativas"].append({
                        "id": int(row[4]),
                        "texto": row[5],
                        "correta": bool(row[6]),
                    })
        return list(perguntas.values())
    finally:
        conn.close()


def _inserir_alternativas(cur, id_pergunta: int, alternativas: list[dict]) -> None:
    cur.executemany(
        "INSERT INTO alternativas (id_pergunta, texto, correta) VALUES (%s, %s, %s)",
        [
            (id_pergunta, alternativa["texto"], alternativa["correta"])
            for alternativa in alternativas
        ],
    )


def atualizar_pergunta(id_quiz: int, id_pergunta: int, enunciado: str, alternativas: list[dict], link_midia: str | None = None) -> None:
    enunciado, alternativas_limpas, midia = normalizar_pergunta(
        enunciado, alternativas, link_midia
    )
    conn = _conectar()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE perguntas SET enunciado = %s, link_midia = %s WHERE id_pergunta = %s AND id_quiz = %s",
                (enunciado, midia, id_pergunta, id_quiz),
            )
            if cur.rowcount == 0:
                raise ValueError("Pergunta não encontrada neste quiz.")
            cur.execute("DELETE FROM alternativas WHERE id_pergunta = %s", (id_pergunta,))
            _inserir_alternativas(cur, id_pergunta, alternativas_limpas)
        conn.commit()
    finally:
        conn.close()


def cadastrar_pergunta(id_quiz: int, enunciado: str, alternativas: list[dict], link_midia: str | None = None) -> None:
    enunciado, alternativas_limpas, midia = normalizar_pergunta(
        enunciado, alternativas, link_midia
    )
    conn = _conectar()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COALESCE(MAX(ordem), 0) + 1 FROM perguntas WHERE id_quiz = %s",
                (id_quiz,),
            )
            proxima_ordem = cur.fetchone()[0]
            cur.execute(
                "INSERT INTO perguntas (id_quiz, enunciado, ordem, link_midia) VALUES (%s, %s, %s, %s) RETURNING id_pergunta",
                (id_quiz, enunciado, proxima_ordem, midia),
            )
            id_pergunta = int(cur.fetchone()[0])
            _inserir_alternativas(cur, id_pergunta, alternativas_limpas)
        conn.commit()
    finally:
        conn.close()


class RepositorioSessoesPostgres:
    def listar_perguntas(self, id_quiz: int) -> list[dict]:
        return listar_perguntas_do_quiz(id_quiz)

    def buscar_docente(self, id_quiz: int) -> int | None:
        return buscar_docente_do_quiz(id_quiz)

    def buscar_tempo(self, id_quiz: int) -> int | None:
        return buscar_tempo_quiz(id_quiz)

    def buscar_link_midia(self, id_quiz: int) -> str | None:
        return buscar_link_midia_quiz(id_quiz)

    def registrar(self, codigo: str, id_quiz: int, id_docente: int) -> int:
        return registrar_sessao(codigo, id_quiz, id_docente)


repositorio_sessoes = RepositorioSessoesPostgres()
