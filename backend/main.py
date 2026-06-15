import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from backend.adaptadores.entrada.http.rotas import router
from backend.adaptadores.entrada.tempo_real.rotas import router as router_sessao
from backend.adaptadores.saida.postgres.repositorio import migrar_schema
from backend.infraestrutura.configuracao import load_environment

load_environment()

logging.basicConfig(
    level=getattr(logging, os.getenv("API_LOG_LEVEL", "warning").upper(), logging.WARNING),
    format="%(levelname)s  %(name)s  %(message)s",
)


def _cors_origins() -> list[str]:
    valor = os.getenv("CORS_ORIGINS", "http://127.0.0.1:8000,http://localhost:8000")
    return [origem.strip() for origem in valor.split(",") if origem.strip()]


def create_app(*, run_migrations: bool = True) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_: FastAPI):
        if run_migrations:
            await asyncio.to_thread(migrar_schema)
        yield

    desabilitar_docs = os.getenv("DISABLE_DOCS", "0") == "1"
    application = FastAPI(
        title="Faccupoint API",
        version="0.1.0",
        docs_url=None if desabilitar_docs else "/docs",
        redoc_url=None if desabilitar_docs else "/redoc",
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(),
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @application.middleware("http")
    async def security_headers(request: Request, call_next) -> Response:
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response

    application.include_router(router)
    application.include_router(router_sessao)

    @application.get("/health", tags=["status"])
    def status():
        return {"status": "ok"}

    @application.get("/versao", tags=["status"])
    def versao():
        return {"versao": os.getenv("APP_VERSION", "1.0.0")}

    return application


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=os.getenv("API_RELOAD", "0") == "1",
        log_level=os.getenv("API_LOG_LEVEL", "warning"),
        access_log=False,
    )
