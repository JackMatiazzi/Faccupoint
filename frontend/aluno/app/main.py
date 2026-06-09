
import asyncio
import sys
import threading
import time
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).parent.parent))

import flet as ft

from app.design_system.tokens import BG_PAGE
from app.telas.entrar import tela_entrar
from app.telas.lobby import tela_lobby
from app.telas.questao import tela_questao
from app.telas.placar import tela_placar


def _query_valor(page: ft.Page, nome: str) -> str:
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


def main(page: ft.Page) -> None:
    page.title = "FaccuPoint"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = BG_PAGE
    page.padding = 0

    rota_inicial = page.route or "/"

    page.sessao_codigo = _query_valor(page, "codigo")
    page.sessao_apelido = ""
    page.sessao_ip = "127.0.0.1"
    page.sessao_porta = _query_valor(page, "api") or "8000"
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
    page.go(rota_inicial)


def run_app(port: int = 8081) -> None:
    ft.app(target=main, view=None, port=port, host="0.0.0.0")


if __name__ == "__main__":
    run_app()
