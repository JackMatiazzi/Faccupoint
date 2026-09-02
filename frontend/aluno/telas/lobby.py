
import asyncio
import json

import flet as ft
import websockets

from compartilhado.navegacao import ir_para
from compartilhado.sistema_design.tokens import (
    ACCENT, BG_CARD, BG_INPUT, BG_PAGE, BORDER, BTN_H, BTN_RADIUS,
    CARD_PADDING, CARD_RADIUS, CARD_W, FONT_CAPTION, FONT_CODE, SPACE_MD,
    TEXT_DANGER, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_ON_ACCENT,
)


def tela_lobby(page: ft.Page) -> ft.View:
    chave_sessao = "faccupoint.sessao_aluno"
    status = ft.Text("Entrando na sala...", color=TEXT_SECONDARY, size=FONT_CAPTION)
    lista_participantes = ft.Column(spacing=8)
    def voltar_ao_inicio(e) -> None:
        page.sessao_codigo = ""
        page.sessao_apelido = ""
        page.sessao_token_reconexao = ""
        page._forcar_entrada_manual = True
        try:
            page.client_storage.remove(chave_sessao)
        except Exception:
            pass
        ir_para(page, "/")

    btn_tentar_novamente = ft.ElevatedButton(
        text="Tentar outro apelido",
        bgcolor=ACCENT, color=TEXT_ON_ACCENT,
        width=CARD_W, height=BTN_H,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=BTN_RADIUS)),
        visible=False,
        on_click=voltar_ao_inicio,
    )

    async def conectar() -> None:
        try:
            salva = await page.client_storage.get_async(chave_sessao) or {}
        except Exception:
            salva = {}
        if not page.sessao_codigo and salva:
            page.sessao_codigo = str(salva.get("codigo", ""))
            page.sessao_apelido = str(salva.get("apelido", ""))
            page.sessao_ip = str(salva.get("api_host", page.sessao_ip))
            page.sessao_porta = str(salva.get("api_port", page.sessao_porta))
            page.sessao_api_secure = bool(salva.get("api_secure", False))
        token_reconexao = ""
        if salva.get("codigo") == page.sessao_codigo and salva.get("apelido") == page.sessao_apelido:
            token_reconexao = str(salva.get("token_reconexao", ""))
        if not page.sessao_codigo or not page.sessao_apelido:
            status.value = "Sessao nao encontrada. Volte ao inicio para entrar novamente."
            status.color = TEXT_DANGER
            btn_tentar_novamente.visible = True
            page.update()
            return

        scheme = "wss" if getattr(page, "sessao_api_secure", False) else "ws"
        uri = f"{scheme}://{page.sessao_ip}:{page.sessao_porta}/ws/aluno/{page.sessao_codigo}"
        navegou = [False]
        page._ws_queue = asyncio.Queue()
        try:
            ws = await websockets.connect(uri, ping_interval=None)
            page._ws_aluno = ws
            await ws.send(json.dumps({
                "apelido": page.sessao_apelido,
                "token_reconexao": token_reconexao,
            }))

            while True:
                texto = await ws.recv()
                dados = json.loads(texto)
                tipo  = dados.get("tipo")
                page._tentativas_reconexao = 0

                if tipo == "identificado":
                    page.sessao_token_reconexao = str(dados.get("token_reconexao", ""))
                    try:
                        await page.client_storage.set_async(chave_sessao, {
                            "codigo": page.sessao_codigo,
                            "apelido": page.sessao_apelido,
                            "api_host": page.sessao_ip,
                            "api_port": page.sessao_porta,
                            "api_secure": page.sessao_api_secure,
                            "token_reconexao": page.sessao_token_reconexao,
                        })
                    except Exception:
                        pass

                elif tipo == "erro":
                    status.value = dados.get("mensagem", "Nao consegui entrar na sala")
                    status.color = TEXT_DANGER
                    btn_tentar_novamente.visible = True
                    page.update()
                    await ws.close()
                    return

                elif tipo == "lobby":
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

                elif tipo == "questao" and not navegou[0]:
                    navegou[0] = True
                    status.value = "A aula vai comecar!"
                    lista_participantes.controls = []
                    page.update()
                    await asyncio.sleep(1.5)
                    page._mensagem_questao = dados
                    ir_para(page, "/questao")

                elif tipo == "fim":
                    navegou[0] = True
                    page._placar_final = dados.get("placar", [])
                    ir_para(page, "/placar")
                    return

                else:
                    queue = getattr(page, "_ws_queue", None)
                    if queue:
                        await queue.put(dados)

        except Exception as e:
            em_quiz = navegou[0] or getattr(page, "_rota_esperada", "") == "/questao"
            if not em_quiz:
                status.value = "Codigo invalido ou sala ja encerrada"
                page.update()
            else:
                tentativas = getattr(page, "_tentativas_reconexao", 0) + 1
                page._tentativas_reconexao = tentativas
                if tentativas <= 5 and getattr(page, "_rota_esperada", "") == "/questao":
                    await asyncio.sleep(2)
                    page.run_task(conectar)
                else:
                    queue = getattr(page, "_ws_queue", None)
                    if queue:
                        detalhe = f"{type(e).__name__}: {str(e)[:80]}"
                        queue.put_nowait({"tipo": "_erro_conexao", "detalhe": detalhe})

    page.run_task(conectar)

    return ft.View(
        route="/lobby",
        bgcolor=BG_PAGE,
        padding=ft.padding.all(SPACE_MD),
        controls=[
            ft.Column(
                expand=True,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                controls=[
                    ft.Container(
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
                ],
            )
        ],
    )
