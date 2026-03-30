# ── PowderyVision7 – Hugging Face Spaces / Google Cloud Run ────────────────
# Compatible con ambas plataformas via variable PORT
FROM python:3.11-slim

WORKDIR /app

# Dependencias del sistema para OpenCV y librerías científicas
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python (aprovecha caché de Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente completo (modelos incluidos)
COPY . .

# Crear directorio de resultados temporales
RUN mkdir -p static/results

# Hugging Face Spaces usa 7860; Cloud Run inyecta 8080 via env PORT
ENV PORT=7860
EXPOSE 7860

# Shell form para que $PORT se resuelva en tiempo de ejecución
CMD gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 120 --keep-alive 5 app:app
