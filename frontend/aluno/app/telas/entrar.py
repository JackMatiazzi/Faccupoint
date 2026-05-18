from __future__ import annotations

from urllib.parse import parse_qs, urlparse

import flet as ft

from app.design_system.tokens import (
    ACCENT, BG_CARD, BG_INPUT, BG_PAGE, BORDER, BTN_H, BTN_RADIUS,
    CARD_PADDING, CARD_RADIUS, CARD_W, FONT_CAPTION, FONT_DISPLAY,
    SPACE_MD, TEXT_DANGER, TEXT_PRIMARY, TEXT_SECONDARY,
)


def tela_entrar(page: ft.Page) -> ft.View:
    erro = ft.Text("", color=TEXT_DANGER, size=FONT_CAPTION)

    def _query_valor(nome: str) -> str:
        if hasattr(page, "query"):
            try:
                valor = page.query.get(nome)
                if valor:
                    return str(valor)
            except KeyError:
                pass

        for origem in (getattr(page, "route", ""), getattr(page, "url", "")):
            parsed = urlparse(origem or "")
            valores = parse_qs(parsed.query).get(nome)
            if valores:
                return valores[0]
        return ""

    parsed = urlparse(getattr(page, "url", "") or "")
    _ip = parsed.hostname or page.sessao_ip or "127.0.0.1"
    _api_porta = _query_valor("api") or page.sessao_porta or "8000"
    _codigo_url = _query_valor("codigo") or page.sessao_codigo

    page.sessao_ip = _ip
    page.sessao_porta = str(_api_porta)

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
                ft.Text("Código da sala", size=FONT_CAPTION, color=TEXT_SECONDARY),
            ],
        )
        campo_codigo = None
    else:
        exibir_codigo = None
        campo_codigo = _campo(
            "Código da sala",
            max_length=4,
            keyboard_type=ft.KeyboardType.NUMBER,
        )

    campo_apelido = _campo("Seu apelido", max_length=20)

    def entrar(e) -> None:
        erro.value = ""
        codigo  = _codigo_url if codigo_fixo else (campo_codigo.value.strip() if campo_codigo else "")
        apelido = campo_apelido.value.strip()

        if not codigo or len(codigo) != 4 or not codigo.isdigit():
            erro.value = "Código deve ter 4 dígitos"
        elif not apelido:
            erro.value = "Informe seu apelido"
        else:
            page.sessao_codigo  = codigo
            page.sessao_apelido = apelido
            page.go("/lobby")
        page.update()

    campo_apelido.on_submit = entrar

    card = ft.Container(
        width=CARD_W,
        padding=ft.padding.all(CARD_PADDING),
        bgcolor=BG_CARD,
        border_radius=CARD_RADIUS,
        content=ft.Column(
            spacing=SPACE_MD,
            controls=[
                ft.Text("FaccuPoint", size=FONT_DISPLAY, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Text("Entre com o código da aula", size=FONT_CAPTION, color=TEXT_SECONDARY),
                ft.Divider(height=8, color="transparent"),
                *([ exibir_codigo ] if exibir_codigo else [ campo_codigo ]),
                campo_apelido,
                erro,
                ft.ElevatedButton(
                    text="Entrar", bgcolor=ACCENT, color=TEXT_PRIMARY,
                    width=CARD_W, height=BTN_H,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=BTN_RADIUS)),
                    on_click=entrar,
                ),
            ],
        ),
    )

    return ft.View(
        route="/",
        bgcolor=BG_PAGE,
        padding=0,
        controls=[ft.Container(expand=True, alignment=ft.alignment.center, content=card)],
    )
