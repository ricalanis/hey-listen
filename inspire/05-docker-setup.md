# Docker Setup Guide

## Overview

This guide covers containerizing the Hey Listen Audio Worker using Docker and Docker Compose for production deployment. Containerization provides isolation, portability, and easy deployment across different environments.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 1.29+
- Senso.ai API key
- Working microphone on host machine

## Docker Architecture

```
┌─────────────────────────────────────────┐
│         Docker Host                      │
│                                          │
│  ┌────────────────────────────────┐    │
│  │  audio-worker Container         │    │
│  │                                 │    │
│  │  ┌──────────────────────┐      │    │
│  │  │  Python 3.9          │      │    │
│  │  │  + Whisper           │      │    │
│  │  │  + sounddevice       │      │    │
│  │  │  + audio_worker.py   │      │    │
│  │  └──────────────────────┘      │    │
│  │                                 │    │
│  │  Volume: .env ───────────────  │    │
│  │  Device: /dev/snd ────────────┼────┼─── Host Microphone
│  └─────────────────────────────────┘   │
│                      │                   │
└──────────────────────┼───────────────────┘
                       │
                       ▼
              Senso.ai API (Internet)
```

## Implementation Steps

### Step 1: Create Dockerfile

#### File: `Dockerfile`

```dockerfile
# Use official Python runtime as base image
FROM python:3.9-slim

# Set metadata
LABEL maintainer="your-email@example.com"
LABEL description="Hey Listen Audio Worker - Real-time transcription with Senso.ai"

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
# This downloads the model during build, reducing startup time
RUN python -c "import whisper; whisper.load_model('tiny')"

# Copy application code
COPY src/audio_worker.py .

# Create non-root user for security
RUN useradd -m -u 1000 audioworker && \
    chown -R audioworker:audioworker /app

# Switch to non-root user
USER audioworker

# Set environment variables (can be overridden by docker-compose)
ENV WHISPER_MODEL=tiny
ENV CHUNK_DURATION=5
ENV SAMPLE_RATE=16000

# Health check (optional - checks if process is running)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD pgrep -f audio_worker.py || exit 1

# Run the application
CMD ["python", "audio_worker.py"]
```

### Step 2: Create Docker Compose Configuration

#### File: `docker-compose.yml`

```yaml
version: '3.8'

services:
  audio-worker:
    # Build configuration
    build:
      context: .
      dockerfile: Dockerfile

    # Container name
    container_name: hey-listen-audio-worker

    # Restart policy
    restart: unless-stopped

    # Environment variables
    environment:
      - SENSO_API_KEY=${SENSO_API_KEY}
      - WHISPER_MODEL=${WHISPER_MODEL:-tiny}
      - CHUNK_DURATION=${CHUNK_DURATION:-5}
      - SAMPLE_RATE=${SAMPLE_RATE:-16000}

    # Volume mounts
    volumes:
      # Mount .env file for local development (optional)
      - ./.env:/app/.env:ro

    # Device access for microphone
    devices:
      - /dev/snd:/dev/snd  # ALSA sound devices (Linux/macOS)

    # Privileged mode for audio device access (if needed)
    # privileged: true  # Uncomment if audio access issues persist

    # Logging configuration
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

# Optional: Networks for multi-service setups
networks:
  default:
    name: hey-listen-network
```

### Step 3: Environment Configuration for Docker

#### File: `.env` (for Docker Compose)

```bash
# Senso.ai API Key (REQUIRED)
SENSO_API_KEY=your_api_key_here

# Whisper Model Configuration
WHISPER_MODEL=tiny

# Audio Configuration
CHUNK_DURATION=5
SAMPLE_RATE=16000
```

**Security Note**: Ensure `.env` is in `.gitignore`

#### File: `.dockerignore`

```
# Python
__pycache__
*.pyc
*.pyo
*.pyd
.Python
*.so

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp

# Git
.git
.gitignore

# Documentation
insights/
*.md

# OS
.DS_Store
Thumbs.db

# Test files
tests/
*.test.py

# Local development
.env.local
```

### Step 4: Build and Run

#### Build the Docker Image

```bash
# Build the image
docker-compose build

# Or build manually
docker build -t hey-listen-audio-worker .
```

**Expected Output**:
```
[+] Building 45.2s (15/15) FINISHED
 => [1/8] FROM docker.io/library/python:3.9-slim
 => [2/8] RUN apt-get update && apt-get install -y portaudio19-dev...
 => [3/8] COPY requirements.txt .
 => [4/8] RUN pip install --no-cache-dir -r requirements.txt
 => [5/8] RUN python -c "import whisper; whisper.load_model('tiny')"
 => [6/8] COPY src/audio_worker.py .
 => exporting to image
Successfully built abc123def456
```

#### Run the Container

```bash
# Run with docker-compose (recommended)
docker-compose up

# Run in detached mode (background)
docker-compose up -d

# View logs
docker-compose logs -f audio-worker
```

**Expected Log Output**:
```
audio-worker | 2025-10-04 12:00:00 - INFO - Loading Whisper model: tiny
audio-worker | 2025-10-04 12:00:01 - INFO - Whisper model loaded successfully
audio-worker | ============================================================
audio-worker | Starting Hey Listen Audio Worker
audio-worker | Model: tiny
audio-worker | Chunk Duration: 5s
audio-worker | Sample Rate: 16000Hz
audio-worker | API Key Set: Yes
audio-worker | ============================================================
audio-worker | 2025-10-04 12:00:01 - INFO - Listening... Press Ctrl+C to stop
```

#### Stop the Container

```bash
# Stop (with docker-compose)
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## Platform-Specific Configurations

### macOS

**Issue**: Docker Desktop on macOS doesn't support `/dev/snd` device passthrough.

**Solution**: Run natively (not in Docker) or use PulseAudio bridge.

**Alternative**: Use host network mode and PulseAudio:

```yaml
services:
  audio-worker:
    network_mode: "host"
    environment:
      - PULSE_SERVER=unix:/run/user/1000/pulse/native
    volumes:
      - /run/user/1000/pulse:/run/user/1000/pulse
```

**Recommendation**: For macOS, run the application natively using `python src/audio_worker.py` instead of Docker.

### Linux

**Standard Setup** (works out of the box):
```yaml
devices:
  - /dev/snd:/dev/snd
```

**If permission issues**:
```bash
# Add user to audio group on host
sudo usermod -a -G audio $USER

# Or run container with privileged mode
privileged: true
```

### Windows (WSL2)

**Requirements**:
- WSL2 with Ubuntu
- Docker Desktop with WSL2 backend

**Audio Setup**:
1. Install PulseAudio in WSL2:
   ```bash
   sudo apt-get install pulseaudio
   ```

2. Configure Docker Compose:
   ```yaml
   devices:
     - /dev/snd:/dev/snd
   environment:
     - PULSE_SERVER=/mnt/wslg/PulseServer
   volumes:
     - /mnt/wslg:/mnt/wslg
   ```

**Recommendation**: For Windows, run natively in WSL2 using Python (not Docker).

## Production Deployment

### Using Docker Hub

#### Build and Push

```bash
# Tag image
docker tag hey-listen-audio-worker your-dockerhub-username/hey-listen:latest

# Login to Docker Hub
docker login

# Push image
docker push your-dockerhub-username/hey-listen:latest
```

#### Pull and Run on Server

```bash
# On production server
docker pull your-dockerhub-username/hey-listen:latest

# Run with environment variables
docker run -d \
  --name hey-listen \
  --device /dev/snd \
  -e SENSO_API_KEY=your_key \
  --restart unless-stopped \
  your-dockerhub-username/hey-listen:latest
```

### Using Docker Secrets (Recommended for Production)

#### File: `docker-compose.prod.yml`

```yaml
version: '3.8'

services:
  audio-worker:
    image: your-dockerhub-username/hey-listen:latest
    container_name: hey-listen-audio-worker
    restart: always

    # Use Docker secrets instead of environment variables
    secrets:
      - senso_api_key

    environment:
      - SENSO_API_KEY_FILE=/run/secrets/senso_api_key
      - WHISPER_MODEL=base  # Larger model for production
      - CHUNK_DURATION=5
      - SAMPLE_RATE=16000

    devices:
      - /dev/snd:/dev/snd

    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "5"

secrets:
  senso_api_key:
    file: ./secrets/senso_api_key.txt
```

**Setup**:
```bash
# Create secrets directory
mkdir -p secrets

# Store API key in file
echo "your_actual_api_key" > secrets/senso_api_key.txt

# Secure the file
chmod 600 secrets/senso_api_key.txt

# Update audio_worker.py to read from file
# In __init__:
# api_key_file = os.getenv('SENSO_API_KEY_FILE')
# if api_key_file:
#     with open(api_key_file) as f:
#         self.api_key = f.read().strip()
```

### Kubernetes Deployment (Advanced)

#### File: `k8s/deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hey-listen-audio-worker
spec:
  replicas: 1
  selector:
    matchLabels:
      app: hey-listen
  template:
    metadata:
      labels:
        app: hey-listen
    spec:
      containers:
      - name: audio-worker
        image: your-dockerhub-username/hey-listen:latest
        env:
        - name: SENSO_API_KEY
          valueFrom:
            secretKeyRef:
              name: senso-credentials
              key: api-key
        - name: WHISPER_MODEL
          value: "base"
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        volumeMounts:
        - name: audio-device
          mountPath: /dev/snd
      volumes:
      - name: audio-device
        hostPath:
          path: /dev/snd
---
apiVersion: v1
kind: Secret
metadata:
  name: senso-credentials
type: Opaque
stringData:
  api-key: your_api_key_here
```

## Monitoring and Debugging

### View Real-time Logs

```bash
# Follow logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100

# Logs from specific service
docker-compose logs audio-worker
```

### Check Container Status

```bash
# List running containers
docker-compose ps

# Container resource usage
docker stats hey-listen-audio-worker

# Inspect container
docker inspect hey-listen-audio-worker
```

### Access Container Shell

```bash
# Interactive shell
docker-compose exec audio-worker /bin/bash

# Run Python inside container
docker-compose exec audio-worker python

# Check audio devices
docker-compose exec audio-worker arecord -l
```

### Test Microphone Access

```bash
# Record 5-second test
docker-compose exec audio-worker arecord -d 5 -f cd test.wav

# Check if file created
docker-compose exec audio-worker ls -lh test.wav
```

## Troubleshooting

### Issue: "Cannot find audio device"

**Cause**: Container doesn't have microphone access

**Solutions**:
1. Add `privileged: true` to docker-compose.yml
2. Verify `/dev/snd` exists on host: `ls /dev/snd`
3. Check user is in audio group: `groups`

### Issue: "SENSO_API_KEY not found"

**Cause**: Environment variable not passed correctly

**Solutions**:
1. Verify `.env` file exists and contains `SENSO_API_KEY=...`
2. Check docker-compose loads .env: `docker-compose config`
3. Pass directly: `SENSO_API_KEY=xxx docker-compose up`

### Issue: "Whisper model download fails in container"

**Cause**: Network issues or cache permissions

**Solutions**:
1. Pre-download in Dockerfile (already included in example)
2. Mount cache: `volumes: - ~/.cache/whisper:/home/audioworker/.cache/whisper`
3. Build with: `docker-compose build --no-cache`

### Issue: High CPU usage

**Cause**: Whisper model too large for container resources

**Solutions**:
1. Use smaller model: `WHISPER_MODEL=tiny`
2. Increase container CPU limit: `cpus: "2.0"` in docker-compose.yml
3. Add resource limits:
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '2.0'
         memory: 4G
   ```

## Best Practices

1. **Use Multi-stage Builds** (optimize image size):
   ```dockerfile
   FROM python:3.9-slim as builder
   # ... install and build ...

   FROM python:3.9-slim
   COPY --from=builder /app /app
   ```

2. **Pin Dependency Versions** in requirements.txt (already done)

3. **Health Checks** for automatic restart on failure (included)

4. **Logging** to external service (e.g., ELK stack, Datadog)

5. **Secrets Management** - never commit API keys

6. **Resource Limits** to prevent runaway containers

7. **Volume Persistence** if adding local fallback buffer

## Next Steps

- [ ] Deploy to cloud (AWS ECS, Google Cloud Run, Azure Container Instances)
- [ ] Set up CI/CD pipeline (GitHub Actions, GitLab CI)
- [ ] Add monitoring (Prometheus, Grafana)
- [ ] Implement log aggregation (ELK, Loki)

Proceed to `06-testing-guide.md` for comprehensive testing strategies.
