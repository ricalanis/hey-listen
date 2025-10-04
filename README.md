# Hey Listen - Audio Transcription System

Real-time audio transcription system that captures conversations, transcribes them with Whisper, and optionally ingests results into Senso.ai for retrieval.

### What's in this repo right now
- Python worker in `src/audio_worker.py` with:
  - Microphone capture via `sounddevice`
  - Whisper transcription
  - Basic diarization placeholder
  - Senso.ai ingestion with retries (`tenacity`)
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
# Senso.ai API Configuration
SENSO_API_KEY=your_api_key_here   # optional for LOCAL MODE

# Whisper Model (tiny, base, small, medium, large)
WHISPER_MODEL=tiny

# Audio Configuration
CHUNK_DURATION=5      # seconds
SAMPLE_RATE=16000     # Hz
```
Notes:
- If `SENSO_API_KEY` is not set, the worker runs in LOCAL MODE (no ingestion) and still logs transcriptions.

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
3) With `SENSO_API_KEY` set, successful ingests show a content ID

### Verify Senso.ai storage (optional)
```bash
curl -X POST https://sdk.senso.ai/api/v1/search \
  -H "X-API-Key: $SENSO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "recent transcriptions from the last hour", "max_results": 5}'
```

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
- Ensure `.env` in the repo root contains `SENSO_API_KEY` if you want ingestion; it is mounted read-only into the container.

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
│   ├── 03-senso-api-integration.md
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
SENSO_API_KEY=...      # optional; enables ingestion when set
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
- **401 from Senso.ai**: Verify `SENSO_API_KEY` has no quotes/spaces and is valid.
- **High CPU usage**: Use a smaller model (`WHISPER_MODEL=tiny`) or increase `CHUNK_DURATION`.

## Optional: Agent-based automation
See `AGENTS.md` for an agent-driven, step-by-step implementation guide. This is optional and not required for local testing.

## Support
- Senso.ai API: support@senso.ai
- Documentation: see the `insights/` folder

