# Deployment Guide

## Production Deployment on Kubernetes

### Prerequisites
- Kubernetes cluster (1.24+)
- kubectl configured
- Helm 3.x (optional, for Milvus)
- Container registry access
- Storage class for persistent volumes

### Step 1: Build and Push Images

```bash
# Build images
docker build -f docker/Dockerfile.indexer -t your-registry/smart-storage-indexer:latest .
docker build -f docker/Dockerfile.api -t your-registry/smart-storage-api:latest .

# Push to registry
docker push your-registry/smart-storage-indexer:latest
docker push your-registry/smart-storage-api:latest
```

### Step 2: Create Namespace and Secrets

```bash
# Create namespace
kubectl create namespace smart-storage

# Create PostgreSQL secret
kubectl create secret generic postgres-secret \
  --from-literal=username=postgres \
  --from-literal=password=YOUR_SECURE_PASSWORD \
  -n smart-storage

# Create MinIO secret
kubectl create secret generic minio-secret \
  --from-literal=access-key=YOUR_ACCESS_KEY \
  --from-literal=secret-key=YOUR_SECRET_KEY \
  -n smart-storage

# Create OpenAI secret (if using OpenAI embeddings)
kubectl create secret generic openai-secret \
  --from-literal=api-key=YOUR_OPENAI_API_KEY \
  -n smart-storage
```

### Step 3: Deploy Infrastructure Services

```bash
# Deploy Milvus
kubectl apply -f kubernetes/milvus-deployment.yaml

# Deploy Kafka and Zookeeper
kubectl apply -f kubernetes/kafka-deployment.yaml

# Wait for services to be ready
kubectl wait --for=condition=ready pod -l app=milvus -n smart-storage --timeout=300s
kubectl wait --for=condition=ready pod -l app=kafka -n smart-storage --timeout=300s
```

### Step 4: Initialize Database

```bash
# Deploy PostgreSQL (or use managed service)
kubectl apply -f kubernetes/postgres-deployment.yaml

# Wait for PostgreSQL to be ready
kubectl wait --for=condition=ready pod -l app=postgres -n smart-storage --timeout=120s

# Run schema initialization
kubectl exec -it postgres-0 -n smart-storage -- \
  psql -U postgres -d smart_storage -f /docker-entrypoint-initdb.d/schema.sql
```

### Step 5: Deploy Application Services

```bash
# Update image references in deployment files
# Edit kubernetes/indexer-deployment.yaml and kubernetes/api-deployment.yaml
# Change image: smart-storage/indexer:latest to your-registry/smart-storage-indexer:latest

# Deploy indexer workers
kubectl apply -f kubernetes/indexer-deployment.yaml

# Deploy search API
kubectl apply -f kubernetes/api-deployment.yaml

# Verify deployments
kubectl get pods -n smart-storage
kubectl get svc -n smart-storage
```

### Step 6: Configure Ingress (Optional)

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: search-api-ingress
  namespace: smart-storage
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: search-api.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: search-api-service
            port:
              number: 80
```

Apply:
```bash
kubectl apply -f ingress.yaml
```

## Environment Variables

### Indexer Worker
- `POSTGRES_USER`: PostgreSQL username
- `POSTGRES_PASSWORD`: PostgreSQL password
- `MINIO_ACCESS_KEY`: MinIO access key
- `MINIO_SECRET_KEY`: MinIO secret key
- `OPENAI_API_KEY`: OpenAI API key (if using OpenAI embeddings)

### Search API
- `POSTGRES_USER`: PostgreSQL username
- `POSTGRES_PASSWORD`: PostgreSQL password

## Scaling

### Horizontal Scaling

```bash
# Scale indexer workers
kubectl scale deployment indexer-worker -n smart-storage --replicas=10

# Scale API
kubectl scale deployment search-api -n smart-storage --replicas=5

# Auto-scaling (HPA already configured in api-deployment.yaml)
# Scales based on CPU and memory usage
```

### Vertical Scaling

Edit resource limits in deployment files:

```yaml
resources:
  requests:
    memory: "4Gi"
    cpu: "2000m"
  limits:
    memory: "8Gi"
    cpu: "4000m"
```

## Monitoring

### Prometheus Metrics

The API exposes metrics at `/metrics`:

```bash
kubectl port-forward svc/search-api-service 8000:80 -n smart-storage
curl http://localhost:8000/metrics
```

### Grafana Dashboard

Import the dashboard from `monitoring/grafana-dashboard.json`

Key metrics:
- `indexer_objects_processed_total`
- `query_latency_seconds`
- `milvus_vector_count`
- `iam_denials_total`

## Backup and Recovery

### Database Backup

```bash
# Backup PostgreSQL
kubectl exec -it postgres-0 -n smart-storage -- \
  pg_dump -U postgres smart_storage > backup.sql

# Restore
kubectl exec -i postgres-0 -n smart-storage -- \
  psql -U postgres smart_storage < backup.sql
```

### Milvus Backup

```bash
# Use Milvus Backup tool
# https://milvus.io/docs/backup_and_restore.md
```

## Troubleshooting

### Check Pod Status
```bash
kubectl get pods -n smart-storage
kubectl describe pod <pod-name> -n smart-storage
kubectl logs <pod-name> -n smart-storage
```

### Check Services
```bash
kubectl get svc -n smart-storage
kubectl describe svc search-api-service -n smart-storage
```

### Test Connectivity
```bash
# Test API internally
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -n smart-storage -- \
  curl http://search-api-service/health

# Test Milvus
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -n smart-storage -- \
  curl http://milvus-service:9091/healthz
```

### Common Issues

**Indexer not processing files**
- Check Kafka connectivity
- Verify MinIO event notifications are configured
- Check worker logs for errors

**High API latency**
- Check Milvus index type (HNSW is faster than IVF_FLAT)
- Scale up API replicas
- Check database connection pool size

**Out of memory errors**
- Increase pod memory limits
- Reduce batch sizes in worker config
- Use smaller embedding models

## High Availability

### Multi-AZ Deployment

```yaml
spec:
  affinity:
    podAntiAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector:
            matchLabels:
              app: search-api
          topologyKey: topology.kubernetes.io/zone
```

### Database HA

Use managed database services:
- Amazon RDS for PostgreSQL
- Google Cloud SQL
- Azure Database for PostgreSQL

### Milvus HA

Deploy Milvus in cluster mode with:
- Multiple query nodes
- Multiple data nodes
- Shared object storage (S3/GCS)

## Security

### Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-network-policy
  namespace: smart-storage
spec:
  podSelector:
    matchLabels:
      app: search-api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
```

### TLS/SSL

Configure TLS in ingress:

```yaml
spec:
  tls:
  - hosts:
    - search-api.yourdomain.com
    secretName: tls-secret
```

### Pod Security

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 1000
  capabilities:
    drop:
    - ALL
```

## Cost Optimization

1. **Use spot instances** for indexer workers (fault-tolerant)
2. **Auto-scale** based on queue depth and API load
3. **Use local SSDs** for Milvus data nodes
4. **Right-size resources** based on actual usage
5. **Enable compression** for object storage
