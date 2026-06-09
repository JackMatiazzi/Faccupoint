import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.banco import migrar_schema
from backend.rotas import router
from backend.rotas_sessao import router as router_sessao

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

logging.basicConfig(
    level=getattr(logging, os.getenv("API_LOG_LEVEL", "warning").upper(), logging.WARNING),
    format="%(levelname)s  %(name)s  %(message)s",
)


def _cors_origins() -> list[str]:
    valor = os.getenv("CORS_ORIGINS", "http://127.0.0.1:8000,http://localhost:8000")
    return [origem.strip() for origem in valor.split(",") if origem.strip()]


migrar_schema()

app = FastAPI(title="Faccupoint API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(router)
app.include_router(router_sessao)


@app.get("/health", tags=["status"])
def status():
    return {"status": "ok"}


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
