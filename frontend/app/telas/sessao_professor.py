from __future__ import annotations

import base64
import io
import json
import socket

import flet as ft
import qrcode
import websockets

from app.design_system.tokens import (
    ACCENT, BG_CARD, BG_INPUT, BG_PAGE, BORDER, BTN_H, BTN_RADIUS,
    CARD_PADDING_SM, CARD_RADIUS, CARD_W, FONT_BODY, FONT_CAPTION,
    FONT_CODE, SPACE_MD, TEXT_DANGER, TEXT_PRIMARY, TEXT_SECONDARY,
    TEXT_SUCCESS,
)
from app.infra.api_client import ApiError, auth_headers, listar_quizzes_do_docente
import requests
import os
from dotenv import load_dotenv

load_dotenv()
_BASE = os.getenv("API_URL", "http://127.0.0.1:8000")
_PORTA_ALUNO = int(os.getenv("PORTA_ALUNO", "8081"))
_API_PORT = int(os.getenv("API_PORT", "8000"))


def _ip_local() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def _gerar_qrcode_b64(url: str) -> str:
    img = qrcode.make(url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def tela_sessao_professor(page: ft.Page) -> ft.View:
    codigo_text = ft.Text("----", size=FONT_CODE, weight=ft.FontWeight.BOLD, color=ACCENT)
    qr_image = ft.Image(width=180, height=180, visible=False)
    url_text = ft.Text("", size=FONT_CAPTION, color=TEXT_SECONDARY)
    status_text = ft.Text("Escolha um quiz para abrir a sala", color=TEXT_SECONDARY, size=FONT_CAPTION)
    participantes_col = ft.Row(spacing=8, wrap=True)
    respondidos_text = ft.Text("", color=TEXT_SECONDARY, size=FONT_CAPTION)
    etapa_text = ft.Text("Etapa 1 de 3: Selecionar quiz", size=FONT_CAPTION, color=TEXT_SECONDARY)
    questao_text = ft.Text("", color=TEXT_PRIMARY, size=FONT_BODY, weight=ft.FontWeight.BOLD, visible=False)
    tempo_text = ft.Text("", color=TEXT_SECONDARY, size=FONT_CAPTION, visible=False)

    _codigo: list[str | None] = [None]
    _timer_ativo: list[bool] = [False]

    selector = ft.Dropdown(
        label="Selecionar quiz",
        bgcolor=BG_INPUT, border_color=BORDER,
        focused_border_color=ACCENT, color=TEXT_PRIMARY,
        label_style=ft.TextStyle(color=TEXT_SECONDARY),
        options=[],
    )
    _mapa_quizzes: dict[str, int] = {}

    btn_criar = ft.ElevatedButton(
        text="Gerar código",
        bgcolor=ACCENT, color=TEXT_PRIMARY, width=CARD_W, height=BTN_H,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=BTN_RADIUS)),
    )
    btn_iniciar = ft.ElevatedButton(
        text="Começar quiz",
        bgcolor=TEXT_SUCCESS, color=BG_PAGE, width=CARD_W, height=BTN_H,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=BTN_RADIUS)),
        visible=False,
    )
    btn_proxima = ft.ElevatedButton(
        text="Próxima",
        bgcolor=BORDER, color=TEXT_PRIMARY, width=CARD_W, height=BTN_H,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=BTN_RADIUS)),
        visible=False,
    )
    erro = ft.Text("", color=TEXT_DANGER, size=FONT_CAPTION)

    def carregar_quizzes() -> None:
        try:
            quizzes = listar_quizzes_do_docente(page.docente_id)
        except ApiError:
            erro.value = "erro ao buscar quizzes"
            page.update()
            return
        selector.options = [
            ft.dropdown.Option(key=str(q.id_quiz), text=q.titulo)
            for q in quizzes
        ]
        quiz_preselecionado = getattr(page, "quiz_sala_id", None)
        for q in quizzes:
            _mapa_quizzes[str(q.id_quiz)] = q.id_quiz
            if q.id_quiz == quiz_preselecionado:
                selector.value = str(q.id_quiz)
        if selector.value is None and quizzes:
            selector.value = str(quizzes[0].id_quiz)
        page.update()

    def criar_sessao(e=None) -> None:
        erro.value = ""
        quiz_key = selector.value
        if not quiz_key or quiz_key not in _mapa_quizzes:
            erro.value = "Escolha um quiz primeiro"
            page.update()
            return
        id_quiz = _mapa_quizzes[quiz_key]
        try:
            r = requests.post(
                f"{_BASE}/sessoes",
                json={"id_quiz": id_quiz, "id_docente_anfitriao": page.docente_id},
                headers=auth_headers(),
                timeout=5,
            )
            if not r.ok:
                erro.value = r.json().get("detail", "Não consegui abrir a sala")
                page.update()
                return
            codigo = r.json()["codigo"]
        except Exception:
            erro.value = "backend fora do ar"
            page.update()
            return

        _codigo[0] = codigo
        ip = _ip_local()
        url = f"http://{ip}:{_PORTA_ALUNO}?codigo={codigo}&api={_API_PORT}"
        qr_b64 = _gerar_qrcode_b64(url)

        codigo_text.value = codigo
        qr_image.src_base64 = qr_b64
        qr_image.visible = True
        url_text.value = f"http://{ip}:{_PORTA_ALUNO}"
        btn_criar.visible = False
        btn_iniciar.visible = True
        selector.disabled = True
        status_text.value = "Esperando os alunos entrarem..."
        etapa_text.value = "Etapa 2 de 3: Aguardando alunos"
        page.update()

        page.run_task(_conectar_ws_professor, codigo)

    async def _timer_questao() -> None:
        import asyncio as _asyncio
        t = 0
        while _timer_ativo[0]:
            tempo_text.value = f"{t}s decorridos"
            page.update()
            await _asyncio.sleep(1)
            t += 1

    async def _conectar_ws_professor(codigo: str) -> None:
        uri = f"ws://{_BASE.replace('http://', '').replace('https://', '')}/ws/professor/{codigo}"
        try:
            async with websockets.connect(uri) as ws:
                async for texto in ws:
                    dados = json.loads(texto)
                    tipo = dados.get("tipo")

                    if tipo == "lobby":
                        participantes = dados.get("participantes", [])
                        n = len(participantes)
                        status_text.value = f"{n} aluno{'s' if n != 1 else ''} na sala"
                        participantes_col.controls = [
                            ft.Container(
                                padding=ft.padding.symmetric(horizontal=12, vertical=6),
                                bgcolor=BG_INPUT,
                                border_radius=20,
                                content=ft.Text(nome, color=TEXT_PRIMARY, size=FONT_CAPTION),
                            )
                            for nome in participantes
                        ]
                        page.update()

                    elif tipo == "questao_professor":
                        numero = dados.get("numero", 1)
                        total = dados.get("total", 1)
                        questao_text.value = f"Questao {numero} de {total}"
                        questao_text.visible = True
                        tempo_text.value = "0s decorridos"
                        tempo_text.visible = True
                        _timer_ativo[0] = True
                        page.run_task(_timer_questao)
                        page.update()

                    elif tipo == "responderam":
                        total = dados.get("total", 0)
                        respondidos = dados.get("respondidos", 0)
                        respondidos_text.value = f"{respondidos} de {total} responderam"
                        page.update()

                    elif tipo == "resultado_professor":
                        _timer_ativo[0] = False
                        btn_proxima.visible = False
                        respondidos_text.value = ""
                        status_text.value = "todos responderam"
                        page.update()

                    elif tipo == "fim":
                        _timer_ativo[0] = False
                        btn_proxima.visible = False
                        btn_iniciar.visible = False
                        status_text.value = "Aula encerrada"
                        respondidos_text.value = ""
                        etapa_text.value = "Aula concluida"
                        questao_text.visible = False
                        tempo_text.visible = False
                        placar = dados.get("placar", [])
                        participantes_col.controls = [
                            ft.Container(
                                padding=ft.padding.symmetric(horizontal=12, vertical=8),
                                bgcolor=BG_INPUT,
                                border_radius=8,
                                content=ft.Row(
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    controls=[
                                        ft.Text(
                                            f"{pos}. {item['apelido']}",
                                            color=TEXT_PRIMARY,
                                            size=FONT_CAPTION,
                                        ),
                                        ft.Text(
                                            f"{item['pontos']} pt{'s' if item['pontos'] != 1 else ''}",
                                            color=TEXT_SECONDARY,
                                            size=FONT_CAPTION,
                                        ),
                                    ],
                                ),
                            )
                            for pos, item in enumerate(placar, start=1)
                        ]
                        page.update()

        except Exception:
            status_text.value = "Conexão caiu"
            page.update()

    def iniciar_quiz(e) -> None:
        if not _codigo[0]:
            return
        try:
            r = requests.post(f"{_BASE}/sessoes/{_codigo[0]}/iniciar", headers=auth_headers(), timeout=5)
            if not r.ok:
                erro.value = r.json().get("detail", "Erro")
                page.update()
                return
        except Exception:
            erro.value = "erro ao iniciar"
            page.update()
            return
        btn_iniciar.visible = False
        btn_proxima.visible = False
        status_text.value = "Quiz começou!"
        etapa_text.value = "Etapa 3 de 3: Em andamento"
        qr_image.visible = False
        page.update()

    def proxima_questao(e) -> None:
        if not _codigo[0]:
            return
        try:
            r = requests.post(f"{_BASE}/sessoes/{_codigo[0]}/proxima", headers=auth_headers(), timeout=5)
            if not r.ok:
                erro.value = r.json().get("detail", "Erro")
                page.update()
                return
            if r.json().get("fim"):
                btn_proxima.visible = False
                status_text.value = "Fim!"
                page.update()
        except Exception:
            erro.value = "erro ao avancar"
            page.update()

    btn_criar.on_click = criar_sessao
    btn_iniciar.on_click = iniciar_quiz
    btn_proxima.on_click = proxima_questao

    carregar_quizzes()
    if getattr(page, "abrir_sala_automaticamente", False):
        page.abrir_sala_automaticamente = False
        selector.visible = False
        criar_sessao()

    card_controles = ft.Container(
        width=CARD_W,
        padding=ft.padding.all(CARD_PADDING_SM),
        bgcolor=BG_CARD,
        border_radius=CARD_RADIUS,
        content=ft.Column(
            spacing=SPACE_MD,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                etapa_text,
                ft.Divider(color=BORDER),
                selector,
                btn_criar,
                codigo_text,
                qr_image,
                url_text,
                btn_iniciar,
                btn_proxima,
                erro,
            ],
        ),
    )

    card_alunos = ft.Container(
        expand=True,
        padding=ft.padding.all(CARD_PADDING_SM),
        bgcolor=BG_CARD,
        border_radius=CARD_RADIUS,
        content=ft.Column(
            spacing=SPACE_MD,
            controls=[
                ft.Text("Alunos na sala", size=FONT_BODY, color=TEXT_SECONDARY),
                ft.Divider(color=BORDER),
                questao_text,
                tempo_text,
                status_text,
                respondidos_text,
                ft.Container(expand=True, content=participantes_col),
            ],
        ),
    )

    return ft.View(
        route="/sessao-professor",
        bgcolor=BG_PAGE,
        appbar=ft.AppBar(
            title=ft.Text("Sala ao Vivo", color=TEXT_PRIMARY),
            bgcolor=BG_CARD,
            actions=[
                ft.TextButton(
                    "Voltar",
                    style=ft.ButtonStyle(color=TEXT_PRIMARY),
                    on_click=lambda _: page.go("/criacao-quiz"),
                )
            ],
        ),
        controls=[
            ft.Container(
                expand=True,
                padding=ft.padding.all(CARD_PADDING_SM),
                content=ft.Row(
                    expand=True,
                    spacing=SPACE_MD,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    controls=[card_controles, card_alunos],
                ),
            )
        ],
    )
