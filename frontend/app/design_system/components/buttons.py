
import flet as ft

from app.design_system.tokens import (
    ACCENT, BG_PAGE, BORDER, BTN_H, BTN_RADIUS, CARD_RADIUS,
    FONT_CAPTION, G4, G8, G16,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_SUCCESS, BTN_GREEN_TEXT,
)



def btn_primary(text: str, on_click=None, icon: str | None = None) -> ft.ElevatedButton:
    return ft.ElevatedButton(
        text=text, icon=icon,
        bgcolor=TEXT_SUCCESS, color=BTN_GREEN_TEXT, height=BTN_H,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=BTN_RADIUS)),
        on_click=on_click,
    )


def btn_outline(text: str, on_click=None, icon: str | None = None) -> ft.OutlinedButton:
    return ft.OutlinedButton(
        text=text, icon=icon, height=BTN_H,
        style=ft.ButtonStyle(
            color=TEXT_PRIMARY,
            side=ft.BorderSide(1, BORDER),
            shape=ft.RoundedRectangleBorder(radius=BTN_RADIUS),
        ),
        on_click=on_click,
    )


def tab_btn(text: str, selected: bool, on_click=None) -> ft.TextButton:
    return ft.TextButton(
        text=text,
        expand=True,
        style=ft.ButtonStyle(
            color=TEXT_PRIMARY,
            bgcolor=ACCENT if selected else "transparent",
            side=ft.BorderSide(1, ACCENT if selected else BORDER),
            shape=ft.RoundedRectangleBorder(radius=G16),
            padding=ft.padding.symmetric(horizontal=G16, vertical=G8),
        ),
        on_click=on_click,
    )


def status_badge(text: str, active: bool = True) -> ft.Container:
    return ft.Container(
        padding=ft.padding.symmetric(horizontal=G8, vertical=G4),
        bgcolor=TEXT_SUCCESS if active else ACCENT,
        border_radius=CARD_RADIUS,
        content=ft.Text(text, color=BTN_GREEN_TEXT, size=FONT_CAPTION, weight=ft.FontWeight.W_600),
    )


def counter_badge(content: ft.Control) -> ft.Container:
    from app.design_system.tokens import G12
    return ft.Container(
        padding=ft.padding.symmetric(horizontal=G12, vertical=G4),
        bgcolor=ACCENT,
        border=ft.border.all(1, TEXT_PRIMARY),
        border_radius=G16,
        content=content,
    )
