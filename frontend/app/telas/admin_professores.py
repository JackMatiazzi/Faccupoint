
import flet as ft

from app.design_system.tokens import (
    ACCENT, BG_CARD, BG_INPUT, BG_PAGE, BORDER, BTN_H,
    CARD_RADIUS, FONT_BODY, FONT_CAPTION, FONT_DISPLAY, FONT_TITLE,
    G4, G8, G12, G16, G24, G32, G48,
    TEXT_DANGER, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_SUCCESS, BTN_GREEN_TEXT,
)
from app.design_system.components.buttons import btn_primary, btn_outline, status_badge, counter_badge
from app.design_system.components.campos import campo
from app.infra import api_client as api
from app.infra.api_client import ApiError, Docente

_NAV_W = G32 * 8 + G16
_LOGO_SZ = G32 + G4
_AVT_SZ = G32 + G4


def tela_admin_professores(page: ft.Page) -> ft.View:
    erro = ft.Text("", color=TEXT_DANGER, size=FONT_CAPTION)
    sucesso = ft.Text("", color=TEXT_SUCCESS, size=FONT_CAPTION)
    busca = campo("Buscar por nome ou email", prefix_icon=ft.Icons.SEARCH, height=BTN_H)
    tabela = ft.Column(spacing=0, scroll=ft.ScrollMode.AUTO)
    contador = ft.Text("0 ativos", color=TEXT_PRIMARY, size=FONT_CAPTION)
    filtro = ["todos"]
    docentes = []

    nome_input = campo("Nome completo")
    email_input = campo("Email institucional")
    senha_input = campo("Senha inicial", value="1234", password=True, can_reveal_password=True, max_length=4)
    enviar_email = ft.Checkbox(
        label="Enviar email com link de primeiro acesso",
        value=True,
        label_style=ft.TextStyle(color=TEXT_SECONDARY),
        fill_color=ACCENT,
        check_color=BG_PAGE,
    )

    def iniciais(nome: str) -> str:
        partes = [p[0].upper() for p in nome.split() if p]
        return "".join(partes[:2]) or "P"

    def gerar_senha(e=None) -> None:
        import random
        senha_input.value = f"{random.randint(1000, 9999)}"
        page.update()

    def abrir_modal(e=None) -> None:
        erro.value = ""
        sucesso.value = ""

        def fechar(ev=None) -> None:
            dlg.open = False
            page.update()

        def cadastrar(ev=None) -> None:
            erro.value = ""
            sucesso.value = ""
            nome = nome_input.value.strip()
            email = email_input.value.strip()
            senha = senha_input.value.strip()
            if not nome:
                erro.value = "Informe o nome."
            elif not email or "@" not in email:
                erro.value = "Email invalido."
            elif len(senha) != 4 or not senha.isdigit():
                erro.value = "Senha inicial deve ter 4 digitos."
            else:
                try:
                    api.inserir_docente(nome, email, senha)
                    nome_input.value = ""
                    email_input.value = ""
                    senha_input.value = "1234"
                    sucesso.value = "Professor cadastrado."
                    carregar_docentes()
                    fechar()
                except ApiError as ex:
                    erro.value = ex.detail
            page.update()

        dlg = ft.AlertDialog(
            modal=True,
            bgcolor=BG_CARD,
            title=ft.Row(
                controls=[
                    ft.Text("Adicionar professor", color=TEXT_PRIMARY, size=FONT_TITLE, weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                    ft.IconButton(icon=ft.Icons.CLOSE, icon_color=TEXT_SECONDARY, on_click=fechar),
                ],
            ),
            content=ft.Container(
                width=G32 * 16,  # 512
                content=ft.Column(
                    tight=True,
                    spacing=G16,
                    controls=[
                        ft.Text("O professor recebe as credenciais para acessar o painel dele.", color=TEXT_SECONDARY, size=FONT_CAPTION),
                        nome_input,
                        email_input,
                        ft.Row(
                            spacing=G8,
                            controls=[
                                ft.Container(expand=True, content=senha_input),
                                btn_outline("Gerar nova", on_click=gerar_senha, icon=ft.Icons.REFRESH),
                            ],
                        ),
                        enviar_email,
                        erro,
                        sucesso,
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Cancelar", style=ft.ButtonStyle(color=TEXT_SECONDARY), on_click=fechar),
                btn_primary("Cadastrar professor", on_click=cadastrar, icon=ft.Icons.CHECK),
            ],
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def remover_docente(docente: Docente) -> None:
        if docente.id_docente == page.docente_id:
            return
        try:
            api.excluir_docente(docente.id_docente)
            carregar_docentes()
        except ApiError as ex:
            erro.value = ex.detail
            page.update()

    def set_filtro(valor: str) -> None:
        filtro[0] = valor
        renderizar_tabela()

    def carregar_docentes() -> None:
        try:
            docentes[:] = api.listar_docentes()
        except ApiError as ex:
            erro.value = ex.detail
            docentes.clear()
        renderizar_tabela()

    def renderizar_tabela() -> None:
        termo = busca.value.strip().lower()
        rows = []
        for d in docentes:
            pendente = d.papel != "adm" and d.email.endswith(".pendente")
            if filtro[0] == "ativos" and pendente:
                continue
            if filtro[0] == "pendentes" and not pendente:
                continue
            if termo and termo not in d.nome.lower() and termo not in d.email.lower():
                continue
            rows.append(d)

        contador.value = f"{len([d for d in docentes if d.papel != 'adm'])} ativos"
        tabela.controls.clear()
        tabela.controls.append(
            ft.Container(
                padding=ft.padding.symmetric(horizontal=G16, vertical=G12),
                border=ft.border.all(1, BORDER),
                content=ft.Row(
                    controls=[
                        ft.Text("Nome", color=TEXT_SECONDARY, size=FONT_CAPTION, expand=2),
                        ft.Text("Email", color=TEXT_SECONDARY, size=FONT_CAPTION, expand=2),
                        ft.Text("Status", color=TEXT_SECONDARY, size=FONT_CAPTION, expand=1),
                        ft.Text("Ações", color=TEXT_SECONDARY, size=FONT_CAPTION, width=G48),
                    ],
                ),
            )
        )
        for d in rows:
            tabela.controls.append(
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=G16, vertical=G12),
                    border=ft.border.only(bottom=ft.BorderSide(1, BORDER)),
                    content=ft.Row(
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Row(
                                expand=2,
                                spacing=G8,
                                controls=[
                                    ft.Container(
                                        width=_AVT_SZ,
                                        height=_AVT_SZ,
                                        alignment=ft.alignment.center,
                                        bgcolor=ACCENT,
                                        border_radius=_AVT_SZ // 2,
                                        content=ft.Text(iniciais(d.nome), color=TEXT_PRIMARY, size=FONT_CAPTION, weight=ft.FontWeight.BOLD),
                                    ),
                                    ft.Text(d.nome, color=TEXT_PRIMARY, size=FONT_BODY, weight=ft.FontWeight.W_600),
                                ],
                            ),
                            ft.Text(d.email, color=TEXT_SECONDARY, size=FONT_CAPTION, expand=2),
                            ft.Container(expand=1, content=status_badge("ADMIN" if d.papel == "adm" else "ATIVO", active=True)),
                            ft.Row(
                                width=G48,
                                controls=[
                                    ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color=TEXT_DANGER, tooltip="Remover", on_click=lambda _, docente=d: remover_docente(docente)),
                                ],
                            ),
                        ],
                    ),
                )
            )
        if not rows:
            tabela.controls.append(
                ft.Container(
                    padding=ft.padding.all(G16),
                    bgcolor=BG_INPUT,
                    content=ft.Text("Nenhum professor encontrado.", color=TEXT_SECONDARY, size=FONT_CAPTION),
                )
            )
        page.update()

    busca.on_change = lambda _: renderizar_tabela()
    carregar_docentes()

    sidebar = ft.Container(
        width=_NAV_W,
        bgcolor=BG_CARD,
        padding=ft.padding.all(G16),
        border=ft.border.only(right=ft.BorderSide(1, BORDER)),
        content=ft.Column(
            spacing=G12,
            controls=[
                ft.Row(
                    spacing=G8,
                    controls=[
                        ft.Container(
                            width=_LOGO_SZ,
                            height=_LOGO_SZ,
                            alignment=ft.alignment.center,
                            bgcolor=ACCENT,
                            border=ft.border.all(1, TEXT_PRIMARY),
                            border_radius=G8,
                            content=ft.Text("Fp", color=TEXT_PRIMARY, size=FONT_CAPTION, weight=ft.FontWeight.BOLD),
                        ),
                        ft.Column(
                            spacing=0,
                            controls=[
                                ft.Text("faccupoint", color=TEXT_PRIMARY, size=FONT_BODY, weight=ft.FontWeight.BOLD),
                                ft.Text("quizzes em sala", color=TEXT_SECONDARY, size=FONT_CAPTION),
                            ],
                        ),
                    ],
                ),
                ft.Text("ADMINISTRAÇÃO", color=TEXT_SECONDARY, size=FONT_CAPTION),
                btn_outline("Visão geral", on_click=lambda _: page.go("/painel-professor"), icon=ft.Icons.DASHBOARD_OUTLINED),
                btn_primary("Professores", icon=ft.Icons.GROUP_OUTLINED),
                btn_outline("Quizzes", on_click=lambda _: page.go("/painel-professor"), icon=ft.Icons.QUIZ_OUTLINED),
            ],
        ),
    )

    return ft.View(
        route="/admin-professores",
        bgcolor=BG_PAGE,
        padding=0,
        controls=[
            ft.Row(
                expand=True,
                spacing=0,
                controls=[
                    sidebar,
                    ft.Container(
                        expand=True,
                        padding=ft.padding.all(G32),
                        content=ft.Column(
                            spacing=G16,
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Column(
                                            expand=True,
                                            spacing=G8,
                                            controls=[
                                                ft.Row(
                                                    spacing=G8,
                                                    controls=[
                                                        ft.Text("Professores", color=TEXT_PRIMARY, size=FONT_DISPLAY, weight=ft.FontWeight.BOLD),
                                                        counter_badge(contador),
                                                    ],
                                                ),
                                                ft.Text("Cadastre, edite e remova professores.", color=TEXT_SECONDARY, size=FONT_CAPTION),
                                            ],
                                        ),
                                        btn_primary("Adicionar professor", on_click=abrir_modal, icon=ft.Icons.PERSON_ADD_ALT),
                                    ],
                                ),
                                ft.Row(
                                    spacing=G8,
                                    controls=[
                                        ft.Container(expand=True, content=busca),
                                        btn_outline("Todos", on_click=lambda _: set_filtro("todos")),
                                        btn_outline("Ativos", on_click=lambda _: set_filtro("ativos")),
                                        btn_outline("Pendentes", on_click=lambda _: set_filtro("pendentes")),
                                    ],
                                ),
                                erro,
                                ft.Container(expand=True, content=tabela),
                            ],
                        ),
                    ),
                ],
            )
        ],
    )
