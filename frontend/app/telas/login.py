from __future__ import annotations

import flet as ft

from app.design_system.tokens import (
    ACCENT, BG_CARD, BG_PAGE, BTN_H, BTN_RADIUS, CARD_PADDING,
    CARD_RADIUS, CARD_W, FONT_CAPTION, FONT_DISPLAY, SPACE_MD,
    TEXT_DANGER, TEXT_PRIMARY, TEXT_SECONDARY,
)
from app.design_system.components.campos import campo
from app.infra import api_client as api
from app.infra.api_client import ApiError


def tela_login(page: ft.Page) -> ft.View:
    erro = ft.Text("", color=TEXT_DANGER, size=FONT_CAPTION)

    aviso_conexao = ft.Row(
        visible=False,
        alignment=ft.MainAxisAlignment.CENTER,
        controls=[
            ft.Icon(ft.Icons.INFO_OUTLINE, color=TEXT_SECONDARY, size=14),
            ft.Text(
                "Primeira conexão com o banco, pode demorar de 1 a 2 min",
                color=TEXT_SECONDARY,
                size=FONT_CAPTION,
            ),
        ],
    )

    campo_email = campo("Email", hint_text="seu@email.com", keyboard_type=ft.KeyboardType.EMAIL)
    campo_pin = campo("PIN", hint_text="4 dígitos", password=True, can_reveal_password=True,
                      keyboard_type=ft.KeyboardType.NUMBER, max_length=4)

    btn_entrar = ft.ElevatedButton(
        text="Entrar",
        bgcolor=ACCENT,
        color=TEXT_PRIMARY,
        width=CARD_W,
        height=BTN_H,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=BTN_RADIUS)),
    )

    def entrar(e) -> None:
        erro.value = ""
        email = campo_email.value.strip().lower()
        pin = campo_pin.value.strip()

        if not email or "@" not in email:
            erro.value = "Email inválido"
            page.update()
            return
        if len(pin) != 4 or not pin.isdigit():
            erro.value = "PIN deve ter 4 dígitos"
            page.update()
            return

        aviso_conexao.visible = True
        btn_entrar.disabled = True
        page.update()

        try:
            docente = api.login(email, pin)
        except ApiError as ex:
            erro.value = ex.detail
            aviso_conexao.visible = False
            btn_entrar.disabled = False
            page.update()
            return

        page.docente_id = docente.id_docente
        page.docente_nome = docente.nome
        page.docente_email = docente.email
        page.docente_papel = docente.papel

        page.go("/criacao-quiz")

    btn_entrar.on_click = entrar
    campo_pin.on_submit = entrar

    card = ft.Container(
        width=CARD_W,
        padding=ft.padding.all(CARD_PADDING),
        bgcolor=BG_CARD,
        border_radius=CARD_RADIUS,
        content=ft.Column(
            spacing=SPACE_MD,
            controls=[
                ft.Text("FaccuPoint", size=FONT_DISPLAY, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Text("Para professores", size=FONT_CAPTION, color=TEXT_SECONDARY),
                ft.Divider(height=8, color="transparent"),
                campo_email,
                campo_pin,
                erro,
                btn_entrar,
                aviso_conexao,
            ],
        ),
    )

    return ft.View(
        route="/",
        bgcolor=BG_PAGE,
        padding=0,
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[card],
    )
