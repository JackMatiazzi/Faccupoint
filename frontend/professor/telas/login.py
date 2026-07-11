
import asyncio
import flet as ft

from compartilhado.sistema_design.tokens import (
    ACCENT, BG_CARD, BG_PAGE, BTN_H, BTN_RADIUS, CARD_PADDING,
    CARD_RADIUS, CARD_W, FONT_CAPTION, FONT_DISPLAY, SPACE_MD,
    TEXT_DANGER, TEXT_PRIMARY, TEXT_SECONDARY,
)
from compartilhado.sistema_design.componentes.campos import campo
from professor.servicos import cliente_api as api
from professor.servicos.cliente_api import ApiError


def tela_login(page: ft.Page) -> ft.View:
    erro = ft.Text("", color=TEXT_DANGER, size=FONT_CAPTION)

    aviso_conexao = ft.Row(
        visible=False,
        alignment=ft.MainAxisAlignment.CENTER,
        controls=[
            ft.Icon(ft.Icons.INFO_OUTLINE, color=TEXT_SECONDARY, size=14),
            ft.Text(
                "Conectando ao servidor...",
                color=TEXT_SECONDARY,
                size=FONT_CAPTION,
            ),
        ],
    )
    _aviso_texto = aviso_conexao.controls[1]

    campo_email = campo("Email", hint_text="seu@email.com", keyboard_type=ft.KeyboardType.EMAIL)
    campo_pin = campo("PIN", hint_text="4 dígitos", password=True, can_reveal_password=True,
                      keyboard_type=ft.KeyboardType.NUMBER, max_length=4)

    btn_entrar = ft.ElevatedButton(
        text="Entrar",
        bgcolor=ACCENT,
        color=TEXT_PRIMARY,
        width=CARD_W,
        height=BTN_H,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=BTN_RADIUS)),
    )

    async def _tentar_login(email: str, pin: str) -> None:
        _MAX_TENTATIVAS = 6
        _ESPERA_ENTRE = 10

        for tentativa in range(1, _MAX_TENTATIVAS + 1):
            try:
                docente = await asyncio.to_thread(api.login, email, pin)
                page.docente_id = docente.id_docente
                page.docente_nome = docente.nome
                page.docente_email = docente.email
                page.docente_papel = docente.papel
                page.go("/painel-professor")
                return
            except ApiError as ex:
                servidor_fora = ex.status == 0 and "fora do ar" in ex.detail
                if ex.status == 429:
                    aviso_conexao.visible = False
                    segundos = ex.retry_after or 60
                    for restante in range(segundos, 0, -1):
                        erro.value = f"Muitas tentativas. Tente novamente em {restante}s."
                        page.update()
                        await asyncio.sleep(1)
                    erro.value = "Voce ja pode tentar novamente."
                    btn_entrar.disabled = False
                    page.update()
                    return
                elif servidor_fora and tentativa < _MAX_TENTATIVAS:
                    _aviso_texto.value = (
                        f"Servidor iniciando... aguarde ({tentativa}/{_MAX_TENTATIVAS})"
                    )
                    aviso_conexao.visible = True
                    page.update()
                    await asyncio.sleep(_ESPERA_ENTRE)
                else:
                    erro.value = ex.detail if not servidor_fora else "Servidor não respondeu. Tente novamente."
                    aviso_conexao.visible = False
                    btn_entrar.disabled = False
                    page.update()
                    return

    def entrar(e) -> None:
        erro.value = ""
        email = campo_email.value.strip().lower()
        pin = campo_pin.value.strip()

        if not email or "@" not in email:
            erro.value = "Email inválido"
            page.update()
            return
        if len(pin) != 4 or not pin.isdigit():
            erro.value = "PIN deve ter 4 dígitos"
            page.update()
            return

        aviso_conexao.visible = True
        _aviso_texto.value = "Conectando ao servidor..."
        btn_entrar.disabled = True
        page.update()

        page.run_task(_tentar_login, email, pin)

    btn_entrar.on_click = entrar
    campo_pin.on_submit = entrar

    card = ft.Container(
        width=CARD_W,
        padding=ft.padding.all(CARD_PADDING),
        bgcolor=BG_CARD,
        border_radius=CARD_RADIUS,
        content=ft.Column(
            spacing=SPACE_MD,
            controls=[
                ft.Text("FaccuPoint", size=FONT_DISPLAY, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Text("Para professores", size=FONT_CAPTION, color=TEXT_SECONDARY),
                ft.Divider(height=8, color="transparent"),
                campo_email,
                campo_pin,
                erro,
                btn_entrar,
                aviso_conexao,
            ],
        ),
    )

    return ft.View(
        route="/",
        bgcolor=BG_PAGE,
        padding=0,
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[card],
    )
