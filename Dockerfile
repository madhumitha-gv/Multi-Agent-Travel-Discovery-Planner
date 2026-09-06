# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Model downloads need certificates; nothing else is required at runtime.
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl \
 && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/models \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app

# Dependencies first so edits to the app don't invalidate this layer.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Bake the models into the image. Without this the first request after
# every cold start pays a multi-hundred-MB download, and the container
# needs a writable, persistent cache it may not have.
RUN python -c "\
from transformers import pipeline; \
pipeline('zero-shot-classification', model='MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli'); \
from sentence_transformers import SentenceTransformer; \
SentenceTransformer('all-MiniLM-L6-v2')"

COPY travel_planner/ ./travel_planner/

# Imports are top-level within the package directory.
WORKDIR /app/travel_planner

# Hosts inject the port to bind; default to Streamlit's own.
ENV PORT=8501
EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=90s --retries=3 \
  CMD curl -fsS "http://localhost:${PORT}/_stcore/health" || exit 1

CMD streamlit run app.py --server.port=${PORT} --server.address=0.0.0.0
