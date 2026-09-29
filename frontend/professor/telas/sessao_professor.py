
import base64
import asyncio
import io
import ipaddress
import json
import socket
from urllib.parse import urlsplit

import flet as ft
import psutil
import qrcode
import websockets

from compartilhado.sistema_design.midia import eh_imagem, id_video_youtube
from compartilhado.pontuacao import formatar_pontos
from compartilhado.sistema_design.tokens import (
    ACCENT, BG_CARD, BG_INPUT, BG_PAGE, BORDER, BTN_GREEN_TEXT, BTN_H, BTN_RADIUS,
    CARD_PADDING_SM, CARD_RADIUS, CARD_W, FONT_BODY, FONT_CAPTION,
    SPACE_MD, TEXT_DANGER, TEXT_PRIMARY, TEXT_SECONDARY,
    TEXT_SUCCESS,
)
from professor.servicos import cliente_api as api
from professor.servicos.cliente_api import ApiError
import os

_BASE = api.api_url()
_PORTA_ALUNO = int(os.getenv("PORTA_ALUNO", "8081"))

# Extrai host/porta/scheme do API_URL para o QR code do aluno
_parsed_base = __import__("urllib.parse", fromlist=["urlparse"]).urlparse(_BASE)
_API_HOST = _parsed_base.hostname or "127.0.0.1"
_API_SECURE = "1" if _BASE.startswith("https") else "0"
_API_PORT = _parsed_base.port or (443 if _BASE.startswith("https") else 8000)


def _ip_local() -> str:
    candidatos = []
    nomes_ignorados = ("virtual", "vpn", "radmin", "virtualbox", "vmware", "bluetooth", "loopback")

    for nome, enderecos in psutil.net_if_addrs().items():
        estatisticas = psutil.net_if_stats().get(nome)
        nome_normalizado = nome.lower()

        if not estatisticas or not estatisticas.isup:
            continue
        if any(termo in nome_normalizado for termo in nomes_ignorados):
            continue

        for endereco in enderecos:
            if endereco.family != socket.AF_INET:
                continue

            try:
                ip = ipaddress.ip_address(endereco.address)
            except ValueError:
                continue

            if ip.is_loopback or ip.is_link_local or not ip.is_private:
                continue

            prioridade = 10
            if "wi-fi" in nome_normalizado or "wifi" in nome_normalizado or "wireless" in nome_normalizado:
                prioridade = 0
            elif "ethernet" in nome_normalizado:
                prioridade = 5

            candidatos.append((prioridade, nome, endereco.address))

    if candidatos:
        return sorted(candidatos)[0][2]

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def _gerar_qrcode_b64(url: str) -> str:
    qr = qrcode.QRCode(box_size=16, border=4, error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def _origem_aluno() -> str:
    configurada = os.getenv("ALUNO_PUBLIC_URL", "").strip().rstrip("/")
    if configurada:
        host = urlsplit(configurada).hostname
        local = host == "localhost"
        try:
            local = local or ipaddress.ip_address(host).is_loopback
        except ValueError:
            pass
        if not local:
            return configurada
    return f"http://{_ip_local()}:{_PORTA_ALUNO}"


def tela_sessao_professor(page: ft.Page) -> ft.View:
    codigo_text = ft.Text("----", size=56, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)
    qr_image = ft.Image(
        width=720, height=720, fit=ft.ImageFit.CONTAIN,
        filter_quality=ft.FilterQuality.NONE, visible=False,
        semantics_label="QR code para entrar na sala",
    )
    _url_entrada = [None]

    def copiar_link(e) -> None:
        if not _url_entrada[0]:
            return
        try:
            page.set_clipboard(_url_entrada[0])
        except Exception:
            page.open(ft.SnackBar(ft.Text("Não foi possível copiar o link. Tente novamente.")))
            return
        page.open(ft.SnackBar(ft.Text("Link da sala copiado! Compartilhe com os alunos.")))

    btn_copiar_link = ft.OutlinedButton(
        text="Copiar link da sala", icon=ft.Icons.CONTENT_COPY,
        on_click=copiar_link, visible=False, height=BTN_H,
        style=ft.ButtonStyle(color=TEXT_PRIMARY),
        tooltip="Copia o mesmo link do QR code, incluindo o código da sala",
    )
    status_text = ft.Text("Escolha um quiz para abrir a sala", color=TEXT_SECONDARY, size=FONT_CAPTION)
    participantes_col = ft.Column(spacing=8)
    respondidos_text = ft.Text("", color=TEXT_SECONDARY, size=FONT_CAPTION)
    etapa_text = ft.Text("Etapa 1 de 3: Selecionar quiz", size=FONT_CAPTION, color=TEXT_SECONDARY)
    questao_text = ft.Text("", color=TEXT_PRIMARY, size=FONT_BODY, weight=ft.FontWeight.BOLD, visible=False)
    tempo_text = ft.Text("", color=TEXT_SECONDARY, size=FONT_CAPTION, visible=False)

    _codigo = [None]
    _timer_ativo = [False]

    midia_sessao = ft.Container(visible=False)
    _midia_url_atual = [None]

    def _render_media_sessao(url: str | None) -> ft.Control | None:
        if not url:
            return None
        video_id = id_video_youtube(url)
        if video_id:
            if page.web:
                return ft.WebView(
                    url=f"https://www.youtube.com/embed/{video_id}?autoplay=1&mute=1&rel=0&playsinline=1",
                    height=360, enable_javascript=True,
                )
            thumbnail = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
            return ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
                controls=[
                    ft.Image(src=thumbnail, height=140, fit=ft.ImageFit.CONTAIN, border_radius=CARD_RADIUS),
                    ft.ElevatedButton(
                        "Abrir video no navegador",
                        icon=ft.Icons.PLAY_CIRCLE_OUTLINE,
                        on_click=lambda _, u=url: page.launch_url(u, web_window_name="_blank"),
                    ),
                ],
            )
        if eh_imagem(url):
            return ft.Image(src=url, height=160, fit=ft.ImageFit.CONTAIN, border_radius=CARD_RADIUS)
        return ft.ElevatedButton(
            "Abrir mídia",
            icon=ft.Icons.OPEN_IN_NEW,
            on_click=lambda _, u=url: page.launch_url(u, web_window_name="_blank"),
        )

    selector = ft.Dropdown(
        label="Selecionar quiz",
        bgcolor=BG_INPUT, border_color=BORDER,
        focused_border_color=ACCENT, color=TEXT_PRIMARY,
        label_style=ft.TextStyle(color=TEXT_SECONDARY),
        options=[],
    )
    _mapa_quizzes = {}

    btn_criar = ft.ElevatedButton(
        text="Gerar código",
        bgcolor=ACCENT, color=ft.Colors.ON_PRIMARY, width=CARD_W, height=BTN_H,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=BTN_RADIUS)),
    )
    btn_iniciar = ft.ElevatedButton(
        text="Começar quiz",
        width=CARD_W, height=BTN_H,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=BTN_RADIUS),
            bgcolor={ft.ControlState.DISABLED: BG_INPUT, ft.ControlState.DEFAULT: TEXT_SUCCESS},
            color={ft.ControlState.DISABLED: TEXT_SECONDARY, ft.ControlState.DEFAULT: BTN_GREEN_TEXT},
        ),
        visible=False, disabled=True,
    )
    erro = ft.Text("", color=TEXT_DANGER, size=FONT_CAPTION)

    def carregar_quizzes() -> None:
        try:
            quizzes = api.listar_quizzes_do_docente(page.docente_id)
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
            codigo = api.criar_sessao(id_quiz, page.docente_id)
        except ApiError as ex:
            erro.value = ex.detail
            page.update()
            return

        try:
            origem_aluno = _origem_aluno()
            url = f"{origem_aluno}?codigo={codigo}"
            qr_b64 = _gerar_qrcode_b64(url)
        except Exception as ex:
            erro.value = f"Erro ao gerar acesso da sala: {type(ex).__name__}: {ex}"
            page.update()
            return

        _codigo[0] = codigo
        codigo_text.value = codigo
        qr_image.src_base64 = qr_b64
        qr_image.visible = True
        _url_entrada[0] = url
        btn_copiar_link.visible = True
        btn_criar.visible = False
        btn_iniciar.visible = True
        btn_iniciar.disabled = True
        selector.disabled = True
        selector.visible = False
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
        token = api.auth_token()
        if not token:
            status_text.value = "Sessão expirada"
            page.update()
            return
        uri = api.websocket_url(f"/ws/professor/{codigo}")
        try:
            async with websockets.connect(uri, open_timeout=30, additional_headers={"Origin": "http://localhost"}) as ws:
                await ws.send(json.dumps({"token": token}))
                async for texto in ws:
                    dados = json.loads(texto)
                    tipo = dados.get("tipo")

                    if tipo == "lobby":
                        participantes = dados.get("participantes", [])
                        n = len(participantes)
                        status_text.value = f"{n} aluno{'s' if n != 1 else ''} na sala"
                        if btn_iniciar.visible:
                            btn_iniciar.disabled = n == 0
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
                        acesso_sala.visible = False
                        andamento_sala.visible = True
                        numero = dados.get("numero", 1)
                        total = dados.get("total", 1)
                        peso = dados.get("peso", 1)
                        questao_text.value = f"Questão {numero} de {total} · {formatar_pontos(peso)} ponto{'s' if peso != 1 else ''}"
                        questao_text.visible = True
                        tempo_text.value = "0s decorridos"
                        tempo_text.visible = True
                        _timer_ativo[0] = True
                        page.run_task(_timer_questao)
                        nova_url = dados.get("link_midia")
                        chave_midia = id_video_youtube(nova_url) if nova_url else None
                        chave_midia = chave_midia or nova_url
                        if chave_midia != _midia_url_atual[0]:
                            _midia_url_atual[0] = chave_midia
                            midia = _render_media_sessao(nova_url)
                            if midia:
                                midia_sessao.content = midia
                                midia_sessao.visible = True
                            else:
                                midia_sessao.content = None
                                midia_sessao.visible = False
                        page.update()

                    elif tipo == "responderam":
                        total = dados.get("total", 0)
                        respondidos = dados.get("respondidos", 0)
                        respondidos_text.value = f"{respondidos} de {total} responderam"
                        page.update()

                    elif tipo == "resultado_professor":
                        _timer_ativo[0] = False
                        respondidos_text.value = ""
                        status_text.value = "todos responderam"
                        page.update()

                    elif tipo == "fim":
                        midia_sessao.content = None
                        midia_sessao.visible = False
                        _midia_url_atual[0] = None
                        acesso_sala.visible = False
                        andamento_sala.visible = True
                        titulo_andamento.value = "Resultado da aula"
                        _timer_ativo[0] = False
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
                                            f"{formatar_pontos(item['pontos'])} pt{'s' if item['pontos'] != 1 else ''}",
                                            color=TEXT_SECONDARY,
                                            size=FONT_CAPTION,
                                        ),
                                    ],
                                ),
                            )
                            for pos, item in enumerate(placar, start=1)
                        ]
                        page.update()

        except websockets.exceptions.ConnectionClosed as e:
            btn_iniciar.disabled = True
            _timer_ativo[0] = False
            code = e.rcvd.code if e.rcvd else 0
            print(f"[ws-professor] conexão fechada code={code}: {e}")
            if code == 4008:
                status_text.value = "Sessão inválida — faça login novamente"
            else:
                status_text.value = "Conexão encerrada pelo servidor"
            page.update()
        except OSError as e:
            btn_iniciar.disabled = True
            _timer_ativo[0] = False
            print(f"[ws-professor] erro de rede (OSError): {e}")
            status_text.value = "Não foi possível conectar ao servidor"
            page.update()
        except Exception as e:
            btn_iniciar.disabled = True
            _timer_ativo[0] = False
            print(f"[ws-professor] erro inesperado: {type(e).__name__}: {e}")
            status_text.value = f"Erro: {type(e).__name__}"
            page.update()
        finally:
            btn_iniciar.disabled = True
            page.update()

    def iniciar_quiz(e) -> None:
        if not _codigo[0] or btn_iniciar.disabled:
            return
        try:
            api.iniciar_sessao(_codigo[0])
        except ApiError as ex:
            erro.value = ex.detail
            page.update()
            return
        btn_iniciar.visible = False
        status_text.value = "Quiz começou!"
        etapa_text.value = "Etapa 3 de 3: Em andamento"
        acesso_sala.visible = False
        andamento_sala.visible = True
        page.update()

    btn_criar.on_click = criar_sessao
    btn_iniciar.on_click = iniciar_quiz

    abrir_automaticamente = getattr(page, "abrir_sala_automaticamente", False)
    if abrir_automaticamente:
        page.abrir_sala_automaticamente = False
        selector.visible = False

    async def preparar_sala_depois_de_renderizar() -> None:
        await asyncio.sleep(0.1)
        carregar_quizzes()
        if abrir_automaticamente:
            criar_sessao()

    page.run_task(preparar_sala_depois_de_renderizar)

    acesso_sala = ft.Column(
        expand=True,
        spacing=8,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Text("Entre na sala", size=28, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
            ft.Text("Aponte a câmera do celular para o QR code", size=18, color=TEXT_SECONDARY,
                    text_align=ft.TextAlign.CENTER),
            codigo_text,
            ft.Container(expand=True, alignment=ft.alignment.center, content=qr_image),
            btn_copiar_link,
            ft.Container(
                padding=ft.padding.symmetric(horizontal=CARD_PADDING_SM, vertical=8),
                bgcolor="#1a2a1a",
                border=ft.border.all(1, TEXT_SUCCESS),
                border_radius=CARD_RADIUS,
                content=ft.Row(
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    controls=[
                        ft.Icon(ft.Icons.WIFI, color=TEXT_SUCCESS, size=FONT_BODY),
                        ft.Column(spacing=2, expand=True, controls=[
                            ft.Text(
                                "Somente alunos na mesma rede Wi-Fi conseguem entrar.",
                                color=TEXT_SUCCESS, size=FONT_CAPTION,
                                weight=ft.FontWeight.W_600,
                            ),
                            ft.Text(
                                "Isso confirma presença física na aula, alunos fora da rede não conseguem participar.",
                                color=TEXT_SECONDARY, size=FONT_CAPTION,
                            ),
                        ]),
                    ],
                ),
            ),
        ],
    )
    titulo_andamento = ft.Text("Quiz em andamento", size=28, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)
    andamento_sala = ft.Column(
        expand=True, visible=False, spacing=SPACE_MD, scroll=ft.ScrollMode.AUTO,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        controls=[titulo_andamento, questao_text, midia_sessao, tempo_text, respondidos_text],
    )
    card_principal = ft.Container(
        expand=True, padding=CARD_PADDING_SM, bgcolor=BG_CARD, border_radius=CARD_RADIUS,
        content=ft.Column(expand=True, horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                          controls=[acesso_sala, andamento_sala]),
    )
    card_alunos = ft.Container(
        width=300,
        padding=CARD_PADDING_SM,
        bgcolor=BG_CARD,
        border_radius=CARD_RADIUS,
        content=ft.Column(
            spacing=SPACE_MD,
            controls=[
                etapa_text,
                selector,
                btn_criar,
                btn_iniciar,
                erro,
                ft.Divider(color=BORDER),
                ft.Text("Alunos na sala", size=20, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                status_text,
                ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, controls=[participantes_col]),
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
                    on_click=lambda _: page.go("/painel-professor"),
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
                    vertical_alignment=ft.CrossAxisAlignment.STRETCH,
                    controls=[card_alunos, card_principal],
                ),
            )
        ],
    )
