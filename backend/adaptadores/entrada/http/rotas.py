
import threading
import time
from collections import defaultdict

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel

_tentativas_login: dict[str, list[float]] = defaultdict(list)
_lock_login = threading.Lock()
_MAX_TENTATIVAS_LOGIN = 5
_JANELA_LOGIN_SEGUNDOS = 300


def _checar_rate_limit_login(email: str) -> None:
    agora = time.monotonic()
    with _lock_login:
        tentativas = _tentativas_login[email]
        tentativas[:] = [t for t in tentativas if agora - t < _JANELA_LOGIN_SEGUNDOS]
        if len(tentativas) >= _MAX_TENTATIVAS_LOGIN:
            raise HTTPException(status_code=429, detail="muitas tentativas, aguarde um minuto")


def _registrar_falha_login(email: str) -> None:
    with _lock_login:
        _tentativas_login[email].append(time.monotonic())


def _limpar_falhas_login(email: str) -> None:
    with _lock_login:
        _tentativas_login.pop(email, None)

from backend.adaptadores.saida.postgres.repositorio import (
    ADM, PROF,
    atualizar_pergunta,
    atualizar_quiz,
    buscar_docente_do_quiz,
    buscar_docente_por_email,
    buscar_docente_por_id,
    cadastrar_docente,
    cadastrar_pergunta,
    cadastrar_quiz,
    copiar_quiz,
    excluir_docente,
    listar_docentes,
    listar_perguntas_do_quiz,
    listar_quizzes,
    listar_quizzes_compartilhados,
)
from backend.adaptadores.saida.email.relatorio import enviar_email_teste
from backend.infraestrutura.seguranca import (
    gerar_token_docente,
    verificar_pin,
    verificar_token_docente,
)

router = APIRouter()


class LoginEntrada(BaseModel):
    email: str
    pin: str


class LoginSaida(BaseModel):
    id_docente: int
    nome: str
    email: str
    papel: str
    token: str


def docente_atual(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="login necessario")
    token = authorization.split(" ", 1)[1].strip()
    payload = verificar_token_docente(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="sessao expirada")
    try:
        id_docente = int(payload["id_docente"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="sessao invalida")
    docente = buscar_docente_por_id(id_docente)
    if docente is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="sessao invalida")
    return {
        "id_docente": docente[0],
        "nome": docente[1],
        "email": docente[2],
        "papel": docente[3],
    }


def admin_atual(atual: dict = Depends(docente_atual)) -> dict:
    if atual.get("papel") != ADM:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="sem permissao")
    return atual


def _id_docente(atual: dict) -> int:
    return int(atual["id_docente"])


@router.post("/diagnostico/email", tags=["diagnostico"])
def diagnosticar_email(atual: dict = Depends(admin_atual)):
    destino = str(atual["email"])
    try:
        enviar_email_teste(destino)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger_msg = f"{type(e).__name__}: {e}"
        raise HTTPException(status_code=502, detail=f"falha ao enviar email de teste: {logger_msg}")
    return {"ok": True, "destino": destino}


@router.post("/auth/login", response_model=LoginSaida, tags=["auth"])
def login(corpo: LoginEntrada):
    email = corpo.email.strip().lower()
    _checar_rate_limit_login(email)
    docente = buscar_docente_por_email(email)
    if docente is None or not verificar_pin(corpo.pin, docente[3]):
        _registrar_falha_login(email)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="email ou pin incorretos")
    _limpar_falhas_login(email)
    token = gerar_token_docente(docente[0], docente[2], docente[4])
    return LoginSaida(id_docente=docente[0], nome=docente[1], email=docente[2], papel=docente[4], token=token)


class DocenteSaida(BaseModel):
    id_docente: int
    nome: str
    email: str
    papel: str


class CadastrarDocenteEntrada(BaseModel):
    nome: str
    email: str
    pin: str
    papel: str = PROF


@router.get("/docentes", response_model=list[DocenteSaida], tags=["docentes"])
def listar(atual: dict = Depends(admin_atual)):
    return [DocenteSaida(id_docente=r[0], nome=r[1], email=r[2], papel=r[3]) for r in listar_docentes()]


@router.post("/docentes", status_code=status.HTTP_201_CREATED, tags=["docentes"])
def cadastrar(corpo: CadastrarDocenteEntrada, atual: dict = Depends(admin_atual)):
    try:
        cadastrar_docente(corpo.nome, corpo.email, corpo.pin, corpo.papel)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True}


@router.delete("/docentes/{id_alvo}", tags=["docentes"])
def excluir(id_alvo: int, atual: dict = Depends(admin_atual)):
    try:
        excluir_docente(id_alvo, _id_docente(atual))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"ok": True}


class QuizSaida(BaseModel):
    id_quiz: int
    titulo: str
    descricao: str | None
    id_docente_proprietario: int
    tempo_segundos: int | None = None
    nome_docente: str | None = None
    link_midia: str | None = None


class CadastrarQuizEntrada(BaseModel):
    id_docente_proprietario: int
    titulo: str
    descricao: str | None = None
    tempo_segundos: int | None = None
    link_midia: str | None = None


class AtualizarQuizEntrada(BaseModel):
    id_docente_proprietario: int
    titulo: str
    descricao: str | None = None
    tempo_segundos: int | None = None
    link_midia: str | None = None


class AlternativaEntrada(BaseModel):
    texto: str
    correta: bool = False


class PerguntaEntrada(BaseModel):
    enunciado: str
    alternativas: list[AlternativaEntrada]
    link_midia: str | None = None


class CopiarQuizEntrada(BaseModel):
    id_docente_destino: int


@router.get("/quizzes", response_model=list[QuizSaida], tags=["quizzes"])
def listar_quiz(id_docente: int, atual: dict = Depends(docente_atual)):
    if id_docente != _id_docente(atual) and atual.get("papel") != ADM:
        raise HTTPException(status_code=403, detail="sem acesso")
    return [QuizSaida(id_quiz=r[0], titulo=r[1], descricao=r[2], id_docente_proprietario=r[3], tempo_segundos=r[4], link_midia=r[5]) for r in listar_quizzes(id_docente)]


@router.get("/quizzes/compartilhados", response_model=list[QuizSaida], tags=["quizzes"])
def listar_compartilhados(id_docente: int, termo: str = "", atual: dict = Depends(docente_atual)):
    if id_docente != _id_docente(atual) and atual.get("papel") != ADM:
        raise HTTPException(status_code=403, detail="sem acesso")
    return [
        QuizSaida(
            id_quiz=r[0],
            titulo=r[1],
            descricao=r[2],
            id_docente_proprietario=r[3],
            tempo_segundos=r[4],
            nome_docente=r[5],
            link_midia=r[6],
        )
        for r in listar_quizzes_compartilhados(id_docente, termo)
    ]


@router.post("/quizzes", status_code=status.HTTP_201_CREATED, tags=["quizzes"])
def cadastrar_quiz_rota(corpo: CadastrarQuizEntrada, atual: dict = Depends(docente_atual)):
    if corpo.id_docente_proprietario != _id_docente(atual):
        raise HTTPException(status_code=403, detail="sem permissao")
    try:
        id_quiz = cadastrar_quiz(corpo.id_docente_proprietario, corpo.titulo, corpo.descricao, corpo.tempo_segundos, corpo.link_midia)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"id": id_quiz}


@router.post("/quizzes/{id_quiz}/copiar", status_code=status.HTTP_201_CREATED, tags=["quizzes"])
def copiar_quiz_rota(id_quiz: int, corpo: CopiarQuizEntrada, atual: dict = Depends(docente_atual)):
    if corpo.id_docente_destino != _id_docente(atual):
        raise HTTPException(status_code=403, detail="sem permissao")
    try:
        id_novo = copiar_quiz(id_quiz, corpo.id_docente_destino)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"id": id_novo}


@router.put("/quizzes/{id_quiz}", tags=["quizzes"])
def atualizar_quiz_rota(id_quiz: int, corpo: AtualizarQuizEntrada, atual: dict = Depends(docente_atual)):
    if corpo.id_docente_proprietario != _id_docente(atual):
        raise HTTPException(status_code=403, detail="sem permissao")
    try:
        atualizar_quiz(id_quiz, corpo.id_docente_proprietario, corpo.titulo, corpo.descricao, corpo.tempo_segundos, corpo.link_midia)
    except (PermissionError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True}


@router.put("/quizzes/{id_quiz}/perguntas/{id_pergunta}", tags=["quizzes"])
def atualizar_pergunta_rota(id_quiz: int, id_pergunta: int, corpo: PerguntaEntrada, atual: dict = Depends(docente_atual)):
    if buscar_docente_do_quiz(id_quiz) != _id_docente(atual):
        raise HTTPException(status_code=403, detail="sem permissao")
    try:
        atualizar_pergunta(
            id_quiz,
            id_pergunta,
            corpo.enunciado,
            [a.model_dump() if hasattr(a, "model_dump") else a.dict() for a in corpo.alternativas],
            corpo.link_midia,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True}


@router.get("/quizzes/{id_quiz}/perguntas", tags=["quizzes"])
def listar_perguntas_rota(id_quiz: int, atual: dict = Depends(docente_atual)):
    if buscar_docente_do_quiz(id_quiz) != _id_docente(atual) and atual.get("papel") != ADM:
        raise HTTPException(status_code=403, detail="sem permissao")
    return listar_perguntas_do_quiz(id_quiz)


@router.post("/quizzes/{id_quiz}/perguntas", status_code=status.HTTP_201_CREATED, tags=["quizzes"])
def cadastrar_pergunta_rota(id_quiz: int, corpo: PerguntaEntrada, atual: dict = Depends(docente_atual)):
    if buscar_docente_do_quiz(id_quiz) != _id_docente(atual):
        raise HTTPException(status_code=403, detail="sem permissao")
    try:
        cadastrar_pergunta(
            id_quiz,
            corpo.enunciado,
            [a.model_dump() if hasattr(a, "model_dump") else a.dict() for a in corpo.alternativas],
            corpo.link_midia,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True}
