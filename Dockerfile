# syntax=docker/dockerfile:1.4

##########################
# Stage 1: Model Download
##########################
FROM python:3.10-slim as downloader

WORKDIR /download

RUN apt-get update && apt-get install -y build-essential gcc curl && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip && pip install huggingface_hub[hf_xet]

# Accept Hugging Face token
ARG HF_TOKEN
ENV HF_TOKEN=${HF_TOKEN}

COPY src/download_model.py .

RUN python download_model.py

##########################
# Stage 2: Final Image
##########################
FROM python:3.10-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y build-essential gcc curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt && pip install huggingface_hub[hf_xet]

# Copy App code
COPY . .

# Copy Model from Stage 1
COPY --from=downloader /download/models ./models

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --start-period=20s \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
