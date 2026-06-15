
import asyncio
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Participante:
    apelido: str
    ws: Any
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
    quiz_link_midia: str | None = None
    tempo_questao: int = 20
    status: str = "lobby"
    questao_atual: int = -1
    participantes: dict[str, Participante] = field(default_factory=dict)
    professor_ws: Any | None = None
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False, repr=False)

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

