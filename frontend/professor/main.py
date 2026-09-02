
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import flet as ft

from compartilhado.ciclo_pagina import configurar_ciclo_pagina
from compartilhado.tema import configurar_tema
from compartilhado.sistema_design.tokens import BG_PAGE
from professor.servicos import cliente_api as api
from professor.telas.admin_professores import tela_admin_professores
from professor.telas.esqueci_senha import tela_esqueci_senha
from professor.telas.login import tela_login
from professor.telas.painel_professor import tela_painel_professor
from professor.telas.sessao_professor import tela_sessao_professor
from professor.telas.trocar_pin import tela_trocar_pin


def main(page: ft.Page) -> None:
    page.title = "FaccuPoint"
    configurar_tema(page)
    page.bgcolor = BG_PAGE
    page.padding = 0

    page.docente_id = None
    page.docente_nome = ""
    page.docente_email = ""
    page.docente_papel = ""
    page.precisa_trocar_pin = False
    page.pin_temporario = None

    def _sessao_perdida() -> None:
        page.docente_id = None
        page.docente_nome = page.docente_email = page.docente_papel = ""
        page.precisa_trocar_pin = False
        page.pin_temporario = None
        page.go("/")

    api.set_on_auth_lost(_sessao_perdida)

    def route_change(e: ft.RouteChangeEvent) -> None:
        page.views.clear()
        rota = page.route

        if rota == "/esqueci-senha":
            page.views.append(tela_esqueci_senha(page))
        elif rota != "/" and not page.docente_id:
            page.views.append(tela_login(page))
        elif page.docente_id and getattr(page, "precisa_trocar_pin", False):
            page.views.append(tela_trocar_pin(page))
        elif rota == "/trocar-pin":
            page.views.append(tela_trocar_pin(page))
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
