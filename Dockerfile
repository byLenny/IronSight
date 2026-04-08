FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

# Install system dependencies for OpenCV and MediaMTX (ffmpeg to generate streams)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libglib2.0-0 \
    wget \
    tar \
    zip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Directory for permanent settings storage
RUN mkdir -p /app/data

# Copy all source files
COPY app /app/app
COPY frontend/dist /app/frontend/dist

# Expose ports
EXPOSE 8000
EXPOSE 8554
EXPOSE 1935

# MediaMTX will be downloaded at runtime by python if not present, but 
# we rely on python to spawn it.

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
