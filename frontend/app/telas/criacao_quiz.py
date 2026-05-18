from __future__ import annotations

import flet as ft

from app.design_system.tokens import (
    ACCENT, BG_CARD, BG_INPUT, BG_PAGE, BORDER, BTN_H, BTN_RADIUS,
    CARD_PADDING_SM, CARD_RADIUS, FONT_BODY, FONT_CAPTION, FONT_TITLE,
    SPACE_MD, TEXT_DANGER, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_SUCCESS,
    BTN_GREEN_TEXT,
)
from app.design_system.components.campos import campo
from app.infra import api_client as api
from app.infra.api_client import ApiError

_NOVO = "+ Criar novo quiz"


def _painel(
    content: ft.Control,
    *,
    col: dict[str, int] | int | None = None,
    expand: bool | int | None = None,
) -> ft.Container:
    return ft.Container(
        expand=expand,
        col=col,
        padding=ft.padding.all(CARD_PADDING_SM),
        bgcolor=BG_CARD,
        border=ft.border.all(1, "#262633"),
        border_radius=CARD_RADIUS,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        content=content,
    )


def _titulo_secao(titulo: str, subtitulo: str | None = None) -> ft.Column:
    controles: list[ft.Control] = [
        ft.Text(titulo, size=FONT_TITLE, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY)
    ]
    if subtitulo:
        controles.append(ft.Text(subtitulo, size=FONT_CAPTION, color=TEXT_SECONDARY))
    return ft.Column(spacing=4, controls=controles)


def _botao_secundario(texto: str, on_click=None, *, width: int | None = None) -> ft.ElevatedButton:
    return ft.ElevatedButton(
        text=texto,
        bgcolor=BG_INPUT,
        color=TEXT_PRIMARY,
        width=width,
        height=BTN_H,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=BTN_RADIUS),
            side=ft.BorderSide(1, BORDER),
        ),
        on_click=on_click,
    )


def tela_criacao_quiz(page: ft.Page) -> ft.View:
    erro_quiz = ft.Text("", color=TEXT_DANGER, size=FONT_CAPTION)
    sucesso_quiz = ft.Text("", color=TEXT_SUCCESS, size=FONT_CAPTION)
    erro_perg = ft.Text("", color=TEXT_DANGER, size=FONT_CAPTION)
    sucesso_perg = ft.Text("", color=TEXT_SUCCESS, size=FONT_CAPTION)

    _mapa_quizzes: dict[str, int] = {}
    _mapa_tempo: dict[str, int] = {}
    _mapa_descricao: dict[str, str] = {}
    _id_quiz_atual: list[int | None] = [None]
    _id_pergunta_editando: list[int | None] = [None]
    _total_perguntas: list[int] = [0]

    lista_perguntas = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO)
    contador_perguntas = ft.Text("0 perguntas", color=TEXT_SECONDARY, size=FONT_CAPTION)

    selector = ft.Dropdown(
        label="Selecionar quiz",
        bgcolor=BG_INPUT,
        border_color=BORDER,
        focused_border_color=ACCENT,
        color=TEXT_PRIMARY,
        label_style=ft.TextStyle(color=TEXT_SECONDARY),
        options=[ft.dropdown.Option(_NOVO)],
    )

    campo_titulo = campo("Título")
    campo_descricao = campo("Descrição (opcional)", multiline=True, min_lines=2, max_lines=4)
    campo_tempo = campo(
        "Tempo por questão",
        keyboard_type=ft.KeyboardType.NUMBER,
        value="30",
        suffix_text="seg",
    )
    campo_enunciado = campo("Enunciado da pergunta", multiline=True, min_lines=3, max_lines=5)
    campo_midia = campo("Link de imagem ou vídeo (opcional)", hint_text="https://...")

    campo_busca_biblioteca = campo("Buscar quiz ou professor")
    resultados_biblioteca = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO)

    alternativas_col = ft.Column(spacing=8)
    _alternativas: list[tuple[ft.TextField, ft.Checkbox]] = []

    def _sincronizar_estado() -> None:
        tem_quiz = _id_quiz_atual[0] is not None
        tem_perguntas = _total_perguntas[0] > 0
        btn_adicionar.disabled = False
        btn_iniciar.disabled = not tem_quiz or not tem_perguntas
        hint_sala.visible = not tem_quiz
        if not tem_quiz:
            btn_iniciar.text = "Abrir sala com este quiz"
        elif not tem_perguntas:
            btn_iniciar.text = "Adicione perguntas para abrir a sala"
        else:
            nome = campo_titulo.value.strip() or "este quiz"
            btn_iniciar.text = f"Abrir sala: {nome}"

    def _adicionar_alternativa(texto: str = "", correta: bool = False, atualizar: bool = True) -> None:
        numero = len(_alternativas) + 1
        campo_alt = campo(f"Alternativa {numero}", value=texto)
        marcada = ft.Checkbox(
            label="Correta",
            value=correta,
            label_style=ft.TextStyle(color=TEXT_SECONDARY),
            check_color=BG_PAGE,
            fill_color=ACCENT,
        )
        _alternativas.append((campo_alt, marcada))

        def _remover(_):
            idx = next(i for i, (f, _) in enumerate(_alternativas) if f is campo_alt)
            _alternativas.pop(idx)
            alternativas_col.controls.pop(idx)
            for i, (f, _) in enumerate(_alternativas):
                f.label = f"Alternativa {i + 1}"
            page.update()

        alternativas_col.controls.append(
            ft.ResponsiveRow(
                columns=12,
                spacing=10,
                run_spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(col={"xs": 12, "sm": 12, "md": 8, "lg": 9}, content=campo_alt),
                    ft.Container(col={"xs": 6, "sm": 4, "md": 2, "lg": 1}, content=marcada),
                    ft.TextButton(
                        "Remover",
                        col={"xs": 6, "sm": 4, "md": 2},
                        style=ft.ButtonStyle(color=TEXT_SECONDARY),
                        on_click=_remover,
                    ),
                ],
            )
        )
        if atualizar:
            _sincronizar_estado()
            page.update()

    def _resetar_alternativas() -> None:
        _alternativas.clear()
        alternativas_col.controls.clear()
        _adicionar_alternativa(atualizar=False)
        _adicionar_alternativa(atualizar=False)

    btn_nova_alternativa = _botao_secundario(
        "+ Adicionar alternativa",
        on_click=lambda _: _adicionar_alternativa(),
    )

    titulo_card_quiz = ft.Text("Criar novo quiz", size=FONT_BODY, color=TEXT_PRIMARY, weight=ft.FontWeight.W_600)
    hint_sala = ft.Text(
        "Salve ou selecione um quiz com perguntas para abrir uma sala.",
        color=TEXT_SECONDARY,
        size=FONT_CAPTION,
        italic=True,
    )

    btn_iniciar = ft.ElevatedButton(
        text="Abrir sala com este quiz",
        bgcolor=TEXT_SUCCESS,
        color=BTN_GREEN_TEXT,
        height=BTN_H,
        disabled=True,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=BTN_RADIUS)),
        on_click=None,
    )

    btn_adicionar = ft.ElevatedButton(
        text="Salvar pergunta",
        bgcolor=ACCENT,
        color=TEXT_PRIMARY,
        height=BTN_H,
        expand=True,
        disabled=True,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=BTN_RADIUS)),
        on_click=None,
    )

    btn_cancelar_edicao = ft.TextButton(
        text="Cancelar edição",
        style=ft.ButtonStyle(color=TEXT_SECONDARY),
        visible=False,
        on_click=None,
    )

    def iniciar_aula(e) -> None:
        if _id_quiz_atual[0] is None:
            return
        page.quiz_sala_id = _id_quiz_atual[0]
        page.abrir_sala_automaticamente = True
        page.go("/sessao-professor")

    def carregar_biblioteca(e=None) -> None:
        termo = campo_busca_biblioteca.value.strip()
        try:
            quizzes = api.listar_quizzes_compartilhados(page.docente_id, termo)
        except ApiError:
            return
        resultados_biblioteca.controls.clear()
        for q in quizzes:
            resultados_biblioteca.controls.append(
                ft.Container(
                    padding=ft.padding.symmetric(vertical=10, horizontal=12),
                    bgcolor=BG_INPUT,
                    border=ft.border.all(1, BORDER),
                    border_radius=8,
                    content=ft.Column(
                        spacing=8,
                        controls=[
                            ft.Row(
                                spacing=8,
                                controls=[
                                    ft.Column(
                                        expand=True,
                                        spacing=2,
                                        controls=[
                                            ft.Text(q.titulo, color=TEXT_PRIMARY, size=FONT_CAPTION, weight=ft.FontWeight.W_600),
                                            ft.Text(q.nome_docente or "Professor", color=TEXT_SECONDARY, size=FONT_CAPTION),
                                        ],
                                    ),
                                ],
                            ),
                            ft.TextButton(
                                "Copiar para meus quizzes",
                                style=ft.ButtonStyle(color=TEXT_SUCCESS),
                                on_click=lambda _, quiz=q: usar_copia(quiz),
                            ),
                        ],
                    ),
                )
            )
        if not quizzes:
            resultados_biblioteca.controls.append(
                ft.Container(
                    padding=ft.padding.all(12),
                    bgcolor=BG_INPUT,
                    border_radius=8,
                    content=ft.Text("Nenhum quiz encontrado", color=TEXT_SECONDARY, size=FONT_CAPTION),
                )
            )
        page.update()

    def carregar_quizzes() -> None:
        try:
            quizzes = api.listar_quizzes_do_docente(page.docente_id)
        except ApiError:
            return
        selector.options.clear()
        selector.options.append(ft.dropdown.Option(_NOVO))
        _mapa_quizzes.clear()
        _mapa_tempo.clear()
        _mapa_descricao.clear()
        titulo_atual = _NOVO
        for q in quizzes:
            selector.options.append(ft.dropdown.Option(q.titulo))
            _mapa_quizzes[q.titulo] = q.id_quiz
            if q.id_quiz == _id_quiz_atual[0]:
                titulo_atual = q.titulo
            if q.tempo_segundos is not None:
                _mapa_tempo[q.titulo] = q.tempo_segundos
            if q.descricao:
                _mapa_descricao[q.titulo] = q.descricao
        selector.value = titulo_atual
        page.update()

    def usar_copia(quiz) -> None:
        erro_quiz.value = ""
        sucesso_quiz.value = ""
        try:
            id_novo = api.copiar_quiz(quiz.id_quiz, page.docente_id)
            _id_quiz_atual[0] = id_novo
            campo_titulo.value = quiz.titulo
            campo_descricao.value = quiz.descricao or ""
            campo_tempo.value = str(quiz.tempo_segundos) if quiz.tempo_segundos else "30"
            titulo_card_quiz.value = "Editar quiz"
            carregar_quizzes()
            _atualizar_lista_perguntas(id_novo)
            sucesso_quiz.value = "Quiz copiado."
        except ApiError as ex:
            erro_quiz.value = ex.detail
        page.update()

    def _limpar_pergunta() -> None:
        campo_enunciado.value = campo_midia.value = ""
        _resetar_alternativas()
        erro_perg.value = sucesso_perg.value = ""
        _id_pergunta_editando[0] = None
        btn_adicionar.text = "Salvar pergunta"
        btn_cancelar_edicao.visible = False

    def _atualizar_lista_perguntas(id_quiz: int) -> None:
        if id_quiz < 1:
            perguntas = []
        else:
            try:
                perguntas = api.listar_perguntas(id_quiz)
            except ApiError:
                perguntas = []
        lista_perguntas.controls.clear()
        for i, p in enumerate(perguntas):
            corretas = [a.texto for a in p.alternativas if a.correta]
            correta_texto = ", ".join(corretas) if corretas else "nenhuma"
            detalhes = [
                ft.Text(p.enunciado, color=TEXT_PRIMARY, size=FONT_CAPTION, weight=ft.FontWeight.W_600),
                ft.Text(f"Certa(s): {correta_texto}", color=TEXT_SUCCESS, size=FONT_CAPTION),
            ]
            if p.link_midia:
                detalhes.append(ft.Text(p.link_midia, color=TEXT_SECONDARY, size=FONT_CAPTION))

            def _fazer_on_click(pergunta):
                def _on_click(_):
                    _id_pergunta_editando[0] = pergunta.id_pergunta
                    campo_enunciado.value = pergunta.enunciado
                    campo_midia.value = pergunta.link_midia or ""
                    _alternativas.clear()
                    alternativas_col.controls.clear()
                    for alt in pergunta.alternativas:
                        _adicionar_alternativa(texto=alt.texto, correta=alt.correta, atualizar=False)
                    _sincronizar_estado()
                    btn_adicionar.text = "Salvar alterações"
                    btn_cancelar_edicao.visible = True
                    erro_perg.value = sucesso_perg.value = ""
                    page.update()
                return _on_click

            lista_perguntas.controls.append(
                ft.Container(
                    padding=ft.padding.all(12),
                    bgcolor=BG_INPUT,
                    border=ft.border.all(1, BORDER),
                    border_radius=8,
                    ink=True,
                    on_click=_fazer_on_click(p),
                    content=ft.Row(
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                        controls=[
                            ft.Container(
                                width=28,
                                height=28,
                                alignment=ft.alignment.center,
                                bgcolor=BG_CARD,
                                border_radius=14,
                                content=ft.Text(str(i + 1), color=TEXT_SECONDARY, size=FONT_CAPTION),
                            ),
                            ft.Column(spacing=4, expand=True, controls=detalhes),
                        ],
                    ),
                )
            )
        n = len(perguntas)
        _total_perguntas[0] = n
        contador_perguntas.value = f"{n} pergunta{'s' if n != 1 else ''}"
        if not perguntas:
            lista_perguntas.controls.append(
                ft.Container(
                    padding=ft.padding.all(16),
                    bgcolor=BG_INPUT,
                    border_radius=8,
                    content=ft.Text(
                        "As perguntas salvas aparecem aqui. Clique em uma delas para editar.",
                        color=TEXT_SECONDARY,
                        size=FONT_CAPTION,
                    ),
                )
            )
        _sincronizar_estado()

    def ao_selecionar(e) -> None:
        titulo = selector.value
        _limpar_pergunta()
        lista_perguntas.controls.clear()
        contador_perguntas.value = "0 perguntas"
        if titulo == _NOVO or titulo not in _mapa_quizzes:
            _id_quiz_atual[0] = None
            campo_titulo.value = campo_descricao.value = ""
            campo_tempo.value = "30"
            titulo_card_quiz.value = "Criar novo quiz"
            _atualizar_lista_perguntas(-1)
        else:
            _id_quiz_atual[0] = _mapa_quizzes[titulo]
            campo_titulo.value = titulo
            campo_descricao.value = _mapa_descricao.get(titulo, "")
            campo_tempo.value = str(_mapa_tempo.get(titulo, 30))
            titulo_card_quiz.value = "Editar quiz"
            _atualizar_lista_perguntas(_id_quiz_atual[0])
        _sincronizar_estado()
        page.update()

    def salvar_quiz(e) -> None:
        erro_quiz.value = ""
        sucesso_quiz.value = ""
        titulo = campo_titulo.value.strip()
        descricao = campo_descricao.value.strip() or None
        try:
            tempo = int(campo_tempo.value.strip()) if campo_tempo.value.strip() else None
        except ValueError:
            tempo = None

        if not titulo:
            erro_quiz.value = "Informe o título."
            page.update()
            return

        try:
            if _id_quiz_atual[0] is None:
                _id_quiz_atual[0] = api.criar_quiz(page.docente_id, titulo, descricao, tempo)
                sucesso_quiz.value = "Quiz criado."
                _atualizar_lista_perguntas(_id_quiz_atual[0])
            else:
                api.atualizar_quiz(_id_quiz_atual[0], page.docente_id, titulo, descricao, tempo)
                sucesso_quiz.value = "Quiz atualizado."
            _sincronizar_estado()
            carregar_quizzes()
        except ApiError as ex:
            erro_quiz.value = ex.detail

        page.update()

    def _on_adicionar(e) -> None:
        erro_perg.value = ""
        sucesso_perg.value = ""
        enunciado = campo_enunciado.value.strip()
        midia = campo_midia.value.strip() or None
        alternativas = [
            {"texto": campo_alt.value.strip(), "correta": bool(correta.value)}
            for campo_alt, correta in _alternativas
            if campo_alt.value.strip()
        ]

        if not enunciado or len(alternativas) < 2:
            erro_perg.value = "Informe o enunciado e ao menos duas alternativas."
            page.update()
            return

        if not any(a["correta"] for a in alternativas):
            erro_perg.value = "Marque a alternativa correta."
            page.update()
            return

        if _id_quiz_atual[0] is None:
            titulo = campo_titulo.value.strip()
            if not titulo:
                erro_perg.value = "Informe o título do quiz primeiro."
                page.update()
                return
            try:
                descricao = campo_descricao.value.strip() or None
                tempo = int(campo_tempo.value.strip()) if campo_tempo.value.strip() else None
                _id_quiz_atual[0] = api.criar_quiz(page.docente_id, titulo, descricao, tempo)
                _sincronizar_estado()
                carregar_quizzes()
            except ApiError as ex:
                erro_perg.value = ex.detail
                page.update()
                return

        try:
            if _id_pergunta_editando[0] is not None:
                api.atualizar_pergunta(
                    _id_quiz_atual[0],
                    _id_pergunta_editando[0],
                    enunciado,
                    alternativas,
                    link_midia=midia,
                )
                sucesso_perg.value = "Pergunta atualizada."
            else:
                api.salvar_pergunta(
                    _id_quiz_atual[0],
                    enunciado,
                    alternativas,
                    link_midia=midia,
                )
                sucesso_perg.value = "Pergunta adicionada."
            _limpar_pergunta()
            _atualizar_lista_perguntas(_id_quiz_atual[0])
        except ApiError as ex:
            erro_perg.value = ex.detail

        page.update()

    btn_iniciar.on_click = iniciar_aula
    btn_adicionar.on_click = _on_adicionar
    btn_cancelar_edicao.on_click = lambda _: (_limpar_pergunta(), page.update())

    def sair(e) -> None:
        page.docente_id = None
        page.docente_nome = ""
        page.docente_email = ""
        page.docente_papel = ""
        page.go("/")

    selector.on_change = ao_selecionar
    campo_busca_biblioteca.on_submit = carregar_biblioteca
    _resetar_alternativas()
    _sincronizar_estado()
    carregar_quizzes()
    carregar_biblioteca()
    _atualizar_lista_perguntas(-1)

    appbar_actions = []
    if page.docente_papel == "adm":
        appbar_actions.append(
            ft.TextButton(
                "Professores",
                style=ft.ButtonStyle(color=TEXT_SECONDARY),
                on_click=lambda _: page.go("/cadastro-docente"),
            )
        )
    appbar_actions.append(
        ft.TextButton(
            "Sair",
            style=ft.ButtonStyle(color=TEXT_SECONDARY),
            on_click=sair,
        )
    )

    btn_salvar_quiz = _botao_secundario("Salvar título e tempo", on_click=salvar_quiz)
    btn_buscar_biblioteca = _botao_secundario("Buscar", on_click=carregar_biblioteca)

    card_quiz = _painel(
        col={"xs": 12, "sm": 12, "md": 4, "lg": 3},
        content=ft.Column(
            spacing=SPACE_MD,
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[
                _titulo_secao("Quiz", "Escolha um quiz existente ou prepare um novo."),
                selector,
                btn_iniciar,
                hint_sala,
                ft.Divider(color=BORDER),
                titulo_card_quiz,
                campo_titulo,
                campo_descricao,
                campo_tempo,
                erro_quiz,
                sucesso_quiz,
                btn_salvar_quiz,
            ],
        ),
    )

    biblioteca_compartilhada = _painel(
        content=ft.Column(
            spacing=SPACE_MD,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[
                _titulo_secao(
                    "Biblioteca compartilhada",
                    "Explore quizzes de outros professores e copie os melhores para adaptar à sua aula.",
                ),
                ft.ResponsiveRow(
                    columns=12,
                    spacing=SPACE_MD,
                    run_spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Container(col={"xs": 12, "md": 9}, content=campo_busca_biblioteca),
                        ft.Container(col={"xs": 12, "md": 3}, content=btn_buscar_biblioteca),
                    ],
                ),
                ft.Container(height=190, content=resultados_biblioteca),
            ],
        ),
    )

    cabecalho_perguntas = ft.ResponsiveRow(
        columns=12,
        spacing=SPACE_MD,
        run_spacing=8,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(
                col={"xs": 12, "md": 9},
                content=_titulo_secao("Editor de perguntas", "Monte as alternativas e marque pelo menos uma correta."),
            ),
            ft.Container(
                col={"xs": 12, "md": 3},
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
                bgcolor=BG_INPUT,
                border=ft.border.all(1, BORDER),
                border_radius=18,
                content=contador_perguntas,
            ),
        ],
    )

    editor_pergunta = _painel(
        col={"xs": 12, "sm": 12, "lg": 8},
        content=ft.Column(
            spacing=SPACE_MD,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[
                _titulo_secao("Nova pergunta"),
                campo_enunciado,
                ft.Text("Alternativas", size=FONT_BODY, color=TEXT_PRIMARY, weight=ft.FontWeight.W_600),
                alternativas_col,
                btn_nova_alternativa,
                campo_midia,
                erro_perg,
                sucesso_perg,
                ft.ResponsiveRow(
                    columns=12,
                    spacing=8,
                    run_spacing=8,
                    controls=[
                        ft.Container(col={"xs": 12, "sm": 4, "md": 3}, content=btn_cancelar_edicao),
                        ft.Container(col={"xs": 12, "sm": 8, "md": 9}, content=btn_adicionar),
                    ],
                ),
            ],
        ),
    )

    perguntas_salvas = _painel(
        col={"xs": 12, "sm": 12, "lg": 4},
        content=ft.Column(
            spacing=SPACE_MD,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[
                _titulo_secao("Perguntas salvas", "Clique em uma pergunta para editar."),
                ft.Container(height=520, content=lista_perguntas),
            ],
        ),
    )

    return ft.View(
        route="/criacao-quiz",
        bgcolor=BG_PAGE,
        padding=0,
        scroll=ft.ScrollMode.AUTO,
        appbar=ft.AppBar(
            title=ft.Text(f"Olá, {page.docente_nome or 'Docente'}", color=TEXT_PRIMARY),
            bgcolor=BG_CARD,
            actions=appbar_actions,
        ),
        controls=[
            ft.Container(
                expand=True,
                padding=ft.padding.all(CARD_PADDING_SM),
                content=ft.ResponsiveRow(
                    columns=12,
                    spacing=SPACE_MD,
                    run_spacing=SPACE_MD,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    controls=[
                        card_quiz,
                        ft.Container(
                            col={"xs": 12, "sm": 12, "md": 8, "lg": 9},
                            content=ft.Column(
                                spacing=SPACE_MD,
                                controls=[
                                    biblioteca_compartilhada,
                                    cabecalho_perguntas,
                                    ft.ResponsiveRow(
                                        columns=12,
                                        spacing=SPACE_MD,
                                        run_spacing=SPACE_MD,
                                        vertical_alignment=ft.CrossAxisAlignment.START,
                                        controls=[editor_pergunta, perguntas_salvas],
                                    ),
                                ],
                            ),
                        ),
                    ],
                ),
            )
        ],
    )
