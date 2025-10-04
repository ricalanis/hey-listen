# Phase 7: Pinecone Integration - Planning Document

## 🎯 Overview

This document outlines the implementation plan for integrating Pinecone vector database into the Hey Listen Audio Worker system. This phase will replace the existing Senso.ai integration with Pinecone vector storage, providing real-time vector storage capabilities for semantic search and retrieval of transcription data.

## 📋 Table of Contents

1. [Objectives](#objectives)
2. [Architecture Overview](#architecture-overview)
3. [Implementation Phases](#implementation-phases)
4. [Technical Requirements](#technical-requirements)
5. [Data Flow Design](#data-flow-design)
6. [FIFO Storage Strategy](#fifo-storage-strategy)
7. [Implementation Steps](#implementation-steps)
8. [Testing Strategy](#testing-strategy)
9. [Performance Considerations](#performance-considerations)
10. [Monitoring & Observability](#monitoring--observability)
11. [Deployment Updates](#deployment-updates)
12. [Future Enhancements](#future-enhancements)

## Objectives

### Primary Goals
- **Real-time Vector Storage**: Store transcription embeddings in Pinecone every 15 seconds
- **FIFO Management**: Automatically remove oldest records when adding new ones
- **Semantic Search**: Enable similarity-based retrieval of conversation history
- **Single Storage**: Replace Senso.ai with Pinecone as the primary storage solution

### Secondary Goals
- **Performance Optimization**: Minimize latency impact on audio processing
- **Cost Management**: Implement efficient vector storage with automatic cleanup
- **Scalability**: Support high-frequency transcription ingestion
- **Reliability**: Handle Pinecone API failures gracefully

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Audio Input   │───▶│  Audio Worker    │───▶│   Transcription │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   Pinecone       │
                       │   Storage        │
                       │                  │
                       │  ┌─────────────┐ │    ┌─────────────────┐
                       │  │ Vector DB   │──┼──▶│ Semantic Search │
                       │  │ + Metadata  │ │    │ + FIFO Queue    │
                       │  └─────────────┘ │    └─────────────────┘
                       └──────────────────┘
```

## Implementation Phases

### Phase 7.1: Environment Setup (30 min)
- Pinecone account setup and API key configuration
- Dependencies installation and configuration
- Environment variables setup

### Phase 7.2: Core Pinecone Integration (2 hours)
- Pinecone client implementation
- Vector embedding generation
- Basic upsert functionality

### Phase 7.3: FIFO Storage Implementation (1.5 hours)
- Oldest record detection and deletion
- Atomic upsert-delete operations
- Error handling and rollback logic

### Phase 7.4: Audio Worker Integration (1 hour)
- Modify existing audio worker to include Pinecone
- Implement dual storage strategy
- Performance optimization

### Phase 7.5: Testing & Validation (1.5 hours)
- Unit tests for Pinecone operations
- Integration testing with audio worker
- Performance benchmarking

### Phase 7.6: Production Deployment (1 hour)
- Docker configuration updates
- Monitoring and logging enhancements
- Documentation updates

**Total Estimated Time**: 7-8 hours

## Technical Requirements

### Dependencies
```txt
# Add to requirements.txt
pinecone-client==2.2.4
sentence-transformers==2.2.2
openai==1.3.0  # Alternative embedding provider
```

### Environment Variables
```bash
# Add to .env
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=your_environment
PINECONE_INDEX_NAME=hey-listen-transcriptions
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
VECTOR_DIMENSION=384
MAX_RECORDS=1000  # Maximum records to maintain in FIFO
```

### Pinecone Index Configuration
```python
INDEX_CONFIG = {
    "name": "hey-listen-transcriptions",
    "dimension": 384,  # all-MiniLM-L6-v2 dimension
    "metric": "cosine",
    "pods": 1,
    "replicas": 1,
    "pod_type": "p1.x1"
}
```

## Data Flow Design

### 1. Transcription Processing
```
Audio → Whisper → Text → Embedding → Vector + Metadata
```

### 2. Pinecone Storage Strategy
```
Transcription Data → Pinecone (Vector + Metadata)
├── ID: "transcript_1705327825_A"
├── Vector: [0.1, -0.2, 0.3, ...] (384 dimensions)
└── Metadata:
    ├── text: "Hello world"
    ├── speaker: "A"
    ├── timestamp: 1705327825
    ├── created_at: "2024-01-15T14:30:25Z"
    ├── title: "Transcription - Speaker A at 2024-01-15 14:30:25"
    ├── summary: "Transcript from A: Hello world..."
    ├── chunk_duration: 5
    ├── sample_rate: 16000
    └── model: "whisper-tiny"
```

### 3. FIFO Storage Workflow
```
1. Generate embedding from transcription text
2. Query Pinecone for oldest record (min timestamp)
3. Delete oldest record if exists
4. Upsert new record with current timestamp
5. Log operation results
```

## FIFO Storage Strategy

### Implementation Approach
```python
class PineconeFIFO:
    def __init__(self, index, max_records=1000):
        self.index = index
        self.max_records = max_records
    
    async def upsert_with_fifo(self, vector_id, vector, metadata):
        # 1. Check if we need to evict
        if await self._should_evict():
            await self._evict_oldest()
        
        # 2. Upsert new record
        await self.index.upsert([(vector_id, vector, metadata)])
    
    async def _should_evict(self):
        stats = await self.index.describe_index_stats()
        return stats.total_vector_count >= self.max_records
    
    async def _evict_oldest(self):
        # Query for oldest record
        oldest = await self._find_oldest_record()
        if oldest:
            await self.index.delete([oldest.id])
```

### Metadata Schema
```python
METADATA_SCHEMA = {
    "text": str,           # Original transcription text
    "speaker": str,        # Speaker identifier (A, B, C, etc.)
    "timestamp": float,    # Unix timestamp
    "created_at": str,     # ISO format timestamp
    "title": str,          # Human-readable title
    "summary": str,        # Brief summary of transcription
    "chunk_duration": int, # Audio chunk duration in seconds
    "sample_rate": int,    # Audio sample rate
    "model": str,          # Whisper model used
    "confidence": float    # Transcription confidence (if available)
}
```

## Implementation Steps

### Step 7.1: Environment Setup

#### 7.1.1: Pinecone Account Setup
```bash
# 1. Create Pinecone account at https://app.pinecone.io
# 2. Create new project
# 3. Generate API key
# 4. Note environment (e.g., us-west1-gcp)
```

#### 7.1.2: Dependencies Installation
```bash
# Add to requirements.txt
echo "pinecone-client==2.2.4" >> requirements.txt
echo "sentence-transformers==2.2.2" >> requirements.txt

# Install dependencies
pip install -r requirements.txt
```

#### 7.1.3: Environment Configuration
```bash
# Add to .env
PINECONE_API_KEY=your_api_key_here
PINECONE_ENVIRONMENT=us-west1-gcp
PINECONE_INDEX_NAME=hey-listen-transcriptions
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
VECTOR_DIMENSION=384
MAX_RECORDS=1000
```

### Step 7.2: Core Pinecone Integration

#### 7.2.1: Create Pinecone Manager
```python
# src/pinecone_manager.py
import pinecone
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
import logging

class PineconeManager:
    def __init__(self):
        self.api_key = os.getenv('PINECONE_API_KEY')
        self.environment = os.getenv('PINECONE_ENVIRONMENT')
        self.index_name = os.getenv('PINECONE_INDEX_NAME', 'hey-listen-transcriptions')
        self.max_records = int(os.getenv('MAX_RECORDS', 1000))
        
        # Initialize Pinecone
        pinecone.init(api_key=self.api_key, environment=self.environment)
        
        # Initialize embedding model
        model_name = os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
        self.embedding_model = SentenceTransformer(model_name)
        
        # Get or create index
        self.index = self._get_or_create_index()
    
    def _get_or_create_index(self):
        if self.index_name not in pinecone.list_indexes():
            pinecone.create_index(
                name=self.index_name,
                dimension=384,
                metric='cosine'
            )
        return pinecone.Index(self.index_name)
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text."""
        return self.embedding_model.encode(text).tolist()
    
    def upsert_with_fifo(self, text: str, metadata: Dict[str, Any]) -> bool:
        """Upsert record with FIFO eviction."""
        # Implementation details in Step 7.3
        pass
```

#### 7.2.2: Basic Upsert Functionality
```python
def upsert_transcription(self, text: str, speaker: str, timestamp: float) -> bool:
    """Store transcription in Pinecone with FIFO management."""
    try:
        # Generate embedding
        vector = self.generate_embedding(text)
        
        # Prepare metadata
        time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
        metadata = {
            "text": text,
            "speaker": speaker,
            "timestamp": timestamp,
            "created_at": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(timestamp)),
            "title": f"Transcription - Speaker {speaker} at {time_str}",
            "summary": f"Transcript from {speaker}: {text[:100]}...",
            "chunk_duration": 5,  # From config
            "sample_rate": 16000,  # From config
            "model": "whisper-tiny"
        }
        
        # Generate unique ID
        vector_id = f"transcript_{int(timestamp)}_{speaker}"
        
        # Upsert with FIFO
        return self.upsert_with_fifo(vector_id, vector, metadata)
        
    except Exception as e:
        logging.error(f"Pinecone upsert failed: {e}")
        return False
```

### Step 7.3: FIFO Storage Implementation

#### 7.3.1: Oldest Record Detection
```python
def _find_oldest_record(self) -> Optional[Dict]:
    """Find the oldest record in the index."""
    try:
        # Query for records sorted by timestamp
        query_response = self.index.query(
            vector=[0.0] * 384,  # Dummy vector
            top_k=1,
            include_metadata=True,
            filter={"timestamp": {"$gte": 0}},  # All records
            sort_by="timestamp"
        )
        
        if query_response.matches:
            return query_response.matches[0]
        return None
        
    except Exception as e:
        logging.error(f"Failed to find oldest record: {e}")
        return None
```

#### 7.3.2: Atomic FIFO Operations
```python
def upsert_with_fifo(self, vector_id: str, vector: List[float], metadata: Dict[str, Any]) -> bool:
    """Upsert with FIFO eviction in atomic operation."""
    try:
        # Check if we need to evict
        stats = self.index.describe_index_stats()
        current_count = stats.total_vector_count
        
        if current_count >= self.max_records:
            # Find and delete oldest record
            oldest = self._find_oldest_record()
            if oldest:
                self.index.delete([oldest.id])
                logging.info(f"Evicted oldest record: {oldest.id}")
        
        # Upsert new record
        self.index.upsert([(vector_id, vector, metadata)])
        logging.info(f"Upserted new record: {vector_id}")
        
        return True
        
    except Exception as e:
        logging.error(f"FIFO upsert failed: {e}")
        return False
```

### Step 7.4: Audio Worker Integration

#### 7.4.1: Modify AudioWorker Class
```python
# Add to AudioWorker.__init__
from src.pinecone_manager import PineconeManager

def __init__(self, ...):
    # ... existing initialization ...
    
    # Remove Senso.ai initialization
    # self.api_key = os.getenv('SENSO_API_KEY')  # Remove this line
    
    # Initialize Pinecone
    self.pinecone_manager = None
    if os.getenv('PINECONE_API_KEY'):
        try:
            self.pinecone_manager = PineconeManager()
            logging.info("Pinecone manager initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize Pinecone: {e}")
    else:
        logging.warning("PINECONE_API_KEY not set - Pinecone disabled")
```

#### 7.4.2: Pinecone Storage in Main Loop
```python
def run(self):
    # ... existing code ...
    
    try:
        while True:
            # ... existing audio processing ...
            
            timestamp = time.time()
            
            # Store in Pinecone with FIFO
            pinecone_success = False
            if self.pinecone_manager:
                pinecone_success = self.pinecone_manager.upsert_transcription(
                    text, speaker, timestamp
                )
            
            # Log results
            if pinecone_success:
                logging.info(f"[{speaker}] {text[:60]}... → Pinecone:✓")
            else:
                logging.warning(f"[{speaker}] {text[:60]}... → Pinecone:✗")
            
            # ... rest of loop ...
```

### Step 7.5: Testing & Validation

#### 7.5.1: Unit Tests
```python
# tests/test_pinecone.py
import pytest
from unittest.mock import Mock, patch
from src.pinecone_manager import PineconeManager

@patch('src.pinecone_manager.pinecone.init')
@patch('src.pinecone_manager.SentenceTransformer')
def test_pinecone_manager_init(mock_transformer, mock_init):
    """Test PineconeManager initialization."""
    with patch.dict(os.environ, {
        'PINECONE_API_KEY': 'test_key',
        'PINECONE_ENVIRONMENT': 'test_env',
        'PINECONE_INDEX_NAME': 'test_index'
    }):
        manager = PineconeManager()
        assert manager.api_key == 'test_key'
        assert manager.environment == 'test_env'

def test_embedding_generation():
    """Test embedding generation."""
    manager = PineconeManager()
    embedding = manager.generate_embedding("Hello world")
    assert len(embedding) == 384
    assert all(isinstance(x, float) for x in embedding)
```

#### 7.5.2: Integration Tests
```python
def test_fifo_eviction():
    """Test FIFO eviction behavior."""
    manager = PineconeManager()
    
    # Insert records beyond max_records limit
    for i in range(1005):  # Exceed max_records=1000
        success = manager.upsert_transcription(
            f"Test transcription {i}",
            "A",
            time.time() + i
        )
        assert success
    
    # Verify we still have max_records
    stats = manager.index.describe_index_stats()
    assert stats.total_vector_count <= 1000

def test_audio_worker_integration():
    """Test AudioWorker with Pinecone integration."""
    with patch.dict(os.environ, {'PINECONE_API_KEY': 'test_key'}):
        worker = AudioWorker()
        assert worker.pinecone_manager is not None
        assert worker.api_key is None  # Senso.ai should be removed
```

### Step 7.6: Production Deployment

#### 7.6.1: Docker Configuration Updates
```dockerfile
# Add to Dockerfile
RUN pip install pinecone-client sentence-transformers

# Add environment variables
ENV PINECONE_API_KEY=""
ENV PINECONE_ENVIRONMENT=""
ENV PINECONE_INDEX_NAME="hey-listen-transcriptions"
ENV EMBEDDING_MODEL="sentence-transformers/all-MiniLM-L6-v2"
ENV MAX_RECORDS="1000"
```

#### 7.6.2: Docker Compose Updates
```yaml
# Add to docker-compose.yml
environment:
  - PINECONE_API_KEY=${PINECONE_API_KEY}
  - PINECONE_ENVIRONMENT=${PINECONE_ENVIRONMENT}
  - PINECONE_INDEX_NAME=${PINECONE_INDEX_NAME}
  - EMBEDDING_MODEL=${EMBEDDING_MODEL:-sentence-transformers/all-MiniLM-L6-v2}
  - MAX_RECORDS=${MAX_RECORDS:-1000}
```

## Testing Strategy

### 1. Unit Testing
- **PineconeManager**: Test initialization, embedding generation, FIFO logic
- **FIFO Operations**: Test eviction behavior, atomic operations
- **Error Handling**: Test API failures, network issues, invalid data

### 2. Integration Testing
- **Audio Worker Integration**: Test dual storage with real audio
- **Performance Testing**: Measure latency impact of Pinecone operations
- **Concurrent Operations**: Test multiple simultaneous upserts

### 3. End-to-End Testing
- **Full Pipeline**: Audio → Transcription → Dual Storage → Retrieval
- **FIFO Behavior**: Verify oldest records are properly evicted
- **Data Consistency**: Ensure Senso.ai and Pinecone data alignment

### 4. Load Testing
- **High Frequency**: Test 15-second interval operations
- **Large Datasets**: Test with max_records=1000
- **Memory Usage**: Monitor embedding model memory consumption

## Performance Considerations

### 1. Embedding Generation
- **Model Selection**: Use lightweight model (all-MiniLM-L6-v2)
- **Caching**: Cache embeddings for identical text
- **Batch Processing**: Process multiple transcriptions together

### 2. Pinecone Operations
- **Async Operations**: Use async/await for non-blocking operations
- **Connection Pooling**: Reuse Pinecone connections
- **Retry Logic**: Implement exponential backoff for failures

### 3. Memory Management
- **Model Loading**: Load embedding model once at startup
- **Vector Cleanup**: Ensure proper cleanup of temporary vectors
- **Garbage Collection**: Monitor and optimize memory usage

### 4. Latency Optimization
- **Parallel Processing**: Run Senso.ai and Pinecone operations in parallel
- **Non-blocking**: Don't block audio processing for storage operations
- **Timeout Management**: Set appropriate timeouts for API calls

## Monitoring & Observability

### 1. Metrics to Track
```python
# Key metrics for monitoring
METRICS = {
    "pinecone_upsert_success_rate": "Percentage of successful upserts",
    "pinecone_upsert_latency": "Average upsert operation latency",
    "fifo_eviction_count": "Number of records evicted per hour",
    "embedding_generation_time": "Time to generate embeddings",
    "index_size": "Current number of vectors in index",
    "api_error_rate": "Pinecone API error rate"
}
```

### 2. Logging Enhancements
```python
# Enhanced logging for Pinecone operations
logging.info(f"Pinecone upsert: {vector_id} | Latency: {latency}ms | Success: {success}")
logging.warning(f"FIFO eviction: Removed {oldest_id} | Index size: {current_size}")
logging.error(f"Pinecone API error: {error_code} | Retry attempt: {attempt}")
```

### 3. Health Checks
```python
# Add to healthcheck.py
def check_pinecone_health():
    """Check Pinecone connectivity and index status."""
    try:
        manager = PineconeManager()
        stats = manager.index.describe_index_stats()
        return {
            "status": "healthy",
            "index_size": stats.total_vector_count,
            "dimension": stats.dimension
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

## Deployment Updates

### 1. Environment Configuration
```bash
# Production .env template
PINECONE_API_KEY=prod_api_key_here
PINECONE_ENVIRONMENT=us-west1-gcp
PINECONE_INDEX_NAME=hey-listen-transcriptions-prod
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
VECTOR_DIMENSION=384
MAX_RECORDS=10000  # Higher limit for production

# Remove Senso.ai configuration
# SENSO_API_KEY=  # Remove this line
```

### 2. Docker Updates
- Add Pinecone dependencies to requirements.txt
- Update Dockerfile with embedding model pre-download
- Configure environment variables in docker-compose.yml

### 3. Monitoring Setup
- Add Pinecone metrics to monitoring dashboard
- Configure alerts for API failures and high latency
- Set up log aggregation for Pinecone operations

## Future Enhancements

### 1. Advanced Features
- **Semantic Search**: Implement conversation search functionality
- **Speaker Clustering**: Use embeddings for speaker identification
- **Topic Modeling**: Extract conversation topics using embeddings
- **Sentiment Analysis**: Add sentiment vectors to metadata

### 2. Performance Optimizations
- **GPU Acceleration**: Use GPU for embedding generation
- **Batch Embeddings**: Process multiple transcriptions together
- **Index Optimization**: Use larger Pinecone pods for better performance
- **Caching Layer**: Add Redis cache for frequent queries

### 3. Integration Enhancements
- **WebSocket API**: Real-time vector search endpoint
- **REST API**: HTTP endpoints for conversation retrieval
- **GraphQL**: Flexible query interface for complex searches
- **Webhook Integration**: Notify external systems of new transcriptions

### 4. Advanced Analytics
- **Conversation Flow**: Track speaker transitions and topics
- **Engagement Metrics**: Measure conversation participation
- **Trend Analysis**: Identify recurring topics and patterns
- **Export Functionality**: Export conversation data in various formats

## Success Criteria

### Phase 7 Completion Checklist
- [ ] Pinecone account setup and API key configured
- [ ] Dependencies installed and environment configured
- [ ] PineconeManager class implemented with FIFO logic
- [ ] AudioWorker integrated with Pinecone storage (Senso.ai removed)
- [ ] Unit tests passing for all Pinecone operations
- [ ] Integration tests validating FIFO behavior
- [ ] Performance benchmarks meeting latency requirements
- [ ] Docker configuration updated for production
- [ ] Monitoring and logging implemented
- [ ] Documentation updated with Pinecone integration

### Performance Targets
- **Upsert Latency**: < 500ms per operation
- **FIFO Eviction**: < 200ms per eviction
- **Embedding Generation**: < 100ms per transcription
- **Memory Usage**: < 2GB additional memory
- **Success Rate**: > 99% for Pinecone operations

## Conclusion

Phase 7 will significantly enhance the Hey Listen system by replacing Senso.ai with Pinecone vector-based storage and retrieval capabilities. The FIFO storage strategy ensures cost-effective operation while maintaining recent conversation history for semantic search. The single storage approach with Pinecone provides vector-based similarity search with rich metadata, creating a streamlined conversation intelligence platform.

**Next Steps**: Begin with Phase 7.1 (Environment Setup) and proceed sequentially through each implementation step, validating functionality at each phase before moving to the next.
