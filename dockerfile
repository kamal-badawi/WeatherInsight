# Basis-Image
FROM python:3.12-slim

# uv installieren
RUN pip install uv

# Arbeitsverzeichnis im Container
WORKDIR /app

# requirements.txt kopieren
COPY backend/requirements.txt .

# virtuelle Umgebung erstellen
RUN uv venv .venv

# Python-Bibliotheken installieren
RUN uv pip install -r requirements.txt --python .venv/bin/python

# restlichen Code kopieren (ohne .env)
COPY backend/ /app/

# FastAPI starten
CMD ["/app/.venv/bin/python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
