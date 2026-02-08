"""
REST API for semantic search and RAG.
Provides endpoints for search, RAG Q&A, and index management.
"""
import logging
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, Depends, Query, Header
from pydantic import BaseModel, Field
import yaml

from retriever import Retriever
from rag_engine import RAGEngine
from iam_authorizer import IAMAuthorizer
from query_processor import QueryProcessor

# Import indexing plane components
import sys
sys.path.append('../indexing_plane')
from milvus_client import MilvusClient
from metadata_store import MetadataStore
from embedder import create_embedder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Smart Object Storage Search API",
    description="Semantic search and RAG API for object storage",
    version="0.1.0"
)


# Request/Response models
class SearchRequest(BaseModel):
    """Search request model."""
    query: str = Field(..., description="Search query")
    top_k: int = Field(default=10, ge=1, le=100, description="Number of results")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Search filters")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "machine learning best practices",
                "top_k": 10,
                "filters": {
                    "bucket": "my-documents",
                    "prefix": "ml/",
                    "tags": {"department": "research"}
                }
            }
        }


class SearchResult(BaseModel):
    """Search result model."""
    score: float
    bucket: str
    key: str
    version_id: Optional[str]
    chunk_index: int
    start_offset: int
    end_offset: int
    text: str
    content_type: str
    citation: str
    

class SearchResponse(BaseModel):
    """Search response model."""
    query: str
    results: List[SearchResult]
    total_results: int


class RAGRequest(BaseModel):
    """RAG Q&A request model."""
    question: str = Field(..., description="Question to answer")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of context chunks")
    include_citations: bool = Field(default=True, description="Include citations")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Search filters")
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "What are the key features of our product?",
                "top_k": 5,
                "include_citations": True,
                "filters": {"bucket": "product-docs"}
            }
        }


class RAGResponse(BaseModel):
    """RAG Q&A response model."""
    question: str
    answer: str
    confidence: float
    citations: Optional[List[Dict[str, Any]]]
    sources: Optional[List[str]]


class IndexStatusResponse(BaseModel):
    """Index status response model."""
    bucket: str
    key: str
    version_id: Optional[str]
    indexed: bool
    chunk_count: Optional[int]
    last_indexed: Optional[str]


# Global components (initialized at startup)
milvus_client = None
metadata_store = None
embedder = None
query_processor = None
iam_authorizer = None
retriever = None
rag_engine = None


def load_config(config_path: str) -> dict:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def get_principal(x_principal: Optional[str] = Header(None)) -> str:
    """Get principal from request header."""
    if not x_principal:
        # Default to anonymous if no principal provided
        return "*"
    return x_principal


@app.on_event("startup")
async def startup_event():
    """Initialize components on startup."""
    global milvus_client, metadata_store, embedder, query_processor
    global iam_authorizer, retriever, rag_engine
    
    logger.info("Initializing Search API...")
    
    try:
        # Load configs
        milvus_config = load_config("../../config/milvus_config.yaml")
        worker_config = load_config("../../config/worker_config.yaml")
        embedding_config = load_config("../../config/embedding_config.yaml")
        
        # Initialize Milvus
        milvus_client = MilvusClient(
            host=milvus_config["milvus"]["host"],
            port=milvus_config["milvus"]["port"]
        )
        milvus_client.connect()
        milvus_client.load_collection(milvus_config["milvus"]["collection"]["name"])
        
        # Initialize metadata store
        db_config = worker_config["database"]["postgresql"]
        connection_string = (
            f"postgresql://{db_config['user']}:{db_config['password']}"
            f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        )
        metadata_store = MetadataStore(connection_string)
        
        # Initialize embedder
        embedder = create_embedder(embedding_config["embedding"])
        
        # Initialize query processor
        query_processor = QueryProcessor(embedder)
        
        # Initialize IAM authorizer
        iam_authorizer = IAMAuthorizer(metadata_store)
        
        # Initialize retriever
        retriever = Retriever(milvus_client, metadata_store, iam_authorizer, query_processor)
        
        # Initialize RAG engine
        rag_engine = RAGEngine(retriever)
        
        logger.info("Search API initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize Search API: {e}", exc_info=True)
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    if milvus_client:
        milvus_client.disconnect()
    logger.info("Search API shutdown complete")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Smart Object Storage Search API",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "milvus": "connected" if milvus_client else "disconnected",
        "database": "connected" if metadata_store else "disconnected"
    }


@app.post("/api/v1/search", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    principal: str = Depends(get_principal)
):
    """
    Semantic search endpoint.
    
    Search for objects semantically similar to the query.
    Results are filtered based on IAM policies.
    """
    try:
        logger.info(f"Search request from {principal}: {request.query}")
        
        results = retriever.search(
            query=request.query,
            principal=principal,
            top_k=request.top_k,
            filters=request.filters
        )
        
        return SearchResponse(
            query=request.query,
            results=[SearchResult(**r) for r in results],
            total_results=len(results)
        )
        
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/rag/query", response_model=RAGResponse)
async def rag_query(
    request: RAGRequest,
    principal: str = Depends(get_principal)
):
    """
    RAG Q&A endpoint.
    
    Answer a question using retrieval-augmented generation.
    Includes citations to source documents.
    """
    try:
        logger.info(f"RAG request from {principal}: {request.question}")
        
        response = rag_engine.answer_question(
            question=request.question,
            principal=principal,
            top_k=request.top_k,
            filters=request.filters,
            include_citations=request.include_citations
        )
        
        return RAGResponse(**response)
        
    except Exception as e:
        logger.error(f"RAG query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/index/status/{bucket}/{key}", response_model=IndexStatusResponse)
async def get_index_status(
    bucket: str,
    key: str,
    version_id: Optional[str] = Query(None),
    principal: str = Depends(get_principal)
):
    """
    Get indexing status for an object.
    
    Returns whether the object is indexed and metadata about the indexing.
    """
    try:
        # Check IAM authorization
        resource = f"{bucket}/{key}"
        if not iam_authorizer.authorize(principal, resource, "s3:GetObject"):
            raise HTTPException(status_code=403, detail="Access denied")
            
        # Get object metadata
        obj_metadata = metadata_store.get_object(bucket, key, version_id)
        
        if not obj_metadata:
            return IndexStatusResponse(
                bucket=bucket,
                key=key,
                version_id=version_id,
                indexed=False,
                chunk_count=None,
                last_indexed=None
            )
            
        # Get chunks
        chunks = metadata_store.get_chunks_by_object(obj_metadata["id"])
        
        return IndexStatusResponse(
            bucket=bucket,
            key=key,
            version_id=version_id,
            indexed=len(chunks) > 0,
            chunk_count=len(chunks),
            last_indexed=obj_metadata.get("created_at")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Status check failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/stats")
async def get_stats():
    """Get collection statistics."""
    try:
        stats = milvus_client.get_collection_stats()
        return {
            "vector_count": stats["num_entities"],
            "collection_name": stats["name"]
        }
    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
