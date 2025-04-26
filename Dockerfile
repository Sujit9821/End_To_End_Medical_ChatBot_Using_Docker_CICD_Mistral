# syntax=docker/dockerfile:1.4

# Base Python image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    curl \
 && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt \
 && pip install huggingface_hub[hf_xet]

# Copy application code
COPY . .

# Accept Hugging Face Token during build
ARG HF_TOKEN
ENV HF_TOKEN=$HF_TOKEN

# Download model during build
RUN mkdir -p models && \
    python3 -c "import os; \
import sys; \
from huggingface_hub import login, hf_hub_download; \
token = os.getenv('HF_TOKEN'); \
if not token: sys.exit('❌ No HF_TOKEN provided!'); \
login(token=token); \
model_dir = './models'; \
os.makedirs(model_dir, exist_ok=True); \
model_path = hf_hub_download( \
    repo_id='TheBloke/Mistral-7B-Instruct-v0.2-GGUF', \
    filename='mistral-7b-instruct-v0.2.Q5_K_M.gguf', \
    local_dir=model_dir, \
    token=token, \
    local_dir_use_symlinks=False \
); \
print(f'✅ Model downloaded and saved at {model_path}');"

# Expose the FastAPI port
EXPOSE 8000

# Add container healthcheck
HEALTHCHECK --interval=10s --timeout=5s --start-period=20s \
  CMD curl -f http://localhost:8000/health || exit 1

# Start the FastAPI app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
