import flet as ft


_CHAVE_TEMA = "faccupoint.tema"


def configurar_tema(page: ft.Page) -> None:
    try:
        preferencia = page.client_storage.get(_CHAVE_TEMA)
    except Exception:
        preferencia = None
    page.theme_mode = ft.ThemeMode.LIGHT if preferencia == "claro" else ft.ThemeMode.DARK
    page.theme = ft.Theme(
        use_material3=True,
        color_scheme=ft.ColorScheme(
            primary="#3457B1", on_primary="#FFFFFF",
            surface="#F7F7FC", on_surface="#171722",
            surface_variant="#E2E3EC", on_surface_variant="#454754",
            outline="#666978", error="#B42318", on_error="#FFFFFF",
        ),
        scaffold_bgcolor="#F7F7FC", card_color="#E2E3EC", divider_color="#666978",
    )
    page.dark_theme = ft.Theme(
        use_material3=True,
        color_scheme=ft.ColorScheme(
            primary="#A9BEFF", on_primary="#10275F",
            surface="#101116", on_surface="#F5F5FA",
            surface_variant="#30323A", on_surface_variant="#D1D3DC",
            outline="#9A9DAA", error="#FFB4AB", on_error="#690005",
        ),
        scaffold_bgcolor="#101116", card_color="#30323A", divider_color="#9A9DAA",
    )

    def alternar(e=None) -> None:
        page.theme_mode = (
            ft.ThemeMode.LIGHT
            if page.theme_mode == ft.ThemeMode.DARK
            else ft.ThemeMode.DARK
        )
        valor = "claro" if page.theme_mode == ft.ThemeMode.LIGHT else "escuro"
        try:
            page.client_storage.set(_CHAVE_TEMA, valor)
        except Exception:
            pass
        page.update()

    page.alternar_tema = alternar


def botao_tema(page: ft.Page) -> ft.IconButton:
    icone = ft.Icons.DARK_MODE if page.theme_mode == ft.ThemeMode.LIGHT else ft.Icons.LIGHT_MODE
    return ft.IconButton(
        icon=icone,
        tooltip="Alternar tema claro/escuro",
        autofocus=False,
        on_click=getattr(page, "alternar_tema", None),
    )
