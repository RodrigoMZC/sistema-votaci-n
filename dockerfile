
# Dockerfile
FROM python:3.12-slim

# Variables de entorno para Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalar dependencias del sistema (necesarias para psycopg2)
RUN apt-get update && apt-get install -y \
    libpq-dev gcc --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código del proyecto
COPY . .

# Recolectar archivos estáticos
# RUN python manage.py collectstatic --noinput

# Exponer el puerto interno de Gunicorn
EXPOSE 8000

# Comando de arranque
CMD ["gunicorn", "votaciones.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
