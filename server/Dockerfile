FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PIP_NO_CACHE_DIR=1

# Cambiamos a /app para que coincida con la raíz de tu código en el contenedor
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiamos desde la carpeta server local al directorio actual (.) que es /app
COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el contenido de server/ a /app
COPY server/ .

EXPOSE 8000

# Ahora el módulo estará directamente en /app y uvicorn lo encontrará
CMD ["uvicorn", "gpu_agent_api:app", "--host", "0.0.0.0", "--port", "8000"]