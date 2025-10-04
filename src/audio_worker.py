"""
Audio Worker for Hey Listen
Captures audio, transcribes with Whisper, and ingests to Senso.ai
"""

import os
import time
import logging

import numpy as np
import requests
import sounddevice as sd
import whisper
from typing import Optional
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("audio_worker.log"),
        logging.StreamHandler()
    ]
)


class AudioWorker:
    """
    Continuous audio transcription worker with Senso.ai integration.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        sample_rate: Optional[int] = None,
        chunk_duration: Optional[int] = None,
    ) -> None:
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

    def capture_audio(self) -> Optional[np.ndarray]:
        """
        Capture audio chunk from microphone.

        Returns:
            numpy.ndarray | None: Audio samples, or None if capture fails
        """
        try:
            logging.debug(
                f"Capturing {self.chunk_duration}s audio at {self.sample_rate}Hz"
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

    def transcribe_audio(self, audio: np.ndarray) -> str:
        """
        Transcribe audio using Whisper.

        Args:
            audio (numpy.ndarray): Audio samples

        Returns:
            str: Transcribed text, or empty string if transcription fails
        """
        try:
            result = self.model.transcribe(
                audio,
                language="en",
                fp16=False  # Disable FP16 for CPU compatibility
            )

            text = result.get("text", "").strip()

            if text:
                logging.debug(f"Transcribed: {text[:50]}...")

            return text

        except Exception as e:
            logging.error(f"Transcription failed: {e}")
            return ""

    def diarize(self, audio: np.ndarray) -> str:
        """
        Perform basic speaker diarization.

        TODO: Implement real diarization with pyannote.audio

        Args:
            audio (numpy.ndarray): Audio samples

        Returns:
            str: Speaker label (A, B, C, etc.)
        """
        # Placeholder: Always return Speaker A
        return "A"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def ingest_to_senso(self, text: str, speaker: str, timestamp: float) -> Optional[str]:
        """
        Ingest transcription to Senso.ai knowledge base.

        Args:
            text (str): Transcribed text
            speaker (str): Speaker identifier
            timestamp (float): Unix timestamp

        Returns:
            str | None: Content ID if successful, None otherwise
        """
        # Validate API key
        if not self.api_key:
            logging.error("Cannot ingest: SENSO_API_KEY not set")
            return None

        # Skip empty transcriptions
        if not text or not text.strip():
            logging.debug("Skipping empty transcription")
            return None

        # Format timestamp for human readability
        time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))

        payload = {
            "title": f"Transcription - Speaker {speaker} at {time_str}",
            "summary": f"Transcript from {speaker}: {text[:100]}...",
            "text": f"**Speaker {speaker}:** {text}\n\n*Timestamp: {timestamp}*",
        }

        try:
            response = requests.post(
                "https://sdk.senso.ai/api/v1/content/raw",
                headers={
                    "X-API-Key": self.api_key or "",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=10,
            )
            response.raise_for_status()

            data = response.json()
            content_id = data.get("id")
            status = data.get("processing_status", "unknown")

            logging.info(f"\u2713 Ingested to Senso: {content_id} (Status: {status})")
            time.sleep(2)

            return content_id

        except requests.exceptions.HTTPError as e:
            try:
                status_code = e.response.status_code if e.response is not None else 'N/A'
                body = e.response.text if e.response is not None else ''
            except Exception:
                status_code = 'N/A'
                body = ''
            logging.error(f"\u2717 HTTP Error during ingest: {status_code} - {body}")
            return None
        except requests.exceptions.RequestException as e:
            logging.error(f"\u2717 Network error during ingest: {e}")
            return None
        except Exception as e:
            logging.error(f"\u2717 Unexpected error during ingest: {e}")
            return None

    def run(self) -> None:
        """Main loop: continuously capture, transcribe, and ingest audio."""
        logging.info("=" * 60)
        logging.info("Starting Hey Listen Audio Worker")
        logging.info(f"Model: {os.getenv('WHISPER_MODEL', 'tiny')}")
        logging.info(f"Chunk Duration: {self.chunk_duration}s")
        logging.info(f"Sample Rate: {self.sample_rate}Hz")
        logging.info(f"API Key Set: {'Yes' if self.api_key else 'No'}")
        logging.info("=" * 60)

        if not self.api_key:
            logging.warning(
                "Running in LOCAL MODE (no Senso.ai ingestion). Set SENSO_API_KEY in .env to enable cloud storage."
            )

        logging.info("Listening... Press Ctrl+C to stop")

        try:
            while True:
                audio = self.capture_audio()
                if audio is None:
                    logging.warning("Audio capture failed, retrying...")
                    time.sleep(1)
                    continue

                text = self.transcribe_audio(audio)
                if not text:
                    logging.debug("No speech detected, continuing...")
                    continue

                speaker = self.diarize(audio)

                timestamp = time.time()
                content_id = self.ingest_to_senso(text, speaker, timestamp) if self.api_key else None

                if content_id:
                    logging.info(f"[{speaker}] {text[:60]}... → {content_id}")
                else:
                    logging.info(f"[{speaker}] {text[:60]}... → LOCAL ONLY")

                time.sleep(0.1)

        except KeyboardInterrupt:
            logging.info("\n" + "=" * 60)
            logging.info("Shutting down Audio Worker")
            logging.info("=" * 60)


def main() -> None:
    """Entry point for the Audio Worker."""
    worker = AudioWorker()
    worker.run()


if __name__ == "__main__":
    main()
