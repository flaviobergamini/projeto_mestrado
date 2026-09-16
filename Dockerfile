FROM python:3.11-slim

WORKDIR /app

# Dependências de sistema pra compilar pacotes com extensões nativas (ex.: cryptography)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Mesmo comando do render.yaml — 2 workers uvicorn atrás do gunicorn,
# timeout de 120s como watchdog de processo (ver PoC/scripts/start_render.sh,
# mesma estratégia usada lá).
ENV PORT=8000
EXPOSE 8000
CMD gunicorn main:app -w 2 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --timeout 120
