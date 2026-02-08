# Smart Object Storage - Semantic Search & RAG System

A production-ready semantic search and RAG (Retrieval-Augmented Generation) system built on top of object storage with IAM-aware retrieval and version-aware indexing.

## Overview

This extends the existing Smart Object Storage system with advanced semantic search and RAG capabilities.

## Features

- **Semantic Search**: Natural language search across all stored objects
- **RAG Q&A**: Question answering with source citations
- **IAM-Aware**: Respects access control policies
- **Version-Aware**: Tracks object versions correctly

## Quick Start

```bash
# Start all services
docker-compose up -d

# Test the API
curl http://localhost:8000/health

# Search
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning", "top_k": 10}'
```

## Documentation

- [Full Documentation](docs/README_SEMANTIC_SEARCH.md)
- [API Reference](docs/API_DOCUMENTATION.md)
- [Deployment Guide](docs/DEPLOYMENT_GUIDE.md)

## Architecture

- **Event Plane**: Handles object storage events
- **Indexing Plane**: Extracts text, generates embeddings, stores vectors
- **Query Plane**: Semantic search and RAG APIs

## Technology Stack

- **Vector DB**: Milvus
- **Embeddings**: Sentence Transformers / OpenAI
- **Message Queue**: Kafka
- **Metadata DB**: PostgreSQL
- **API**: FastAPI
- **Object Storage**: MinIO / S3

## License

MIT License
