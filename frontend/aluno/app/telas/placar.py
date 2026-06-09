
import flet as ft

from app.design_system.tokens import (
    BG_CARD, BG_PAGE, CARD_PADDING, CARD_RADIUS, CARD_W,
    FONT_CAPTION, FONT_HEADING, SPACE_MD, TEXT_PRIMARY, TEXT_SECONDARY,
)


def tela_placar(page: ft.Page) -> ft.View:
    placar = getattr(page, "_placar_final", []) or []
    linhas = []
    for posicao, item in enumerate(placar, start=1):
        apelido = item.get("apelido", "Aluno")
        pontos = item.get("pontos", 0)
        linhas.append(
            ft.Container(
                bgcolor=BG_PAGE,
                border_radius=8,
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(f"{posicao}. {apelido}", color=TEXT_PRIMARY, size=FONT_CAPTION),
                        ft.Text(f"{pontos} ponto{'s' if pontos != 1 else ''}", color=TEXT_SECONDARY, size=FONT_CAPTION),
                    ],
                ),
            )
        )

    if not linhas:
        linhas.append(
            ft.Text(
                "sem respostas",
                size=FONT_CAPTION,
                color=TEXT_SECONDARY,
                text_align=ft.TextAlign.CENTER,
            )
        )

    return ft.View(
        route="/placar",
        bgcolor=BG_PAGE,
        padding=ft.padding.all(SPACE_MD),
        controls=[
            ft.Column(
                expand=True,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                controls=[
                    ft.Container(
                        padding=ft.padding.all(CARD_PADDING),
                        bgcolor=BG_CARD,
                        border_radius=CARD_RADIUS,
                        content=ft.Column(
                            spacing=SPACE_MD,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Text("Aula encerrada", size=FONT_CAPTION, color=TEXT_SECONDARY),
                                ft.Text("Placar final", size=FONT_HEADING, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                                *linhas,
                            ],
                        ),
                    ),
                ],
            )
        ],
    )
