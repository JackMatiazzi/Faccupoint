
import flet as ft

from compartilhado.sistema_design.midia import eh_imagem, id_video_youtube, url_thumb_youtube
from compartilhado.sistema_design.tokens import (
    ACCENT, BG_CARD, BG_INPUT, BG_PAGE, BORDER, BTN_H, BTN_RADIUS,
    FONT_BODY, FONT_CAPTION, FONT_DISPLAY, FONT_TITLE, TEXT_DANGER, TEXT_PRIMARY,
    TEXT_SECONDARY, TEXT_SUCCESS, BTN_GREEN_TEXT,
    G4, G8, G12, G16, G24, G32, G48,
    CARD_RADIUS, CARD_PADDING_SM, SPACE_MD,
)
from compartilhado.sistema_design.componentes.botoes import (
    btn_primary as _btn_primary,
    btn_outline as _btn_outline,
    tab_btn as _tab,
)
from compartilhado.sistema_design.componentes.campos import campo
from professor.servicos import cliente_api as api
from professor.servicos.cliente_api import ApiError, Quiz

_NAV_W = G32 * 8 + G16
_LOGO_SZ = G32 + G4
_ICON_SZ = G48 + G32
_STEP_W = G32 * 5


def _step_card(num: str, titulo: str, desc: str, icon: str) -> ft.Container:
    return ft.Container(
        width=_STEP_W,
        padding=ft.padding.all(G16),
        bgcolor=BG_CARD,
        border=ft.border.all(1, BORDER),
        border_radius=CARD_RADIUS,
        content=ft.Column(
            spacing=G8,
            controls=[
                ft.Row(spacing=G8, controls=[
                    ft.Container(
                        width=G24, height=G24, alignment=ft.alignment.center,
                        bgcolor=ACCENT, border_radius=G16,
                        content=ft.Text(num, color=TEXT_PRIMARY, size=FONT_CAPTION, weight=ft.FontWeight.BOLD),
                    ),
                    ft.Icon(icon, color=TEXT_SECONDARY, size=G16),
                ]),
                ft.Text(titulo, color=TEXT_PRIMARY, size=FONT_BODY, weight=ft.FontWeight.W_600),
                ft.Text(desc, color=TEXT_SECONDARY, size=FONT_CAPTION),
            ],
        ),
    )


def _panel(content: ft.Control, *, expand=None, width=None) -> ft.Container:
    return ft.Container(
        expand=expand, width=width,
        padding=ft.padding.all(CARD_PADDING_SM),
        bgcolor=BG_CARD,
        border=ft.border.all(1, BORDER),
        border_radius=CARD_RADIUS,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        content=content,
    )


def _chip(text: str, icon: str | None = None) -> ft.Container:
    return ft.Container(
        padding=ft.padding.symmetric(horizontal=G12, vertical=G8),
        bgcolor=BG_INPUT,
        border=ft.border.all(1, BORDER),
        border_radius=G16,
        content=ft.Row(tight=True, spacing=G8, controls=[
            *([ft.Icon(icon, color=TEXT_SECONDARY, size=G12)] if icon else []),
            ft.Text(text, color=TEXT_PRIMARY, size=FONT_CAPTION),
        ]),
    )


def tela_painel_professor(page: ft.Page) -> ft.View:
    erro = ft.Text("", color=TEXT_DANGER, size=FONT_CAPTION)

    busca = campo("Buscar quiz", prefix_icon=ft.Icons.SEARCH, height=BTN_H)
    lista_quizzes = ft.Column(spacing=G8, scroll=ft.ScrollMode.AUTO)
    contador = ft.Text("0 quizzes", color=TEXT_PRIMARY, size=FONT_CAPTION)
    _quizzes = []
    _compartilhados = []
    _aba = ["meus"]

    _modo = ["idle"]
    quiz_atual = [getattr(page, "quiz_editando_id", None)]
    pergunta_atual = [None]

    titulo_f = campo("Título do quiz", value="Novo quiz")
    descricao_f = campo("Descrição (opcional)", multiline=True, min_lines=1, max_lines=3)
    tempo_f = campo("Tempo por questão", value="30", suffix_text="seg", keyboard_type=ft.KeyboardType.NUMBER)
    quiz_midia_f = campo("Imagem ou vídeo para todas as perguntas (opcional)", prefix_icon=ft.Icons.IMAGE_OUTLINED)
    quiz_midia_preview = ft.Container(visible=False, padding=ft.padding.symmetric(vertical=G8))
    enunciado_f = campo("Enunciado da pergunta", multiline=True, min_lines=4, max_lines=6)
    alternativas_col = ft.Column(spacing=G8)
    alternativas = []
    lista_perguntas = ft.Column(spacing=G8, scroll=ft.ScrollMode.AUTO)
    contador_perguntas = ft.Text("0 perguntas", color=TEXT_PRIMARY, size=FONT_CAPTION)
    status_salvo = ft.Text("Salvo", color=TEXT_SECONDARY, size=FONT_CAPTION)

    if not hasattr(page, "cache_perguntas_quiz"):
        page.cache_perguntas_quiz = {}
    perguntas_cache: dict = page.cache_perguntas_quiz
    perguntas_versao = [0]
    compartilhados_versao = [0]

    topbar_titulo = ft.Text("", color=TEXT_PRIMARY, size=FONT_BODY, weight=ft.FontWeight.W_600)
    topbar_status = ft.Row(
        visible=False, spacing=G8, vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Icon(ft.Icons.CHECK, color=TEXT_SECONDARY, size=G16),
            status_salvo,
        ],
    )
    topbar_voltar = ft.TextButton(
        "Meus quizzes", icon=ft.Icons.ARROW_BACK,
        style=ft.ButtonStyle(color=TEXT_SECONDARY),
        visible=False,
    )
    topbar_sep = ft.Text("/", color=TEXT_SECONDARY, visible=False)

    def _sync_topbar():
        if _modo[0] == "editor":
            topbar_titulo.value = titulo_f.value or "Novo quiz"
            topbar_voltar.visible = True
            topbar_sep.visible = True
            topbar_status.visible = True
        else:
            topbar_titulo.value = ""
            topbar_voltar.visible = False
            topbar_sep.visible = False
            topbar_status.visible = False
        page.update()

    def sair(e=None):
        api.limpar_token()
        page.docente_id = None
        page.docente_nome = page.docente_email = page.docente_papel = ""
        page.go("/")

    def abrir_sala(e=None):
        if _modo[0] == "editor":
            if quiz_atual[0] is None:
                salvar_quiz()
            if quiz_atual[0] is None:
                return
            page.quiz_sala_id = quiz_atual[0]
        page.abrir_sala_automaticamente = True
        page.go("/sessao-professor")

    btn_abrir_sala = _btn_primary("Abrir sala", on_click=abrir_sala, icon=ft.Icons.PLAY_ARROW)

    def entrar_modo_editor(quiz_id: int | None = None):
        _modo[0] = "editor"
        quiz_atual[0] = quiz_id
        page.quiz_editando_id = quiz_id

        if quiz_id:
            q = next((q for q in _quizzes if q.id_quiz == quiz_id), None)
            if q:
                titulo_f.value = q.titulo
                descricao_f.value = q.descricao or ""
                tempo_f.value = str(q.tempo_segundos or 30)
                quiz_midia_f.value = q.link_midia or ""
                _atualizar_quiz_midia_preview()
        else:
            titulo_f.value = "Novo quiz"
            descricao_f.value = ""
            tempo_f.value = "30"
            quiz_midia_f.value = ""
            quiz_midia_preview.visible = False
            status_salvo.value = "Alterações locais"

        limpar_pergunta(atualizar=False)
        renderizar_perguntas([], carregando=bool(quiz_id))
        area_principal.content = _montar_editor()
        _sync_topbar()
        renderizar_lista_quizzes()

        if quiz_id:
            if quiz_id in perguntas_cache:
                renderizar_perguntas(perguntas_cache[quiz_id])
            else:
                carregar_perguntas_async(quiz_id)

    def sair_modo_editor(e=None):
        _modo[0] = "idle"
        quiz_atual[0] = None
        page.quiz_editando_id = None
        area_principal.content = _montar_guia()
        _sync_topbar()
        renderizar_lista_quizzes()

    topbar_voltar.on_click = sair_modo_editor

    def selecionar_aba(nome: str):
        _aba[0] = nome
        tabs_row.controls = [
            ft.Container(expand=True, content=_tab("Meus quizzes", nome == "meus", on_click=lambda _: selecionar_aba("meus"))),
            ft.Container(expand=True, content=_tab("Compartilhados", nome == "compartilhados", on_click=lambda _: selecionar_aba("compartilhados"))),
        ]
        if nome == "compartilhados":
            carregar_compartilhados()
        else:
            renderizar_lista_quizzes()

    def copiar_biblioteca(quiz: Quiz):
        try:
            novo_id = api.copiar_quiz(quiz.id_quiz, page.docente_id)
            selecionar_aba("meus")
            carregar_quizzes(atualizar=False)
            entrar_modo_editor(novo_id)
        except ApiError as ex:
            erro.value = ex.detail
            page.update()

    def renderizar_lista_quizzes():
        termo = busca.value.strip().lower()
        fonte = _compartilhados if _aba[0] == "compartilhados" else _quizzes
        contador.value = f"{len(fonte)} quiz{'zes' if len(fonte) != 1 else ''}"
        lista_quizzes.controls.clear()

        filtrados = [
            q for q in fonte
            if not termo
            or termo in q.titulo.lower()
            or termo in (q.descricao or "").lower()
            or termo in (q.nome_docente or "").lower()
        ]

        for q in filtrados:
            selecionado = _aba[0] == "meus" and q.id_quiz == quiz_atual[0]
            if _aba[0] == "compartilhados":
                acao = ft.TextButton(
                    "Copiar", icon=ft.Icons.CONTENT_COPY,
                    style=ft.ButtonStyle(color=TEXT_SUCCESS),
                    on_click=lambda _, quiz=q: copiar_biblioteca(quiz),
                )
            else:
                acao = ft.IconButton(
                    icon=ft.Icons.PLAY_ARROW, icon_color=BTN_GREEN_TEXT, bgcolor=TEXT_SUCCESS,
                    tooltip="Abrir sala",
                    on_click=lambda _, quiz=q: (
                        setattr(page, "quiz_sala_id", quiz.id_quiz),
                        setattr(page, "abrir_sala_automaticamente", True),
                        page.go("/sessao-professor"),
                    ),
                )
            lista_quizzes.controls.append(
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=G12, vertical=G8),
                    bgcolor=BG_INPUT if selecionado else BG_CARD,
                    border=ft.border.all(1, ACCENT if selecionado else BORDER),
                    border_radius=G8,
                    ink=_aba[0] == "meus",
                    on_click=(lambda _, quiz=q: entrar_modo_editor(quiz.id_quiz)) if _aba[0] == "meus" else None,
                    content=ft.Row(
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Column(expand=True, spacing=G4, controls=[
                                ft.Text(q.titulo, color=TEXT_PRIMARY, size=FONT_CAPTION, weight=ft.FontWeight.W_600),
                                *([ft.Text(
                                    q.nome_docente or q.descricao,
                                    color=TEXT_SECONDARY, size=FONT_CAPTION, max_lines=1,
                                )] if (q.nome_docente or q.descricao) else []),
                                ft.Row(tight=True, spacing=0, controls=[
                                    ft.Container(
                                        padding=ft.padding.symmetric(horizontal=G8, vertical=G4),
                                        bgcolor=BG_PAGE, border=ft.border.all(1, BORDER), border_radius=G16,
                                        content=ft.Row(tight=True, spacing=G4, controls=[
                                            ft.Icon(ft.Icons.TIMER_OUTLINED, color=TEXT_SECONDARY, size=G12),
                                            ft.Text(f"{q.tempo_segundos or 30}s", color=TEXT_SECONDARY, size=FONT_CAPTION),
                                        ]),
                                    ),
                                ]),
                            ]),
                            acao,
                        ],
                    ),
                )
            )

        if not filtrados:
            lista_quizzes.controls.append(
                ft.Container(
                    padding=ft.padding.all(G16), bgcolor=BG_INPUT,
                    border=ft.border.all(1, BORDER), border_radius=G8,
                    content=ft.Text(
                        "Nenhum quiz compartilhado." if _aba[0] == "compartilhados" else "Nenhum quiz ainda.",
                        color=TEXT_SECONDARY, size=FONT_CAPTION,
                    ),
                )
            )

        if _modo[0] == "idle":
            _atualizar_centro_idle()

        page.update()

    def _atualizar_centro_idle():
        if not _quizzes and _aba[0] == "meus":
            centro.controls = [
                ft.Container(
                    width=_ICON_SZ, height=_ICON_SZ, alignment=ft.alignment.center,
                    bgcolor=ACCENT, border=ft.border.all(2, TEXT_PRIMARY), border_radius=BTN_RADIUS,
                    content=ft.Icon(ft.Icons.QUESTION_MARK, color=TEXT_PRIMARY, size=G32 + G8),
                ),
                ft.Text("Nenhum quiz cadastrado", color=TEXT_PRIMARY, size=FONT_DISPLAY, weight=ft.FontWeight.BOLD),
                ft.Text(
                    "Crie um quiz, adicione as perguntas e abra a sala para a turma.",
                    color=TEXT_SECONDARY, size=FONT_BODY, text_align=ft.TextAlign.CENTER,
                ),
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER, wrap=True, spacing=G8,
                    controls=[
                        _btn_primary("Criar quiz em branco", on_click=lambda _: entrar_modo_editor(), icon=ft.Icons.ADD),
                        _btn_outline("Ver biblioteca", on_click=lambda _: selecionar_aba("compartilhados"), icon=ft.Icons.CONTENT_COPY),
                    ],
                ),
            ]
        elif _aba[0] == "compartilhados":
            centro.controls = [
                ft.Container(
                    width=_ICON_SZ, height=_ICON_SZ, alignment=ft.alignment.center,
                    bgcolor=ACCENT, border=ft.border.all(2, TEXT_PRIMARY), border_radius=BTN_RADIUS,
                    content=ft.Icon(ft.Icons.CONTENT_COPY, color=TEXT_PRIMARY, size=G32 + G8),
                ),
                ft.Text("Copie para sua lista", color=TEXT_PRIMARY, size=FONT_DISPLAY, weight=ft.FontWeight.BOLD),
                ft.Text(
                    "Clique em Copiar para trazer o quiz para seus quizzes e editar antes de abrir a sala.",
                    color=TEXT_SECONDARY, size=FONT_BODY, text_align=ft.TextAlign.CENTER,
                ),
            ]
        else:
            centro.controls = [
                ft.Text("Fluxo da aula", color=TEXT_SECONDARY, size=FONT_CAPTION),
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER, spacing=G16, wrap=True,
                    controls=[
                        _step_card("1", "Selecione um quiz", "Escolha um quiz na lateral para editar perguntas.", ft.Icons.QUIZ_OUTLINED),
                        _step_card("2", "Edite as perguntas", "Adicione enunciados, alternativas e marque a resposta correta.", ft.Icons.EDIT_OUTLINED),
                        _step_card("3", "Abra a sala", "Alunos entram em tempo real com o código da sessão.", ft.Icons.PLAY_ARROW),
                    ],
                ),
            ]

    def carregar_quizzes(atualizar: bool = True):
        try:
            _quizzes[:] = api.listar_quizzes_do_docente(page.docente_id)
        except ApiError as ex:
            erro.value = ex.detail
            _quizzes.clear()
        if atualizar:
            renderizar_lista_quizzes()

    def carregar_compartilhados():
        compartilhados_versao[0] += 1
        versao = compartilhados_versao[0]
        lista_quizzes.controls.clear()
        lista_quizzes.controls.append(
            ft.Container(
                padding=ft.padding.all(G16), bgcolor=BG_INPUT,
                border=ft.border.all(1, BORDER), border_radius=G8,
                content=ft.Row(spacing=G8, controls=[
                    ft.ProgressRing(width=G16, height=G16, stroke_width=2),
                    ft.Text("Carregando...", color=TEXT_SECONDARY, size=FONT_CAPTION),
                ]),
            )
        )
        page.update()

        def buscar():
            try:
                dados = api.listar_quizzes_compartilhados(page.docente_id, busca.value.strip())
                if versao == compartilhados_versao[0] and _aba[0] == "compartilhados":
                    _compartilhados[:] = dados
                    renderizar_lista_quizzes()
            except ApiError as ex:
                if versao == compartilhados_versao[0]:
                    erro.value = ex.detail
                    _compartilhados.clear()
                    renderizar_lista_quizzes()

        page.run_thread(buscar)

    def salvar_quiz(e=None):
        nome = titulo_f.value.strip() or "Novo quiz"
        desc = descricao_f.value.strip() or None
        midia = quiz_midia_f.value.strip() or None
        try:
            t = int(tempo_f.value.strip()) if tempo_f.value.strip() else 30
        except ValueError:
            t = 30
        try:
            if quiz_atual[0] is None:
                quiz_atual[0] = api.criar_quiz(page.docente_id, nome, desc, t, link_midia=midia)
                page.quiz_editando_id = quiz_atual[0]
            else:
                api.atualizar_quiz(quiz_atual[0], page.docente_id, nome, desc, t, link_midia=midia)
            status_salvo.value = "salvo agora"
            carregar_quizzes(atualizar=False)
            renderizar_lista_quizzes()
        except ApiError as ex:
            erro.value = ex.detail
        page.update()

    def add_alternativa(texto: str = "", correta: bool = False, atualizar: bool = True):
        campo_alt = campo(f"Alternativa {len(alternativas) + 1}", value=texto)
        check = ft.Checkbox(value=correta, fill_color=ACCENT, check_color=BG_PAGE)
        alternativas.append((campo_alt, check))

        def remover(e):
            idx = next(i for i, (f, _) in enumerate(alternativas) if f is campo_alt)
            alternativas.pop(idx)
            alternativas_col.controls.pop(idx)
            for i, (f, _) in enumerate(alternativas):
                f.label = f"Alternativa {i + 1}"
            page.update()

        alternativas_col.controls.append(
            ft.Row(spacing=G8, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                ft.Icon(ft.Icons.DRAG_HANDLE, color=TEXT_SECONDARY, size=G16),
                ft.Container(expand=True, content=campo_alt),
                check,
                ft.Text("Correta", color=TEXT_SECONDARY, size=FONT_CAPTION),
                ft.IconButton(icon=ft.Icons.CLOSE, icon_color=TEXT_SECONDARY, tooltip="Remover", on_click=remover),
            ])
        )
        if atualizar:
            page.update()

    def reset_alternativas():
        alternativas.clear()
        alternativas_col.controls.clear()
        add_alternativa(atualizar=False)
        add_alternativa(atualizar=False)

    def _render_media_preview(url: str | None) -> ft.Control | None:
        if not url:
            return None
        video_id = id_video_youtube(url)
        if video_id:
            thumb = url_thumb_youtube(video_id)
            return ft.GestureDetector(
                on_tap=lambda _: page.launch_url(url),
                content=ft.Stack([
                    ft.Image(src=thumb, height=160, fit=ft.ImageFit.COVER, border_radius=CARD_RADIUS),
                    ft.Container(
                        height=160, alignment=ft.alignment.center,
                        content=ft.Icon(ft.Icons.PLAY_CIRCLE_FILL, color="white", size=48, opacity=0.9),
                    ),
                ]),
            )
        if eh_imagem(url):
            return ft.Image(src=url, height=200, fit=ft.ImageFit.CONTAIN, border_radius=CARD_RADIUS)
        return ft.TextButton(
            "Abrir mídia", icon=ft.Icons.OPEN_IN_NEW,
            on_click=lambda _: page.launch_url(url),
        )

    def _atualizar_quiz_midia_preview(e=None):
        url = quiz_midia_f.value.strip()
        ctrl = _render_media_preview(url)
        if ctrl:
            quiz_midia_preview.content = ctrl
            quiz_midia_preview.visible = True
        else:
            quiz_midia_preview.visible = False
        page.update()

    quiz_midia_f.on_change = _atualizar_quiz_midia_preview

    def limpar_pergunta(atualizar: bool = True):
        pergunta_atual[0] = None
        enunciado_f.value = ""
        reset_alternativas()
        salvar_pergunta_btn.text = "Salvar pergunta"
        erro.value = ""
        if atualizar:
            page.update()

    def carregar_pergunta(pergunta):
        pergunta_atual[0] = pergunta.id_pergunta
        enunciado_f.value = pergunta.enunciado
        alternativas.clear()
        alternativas_col.controls.clear()
        for alt in pergunta.alternativas:
            add_alternativa(alt.texto, alt.correta, atualizar=False)
        salvar_pergunta_btn.text = "Salvar alterações"
        page.update()

    def renderizar_perguntas(perguntas: list, *, carregando: bool = False):
        lista_perguntas.controls.clear()
        if carregando:
            contador_perguntas.value = "carregando..."
            btn_abrir_sala.disabled = True
            lista_perguntas.controls.append(
                ft.Container(
                    padding=ft.padding.all(G16), bgcolor=BG_INPUT, border_radius=G8,
                    content=ft.Row(spacing=G8, controls=[
                        ft.ProgressRing(width=G16, height=G16, stroke_width=2),
                        ft.Text("Carregando perguntas...", color=TEXT_SECONDARY, size=FONT_CAPTION),
                    ]),
                )
            )
            page.update()
            return

        contador_perguntas.value = f"{len(perguntas)} pergunta{'s' if len(perguntas) != 1 else ''}"
        btn_abrir_sala.disabled = len(perguntas) == 0

        for idx, p in enumerate(perguntas, start=1):
            corretas = [a.texto for a in p.alternativas if a.correta]
            lista_perguntas.controls.append(
                ft.Container(
                    padding=ft.padding.all(G12), bgcolor=BG_INPUT,
                    border=ft.border.all(1, BORDER), border_radius=G8,
                    ink=True, on_click=lambda _, pergunta=p: carregar_pergunta(pergunta),
                    content=ft.Column(spacing=G8, controls=[
                        ft.Row(controls=[
                            ft.Container(
                                width=G24 + G4, height=G24 + G4,
                                alignment=ft.alignment.center, bgcolor=BG_CARD, border_radius=G16 - 2,
                                content=ft.Text(str(idx), color=TEXT_PRIMARY, size=FONT_CAPTION),
                            ),
                            ft.Text(p.enunciado, color=TEXT_PRIMARY, size=FONT_CAPTION,
                                    weight=ft.FontWeight.W_600, expand=True),
                        ]),
                        ft.Row(wrap=True, spacing=G8, controls=[
                            _chip(f"{len(p.alternativas)} alts"),
                            *[_chip(c) for c in corretas[:2]],
                        ]),
                    ]),
                )
            )

        if not perguntas:
            lista_perguntas.controls.append(
                ft.Container(
                    padding=ft.padding.all(G16), bgcolor=BG_INPUT, border_radius=G8,
                    content=ft.Text("As perguntas salvas aparecem aqui.", color=TEXT_SECONDARY, size=FONT_CAPTION),
                )
            )
        page.update()

    def carregar_perguntas_async(id_quiz: int | None = None, *, force: bool = False):
        if id_quiz is None:
            id_quiz = quiz_atual[0]
        if not id_quiz:
            renderizar_perguntas([])
            return
        if not force and id_quiz in perguntas_cache:
            renderizar_perguntas(perguntas_cache[id_quiz])
            return

        perguntas_versao[0] += 1
        versao = perguntas_versao[0]
        renderizar_perguntas([], carregando=True)

        def buscar():
            try:
                perguntas = api.listar_perguntas(id_quiz)
                perguntas_cache[id_quiz] = perguntas
                if versao == perguntas_versao[0] and quiz_atual[0] == id_quiz:
                    renderizar_perguntas(perguntas)
            except ApiError as ex:
                if versao == perguntas_versao[0]:
                    erro.value = ex.detail
                    renderizar_perguntas([])

        page.run_thread(buscar)

    def salvar_pergunta(e=None):
        erro.value = ""
        texto = enunciado_f.value.strip()
        alts = [{"texto": f.value.strip(), "correta": bool(c.value)} for f, c in alternativas if f.value.strip()]
        if not texto or len(alts) < 2:
            erro.value = "Informe o enunciado e pelo menos duas alternativas."
            page.update()
            return
        if not any(a["correta"] for a in alts):
            erro.value = "Marque a alternativa correta."
            page.update()
            return

        id_pergunta = pergunta_atual[0]
        nome_quiz = titulo_f.value.strip() or "Novo quiz"
        desc_quiz = descricao_f.value.strip() or None
        midia_quiz = quiz_midia_f.value.strip() or None
        try:
            tempo_quiz = int(tempo_f.value.strip()) if tempo_f.value.strip() else 30
        except ValueError:
            tempo_quiz = 30

        salvar_pergunta_btn.disabled = True
        salvar_pergunta_btn.text = "Salvando..."
        status_salvo.value = "salvando..."
        page.update()

        def executar():
            try:
                if quiz_atual[0] is None:
                    quiz_atual[0] = api.criar_quiz(page.docente_id, nome_quiz, desc_quiz, tempo_quiz, link_midia=midia_quiz)
                    page.quiz_editando_id = quiz_atual[0]
                    carregar_quizzes(atualizar=False)
                if id_pergunta:
                    api.atualizar_pergunta(quiz_atual[0], id_pergunta, texto, alts)
                else:
                    api.salvar_pergunta(quiz_atual[0], texto, alts)
                status_salvo.value = "salvo agora"
                perguntas_cache.pop(quiz_atual[0], None)
                limpar_pergunta(atualizar=False)
                salvar_pergunta_btn.disabled = False
                salvar_pergunta_btn.text = "Salvar pergunta"
                renderizar_lista_quizzes()
                carregar_perguntas_async(quiz_atual[0], force=True)
            except ApiError as ex:
                erro.value = ex.detail
                salvar_pergunta_btn.disabled = False
                salvar_pergunta_btn.text = "Salvar pergunta" if id_pergunta is None else "Salvar alterações"
                page.update()

        page.run_thread(executar)

    salvar_pergunta_btn = _btn_primary("Salvar pergunta", on_click=salvar_pergunta, icon=ft.Icons.CHECK)
    nova_pergunta_btn   = _btn_primary("Nova pergunta",   on_click=lambda _: limpar_pergunta(), icon=ft.Icons.ADD)

    titulo_f.on_submit      = salvar_quiz
    descricao_f.on_submit   = salvar_quiz
    tempo_f.on_submit       = salvar_quiz
    quiz_midia_f.on_submit  = salvar_quiz
    quiz_midia_f.on_blur    = salvar_quiz

    centro = ft.Column(spacing=G12, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    def _montar_guia() -> ft.Container:
        _atualizar_centro_idle()
        return ft.Container(
            expand=True,
            padding=ft.padding.symmetric(horizontal=G48, vertical=G32),
            content=ft.Column(
                spacing=G16,
                controls=[
                    ft.Row(controls=[
                        ft.Column(expand=True, spacing=G8, controls=[
                            ft.Row(spacing=G8, controls=[
                                ft.Text("Meus quizzes", color=TEXT_PRIMARY, size=FONT_DISPLAY, weight=ft.FontWeight.BOLD),
                                ft.Container(
                                    padding=ft.padding.symmetric(horizontal=G12, vertical=G4),
                                    bgcolor=ACCENT, border=ft.border.all(1, TEXT_PRIMARY), border_radius=G16,
                                    content=contador,
                                ),
                            ]),
                            ft.Text("Crie, edite e abra salas em tempo real para sua turma.", color=TEXT_SECONDARY, size=FONT_CAPTION),
                        ]),
                        _btn_primary("Criar quiz em branco", on_click=lambda _: entrar_modo_editor(), icon=ft.Icons.ADD),
                    ]),
                    erro,
                    ft.Container(expand=True, alignment=ft.alignment.center, content=centro),
                ],
            ),
        )

    def _montar_editor() -> ft.Row:
        return ft.Row(
            expand=True,
            spacing=0,
            controls=[
                ft.Container(
                    expand=True,
                    padding=ft.padding.symmetric(horizontal=G32, vertical=G24),
                    content=ft.Column(
                        expand=True,
                        spacing=SPACE_MD,
                        controls=[
                            ft.Row(
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Column(expand=True, spacing=G8, controls=[titulo_f, descricao_f]),
                                    ft.Container(width=G8),
                                    ft.Container(
                                        padding=ft.padding.symmetric(horizontal=G12, vertical=G8),
                                        bgcolor=ACCENT, border_radius=G16,
                                        content=contador_perguntas,
                                    ),
                                ],
                            ),
                            tempo_f,
                            quiz_midia_f,
                            quiz_midia_preview,
                            erro,
                            _panel(
                                ft.Column(
                                    spacing=SPACE_MD,
                                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                                    controls=[
                                        ft.Text("Editando pergunta", color=TEXT_PRIMARY, size=FONT_TITLE, weight=ft.FontWeight.BOLD),
                                        enunciado_f,
                                        ft.Row(
                                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                            controls=[
                                                ft.Text("Alternativas", color=TEXT_PRIMARY, size=FONT_BODY, weight=ft.FontWeight.W_600),
                                                ft.Text("marque a(s) correta(s)", color=TEXT_SECONDARY, size=FONT_CAPTION),
                                            ],
                                        ),
                                        alternativas_col,
                                        _btn_outline("Adicionar alternativa", on_click=lambda _: add_alternativa(), icon=ft.Icons.ADD),
                                        salvar_pergunta_btn,
                                    ],
                                ),
                                expand=True,
                            ),
                        ],
                    ),
                ),
                ft.Container(
                    width=330,
                    padding=ft.padding.all(CARD_PADDING_SM),
                    bgcolor=BG_CARD,
                    border=ft.border.only(left=ft.BorderSide(1, BORDER)),
                    content=ft.Column(
                        expand=True,
                        spacing=SPACE_MD,
                        controls=[
                            ft.Row(controls=[
                                ft.Column(expand=True, spacing=G4, controls=[
                                    ft.Text("Perguntas do quiz", color=TEXT_PRIMARY, size=FONT_TITLE, weight=ft.FontWeight.BOLD),
                                    ft.Text("Clique para editar", color=TEXT_SECONDARY, size=FONT_CAPTION),
                                ]),
                                _chip("?", ft.Icons.HELP_OUTLINE),
                            ]),
                            nova_pergunta_btn,
                            ft.Container(expand=True, content=lista_perguntas),
                            ft.Text("Pronto para abrir sala", color=TEXT_SECONDARY, size=FONT_CAPTION),
                        ],
                    ),
                ),
            ],
        )

    busca.on_change = lambda _: carregar_compartilhados() if _aba[0] == "compartilhados" else renderizar_lista_quizzes()
    carregar_quizzes()

    tabs_row = ft.Row(
        spacing=G8,
        controls=[
            ft.Container(expand=True, content=_tab("Meus quizzes", True,  on_click=lambda _: selecionar_aba("meus"))),
            ft.Container(expand=True, content=_tab("Compartilhados", False, on_click=lambda _: selecionar_aba("compartilhados"))),
        ],
    )

    area_principal = ft.Container(expand=True, content=_montar_guia())

    if quiz_atual[0]:
        entrar_modo_editor(quiz_atual[0])

    nav = ft.Container(
        width=_NAV_W,
        padding=ft.padding.all(G16),
        bgcolor=BG_CARD,
        border=ft.border.only(right=ft.BorderSide(1, BORDER)),
        content=ft.Column(
            expand=True,
            spacing=G12,
            controls=[
                ft.Row(spacing=G8, controls=[
                    ft.Container(
                        width=_LOGO_SZ, height=_LOGO_SZ, alignment=ft.alignment.center,
                        bgcolor=ACCENT, border=ft.border.all(1, TEXT_PRIMARY), border_radius=BTN_RADIUS,
                        content=ft.Text("Fp", color=TEXT_PRIMARY, size=FONT_CAPTION, weight=ft.FontWeight.BOLD),
                    ),
                    ft.Column(spacing=0, controls=[
                        ft.Text("faccupoint", color=TEXT_PRIMARY, size=FONT_BODY, weight=ft.FontWeight.BOLD),
                        ft.Text("quizzes em sala", color=TEXT_SECONDARY, size=FONT_CAPTION),
                    ]),
                ]),
                tabs_row,
                busca,
                ft.Container(expand=True, content=lista_quizzes),
                _btn_outline("Novo quiz", on_click=lambda _: entrar_modo_editor(), icon=ft.Icons.ADD),
            ],
        ),
    )

    topbar_actions = [
        topbar_status,
        btn_abrir_sala,
        ft.OutlinedButton(
            text=page.docente_nome or "Professor",
            icon=ft.Icons.PERSON_OUTLINE, height=BTN_H,
            style=ft.ButtonStyle(color=TEXT_PRIMARY, side=ft.BorderSide(1, BORDER)),
            on_click=sair,
        ),
    ]
    if page.docente_papel == "adm":
        topbar_actions.insert(
            0,
            _btn_outline("Professores", on_click=lambda _: page.go("/admin-professores"), icon=ft.Icons.GROUP_OUTLINED),
        )

    return ft.View(
        route="/painel-professor",
        bgcolor=BG_PAGE,
        padding=0,
        controls=[
            ft.Column(
                expand=True,
                spacing=0,
                controls=[
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=G32, vertical=G16),
                        bgcolor=BG_CARD,
                        border=ft.border.only(bottom=ft.BorderSide(1, BORDER)),
                        content=ft.Row(
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                topbar_voltar,
                                topbar_sep,
                                topbar_titulo,
                                ft.Container(expand=True),
                                *topbar_actions,
                            ],
                        ),
                    ),
                    ft.Row(expand=True, spacing=0, controls=[nav, area_principal]),
                ],
            )
        ],
    )
