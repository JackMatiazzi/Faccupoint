import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]


def load_environment() -> None:
    load_dotenv(dotenv_path=BACKEND_DIR / ".env")


def database_url() -> str:
    value = os.environ.get("DATABASE_URL")
    if not value:
        raise RuntimeError("DATABASE_URL nao definida no .env")
    return value
