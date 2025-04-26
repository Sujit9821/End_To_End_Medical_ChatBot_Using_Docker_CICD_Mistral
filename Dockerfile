# Use BuildKit for optional secret mounting if you enable it (see docs)
# syntax=docker/dockerfile:1.4

FROM python:3.10-slim

# Prevent Python from writing .pyc files and buffer flushing
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    curl \
  && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Accept HF_TOKEN at build time
ARG HF_TOKEN
ENV HF_TOKEN=$HF_TOKEN

# Download model at build time
RUN mkdir -p models && \
    python3 - <<EOF
import os
from huggingface_hub import login, hf_hub_download

token = os.getenv("HF_TOKEN")
login(token=token)
hf_hub_download(
  repo_id="TheBloke/Mistral-7B-Instruct-v0.2-GGUF",
  filename="mistral-7b-instruct-v0.2.Q5_K_M.gguf",
  local_dir="./models",
  token=token
)
EOF

# Expose port and add container‐level healthcheck
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=5s --start-period=20s \
  CMD curl -f http://localhost:8000/health || exit 1

# Start the FastAPI app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
