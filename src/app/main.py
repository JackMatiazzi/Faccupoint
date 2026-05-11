import sys
import warnings
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_SRC = _REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from kivy.app import App
from kivy.uix.screenmanager import FadeTransition, ScreenManager

from app.telas.cadastro_docente import CadastroDocenteScreen
from app.telas.criacao_quiz import CriacaoQuizScreen
from app.telas.inicio import InicioScreen
from app.telas.login import LoginScreen


class FaccupointApp(App):
    docente_id = None
    docente_nome = ""
    docente_email = ""
    docente_papel = ""

    def build(self):
        self.title = "FaccuPoint"
        sm = ScreenManager(transition=FadeTransition(duration=0.15))
        sm.add_widget(LoginScreen())
        sm.add_widget(InicioScreen())
        sm.add_widget(CadastroDocenteScreen())
        sm.add_widget(CriacaoQuizScreen())
        sm.current = "login"
        return sm


def run_app() -> None:
    FaccupointApp().run()


if __name__ == "__main__":
    warnings.warn(
        "Use na raiz do repo: python main.py  (não execute este arquivo direto.)",
        UserWarning,
        stacklevel=1,
    )
    run_app()
