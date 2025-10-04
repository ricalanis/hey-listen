# Testing and Verification Guide

## Overview

This guide provides comprehensive testing strategies for the Hey Listen Audio Worker, covering unit tests, integration tests, end-to-end verification, and performance benchmarking.

## Testing Strategy

```
┌─────────────────────────────────────────────────┐
│              Testing Pyramid                     │
├─────────────────────────────────────────────────┤
│                                                  │
│              ┌──────────────┐                   │
│              │  E2E Tests   │                   │
│              └──────────────┘                   │
│         ┌─────────────────────────┐             │
│         │   Integration Tests     │             │
│         └─────────────────────────┘             │
│    ┌──────────────────────────────────┐         │
│    │        Unit Tests                │         │
│    └──────────────────────────────────┘         │
│                                                  │
└─────────────────────────────────────────────────┘
```

## Test Environment Setup

### Test Dependencies

Add to `requirements.txt`:

```txt
# Existing dependencies
openai-whisper==20230124
sounddevice==0.4.6
numpy==1.24.3
requests==2.31.0
python-dotenv==1.0.0

# Test dependencies
pytest==7.4.3
pytest-cov==4.1.0
pytest-mock==3.12.0
responses==0.24.1
```

Install test dependencies:

```bash
pip install -r requirements.txt
```

### Test Project Structure

```
hey-listen/
├── src/
│   └── audio_worker.py
├── tests/
│   ├── __init__.py
│   ├── test_unit.py
│   ├── test_integration.py
│   ├── test_e2e.py
│   └── fixtures/
│       ├── test_audio.wav
│       └── test_audio_silent.wav
├── .env.test
└── pytest.ini
```

### Test Configuration

#### File: `pytest.ini`

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --tb=short
    --cov=src
    --cov-report=html
    --cov-report=term-missing
env_files =
    .env.test
```

#### File: `.env.test`

```bash
# Test environment configuration
SENSO_API_KEY=test_api_key_12345
WHISPER_MODEL=tiny
CHUNK_DURATION=2
SAMPLE_RATE=16000
```

## Unit Tests

### File: `tests/test_unit.py`

```python
"""
Unit tests for Audio Worker components
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from audio_worker import AudioWorker


class TestAudioWorkerInit:
    """Test AudioWorker initialization"""

    @patch.dict(os.environ, {"SENSO_API_KEY": "test_key"})
    @patch('audio_worker.whisper.load_model')
    def test_init_with_env_vars(self, mock_load_model):
        """Test initialization with environment variables"""
        mock_load_model.return_value = Mock()

        worker = AudioWorker()

        assert worker.api_key == "test_key"
        assert worker.sample_rate == 16000
        assert worker.chunk_duration == 5
        mock_load_model.assert_called_once_with("tiny")

    @patch.dict(os.environ, {}, clear=True)
    @patch('audio_worker.whisper.load_model')
    def test_init_without_api_key(self, mock_load_model):
        """Test initialization without API key (should warn but not crash)"""
        mock_load_model.return_value = Mock()

        worker = AudioWorker()

        assert worker.api_key is None

    @patch('audio_worker.whisper.load_model')
    def test_init_custom_params(self, mock_load_model):
        """Test initialization with custom parameters"""
        mock_load_model.return_value = Mock()

        worker = AudioWorker(
            model_name="base",
            sample_rate=22050,
            chunk_duration=10
        )

        assert worker.sample_rate == 22050
        assert worker.chunk_duration == 10
        mock_load_model.assert_called_once_with("base")


class TestAudioCapture:
    """Test audio capture functionality"""

    @patch('audio_worker.sd.rec')
    @patch('audio_worker.sd.wait')
    @patch('audio_worker.whisper.load_model')
    def test_capture_audio_success(self, mock_load_model, mock_wait, mock_rec):
        """Test successful audio capture"""
        mock_load_model.return_value = Mock()
        mock_audio = np.random.rand(80000, 1).astype('float32')
        mock_rec.return_value = mock_audio

        worker = AudioWorker()
        result = worker.capture_audio()

        assert result is not None
        assert isinstance(result, np.ndarray)
        assert result.shape == (80000,)
        mock_rec.assert_called_once()
        mock_wait.assert_called_once()

    @patch('audio_worker.sd.rec')
    @patch('audio_worker.whisper.load_model')
    def test_capture_audio_failure(self, mock_load_model, mock_rec):
        """Test audio capture failure handling"""
        mock_load_model.return_value = Mock()
        mock_rec.side_effect = Exception("Microphone not found")

        worker = AudioWorker()
        result = worker.capture_audio()

        assert result is None


class TestTranscription:
    """Test transcription functionality"""

    @patch('audio_worker.whisper.load_model')
    def test_transcribe_audio_success(self, mock_load_model):
        """Test successful transcription"""
        mock_model = Mock()
        mock_model.transcribe.return_value = {"text": "  Hello world  "}
        mock_load_model.return_value = mock_model

        worker = AudioWorker()
        audio = np.random.rand(80000).astype('float32')
        result = worker.transcribe_audio(audio)

        assert result == "Hello world"
        mock_model.transcribe.assert_called_once()

    @patch('audio_worker.whisper.load_model')
    def test_transcribe_audio_empty(self, mock_load_model):
        """Test transcription with empty result"""
        mock_model = Mock()
        mock_model.transcribe.return_value = {"text": "   "}
        mock_load_model.return_value = mock_model

        worker = AudioWorker()
        audio = np.random.rand(80000).astype('float32')
        result = worker.transcribe_audio(audio)

        assert result == ""

    @patch('audio_worker.whisper.load_model')
    def test_transcribe_audio_failure(self, mock_load_model):
        """Test transcription failure handling"""
        mock_model = Mock()
        mock_model.transcribe.side_effect = Exception("Model error")
        mock_load_model.return_value = mock_model

        worker = AudioWorker()
        audio = np.random.rand(80000).astype('float32')
        result = worker.transcribe_audio(audio)

        assert result == ""


class TestDiarization:
    """Test speaker diarization"""

    @patch('audio_worker.whisper.load_model')
    def test_diarize_placeholder(self, mock_load_model):
        """Test placeholder diarization (always returns A)"""
        mock_load_model.return_value = Mock()

        worker = AudioWorker()
        audio = np.random.rand(80000).astype('float32')
        result = worker.diarize(audio)

        assert result == "A"


class TestSensoIngestion:
    """Test Senso.ai ingestion"""

    @patch('audio_worker.requests.post')
    @patch('audio_worker.time.sleep')
    @patch.dict(os.environ, {"SENSO_API_KEY": "test_key"})
    @patch('audio_worker.whisper.load_model')
    def test_ingest_success(self, mock_load_model, mock_sleep, mock_post):
        """Test successful ingestion to Senso.ai"""
        mock_load_model.return_value = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "content_123",
            "processing_status": "pending"
        }
        mock_post.return_value = mock_response

        worker = AudioWorker()
        result = worker.ingest_to_senso("Hello world", "A", 1728054645.0)

        assert result == "content_123"
        mock_post.assert_called_once()
        mock_sleep.assert_called_once_with(2)

    @patch.dict(os.environ, {}, clear=True)
    @patch('audio_worker.whisper.load_model')
    def test_ingest_no_api_key(self, mock_load_model):
        """Test ingestion without API key"""
        mock_load_model.return_value = Mock()

        worker = AudioWorker()
        result = worker.ingest_to_senso("Hello world", "A", 1728054645.0)

        assert result is None

    @patch('audio_worker.requests.post')
    @patch.dict(os.environ, {"SENSO_API_KEY": "test_key"})
    @patch('audio_worker.whisper.load_model')
    def test_ingest_empty_text(self, mock_load_model, mock_post):
        """Test ingestion with empty text (should skip)"""
        mock_load_model.return_value = Mock()

        worker = AudioWorker()
        result = worker.ingest_to_senso("   ", "A", 1728054645.0)

        assert result is None
        mock_post.assert_not_called()

    @patch('audio_worker.requests.post')
    @patch.dict(os.environ, {"SENSO_API_KEY": "test_key"})
    @patch('audio_worker.whisper.load_model')
    def test_ingest_http_error(self, mock_load_model, mock_post):
        """Test ingestion with HTTP error"""
        mock_load_model.return_value = Mock()
        mock_post.side_effect = Exception("Network error")

        worker = AudioWorker()
        result = worker.ingest_to_senso("Hello world", "A", 1728054645.0)

        assert result is None
```

### Run Unit Tests

```bash
# Run all unit tests
pytest tests/test_unit.py

# Run with coverage
pytest tests/test_unit.py --cov=src --cov-report=term-missing

# Run specific test
pytest tests/test_unit.py::TestAudioCapture::test_capture_audio_success -v
```

## Integration Tests

### File: `tests/test_integration.py`

```python
"""
Integration tests for Audio Worker with real Senso.ai API
"""

import pytest
import os
import time
import requests
from unittest.mock import patch
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from audio_worker import AudioWorker


@pytest.fixture
def real_api_key():
    """Get real API key from environment (skip if not set)"""
    api_key = os.getenv('SENSO_API_KEY')
    if not api_key or api_key.startswith('test_'):
        pytest.skip("Real SENSO_API_KEY not set")
    return api_key


class TestSensoAPIIntegration:
    """Test real Senso.ai API integration"""

    def test_ingest_and_search(self, real_api_key):
        """Test full ingest → search flow"""
        # Ingest test content
        payload = {
            "title": "Integration Test Transcription",
            "summary": "Testing Hey Listen integration",
            "text": "**Speaker A:** This is an integration test.\n*Timestamp: 1728054645*"
        }

        response = requests.post(
            "https://sdk.senso.ai/api/v1/content/raw",
            headers={
                "X-API-Key": real_api_key,
                "Content-Type": "application/json"
            },
            json=payload
        )

        assert response.status_code == 201
        content_id = response.json()["id"]
        assert content_id is not None

        # Wait for indexing
        time.sleep(5)

        # Search for ingested content
        search_response = requests.post(
            "https://sdk.senso.ai/api/v1/search",
            headers={
                "X-API-Key": real_api_key,
                "Content-Type": "application/json"
            },
            json={
                "query": "integration test transcription",
                "max_results": 5
            }
        )

        assert search_response.status_code == 200
        results = search_response.json()
        assert len(results.get("results", [])) > 0

    @patch('audio_worker.whisper.load_model')
    def test_worker_ingest_real_api(self, mock_load_model, real_api_key):
        """Test AudioWorker ingest with real API"""
        mock_load_model.return_value = Mock()

        worker = AudioWorker()
        worker.api_key = real_api_key

        content_id = worker.ingest_to_senso(
            "Integration test from AudioWorker",
            "B",
            time.time()
        )

        assert content_id is not None
        assert content_id.startswith("content_")
```

### Run Integration Tests

```bash
# Set real API key
export SENSO_API_KEY=your_real_api_key

# Run integration tests
pytest tests/test_integration.py -v

# Skip integration tests (for CI without API key)
pytest tests/test_integration.py -m "not integration"
```

## End-to-End Tests

### File: `tests/test_e2e.py`

```python
"""
End-to-end tests with real audio files
"""

import pytest
import os
import numpy as np
import soundfile as sf
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from audio_worker import AudioWorker


@pytest.fixture
def test_audio_file():
    """Create a test audio file"""
    # Generate 3 seconds of 440Hz sine wave (A note)
    sample_rate = 16000
    duration = 3
    frequency = 440
    t = np.linspace(0, duration, sample_rate * duration)
    audio = 0.5 * np.sin(2 * np.pi * frequency * t)

    filepath = "tests/fixtures/test_audio.wav"
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    sf.write(filepath, audio, sample_rate)

    yield filepath

    # Cleanup
    if os.path.exists(filepath):
        os.remove(filepath)


class TestE2E:
    """End-to-end workflow tests"""

    def test_full_pipeline_with_audio_file(self, test_audio_file):
        """Test complete pipeline with audio file"""
        worker = AudioWorker()

        # Load test audio
        audio, _ = sf.read(test_audio_file)

        # Transcribe
        text = worker.transcribe_audio(audio)

        # Note: Whisper might not transcribe pure tone,
        # but should not crash
        assert isinstance(text, str)

    def test_spoken_audio_transcription(self):
        """Test with real spoken audio (if available)"""
        # This requires a pre-recorded sample with speech
        audio_path = "tests/fixtures/spoken_sample.wav"

        if not os.path.exists(audio_path):
            pytest.skip("Spoken audio sample not available")

        worker = AudioWorker()
        audio, _ = sf.read(audio_path)
        text = worker.transcribe_audio(audio)

        assert len(text) > 0
        # Add assertions based on known content
        # e.g., assert "hello" in text.lower()
```

### Create Test Audio Fixtures

```bash
# Create fixtures directory
mkdir -p tests/fixtures

# Record a test sample (speak for 3 seconds)
arecord -d 3 -f cd tests/fixtures/spoken_sample.wav

# Or use a pre-generated file from online resources
```

### Run E2E Tests

```bash
pytest tests/test_e2e.py -v
```

## Performance Testing

### File: `tests/test_performance.py`

```python
"""
Performance and benchmarking tests
"""

import pytest
import time
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from audio_worker import AudioWorker


class TestPerformance:
    """Performance benchmarks"""

    @pytest.mark.benchmark
    def test_transcription_latency(self):
        """Measure transcription latency"""
        worker = AudioWorker(model_name="tiny")
        audio = np.random.rand(80000).astype('float32')  # 5 seconds

        start = time.time()
        text = worker.transcribe_audio(audio)
        latency = time.time() - start

        print(f"\nTranscription latency: {latency:.2f}s")
        assert latency < 10  # Should complete within 10 seconds

    @pytest.mark.benchmark
    def test_capture_overhead(self):
        """Measure audio capture overhead"""
        worker = AudioWorker()

        start = time.time()
        audio = worker.capture_audio()
        overhead = time.time() - start - worker.chunk_duration

        print(f"\nCapture overhead: {overhead:.3f}s")
        assert overhead < 1  # Overhead should be minimal

    @pytest.mark.benchmark
    def test_full_cycle_latency(self):
        """Measure full capture → transcribe → ingest cycle"""
        worker = AudioWorker()

        start = time.time()

        # Simulate full cycle (mock capture for speed)
        audio = np.random.rand(80000).astype('float32')
        text = worker.transcribe_audio(audio)
        speaker = worker.diarize(audio)
        # Skip actual ingest for benchmark

        total_latency = time.time() - start

        print(f"\nFull cycle latency: {total_latency:.2f}s")
        assert total_latency < 15
```

### Run Performance Tests

```bash
pytest tests/test_performance.py -v -m benchmark
```

## Manual Testing Checklist

### Local Development Testing

- [ ] **Environment Setup**
  ```bash
  cp .env.example .env
  # Add real SENSO_API_KEY
  python src/audio_worker.py
  ```

- [ ] **Microphone Access**
  - Verify system prompts for microphone permission
  - Check logs show "Listening..."

- [ ] **Transcription Quality**
  - Speak clearly: "Hello, this is a test"
  - Check log shows transcribed text
  - Verify accuracy (>80% word accuracy)

- [ ] **Senso.ai Ingestion**
  - Check logs show: `✓ Ingested to Senso: content_xxx`
  - Verify via curl search:
    ```bash
    curl -X POST https://sdk.senso.ai/api/v1/search \
      -H "X-API-Key: $SENSO_API_KEY" \
      -d '{"query":"recent test", "max_results":5}'
    ```

- [ ] **Error Handling**
  - Test without API key (should warn, not crash)
  - Disconnect internet (should log error, continue)
  - Cover microphone (should transcribe silence/empty)

### Docker Testing

- [ ] **Build and Run**
  ```bash
  docker-compose build
  docker-compose up
  ```

- [ ] **Container Health**
  - Check `docker ps` shows running container
  - Logs show same output as local run

- [ ] **Audio Device Access**
  ```bash
  docker-compose exec audio-worker arecord -l
  # Should list microphone devices
  ```

- [ ] **Environment Variables**
  ```bash
  docker-compose exec audio-worker env | grep SENSO
  # Should show SENSO_API_KEY
  ```

### Production Testing

- [ ] **API Rate Limits**
  - Run for 1 hour, monitor for 429 errors
  - Verify retry logic (if implemented)

- [ ] **Resource Usage**
  - Monitor CPU: `docker stats`
  - Should stay < 50% on modern hardware

- [ ] **Memory Leaks**
  - Run overnight
  - Check memory usage doesn't grow indefinitely

- [ ] **Network Resilience**
  - Disconnect internet temporarily
  - Verify graceful degradation

## Continuous Integration Setup

### File: `.github/workflows/test.yml`

```yaml
name: Test Hey Listen

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'

    - name: Install system dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y portaudio19-dev

    - name: Install Python dependencies
      run: |
        pip install -r requirements.txt

    - name: Run unit tests
      run: |
        pytest tests/test_unit.py -v --cov=src --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        files: ./coverage.xml

    # Skip integration tests in CI (no real API key)
    # - name: Run integration tests
    #   env:
    #     SENSO_API_KEY: ${{ secrets.SENSO_API_KEY }}
    #   run: pytest tests/test_integration.py -v
```

## Test Coverage Goals

Target coverage metrics:

| Component | Coverage Target |
|-----------|----------------|
| Overall   | > 80%          |
| Core logic (transcribe, ingest) | > 90% |
| Error handling | 100% |
| Initialization | > 85% |

### Check Coverage

```bash
# Generate HTML coverage report
pytest --cov=src --cov-report=html

# Open in browser
open htmlcov/index.html
```

## Common Test Scenarios

### Scenario 1: Silent Audio
**Expected**: Empty transcription, no ingest

```python
def test_silent_audio():
    worker = AudioWorker()
    silent_audio = np.zeros(80000, dtype='float32')
    text = worker.transcribe_audio(silent_audio)
    assert text == ""
```

### Scenario 2: Multi-speaker Conversation
**Expected**: Different speaker labels (when diarization implemented)

```python
# Future test when diarization is real
def test_multi_speaker():
    # Load multi-speaker audio
    # Verify diarize() returns A, B, C correctly
    pass
```

### Scenario 3: API Failure Recovery
**Expected**: Logs error, continues operation

```python
@patch('requests.post')
def test_api_failure_recovery(mock_post):
    mock_post.side_effect = [Exception("Network error"), Mock()]
    # Verify worker continues after failed ingest
```

## Debugging Tools

### Enable Debug Logging

```python
# In audio_worker.py
logging.basicConfig(level=logging.DEBUG)
```

### Inspect Whisper Output

```python
result = model.transcribe(audio, verbose=True)
print(result)  # Shows segments, timestamps, confidence
```

### Monitor Senso.ai API

```bash
# Check recent ingests
curl -X POST https://sdk.senso.ai/api/v1/search \
  -H "X-API-Key: $SENSO_API_KEY" \
  -d '{"query":"recent", "max_results":10}' | jq
```

## Next Steps

- [ ] Implement real speaker diarization (pyannote.audio)
- [ ] Add retry logic with tenacity
- [ ] Create stress test suite (1000+ ingests)
- [ ] Set up performance monitoring (New Relic, Datadog)
- [ ] Build integration tests for Context Manager (next module)

## Summary

You now have:
- ✅ Comprehensive unit test suite
- ✅ Integration tests with real API
- ✅ E2E tests with audio files
- ✅ Performance benchmarks
- ✅ Manual testing checklist
- ✅ CI/CD pipeline template

Run all tests:
```bash
pytest tests/ -v --cov=src --cov-report=term-missing
```

Your listening module is now fully tested and ready for production deployment!
