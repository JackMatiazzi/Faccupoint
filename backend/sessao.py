from __future__ import annotations

import random
import string
from dataclasses import dataclass, field

from fastapi import WebSocket


@dataclass
class Participante:
    apelido: str
    ws: WebSocket
    id_participante: int | None = None
    pontos: int = 0
    resposta_atual: int | None = None


@dataclass
class Sessao:
    codigo: str
    id_sessao: int
    id_docente: int
    id_quiz: int
    perguntas: list[dict]
    tempo_questao: int = 20
    status: str = "lobby"
    questao_atual: int = -1
    participantes: dict[str, Participante] = field(default_factory=dict)
    professor_ws: WebSocket | None = None

    def total_participantes(self) -> int:
        return len(self.participantes)

    def todos_responderam(self) -> bool:
        if not self.participantes:
            return False
        return all(p.resposta_atual is not None for p in self.participantes.values())

    def pergunta_atual(self) -> dict | None:
        if 0 <= self.questao_atual < len(self.perguntas):
            return self.perguntas[self.questao_atual]
        return None

    def contagem_respostas(self) -> dict[int, int]:
        contagem: dict[int, int] = {}
        for p in self.participantes.values():
            if p.resposta_atual is not None:
                contagem[p.resposta_atual] = contagem.get(p.resposta_atual, 0) + 1
        return contagem


_sessoes: dict[str, Sessao] = {}


def gerar_codigo_sessao() -> str:
    while True:
        codigo = "".join(random.choices(string.digits, k=4))
        if codigo not in _sessoes:
            return codigo


def criar_sessao(codigo: str, id_sessao: int, id_docente: int, id_quiz: int, perguntas: list[dict], tempo_questao: int = 20) -> str:
    _sessoes[codigo] = Sessao(
        codigo=codigo,
        id_sessao=id_sessao,
        id_docente=id_docente,
        id_quiz=id_quiz,
        perguntas=perguntas,
        tempo_questao=tempo_questao,
    )
    return codigo


def obter_sessao(codigo: str) -> Sessao | None:
    return _sessoes.get(codigo)
