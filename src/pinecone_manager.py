import os
import time
import logging
import concurrent.futures
from typing import Any, Dict, List, Optional, Tuple
from dotenv import load_dotenv


class PineconeManager:
    """
    Manages Pinecone vector storage for transcriptions with simple FIFO control.

    Notes:
    - Imports for heavy dependencies are done lazily inside methods/constructor
      to avoid import errors when the environment is not configured yet.
    - FIFO eviction uses a heuristic query to find a candidate to evict when the
      index size exceeds the configured limit. Exact oldest selection is not
      guaranteed without a separate ordering store.
    """

    def __init__(self) -> None:
        # Load environment variables from .env file
        load_dotenv()
        
        # Read environment configuration
        self.api_key: Optional[str] = os.getenv("PINECONE_API_KEY")
        self.environment: Optional[str] = os.getenv("PINECONE_ENVIRONMENT")
        self.index_name: str = os.getenv("PINECONE_INDEX_NAME", "hey-listen-transcriptions")
        self.embedding_model_name: str = os.getenv(
            "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
        )
        self.vector_dimension: int = int(os.getenv("VECTOR_DIMENSION", 384))
        self.max_records: int = int(os.getenv("MAX_RECORDS", 1000))

        if not self.api_key or not self.environment:
            raise ValueError(
                "Pinecone is not configured. PINECONE_API_KEY and PINECONE_ENVIRONMENT are required."
            )

        # Lazy imports
        try:
            from pinecone import Pinecone  # type: ignore
            from sentence_transformers import SentenceTransformer  # type: ignore
        except Exception as e:  # pragma: no cover - surfaced to callers
            raise RuntimeError(
                "Missing dependencies for Pinecone. Install 'pinecone-client' and 'sentence-transformers'."
            ) from e

        # Initialize Pinecone client
        self.pc = Pinecone(api_key=self.api_key)

        # Create or get the index
        existing_indexes = [idx.name for idx in self.pc.list_indexes()]
        if self.index_name not in existing_indexes:
            logging.info(
                f"Creating Pinecone index '{self.index_name}' (dim={self.vector_dimension}, metric=cosine)"
            )
            self.pc.create_index(
                name=self.index_name,
                dimension=self.vector_dimension,
                metric="cosine",
            )

        self.index = self.pc.Index(self.index_name)

        # Load embedding model once
        self._embedding_model = SentenceTransformer(self.embedding_model_name)

        # Thread pool for non-blocking upserts
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)

    # ---- Embeddings ----
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a given text."""
        vector: List[float] = self._embedding_model.encode(text).tolist()
        return vector

    # ---- Async storage interface ----
    def store_transcription_async(self, text: str, speaker: str, timestamp: float):
        """
        Schedule asynchronous storage of a transcription with FIFO management.
        Returns a Future-like object or None if skipped.
        """
        if not text or not text.strip():
            logging.debug("Skipping empty transcription")
            return None

        future = self._executor.submit(self._upsert_transcription_sync, text, speaker, timestamp)
        return future

    def check_storage_status(self, future) -> str:
        """
        Check the status of an async storage operation.
        Returns one of: 'pending' | 'success' | 'failed' | 'error' | 'skipped'.
        """
        if future is None:
            return "skipped"
        if not future.done():
            return "pending"
        try:
            ok: bool = future.result()
            return "success" if ok else "failed"
        except Exception as e:
            logging.error(f"Async storage error: {e}")
            return "error"

    # ---- Internal sync operations ----
    def _upsert_transcription_sync(self, text: str, speaker: str, timestamp: float) -> bool:
        try:
            # Prepare vector and metadata
            vector = self.generate_embedding(text)
            time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
            metadata: Dict[str, Any] = {
                "text": text,
                "speaker": speaker,
                "timestamp": float(timestamp),
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(timestamp)),
                "title": f"Transcription - Speaker {speaker} at {time_str}",
                "summary": f"Transcript from {speaker}: {text[:100]}...",
            }

            vector_id = f"transcript_{int(timestamp)}_{speaker}"

            # Enforce simple FIFO limit
            if self._should_evict():
                self._evict_one_candidate()

            # Upsert new record
            self.index.upsert([(vector_id, vector, metadata)])
            logging.info(f"Pinecone upsert completed: {vector_id}")
            return True
        except Exception as e:
            logging.error(f"Pinecone upsert failed: {e}")
            return False

    def _should_evict(self) -> bool:
        try:
            stats = self.index.describe_index_stats()
            total = getattr(stats, "total_vector_count", None)
            if total is None and isinstance(stats, dict):  # fallback if dict-like
                total = stats.get("total_vector_count")
            return bool(total and int(total) >= self.max_records)
        except Exception as e:
            logging.warning(f"Could not determine index size for FIFO: {e}")
            return False

    def _evict_one_candidate(self) -> None:
        """
        Evict a candidate vector when over capacity. Heuristic approach:
        query a small set and delete the one with the smallest 'timestamp'.
        """
        try:
            # Query a small sample to pick an oldest candidate
            dummy = [0.0] * self.vector_dimension
            res = self.index.query(
                vector=dummy,
                top_k=10,
                include_metadata=True,
                filter={"timestamp": {"$gte": 0}},
            )

            matches: List[Any] = getattr(res, "matches", []) or []
            if not matches:
                return

            def match_tuple(m: Any) -> Tuple[float, str]:
                meta = getattr(m, "metadata", {}) or {}
                ts = meta.get("timestamp", time.time())
                mid = getattr(m, "id", None) or meta.get("id") or ""
                return float(ts), str(mid)

            oldest = min(matches, key=lambda m: match_tuple(m)[0])
            _, oldest_id = match_tuple(oldest)
            if oldest_id:
                self.index.delete(ids=[oldest_id])
                logging.info(f"Evicted vector (FIFO heuristic): {oldest_id}")
        except Exception as e:
            logging.warning(f"FIFO eviction skipped due to error: {e}")
