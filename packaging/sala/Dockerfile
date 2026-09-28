FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app:/app/frontend
WORKDIR /app
COPY backend/requirements.txt /tmp/backend-requirements.txt
RUN pip install --no-cache-dir -r /tmp/backend-requirements.txt flet==0.28.3 flet-web==0.28.3 requests qrcode Pillow truststore psutil
COPY backend /app/backend
COPY frontend /app/frontend
COPY packaging/sala /app/packaging/sala
RUN useradd --uid 10001 --create-home app
USER 10001
CMD ["python", "/app/packaging/sala/iniciar.py"]
