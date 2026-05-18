from __future__ import annotations

import asyncio
import json

import flet as ft
import websockets

from app.design_system.tokens import (
    ACCENT, BG_CARD, BG_INPUT, BG_PAGE, BORDER, BTN_H, BTN_RADIUS,
    CARD_PADDING, CARD_RADIUS, CARD_W, FONT_CAPTION, FONT_CODE, SPACE_MD,
    TEXT_DANGER, TEXT_PRIMARY, TEXT_SECONDARY,
)


def tela_lobby(page: ft.Page) -> ft.View:
    status = ft.Text("Entrando na sala...", color=TEXT_SECONDARY, size=FONT_CAPTION)
    lista_participantes = ft.Column(spacing=8)
    btn_tentar_novamente = ft.ElevatedButton(
        text="Tentar outro apelido",
        bgcolor=ACCENT, color=TEXT_PRIMARY,
        width=CARD_W, height=BTN_H,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=BTN_RADIUS)),
        visible=False,
        on_click=lambda _: page.go("/"),
    )

    async def conectar() -> None:
        uri = f"ws://{page.sessao_ip}:{page.sessao_porta}/ws/aluno/{page.sessao_codigo}"
        try:
            ws = await websockets.connect(uri)
            page._ws_aluno = ws
            await ws.send(json.dumps({"apelido": page.sessao_apelido}))

            async for texto in ws:
                dados = json.loads(texto)
                tipo  = dados.get("tipo")

                if tipo == "erro":
                    status.value = dados.get("mensagem", "Nao consegui entrar na sala")
                    status.color = TEXT_DANGER
                    btn_tentar_novamente.visible = True
                    page.update()
                    await ws.close()
                    return

                if tipo == "lobby":
                    participantes = dados.get("participantes", [])
                    n = len(participantes)
                    status.value = f"Aguardando o professor iniciar a aula ({n} na sala)"
                    lista_participantes.controls = [
                        ft.Container(
                            bgcolor=BG_INPUT,
                            border_radius=8,
                            padding=ft.padding.symmetric(horizontal=SPACE_MD, vertical=10),
                            content=ft.Text(nome, color=TEXT_PRIMARY, size=15),
                        )
                        for nome in participantes
                    ]
                    page.update()

                elif tipo == "questao":
                    status.value = "A aula vai comecar!"
                    lista_participantes.controls = []
                    page.update()
                    await asyncio.sleep(1.5)
                    page._mensagem_questao = dados
                    page.go("/questao")
                    return

        except Exception:
            status.value = "Codigo invalido ou sala ja encerrada"
            page.update()

    page.run_task(conectar)

    return ft.View(
        route="/lobby",
        bgcolor=BG_PAGE,
        padding=0,
        controls=[
            ft.Container(
                expand=True,
                alignment=ft.alignment.center,
                content=ft.Container(
                    width=CARD_W,
                    padding=ft.padding.all(CARD_PADDING),
                    bgcolor=BG_CARD,
                    border_radius=CARD_RADIUS,
                    content=ft.Column(
                        spacing=SPACE_MD,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Text(page.sessao_codigo, size=FONT_CODE, weight=ft.FontWeight.BOLD, color=ACCENT),
                            ft.Text("Codigo da sala", size=FONT_CAPTION, color=TEXT_SECONDARY),
                            ft.Divider(color=BORDER),
                            status,
                            btn_tentar_novamente,
                            lista_participantes,
                        ],
                    ),
                ),
            )
        ],
    )
