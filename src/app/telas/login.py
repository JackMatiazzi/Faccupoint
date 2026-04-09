import sys
from collections import Counter
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SRC = _REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.textinput import TextInput

from app.design_system import tokens as T
from app.design_system.components.focus_widgets import FocusButton, FocusSpinner
from app.design_system.components.toast import mostrar_toast
from app.infra.pin_hash import verificar_pin
from app.repos.docentes_repo import listar_docentes, obter_docente_por_email

_PLACEHOLDER = "Selecione o usuário"


class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "login"
        self._email_por_rotulo: dict[str, str | None] = {_PLACEHOLDER: None}

        root = BoxLayout(
            orientation="vertical",
            padding=dp(T.SPACING_XXL),
            spacing=dp(T.SPACING_MD),
        )

        root.add_widget(
            Label(
                text="FaccuPoint — Login",
                font_size=dp(T.FONT_SCREEN_TITLE),
                size_hint_y=None,
                height=dp(T.LINE_HEADING),
            )
        )

        root.add_widget(
            Label(
                text="Usuário",
                size_hint_y=None,
                height=dp(T.LINE_LABEL),
                halign="left",
            )
        )
        self.spinner = FocusSpinner(
            text=_PLACEHOLDER,
            values=[_PLACEHOLDER],
            size_hint_y=None,
            height=dp(T.INPUT_HEIGHT_COMFY),
            sync_height=True,
        )
        root.add_widget(self.spinner)

        root.add_widget(
            Label(
                text="PIN",
                size_hint_y=None,
                height=dp(T.LINE_LABEL),
                halign="left",
            )
        )
        self.in_pin = TextInput(
            hint_text="4 dígitos",
            multiline=False,
            password=True,
            write_tab=False,
            size_hint_y=None,
            height=dp(T.INPUT_HEIGHT_COMFY),
        )
        self.in_pin.bind(on_text_validate=self._on_entrar)
        root.add_widget(self.in_pin)

        self.btn_entrar = FocusButton(
            text="Entrar",
            size_hint_y=None,
            height=dp(T.BUTTON_PRIMARY_HEIGHT),
        )
        self.btn_entrar.bind(on_release=self._on_entrar)
        root.add_widget(self.btn_entrar)

        self.spinner.focus_next = self.in_pin
        self.in_pin.focus_previous = self.spinner
        self.in_pin.focus_next = self.btn_entrar
        self.btn_entrar.focus_previous = self.in_pin
        self.btn_entrar.focus_next = self.spinner
        self.spinner.focus_previous = self.btn_entrar

        self.add_widget(root)

    def on_pre_enter(self, *args):
        self._recarregar_docentes()
        Clock.schedule_once(self._focar_seletor, 0.2)

    def _focar_seletor(self, _dt):
        self.spinner.focus = True

    def _recarregar_docentes(self) -> None:
        self._email_por_rotulo = {_PLACEHOLDER: None}
        try:
            rows = listar_docentes()
        except FileNotFoundError:
            self.spinner.values = [_PLACEHOLDER]
            self.spinner.text = _PLACEHOLDER
            return

        if not rows:
            self.spinner.values = [_PLACEHOLDER]
            self.spinner.text = _PLACEHOLDER
            return

        contagem = Counter(nome for _, nome, _ in rows)
        labels: list[str] = []
        for _id, nome, email in rows:
            if contagem[nome] > 1:
                label = f"{nome} ({email})"
            else:
                label = nome
            labels.append(label)
            self._email_por_rotulo[label] = email.strip().lower()

        self.spinner.values = [_PLACEHOLDER] + labels
        self.spinner.text = _PLACEHOLDER

    def _email_selecionado(self) -> str | None:
        rotulo = self.spinner.text.strip()
        return self._email_por_rotulo.get(rotulo)

    def _on_entrar(self, *_args) -> None:
        email = self._email_selecionado()
        pin = self.in_pin.text.strip()

        if not email:
            mostrar_toast("Login", "Selecione o seu usuário na lista.")
            return
        if len(pin) != 4 or not pin.isdigit():
            mostrar_toast("Login", "O PIN deve ter 4 dígitos.")
            return

        try:
            row = obter_docente_por_email(email)
        except FileNotFoundError as e:
            mostrar_toast("Banco", str(e))
            return

        if row is None or not verificar_pin(pin, row[3]):
            mostrar_toast("Login", "PIN incorreto.")
            return

        app = App.get_running_app()
        app.docente_id = row[0]
        app.docente_nome = row[1]
        app.docente_email = row[2]
        app.docente_papel = row[4]

        self.in_pin.text = ""
        self.manager.current = "inicio"
