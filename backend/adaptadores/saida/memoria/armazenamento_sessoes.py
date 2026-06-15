import secrets
import string

from backend.dominio.sessao import Sessao

_CHARS_CODIGO = "".join(
    c for c in string.ascii_uppercase + string.digits if c not in "OI01"
)


class ArmazenamentoSessoesMemoria:
    def __init__(self):
        self._sessoes: dict[str, Sessao] = {}

    def gerar_codigo(self) -> str:
        while True:
            codigo = "".join(secrets.choice(_CHARS_CODIGO) for _ in range(6))
            if codigo not in self._sessoes:
                return codigo

    def criar(
        self,
        codigo: str,
        id_sessao: int,
        id_docente: int,
        id_quiz: int,
        perguntas: list[dict],
        tempo_questao: int = 20,
        quiz_link_midia: str | None = None,
    ) -> Sessao:
        sessao = Sessao(
            codigo=codigo,
            id_sessao=id_sessao,
            id_docente=id_docente,
            id_quiz=id_quiz,
            perguntas=perguntas,
            quiz_link_midia=quiz_link_midia,
            tempo_questao=tempo_questao,
        )
        self._sessoes[codigo] = sessao
        return sessao

    def obter(self, codigo: str) -> Sessao | None:
        return self._sessoes.get(codigo)

    def remover(self, codigo: str) -> None:
        self._sessoes.pop(codigo, None)

armazenamento_sessoes_ativas = ArmazenamentoSessoesMemoria()
