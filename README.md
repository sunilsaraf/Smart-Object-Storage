# **Smart Object Storage Platform**

## **Overview**
The **Smart Object Storage Platform** is an advanced, production-ready system that combines intelligent tiered storage management with powerful semantic search and RAG (Retrieval-Augmented Generation) capabilities. The platform provides:

1. **Tiered Hybrid Storage**: Automatic data migration across Hot, Warm, and Cold tiers based on access patterns
2. **Semantic Search & RAG**: AI-powered natural language search with question answering and precise citations
3. **IAM-Aware Security**: Robust access control ensuring users only access authorized content
4. **Version Management**: Complete version tracking and point-in-time retrieval

### Key Capabilities
- **Intelligent Tiering**: Automatically migrates data between MinIO (on-premise) and AWS S3 (cloud) tiers
- **Semantic Search**: Natural language queries across all stored objects (PDFs, DOCX, PPTX, etc.)
- **RAG Q&A**: Ask questions and get answers with source citations (bucket/key/version + byte offsets)
- **IAM Enforcement**: Policy-based access control with ALLOW/DENY rules
- **Multi-Format Support**: Extract and search content from PDF, DOCX, PPTX, HTML, and text files

---

## **System Architecture**

### **1. Tiered Storage Architecture**
Manages data lifecycle across three performance/cost tiers:

```plaintext
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│   MinIO Hot     │ Policy  │   MinIO Warm    │ Policy  │   AWS S3 Cold   │
│  (Active/SSD)   │────────▶│   (Idle/HDD)    │────────▶│   (Archive)     │
│   Fast Access   │ 10 days │ Medium Access   │ 30 days │  Low Cost       │
└─────────────────┘         └─────────────────┘         └─────────────────┘
```

### **2. Semantic Search & RAG Architecture**
Three-plane design for AI-powered search and retrieval:

```plaintext
┌──────────────────────────────────────────────────────────────────┐
│                     Object Storage (S3/MinIO)                     │
└────────────────────────────┬─────────────────────────────────────┘
                             │ Events (PutObject, DeleteObject, etc.)
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                         EVENT PLANE                               │
│  Kafka/SQS/Pub/Sub ◀─── Event Publisher ◀─── Event Listener     │
└────────────────────────────┬─────────────────────────────────────┘
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                       INDEXING PLANE                              │
│  ┌──────────────┐  ┌───────────────┐  ┌────────────────────┐   │
│  │Text Extractor│─▶│Chunker        │─▶│Embedder            │   │
│  │(PDF/DOCX)    │  │(Semantic)     │  │(Transformers/OpenAI)│   │
│  └──────────────┘  └───────────────┘  └─────────┬──────────┘   │
│                                                   ▼               │
│  ┌─────────────────────────┐      ┌──────────────────────────┐ │
│  │ Milvus Vector Database  │◀────▶│ PostgreSQL Metadata DB   │ │
│  │ (Embeddings)            │      │ (Objects, Chunks, IAM)   │ │
│  └─────────────────────────┘      └──────────────────────────┘ │
└────────────────────────────┬─────────────────────────────────────┘
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                        QUERY PLANE                                │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │Search API    │─▶│Query Processor│─▶│Vector Search       │    │
│  │(FastAPI)     │  │(Embedding)    │  │+ IAM Filter        │    │
│  └──────────────┘  └──────────────┘  └─────────┬──────────┘    │
│                                                  ▼                │
│                                       ┌────────────────────┐     │
│                                       │RAG Engine          │     │
│                                       │(Answer + Citations)│     │
│                                       └────────────────────┘     │
└──────────────────────────────────────────────────────────────────┘
```

---

## **Key Features**

### **Tiered Storage Features**
1. **Hybrid Storage Design**:
   - Combines on-premise (MinIO) and cloud-based (S3) solutions
   - MinIO for active access, AWS S3 for long-term archival

2. **Smart Policy Management**:
   - Automatic tier transitions based on access frequency and age
   - Configurable policies: Hot → Warm (10 days), Warm → Cold (30 days)

3. **Fault-Tolerant Multipart Uploads**:
   - Retries failed uploads with exponential backoff
   - Tracks incomplete uploads for resumption

4. **S3 API Compatibility**:
   - Full S3-compatible interface for storage operations

### **Semantic Search & RAG Features**
1. **Natural Language Search**:
   - Query stored documents using plain English
   - Semantic understanding beyond keyword matching
   - Support for PDF, DOCX, PPTX, HTML, and text files

2. **RAG Question Answering**:
   - Ask questions and get AI-generated answers
   - Includes precise citations with source references
   - Citations include: bucket, key, version ID, and byte offsets

3. **IAM-Aware Retrieval**:
   - ALLOW/DENY policy enforcement
   - Users only see content they're authorized to access
   - Wildcard pattern matching for flexible policies
   - Default deny security model

4. **Version-Aware Indexing**:
   - Tracks all object versions
   - Handles concurrent updates correctly
   - Point-in-time retrieval support

5. **Multi-Format Text Extraction**:
   - PDF documents
   - Microsoft Office (DOCX, PPTX)
   - HTML and plain text
   - Optional OCR support for images

6. **Production-Ready Infrastructure**:
   - Docker Compose for local development
   - Kubernetes manifests for production
   - Horizontal scaling support
   - Prometheus metrics and health checks

---

## **Why This Project Is Unique**

### Key Differentiators:
1. **Hybrid Design**:
   - Combines **on-premise storage** with **cloud storage** effortlessly.
   - Balances between performance, control, and cost-efficiency.

2. **Automated Smart Policies**:
   - Intelligent tiering policies simplify storage management.
   - No manual migration — objects are automatically relocated across tiers based on usage.

3. **Cost-Efficiency**:
   - Reduces storage costs by archiving unused data in AWS S3’s cost-efficient storage classes.
   - Utilizes MinIO for reducing cloud egress charges and latency costs for active workloads.

4. **Future-Proof**:
   - Designed to integrate with other S3-compatible platforms beyond AWS (e.g., Wasabi, Ceph).

---

## **Quick Start**

### **Option 1: Full Platform with Semantic Search (Recommended)**

Start the complete platform with semantic search capabilities:

```bash
# Clone repository
git clone https://github.com/sunilsaraf/Smart-Object-Storage.git
cd Smart-Object-Storage

# Start all services (Milvus, PostgreSQL, Kafka, MinIO, workers, API)
docker-compose up -d

# Wait for services to be ready (~30 seconds)
sleep 30

# Test the health endpoint
curl http://localhost:8000/health

# Upload a document to MinIO
aws s3 cp document.pdf s3://my-bucket/document.pdf \
  --endpoint-url http://localhost:9000

# Search for content (indexer automatically processes uploaded files)
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -H "X-Principal: admin" \
  -d '{
    "query": "machine learning best practices",
    "top_k": 10
  }'

# Ask a question with RAG
curl -X POST http://localhost:8000/api/v1/rag/query \
  -H "Content-Type: application/json" \
  -H "X-Principal: admin" \
  -d '{
    "question": "What are the key features?",
    "top_k": 5,
    "include_citations": true
  }'
```

**Services Started:**
- **Milvus**: Vector database (port 19530)
- **PostgreSQL**: Metadata database (port 5432)
- **Kafka**: Message queue (port 9092)
- **MinIO**: Object storage (ports 9000-9001)
- **Search API**: REST API (port 8000)
- **Indexer Workers**: Background processing

### **Option 2: Tiered Storage Only (Java)**

For just the tiered storage functionality:

```bash
# Install and start MinIO
docker run -d -p 9000:9000 -p 9001:9001 --name minio \
  -e "MINIO_ROOT_USER=admin" -e "MINIO_ROOT_PASSWORD=password123" \
  minio/minio server /data --console-address ":9001"

# Set environment variables
export MINIO_ACCESS_KEY="admin"
export MINIO_SECRET_KEY="password123"
export AWS_ACCESS_KEY_ID="your-aws-access-key"
export AWS_SECRET_ACCESS_KEY="your-aws-secret-key"
export AWS_REGION="us-east-1"

# Build and run the Java application
./gradlew build
java -jar build/libs/tiered-storage-0.0.1-SNAPSHOT.jar

# Access Swagger UI
open http://localhost:8080/swagger-ui.html
```

---

## **API Examples**

### **Semantic Search API**

**Search documents by natural language query:**
```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -H "X-Principal: user1" \
  -d '{
    "query": "kubernetes deployment strategies",
    "top_k": 10,
    "filters": {
      "bucket": "engineering-docs",
      "tags": {"department": "devops"}
    }
  }'
```

**Response:**
```json
{
  "query": "kubernetes deployment strategies",
  "results": [
    {
      "score": 0.95,
      "bucket": "engineering-docs",
      "key": "k8s-guide.pdf",
      "version_id": "v123",
      "chunk_index": 5,
      "start_offset": 2048,
      "end_offset": 2560,
      "text": "Kubernetes supports multiple deployment strategies...",
      "citation": "s3://engineering-docs/k8s-guide.pdf?versionId=v123 (offset 2048-2560)"
    }
  ],
  "total_results": 10
}
```

**Ask questions with RAG:**
```bash
curl -X POST http://localhost:8000/api/v1/rag/query \
  -H "Content-Type: application/json" \
  -H "X-Principal: user1" \
  -d '{
    "question": "How do I deploy a microservice on Kubernetes?",
    "top_k": 5,
    "include_citations": true
  }'
```

**Response:**
```json
{
  "question": "How do I deploy a microservice on Kubernetes?",
  "answer": "To deploy a microservice on Kubernetes, you create a Deployment manifest that specifies the container image, replicas, and resource requirements. Then use kubectl apply to create the deployment...",
  "confidence": 0.92,
  "citations": [
    {
      "index": 1,
      "bucket": "engineering-docs",
      "key": "k8s-guide.pdf",
      "citation_string": "s3://engineering-docs/k8s-guide.pdf (offset 2048-2560)"
    }
  ],
  "sources": ["engineering-docs/k8s-guide.pdf"]
}
```

**Check indexing status:**
```bash
curl http://localhost:8000/api/v1/index/status/my-bucket/document.pdf
```

### **Tiered Storage API**

**Upload object:**
```bash
curl -X PUT "http://localhost:8080/api/v1/s3/minio-tiered-storage/sample-object" \
     -H "Content-Type: application/octet-stream" \
     --data-binary @sample-data.txt
```

**Migrate to cold tier:**
```bash
curl -X POST "http://localhost:8080/api/v1/s3/move-to-cold?objectId=sample-object"
```

**Fetch from specific tier:**
```bash
# From MinIO Hot/Warm tier
curl -X GET "http://localhost:8080/api/v1/s3/fetch/hot?objectId=sample-object"

# From AWS S3 Cold tier
curl -X GET "http://localhost:8080/api/v1/s3/fetch/cold?objectId=sample-object"
```

---

## **Technology Stack**

### **Semantic Search & RAG System (Python)**
- **Vector Database**: Milvus 2.3.5 with HNSW/IVF indices
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2) / OpenAI
- **Message Queue**: Apache Kafka / AWS SQS / Google Pub/Sub
- **Metadata Database**: PostgreSQL 15 with JSONB support
- **API Framework**: FastAPI with async support
- **Text Extraction**: pypdf, python-docx, python-pptx, pytesseract
- **Container Orchestration**: Docker Compose, Kubernetes
- **Monitoring**: Prometheus metrics, structured logging

### **Tiered Storage System (Java)**
- **Object Storage**: MinIO (on-premise), AWS S3 (cloud)
- **Backend**: Java Spring Boot
- **Storage Tiers**: Hot (SSD), Warm (HDD), Cold (S3)
- **Policy Engine**: Automatic tier migration based on access patterns
- **API**: S3-compatible REST API with Swagger documentation

---

## **Use Cases**

### **Semantic Search & RAG**
1. **Enterprise Knowledge Base**: Search across company documents, wikis, and reports
2. **Legal Document Discovery**: Find relevant case law and precedents using natural language
3. **Research & Development**: Query technical papers, patents, and research notes
4. **Customer Support**: Retrieve relevant documentation to answer customer questions
5. **Compliance & Audit**: Find specific clauses and requirements across policy documents

### **Tiered Storage**
1. **Cost-Optimized Archival**: Move long-term data to cost-effective AWS S3 Glacier
2. **Data Backup and Recovery**: Keep active data local, archive older versions in cloud
3. **Hybrid Cloud Storage**: Balance on-prem performance with cloud durability
4. **Media Asset Management**: Hot tier for recent projects, cold tier for archives
5. **Regulatory Compliance**: Retain data according to policies with automatic tiering

---

## **Documentation**

### **Semantic Search & RAG**
- 📖 [Complete Documentation](README_SEMANTIC_SEARCH.md) - Full system overview
- 📋 [API Reference](docs/API_DOCUMENTATION.md) - REST API endpoints
- 🚀 [Deployment Guide](docs/DEPLOYMENT_GUIDE.md) - Kubernetes production setup
- 🔒 [IAM Policy Examples](docs/IAM_POLICY_EXAMPLES.md) - Access control patterns
- ⚡ [Performance Tuning](docs/PERFORMANCE_TUNING.md) - Optimization guide
- 🔐 [Security Advisory](SECURITY_ADVISORY.md) - Security updates and patches

### **Architecture & Implementation**
- 📊 [Implementation Summary](IMPLEMENTATION_SUMMARY.md) - Complete implementation details
- 🏗️ Architecture diagrams and design decisions
- 🧪 Testing strategy and test coverage

---

## **Performance**

### **Semantic Search System**
- **Indexing Throughput**: 1000+ objects/minute
- **Query Latency (p95)**: <200ms
- **Vector Search**: <100ms with HNSW index
- **IAM Evaluation**: <10ms per request
- **Concurrent Requests**: 100+ QPS per API replica
- **Scalability**: Horizontal scaling with Kubernetes HPA

### **Tiered Storage System**
- **Hot Tier Latency**: <10ms (SSD/NVMe)
- **Warm Tier Latency**: <50ms (HDD)
- **Cold Tier Latency**: Variable (S3 retrieval time)
- **Migration**: Automatic based on configurable policies
- **Throughput**: Limited by network and storage backend

---

## **Security & IAM**

### **IAM Policy Enforcement**
The semantic search system enforces IAM policies at query time:

```sql
-- Example: Grant read access to engineering bucket
INSERT INTO iam_policies (principal, resource_pattern, actions, effect)
VALUES ('engineering-team', 'engineering-docs/*', ARRAY['s3:GetObject'], 'ALLOW');

-- Example: Deny access to confidential data
INSERT INTO iam_policies (principal, resource_pattern, actions, effect)
VALUES ('contractors', 'confidential/*', ARRAY['s3:*'], 'DENY');
```

### **Security Features**
- ✅ ALLOW/DENY policy evaluation (DENY takes precedence)
- ✅ Wildcard pattern matching (`bucket/*`, `prefix/*/file.txt`)
- ✅ Default deny security model
- ✅ Result filtering before returning to users
- ✅ Audit logging of policy evaluations
- ✅ All dependencies patched for known vulnerabilities

---

## **Monitoring & Observability**

### **Metrics (Prometheus)**
- `indexer_objects_processed_total` - Objects indexed
- `query_latency_seconds` - Query response time
- `milvus_vector_count` - Total vectors in database
- `iam_denials_total` - Access denied events
- `embedding_generation_duration` - Embedding latency

### **Health Checks**
```bash
# Semantic search API
curl http://localhost:8000/health

# Tiered storage API
curl http://localhost:8080/actuator/health
```

### **Logs**
Structured JSON logging for easy parsing and analysis:
```json
{
  "timestamp": "2024-02-08T10:30:00Z",
  "level": "INFO",
  "message": "Indexed object successfully",
  "bucket": "engineering-docs",
  "key": "document.pdf",
  "chunks": 15,
  "duration_ms": 2341
}
```

---

## **Contributing**

We welcome contributions to both the tiered storage and semantic search systems!

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature`
3. **Make your changes** with tests
4. **Run tests**: `pytest tests/` (Python) or `./gradlew test` (Java)
5. **Submit a pull request** with detailed description

### **Development Setup**

**Python (Semantic Search):**
```bash
# Install dependencies
pip install -r requirements.txt
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Code formatting
black src/ tests/
flake8 src/ tests/
```

**Java (Tiered Storage):**
```bash
# Build project
./gradlew build

# Run tests
./gradlew test

# Generate Swagger docs
./gradlew bootRun
```

### **Areas for Contribution**
- 🔍 Additional embedding model support (Cohere, Anthropic)
- 📊 Enhanced monitoring and dashboards
- 🌐 Multi-language support for text extraction
- 🔐 Additional IAM policy features
- ⚡ Performance optimizations
- 📝 Documentation improvements
- 🧪 Additional test coverage

---

## **License**

Licensed under the MIT License. See [LICENSE](LICENSE) for more details.

---

## **Acknowledgments**

Built with:
- [Milvus](https://milvus.io/) - Vector database
- [MinIO](https://min.io/) - S3-compatible object storage
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Sentence Transformers](https://www.sbert.net/) - State-of-the-art embeddings
- [Apache Kafka](https://kafka.apache.org/) - Distributed event streaming

---

## **Support & Contact**

- 📧 **Email**: support@example.com
- 🐛 **Issues**: [GitHub Issues](https://github.com/sunilsaraf/Smart-Object-Storage/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/sunilsaraf/Smart-Object-Storage/discussions)
- 📖 **Documentation**: See `docs/` directory

---

**Smart Object Storage Platform** - Intelligent storage with AI-powered search 🚀