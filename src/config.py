import os
from dataclasses import dataclass


@dataclass
class Config:
    # Pinecone
    PINECONE_API_KEY: str = os.getenv('PINECONE_API_KEY', '')
    PINECONE_ENVIRONMENT: str = os.getenv('PINECONE_ENVIRONMENT', '')
    PINECONE_INDEX_NAME: str = os.getenv('PINECONE_INDEX_NAME', 'realtime')
    EMBEDDING_MODEL: str = os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
    VECTOR_DIMENSION: int = int(os.getenv('VECTOR_DIMENSION', 256))
    MAX_RECORDS: int = int(os.getenv('MAX_RECORDS', 120))
    WHISPER_MODEL: str = os.getenv('WHISPER_MODEL', 'tiny')
    CHUNK_DURATION: int = int(os.getenv('CHUNK_DURATION', 15))
    SAMPLE_RATE: int = int(os.getenv('SAMPLE_RATE', 16000))
    ENVIRONMENT: str = os.getenv('ENVIRONMENT', 'development')

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == 'production'
