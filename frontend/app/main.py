from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import flet as ft

from app.design_system.tokens import BG_PAGE
from app.telas.login import tela_login
from app.telas.cadastro_docente import tela_cadastro_docente
from app.telas.criacao_quiz import tela_criacao_quiz
from app.telas.sessao_professor import tela_sessao_professor



def main(page: ft.Page) -> None:
    page.title = "FaccuPoint"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = BG_PAGE
    page.padding = 0

    page.docente_id = None
    page.docente_nome = ""
    page.docente_email = ""
    page.docente_papel = ""

    def route_change(e: ft.RouteChangeEvent) -> None:
        page.views.clear()
        rota = page.route

        if rota == "/cadastro-docente":
            page.views.append(tela_cadastro_docente(page))
        elif rota == "/criacao-quiz":
            page.views.append(tela_criacao_quiz(page))
        elif rota == "/sessao-professor":
            page.views.append(tela_sessao_professor(page))
        else:
            page.views.append(tela_login(page))

        page.update()

    def view_pop(e: ft.ViewPopEvent) -> None:
        page.views.pop()
        if page.views:
            top = page.views[-1]
            page.go(top.route)
        else:
            page.go("/")

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go("/")


def run_app() -> None:
    ft.app(target=main, view=ft.AppView.FLET_APP)


if __name__ == "__main__":
    run_app()
