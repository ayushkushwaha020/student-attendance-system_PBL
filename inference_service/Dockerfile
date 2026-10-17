FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    OMP_NUM_THREADS=2 \
    OPENBLAS_NUM_THREADS=1

WORKDIR /service
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake libgl1 libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

COPY inference_service/requirements.txt ./requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY inference_service/ ./inference_service/
WORKDIR /service/inference_service

CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port \$\{PORT:-8000\}"]
