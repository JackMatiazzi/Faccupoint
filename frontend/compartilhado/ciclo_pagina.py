import threading
import time

import flet as ft


def configurar_ciclo_pagina(page: ft.Page) -> None:
    ativo = [True]

    def voltar_view(e: ft.ViewPopEvent) -> None:
        page.views.pop()
        if page.views:
            page.go(page.views[-1].route)
        else:
            page.go("/")

    def manter_conexao() -> None:
        while ativo[0]:
            time.sleep(30)
            if not ativo[0]:
                break
            try:
                page.update()
            except Exception:
                break

    def ao_fechar(e=None) -> None:
        ativo[0] = False

    page.on_close = ao_fechar
    page.on_view_pop = voltar_view
    threading.Thread(target=manter_conexao, daemon=True).start()
