from datetime import datetime

import flet as ft

from compartilhado.navegacao import ir_para
from compartilhado.sistema_design.componentes.podio import construir_podio
from compartilhado.sistema_design.tokens import (
    ACCENT, BG_CARD, BG_PAGE, BTN_H, BTN_RADIUS, CARD_PADDING_SM, CARD_RADIUS,
    FONT_CAPTION, FONT_HEADING, SPACE_MD, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_ON_ACCENT,
)


def tela_placar(page: ft.Page) -> ft.View:
    placar = getattr(page, "_placar_final", []) or []
    horario_encerramento = datetime.now().strftime("%H:%M")

    def entrar_em_outra_sala(e) -> None:
        page.sessao_codigo = ""
        page.sessao_apelido = ""
        page._ws_aluno = None
        page._placar_final = []
        page._mensagem_questao = {}
        page._forcar_entrada_manual = True
        try:
            page.client_storage.remove("faccupoint.sessao_aluno")
        except Exception:
            pass
        ir_para(page, "/")

    return ft.View(
        route="/placar",
        bgcolor=BG_PAGE,
        padding=ft.padding.all(SPACE_MD),
        controls=[
            ft.Column(
                expand=True,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                controls=[
                    ft.Container(
                        expand=True,
                        padding=ft.padding.all(CARD_PADDING_SM),
                        bgcolor=BG_CARD,
                        border_radius=CARD_RADIUS,
                        content=ft.Column(
                            expand=True,
                            spacing=SPACE_MD,
                            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                            controls=[
                                ft.Text(f"Aula encerrada às {horario_encerramento}", size=FONT_CAPTION, color=TEXT_SECONDARY, text_align=ft.TextAlign.CENTER),
                                ft.Text("Placar final", size=FONT_HEADING, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY, text_align=ft.TextAlign.CENTER),
                                construir_podio(placar),
                                ft.ElevatedButton(
                                    text="Entrar em outra sala",
                                    bgcolor=ACCENT, color=TEXT_ON_ACCENT, height=BTN_H,
                                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=BTN_RADIUS)),
                                    on_click=entrar_em_outra_sala,
                                ),
                            ],
                        ),
                    ),
                ],
            )
        ],
    )
