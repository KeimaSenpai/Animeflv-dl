# Usa una imagen de Python
FROM python:3.11.6

# Establece el directorio de trabajo en /app
WORKDIR /app

RUN apt update && apt upgrade -y

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    # Si necesitas hacer operaciones con video, también podrías necesitar:
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    && rm -rf /var/lib/apt/lists/*
# Copia el archivo de requisitos al contenedor
COPY requirements.txt .

# Instala las dependencias
RUN pip install -r requirements.txt

# Copia el script de Python al contenedor
COPY . .

# Ejecuta el script cuando el contenedor se inicia
CMD ["bash", "start.sh"]