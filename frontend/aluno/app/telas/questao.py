
import asyncio
import json

import flet as ft

from app.design_system.media import eh_imagem, id_video_youtube
from app.design_system.tokens import (
    ACCENT, BG_CARD, BG_INPUT, BG_PAGE, BTN_QUESTAO_H, BTN_RADIUS,
    CARD_PADDING_SM, CARD_RADIUS, CARD_W, CORES_ALTERNATIVAS,
    FONT_CAPTION, FONT_SUBHEADING, SPACE_MD, TEXT_DANGER,
    TEXT_PRIMARY, TEXT_SECONDARY,
)


def tela_questao(page: ft.Page) -> ft.View:
    page._questao_token = getattr(page, "_questao_token", 0) + 1
    questao_token = page._questao_token

    dados = getattr(page, "_mensagem_questao", {})
    enunciado = dados.get("enunciado", "")
    alternativas = dados.get("alternativas", [])
    numero = dados.get("numero", 1)
    total = dados.get("total", 1)
    tempo_total = dados.get("tempo", 20)
    link_midia = dados.get("link_midia")

    def _render_media(url: str | None) -> ft.Control | None:
        if not url:
            return None
        video_id = id_video_youtube(url)
        if video_id:
            embed = (
                f"https://www.youtube.com/embed/{video_id}"
                f"?autoplay=1&mute=1&rel=0&playsinline=1"
            )
            return ft.WebView(url=embed, height=200, enable_javascript=True)
        if eh_imagem(url):
            return ft.Image(src=url, height=200, fit=ft.ImageFit.CONTAIN, border_radius=CARD_RADIUS)
        return ft.ElevatedButton(
            "Abrir mídia",
            icon=ft.Icons.OPEN_IN_NEW,
            on_click=lambda _, u=url: page.launch_url(u, web_window_name="_blank"),
        )

    resposta_enviada = [None]
    progresso = ft.ProgressBar(value=1.0, bgcolor=BG_INPUT, color=ACCENT)
    texto_tempo = ft.Text(str(tempo_total), size=FONT_SUBHEADING, color=TEXT_PRIMARY, weight=ft.FontWeight.BOLD)
    feedback    = ft.Text("", size=FONT_SUBHEADING, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER)
    botoes = []

    def fazer_botao(indice: int, texto: str) -> ft.ElevatedButton:
        return ft.ElevatedButton(
            text=texto,
            bgcolor=CORES_ALTERNATIVAS[indice % len(CORES_ALTERNATIVAS)],
            color=TEXT_PRIMARY,
            height=BTN_QUESTAO_H,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=BTN_RADIUS)),
            on_click=lambda e, i=indice: responder(i),
        )

    def responder(indice: int) -> None:
        if resposta_enviada[0] is not None:
            return
        resposta_enviada[0] = indice
        for b in botoes:
            b.disabled = True
        feedback.value = "aguardando..."
        feedback.color = TEXT_PRIMARY
        page.update()
        page.run_task(enviar_resposta, indice)

    async def enviar_resposta(indice: int) -> None:
        ws = getattr(page, "_ws_aluno", None)
        if ws:
            try:
                await ws.send(json.dumps({"tipo": "resposta", "indice": indice}))
            except Exception:
                feedback.value = "Falha ao enviar"
                feedback.color = TEXT_DANGER
                page.update()

    async def aguardar_resultado() -> None:
        queue = getattr(page, "_ws_queue", None)
        if not queue:
            feedback.value = "Conexão perdida"
            feedback.color = TEXT_DANGER
            page.update()
            return
        try:
            while True:
                dados_ws = await queue.get()
                tipo = dados_ws.get("tipo")

                if tipo == "_erro_conexao":
                    feedback.value = "Conexão perdida"
                    feedback.color = TEXT_DANGER
                    page.update()
                    return

                elif tipo == "resultado":
                    corretas = dados_ws.get("indices_corretos", [])
                    acertou = dados_ws.get("acertou")
                    if resposta_enviada[0] is None:
                        feedback.value = "Tempo esgotado"
                        feedback.color = TEXT_SECONDARY
                    elif acertou is True or resposta_enviada[0] in corretas:
                        feedback.value = "Correta"
                        feedback.color = ACCENT
                    else:
                        feedback.value = "Incorreta"
                        feedback.color = TEXT_DANGER
                    for b in botoes:
                        b.disabled = True
                    page.update()

                elif tipo == "questao":
                    page._mensagem_questao = dados_ws
                    page.views.clear()
                    page.views.append(tela_questao(page))
                    page.update()
                    return

                elif tipo == "fim":
                    page._placar_final = dados_ws.get("placar", [])
                    page.go("/placar")
                    return

        except Exception:
            feedback.value = "Conexão perdida"
            feedback.color = TEXT_DANGER
            page.update()

    async def countdown() -> None:
        for t in range(tempo_total, -1, -1):
            if getattr(page, "_questao_token", None) != questao_token:
                return

            progresso.value = t / tempo_total
            texto_tempo.value = str(t) if t > 0 else "0"
            page.update()
            if t == 0:
                if resposta_enviada[0] is None:
                    for b in botoes:
                        b.disabled = True
                    feedback.value = "Tempo esgotado"
                    feedback.color = TEXT_SECONDARY
                    page.update()
                break
            await asyncio.sleep(1)

    for i, alt in enumerate(alternativas):
        botoes.append(fazer_botao(i, alt))

    media_ctrl = _render_media(link_midia)

    if resposta_enviada[0] is None:
        page.run_task(countdown)
        page.run_task(aguardar_resultado)

    return ft.View(
        route="/questao",
        bgcolor=BG_PAGE,
        padding=SPACE_MD,
        controls=[
            ft.Column(
                expand=True,
                scroll=ft.ScrollMode.AUTO,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(f"Questão {numero}/{total}", size=FONT_CAPTION, color=TEXT_SECONDARY),
                            ft.Row(controls=[texto_tempo, ft.Text("s", color=TEXT_SECONDARY, size=FONT_CAPTION)], spacing=2),
                        ],
                    ),
                    progresso,
                    ft.Container(height=SPACE_MD),
                    ft.Container(
                        padding=ft.padding.all(CARD_PADDING_SM),
                        bgcolor=BG_CARD,
                        border_radius=CARD_RADIUS,
                        content=ft.Text(enunciado, size=FONT_SUBHEADING, color=TEXT_PRIMARY, text_align=ft.TextAlign.CENTER),
                    ),
                    *([ft.Container(height=SPACE_MD), media_ctrl] if media_ctrl else [ft.Container(height=SPACE_MD)]),
                    *botoes,
                    ft.Container(height=8),
                    feedback,
                ],
            )
        ],
    )
