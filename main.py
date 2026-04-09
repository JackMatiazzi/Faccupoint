import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent
_SRC = _REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from app.main import run_app

if __name__ == "__main__":
    run_app()
