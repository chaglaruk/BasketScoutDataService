FROM python:3.11-slim

# Metadata
LABEL maintainer="chaglaruk"
LABEL description="BasketScoutDataService — FastAPI backend"

# Ortam değişkenleri
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=8787 \
    ENV=production \
    DEBUG=false

WORKDIR /app

# Bağımlılıkları kopyala ve yükle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama kodunu kopyala
COPY app/ ./app/
COPY data/ ./data/

# Veri dizinini oluştur
RUN mkdir -p data/manual_import artifacts

# Veritabanı başlatma
RUN python -m app.scripts.seed_demo_data || true

EXPOSE 8787

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import httpx; r=httpx.get('http://localhost:8787/health'); assert r.json()['ok']"

CMD ["sh", "-c", "python -m uvicorn app.main:app --host ${HOST:-0.0.0.0} --port ${PORT:-8787}"]
