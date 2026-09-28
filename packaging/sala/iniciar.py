import os
from pathlib import Path

import uvicorn

if __name__ == "__main__":
    senha = Path("/run/secrets/db_password").read_text().strip()
    os.environ["DATABASE_URL"] = f"postgresql://faccupoint:{senha}@db:5432/faccupoint"
    os.environ["SECRET_KEY"] = Path("/run/secrets/token_key").read_text().strip()
    from backend.adaptadores.saida.postgres.repositorio import (
        buscar_docente_por_email, cadastrar_docente, cadastrar_quiz, cadastrar_pergunta,
    )
    email = "professor@teste.invalid"
    if buscar_docente_por_email(email) is None:
        pin = Path("/run/secrets/admin_pin").read_text().strip()
        cadastrar_docente("Professor de teste", email, pin, "adm", precisa_trocar_pin=True)
        docente = buscar_docente_por_email(email)
        quiz = cadastrar_quiz(docente[0], "Quiz de teste isolado", "Somente dados ficticios", 30)
        cadastrar_pergunta(quiz, "Quanto e 2 + 2?", [
            {"texto": "3", "correta": False}, {"texto": "4", "correta": True},
        ])
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, workers=1,
                proxy_headers=False, ws_max_size=16384, ws_max_queue=16,
                limit_concurrency=512, timeout_keep_alive=5)
