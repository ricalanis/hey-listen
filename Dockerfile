# Use official Python runtime as base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies for audio processing
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    python3-pyaudio \
    alsa-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download Whisper model to avoid runtime download
RUN python -c "import whisper; whisper.load_model('tiny')"

# Copy application code
COPY src/audio_worker.py ./
COPY src/config.py ./
COPY src/pinecone_manager.py ./

# Create non-root user for security
RUN useradd -m -u 1000 audioworker && \
    chown -R audioworker:audioworker /app

# Switch to non-root user
USER audioworker

# Set environment variables
ENV WHISPER_MODEL=tiny
ENV CHUNK_DURATION=5
ENV SAMPLE_RATE=16000
ENV PINECONE_API_KEY=""
ENV PINECONE_ENVIRONMENT=""
ENV PINECONE_INDEX_NAME="hey-listen-transcriptions"
ENV EMBEDDING_MODEL="sentence-transformers/all-MiniLM-L6-v2"
ENV VECTOR_DIMENSION="384"
ENV MAX_RECORDS="1000"

# Run the application
CMD ["python", "audio_worker.py"]
