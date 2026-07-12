import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import launcher


class AtualizacaoTest(unittest.TestCase):
    def test_compara_versoes_sem_fazer_downgrade(self):
        self.assertTrue(launcher._versao_mais_nova("1.0.1", "1.0.0"))
        self.assertTrue(launcher._versao_mais_nova("v2.0.0", "1.9.9"))
        self.assertFalse(launcher._versao_mais_nova("1.0.0", "1.0.0"))
        self.assertFalse(launcher._versao_mais_nova("1.0.0", "1.0.1"))
        self.assertFalse(launcher._versao_mais_nova("invalida", "1.0.0"))

    def test_encontra_setup_e_hash_na_release(self):
        release = {
            "tag_name": "v1.0.1",
            "assets": [
                {"name": "FaccuPoint-Setup.exe", "browser_download_url": "https://example/setup"},
                {"name": "FaccuPoint-Setup.exe.sha256", "browser_download_url": "https://example/sha"},
            ],
        }
        resposta = io.BytesIO(json.dumps(release).encode("utf-8"))

        with patch.object(launcher, "_versao_local", return_value="1.0.0"), patch(
            "urllib.request.urlopen", return_value=resposta
        ):
            atualizacao = launcher._buscar_atualizacao()

        self.assertEqual(atualizacao["versao"], "1.0.1")
        self.assertEqual(atualizacao["setup_url"], "https://example/setup")
        self.assertEqual(atualizacao["sha256_url"], "https://example/sha")

    def test_valida_hash_antes_de_iniciar_instalador(self):
        conteudo = b"instalador de teste"
        sha256 = hashlib.sha256(conteudo).hexdigest()
        atualizacao = {
            "versao": "1.0.1",
            "setup_url": "https://example/setup",
            "sha256_url": "https://example/sha",
        }

        def baixar(_url, destino):
            Path(destino).write_bytes(conteudo)

        with tempfile.TemporaryDirectory() as pasta, patch(
            "tempfile.gettempdir", return_value=pasta
        ), patch("urllib.request.urlretrieve", side_effect=baixar), patch(
            "urllib.request.urlopen", return_value=io.BytesIO(f"{sha256}  FaccuPoint-Setup.exe".encode())
        ), patch.object(launcher.subprocess, "Popen") as iniciar:
            resultado = launcher._baixar_e_iniciar_atualizacao(atualizacao)

        self.assertTrue(resultado)
        argumentos = iniciar.call_args.args[0]
        self.assertTrue(argumentos[0].endswith("FaccuPoint-Setup-1.0.1.exe"))
        self.assertIn("/VERYSILENT", argumentos)

    def test_recusa_instalador_com_hash_diferente(self):
        atualizacao = {
            "versao": "1.0.1",
            "setup_url": "https://example/setup",
            "sha256_url": "https://example/sha",
        }

        def baixar(_url, destino):
            Path(destino).write_bytes(b"arquivo adulterado")

        with tempfile.TemporaryDirectory() as pasta, patch(
            "tempfile.gettempdir", return_value=pasta
        ), patch("urllib.request.urlretrieve", side_effect=baixar), patch(
            "urllib.request.urlopen", return_value=io.BytesIO(("0" * 64).encode())
        ), patch.object(launcher.subprocess, "Popen") as iniciar:
            with self.assertRaisesRegex(RuntimeError, "SHA-256"):
                launcher._baixar_e_iniciar_atualizacao(atualizacao)

        iniciar.assert_not_called()


if __name__ == "__main__":
    unittest.main()
