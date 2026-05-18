from __future__ import annotations

import subprocess
import sys
import time
import os
from pathlib import Path

ROOT = Path(__file__).parent
PYTHON = sys.executable


def _iniciar(args: list[str], cwd: Path) -> subprocess.Popen:
    return subprocess.Popen([PYTHON] + args, cwd=cwd)


def _matar(proc: subprocess.Popen) -> None:
    try:
        subprocess.call(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (Exception, KeyboardInterrupt):
        pass


def _matar_porta(porta: int) -> None:
    try:
        saida = subprocess.check_output(
            ["netstat", "-ano", "-p", "tcp"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return

    pids: set[str] = set()
    alvo = f":{porta}"
    for linha in saida.splitlines():
        partes = linha.split()
        if len(partes) < 5:
            continue
        endereco_local = partes[1]
        estado = partes[3]
        pid = partes[-1]
        if endereco_local.endswith(alvo) and estado == "LISTENING":
            pids.add(pid)

    for pid in pids:
        try:
            subprocess.call(
                ["taskkill", "/F", "/T", "/PID", pid],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except (Exception, KeyboardInterrupt):
            pass


def main() -> None:
    print("abrindo o faccupoint")
    porta_aluno = int(os.getenv("PORTA_ALUNO", "8081"))
    _matar_porta(porta_aluno)

    backend = _iniciar(["-m", "backend.main"], ROOT)
    aluno = subprocess.Popen(
        [PYTHON, "-m", "app.main"],
        cwd=ROOT / "frontend" / "aluno",
    )
    time.sleep(2)

    professor = subprocess.Popen(
        [PYTHON, "-m", "app.main"],
        cwd=ROOT / "frontend",
    )
    print("faccupoint aberto")
    try:
        professor.wait()
    except KeyboardInterrupt:
        pass
    finally:
        print("fechando o faccupoint")
        try:
            _matar(professor)
            _matar(aluno)
            _matar(backend)
            _matar_porta(porta_aluno)
        except KeyboardInterrupt:
            pass
        print("fechado")


if __name__ == "__main__":
    main()
