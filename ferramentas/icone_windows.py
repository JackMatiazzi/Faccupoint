from pathlib import Path
import shutil
import struct

import win32api


RT_ICON = 3
RT_GROUP_ICON = 14


def criar_executavel_com_icone(
    executavel_origem: Path,
    arquivo_ico: Path,
    executavel_destino: Path,
) -> Path:
    executavel_destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(executavel_origem, executavel_destino)

    dados_ico = arquivo_ico.read_bytes()
    reservado, tipo, quantidade = struct.unpack_from("<HHH", dados_ico, 0)
    if reservado != 0 or tipo != 1 or quantidade < 1:
        raise ValueError(f"arquivo ICO invalido: {arquivo_ico}")

    entradas = []
    for indice in range(quantidade):
        base = 6 + indice * 16
        (
            largura,
            altura,
            cores,
            reservado_entrada,
            planos,
            bits,
            tamanho,
            deslocamento,
        ) = struct.unpack_from("<BBBBHHII", dados_ico, base)
        imagem = dados_ico[deslocamento:deslocamento + tamanho]
        entradas.append(
            (
                largura,
                altura,
                cores,
                reservado_entrada,
                planos,
                bits,
                tamanho,
                imagem,
            )
        )

    atualizacao = win32api.BeginUpdateResource(str(executavel_destino), False)
    try:
        grupo = bytearray(struct.pack("<HHH", 0, 1, len(entradas)))
        for id_icone, entrada in enumerate(entradas, start=1):
            largura, altura, cores, reservado_entrada, planos, bits, tamanho, imagem = entrada
            win32api.UpdateResource(
                atualizacao,
                RT_ICON,
                id_icone,
                imagem,
                0,
            )
            grupo.extend(
                struct.pack(
                    "<BBBBHHIH",
                    largura,
                    altura,
                    cores,
                    reservado_entrada,
                    planos,
                    bits,
                    tamanho,
                    id_icone,
                )
            )

        win32api.UpdateResource(
            atualizacao,
            RT_GROUP_ICON,
            101,
            bytes(grupo),
            0,
        )
    except Exception:
        win32api.EndUpdateResource(atualizacao, True)
        raise
    else:
        win32api.EndUpdateResource(atualizacao, False)

    return executavel_destino
