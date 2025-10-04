# Hey Listen - Audio Transcription System with Senso.ai

## Project Overview

Hey Listen is a real-time audio transcription system that captures spoken conversations, transcribes them using OpenAI's Whisper, and organizes the data using Senso.ai's knowledge base for future retrieval and context management.

## System Architecture

```
┌─────────────────┐
│  Audio Input    │
│  (Microphone)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Audio Worker   │
│  - Capture      │
│  - Transcribe   │
│  - Diarize      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Senso.ai      │
│  Knowledge Base │
│  - Ingest       │
│  - Search       │
│  - Organize     │
└─────────────────┘
```

## Core Components

### 1. Audio Worker
- **Purpose**: Continuous audio capture and processing
- **Technology**: Python, Whisper (local), sounddevice
- **Functions**:
  - Capture audio in 5-second chunks
  - Transcribe speech to text
  - Basic speaker diarization (placeholder: Speaker A, B, C)
  - Send transcriptions to Senso.ai

### 2. Senso.ai Integration
- **Purpose**: Long-term knowledge organization and retrieval
- **API Base**: `https://sdk.senso.ai/api/v1`
- **Key Endpoints**:
  - `POST /content/raw` - Ingest transcriptions
  - `POST /search` - Query knowledge base
- **Authentication**: Organization-scoped API key via `X-API-Key` header

### 3. Docker Environment
- **Purpose**: Containerized deployment
- **Services**:
  - audio-worker: Main transcription service
- **Requirements**:
  - Microphone access (`/dev/snd`)
  - Environment variable for API key
  - Network access for Senso.ai API

## Key Features

1. **Real-time Transcription**: Continuous 5-second audio chunk processing
2. **Cloud Storage**: All transcriptions stored in Senso.ai knowledge base
3. **Searchable Archive**: AI-powered natural language search
4. **Speaker Awareness**: Basic diarization support (extensible)
5. **Containerized**: Easy deployment via Docker Compose

## Technology Stack

- **Python 3.9**: Core runtime
- **OpenAI Whisper**: Speech-to-text (tiny model for speed)
- **sounddevice**: Audio capture
- **requests**: HTTP API client
- **python-dotenv**: Environment configuration
- **Docker**: Containerization

## Project Goals

1. Capture and transcribe conversations in real-time
2. Organize transcriptions for easy retrieval
3. Enable context-aware search across conversation history
4. Maintain speaker identity throughout conversations
5. Provide foundation for future agentic decision-making

## Next Steps

This documentation set will guide you through:
1. Requirements and dependencies
2. Senso.ai API integration
3. Audio worker implementation
4. Docker setup and deployment
5. Testing and verification

Proceed to `02-requirements.md` for detailed specifications.
