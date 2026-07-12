
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
_GITHUB_ASSET = "FaccuPoint.zip"


def _versao_local() -> str:
    for version_file in (_MEIPASS / "VERSION", ROOT / "VERSION"):
        try:
            return version_file.read_text(encoding="utf-8").strip()
        except OSError:
            continue
    return "0.0.0"


def _verificar_atualizacao(api_url: str) -> None:
    if _FROZEN:
        return

    import hashlib
    import urllib.request
    import urllib.error
    import json
    import zipfile
    import tempfile
    import shutil

    try:
        resp = urllib.request.urlopen(api_url.rstrip("/") + "/versao", timeout=8)
        dados = json.loads(resp.read())
        versao_remota = dados.get("versao", "")
    except Exception:
        return

    versao_local = _versao_local()
    if versao_remota == versao_local or not versao_remota:
        return

    print(f"atualizacao disponivel: {versao_local} → {versao_remota}")
    print("baixando atualizacao...")

    base_release = (
        f"https://github.com/{_GITHUB_REPO}/releases/download/v{versao_remota}"
    )
    url_zip = f"{base_release}/{_GITHUB_ASSET}"
    url_sha = f"{base_release}/{_GITHUB_ASSET}.sha256"

    try:
        with tempfile.TemporaryDirectory() as tmp:
            zip_path = os.path.join(tmp, _GITHUB_ASSET)
            urllib.request.urlretrieve(url_zip, zip_path)

            try:
                sha_resp = urllib.request.urlopen(url_sha, timeout=8)
                sha_esperado = sha_resp.read().decode().split()[0].strip().lower()
            except Exception:
                print("aviso: arquivo .sha256 nao encontrado no release — atualizacao cancelada por seguranca")
                return

            sha_calculado = hashlib.sha256(open(zip_path, "rb").read()).hexdigest().lower()
            if sha_calculado != sha_esperado:
                print("erro: SHA-256 do pacote nao confere — atualizacao cancelada")
                return

            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(tmp)

            extraido = os.path.join(tmp, "FaccuPoint")
            origem = extraido if os.path.isdir(extraido) else tmp

            for item in os.listdir(origem):
                src = os.path.join(origem, item)
                dst = str(ROOT / item)
                if os.path.isdir(src):
                    if os.path.exists(dst):
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)

        print(f"atualizado para {versao_remota}, reiniciando...")
        subprocess.Popen(
            [sys.executable, str(ROOT / "launcher.py")],
            creationflags=_SEM_JANELA,
        )
        sys.exit(0)
    except Exception as e:
        print(f"falha na atualizacao ({e}), continuando com versao atual")


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

    if backend_remoto:
        _verificar_atualizacao(api_url)

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
