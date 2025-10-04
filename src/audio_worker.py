"""
Audio Worker for Hey Listen
Captures audio, transcribes with Whisper, and stores metadata in Pinecone
"""

import os
import time
import logging

import numpy as np
import sounddevice as sd
import whisper
from typing import Optional
from dotenv import load_dotenv
from pinecone_manager import PineconeManager

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
    Continuous audio transcription worker with Pinecone integration.
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

        # Pinecone configuration
        self.pinecone_manager: Optional[PineconeManager] = None
        if os.getenv('PINECONE_API_KEY'):
            try:
                self.pinecone_manager = PineconeManager()
                logging.info("Pinecone initialized")
            except Exception as e:
                logging.error(f"Pinecone initialization failed: {e}")
        else:
            logging.warning("PINECONE_API_KEY not set in .env file. Pinecone disabled.")

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

    # Senso ingestion removed. Pinecone storage is handled asynchronously in run().

    def run(self) -> None:
        """Main loop: continuously capture, transcribe, and ingest audio."""
        logging.info("=" * 60)
        logging.info("Starting Hey Listen Audio Worker")
        logging.info(f"Model: {os.getenv('WHISPER_MODEL', 'tiny')}")
        logging.info(f"Chunk Duration: {self.chunk_duration}s")
        logging.info(f"Sample Rate: {self.sample_rate}Hz")
        logging.info(f"Pinecone Enabled: {'Yes' if self.pinecone_manager else 'No'}")
        logging.info("=" * 60)

        if not self.pinecone_manager:
            logging.warning("Running without Pinecone storage (set PINECONE_API_KEY to enable)")

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

                # Schedule async storage to Pinecone (non-blocking)
                if self.pinecone_manager:
                    future = self.pinecone_manager.store_transcription_async(text, speaker, timestamp)
                    status = self.pinecone_manager.check_storage_status(future)
                    if status == "pending":
                        logging.info(f"[{speaker}] {text[:60]}... → Pinecone: pending")
                    elif status == "success":
                        logging.info(f"[{speaker}] {text[:60]}... → Pinecone: ✓")
                    elif status in ("failed", "error"):
                        logging.warning(f"[{speaker}] {text[:60]}... → Pinecone: ✗")
                    else:
                        logging.info(f"[{speaker}] {text[:60]}... → Pinecone: {status}")
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
