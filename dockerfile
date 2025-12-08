# Base image
FROM python:3.12-slim

# Install uv
RUN pip install uv

# Working directory inside the container
WORKDIR /app

# Copy requirements.txt
COPY backend/requirements.txt .

# Create virtual environment
RUN uv venv .venv

# Install Python dependencies
RUN uv pip install -r requirements.txt --python .venv/bin/python

# Copy the rest of the code (without .env)
COPY backend/ /app/

# Start FastAPI
CMD ["/app/.venv/bin/python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
