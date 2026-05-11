from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent.parent


def db_path() -> Path:
    return project_root() / "data" / "faccupoint.db"
