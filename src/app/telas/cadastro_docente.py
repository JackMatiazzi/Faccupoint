import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SRC = _REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import sqlite3

from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput

from app.design_system import tokens as T
from app.design_system.components.toast import mostrar_toast
from app.repos.docentes_repo import ADM, excluir_docente, inserir_docente, listar_docentes_com_papel

_EXCLUIR_PLACEHOLDER = "— Escolha para excluir —"


class CadastroDocenteScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "cadastro_docente"

        root = BoxLayout(
            orientation="vertical",
            padding=dp(T.SPACING_XL),
            spacing=dp(T.SPACING_SM),
        )

        root.add_widget(
            Label(
                text="Docentes",
                font_size=dp(T.FONT_HEADING),
                size_hint_y=None,
                height=dp(T.LINE_TITLE),
            )
        )
        root.add_widget(
            Label(
                text="Cadastro: PIN com 4 dígitos. Só administrador exclui usuários.",
                font_size=dp(T.FONT_CAPTION),
                size_hint_y=None,
                height=dp(T.LINE_SUBTITLE),
            )
        )

        form = BoxLayout(
            orientation="vertical",
            spacing=dp(T.TOAST_SPACING),
            size_hint_y=None,
        )
        form.bind(minimum_height=form.setter("height"))

        def rotulo(texto: str) -> Label:
            return Label(
                text=texto,
                size_hint_y=None,
                height=dp(T.LINE_LABEL),
                halign="left",
            )

        self.in_nome = TextInput(
            hint_text="Nome completo",
            multiline=False,
            size_hint_y=None,
            height=dp(T.INPUT_HEIGHT),
        )
        self.in_email = TextInput(
            hint_text="E-mail",
            multiline=False,
            size_hint_y=None,
            height=dp(T.INPUT_HEIGHT),
        )
        self.in_pin = TextInput(
            hint_text="PIN (4 dígitos)",
            multiline=False,
            password=True,
            size_hint_y=None,
            height=dp(T.INPUT_HEIGHT),
        )
        self.in_pin2 = TextInput(
            hint_text="Confirmar PIN",
            multiline=False,
            password=True,
            size_hint_y=None,
            height=dp(T.INPUT_HEIGHT),
        )

        for w in (
            rotulo("Nome"),
            self.in_nome,
            rotulo("E-mail"),
            self.in_email,
            rotulo("PIN"),
            self.in_pin,
            rotulo("Confirmar PIN"),
            self.in_pin2,
        ):
            form.add_widget(w)

        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(form)
        root.add_widget(scroll)

        root.add_widget(
            Label(
                text="Excluir docente (e seus quizzes)",
                font_size=dp(T.FONT_CAPTION),
                size_hint_y=None,
                height=dp(36),
                halign="left",
            )
        )
        self._id_excluir_por_rotulo: dict[str, int] = {}
        self.sp_excluir = Spinner(
            text=_EXCLUIR_PLACEHOLDER,
            values=[_EXCLUIR_PLACEHOLDER],
            size_hint_y=None,
            height=dp(T.INPUT_HEIGHT_COMFY),
            sync_height=True,
        )
        root.add_widget(self.sp_excluir)
        btn_excluir = Button(
            text="Excluir selecionado",
            size_hint_y=None,
            height=dp(T.BUTTON_SECONDARY_HEIGHT),
        )
        btn_excluir.bind(on_release=self._on_pedir_exclusao)
        root.add_widget(btn_excluir)

        row = BoxLayout(
            size_hint_y=None,
            height=dp(T.BUTTON_ROW_HEIGHT),
            spacing=dp(T.TOAST_SPACING),
        )
        btn_ok = Button(text="Cadastrar")
        btn_ok.bind(on_release=self._on_cadastrar)
        btn_voltar = Button(text="Voltar")
        btn_voltar.bind(on_release=self._on_voltar)
        row.add_widget(btn_ok)
        row.add_widget(btn_voltar)
        root.add_widget(row)

        self.add_widget(root)

    def on_pre_enter(self, *args):
        app = App.get_running_app()
        if app.docente_id is None:
            mostrar_toast("Acesso", "Faça login primeiro.")
            self.manager.current = "login"
            return
        if app.docente_papel != ADM:
            mostrar_toast("Acesso", "Só administrador cadastra docentes.")
            self.manager.current = "inicio"
            return
        self._recarregar_spinner_exclusao()

    def _recarregar_spinner_exclusao(self) -> None:
        app = App.get_running_app()
        meu_id = app.docente_id
        self._id_excluir_por_rotulo = {_EXCLUIR_PLACEHOLDER: -1}
        try:
            rows = listar_docentes_com_papel()
        except FileNotFoundError:
            self.sp_excluir.values = [_EXCLUIR_PLACEHOLDER]
            self.sp_excluir.text = _EXCLUIR_PLACEHOLDER
            return
        labels = [_EXCLUIR_PLACEHOLDER]
        for id_d, nome, email, papel in rows:
            if meu_id is not None and id_d == meu_id:
                continue
            rotulo = f"{nome} — {email} — {papel}"
            labels.append(rotulo)
            self._id_excluir_por_rotulo[rotulo] = id_d
        self.sp_excluir.values = labels
        self.sp_excluir.text = _EXCLUIR_PLACEHOLDER

    def _on_pedir_exclusao(self, *_args) -> None:
        rotulo = self.sp_excluir.text.strip()
        id_alvo = self._id_excluir_por_rotulo.get(rotulo, -1)
        if id_alvo is None or id_alvo < 0:
            mostrar_toast("Exclusão", "Escolha um docente na lista.")
            return

        app = App.get_running_app()
        id_admin = app.docente_id
        if id_admin is None:
            self.manager.current = "login"
            return

        content = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(12))
        content.add_widget(
            Label(
                text=f"Excluir permanentemente?\n{rotulo}",
                size_hint_y=None,
                height=dp(72),
            )
        )
        row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        popup = Popup(title="Confirmar exclusão", size_hint=(0.85, 0.35))

        def fechar(*_):
            popup.dismiss()

        def confirmar(*_):
            popup.dismiss()
            self._executar_exclusao(id_alvo, int(id_admin))

        btn_nao = Button(text="Cancelar")
        btn_nao.bind(on_release=fechar)
        btn_sim = Button(text="Excluir")
        btn_sim.bind(on_release=confirmar)
        row.add_widget(btn_nao)
        row.add_widget(btn_sim)
        content.add_widget(row)
        popup.content = content
        popup.open()

    def _executar_exclusao(self, id_alvo: int, id_admin: int) -> None:
        try:
            excluir_docente(id_alvo, id_admin)
        except ValueError as e:
            mostrar_toast("Exclusão", str(e))
            return
        except PermissionError as e:
            mostrar_toast("Exclusão", str(e))
            return
        except FileNotFoundError as e:
            mostrar_toast("Banco", str(e))
            return
        except Exception as e:  # noqa: BLE001
            mostrar_toast("Erro", str(e))
            return
        mostrar_toast("Ok", "Docente removido.")
        self._recarregar_spinner_exclusao()

    def _on_voltar(self, *_args):
        app = App.get_running_app()
        self.manager.current = "inicio" if app.docente_id is not None else "login"

    def _validar(self) -> tuple[bool, str]:
        nome = self.in_nome.text.strip()
        email = self.in_email.text.strip()
        pin = self.in_pin.text.strip()
        pin2 = self.in_pin2.text.strip()

        if not nome:
            return False, "Informe o nome."
        if not email or "@" not in email:
            return False, "Informe um e-mail válido."
        if len(pin) != 4 or not pin.isdigit():
            return False, "O PIN deve ter exatamente 4 dígitos."
        if pin != pin2:
            return False, "Os PINs não coincidem."
        return True, ""

    def _limpar(self) -> None:
        self.in_nome.text = ""
        self.in_email.text = ""
        self.in_pin.text = ""
        self.in_pin2.text = ""

    def _on_cadastrar(self, *_args) -> None:
        ok, msg = self._validar()
        if not ok:
            mostrar_toast("Validação", msg)
            return

        nome = self.in_nome.text.strip()
        email = self.in_email.text.strip()
        pin = self.in_pin.text.strip()

        try:
            inserir_docente(nome, email, pin)
        except FileNotFoundError as e:
            mostrar_toast("Banco", str(e))
            return
        except sqlite3.IntegrityError:
            mostrar_toast("Cadastro", "Já existe um docente com este e-mail.")
            return
        except Exception as e:  # noqa: BLE001
            mostrar_toast("Erro", f"Não foi possível salvar: {e}")
            return

        self._limpar()
        mostrar_toast("Sucesso", "Docente cadastrado no banco de dados.")
