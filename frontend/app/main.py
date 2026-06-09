
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import flet as ft

from app.design_system.tokens import BG_PAGE
from app.telas.admin_professores import tela_admin_professores
from app.telas.login import tela_login
from app.telas.painel_professor import tela_painel_professor
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

    def view_pop(e: ft.ViewPopEvent) -> None:
        page.views.pop()
        if page.views:
            top = page.views[-1]
            page.go(top.route)
        else:
            page.go("/")

    _ativo = [True]

    def _keepalive():
        while _ativo[0]:
            time.sleep(30)
            if not _ativo[0]:
                break
            try:
                page.update()
            except Exception:
                break

    def _ao_fechar(e=None):
        _ativo[0] = False

    page.on_close = _ao_fechar
    threading.Thread(target=_keepalive, daemon=True).start()

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go("/")


def run_app() -> None:
    ft.app(target=main, view=ft.AppView.FLET_APP)


if __name__ == "__main__":
    run_app()
