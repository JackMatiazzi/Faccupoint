from typing import Protocol

from backend.dominio.sessao import Sessao


class RepositorioSessoes(Protocol):
    def listar_perguntas(self, id_quiz: int) -> list[dict]: ...

    def buscar_docente(self, id_quiz: int) -> int | None: ...

    def buscar_tempo(self, id_quiz: int) -> int | None: ...

    def buscar_link_midia(self, id_quiz: int) -> str | None: ...

    def registrar(self, codigo: str, id_quiz: int, id_docente: int) -> int: ...


class ArmazenamentoSessoesAtivas(Protocol):
    def gerar_codigo(self) -> str: ...

    def criar(
        self,
        codigo: str,
        id_sessao: int,
        id_docente: int,
        id_quiz: int,
        perguntas: list[dict],
        tempo_questao: int,
        quiz_link_midia: str | None,
    ) -> Sessao: ...

    def obter(self, codigo: str) -> Sessao | None: ...

    def remover(self, codigo: str) -> None: ...
