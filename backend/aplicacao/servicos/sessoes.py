from backend.aplicacao.portas.sessoes import (
    ArmazenamentoSessoesAtivas,
    RepositorioSessoes,
)


class ErroCasoUsoSessao(Exception):
    pass


class QuizSemPerguntas(ErroCasoUsoSessao):
    pass


class QuizNaoEncontrado(ErroCasoUsoSessao):
    pass


class SemPermissao(ErroCasoUsoSessao):
    pass


class AbrirSessao:
    def __init__(
        self,
        repositorio: RepositorioSessoes,
        armazenamento: ArmazenamentoSessoesAtivas,
        tempo_padrao: int = 30,
    ):
        self.repositorio = repositorio
        self.armazenamento = armazenamento
        self.tempo_padrao = tempo_padrao

    def executar(
        self,
        id_quiz: int,
        id_docente_atual: int,
        id_docente_anfitriao: int | None = None,
    ) -> str:
        perguntas = self.repositorio.listar_perguntas(id_quiz)
        if not perguntas:
            raise QuizSemPerguntas("quiz sem perguntas")

        proprietario = self.repositorio.buscar_docente(id_quiz)
        if proprietario is None:
            raise QuizNaoEncontrado("quiz nao encontrado")
        if id_docente_anfitriao is not None and id_docente_anfitriao != proprietario:
            raise SemPermissao("sem permissao")
        if id_docente_atual != proprietario:
            raise SemPermissao("sem permissao")

        tempo = self.repositorio.buscar_tempo(id_quiz) or self.tempo_padrao
        link_midia = self.repositorio.buscar_link_midia(id_quiz)
        codigo = self.armazenamento.gerar_codigo()
        id_sessao = self.repositorio.registrar(codigo, id_quiz, proprietario)
        self.armazenamento.criar(
            codigo,
            id_sessao,
            proprietario,
            id_quiz,
            perguntas,
            tempo,
            link_midia,
        )
        return codigo
