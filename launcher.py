
import sys
import os
from pathlib import Path

_FROZEN = getattr(sys, "frozen", False)
_MEIPASS = Path(sys._MEIPASS) if _FROZEN else Path(__file__).parent


def _fix_stdio():
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w")


if _FROZEN and "--run-backend" in sys.argv:
    _fix_stdio()
    sys.path.insert(0, str(_MEIPASS))
    os.chdir(str(_MEIPASS))
    import uvicorn
    from backend.main import app as _fastapi_app
    uvicorn.run(
        _fastapi_app,
        host="0.0.0.0",
        port=int(os.getenv("API_PORT", "8000")),
        log_level="error",
    )
    sys.exit(0)

if _FROZEN and "--run-aluno" in sys.argv:
    _fix_stdio()
    os.environ["FLET_SERVER_IP"] = "0.0.0.0"
    os.environ.setdefault("FLET_SERVER_PORT", os.getenv("PORTA_ALUNO", "8081"))
    sys.path.insert(0, str(_MEIPASS))
    from aluno.main import run_app
    run_app()
    sys.exit(0)

import subprocess
import threading
import time

ROOT = Path(sys.executable).parent if _FROZEN else Path(__file__).parent
PYTHON = sys.executable
_SEM_JANELA = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0


def _matar_flet_clientes() -> None:
    if os.name != "nt":
        return
    try:
        subprocess.call(
            ["taskkill", "/F", "/IM", "flet.exe"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=_SEM_JANELA,
        )
    except Exception:
        pass


def _matar(proc) -> None:
    if os.name != "nt":
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
        return
    try:
        subprocess.call(
            ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=_SEM_JANELA,
        )
    except Exception:
        pass


def _matar_porta(porta: int) -> None:
    if os.name != "nt":
        return
    try:
        saida = subprocess.check_output(
            ["netstat", "-ano", "-p", "tcp"],
            text=True,
            stderr=subprocess.DEVNULL,
            creationflags=_SEM_JANELA,
        )
    except Exception:
        return
    for linha in saida.splitlines():
        partes = linha.split()
        if len(partes) >= 5 and partes[1].endswith(f":{porta}") and partes[3] == "LISTENING":
            try:
                subprocess.call(
                    ["taskkill", "/F", "/T", "/PID", partes[-1]],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=_SEM_JANELA,
                )
            except Exception:
                pass


_GITHUB_REPO = "JackMatiazzi/Faccupoint"
_GITHUB_API_LATEST = f"https://api.github.com/repos/{_GITHUB_REPO}/releases/latest"
_GITHUB_SETUP = "FaccuPoint-Setup.exe"
_GITHUB_SETUP_SHA256 = f"{_GITHUB_SETUP}.sha256"


def _versao_local() -> str:
    import json

    nome_manifesto = ".release-please-manifest.json"
    for version_file in (_MEIPASS / nome_manifesto, ROOT / nome_manifesto):
        try:
            manifesto = json.loads(version_file.read_text(encoding="utf-8"))
            return str(manifesto["."])
        except (OSError, KeyError, TypeError, ValueError):
            continue
    return "0.0.0"


def _chave_versao(valor: str) -> tuple[int, int, int, int, str] | None:
    import re

    correspondencia = re.fullmatch(
        r"v?(\d+)\.(\d+)\.(\d+)(?:[-.]([0-9A-Za-z.-]+))?",
        valor.strip(),
    )
    if correspondencia is None:
        return None
    principal = tuple(int(item) for item in correspondencia.group(1, 2, 3))
    pre_release = correspondencia.group(4)
    return (*principal, 1 if pre_release is None else 0, pre_release or "")


def _versao_mais_nova(remota: str, local: str) -> bool:
    chave_remota = _chave_versao(remota)
    chave_local = _chave_versao(local)
    return chave_remota is not None and chave_local is not None and chave_remota > chave_local


def _buscar_atualizacao() -> dict | None:
    import json
    import urllib.request

    requisicao = urllib.request.Request(
        _GITHUB_API_LATEST,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"FaccuPoint/{_versao_local()}",
        },
    )
    with urllib.request.urlopen(requisicao, timeout=10) as resposta:
        release = json.load(resposta)

    versao = str(release.get("tag_name", "")).removeprefix("v")
    if not _versao_mais_nova(versao, _versao_local()):
        return None

    assets = {
        str(asset.get("name")): str(asset.get("browser_download_url"))
        for asset in release.get("assets", [])
    }
    setup_url = assets.get(_GITHUB_SETUP)
    sha256_url = assets.get(_GITHUB_SETUP_SHA256)
    if not setup_url or not sha256_url:
        raise RuntimeError("release sem instalador ou SHA-256")
    return {"versao": versao, "setup_url": setup_url, "sha256_url": sha256_url}


def _confirmar_atualizacao(versao: str) -> bool:
    import ctypes

    resposta = ctypes.windll.user32.MessageBoxW(
        None,
        f"A versao {versao} do FaccuPoint esta disponivel.\n\nDeseja atualizar agora?",
        "Atualizacao do FaccuPoint",
        0x00000004 | 0x00000040,
    )
    return resposta == 6


def _baixar_e_iniciar_atualizacao(atualizacao: dict) -> bool:
    import hashlib
    import re
    import tempfile
    import urllib.request

    pasta = Path(tempfile.gettempdir()) / "FaccuPoint" / "updates"
    pasta.mkdir(parents=True, exist_ok=True)
    setup = pasta / f"FaccuPoint-Setup-{atualizacao['versao']}.exe"
    download = setup.with_suffix(".download")

    urllib.request.urlretrieve(atualizacao["setup_url"], download)
    with urllib.request.urlopen(atualizacao["sha256_url"], timeout=10) as resposta:
        sha_esperado = resposta.read().decode("utf-8").split()[0].strip().lower()
    if re.fullmatch(r"[0-9a-f]{64}", sha_esperado) is None:
        raise RuntimeError("arquivo SHA-256 invalido")

    sha_calculado = hashlib.sha256()
    with download.open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1024 * 1024), b""):
            sha_calculado.update(bloco)
    if sha_calculado.hexdigest().lower() != sha_esperado:
        download.unlink(missing_ok=True)
        raise RuntimeError("SHA-256 do instalador nao confere")

    download.replace(setup)
    subprocess.Popen(
        [
            str(setup),
            "/VERYSILENT",
            "/SUPPRESSMSGBOXES",
            "/NORESTART",
            "/CLOSEAPPLICATIONS",
        ],
        creationflags=_SEM_JANELA,
    )
    return True


def _verificar_atualizacao() -> bool:
    if not _FROZEN or os.name != "nt":
        return False
    try:
        atualizacao = _buscar_atualizacao()
        if atualizacao is None or not _confirmar_atualizacao(atualizacao["versao"]):
            return False
        return _baixar_e_iniciar_atualizacao(atualizacao)
    except Exception as e:
        print(f"falha ao verificar atualizacao ({e}), continuando com versao atual")
        return False


def _aguardar_backend(api_url: str, remoto: bool) -> None:
    import urllib.request
    import urllib.error

    health = api_url.rstrip("/") + "/health"
    tentativas = 15 if remoto else 8
    intervalo = 6 if remoto else 2

    for i in range(1, tentativas + 1):
        try:
            urllib.request.urlopen(health, timeout=8)
            if i > 1:
                print("servidor pronto")
            return
        except Exception:
            if remoto and i == 1:
                print("aguardando servidor iniciar (pode levar ate 1 min)...")
            elif not remoto and i == 1:
                print("aguardando backend local...")
            time.sleep(intervalo)

    print("aviso: servidor nao respondeu, abrindo mesmo assim")


def _iniciar_keepalive(api_url: str, parar: threading.Event) -> None:
    import urllib.request

    health = api_url.rstrip("/") + "/health"

    def _loop():
        while not parar.wait(timeout=600):
            try:
                urllib.request.urlopen(health, timeout=8)
            except Exception:
                pass

    t = threading.Thread(target=_loop, daemon=True)
    t.start()


def _testar_pacote() -> None:
    import base64

    sys.path.insert(0, str(_MEIPASS))
    import psutil
    from aluno.main import main as aluno_main
    from professor.main import main as professor_main
    from professor.telas.sessao_professor import _gerar_qrcode_b64

    png = base64.b64decode(_gerar_qrcode_b64("http://127.0.0.1:8081?codigo=TESTE"))
    if not png.startswith(b"\x89PNG\r\n\x1a\n"):
        raise RuntimeError("falha ao gerar QR Code no pacote")
    if not callable(aluno_main) or not callable(professor_main) or not psutil.net_if_addrs():
        raise RuntimeError("modulos essenciais indisponiveis no pacote")
    if _versao_local() == "0.0.0":
        raise RuntimeError("arquivo de versao ausente do pacote")


def main() -> None:
    if "--smoke-test-package" in sys.argv:
        _testar_pacote()
        return

    _matar_flet_clientes()
    print("abrindo o faccupoint")
    api_url = os.getenv("API_URL", "https://faccupoint-backend.onrender.com")
    backend_remoto = not ("127.0.0.1" in api_url or "localhost" in api_url)

    if _verificar_atualizacao():
        return

    porta_aluno = int(os.getenv("PORTA_ALUNO", "8081"))
    _matar_porta(porta_aluno)
    if not backend_remoto:
        _matar_porta(int(os.getenv("API_PORT", "8000")))

    procs = []

    if _FROZEN:
        if not backend_remoto:
            procs.append(
                subprocess.Popen(
                    [PYTHON, "--run-backend"],
                    creationflags=_SEM_JANELA,
                )
            )
        procs.append(
            subprocess.Popen(
                [PYTHON, "--run-aluno"],
                creationflags=_SEM_JANELA,
            )
        )
    else:
        if not backend_remoto:
            procs.append(
                subprocess.Popen(
                    [PYTHON, "-m", "backend.main"],
                    cwd=ROOT,
                    creationflags=_SEM_JANELA,
                )
            )
        env_aluno = {
            **os.environ,
            "PYTHONPATH": str(ROOT / "frontend"),
            "FLET_SERVER_IP": "0.0.0.0",
            "FLET_SERVER_PORT": str(porta_aluno),
        }
        procs.append(
            subprocess.Popen(
                [PYTHON, "-m", "aluno.main"],
                cwd=ROOT / "frontend",
                env=env_aluno,
                creationflags=_SEM_JANELA,
            )
        )

    _aguardar_backend(api_url, backend_remoto)

    parar_keepalive = threading.Event()
    if backend_remoto:
        _iniciar_keepalive(api_url, parar_keepalive)

    os.environ["API_URL"] = api_url

    if not _FROZEN:
        os.chdir(str(ROOT / "frontend"))
        sys.path.insert(0, str(ROOT / "frontend"))

    import flet as ft
    from professor.main import main as professor_main

    print("faccupoint aberto")
    try:
        ft.app(target=professor_main, view=ft.AppView.FLET_APP)
    except KeyboardInterrupt:
        pass
    finally:
        parar_keepalive.set()
        print("fechando o faccupoint")
        for p in procs:
            _matar(p)
        _matar_porta(porta_aluno)
        print("fechado")


if __name__ == "__main__":
    main()
