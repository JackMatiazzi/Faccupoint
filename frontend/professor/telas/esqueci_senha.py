
import asyncio
import flet as ft

from compartilhado.sistema_design.tokens import (
    ACCENT, BG_CARD, BG_PAGE, BTN_H, BTN_RADIUS, CARD_PADDING, TEXT_ON_ACCENT,
    CARD_RADIUS, CARD_W, FONT_CAPTION, FONT_DISPLAY, SPACE_MD,
    TEXT_DANGER, TEXT_PRIMARY, TEXT_SECONDARY,
)
from compartilhado.sistema_design.componentes.campos import campo
from professor.servicos import cliente_api as api
from professor.servicos.cliente_api import ApiError


def tela_esqueci_senha(page: ft.Page) -> ft.View:
    mensagem = ft.Text("", size=FONT_CAPTION, text_align=ft.TextAlign.CENTER)

    campo_email = campo("Email", hint_text="seu@email.com", keyboard_type=ft.KeyboardType.EMAIL)

    btn_enviar = ft.ElevatedButton(
        text="Avisar os administradores",
        bgcolor=ACCENT,
        color=TEXT_ON_ACCENT,
        width=CARD_W,
        height=BTN_H,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=BTN_RADIUS)),
    )

    _enviando = [False]

    async def _pedir_reset(email: str) -> None:
        try:
            await asyncio.to_thread(api.esqueci_senha, email)
            mensagem.value = (
                "Se esse email estiver cadastrado, avisamos os administradores. "
                "Procure um deles para receber um PIN provisório."
            )
            mensagem.color = TEXT_SECONDARY
        except ApiError as ex:
            if ex.status == 429:
                mensagem.value = "Muitas tentativas. Tente novamente mais tarde."
            else:
                mensagem.value = "Não foi possível registrar a solicitação agora. Tente novamente."
            mensagem.color = TEXT_DANGER
        finally:
            _enviando[0] = False
            btn_enviar.disabled = False
            page.update()

    def enviar(e) -> None:
        if _enviando[0]:
            return

        email = campo_email.value.strip().lower()
        if not email or "@" not in email:
            mensagem.value = "Email inválido"
            mensagem.color = TEXT_DANGER
            page.update()
            return

        _enviando[0] = True
        mensagem.value = ""
        btn_enviar.disabled = True
        page.update()
        page.run_task(_pedir_reset, email)

    btn_enviar.on_click = enviar
    campo_email.on_submit = enviar

    card = ft.Container(
        width=CARD_W,
        padding=ft.padding.all(CARD_PADDING),
        bgcolor=BG_CARD,
        border_radius=CARD_RADIUS,
        content=ft.Column(
            spacing=SPACE_MD,
            controls=[
                ft.Text("Esqueci minha senha", size=FONT_DISPLAY, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Text(
                    "Informe seu email. Os administradores são avisados e um deles gera um PIN provisório para você.",
                    size=FONT_CAPTION, color=TEXT_SECONDARY,
                ),
                ft.Divider(height=8, color="transparent"),
                campo_email,
                mensagem,
                btn_enviar,
                ft.TextButton(text="Voltar para o login", on_click=lambda _: page.go("/")),
            ],
        ),
    )

    return ft.View(
        route="/esqueci-senha",
        bgcolor=BG_PAGE,
        padding=0,
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[card],
    )
