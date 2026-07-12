# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.building.datastruct import Tree
from PyInstaller.utils.hooks import collect_all


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
dados_flet_desktop, binarios_flet_desktop, imports_flet_desktop = collect_all('flet_desktop')


a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=binarios_flet_web + binarios_flet_desktop,
    datas=dados_flet_web + dados_flet_desktop,
    hiddenimports=imports_flet_web + imports_flet_desktop + [
        'requests', 'requests.adapters', 'requests.auth', 'requests.cookies',
        'requests.exceptions', 'requests.models', 'requests.sessions',
        'dotenv',
        'truststore',
        'qrcode', 'qrcode.image.base', 'qrcode.image.pil', 'qrcode.image.pure',
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
a.datas += (
    arquivos_backend
    + arquivos_professor
    + arquivos_aluno
    + arquivos_compartilhados
    + [(
        '.release-please-manifest.json',
        str(Path('.release-please-manifest.json').resolve()),
        'DATA',
    )]
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='FaccuPoint',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
