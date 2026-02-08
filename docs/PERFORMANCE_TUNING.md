# Performance Tuning Guide

## Overview

This guide provides recommendations for optimizing the performance of the semantic search and RAG system.

## Target Performance Metrics

- **Indexing Throughput**: 1000+ objects/minute
- **Query Latency (p95)**: <200ms
- **Vector Search Latency**: <100ms
- **Embedding Generation**: <50ms per batch
- **IAM Evaluation**: <10ms

## Indexing Performance

### 1. Increase Worker Concurrency

Edit `config/worker_config.yaml`:

```yaml
worker:
  indexer:
    num_workers: 10  # Increase based on CPU cores
    batch_size: 20   # Process more objects per batch
```

Deploy more worker pods:
```bash
kubectl scale deployment indexer-worker -n smart-storage --replicas=10
```

### 2. Optimize Chunking

Larger chunks = fewer vectors = faster indexing:

```yaml
chunking:
  max_chunk_size: 1024  # Increase from 512
  overlap: 100
  min_chunk_size: 100
```

**Trade-off**: Larger chunks reduce granularity of search results.

### 3. Use Faster Embedding Models

In `config/embedding_config.yaml`:

```yaml
embedding:
  sentence_transformers:
    model_name: "all-MiniLM-L6-v2"  # Fast (384 dim)
    device: "cuda"  # Use GPU if available
    batch_size: 64  # Increase batch size
```

**Model Comparison**:
- `all-MiniLM-L6-v2`: Fast, 384 dim, good quality
- `all-MiniLM-L12-v2`: Medium, 384 dim, better quality
- `all-mpnet-base-v2`: Slow, 768 dim, best quality

### 4. Enable Embedding Cache

```yaml
embedding:
  cache:
    enabled: true
    max_size: 50000  # Increase cache size
    ttl_seconds: 7200
```

### 5. Optimize Text Extraction

Skip OCR for faster processing:

```yaml
text_extraction:
  ocr:
    enabled: false  # Disable if not needed
```

### 6. Use Batch Processing

Batch insertions to Milvus:

```python
# Instead of inserting one at a time
for chunk in chunks:
    milvus_client.insert_vectors([chunk])

# Batch insert
milvus_client.insert_vectors(all_chunks)
```

## Query Performance

### 1. Optimize Milvus Index

Use HNSW for faster search:

In `config/milvus_config.yaml`:

```yaml
milvus:
  collection:
    schema:
      index_type: "HNSW"  # Faster than IVF_FLAT
  index_params:
    M: 16
    efConstruction: 200
  search_params:
    ef: 100
```

**Trade-off**: HNSW uses more memory but is much faster.

### 2. Reduce Search Scope

Limit top_k:

```python
# Instead of
results = retriever.search(query, top_k=100)

# Use
results = retriever.search(query, top_k=10)
```

Use filters to reduce search space:

```python
results = retriever.search(
    query,
    filters={"bucket": "specific-bucket"}
)
```

### 3. Scale API Horizontally

```bash
kubectl scale deployment search-api -n smart-storage --replicas=10
```

Enable auto-scaling (HPA):

```yaml
spec:
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        averageUtilization: 70
```

### 4. Use Connection Pooling

In `config/worker_config.yaml`:

```yaml
database:
  postgresql:
    pool_size: 20  # Increase pool size
    max_overflow: 40
```

### 5. Cache Common Queries

Implement query result caching:

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_search(query_hash):
    return retriever.search(query)
```

### 6. Async Processing

Use async for parallel operations:

```python
import asyncio

async def process_queries(queries):
    tasks = [search_async(q) for q in queries]
    results = await asyncio.gather(*tasks)
    return results
```

## Database Performance

### 1. Add Indexes

```sql
-- Index for common queries
CREATE INDEX idx_objects_bucket_key_version 
ON objects(bucket, key, version_id);

CREATE INDEX idx_chunks_object_chunk 
ON chunks(object_id, chunk_index);

-- GIN index for JSONB
CREATE INDEX idx_objects_tags_gin 
ON objects USING GIN(tags);
```

### 2. Use Read Replicas

For read-heavy workloads, use PostgreSQL read replicas:

```yaml
database:
  postgresql:
    read_hosts:
      - "postgres-replica-1:5432"
      - "postgres-replica-2:5432"
```

### 3. Vacuum Regularly

```sql
-- Run weekly
VACUUM ANALYZE objects;
VACUUM ANALYZE chunks;
```

### 4. Optimize Queries

Use EXPLAIN ANALYZE to optimize slow queries:

```sql
EXPLAIN ANALYZE
SELECT * FROM objects
WHERE bucket = 'my-bucket'
AND created_at > NOW() - INTERVAL '1 day';
```

## Milvus Performance

### 1. Use Appropriate Index Type

**IVF_FLAT**:
- Memory efficient
- Good for small datasets (<1M vectors)
- Slower search

**HNSW**:
- Memory intensive
- Fast search
- Best for production

**IVF_SQ8**:
- Compressed index
- Good balance of speed and memory

### 2. Tune Index Parameters

For HNSW:

```yaml
index_params:
  M: 16        # Connections per layer (higher = better recall, more memory)
  efConstruction: 200  # Build-time effort (higher = better quality, slower build)

search_params:
  ef: 100      # Search effort (higher = better recall, slower search)
```

For IVF_FLAT:

```yaml
index_params:
  nlist: 1024  # Number of clusters (sqrt(num_vectors) is a good start)

search_params:
  nprobe: 10   # Clusters to search (higher = better recall, slower)
```

### 3. Load Collection into Memory

```python
# Ensure collection is loaded before searching
milvus_client.load_collection("object_chunks")
```

### 4. Use Multiple Replicas

```python
# Create collection with replicas
collection.create_replica(num_replicas=3)
```

### 5. Optimize Dimension

Use lower-dimensional embeddings:

- 384 dimensions: Fast, good quality
- 768 dimensions: Slower, better quality
- 1536 dimensions: Slowest, best quality (OpenAI)

### 6. Use GPU for Search

Deploy Milvus with GPU support for 10-100x faster search.

## Network Performance

### 1. Co-locate Services

Deploy services in the same availability zone to reduce network latency.

### 2. Use Internal DNS

Use Kubernetes internal DNS instead of external endpoints:

```yaml
milvus:
  host: milvus-service  # Internal DNS
  port: 19530
```

### 3. Enable HTTP/2

For API communication:

```python
import httpx

client = httpx.AsyncClient(http2=True)
```

### 4. Compress Responses

Enable compression in FastAPI:

```python
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware

app = FastAPI()
app.add_middleware(GZipMiddleware, minimum_size=1000)
```

## Monitoring and Profiling

### 1. Track Key Metrics

```python
from prometheus_client import Counter, Histogram

# Indexing metrics
objects_indexed = Counter('objects_indexed_total', 'Total objects indexed')
indexing_duration = Histogram('indexing_duration_seconds', 'Indexing duration')

# Query metrics
query_latency = Histogram('query_latency_seconds', 'Query latency')
search_results = Counter('search_results_total', 'Total search results')
```

### 2. Profile Python Code

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Your code here

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

### 3. Monitor System Resources

```bash
# CPU and memory
kubectl top nodes
kubectl top pods -n smart-storage

# Milvus metrics
curl http://milvus-service:9091/metrics
```

## Hardware Recommendations

### Development
- CPU: 4 cores
- RAM: 8 GB
- Storage: 50 GB SSD

### Production (Small)
- Indexer: 8 cores, 16 GB RAM
- API: 4 cores, 8 GB RAM
- Milvus: 8 cores, 32 GB RAM
- PostgreSQL: 4 cores, 16 GB RAM

### Production (Large)
- Indexer: 16 cores, 32 GB RAM (multiple replicas)
- API: 8 cores, 16 GB RAM (multiple replicas)
- Milvus: 32 cores, 128 GB RAM (with GPU)
- PostgreSQL: 16 cores, 64 GB RAM (with replicas)

## Cost Optimization

1. **Use Spot Instances**: For indexer workers (fault-tolerant)
2. **Right-size Pods**: Monitor actual resource usage
3. **Scale to Zero**: Scale indexers to 0 during off-hours
4. **Use S3 Intelligent-Tiering**: For object storage
5. **Compress Data**: Enable compression in Milvus and PostgreSQL
6. **Use Regional Resources**: Avoid cross-region data transfer

## Troubleshooting Performance Issues

### Slow Indexing

1. Check worker CPU/memory usage
2. Profile text extraction (PDF parsing can be slow)
3. Check Milvus insert latency
4. Verify embedding generation time
5. Check Kafka consumer lag

### Slow Search

1. Profile query processing time
2. Check Milvus search latency
3. Verify index type (use HNSW for production)
4. Check IAM evaluation time
5. Monitor database query time

### High Memory Usage

1. Reduce embedding cache size
2. Use smaller batch sizes
3. Use compressed Milvus index (IVF_SQ8)
4. Limit collection replicas
5. Clear unused data

## Performance Testing

### Load Testing

```python
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

async def load_test():
    queries = ["test query"] * 100
    
    start = time.time()
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(lambda q: search(q), queries))
    end = time.time()
    
    print(f"Completed {len(queries)} queries in {end-start:.2f}s")
    print(f"QPS: {len(queries)/(end-start):.2f}")
```

### Benchmark Results

Target benchmarks for reference:

- Indexing: 1000 objects/min (500-word documents)
- Search: 100 QPS per API replica
- p50 latency: <100ms
- p95 latency: <200ms
- p99 latency: <500ms
