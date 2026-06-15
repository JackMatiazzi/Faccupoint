
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import flet as ft

from compartilhado.ciclo_pagina import configurar_ciclo_pagina
from compartilhado.navegacao import query_valor
from compartilhado.sistema_design.tokens import BG_PAGE
from aluno.telas.entrar import tela_entrar
from aluno.telas.lobby import tela_lobby
from aluno.telas.questao import tela_questao
from aluno.telas.placar import tela_placar


def main(page: ft.Page) -> None:
    page.title = "FaccuPoint"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = BG_PAGE
    page.padding = 0

    rota_inicial = page.route or "/"

    page.sessao_codigo = query_valor(page, "codigo")
    page.sessao_apelido = ""
    page.sessao_ip = "127.0.0.1"
    page.sessao_porta = "8000"
    page.sessao_api_secure = False
    page._ws_queue = asyncio.Queue()

    def route_change(e: ft.RouteChangeEvent) -> None:
        page.views.clear()
        rota = page.route

        if rota == "/lobby":
            page.views.append(tela_lobby(page))
        elif rota == "/questao":
            page.views.append(tela_questao(page))
        elif rota == "/placar":
            page.views.append(tela_placar(page))
        else:
            page.views.append(tela_entrar(page))

        page.update()

    configurar_ciclo_pagina(page)
    page.on_route_change = route_change
    page.go(rota_inicial)


def run_app(port: int = 8081) -> None:
    ft.app(target=main, view=None, port=port, host="0.0.0.0")


if __name__ == "__main__":
    run_app()
