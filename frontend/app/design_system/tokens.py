from __future__ import annotations

import flet as ft

# cores
BG_PAGE        = "#111116"
BG_CARD        = "#1c1c24"
BG_INPUT       = "#262630"
BORDER         = "#383847"
ACCENT         = "#6090ff"
TEXT_PRIMARY   = "#f2f2f8"
TEXT_SECONDARY = "#8c8ca6"
TEXT_DANGER    = "#ff5c5c"
TEXT_SUCCESS   = "#48d98c"
BTN_GREEN_TEXT = "#111116"
BTN_DANGER     = "#8c2121"

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
FONT_CAPTION    = G12       # legenda, erro, hint
FONT_BODY       = G16       # texto padrão
FONT_TITLE      = G16 + G4  # título de card (20)
FONT_SUBHEADING = G16 + G4  # alias de FONT_TITLE
FONT_HEADING    = G24       # cabeçalho de seção
FONT_DISPLAY    = G32       # título principal de tela
FONT_CODE       = G48       # código de sala

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
CARD_W          = G32 * 12 + G16   # 400
CARD_PADDING    = G32
CARD_PADDING_SM = G24
SPACE_MD        = G16
CARD_RADIUS     = G12
BTN_RADIUS      = G8

# componentes
BTN_H         = G48
BTN_QUESTAO_H = G8 * 7   # 56
INPUT_H       = G48
