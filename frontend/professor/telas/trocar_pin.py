
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


def tela_trocar_pin(page: ft.Page) -> ft.View:
    mensagem = ft.Text("", size=FONT_CAPTION, color=TEXT_DANGER)

    campo_novo = campo(
        "Novo PIN", hint_text="4 dígitos", password=True, can_reveal_password=True,
        keyboard_type=ft.KeyboardType.NUMBER, max_length=4, autofocus=True,
    )
    campo_confirma = campo(
        "Confirmar novo PIN", hint_text="repita o PIN", password=True, can_reveal_password=True,
        keyboard_type=ft.KeyboardType.NUMBER, max_length=4,
    )

    btn_salvar = ft.ElevatedButton(
        text="Salvar novo PIN",
        bgcolor=ACCENT,
        color=TEXT_ON_ACCENT,
        width=CARD_W,
        height=BTN_H,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=BTN_RADIUS)),
    )

    def _voltar_login(_=None) -> None:
        api.limpar_token()
        page.docente_id = None
        page.docente_nome = page.docente_email = page.docente_papel = ""
        page.precisa_trocar_pin = False
        page.pin_temporario = None
        page.go("/")

    _salvando = [False]

    async def _salvar(novo: str) -> None:
        pin_atual = getattr(page, "pin_temporario", None) or ""
        try:
            await asyncio.to_thread(api.trocar_pin, pin_atual, novo)
        except ApiError as ex:
            if ex.status == 429:
                mensagem.value = "Muitas tentativas. Aguarde um pouco e tente de novo."
            elif ex.status == 401:
                mensagem.value = "Sessão expirada. Entre de novo com o PIN provisório."
            else:
                mensagem.value = ex.detail
            _salvando[0] = False
            btn_salvar.disabled = False
            page.update()
            return
        page.precisa_trocar_pin = False
        page.pin_temporario = None
        page.go("/painel-professor")

    def salvar(e) -> None:
        if _salvando[0]:
            return

        novo = (campo_novo.value or "").strip()
        confirma = (campo_confirma.value or "").strip()
        mensagem.value = ""

        if len(novo) != 4 or not novo.isdigit():
            mensagem.value = "O PIN deve ter exatamente 4 dígitos"
            page.update()
            return
        if novo != confirma:
            mensagem.value = "Os dois campos precisam ser iguais"
            page.update()
            return

        _salvando[0] = True
        btn_salvar.disabled = True
        page.update()
        page.run_task(_salvar, novo)

    btn_salvar.on_click = salvar
    campo_confirma.on_submit = salvar

    card = ft.Container(
        width=CARD_W,
        padding=ft.padding.all(CARD_PADDING),
        bgcolor=BG_CARD,
        border_radius=CARD_RADIUS,
        content=ft.Column(
            spacing=SPACE_MD,
            controls=[
                ft.Text("Defina seu PIN", size=FONT_DISPLAY, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Text(
                    "Você entrou com um PIN provisório. Escolha um PIN só seu para continuar.",
                    size=FONT_CAPTION, color=TEXT_SECONDARY,
                ),
                ft.Divider(height=8, color="transparent"),
                campo_novo,
                campo_confirma,
                mensagem,
                btn_salvar,
                ft.TextButton(text="Entrar com outra conta", on_click=_voltar_login),
            ],
        ),
    )

    return ft.View(
        route="/trocar-pin",
        bgcolor=BG_PAGE,
        padding=0,
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[card],
    )
