
import re
from urllib.parse import urlparse

import flet as ft

from compartilhado.navegacao import query_valor
from compartilhado.sistema_design.tokens import (
    ACCENT, BG_CARD, BG_INPUT, BG_PAGE, BORDER, BTN_H, BTN_RADIUS,
    CARD_PADDING, CARD_RADIUS, FONT_CAPTION, FONT_DISPLAY,
    SPACE_MD, TEXT_DANGER, TEXT_PRIMARY, TEXT_SECONDARY,
)


def tela_entrar(page: ft.Page) -> ft.View:
    erro = ft.Text("", color=TEXT_DANGER, size=FONT_CAPTION)

    parsed = urlparse(getattr(page, "url", "") or "")
    _ip = query_valor(page, "api_host") or parsed.hostname or page.sessao_ip or "127.0.0.1"
    _api_porta = query_valor(page, "api_port") or query_valor(page, "api") or page.sessao_porta or "8000"
    _api_secure = (query_valor(page, "api_secure") or "0") == "1"
    _codigo_url = (query_valor(page, "codigo") or page.sessao_codigo or "").upper()

    page.sessao_ip = _ip
    page.sessao_porta = str(_api_porta)
    page.sessao_api_secure = _api_secure

    def _campo(label: str, **kw) -> ft.TextField:
        return ft.TextField(
            label=label, bgcolor=BG_INPUT, border_color=BORDER,
            focused_border_color=ACCENT, color=TEXT_PRIMARY,
            label_style=ft.TextStyle(color=TEXT_SECONDARY), **kw,
        )

    codigo_fixo = bool(_codigo_url)
    if codigo_fixo:
        exibir_codigo = ft.Column(
            spacing=4,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text(_codigo_url, size=32, weight=ft.FontWeight.BOLD, color=ACCENT),
                ft.Text("Codigo da sala", size=FONT_CAPTION, color=TEXT_SECONDARY),
            ],
        )
        campo_codigo = None
    else:
        exibir_codigo = None
        campo_codigo = _campo("Codigo da sala", max_length=6)

    campo_apelido = _campo("Seu apelido", max_length=20)

    def entrar(e) -> None:
        erro.value = ""
        codigo = (_codigo_url if codigo_fixo else (campo_codigo.value.strip() if campo_codigo else "")).upper()
        apelido = campo_apelido.value.strip()

        if not re.fullmatch(r"[A-HJ-NP-Z2-9]{6}", codigo):
            erro.value = "Codigo invalido"
        elif not apelido:
            erro.value = "Informe seu apelido"
        else:
            page.sessao_codigo = codigo
            page.sessao_apelido = apelido
            page.go("/lobby")
        page.update()

    campo_apelido.on_submit = entrar

    card = ft.Container(
        padding=ft.padding.all(CARD_PADDING),
        bgcolor=BG_CARD,
        border_radius=CARD_RADIUS,
        content=ft.Column(
            spacing=SPACE_MD,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[
                ft.Text("FaccuPoint", size=FONT_DISPLAY, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Text("Entre com o codigo da aula", size=FONT_CAPTION, color=TEXT_SECONDARY),
                ft.Divider(height=8, color="transparent"),
                *([exibir_codigo] if exibir_codigo else [campo_codigo]),
                campo_apelido,
                erro,
                ft.ElevatedButton(
                    text="Entrar", bgcolor=ACCENT, color=TEXT_PRIMARY,
                    height=BTN_H,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=BTN_RADIUS)),
                    on_click=entrar,
                ),
            ],
        ),
    )

    return ft.View(
        route="/",
        bgcolor=BG_PAGE,
        padding=ft.padding.all(SPACE_MD),
        controls=[
            ft.Column(
                expand=True,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                controls=[card],
            )
        ],
    )
