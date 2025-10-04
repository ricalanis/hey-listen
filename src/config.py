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
    def is_production(self) -> bool:
        return self.ENVIRONMENT == 'production'
