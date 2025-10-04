# Hey Listen - Agent Implementation Guide

## 🎯 Overview

This document provides a step-by-step implementation guide for building the **Hey Listen Audio Worker** - a real-time transcription system that captures conversations, transcribes them using Whisper, and organizes the data in Senso.ai for intelligent retrieval.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Implementation Phases](#implementation-phases)
3. [Phase 1: Environment Setup](#phase-1-environment-setup)
4. [Phase 2: Core Implementation](#phase-2-core-implementation)
5. [Phase 3: Senso.ai Integration](#phase-3-sensoai-integration)
6. [Phase 4: Testing & Validation](#phase-4-testing--validation)
7. [Phase 5: Docker Deployment](#phase-5-docker-deployment)
8. [Phase 6: Production Readiness](#phase-6-production-readiness)
9. [Troubleshooting](#troubleshooting)
10. [Next Steps](#next-steps)

## Prerequisites

### Required Knowledge
- Python 3.9+ programming
- Basic understanding of APIs and REST
- Docker fundamentals (for deployment)
- Audio processing concepts (basic)

### Required Tools
- Python 3.9 or higher
- Git
- Docker Desktop (for containerization)
- A microphone
- Text editor / IDE

### Required Accounts
- Senso.ai account with API key ([contact support@senso.ai](mailto:support@senso.ai))

## Implementation Phases

```
Phase 1: Environment Setup (30 min)
    ↓
Phase 2: Core Implementation (2-3 hours)
    ↓
Phase 3: Senso.ai Integration (1 hour)
    ↓
Phase 4: Testing & Validation (1-2 hours)
    ↓
Phase 5: Docker Deployment (1 hour)
    ↓
Phase 6: Production Readiness (ongoing)
```

**Total Estimated Time**: 6-8 hours for complete implementation

---

## Phase 1: Environment Setup

**Goal**: Set up your development environment with all necessary dependencies.

### Step 1.1: Clone and Initialize Repository

```bash
# Navigate to your projects directory
cd ~/Documents/dev

# If starting fresh
mkdir hey-listen
cd hey-listen
git init

# Create basic structure
mkdir -p src tests/fixtures insights
```

### Step 1.2: Create Requirements File

Create `requirements.txt`:

```txt
openai-whisper==20230124
sounddevice==0.4.6
numpy==1.24.3
requests==2.31.0
python-dotenv==1.0.0
```

### Step 1.3: Install System Dependencies

**macOS**:
```bash
brew install portaudio
```

**Ubuntu/Debian**:
```bash
sudo apt-get update
sudo apt-get install portaudio19-dev python3-pyaudio
```

**Windows** (WSL2):
```bash
sudo apt-get install portaudio19-dev
```

### Step 1.4: Set Up Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

**✅ Validation**: Run `pip list` and verify all packages are installed.

### Step 1.5: Configure Environment Variables

Create `.env.example`:

```bash
# Senso.ai API Configuration
SENSO_API_KEY=your_api_key_here

# Whisper Model (tiny, base, small, medium, large)
WHISPER_MODEL=tiny

# Audio Configuration
CHUNK_DURATION=5
SAMPLE_RATE=16000
```

Create `.env` (your actual config):

```bash
cp .env.example .env
# Edit .env and add your real Senso.ai API key
```

Create `.gitignore`:

```
# Environment
.env

# Python
__pycache__/
*.py[cod]
venv/
.Python

# IDEs
.vscode/
.idea/

# OS
.DS_Store

# Whisper cache
~/.cache/whisper/
```

**✅ Validation**: Run `cat .env` and verify your API key is present.

### Step 1.6: Request Senso.ai API Key

1. Email: [support@senso.ai](mailto:support@senso.ai)
2. Request: "Organization-scoped API key for transcription project"
3. Wait for response (usually 1-2 business days)
4. Add key to `.env` file

**📚 Reference**: See `insights/03-senso-api-integration.md` for API details.

---

## Phase 2: Core Implementation

**Goal**: Build the audio worker with capture, transcription, and diarization.

### Step 2.1: Create Audio Worker Skeleton

Create `src/audio_worker.py`:

```python
"""
Audio Worker for Hey Listen
Captures audio, transcribes with Whisper, and ingests to Senso.ai
"""

import sounddevice as sd
import whisper
import numpy as np
import requests
from dotenv import load_dotenv
import os
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class AudioWorker:
    """
    Continuous audio transcription worker with Senso.ai integration.
    """

    def __init__(
        self,
        model_name=None,
        sample_rate=None,
        chunk_duration=None
    ):
        """Initialize the Audio Worker."""
        # Load environment variables
        load_dotenv()

        # API Configuration
        self.api_key = os.getenv('SENSO_API_KEY')
        if not self.api_key:
            logging.warning("SENSO_API_KEY not set in .env file.")

        # Audio Configuration
        self.sample_rate = sample_rate or int(os.getenv('SAMPLE_RATE', 16000))
        self.chunk_duration = chunk_duration or int(os.getenv('CHUNK_DURATION', 5))

        # Whisper Model
        model_name = model_name or os.getenv('WHISPER_MODEL', 'tiny')
        logging.info(f"Loading Whisper model: {model_name}")
        self.model = whisper.load_model(model_name)
        logging.info("Whisper model loaded successfully")


def main():
    """Entry point for the Audio Worker."""
    worker = AudioWorker()
    # TODO: Implement run loop


if __name__ == "__main__":
    main()
```

**✅ Validation**: Run `python src/audio_worker.py` - should load Whisper model without errors.

### Step 2.2: Implement Audio Capture

Add to `AudioWorker` class:

```python
def capture_audio(self):
    """
    Capture audio chunk from microphone.

    Returns:
        numpy.ndarray: Audio samples, or None if capture fails
    """
    try:
        logging.debug(
            f"Capturing {self.chunk_duration}s audio "
            f"at {self.sample_rate}Hz"
        )

        # Record audio
        audio = sd.rec(
            int(self.chunk_duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=1,
            dtype='float32'
        )
        sd.wait()  # Wait for recording to finish

        return audio.flatten()

    except Exception as e:
        logging.error(f"Audio capture failed: {e}")
        return None
```

**✅ Validation**:
```python
# Test in Python REPL
from src.audio_worker import AudioWorker
worker = AudioWorker()
audio = worker.capture_audio()  # Speak for 5 seconds
print(f"Captured {len(audio)} samples")
```

### Step 2.3: Implement Transcription

Add to `AudioWorker` class:

```python
def transcribe_audio(self, audio):
    """
    Transcribe audio using Whisper.

    Args:
        audio (numpy.ndarray): Audio samples

    Returns:
        str: Transcribed text, or empty string if transcription fails
    """
    try:
        # Transcribe with Whisper
        result = self.model.transcribe(
            audio,
            language="en",
            fp16=False  # Disable FP16 for CPU compatibility
        )

        text = result["text"].strip()

        if text:
            logging.debug(f"Transcribed: {text[:50]}...")

        return text

    except Exception as e:
        logging.error(f"Transcription failed: {e}")
        return ""
```

**✅ Validation**:
```python
worker = AudioWorker()
audio = worker.capture_audio()  # Say "Hello world"
text = worker.transcribe_audio(audio)
print(f"Transcription: {text}")
```

### Step 2.4: Implement Basic Diarization (Placeholder)

Add to `AudioWorker` class:

```python
def diarize(self, audio):
    """
    Perform basic speaker diarization.

    TODO: Implement real diarization with pyannote.audio

    Args:
        audio (numpy.ndarray): Audio samples

    Returns:
        str: Speaker label (A, B, C, etc.)
    """
    # Placeholder: Always return Speaker A
    # Future enhancement: Use pyannote.audio for real diarization
    return "A"
```

**📚 Reference**: See `insights/04-audio-worker-implementation.md` for advanced diarization.

---

## Phase 3: Senso.ai Integration

**Goal**: Integrate with Senso.ai API for cloud storage and retrieval.

### Step 3.1: Implement Ingestion Method

Add to `AudioWorker` class:

```python
def ingest_to_senso(self, text, speaker, timestamp):
    """
    Ingest transcription to Senso.ai knowledge base.

    Args:
        text (str): Transcribed text
        speaker (str): Speaker identifier
        timestamp (float): Unix timestamp

    Returns:
        str: Content ID if successful, None otherwise
    """
    # Validate API key
    if not self.api_key:
        logging.error("Cannot ingest: SENSO_API_KEY not set")
        return None

    # Skip empty transcriptions
    if not text.strip():
        logging.debug("Skipping empty transcription")
        return None

    # Format timestamp for human readability
    time_str = time.strftime(
        '%Y-%m-%d %H:%M:%S',
        time.localtime(timestamp)
    )

    # Prepare payload
    payload = {
        "title": f"Transcription - Speaker {speaker} at {time_str}",
        "summary": f"Transcript from {speaker}: {text[:100]}...",
        "text": (
            f"**Speaker {speaker}:** {text}\n\n"
            f"*Timestamp: {timestamp}*"
        )
    }

    try:
        # Send POST request to Senso.ai
        response = requests.post(
            "https://sdk.senso.ai/api/v1/content/raw",
            headers={
                "X-API-Key": self.api_key,
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=10
        )

        # Check for HTTP errors
        response.raise_for_status()

        # Parse response
        data = response.json()
        content_id = data.get("id")
        status = data.get("processing_status", "unknown")

        logging.info(
            f"✓ Ingested to Senso: {content_id} "
            f"(Status: {status})"
        )

        # Wait for content to be indexed
        time.sleep(2)

        return content_id

    except requests.exceptions.HTTPError as e:
        logging.error(
            f"✗ HTTP Error during ingest: "
            f"{e.response.status_code} - {e.response.text}"
        )
        return None

    except requests.exceptions.RequestException as e:
        logging.error(f"✗ Network error during ingest: {e}")
        return None

    except Exception as e:
        logging.error(f"✗ Unexpected error during ingest: {e}")
        return None
```

**✅ Validation**:
```bash
# Test with curl first
curl -X POST https://sdk.senso.ai/api/v1/content/raw \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test",
    "summary": "Testing",
    "text": "**Speaker A:** Hello\n*Timestamp: 1728054645*"
  }'
```

### Step 3.2: Implement Main Run Loop

Add to `AudioWorker` class:

```python
def run(self):
    """
    Main loop: continuously capture, transcribe, and ingest audio.
    """
    logging.info("=" * 60)
    logging.info("Starting Hey Listen Audio Worker")
    logging.info(f"Model: {os.getenv('WHISPER_MODEL', 'tiny')}")
    logging.info(f"Chunk Duration: {self.chunk_duration}s")
    logging.info(f"Sample Rate: {self.sample_rate}Hz")
    logging.info(f"API Key Set: {'Yes' if self.api_key else 'No'}")
    logging.info("=" * 60)

    if not self.api_key:
        logging.warning(
            "Running in LOCAL MODE (no Senso.ai ingestion). "
            "Set SENSO_API_KEY in .env to enable cloud storage."
        )

    logging.info("Listening... Press Ctrl+C to stop")

    try:
        while True:
            # Step 1: Capture audio
            audio = self.capture_audio()
            if audio is None:
                logging.warning("Audio capture failed, retrying...")
                time.sleep(1)
                continue

            # Step 2: Transcribe
            text = self.transcribe_audio(audio)
            if not text:
                logging.debug("No speech detected, continuing...")
                continue

            # Step 3: Diarize
            speaker = self.diarize(audio)

            # Step 4: Ingest to Senso.ai
            timestamp = time.time()
            content_id = self.ingest_to_senso(text, speaker, timestamp)

            # Log result
            if content_id:
                logging.info(
                    f"[{speaker}] {text[:60]}... → {content_id}"
                )
            else:
                logging.info(f"[{speaker}] {text[:60]}... → LOCAL ONLY")

            # Small delay to prevent CPU overload
            time.sleep(0.1)

    except KeyboardInterrupt:
        logging.info("\n" + "=" * 60)
        logging.info("Shutting down Audio Worker")
        logging.info("=" * 60)
```

Update `main()`:

```python
def main():
    """Entry point for the Audio Worker."""
    worker = AudioWorker()
    worker.run()
```

**✅ Validation**: Run `python src/audio_worker.py` and speak - should see transcriptions and Senso.ai IDs.

**📚 Reference**: See `insights/03-senso-api-integration.md` for API details.

---

## Phase 4: Testing & Validation

**Goal**: Ensure the system works correctly with comprehensive testing.

### Step 4.1: Manual Testing

```bash
# Activate virtual environment
source venv/bin/activate

# Run the worker
python src/audio_worker.py
```

**Test Scenarios**:

1. **Basic Transcription**
   - Speak clearly: "Hello, this is a test"
   - Verify log shows transcription
   - Check for Senso.ai content ID

2. **Silent Audio**
   - Stay silent for 5 seconds
   - Verify "No speech detected" in logs

3. **Error Handling**
   - Remove API key from `.env`
   - Verify warning but no crash
   - Should show "LOCAL ONLY" mode

4. **Network Failure**
   - Disconnect internet
   - Speak and verify error logged
   - Reconnect and verify recovery

### Step 4.2: Verify Senso.ai Storage

```bash
# Search for your transcriptions
curl -X POST https://sdk.senso.ai/api/v1/search \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "recent transcriptions from the last hour",
    "max_results": 10
  }' | jq
```

**Expected**: Should see your transcriptions in results.

### Step 4.3: Unit Testing (Optional)

Create `tests/test_unit.py`:

```python
import pytest
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from audio_worker import AudioWorker


@patch('audio_worker.whisper.load_model')
@patch.dict(os.environ, {"SENSO_API_KEY": "test_key"})
def test_init(mock_load_model):
    mock_load_model.return_value = Mock()
    worker = AudioWorker()
    assert worker.api_key == "test_key"
    assert worker.sample_rate == 16000
```

Run tests:
```bash
pip install pytest pytest-mock
pytest tests/test_unit.py -v
```

**📚 Reference**: See `insights/06-testing-guide.md` for comprehensive testing.

---

## Phase 5: Docker Deployment

**Goal**: Containerize the application for production deployment.

### Step 5.1: Create Dockerfile

Create `Dockerfile`:

```dockerfile
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
COPY src/audio_worker.py .

# Create non-root user for security
RUN useradd -m -u 1000 audioworker && \
    chown -R audioworker:audioworker /app

# Switch to non-root user
USER audioworker

# Set environment variables
ENV WHISPER_MODEL=tiny
ENV CHUNK_DURATION=5
ENV SAMPLE_RATE=16000

# Run the application
CMD ["python", "audio_worker.py"]
```

### Step 5.2: Create Docker Compose Configuration

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  audio-worker:
    build:
      context: .
      dockerfile: Dockerfile

    container_name: hey-listen-audio-worker

    restart: unless-stopped

    environment:
      - SENSO_API_KEY=${SENSO_API_KEY}
      - WHISPER_MODEL=${WHISPER_MODEL:-tiny}
      - CHUNK_DURATION=${CHUNK_DURATION:-5}
      - SAMPLE_RATE=${SAMPLE_RATE:-16000}

    volumes:
      - ./.env:/app/.env:ro

    devices:
      - /dev/snd:/dev/snd  # ALSA sound devices (Linux/macOS)

    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### Step 5.3: Build and Run

```bash
# Build the image
docker-compose build

# Run in foreground
docker-compose up

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f audio-worker

# Stop
docker-compose down
```

**✅ Validation**: Check logs show same output as local run.

### Step 5.4: Platform-Specific Notes

**macOS**: Docker Desktop doesn't support `/dev/snd` passthrough. Recommend running natively:
```bash
python src/audio_worker.py
```

**Linux**: Should work out of the box. If permissions issues:
```bash
sudo usermod -a -G audio $USER
```

**Windows (WSL2)**: Run natively in WSL2 instead of Docker.

**📚 Reference**: See `insights/05-docker-setup.md` for detailed Docker setup.

---

## Phase 6: Production Readiness

**Goal**: Prepare for production deployment with monitoring and enhancements.

### Step 6.1: Add Retry Logic

Install retry library:
```bash
pip install tenacity
echo "tenacity==8.2.3" >> requirements.txt
```

Update `ingest_to_senso()`:

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def ingest_to_senso(self, text, speaker, timestamp):
    # ... existing code ...
```

### Step 6.2: Add Health Monitoring

Create `healthcheck.py`:

```python
import requests
import sys

try:
    # Check if process is running
    import psutil
    processes = [p for p in psutil.process_iter() if 'audio_worker.py' in ' '.join(p.cmdline())]

    if not processes:
        print("Audio worker not running")
        sys.exit(1)

    print("Audio worker healthy")
    sys.exit(0)

except Exception as e:
    print(f"Health check failed: {e}")
    sys.exit(1)
```

### Step 6.3: Add Logging to File

Update `audio_worker.py`:

```python
# Configure logging with file output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("audio_worker.log"),
        logging.StreamHandler()
    ]
)
```

### Step 6.4: Environment-Specific Configs

Create `config.py`:

```python
import os
from dataclasses import dataclass

@dataclass
class Config:
    SENSO_API_KEY: str = os.getenv('SENSO_API_KEY')
    WHISPER_MODEL: str = os.getenv('WHISPER_MODEL', 'tiny')
    CHUNK_DURATION: int = int(os.getenv('CHUNK_DURATION', 5))
    SAMPLE_RATE: int = int(os.getenv('SAMPLE_RATE', 16000))
    ENVIRONMENT: str = os.getenv('ENVIRONMENT', 'development')

    @property
    def is_production(self):
        return self.ENVIRONMENT == 'production'
```

### Step 6.5: Production Checklist

- [ ] API key stored in secrets manager (not .env)
- [ ] Retry logic implemented for API calls
- [ ] Health checks configured
- [ ] Logging to file and/or external service
- [ ] Resource limits set in docker-compose.yml
- [ ] Monitoring dashboard (Grafana, Datadog, etc.)
- [ ] Alerts configured for failures
- [ ] Backup strategy for critical failures
- [ ] Documentation updated

**📚 Reference**: See `insights/05-docker-setup.md` for production deployment.

---

## Troubleshooting

### Issue: "No module named 'sounddevice'"

**Solution**:
```bash
# Install PortAudio
brew install portaudio  # macOS
sudo apt-get install portaudio19-dev  # Linux

# Reinstall sounddevice
pip install --force-reinstall sounddevice
```

### Issue: "Microphone not accessible"

**Solution**:
- **macOS**: System Preferences → Security & Privacy → Microphone → Enable for Terminal/IDE
- **Linux**: Add user to audio group: `sudo usermod -a -G audio $USER`
- **Docker**: Add `privileged: true` to docker-compose.yml

### Issue: "401 Unauthorized from Senso.ai"

**Solution**:
- Verify API key in `.env` has no quotes or spaces
- Check key is valid: `echo $SENSO_API_KEY`
- Request new key from support@senso.ai

### Issue: "Whisper model download fails"

**Solution**:
```bash
# Manually download model
python -c "import whisper; whisper.load_model('tiny')"

# Or specify cache directory
export WHISPER_CACHE_DIR=~/.cache/whisper
```

### Issue: High CPU usage

**Solution**:
- Use smaller model: `WHISPER_MODEL=tiny`
- Increase chunk duration: `CHUNK_DURATION=10`
- Enable GPU if available (install PyTorch with CUDA)

### Issue: Poor transcription quality

**Solution**:
- Upgrade model: `WHISPER_MODEL=base` or `small`
- Improve microphone quality
- Reduce background noise
- Adjust sample rate: `SAMPLE_RATE=44100`

**📚 Reference**: See `insights/06-testing-guide.md` for debugging tools.

---

## Next Steps

### Immediate Enhancements

1. **Real Speaker Diarization**
   ```bash
   pip install pyannote.audio
   ```
   See `insights/04-audio-worker-implementation.md` for implementation.

2. **Context Retrieval**
   - Build search function using Senso.ai `/search` endpoint
   - Integrate with decision-making agent

3. **Multi-language Support**
   ```python
   result = self.model.transcribe(audio, language=None)  # Auto-detect
   ```

### Future Modules

Based on the original conversation assistant architecture:

1. **Context Manager** - Aggregates transcription context for decision-making
2. **Decision Agent** - Analyzes context and determines actions
3. **Action Executor** - Executes decisions (notifications, summaries, etc.)
4. **Feedback Loop** - Learns from user interactions

### Advanced Features

- **Real-time streaming** instead of chunks
- **WebSocket API** for live transcription feed
- **Multi-speaker clustering** for better diarization
- **Sentiment analysis** on transcriptions
- **Custom wake word detection**
- **Integration with calendar/tasks** for actionable insights

---

## Resources

### Documentation
- **Project Overview**: `insights/01-project-overview.md`
- **Requirements**: `insights/02-requirements.md`
- **API Integration**: `insights/03-senso-api-integration.md`
- **Implementation**: `insights/04-audio-worker-implementation.md`
- **Docker Setup**: `insights/05-docker-setup.md`
- **Testing Guide**: `insights/06-testing-guide.md`

### External Links
- [Senso.ai Documentation](https://senso.ai)
- [OpenAI Whisper](https://github.com/openai/whisper)
- [sounddevice Documentation](https://python-sounddevice.readthedocs.io/)
- [Docker Documentation](https://docs.docker.com/)

### Support
- Senso.ai API: support@senso.ai
- Project Issues: Create GitHub issue
- Community: [Add Discord/Slack link]

---

## Conclusion

You now have a complete implementation guide for the Hey Listen Audio Worker! Follow the phases sequentially, validate at each step, and refer to the detailed documentation in the `insights/` folder for deep dives.

**Quick Start Command**:
```bash
# After completing Phase 1-3
python src/audio_worker.py
```

**Docker Start Command**:
```bash
# After completing Phase 5
docker-compose up
```

Happy building! 🎧🤖
