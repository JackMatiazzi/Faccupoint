
import flet as ft

from compartilhado.sistema_design.tokens import ACCENT, BG_INPUT, BORDER, TEXT_PRIMARY, TEXT_SECONDARY


def campo(label: str, **kwargs) -> ft.TextField:
    return ft.TextField(
        label=label,
        bgcolor=BG_INPUT,
        border_color=BORDER,
        focused_border_color=ACCENT,
        border_radius=8,
        cursor_color=ACCENT,
        color=TEXT_PRIMARY,
        label_style=ft.TextStyle(color=TEXT_SECONDARY),
        content_padding=ft.padding.symmetric(horizontal=14, vertical=12),
        **kwargs,
    )
