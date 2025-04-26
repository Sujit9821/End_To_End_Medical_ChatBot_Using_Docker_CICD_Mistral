# syntax=docker/dockerfile:1.4

# Base Python image
FROM python:3.10-slim

# Environment settings
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
 && pip install "huggingface_hub[hf_xet]"

# Copy application source code
COPY . .

# Accept Hugging Face token as build argument
ARG HF_TOKEN
ENV HF_TOKEN=${HF_TOKEN}

# Download model during build
RUN python scripts/download_model.py

# Expose the app port
EXPOSE 8000

# Container healthcheck
HEALTHCHECK --interval=10s --timeout=5s --start-period=20s \
  CMD curl -f http://localhost:8000/health || exit 1

# Start FastAPI app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
