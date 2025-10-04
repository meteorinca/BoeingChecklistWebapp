# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1

WORKDIR /app

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend /app/backend

ENV FLASK_APP=backend.wsgi:app     APP_ENV=production

CMD ["gunicorn", "--bind=0.0.0.0:8080", "--workers=4", "backend.wsgi:app"]
