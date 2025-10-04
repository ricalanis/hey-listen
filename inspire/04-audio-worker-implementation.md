# Audio Worker Implementation Guide

## Overview

The Audio Worker is the core service that continuously captures audio, transcribes it using Whisper, performs basic speaker diarization, and ingests the results into Senso.ai. This guide provides the complete implementation.

## Architecture

```
┌──────────────────────────────────────────────────┐
│              AudioWorker Class                    │
├──────────────────────────────────────────────────┤
│                                                   │
│  ┌─────────────┐    ┌──────────────┐            │
│  │   capture   │───▶│  transcribe  │            │
│  │   _audio()  │    │   _audio()   │            │
│  └─────────────┘    └──────┬───────┘            │
│                             │                     │
│                             ▼                     │
│                    ┌─────────────┐               │
│                    │  diarize()  │               │
│                    └──────┬──────┘               │
│                           │                       │
│                           ▼                       │
│                  ┌──────────────────┐            │
│                  │ ingest_to_senso()│            │
│                  └──────────────────┘            │
│                           │                       │
└───────────────────────────┼───────────────────────┘
                            ▼
                    Senso.ai Knowledge Base
```

## Implementation Steps

### Step 1: Project Structure Setup

Create the following directory structure:

```bash
hey-listen/
├── src/
│   └── audio_worker.py
├── .env.example
├── .gitignore
└── requirements.txt
```

### Step 2: Environment Configuration

#### File: `.env.example`

```bash
# Senso.ai API Configuration
SENSO_API_KEY=your_api_key_here

# Whisper Configuration
WHISPER_MODEL=tiny

# Audio Configuration
CHUNK_DURATION=5
SAMPLE_RATE=16000
```

#### File: `.gitignore`

```
# Environment
.env

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# Virtual Environment
venv/
env/
ENV/

# IDEs
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Whisper models cache
~/.cache/whisper/
```

**Action**: Copy `.env.example` to `.env` and add your real API key

```bash
cp .env.example .env
# Edit .env with your Senso.ai API key
```

### Step 3: Dependencies Installation

#### File: `requirements.txt`

```txt
openai-whisper==20230124
sounddevice==0.4.6
numpy==1.24.3
requests==2.31.0
python-dotenv==1.0.0
```

#### Install System Dependencies

**macOS**:
```bash
brew install portaudio
```

**Ubuntu/Debian**:
```bash
sudo apt-get update
sudo apt-get install portaudio19-dev python3-pyaudio
```

**Windows**: PortAudio is bundled with sounddevice pip package

#### Install Python Dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Note**: First run will download Whisper model (~75MB for `tiny` model)

### Step 4: Core Implementation

#### File: `src/audio_worker.py`

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
        """
        Initialize the Audio Worker.

        Args:
            model_name (str): Whisper model size (tiny, base, small, medium, large)
            sample_rate (int): Audio sample rate in Hz
            chunk_duration (int): Audio chunk duration in seconds
        """
        # Load environment variables
        load_dotenv()

        # API Configuration
        self.api_key = os.getenv('SENSO_API_KEY')
        if not self.api_key:
            logging.warning(
                "SENSO_API_KEY not set in .env file. "
                "Transcriptions will not be ingested."
            )

        # Audio Configuration
        self.sample_rate = sample_rate or int(os.getenv('SAMPLE_RATE', 16000))
        self.chunk_duration = chunk_duration or int(os.getenv('CHUNK_DURATION', 5))

        # Whisper Model
        model_name = model_name or os.getenv('WHISPER_MODEL', 'tiny')
        logging.info(f"Loading Whisper model: {model_name}")
        self.model = whisper.load_model(model_name)
        logging.info("Whisper model loaded successfully")

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

    def diarize(self, audio):
        """
        Perform basic speaker diarization.

        TODO: Implement real diarization with pyannote.audio or clustering

        Args:
            audio (numpy.ndarray): Audio samples

        Returns:
            str: Speaker label (A, B, C, etc.)
        """
        # Placeholder: Always return Speaker A
        # Future enhancement: Use pyannote.audio for real diarization
        return "A"

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


def main():
    """
    Entry point for the Audio Worker.
    """
    worker = AudioWorker()
    worker.run()


if __name__ == "__main__":
    main()
```

## Code Walkthrough

### Class Initialization (`__init__`)
1. **Load environment variables** from `.env` using `python-dotenv`
2. **Check API key** - warn if missing but don't crash (allows local testing)
3. **Configure audio settings** - sample rate (16kHz) and chunk duration (5s)
4. **Load Whisper model** - downloads on first run, cached thereafter

### Audio Capture (`capture_audio`)
- Uses `sounddevice.rec()` to capture mono audio
- Blocks until chunk duration completes (`sd.wait()`)
- Returns flattened numpy array for Whisper processing
- Handles errors gracefully (returns `None`)

### Transcription (`transcribe_audio`)
- Calls Whisper's `transcribe()` method
- Forces English language (`language="en"`)
- Disables FP16 for CPU compatibility
- Returns cleaned text (stripped whitespace)

### Diarization (`diarize`)
- **Current**: Placeholder returning "A"
- **Future**: Integrate pyannote.audio:
  ```python
  from pyannote.audio import Pipeline
  pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization")
  diarization = pipeline(audio)
  # Extract speaker labels from diarization
  ```

### Senso.ai Ingestion (`ingest_to_senso`)
1. **Validate** API key and text
2. **Format** payload with title, summary, markdown text
3. **POST** to Senso.ai API
4. **Handle errors** - HTTP, network, unexpected
5. **Wait** 2 seconds for indexing
6. **Return** content ID or None

### Main Loop (`run`)
1. **Initialize** - log configuration
2. **Loop infinitely**:
   - Capture 5s audio chunk
   - Transcribe to text
   - Identify speaker (placeholder)
   - Ingest to Senso.ai
   - Log result
3. **Graceful shutdown** on Ctrl+C

## Running the Application

### Local Development

```bash
# Activate virtual environment
source venv/bin/activate

# Set environment variables
cp .env.example .env
# Edit .env with your SENSO_API_KEY

# Run the worker
python src/audio_worker.py
```

**Expected Output**:
```
2025-10-04 12:00:00 - INFO - Loading Whisper model: tiny
2025-10-04 12:00:02 - INFO - Whisper model loaded successfully
============================================================
Starting Hey Listen Audio Worker
Model: tiny
Chunk Duration: 5s
Sample Rate: 16000Hz
API Key Set: Yes
============================================================
2025-10-04 12:00:02 - INFO - Listening... Press Ctrl+C to stop
2025-10-04 12:00:07 - INFO - ✓ Ingested to Senso: content_abc123 (Status: pending)
2025-10-04 12:00:07 - INFO - [A] Hello, this is a test transcription... → content_abc123
```

### Testing Without API Key

Remove `SENSO_API_KEY` from `.env` to test local transcription only:

```
2025-10-04 12:00:00 - WARNING - SENSO_API_KEY not set in .env file...
2025-10-04 12:00:02 - WARNING - Running in LOCAL MODE (no Senso.ai ingestion)...
2025-10-04 12:00:07 - INFO - [A] Hello, this is a test transcription... → LOCAL ONLY
```

## Troubleshooting

### Issue: "No module named 'sounddevice'"
**Solution**: Install PortAudio system library (see Step 3)

### Issue: "OSError: PortAudio library not found"
**Solution**:
- macOS: `brew install portaudio`
- Linux: `sudo apt-get install portaudio19-dev`

### Issue: "Whisper model download fails"
**Solution**: Check internet connection; Whisper downloads ~75MB on first run

### Issue: "401 Unauthorized from Senso.ai"
**Solution**: Verify API key in `.env` is correct (no quotes, no spaces)

### Issue: "Microphone not accessible"
**Solution**: Grant microphone permissions in System Preferences (macOS) or Privacy Settings (Windows/Linux)

### Issue: High CPU usage
**Solution**: Use smaller Whisper model (`tiny` instead of `base`) or increase chunk duration

### Issue: Transcription quality poor
**Solution**: Upgrade to larger model (`base` or `small`), ensure good microphone quality, reduce background noise

## Performance Optimization

### Model Selection
| Model | Size | Speed | Accuracy | Use Case |
|-------|------|-------|----------|----------|
| tiny  | 75MB | Fast  | Lower    | Real-time, low-resource |
| base  | 150MB| Medium| Good     | Balanced performance |
| small | 500MB| Slow  | Better   | Accuracy priority |
| medium| 1.5GB| Slower| High     | GPU recommended |
| large | 3GB  | Slowest| Highest | GPU required |

### Chunk Duration Tuning
- **5 seconds** (default): Good balance, ~10s total latency
- **3 seconds**: Faster feedback, may reduce accuracy
- **10 seconds**: Better accuracy, higher latency

### Async Processing (Future Enhancement)
```python
import asyncio
import aiohttp

async def ingest_async(text, speaker, timestamp):
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            return await resp.json()
```

## Next Steps

- [ ] Implement real speaker diarization (see `06-testing-guide.md` for pyannote.audio setup)
- [ ] Add retry logic with exponential backoff
- [ ] Containerize with Docker (see `05-docker-setup.md`)
- [ ] Implement context retrieval for decision-making agent
- [ ] Add batch ingestion for high-volume scenarios

Proceed to `05-docker-setup.md` for containerization.
