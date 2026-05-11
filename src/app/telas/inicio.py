import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SRC = _REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen

from app.design_system import tokens as T
from app.repos.docentes_repo import ADM


class InicioScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "inicio"

        self._layout = BoxLayout(
            orientation="vertical",
            padding=dp(T.SPACING_XXL),
            spacing=dp(T.SPACING_LG),
        )
        self._titulo = Label(
            text="Bem-vindo",
            font_size=dp(T.FONT_HEADING),
            size_hint_y=None,
            height=dp(T.LINE_TITLE),
        )
        self._sub = Label(
            text="",
            font_size=dp(T.FONT_SUBHEADING),
            size_hint_y=None,
            height=dp(T.TEXT_BLOCK_TWO_LINES),
        )
        self._layout.add_widget(self._titulo)
        self._layout.add_widget(self._sub)

        btn_quiz = Button(
            text="Criar / editar quiz",
            size_hint_y=None,
            height=dp(T.BUTTON_PRIMARY_HEIGHT),
        )
        btn_quiz.bind(on_release=lambda *_: setattr(self.manager, "current", "criacao_quiz"))
        self._layout.add_widget(btn_quiz)

        self._btn_cad = Button(
            text="Gerenciar docentes",
            size_hint_y=None,
            height=dp(T.BUTTON_SECONDARY_HEIGHT),
        )
        self._btn_cad.bind(
            on_release=lambda *_: setattr(self.manager, "current", "cadastro_docente")
        )
        self._layout.add_widget(self._btn_cad)

        btn_sair = Button(
            text="Sair (voltar ao login)",
            size_hint_y=None,
            height=dp(T.BUTTON_SECONDARY_HEIGHT),
        )
        btn_sair.bind(on_release=self._on_sair)
        self._layout.add_widget(btn_sair)

        self.add_widget(self._layout)

    def on_enter(self, *args):
        app = App.get_running_app()
        nome = app.docente_nome or "Docente"
        email = app.docente_email or ""
        self._sub.text = f"{nome}\n{email}"
        is_adm = app.docente_papel == ADM
        self._btn_cad.disabled = not is_adm
        self._btn_cad.opacity = 1 if is_adm else 0
        self._btn_cad.height = dp(T.BUTTON_SECONDARY_HEIGHT) if is_adm else 0

    def _on_sair(self, *_args):
        app = App.get_running_app()
        app.docente_id = None
        app.docente_nome = ""
        app.docente_email = ""
        app.docente_papel = ""
        self.manager.current = "login"
