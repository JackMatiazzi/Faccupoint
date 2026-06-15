
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import flet as ft

from compartilhado.ciclo_pagina import configurar_ciclo_pagina
from compartilhado.sistema_design.tokens import BG_PAGE
from professor.telas.admin_professores import tela_admin_professores
from professor.telas.login import tela_login
from professor.telas.painel_professor import tela_painel_professor
from professor.telas.sessao_professor import tela_sessao_professor


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

        if rota != "/" and not page.docente_id:
            page.views.append(tela_login(page))
        elif rota == "/admin-professores":
            if page.docente_papel == "adm":
                page.views.append(tela_admin_professores(page))
            else:
                page.views.append(tela_painel_professor(page))
        elif rota == "/painel-professor":
            page.views.append(tela_painel_professor(page))
        elif rota == "/criacao-quiz":
            page.views.append(tela_painel_professor(page))
        elif rota == "/sessao-professor":
            page.views.append(tela_sessao_professor(page))
        else:
            page.views.append(tela_login(page))

        page.update()

    configurar_ciclo_pagina(page)
    page.on_route_change = route_change
    page.go("/")


def run_app() -> None:
    ft.app(target=main, view=ft.AppView.FLET_APP)


if __name__ == "__main__":
    run_app()
