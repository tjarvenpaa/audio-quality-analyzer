# Dockerfile for Audio Quality AI - Main Application
FROM python:3.10-slim

# Metadata
LABEL maintainer="Audio Quality AI"
LABEL description="GPU-accelerated audio quality analyzer"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# For GPU support, uncomment:
# RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Copy application code
COPY src/ /app/src/
COPY config.yaml /app/
COPY *.md /app/

# Create input/output directories
RUN mkdir -p /app/input_folder /app/output

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV OLLAMA_URL=http://ollama:11434
ENV PYTHONPATH=/app

# Expose ports (if needed for future API)
EXPOSE 8000

# Default command - keep container running
CMD ["tail", "-f", "/dev/null"]
