import sqlite3
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SRC = _REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.checkbox import CheckBox
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button

from app.design_system import tokens as T
from app.design_system.components.toast import mostrar_toast
from app.repos.quizzes_repo import (
    atualizar_quiz,
    buscar_quizzes_por_titulo_global,
    inserir_pergunta_com_duas_alternativas,
    inserir_quiz,
    listar_quizzes_do_docente,
    obter_primeira_pergunta_com_alternativas,
    obter_quiz,
    salvar_primeira_pergunta_com_duas_alternativas,
)

_NOVO = "— Novo quiz —"


class CriacaoQuizScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "criacao_quiz"
        self._id_quiz_atual: int | None = None
        self._rotulo_por_id: dict[int, str] = {}
        self._mapa_busca: dict[str, tuple[int, int]] = {}
        self._modo_consulta = False

        outer = BoxLayout(orientation="vertical", padding=dp(T.SPACING_XL), spacing=dp(T.SPACING_SM))

        outer.add_widget(
            Label(
                text="Quiz",
                font_size=dp(T.FONT_HEADING),
                size_hint_y=None,
                height=dp(T.LINE_TITLE),
            )
        )

        outer.add_widget(
            Label(
                text="Não pode repetir título igual (normaliza espaço e maiúscula).",
                font_size=dp(T.FONT_CAPTION),
                size_hint_y=None,
                height=dp(36),
            )
        )

        outer.add_widget(Label(text="Quiz", size_hint_y=None, height=dp(T.LINE_LABEL), halign="left"))
        self.spinner = Spinner(
            text=_NOVO,
            values=[_NOVO],
            size_hint_y=None,
            height=dp(T.INPUT_HEIGHT_COMFY),
            sync_height=True,
        )
        self.spinner.bind(text=self._on_spinner_text)
        outer.add_widget(self.spinner)

        outer.add_widget(
            Label(
                text="Buscar quiz de outros docentes",
                font_size=dp(T.FONT_CAPTION),
                size_hint_y=None,
                height=dp(30),
            )
        )
        self.in_busca = TextInput(
            hint_text="Parte do título",
            multiline=False,
            size_hint_y=None,
            height=dp(T.INPUT_HEIGHT),
        )
        outer.add_widget(self.in_busca)
        btn_buscar = Button(text="Buscar no banco", size_hint_y=None, height=dp(T.INPUT_HEIGHT_COMFY))
        btn_buscar.bind(on_release=self._on_buscar_global)
        outer.add_widget(btn_buscar)
        self.sp_busca = Spinner(
            text="— Resultado da busca —",
            values=["— Resultado da busca —"],
            size_hint_y=None,
            height=dp(T.INPUT_HEIGHT_COMFY),
            sync_height=True,
        )
        self.sp_busca.bind(text=self._on_resultado_busca)
        outer.add_widget(self.sp_busca)

        form = BoxLayout(orientation="vertical", spacing=dp(T.TOAST_SPACING), size_hint_y=None)
        form.bind(minimum_height=form.setter("height"))

        def rot(t: str) -> Label:
            return Label(text=t, size_hint_y=None, height=dp(T.LINE_LABEL), halign="left")

        self.in_titulo = TextInput(
            hint_text="Título do quiz",
            multiline=False,
            size_hint_y=None,
            height=dp(T.INPUT_HEIGHT),
        )
        self.in_desc = TextInput(
            hint_text="Descrição (opcional)",
            multiline=True,
            size_hint_y=None,
            height=dp(72),
        )

        for w in (rot("Título"), self.in_titulo, rot("Descrição"), self.in_desc):
            form.add_widget(w)

        form.add_widget(
            Label(
                text="Pergunta",
                font_size=dp(T.FONT_CAPTION),
                size_hint_y=None,
                height=dp(40),
            )
        )
        self.in_enunciado = TextInput(
            hint_text="Enunciado",
            multiline=False,
            size_hint_y=None,
            height=dp(T.INPUT_HEIGHT),
        )
        self.in_alt_a = TextInput(
            hint_text="Alternativa A",
            multiline=False,
            size_hint_y=None,
            height=dp(T.INPUT_HEIGHT),
        )
        self.in_alt_b = TextInput(
            hint_text="Alternativa B",
            multiline=False,
            size_hint_y=None,
            height=dp(T.INPUT_HEIGHT),
        )

        row_cor = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(T.SPACING_MD))
        self.chk_a = CheckBox(size_hint_x=None, width=dp(36))
        self.chk_b = CheckBox(size_hint_x=None, width=dp(36))
        self.chk_a.bind(active=self._on_chk_a)
        self.chk_b.bind(active=self._on_chk_b)
        row_cor.add_widget(self.chk_a)
        row_cor.add_widget(Label(text="A correta", size_hint_x=None, width=dp(90)))
        row_cor.add_widget(self.chk_b)
        row_cor.add_widget(Label(text="B correta", size_hint_x=None, width=dp(90)))
        form.add_widget(self.in_enunciado)
        form.add_widget(self.in_alt_a)
        form.add_widget(self.in_alt_b)
        form.add_widget(row_cor)

        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(form)
        outer.add_widget(scroll)

        row_btn = BoxLayout(size_hint_y=None, height=dp(T.BUTTON_ROW_HEIGHT), spacing=dp(T.TOAST_SPACING))
        self.btn_salvar = Button(text="Salvar")
        self.btn_salvar.bind(on_release=self._on_salvar)
        btn_voltar = Button(text="Voltar")
        btn_voltar.bind(on_release=self._on_voltar)
        row_btn.add_widget(self.btn_salvar)
        row_btn.add_widget(btn_voltar)
        outer.add_widget(row_btn)

        self.add_widget(outer)

    def on_pre_enter(self, *args):
        self._recarregar_spinner()

    def _on_chk_a(self, _cb, active: bool) -> None:
        if active:
            self.chk_b.active = False

    def _on_chk_b(self, _cb, active: bool) -> None:
        if active:
            self.chk_a.active = False

    def _set_modo_consulta(self, ativo: bool) -> None:
        self._modo_consulta = ativo
        self.btn_salvar.text = (
            "Salvar cópia nos meus quizzes" if ativo else "Salvar"
        )
        self.btn_salvar.disabled = False
        self.btn_salvar.opacity = 1

    def _preencher_form_quiz_docente(self, id_q: int, id_docente: int) -> bool:
        try:
            row = obter_quiz(id_q, id_docente)
        except FileNotFoundError:
            return False
        if row is None:
            mostrar_toast("Erro", "Não carregou o quiz.")
            return False
        tit, desc = row
        self.in_titulo.text = tit
        self.in_desc.text = desc or ""
        try:
            pergunta = obter_primeira_pergunta_com_alternativas(id_q, id_docente)
        except FileNotFoundError:
            return False
        if pergunta is None:
            self.in_enunciado.text = ""
            self.in_alt_a.text = ""
            self.in_alt_b.text = ""
            self.chk_a.active = True
            self.chk_b.active = False
            return True
        enunciado, alt_a, alt_b, idx = pergunta
        self.in_enunciado.text = enunciado
        self.in_alt_a.text = alt_a
        self.in_alt_b.text = alt_b
        self.chk_a.active = idx == 0
        self.chk_b.active = idx == 1
        return True

    def _rotulo_quiz(self, id_q: int, titulo: str) -> str:
        return f"{id_q} · {titulo}"

    def _recarregar_spinner(self, selecionar_id: int | None = None) -> None:
        app = App.get_running_app()
        did = app.docente_id
        if did is None:
            self.spinner.values = [_NOVO]
            self.spinner.text = _NOVO
            return
        try:
            rows = listar_quizzes_do_docente(int(did))
        except FileNotFoundError:
            self.spinner.values = [_NOVO]
            self.spinner.text = _NOVO
            return

        self._rotulo_por_id = {}
        labels = [_NOVO]
        for id_q, tit in rows:
            lab = self._rotulo_quiz(id_q, tit)
            self._rotulo_por_id[id_q] = lab
            labels.append(lab)
        self.spinner.values = labels

        if selecionar_id is not None:
            lab_sel = self._rotulo_por_id.get(selecionar_id)
            if lab_sel:
                self.spinner.text = lab_sel
                self._id_quiz_atual = selecionar_id
                self._set_modo_consulta(False)
                self._preencher_form_quiz_docente(selecionar_id, int(did))
                return

        self.spinner.text = _NOVO
        self._id_quiz_atual = None
        self._set_modo_consulta(False)
        self._limpar_campos(manter_spinner=False)

    def _id_do_rotulo(self, rotulo: str) -> int | None:
        if rotulo == _NOVO:
            return None
        for id_q, lab in self._rotulo_por_id.items():
            if lab == rotulo:
                return id_q
        return None

    def _on_spinner_text(self, _sp, texto: str) -> None:
        id_q = self._id_do_rotulo(texto.strip())
        self._id_quiz_atual = id_q
        if id_q is None:
            self._set_modo_consulta(False)
            self._limpar_campos(manter_spinner=True)
            return
        self._set_modo_consulta(False)
        app = App.get_running_app()
        did = app.docente_id
        if did is None:
            return
        self._preencher_form_quiz_docente(id_q, int(did))

    def _on_buscar_global(self, *_args) -> None:
        termo = self.in_busca.text.strip()
        if not termo:
            mostrar_toast("Busca", "Digite algo para buscar.")
            return
        try:
            rows = buscar_quizzes_por_titulo_global(termo)
        except FileNotFoundError as e:
            mostrar_toast("DB", str(e))
            return
        self._mapa_busca = {}
        values = ["— Resultado da busca —"]
        for id_quiz, id_docente, titulo, nome, email in rows:
            rot = f"{id_quiz} · {titulo} — {nome}, {email}"
            values.append(rot)
            self._mapa_busca[rot] = (id_quiz, id_docente)
        self.sp_busca.values = values
        self.sp_busca.text = values[0]
        if len(values) == 1:
            mostrar_toast("Busca", "Nenhum quiz encontrado.")

    def _on_resultado_busca(self, _sp, texto: str) -> None:
        alvo = self._mapa_busca.get(texto.strip())
        if alvo is None:
            return
        id_quiz, id_docente = alvo
        try:
            row = obter_quiz(id_quiz, id_docente)
            pergunta = obter_primeira_pergunta_com_alternativas(id_quiz, id_docente)
        except FileNotFoundError as e:
            mostrar_toast("DB", str(e))
            return
        if row is None:
            mostrar_toast("Erro", "Quiz não encontrado.")
            return
        tit, desc = row
        self._id_quiz_atual = id_quiz
        self.in_titulo.text = tit
        self.in_desc.text = desc or ""
        if pergunta is None:
            self.in_enunciado.text = ""
            self.in_alt_a.text = ""
            self.in_alt_b.text = ""
            self.chk_a.active = True
            self.chk_b.active = False
        else:
            enunciado, alt_a, alt_b, idx = pergunta
            self.in_enunciado.text = enunciado
            self.in_alt_a.text = alt_a
            self.in_alt_b.text = alt_b
            self.chk_a.active = idx == 0
            self.chk_b.active = idx == 1
        app = App.get_running_app()
        meu_id = app.docente_id
        if meu_id is None or int(meu_id) != int(id_docente):
            self._set_modo_consulta(True)
            mostrar_toast(
                "Cópia",
                "Quiz de outro docente. Salvar cria uma cópia sua — o original não muda.",
            )
        else:
            self._set_modo_consulta(False)

    def _limpar_campos(self, *, manter_spinner: bool) -> None:
        if not manter_spinner:
            self.spinner.text = _NOVO
        self.in_titulo.text = ""
        self.in_desc.text = ""
        self.in_enunciado.text = ""
        self.in_alt_a.text = ""
        self.in_alt_b.text = ""
        self.chk_a.active = True
        self.chk_b.active = False

    def _on_voltar(self, *_args):
        self.manager.current = "inicio"

    def _on_salvar(self, *_args) -> None:
        app = App.get_running_app()
        did = app.docente_id
        if did is None:
            mostrar_toast("Login", "Deslogou? Entra de novo.")
            return

        tit = self.in_titulo.text.strip()
        desc = self.in_desc.text.strip()
        if not tit:
            mostrar_toast("Ops", "Falta título.")
            return

        try:
            if self._modo_consulta:
                qid = inserir_quiz(int(did), tit, desc or None)
                if obter_quiz(qid, int(did)) is None:
                    raise RuntimeError("Quiz não foi persistido no banco.")
                en = self.in_enunciado.text.strip()
                if en:
                    if not self.chk_a.active and not self.chk_b.active:
                        mostrar_toast("Ops", "Marca A ou B certa.")
                        return
                    ta = self.in_alt_a.text.strip()
                    tb = self.in_alt_b.text.strip()
                    cor = 0 if self.chk_a.active else 1
                    inserir_pergunta_com_duas_alternativas(qid, en, ta, tb, cor)
                mostrar_toast("Ok", f"Cópia salva nos seus quizzes, id {qid}.")
                self._recarregar_spinner(selecionar_id=qid)
                return

            if self._id_quiz_atual is None:
                qid = inserir_quiz(int(did), tit, desc or None)
                if obter_quiz(qid, int(did)) is None:
                    raise RuntimeError("Quiz não foi persistido no banco.")
                en = self.in_enunciado.text.strip()
                if en:
                    if not self.chk_a.active and not self.chk_b.active:
                        mostrar_toast("Ops", "Marca A ou B certa.")
                        return
                    ta = self.in_alt_a.text.strip()
                    tb = self.in_alt_b.text.strip()
                    cor = 0 if self.chk_a.active else 1
                    inserir_pergunta_com_duas_alternativas(qid, en, ta, tb, cor)
                mostrar_toast("Ok", f"Salvo, id {qid}.")
                self._recarregar_spinner()
            else:
                atualizar_quiz(self._id_quiz_atual, int(did), tit, desc or None)
                en = self.in_enunciado.text.strip()
                if en:
                    if not self.chk_a.active and not self.chk_b.active:
                        mostrar_toast("Ops", "Marca A ou B certa.")
                        return
                    ta = self.in_alt_a.text.strip()
                    tb = self.in_alt_b.text.strip()
                    cor = 0 if self.chk_a.active else 1
                    salvar_primeira_pergunta_com_duas_alternativas(
                        self._id_quiz_atual,
                        int(did),
                        en,
                        ta,
                        tb,
                        cor,
                    )
                mostrar_toast("Ok", "Atualizou.")
                self._recarregar_spinner()
        except ValueError as e:
            mostrar_toast("Ops", str(e))
        except sqlite3.IntegrityError:
            mostrar_toast("Título", "Já tem quiz com esse nome (normalizado).")
        except PermissionError as e:
            mostrar_toast("Ops", str(e))
        except FileNotFoundError as e:
            mostrar_toast("DB", str(e))
        except Exception as e:  # noqa: BLE001
            mostrar_toast("Erro", str(e))
