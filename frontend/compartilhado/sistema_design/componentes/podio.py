import flet as ft

from compartilhado.pontuacao import formatar_pontos
from compartilhado.sistema_design.tokens import (
    BG_INPUT,
    CARD_RADIUS,
    FONT_BODY,
    FONT_CAPTION,
    FONT_HEADING,
    G8,
    SPACE_MD,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)

TAMANHO_PODIO = 5
ORDEM_VISUAL = [4, 2, 1, 3, 5]
PROPORCAO_ALTURA = {1: 1.0, 2: 0.85, 3: 0.72, 4: 0.6, 5: 0.5}
ALTURA_NOME_GRANDE = 300


def _texto_pontos(pontos: float) -> str:
    return f"{formatar_pontos(pontos)} pt{'s' if pontos != 1 else ''}"


def construir_podio(placar: list[dict], altura_max: int = 220) -> ft.Control:
    if not placar:
        return ft.Text(
            "Nenhuma resposta registrada.", color=TEXT_SECONDARY,
            size=FONT_BODY, text_align=ft.TextAlign.CENTER,
        )

    topo = placar[:TAMANHO_PODIO]
    resto = placar[TAMANHO_PODIO:]
    tamanho_nome = FONT_BODY if altura_max >= ALTURA_NOME_GRANDE else FONT_CAPTION

    def _bloco(posicao: int) -> ft.Control:
        item = topo[posicao - 1]
        return ft.Container(
            expand=True, height=altura_max * PROPORCAO_ALTURA[posicao],
            alignment=ft.alignment.center, padding=ft.padding.all(4),
            bgcolor=BG_INPUT, border_radius=CARD_RADIUS,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
                controls=[
                    ft.Text(f"{posicao}º", size=FONT_HEADING, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ft.Text(
                        item["apelido"], color=TEXT_PRIMARY, size=tamanho_nome,
                        weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER,
                        max_lines=2, overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    ft.Text(_texto_pontos(item["pontos"]), color=TEXT_SECONDARY, size=FONT_CAPTION),
                ],
            ),
        )

    linha_podio = ft.Row(
        alignment=ft.MainAxisAlignment.CENTER,
        vertical_alignment=ft.CrossAxisAlignment.END,
        spacing=G8,
        controls=[_bloco(p) for p in ORDEM_VISUAL if p <= len(topo)],
    )

    lista_resto = ft.Column(
        spacing=G8, scroll=ft.ScrollMode.AUTO, expand=True,
        controls=[
            ft.Container(
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
                bgcolor=BG_INPUT, border_radius=8,
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(f"{pos}. {item['apelido']}", color=TEXT_PRIMARY, size=FONT_CAPTION),
                        ft.Text(_texto_pontos(item["pontos"]), color=TEXT_SECONDARY, size=FONT_CAPTION),
                    ],
                ),
            )
            for pos, item in enumerate(resto, start=TAMANHO_PODIO + 1)
        ],
    ) if resto else ft.Container()

    return ft.Column(
        expand=True, spacing=SPACE_MD, horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        controls=[linha_podio, lista_resto],
    )
