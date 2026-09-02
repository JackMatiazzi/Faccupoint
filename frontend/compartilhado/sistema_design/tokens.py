
import flet as ft

# Cores semanticas: o Flet resolve cada uma conforme o tema claro/escuro.
BG_PAGE        = ft.Colors.SURFACE
BG_CARD        = ft.Colors.SURFACE_CONTAINER_HIGHEST
BG_INPUT       = ft.Colors.SURFACE_CONTAINER_HIGHEST
BORDER         = ft.Colors.OUTLINE
ACCENT         = ft.Colors.PRIMARY
TEXT_PRIMARY   = ft.Colors.ON_SURFACE
TEXT_SECONDARY = ft.Colors.ON_SURFACE_VARIANT
TEXT_DANGER    = ft.Colors.ERROR
TEXT_SUCCESS   = "#087443"
TEXT_ON_ACCENT = ft.Colors.ON_PRIMARY
BTN_GREEN_TEXT = "#FFFFFF"
BTN_DANGER     = ft.Colors.ERROR

CORES_ALTERNATIVAS = ["#4355b9", "#c43e31", "#2e7d32", "#e65100"]

# grade base
G2  =  2
G4  =  4
G8  =  8
G12 = 12
G16 = 16
G24 = 24
G32 = 32
G48 = 48
G64 = 64

# tipografia
FONT_CAPTION    = G12
FONT_BODY       = G16
FONT_TITLE      = G16 + G4
FONT_SUBHEADING = G16 + G4
FONT_HEADING    = G24
FONT_DISPLAY    = G32
FONT_CODE       = G48

# estilos de texto
T_DISPLAY = {"size": FONT_DISPLAY, "weight": ft.FontWeight.BOLD,  "color": TEXT_PRIMARY}
T_HEADING = {"size": FONT_HEADING, "weight": ft.FontWeight.BOLD,  "color": TEXT_PRIMARY}
T_TITLE   = {"size": FONT_TITLE,   "weight": ft.FontWeight.W_500, "color": TEXT_PRIMARY}
T_BODY    = {"size": FONT_BODY,                                    "color": TEXT_PRIMARY}
T_CAPTION = {"size": FONT_CAPTION,                                 "color": TEXT_SECONDARY}
T_ERRO    = {"size": FONT_CAPTION,                                 "color": TEXT_DANGER}
T_SUCESSO = {"size": FONT_CAPTION,                                 "color": TEXT_SUCCESS}
T_CODE    = {"size": FONT_CODE,    "weight": ft.FontWeight.BOLD,  "color": ACCENT}

# layout
CARD_W          = G32 * 12 + G16
CARD_PADDING    = G32
CARD_PADDING_SM = G24
SPACE_MD        = G16
CARD_RADIUS     = G12
BTN_RADIUS      = G8

# componentes
BTN_H         = G48
BTN_QUESTAO_H = G8 * 7
INPUT_H       = G48
