import socket
import sys
import unittest
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import urlopen
from websockets.sync.client import connect
from websockets.exceptions import InvalidStatus

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "frontend"))
from professor.janela import servidor_professor


class JanelaProfessorTest(unittest.TestCase):
    def test_servidor_local_serve_interface_e_fecha_porta_ao_sair(self):
        with servidor_professor(lambda page: None) as url:
            destino = urlsplit(url)
            self.assertEqual(destino.hostname, "127.0.0.1")
            with urlopen(url, timeout=5) as response:
                self.assertEqual(response.status, 200)
                self.assertIn(b"flutter", response.read().lower())
            with self.assertRaises(InvalidStatus) as rejeitado:
                with connect(url.replace("http:", "ws:") + "/ws", origin="https://outro.example"):
                    pass
            self.assertEqual(rejeitado.exception.response.status_code, 403)
        with socket.socket() as client:
            client.settimeout(1)
            self.assertNotEqual(client.connect_ex((destino.hostname, destino.port)), 0)
