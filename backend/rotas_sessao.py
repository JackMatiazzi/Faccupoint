from __future__ import annotations

import asyncio
import json
import logging
import os

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from backend.email_relatorio import enviar_relatorio_sessao
from backend.banco import (
    atualizar_pergunta_atual_sessao,
    buscar_docente_do_quiz,
    buscar_tempo_quiz,
    listar_perguntas_do_quiz,
    registrar_participante_sessao,
    registrar_sessao,
    registrar_tentativa,
)
from backend.rotas import docente_atual
from backend.sessao import Participante, criar_sessao, gerar_codigo_sessao, obter_sessao

load_dotenv()
router = APIRouter()
logger = logging.getLogger(__name__)

TEMPO_QUESTAO = int(os.getenv("TEMPO_QUESTAO_SEGUNDOS", "30"))


class CriarSessaoEntrada(BaseModel):
    id_quiz: int
    id_docente_anfitriao: int | None = None


async def _broadcast_alunos(sessao, mensagem: dict) -> None:
    mortos = []
    for apelido, p in sessao.participantes.items():
        try:
            await p.ws.send_json(mensagem)
        except WebSocketDisconnect:
            logger.info("aluno %s desconectou", apelido)
            mortos.append(apelido)
        except Exception:
            logger.exception("falha ao enviar mensagem para aluno %s", apelido)
            mortos.append(apelido)
    for a in mortos:
        sessao.participantes.pop(a, None)


async def _enviar_professor(sessao, mensagem: dict) -> None:
    if sessao.professor_ws:
        try:
            await sessao.professor_ws.send_json(mensagem)
        except WebSocketDisconnect:
            logger.info("professor desconectou da sala %s", sessao.codigo)
            sessao.professor_ws = None
        except Exception:
            logger.exception("falha ao enviar mensagem para o professor da sala %s", sessao.codigo)
            sessao.professor_ws = None


async def _rodar_questao(codigo: str) -> None:
    sessao = obter_sessao(codigo)
    if not sessao:
        return

    pergunta = sessao.pergunta_atual()
    if not pergunta:
        return
    atualizar_pergunta_atual_sessao(sessao.id_sessao, sessao.questao_atual)
    logger.info(
        "sala %s rodando questao %s de %s",
        codigo,
        sessao.questao_atual + 1,
        len(sessao.perguntas),
    )

    for p in sessao.participantes.values():
        p.resposta_atual = None

    tempo = sessao.tempo_questao
    msg_questao = {
        "tipo": "questao",
        "numero": sessao.questao_atual + 1,
        "total": len(sessao.perguntas),
        "enunciado": pergunta["enunciado"],
        "alternativas": [a["texto"] for a in pergunta["alternativas"]],
        "tempo": tempo,
    }
    await _broadcast_alunos(sessao, msg_questao)
    await _enviar_professor(sessao, {**msg_questao, "tipo": "questao_professor"})

    for _ in range(tempo):
        await asyncio.sleep(1)
        sessao = obter_sessao(codigo)
        if not sessao or sessao.status != "rodando":
            return
        if sessao.todos_responderam():
            break

    await _revelar_resultado(codigo)


async def _revelar_resultado(codigo: str) -> None:
    sessao = obter_sessao(codigo)
    if not sessao:
        return

    pergunta = sessao.pergunta_atual()
    if not pergunta:
        return

    indices_corretos = [
        i for i, a in enumerate(pergunta["alternativas"]) if a["correta"]
    ]

    for p in sessao.participantes.values():
        acertou = p.resposta_atual in indices_corretos
        if acertou:
            p.pontos += 1

    contagem = sessao.contagem_respostas()
    placar = [{"apelido": p.apelido, "pontos": p.pontos} for p in sorted(sessao.participantes.values(), key=lambda x: -x.pontos)]
    resultado = {
        "tipo": "resultado",
        "indice_correto": indices_corretos[0] if indices_corretos else 0,
        "indices_corretos": indices_corretos,
        "contagem": contagem,
        "placar": placar,
    }
    mortos = []
    for p in sessao.participantes.values():
        try:
            await p.ws.send_json({
                **resultado,
                "sua_resposta": p.resposta_atual,
                "acertou": p.resposta_atual in indices_corretos,
                "pontos": p.pontos,
            })
        except WebSocketDisconnect:
            logger.info("aluno %s desconectou antes de receber o resultado", p.apelido)
            mortos.append(p.apelido)
        except Exception:
            logger.exception("falha ao enviar resultado para aluno %s", p.apelido)
            mortos.append(p.apelido)
    for apelido in mortos:
        sessao.participantes.pop(apelido, None)
    await _enviar_professor(sessao, {
        **resultado,
        "tipo": "resultado_professor",
    })

    e_ultima = sessao.questao_atual >= len(sessao.perguntas) - 1
    if e_ultima:
        await asyncio.sleep(3)
        await _encerrar(codigo)
    else:
        questao_antes = sessao.questao_atual
        await asyncio.sleep(2)
        sessao = obter_sessao(codigo)
        if sessao and sessao.questao_atual == questao_antes and sessao.status == "rodando":
            sessao.questao_atual += 1
            await _rodar_questao(codigo)


async def _encerrar(codigo: str) -> None:
    sessao = obter_sessao(codigo)
    if not sessao:
        return
    sessao.status = "encerrada"
    logger.info("sala %s encerrada", codigo)
    placar = [{"apelido": p.apelido, "pontos": p.pontos} for p in sorted(sessao.participantes.values(), key=lambda x: -x.pontos)]
    await _broadcast_alunos(sessao, {"tipo": "fim", "placar": placar})
    await _enviar_professor(sessao, {"tipo": "fim", "placar": placar})
    asyncio.create_task(asyncio.to_thread(enviar_relatorio_sessao, sessao.id_sessao))


@router.post("/sessoes", tags=["sessao"])
async def criar(corpo: CriarSessaoEntrada, atual: dict = Depends(docente_atual)):
    perguntas = listar_perguntas_do_quiz(corpo.id_quiz)
    if not perguntas:
        raise HTTPException(status_code=400, detail="quiz sem perguntas")
    id_docente_proprietario = buscar_docente_do_quiz(corpo.id_quiz)
    if id_docente_proprietario is None:
        raise HTTPException(status_code=400, detail="quiz nao encontrado")
    if (
        corpo.id_docente_anfitriao is not None
        and corpo.id_docente_anfitriao != id_docente_proprietario
    ):
        raise HTTPException(status_code=403, detail="sem permissao")
    if int(atual["id_docente"]) != id_docente_proprietario:
        raise HTTPException(status_code=403, detail="sem permissao")
    tempo = buscar_tempo_quiz(corpo.id_quiz) or TEMPO_QUESTAO
    codigo = gerar_codigo_sessao()
    id_sessao = registrar_sessao(codigo, corpo.id_quiz, id_docente_proprietario)
    criar_sessao(codigo, id_sessao, id_docente_proprietario, corpo.id_quiz, perguntas, tempo)
    logger.info("sala %s aberta para quiz %s com %s pergunta(s)", codigo, corpo.id_quiz, len(perguntas))
    return {"codigo": codigo}


@router.post("/sessoes/{codigo}/iniciar", tags=["sessao"])
async def iniciar(codigo: str, atual: dict = Depends(docente_atual)):
    sessao = obter_sessao(codigo)
    if not sessao:
        raise HTTPException(status_code=404, detail="sala nao encontrada")
    if int(atual["id_docente"]) != sessao.id_docente:
        raise HTTPException(status_code=403, detail="sem permissao")
    if sessao.status != "lobby":
        raise HTTPException(status_code=400, detail="sala ja iniciada")
    if not sessao.participantes:
        raise HTTPException(status_code=400, detail="nenhum aluno na sala")
    sessao.status = "rodando"
    sessao.questao_atual = 0
    logger.info("sala %s comecou", codigo)
    asyncio.create_task(_rodar_questao(codigo))
    return {"ok": True}


@router.post("/sessoes/{codigo}/proxima", tags=["sessao"])
async def proxima(codigo: str, atual: dict = Depends(docente_atual)):
    sessao = obter_sessao(codigo)
    if not sessao or sessao.status != "rodando":
        raise HTTPException(status_code=400, detail="sala invalida")
    if int(atual["id_docente"]) != sessao.id_docente:
        raise HTTPException(status_code=403, detail="sem permissao")
    sessao.questao_atual += 1
    if sessao.questao_atual >= len(sessao.perguntas):
        await _encerrar(codigo)
        return {"fim": True}
    asyncio.create_task(_rodar_questao(codigo))
    return {"fim": False}


@router.get("/sessoes/{codigo}", tags=["sessao"])
def info(codigo: str):
    sessao = obter_sessao(codigo)
    if not sessao:
        raise HTTPException(status_code=404, detail="sessao nao encontrada")
    return {
        "codigo": codigo,
        "status": sessao.status,
        "participantes": list(sessao.participantes.keys()),
        "total_perguntas": len(sessao.perguntas),
    }


@router.websocket("/ws/professor/{codigo}")
async def ws_professor(ws: WebSocket, codigo: str):
    sessao = obter_sessao(codigo)
    if not sessao:
        await ws.close(code=4004)
        return
    await ws.accept()
    sessao.professor_ws = ws
    await ws.send_json({"tipo": "conectado", "codigo": codigo})
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        if sessao.professor_ws is ws:
            sessao.professor_ws = None


@router.websocket("/ws/aluno/{codigo}")
async def ws_aluno(ws: WebSocket, codigo: str):
    sessao = obter_sessao(codigo)
    if not sessao:
        await ws.close(code=4004)
        return
    await ws.accept()
    apelido = None
    try:
        dados = json.loads(await ws.receive_text())
        apelido = dados.get("apelido", "").strip()[:20]
        if not apelido or apelido in sessao.participantes:
            await ws.send_json({"tipo": "erro", "mensagem": "apelido invalido ou ja em uso"})
            await ws.close()
            return

        id_participante = registrar_participante_sessao(sessao.id_sessao, apelido)
        sessao.participantes[apelido] = Participante(apelido=apelido, ws=ws, id_participante=id_participante)
        logger.info("sala %s: %s entrou", codigo, apelido)
        lista = list(sessao.participantes.keys())
        await _broadcast_alunos(sessao, {"tipo": "lobby", "participantes": lista})
        await _enviar_professor(sessao, {"tipo": "lobby", "participantes": lista})

        while True:
            texto = await ws.receive_text()
            dados = json.loads(texto)
            if dados.get("tipo") == "resposta" and sessao.status == "rodando":
                p = sessao.participantes.get(apelido)
                if p and p.resposta_atual is None:
                    indice = int(dados["indice"])
                    pergunta = sessao.pergunta_atual()
                    alternativas = pergunta["alternativas"] if pergunta else []
                    alternativa = alternativas[indice] if 0 <= indice < len(alternativas) else None
                    acertou = bool(alternativa and alternativa["correta"])
                    p.resposta_atual = indice
                    if p.id_participante is not None and pergunta:
                        registrar_tentativa(
                            p.id_participante,
                            pergunta["id_pergunta"],
                            alternativa["id"] if alternativa else None,
                            acertou,
                        )
                        logger.debug("sala %s: resposta de %s salva", codigo, apelido)
                    await _enviar_professor(sessao, {
                        "tipo": "responderam",
                        "total": sessao.total_participantes(),
                        "respondidos": sum(1 for x in sessao.participantes.values() if x.resposta_atual is not None),
                    })

    except WebSocketDisconnect:
        pass
    finally:
        if apelido and apelido in sessao.participantes:
            sessao.participantes.pop(apelido)
            lista = list(sessao.participantes.keys())
            await _broadcast_alunos(sessao, {"tipo": "lobby", "participantes": lista})
            await _enviar_professor(sessao, {"tipo": "lobby", "participantes": lista})
