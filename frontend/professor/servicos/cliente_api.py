import os
from dataclasses import dataclass
from dotenv import load_dotenv
from urllib.parse import urlparse

try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

import requests
from urllib3.exceptions import InsecureRequestWarning

load_dotenv()
_BASE = os.getenv("API_URL", "https://faccupoint-backend.onrender.com")
_TOKEN: str | None = None
_HOST_API = urlparse(_BASE).hostname or ""


def _pode_ignorar_ssl_institucional() -> bool:
    return _HOST_API == "faccupoint-backend.onrender.com"


class ApiError(Exception):
    def __init__(self, status: int, detail: str):
        self.status = status
        self.detail = detail
        super().__init__(f"[{status}] {detail}")


def _req(method: str, path: str, **kwargs) -> dict | list:
    headers = dict(kwargs.pop("headers", {}) or {})
    if _TOKEN:
        headers["Authorization"] = f"Bearer {_TOKEN}"
    try:
        r = requests.request(method, f"{_BASE}{path}", timeout=60, headers=headers, **kwargs)
    except requests.Timeout:
        raise ApiError(0, "backend demorou para responder")
    except requests.exceptions.SSLError:
        if not _pode_ignorar_ssl_institucional():
            raise ApiError(0, "falha de certificado da rede")
        requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
        try:
            r = requests.request(
                method,
                f"{_BASE}{path}",
                timeout=60,
                headers=headers,
                verify=False,
                **kwargs,
            )
        except requests.Timeout:
            raise ApiError(0, "backend demorou para responder")
        except requests.ConnectionError:
            raise ApiError(0, "backend fora do ar")
    except requests.exceptions.ProxyError:
        raise ApiError(0, "proxy da rede bloqueou a conexao")
    except requests.ConnectionError:
        raise ApiError(0, "backend fora do ar")
    if not r.ok:
        try:
            detail = r.json().get("detail", r.text)
        except Exception:
            detail = r.text
        raise ApiError(r.status_code, str(detail))
    return r.json()


@dataclass
class Docente:
    id_docente: int
    nome: str
    email: str
    papel: str
    token: str | None = None


def limpar_token() -> None:
    global _TOKEN
    _TOKEN = None


def auth_token() -> str | None:
    return _TOKEN


def api_url() -> str:
    return _BASE


def websocket_url(path: str) -> str:
    base = urlparse(_BASE)
    scheme = "wss" if base.scheme == "https" else "ws"
    return f"{scheme}://{base.netloc}/{path.lstrip('/')}"


def login(email: str, pin: str) -> Docente:
    global _TOKEN
    data = _req("POST", "/auth/login", json={"email": email, "pin": pin})
    _TOKEN = str(data["token"])
    return Docente(**data)


def listar_docentes() -> list[Docente]:
    rows = _req("GET", "/docentes")
    return [Docente(**r) for r in rows]


def inserir_docente(nome: str, email: str, pin: str, papel: str = "prof") -> None:
    _req("POST", "/docentes", json={
        "nome": nome, "email": email, "pin": pin, "papel": papel,
    })


def excluir_docente(id_docente: int) -> None:
    _req("DELETE", f"/docentes/{id_docente}")


@dataclass
class Quiz:
    id_quiz: int
    titulo: str
    descricao: str | None
    id_docente_proprietario: int
    tempo_segundos: int | None = None
    nome_docente: str | None = None
    link_midia: str | None = None


@dataclass
class Alternativa:
    id_alternativa: int
    texto: str
    correta: bool


@dataclass
class Pergunta:
    id_pergunta: int
    enunciado: str
    ordem: int
    alternativas: list[Alternativa]
    link_midia: str | None = None


def listar_quizzes_do_docente(id_docente: int) -> list[Quiz]:
    rows = _req("GET", "/quizzes", params={"id_docente": id_docente})
    return [Quiz(**{k: v for k, v in r.items() if k in Quiz.__dataclass_fields__}) for r in rows]


def listar_quizzes_compartilhados(id_docente: int, termo: str = "") -> list[Quiz]:
    rows = _req("GET", "/quizzes/compartilhados", params={
        "id_docente": id_docente,
        "termo": termo,
    })
    return [Quiz(**{k: v for k, v in r.items() if k in Quiz.__dataclass_fields__}) for r in rows]


def criar_quiz(id_docente: int, titulo: str, descricao: str | None, tempo_segundos: int | None = None, link_midia: str | None = None) -> int:
    data = _req("POST", "/quizzes", json={
        "titulo": titulo,
        "descricao": descricao,
        "id_docente_proprietario": id_docente,
        "tempo_segundos": tempo_segundos,
        "link_midia": link_midia,
    })
    return int(data["id"])


def copiar_quiz(id_quiz: int, id_docente_destino: int) -> int:
    data = _req("POST", f"/quizzes/{id_quiz}/copiar", json={
        "id_docente_destino": id_docente_destino,
    })
    return int(data["id"])


def atualizar_quiz(id_quiz: int, id_docente: int, titulo: str, descricao: str | None, tempo_segundos: int | None = None, link_midia: str | None = None) -> None:
    _req("PUT", f"/quizzes/{id_quiz}", json={
        "titulo": titulo,
        "descricao": descricao,
        "id_docente_proprietario": id_docente,
        "tempo_segundos": tempo_segundos,
        "link_midia": link_midia,
    })


def listar_perguntas(id_quiz: int) -> list[Pergunta]:
    rows = _req("GET", f"/quizzes/{id_quiz}/perguntas")
    result = []
    for r in rows:
        alts = [
            Alternativa(id_alternativa=a["id"], texto=a["texto"], correta=a["correta"])
            for a in r.get("alternativas", [])
        ]
        result.append(Pergunta(id_pergunta=r["id_pergunta"], enunciado=r["enunciado"], ordem=r["ordem"], alternativas=alts, link_midia=r.get("link_midia")))
    return result


def salvar_pergunta(id_quiz: int, enunciado: str, alternativas: list[dict], link_midia: str | None = None) -> None:
    _req("POST", f"/quizzes/{id_quiz}/perguntas", json={
        "enunciado": enunciado,
        "alternativas": alternativas,
        "link_midia": link_midia,
    })


def atualizar_pergunta(id_quiz: int, id_pergunta: int, enunciado: str, alternativas: list[dict], link_midia: str | None = None) -> None:
    _req("PUT", f"/quizzes/{id_quiz}/perguntas/{id_pergunta}", json={
        "enunciado": enunciado,
        "alternativas": alternativas,
        "link_midia": link_midia,
    })


def criar_sessao(id_quiz: int, id_docente_anfitriao: int | None = None) -> str:
    corpo = {"id_quiz": id_quiz}
    if id_docente_anfitriao is not None:
        corpo["id_docente_anfitriao"] = id_docente_anfitriao
    data = _req("POST", "/sessoes", json=corpo)
    return str(data["codigo"])


def iniciar_sessao(codigo: str) -> None:
    _req("POST", f"/sessoes/{codigo}/iniciar")
