# Senso.ai API Integration Guide

## Overview

Senso.ai provides an AI-powered knowledge base for organizing and retrieving transcription data. This guide covers the two primary operations: **ingesting** transcriptions and **searching** for context.

## API Basics

### Base URL
```
https://sdk.senso.ai/api/v1
```

### Authentication
All requests require an organization API key in the header:

```http
X-API-Key: your_api_key_here
Content-Type: application/json
```

### Getting an API Key
1. Email: support@senso.ai
2. Request: Organization-scoped API key with read/write permissions
3. Store securely in `.env` file (never commit to git)

## Ingestion: POST /content/raw

### Purpose
Store transcriptions as raw content in the knowledge base for future search and retrieval.

### Endpoint
```
POST https://sdk.senso.ai/api/v1/content/raw
```

### Request Headers
```http
X-API-Key: your_api_key_here
Content-Type: application/json
```

### Request Payload
```json
{
  "title": "string (required)",
  "summary": "string (optional but recommended)",
  "text": "string (required, supports markdown)"
}
```

### Payload Example for Transcription
```json
{
  "title": "Transcription - Speaker A at 2025-10-04 11:30:45",
  "summary": "Transcript from Speaker A: Let's discuss the project timeline and milestones...",
  "text": "**Speaker A:** Let's discuss the project timeline and milestones for the next quarter.\n*Timestamp: 1728054645.123*"
}
```

### Response
```json
{
  "id": "content_abc123xyz",
  "processing_status": "pending",
  "created_at": "2025-10-04T11:30:47Z"
}
```

**Status Code**: `201 Created`

### Processing Time
- Content is indexed asynchronously
- Typically takes **2-5 seconds** to become searchable
- Recommendation: `time.sleep(2)` after ingestion before searching

### Error Responses

#### 400 Bad Request
```json
{
  "error": "Invalid payload",
  "details": "Missing required field: text"
}
```

#### 401 Unauthorized
```json
{
  "error": "Invalid API key"
}
```

#### 429 Too Many Requests
```json
{
  "error": "Rate limit exceeded",
  "retry_after": 60
}
```

### Python Implementation

```python
import requests
import time

def ingest_transcription(api_key, text, speaker, timestamp):
    """
    Ingest a transcription to Senso.ai knowledge base.

    Args:
        api_key (str): Senso.ai API key
        text (str): Transcribed text
        speaker (str): Speaker identifier (A, B, C, etc.)
        timestamp (float): Unix timestamp

    Returns:
        str: Content ID if successful, None otherwise
    """
    # Format timestamp for title
    time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))

    # Prepare payload
    payload = {
        "title": f"Transcription - Speaker {speaker} at {time_str}",
        "summary": f"Transcript from {speaker}: {text[:100]}...",
        "text": f"**Speaker {speaker}:** {text}\n*Timestamp: {timestamp}*"
    }

    # Send request
    try:
        response = requests.post(
            "https://sdk.senso.ai/api/v1/content/raw",
            headers={
                "X-API-Key": api_key,
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=10
        )

        # Check response
        response.raise_for_status()
        data = response.json()

        print(f"✓ Ingested: {data['id']} (Status: {data['processing_status']})")

        # Wait for indexing
        time.sleep(2)

        return data['id']

    except requests.exceptions.HTTPError as e:
        print(f"✗ HTTP Error: {e.response.status_code} - {e.response.text}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"✗ Request failed: {e}")
        return None
```

### Best Practices for Ingestion

1. **Batch if Needed**: If generating many transcriptions quickly, consider buffering locally and batching ingests to reduce API calls

2. **Retry Logic**: Implement exponential backoff for transient failures
   ```python
   from tenacity import retry, stop_after_attempt, wait_exponential

   @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
   def ingest_with_retry(api_key, text, speaker, timestamp):
       # ... ingest logic ...
   ```

3. **Validate Before Send**: Check text is non-empty and API key is set

4. **Log All Responses**: Track content IDs for debugging

## Search: POST /search

### Purpose
Query the knowledge base for relevant transcriptions using natural language.

### Endpoint
```
POST https://sdk.senso.ai/api/v1/search
```

### Request Headers
```http
X-API-Key: your_api_key_here
Content-Type: application/json
```

### Request Payload
```json
{
  "query": "string (required)",
  "max_results": "integer (optional, default varies)"
}
```

### Query Examples

#### Get Recent Transcriptions
```json
{
  "query": "Show me recent conversation transcriptions from the last 10 minutes",
  "max_results": 10
}
```

#### Topic-Based Search
```json
{
  "query": "What did we discuss about the project timeline?",
  "max_results": 5
}
```

#### Speaker-Specific Search
```json
{
  "query": "What did Speaker A say about milestones?",
  "max_results": 5
}
```

### Response
```json
{
  "answer": "Based on recent transcriptions, Speaker A discussed...",
  "results": [
    {
      "content_id": "content_abc123",
      "chunk": "**Speaker A:** Let's discuss the project timeline...",
      "score": 0.92,
      "metadata": {
        "title": "Transcription - Speaker A at 2025-10-04 11:30:45"
      }
    },
    {
      "content_id": "content_xyz789",
      "chunk": "**Speaker B:** I agree, we should set clear milestones...",
      "score": 0.87,
      "metadata": {
        "title": "Transcription - Speaker B at 2025-10-04 11:31:02"
      }
    }
  ]
}
```

**Status Code**: `200 OK`

### Python Implementation

```python
def search_transcriptions(api_key, query, max_results=10):
    """
    Search Senso.ai knowledge base for relevant transcriptions.

    Args:
        api_key (str): Senso.ai API key
        query (str): Natural language query
        max_results (int): Maximum results to return

    Returns:
        dict: Search results with answer and chunks
    """
    payload = {
        "query": query,
        "max_results": max_results
    }

    try:
        response = requests.post(
            "https://sdk.senso.ai/api/v1/search",
            headers={
                "X-API-Key": api_key,
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=10
        )

        response.raise_for_status()
        data = response.json()

        print(f"✓ Search completed: {len(data.get('results', []))} results")
        print(f"Answer: {data.get('answer', 'No answer provided')}")

        return data

    except requests.exceptions.RequestException as e:
        print(f"✗ Search failed: {e}")
        return None
```

### Search Best Practices

1. **Specific Queries**: Include time references ("recent", "last 5 minutes") or speaker names for better results

2. **Max Results**: Start with 5-10 results; increase if needed

3. **Parse Chunks**: Extract timestamps from chunk text for chronological ordering

4. **Cache Results**: For repeated queries (e.g., "recent context"), cache for short periods

## Advanced Features (Future)

### Categories
Organize transcriptions by topic:

```http
POST /categories
{
  "name": "Project Discussions",
  "description": "All transcriptions about project planning"
}
```

Then tag content during ingestion:
```json
{
  "title": "...",
  "text": "...",
  "category_ids": ["cat_123"]
}
```

### Metadata Filtering
Add custom metadata for finer search control:
```json
{
  "title": "...",
  "text": "...",
  "metadata": {
    "speaker": "A",
    "timestamp": 1728054645,
    "conversation_id": "conv_001"
  }
}
```

## Error Handling Checklist

- [ ] Check API key is set before every request
- [ ] Handle 401/403 (auth errors) → log and skip
- [ ] Handle 429 (rate limit) → exponential backoff
- [ ] Handle 500 (server error) → retry once, then skip
- [ ] Handle network timeouts → log and continue
- [ ] Validate response structure before parsing

## Testing the Integration

### Test Ingestion
```bash
curl -X POST https://sdk.senso.ai/api/v1/content/raw \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Transcription",
    "summary": "Testing Senso API",
    "text": "**Speaker A:** This is a test.\n*Timestamp: 1728054645*"
  }'
```

Expected: `201` with content ID

### Test Search
```bash
# Wait 2-5 seconds after ingestion

curl -X POST https://sdk.senso.ai/api/v1/search \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "test transcription",
    "max_results": 5
  }'
```

Expected: `200` with results including your test content

## Integration Checklist

- [ ] API key obtained and stored in `.env`
- [ ] Ingestion function implemented with error handling
- [ ] Search function implemented for future context retrieval
- [ ] Retry logic added for transient failures
- [ ] Logging configured for all API calls
- [ ] Test ingestion with curl verified
- [ ] Test search with curl verified
- [ ] Processing delay (2s) added after ingestion

Proceed to `04-audio-worker-implementation.md` for full application code.
