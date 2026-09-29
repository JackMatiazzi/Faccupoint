"""Janela Windows com suporte a vídeos incorporados (WebView2)."""

import socket
import sys
import threading
import time
from contextlib import contextmanager
from pathlib import Path

import flet as ft


@contextmanager
def servidor_professor(target):
    import flet.fastapi
    import uvicorn

    # Socket reservado evita disputa de porta; a interface fica apenas no computador.
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        porta = sock.getsockname()[1]
        app = flet.fastapi.app(
            target,
            assets_dir=str(Path(__file__).resolve().parents[1] / "assets"),
        )
        url = f"http://127.0.0.1:{porta}"

        async def interface_local(scope, receive, send):
            if scope["type"] == "websocket":
                origem = dict(scope.get("headers", [])).get(b"origin", b"")
                if origem != url.encode("ascii"):
                    await send({"type": "websocket.close", "code": 1008})
                    return
            await app(scope, receive, send)

        server = uvicorn.Server(uvicorn.Config(
            interface_local, log_config=None, access_log=False, timeout_graceful_shutdown=3,
        ))
        thread = threading.Thread(
            target=server.run, kwargs={"sockets": [sock]}, daemon=True,
            name="faccupoint-professor",
        )
        thread.start()
        try:
            limite = time.monotonic() + 30
            while not server.started:
                if not thread.is_alive() or time.monotonic() >= limite:
                    raise RuntimeError("Não foi possível iniciar a janela do professor.")
                time.sleep(0.05)
            yield url
        finally:
            server.should_exit = True
            thread.join(timeout=5)


def abrir_janela(target):
    if sys.platform != "win32":
        ft.app(target=target, view=ft.AppView.FLET_APP)
        return

    import webview

    with servidor_professor(target) as url:
        webview.create_window(
            "FaccuPoint", url, width=1280, height=800,
            min_size=(900, 600), background_color="#101116",
        )
        webview.start(gui="edgechromium")
