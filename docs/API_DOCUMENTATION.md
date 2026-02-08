# API Documentation

## Base URL
```
http://localhost:8000
```

## Authentication
Pass principal identifier in `X-Principal` header.

## Endpoints

### Health Check
```
GET /health
```

Response:
```json
{
  "status": "healthy",
  "milvus": "connected",
  "database": "connected"
}
```

### Semantic Search
```
POST /api/v1/search
```

Request Body:
```json
{
  "query": "string (required)",
  "top_k": "integer (default: 10, max: 100)",
  "filters": {
    "bucket": "string (optional)",
    "prefix": "string (optional)",
    "tags": {}
  }
}
```

Response:
```json
{
  "query": "search query",
  "results": [
    {
      "score": 0.95,
      "bucket": "my-bucket",
      "key": "path/to/file.pdf",
      "version_id": "v123",
      "chunk_index": 0,
      "start_offset": 1024,
      "end_offset": 1536,
      "text": "relevant text...",
      "content_type": "application/pdf",
      "citation": "s3://my-bucket/path/to/file.pdf?versionId=v123 (offset 1024-1536)"
    }
  ],
  "total_results": 10
}
```

### RAG Query
```
POST /api/v1/rag/query
```

Request Body:
```json
{
  "question": "string (required)",
  "top_k": "integer (default: 5, max: 20)",
  "include_citations": "boolean (default: true)",
  "filters": {}
}
```

Response:
```json
{
  "question": "What are the features?",
  "answer": "The features include...",
  "confidence": 0.92,
  "citations": [
    {
      "index": 1,
      "bucket": "docs",
      "key": "features.pdf",
      "version_id": "v1",
      "start_offset": 2048,
      "end_offset": 2560,
      "citation_string": "s3://docs/features.pdf (offset 2048-2560)",
      "score": 0.95
    }
  ],
  "sources": ["docs/features.pdf"]
}
```

### Index Status
```
GET /api/v1/index/status/{bucket}/{key}?version_id=v123
```

Response:
```json
{
  "bucket": "my-bucket",
  "key": "file.pdf",
  "version_id": "v123",
  "indexed": true,
  "chunk_count": 15,
  "last_indexed": "2024-01-15T10:30:00Z"
}
```

### Collection Stats
```
GET /api/v1/stats
```

Response:
```json
{
  "vector_count": 10000,
  "collection_name": "object_chunks"
}
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid request parameters"
}
```

### 403 Forbidden
```json
{
  "detail": "Access denied"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error message"
}
```

## Rate Limiting

- Search: 100 requests/minute per principal
- RAG: 50 requests/minute per principal

## Examples

### Python
```python
import requests

# Search
response = requests.post(
    "http://localhost:8000/api/v1/search",
    json={"query": "machine learning", "top_k": 5},
    headers={"X-Principal": "user1"}
)
results = response.json()

# RAG
response = requests.post(
    "http://localhost:8000/api/v1/rag/query",
    json={"question": "What is machine learning?"},
    headers={"X-Principal": "user1"}
)
answer = response.json()
```

### cURL
```bash
# Search
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -H "X-Principal: user1" \
  -d '{"query": "machine learning", "top_k": 5}'

# RAG
curl -X POST http://localhost:8000/api/v1/rag/query \
  -H "Content-Type: application/json" \
  -H "X-Principal: user1" \
  -d '{"question": "What is machine learning?"}'
```
