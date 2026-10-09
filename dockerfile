# Usa una imagen oficial y ligera de Python
FROM python:3.12-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia primero el archivo de requerimientos para aprovechar el caché de Docker
COPY requirements.txt .

# Instala las dependencias sin guardar caché temporal para mantener la imagen ligera
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo el código fuente de tu proyecto al contenedor
COPY . .

# Expone el puerto 8000 para que el tráfico externo pueda comunicarse con FastAPI
EXPOSE 8000

# Comando para ejecutar la aplicación (usando 0.0.0.0 para que escuche conexiones externas)
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]