FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY api /app
COPY data /data
COPY scrapers /scrapers

ENV PYTHONPATH=/app:/scrapers
ENV USE_SQLITE=true
ENV SAMPLE_DATA_PATH=/data/sample/scandals.json
ENV SEED_ON_STARTUP=true
ENV REPLACE_SEED_ON_STARTUP=false
ENV ENVIRONMENT=development
ENV DISABLE_DOCS=false
ENV TRUSTED_HOSTS=["*"]

EXPOSE 7860

# Render injects $PORT; default 7860 for local/HF-style runs
CMD ["sh", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
