# Requirements Specification

## System Requirements

### Hardware Requirements
- **Microphone**: Any standard microphone or built-in device mic
- **RAM**: Minimum 4GB (8GB recommended for faster Whisper models)
- **CPU**: Multi-core processor (GPU optional but recommended for larger Whisper models)
- **Network**: Stable internet connection for Senso.ai API calls

### Software Requirements
- **OS**: macOS, Linux, or Windows with WSL2
- **Docker**: Version 20.10+
- **Docker Compose**: Version 1.29+
- **Python**: 3.9+ (for local development)

## Python Dependencies

Create `requirements.txt`:

```txt
openai-whisper==20230124
sounddevice==0.4.6
numpy==1.24.3
requests==2.31.0
python-dotenv==1.0.0
```

### Dependency Details

1. **openai-whisper==20230124**
   - Purpose: Speech-to-text transcription
   - Model: `tiny` (fastest, lower accuracy) - can upgrade to `base`, `small`, `medium`, or `large`
   - Installation will pull PyTorch and other ML dependencies

2. **sounddevice==0.4.6**
   - Purpose: Real-time audio capture
   - Requires: PortAudio library
   - Platform-specific setup:
     - macOS: `brew install portaudio`
     - Ubuntu: `apt-get install portaudio19-dev`
     - Windows: Included with pip install

3. **numpy==1.24.3**
   - Purpose: Audio data processing
   - Used for array manipulation of audio samples

4. **requests==2.31.0**
   - Purpose: HTTP client for Senso.ai API
   - Simple, synchronous API calls

5. **python-dotenv==1.0.0**
   - Purpose: Environment variable management
   - Loads `.env` file for secure API key storage

## Senso.ai Requirements

### API Key Setup
1. **Request Access**: Contact support@senso.ai to request an organization API key
2. **Key Type**: Organization-scoped (not user-scoped)
3. **Permissions**: Need write access for content ingestion, read for search

### API Quotas & Limits
- **Rate Limits**: Check with Senso.ai support (typically generous for transcription use cases)
- **Content Size**: Raw text endpoint accepts markdown; no explicit size limit mentioned
- **Processing Time**: ~2-5 seconds for content indexing
- **Search**: Returns up to `max_results` chunks per query

### Expected Costs
- Contact Senso.ai for pricing (may vary by usage tier)
- Consider costs for API calls (ingest every 5 seconds during active conversation)

## Environment Configuration

### Required Environment Variables

Create `.env` file:

```bash
# Senso.ai API Key (get from support@senso.ai)
SENSO_API_KEY=your_api_key_here

# Optional: Whisper model size (tiny, base, small, medium, large)
WHISPER_MODEL=tiny

# Optional: Audio chunk duration in seconds
CHUNK_DURATION=5

# Optional: Sample rate for audio capture
SAMPLE_RATE=16000
```

### Security Considerations
- **Never commit** `.env` to version control
- Add `.env` to `.gitignore`
- Use `.env.example` as template for other developers
- In production, use secrets manager (Docker secrets, AWS Secrets Manager, etc.)

## File Structure

Expected project layout:

```
hey-listen/
├── insights/               # Documentation (this folder)
│   ├── 01-project-overview.md
│   ├── 02-requirements.md
│   ├── 03-senso-api-integration.md
│   ├── 04-audio-worker-implementation.md
│   ├── 05-docker-setup.md
│   └── 06-testing-guide.md
├── src/                    # Source code
│   └── audio_worker.py    # Main application
├── .env.example           # Environment template
├── .env                   # Local config (not committed)
├── .gitignore            # Ignore .env, __pycache__, etc.
├── requirements.txt      # Python dependencies
├── Dockerfile            # Container definition
├── docker-compose.yml    # Service orchestration
└── README.md             # Quick start guide
```

## Functional Requirements

### FR1: Audio Capture
- **Must** capture audio continuously in configurable chunks (default 5 seconds)
- **Must** handle microphone access permissions
- **Should** log errors if microphone unavailable

### FR2: Transcription
- **Must** transcribe captured audio using Whisper
- **Must** support English language (extensible to others)
- **Should** filter out empty/silent transcriptions
- **Should** log transcription failures

### FR3: Speaker Diarization
- **Must** assign speaker labels (A, B, C, etc.) - placeholder initially
- **Should** support future integration with pyannote.audio or similar
- **Could** implement basic clustering for multi-speaker detection

### FR4: Senso.ai Ingestion
- **Must** send each transcription to Senso.ai `/content/raw` endpoint
- **Must** format as markdown with speaker and timestamp
- **Must** include title, summary, and text fields
- **Must** handle API errors gracefully (log, don't crash)
- **Should** retry once on network failure
- **Should** wait 2 seconds post-ingest for processing

### FR5: Data Format
Each ingested content must include:
- **Title**: `"Transcription - Speaker {X} at {timestamp}"`
- **Summary**: First 100 characters of text
- **Text**: Markdown formatted:
  ```markdown
  **Speaker {X}:** {transcribed_text}
  *Timestamp: {unix_timestamp}*
  ```

### FR6: Error Handling
- **Must** log all errors to stdout with timestamps
- **Must** continue operation if single transcription fails
- **Must** warn if API key missing but not crash
- **Should** implement exponential backoff for API retries (future)

## Non-Functional Requirements

### NFR1: Performance
- **Latency**: Transcription + ingestion within 10 seconds of speech end
- **CPU Usage**: <50% on modern quad-core CPU with `tiny` model
- **Memory**: <2GB RAM usage

### NFR2: Reliability
- **Uptime**: Service restarts automatically on crash (Docker restart policy)
- **Data Loss**: Accept loss if Senso.ai unreachable (no local backup initially)

### NFR3: Scalability
- **Concurrent Speakers**: Support 1-2 speakers initially (expand with better diarization)
- **Duration**: Unlimited continuous operation

### NFR4: Maintainability
- **Logging**: Structured logs with INFO, ERROR levels
- **Code Style**: PEP 8 compliant
- **Documentation**: Inline comments for complex logic

## Installation Steps Preview

1. Clone repository
2. Create `.env` from `.env.example`
3. Request Senso.ai API key
4. Install PortAudio (platform-specific)
5. Install Python dependencies: `pip install -r requirements.txt`
6. Run locally: `python src/audio_worker.py`
7. OR build Docker: `docker-compose up`

See `04-audio-worker-implementation.md` and `05-docker-setup.md` for detailed steps.

## Validation Checklist

Before development:
- [ ] Senso.ai API key obtained
- [ ] Microphone available and permissions granted
- [ ] Docker installed and running
- [ ] PortAudio installed (for local dev)
- [ ] `.env` file created with API key

Proceed to `03-senso-api-integration.md` for API integration details.
