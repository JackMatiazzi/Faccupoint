from __future__ import annotations

import flet as ft

from app.design_system.tokens import (
    ACCENT, BG_CARD, BG_PAGE, BTN_DANGER, BTN_H, BTN_RADIUS,
    CARD_PADDING_SM, CARD_RADIUS, CARD_W, FONT_CAPTION, FONT_SUBHEADING,
    INPUT_H, SPACE_MD, TEXT_DANGER, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_SUCCESS,
)
from app.design_system.components.campos import campo
from app.infra import api_client as api
from app.infra.api_client import ApiError


def tela_cadastro_docente(page: ft.Page) -> ft.View:
    erro = ft.Text("", color=TEXT_DANGER, size=FONT_CAPTION)
    sucesso = ft.Text("", color=TEXT_SUCCESS, size=FONT_CAPTION)

    campo_nome  = campo("Nome")
    campo_email = campo("Email")
    campo_pin   = campo("PIN", password=True, can_reveal_password=True, max_length=4, keyboard_type=ft.KeyboardType.NUMBER)
    campo_pin2  = campo("Confirmar PIN", password=True, can_reveal_password=True, max_length=4, keyboard_type=ft.KeyboardType.NUMBER)

    lista_exclusao = ft.Dropdown(
        label="Excluir docente",
        bgcolor=ACCENT,
        border_color=ACCENT,
        focused_border_color=TEXT_DANGER,
        color=TEXT_PRIMARY,
        label_style=ft.TextStyle(color=TEXT_SECONDARY),
        options=[],
    )
    _mapa_exclusao: dict[str, int] = {}

    def carregar_lista() -> None:
        try:
            docentes = api.listar_docentes()
        except ApiError:
            erro.value = "erro ao buscar lista"
            page.update()
            return
        lista_exclusao.options.clear()
        _mapa_exclusao.clear()
        for d in docentes:
            if d.id_docente == page.docente_id:
                continue
            rotulo = f"{d.nome} - {d.email}"
            lista_exclusao.options.append(ft.dropdown.Option(rotulo))
            _mapa_exclusao[rotulo] = d.id_docente
        page.update()

    def cadastrar(e) -> None:
        erro.value = ""
        sucesso.value = ""
        nome  = campo_nome.value.strip()
        email = campo_email.value.strip()
        pin   = campo_pin.value.strip()
        pin2  = campo_pin2.value.strip()

        if not nome:
            erro.value = "Informe o nome"
        elif not email or "@" not in email:
            erro.value = "Email inválido"
        elif len(pin) != 4 or not pin.isdigit():
            erro.value = "PIN deve ter 4 dígitos"
        elif pin != pin2:
            erro.value = "PINs não coincidem"
        else:
            try:
                api.inserir_docente(nome, email, pin)
                sucesso.value = "cadastrado!"
                campo_nome.value = campo_email.value = campo_pin.value = campo_pin2.value = ""
                carregar_lista()
            except ApiError as ex:
                erro.value = ex.detail

        page.update()

    def confirmar_exclusao(e) -> None:
        rotulo = lista_exclusao.value
        if not rotulo or rotulo not in _mapa_exclusao:
            return
        id_alvo = _mapa_exclusao[rotulo]

        def executar(e) -> None:
            dlg.open = False
            page.update()
            try:
                api.excluir_docente(id_alvo, page.docente_id)
                carregar_lista()
                lista_exclusao.value = None
            except ApiError as ex:
                erro.value = ex.detail
            page.update()

        def cancelar(e) -> None:
            dlg.open = False
            page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Tem certeza?"),
            content=ft.Text(f"Remover permanentemente?\n{rotulo}"),
            actions=[
                ft.TextButton("Cancelar", on_click=cancelar),
                ft.ElevatedButton("Remover", bgcolor=BTN_DANGER, color=TEXT_PRIMARY, on_click=executar),
            ],
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    carregar_lista()

    def _card(controls: list) -> ft.Container:
        return ft.Container(
            width=CARD_W,
            padding=ft.padding.all(CARD_PADDING_SM),
            bgcolor=BG_CARD,
            border_radius=CARD_RADIUS,
            content=ft.Column(spacing=SPACE_MD, controls=controls),
        )

    return ft.View(
        route="/cadastro-docente",
        bgcolor=BG_PAGE,
        appbar=ft.AppBar(
            title=ft.Text("Professores", color=TEXT_PRIMARY),
            bgcolor=BG_CARD,
            actions=[
                ft.TextButton(
                    "Voltar",
                    style=ft.ButtonStyle(color=TEXT_PRIMARY),
                    on_click=lambda _: page.go("/criacao-quiz"),
                )
            ],
        ),
        controls=[
            ft.Column(
                scroll=ft.ScrollMode.AUTO,
                expand=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        margin=ft.margin.only(top=CARD_PADDING_SM),
                        content=_card([
                            ft.Text("Novo professor", size=FONT_SUBHEADING, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                            campo_nome, campo_email, campo_pin, campo_pin2,
                            erro, sucesso,
                            ft.ElevatedButton(
                                text="Cadastrar", bgcolor=ACCENT, color=TEXT_PRIMARY,
                                width=CARD_W, height=INPUT_H,
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=BTN_RADIUS)),
                                on_click=cadastrar,
                            ),
                        ]),
                    ),
                    ft.Container(
                        margin=ft.margin.only(top=SPACE_MD, bottom=CARD_PADDING_SM),
                        content=_card([
                            ft.Text("Remover professor", size=FONT_SUBHEADING, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                            lista_exclusao,
                            ft.ElevatedButton(
                                text="Remover", bgcolor=BTN_DANGER, color=TEXT_PRIMARY,
                                width=CARD_W, height=INPUT_H,
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=BTN_RADIUS)),
                                on_click=confirmar_exclusao,
                            ),
                        ]),
                    ),
                ],
            )
        ],
    )
