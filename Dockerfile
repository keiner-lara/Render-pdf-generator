# src/Dockerfile
FROM python:3.11-slim

# Evitar que Python genere archivos .pyc y permitir logs en tiempo real
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/app

WORKDIR /app

# Instalar dependencias del sistema para psycopg2 y utilidades
# Instalar dependencias del sistema para psycopg2, cairo (PDFs) y utilidades
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    netcat-openbsd \
    pkg-config \
    python3-dev \
    libjpeg-dev \
    zlib1g-dev \
    libcairo2-dev \
    libpango1.0-dev \
    libgif-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Crear carpeta para los reportes generados
RUN mkdir -p artifacts

# Script de entrada para esperar a la DB y ejecutar migraciones/seed
RUN chmod +x test_deploy.sh

CMD ["python", "src/main_api.py"]