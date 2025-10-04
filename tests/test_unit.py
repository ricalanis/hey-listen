import os
import sys
from unittest.mock import Mock, patch

import pytest

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from audio_worker import AudioWorker


@patch('audio_worker.whisper.load_model')
@patch.dict(os.environ, {"SENSO_API_KEY": "test_key"}, clear=False)
def test_init_loads_env_and_model(mock_load_model):
    mock_load_model.return_value = Mock()
    worker = AudioWorker()
    assert worker.api_key == "test_key"
    assert worker.sample_rate == 16000
    assert worker.chunk_duration == 5
    mock_load_model.assert_called()


@patch('audio_worker.whisper.load_model')
@patch('audio_worker.sd.rec')
@patch('audio_worker.sd.wait')
def test_capture_audio_success(mock_wait, mock_rec, mock_load_model):
    mock_load_model.return_value = Mock()
    worker = AudioWorker()
    # simulate 5 seconds at 16kHz mono
    import numpy as np
    dummy = np.zeros((worker.sample_rate * worker.chunk_duration, 1), dtype='float32')
    mock_rec.return_value = dummy

    audio = worker.capture_audio()
    assert audio is not None
    assert audio.ndim == 1
    assert len(audio) == worker.sample_rate * worker.chunk_duration


@patch('audio_worker.whisper.load_model')
@patch('audio_worker.AudioWorker.transcribe_audio')
@patch('audio_worker.AudioWorker.capture_audio')
@patch('audio_worker.requests.post')
@patch.dict(os.environ, {"SENSO_API_KEY": "test_key"}, clear=False)
def test_run_loop_ingest_flow(mock_post, mock_capture, mock_transcribe, mock_load_model):
    mock_load_model.return_value = Mock()
    worker = AudioWorker()

    # Prepare one successful cycle then KeyboardInterrupt
    import numpy as np
    mock_capture.side_effect = [np.zeros(worker.sample_rate * worker.chunk_duration, dtype='float32'), KeyboardInterrupt()]
    mock_transcribe.return_value = "hello world"

    mock_resp = Mock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {"id": "content_123", "processing_status": "done"}
    mock_post.return_value = mock_resp

    # Run loop once; catch KeyboardInterrupt thrown by our side effect
    try:
        worker.run()
    except KeyboardInterrupt:
        pass

    assert mock_post.called
