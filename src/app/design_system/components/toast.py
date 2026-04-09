from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup

from app.design_system import tokens as T


def mostrar_toast(titulo: str, mensagem: str) -> None:
    content = BoxLayout(
        orientation="vertical",
        spacing=dp(T.TOAST_SPACING),
        padding=dp(T.TOAST_PADDING),
    )
    content.add_widget(
        Label(
            text=mensagem,
            text_size=(dp(T.TOAST_MESSAGE_WIDTH), None),
            halign="left",
        )
    )
    btn = Button(
        text="OK",
        size_hint_y=None,
        height=dp(T.TOAST_BUTTON_HEIGHT),
    )
    pop = Popup(
        title=titulo,
        content=content,
        size_hint=(T.TOAST_WIDTH_HINT, None),
        height=dp(T.TOAST_POPUP_HEIGHT),
    )
    btn.bind(on_release=pop.dismiss)
    content.add_widget(btn)
    pop.open()
