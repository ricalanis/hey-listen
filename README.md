# Hey Listen - Audio Transcription System (Pinecone-only)

Real-time audio transcription system that captures conversations, transcribes them with Whisper, and stores results in Pinecone for semantic retrieval. Senso.ai support has been removed.

### What's in this repo right now
- Python worker in `src/audio_worker.py` with:
  - Microphone capture via `sounddevice`
  - Whisper transcription
  - Basic diarization placeholder
  - Pinecone vector storage (async) with simple FIFO control
  - Console and file logging (`audio_worker.log`)
- Dockerfile and `docker-compose.yml` (Linux audio passthrough via `/dev/snd`)
- Unit tests in `tests/test_unit.py`
- Health check script `healthcheck.py`
- Documentation in `insights/`

## Quick Start (Local)

### 1) System dependencies
```bash
# macOS
brew install portaudio

# Ubuntu/Debian (Linux)
sudo apt-get update && sudo apt-get install -y portaudio19-dev python3-pyaudio

# Windows (WSL2)
sudo apt-get install -y portaudio19-dev
```

### 2) Python setup
```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -U pip
pip install -r requirements.txt
```

### 3) Environment variables
Create a `.env` file in the repo root (no template is committed):
```bash
# Pinecone Configuration
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=your_pinecone_environment   # e.g., us-west1-gcp
PINECONE_INDEX_NAME=hey-listen-transcriptions
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
VECTOR_DIMENSION=384
MAX_RECORDS=1000

# Whisper Model (tiny, base, small, medium, large)
WHISPER_MODEL=tiny

# Audio Configuration
CHUNK_DURATION=5      # seconds
SAMPLE_RATE=16000     # Hz
```
Notes:
- If `PINECONE_API_KEY` is not set, the worker runs without storage and still logs transcriptions.

### 4) Run the worker
```bash
python src/audio_worker.py
```
View logs:
```bash
tail -f audio_worker.log
```

### 5) Stop
Press Ctrl+C.

## Testing locally

### Unit tests
```bash
pip install pytest pytest-mock
pytest -q
```

### Manual test
1) Start the worker: `python src/audio_worker.py`
2) Speak a sentence; watch console or `audio_worker.log` for a transcription line
3) With `PINECONE_API_KEY` set, logs show Pinecone upsert status (✓/pending/✗)

### Verify Pinecone setup
- Ensure the index specified by `PINECONE_INDEX_NAME` exists; it will be created automatically if missing.
- In Pinecone console, inspect the index to see vectors and metadata.

## Run with Docker

```bash
docker-compose up --build
# logs
docker-compose logs -f audio-worker
# stop
docker-compose down
```
Notes:
- Linux: `/dev/snd` is passed through and should work out of the box.
- macOS: Docker Desktop does not support `/dev/snd`; run natively instead.
- Ensure `.env` in the repo root contains `PINECONE_API_KEY` and related vars; it is mounted read-only into the container.

## Project structure
```
hey-listen/
├── AGENTS.md
├── Dockerfile
├── README.md
├── docker-compose.yml
├── healthcheck.py
├── insights/
│   ├── 01-project-overview.md
│   ├── 02-requirements.md
│   ├── 07-pinecone-integration.md
│   ├── 04-audio-worker-implementation.md
│   ├── 05-docker-setup.md
│   └── 06-testing-guide.md
├── requirements.txt
├── src/
│   ├── audio_worker.py
│   └── config.py
└── tests/
    └── test_unit.py
```

## Configuration
Key environment variables in `.env` (see above):
```bash
PINECONE_API_KEY=...      # required for Pinecone storage
PINECONE_ENVIRONMENT=...
PINECONE_INDEX_NAME=hey-listen-transcriptions
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
VECTOR_DIMENSION=384
MAX_RECORDS=1000
WHISPER_MODEL=tiny
CHUNK_DURATION=5
SAMPLE_RATE=16000
```

## Health check
```bash
python healthcheck.py
```
Exits 0 if the worker process is running.

## Troubleshooting
- **No module named 'sounddevice'**: Install PortAudio (see System dependencies), then `pip install --force-reinstall sounddevice`.
- **Microphone not accessible (Linux)**: `sudo usermod -a -G audio $USER` and re-login.
- **Pinecone errors**: Verify `PINECONE_API_KEY`/`PINECONE_ENVIRONMENT` are correct and index is reachable.
- **High CPU usage**: Use a smaller model (`WHISPER_MODEL=tiny`) or increase `CHUNK_DURATION`.

## Pinecone setup instructions
1) Create a Pinecone account and project at `https://app.pinecone.io`
2) Create an API key and note your environment (e.g., `us-west1-gcp`)
3) Add variables to `.env` as shown above
4) Run the worker and verify logs show Pinecone initialization

## Support
- Documentation: see the `insights/` folder

