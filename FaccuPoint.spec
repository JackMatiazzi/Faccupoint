# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
import sys

import flet_desktop
from PyInstaller.building.datastruct import Tree
from PyInstaller.utils.hooks import collect_all

sys.path.insert(0, str(Path.cwd()))
from ferramentas.icone_windows import criar_executavel_com_icone


icone_aplicacao = Path('frontend/assets/image/logoF.ico').resolve()
flet_original = Path(flet_desktop.__file__).parent / 'app' / 'flet' / 'flet.exe'
flet_personalizado = criar_executavel_com_icone(
    flet_original,
    icone_aplicacao,
    Path('build/recursos/flet.exe').resolve(),
)

arquivos_backend = Tree(
    'backend',
    prefix='backend',
    excludes=['.env', '.env.example', '.env.*', '__pycache__', '*.pyc', '*.pyo'],
)
arquivos_professor = Tree(
    'frontend/professor',
    prefix='professor',
    excludes=['__pycache__', '*.pyc', '*.pyo'],
)
arquivos_aluno = Tree(
    'frontend/aluno',
    prefix='aluno',
    excludes=['__pycache__', '*.pyc', '*.pyo'],
)
arquivos_compartilhados = Tree(
    'frontend/compartilhado',
    prefix='compartilhado',
    excludes=['__pycache__', '*.pyc', '*.pyo'],
)
dados_flet_web, binarios_flet_web, imports_flet_web = collect_all('flet_web')


a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=binarios_flet_web,
    datas=dados_flet_web,
    hiddenimports=imports_flet_web + [
        'requests', 'requests.adapters', 'requests.auth', 'requests.cookies',
        'requests.exceptions', 'requests.models', 'requests.sessions',
        'dotenv',
        'truststore',
        'qrcode', 'qrcode.image.base', 'qrcode.image.pure', 'qrcode.image.svg',
        'PIL', 'PIL.Image', 'PIL.ImageDraw',
        'psutil',
        'websockets', 'websockets.legacy', 'websockets.legacy.client',
        'uvicorn', 'uvicorn.logging', 'uvicorn.loops', 'uvicorn.loops.auto',
        'uvicorn.protocols', 'uvicorn.protocols.http', 'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets', 'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan', 'uvicorn.lifespan.on',
        'fastapi',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
a.binaries = [
    (
        destino,
        str(flet_personalizado)
        if destino.replace('\\', '/').endswith('flet_desktop/app/flet/flet.exe')
        else origem,
        tipo,
    )
    for destino, origem, tipo in a.binaries
]
a.datas += (
    arquivos_backend
    + arquivos_professor
    + arquivos_aluno
    + arquivos_compartilhados
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='FaccuPoint',
    icon=str(icone_aplicacao),
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version=None,
)
