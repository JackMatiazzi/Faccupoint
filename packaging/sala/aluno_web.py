import flet.fastapi
from aluno.main import main
from backend.infraestrutura.limites import LimitesMiddleware

app = LimitesMiddleware(flet.fastapi.app(main, session_timeout_seconds=300))
