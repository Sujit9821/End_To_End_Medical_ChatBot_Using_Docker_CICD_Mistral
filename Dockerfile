# Use official Python slim image
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

# Copy only requirements first
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy the whole project (src, templates, static, etc.)
COPY . .

# Accept build-time Hugging Face token
ARG HF_TOKEN
ENV HF_TOKEN=$HF_TOKEN

# Download model during Docker build itself
RUN mkdir -p models && \
    python3 -c "\
import os; \
from huggingface_hub import login, hf_hub_download; \
token = os.getenv('HF_TOKEN'); \
login(token=token); \
hf_hub_download(repo_id='TheBloke/Mistral-7B-Instruct-v0.2-GGUF', \
                filename='mistral-7b-instruct-v0.2.Q5_K_M.gguf', \
                local_dir='./models', token=token);"

# Expose FastAPI default port
EXPOSE 8000

# Command to run the app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
