"""
Milvus client for vector database operations.
Handles collection management and vector operations.
"""
import logging
from typing import List, Dict, Any, Optional
from pymilvus import (
    connections, Collection, CollectionSchema, FieldSchema, 
    DataType, utility
)

logger = logging.getLogger(__name__)


class MilvusClient:
    """Client for Milvus vector database operations."""
    
    def __init__(self, host: str = "localhost", port: int = 19530,
                 user: str = "", password: str = ""):
        """
        Initialize Milvus client.
        
        Args:
            host: Milvus server host
            port: Milvus server port
            user: Username for authentication
            password: Password for authentication
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.collection = None
        
    def connect(self):
        """Connect to Milvus server."""
        try:
            connections.connect(
                alias="default",
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password
            )
            logger.info(f"Connected to Milvus at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {e}")
            raise
            
    def create_collection(self, collection_name: str, dimension: int = 768,
                         metric_type: str = "IP", index_type: str = "IVF_FLAT",
                         index_params: Optional[Dict] = None):
        """
        Create a new collection with schema for object chunks.
        
        Args:
            collection_name: Name of the collection
            dimension: Vector dimension
            metric_type: Distance metric (IP, L2, COSINE)
            index_type: Index type (IVF_FLAT, HNSW, etc.)
            index_params: Index parameters
        """
        if utility.has_collection(collection_name):
            logger.info(f"Collection {collection_name} already exists")
            self.collection = Collection(collection_name)
            return
            
        # Define schema
        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=255),
            FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=dimension),
            FieldSchema(name="bucket", dtype=DataType.VARCHAR, max_length=255),
            FieldSchema(name="key", dtype=DataType.VARCHAR, max_length=1024),
            FieldSchema(name="version_id", dtype=DataType.VARCHAR, max_length=255),
            FieldSchema(name="chunk_index", dtype=DataType.INT64),
            FieldSchema(name="start_offset", dtype=DataType.INT64),
            FieldSchema(name="end_offset", dtype=DataType.INT64),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="content_type", dtype=DataType.VARCHAR, max_length=255),
            FieldSchema(name="tags", dtype=DataType.VARCHAR, max_length=2048),  # JSON string
        ]
        
        schema = CollectionSchema(fields=fields, description="Object chunk embeddings")
        
        # Create collection
        self.collection = Collection(name=collection_name, schema=schema)
        logger.info(f"Created collection: {collection_name}")
        
        # Create index
        if index_params is None:
            index_params = {"nlist": 1024}
            
        index = {
            "index_type": index_type,
            "metric_type": metric_type,
            "params": index_params
        }
        
        self.collection.create_index(field_name="vector", index_params=index)
        logger.info(f"Created index on collection: {collection_name}")
        
    def load_collection(self, collection_name: str):
        """Load collection into memory for searching."""
        if not self.collection:
            self.collection = Collection(collection_name)
        self.collection.load()
        logger.info(f"Loaded collection: {collection_name}")
        
    def insert_vectors(self, data: List[Dict[str, Any]]) -> List[str]:
        """
        Insert vectors into collection.
        
        Args:
            data: List of dictionaries with vector data
            
        Returns:
            List of inserted IDs
        """
        if not self.collection:
            raise ValueError("Collection not initialized")
            
        try:
            # Prepare data for insertion
            entities = [
                [item["id"] for item in data],
                [item["vector"] for item in data],
                [item["bucket"] for item in data],
                [item["key"] for item in data],
                [item["version_id"] for item in data],
                [item["chunk_index"] for item in data],
                [item["start_offset"] for item in data],
                [item["end_offset"] for item in data],
                [item["text"] for item in data],
                [item["content_type"] for item in data],
                [item["tags"] for item in data],
            ]
            
            result = self.collection.insert(entities)
            self.collection.flush()
            
            logger.debug(f"Inserted {len(data)} vectors")
            return result.primary_keys
            
        except Exception as e:
            logger.error(f"Failed to insert vectors: {e}")
            raise
            
    def search_vectors(self, query_vectors: List[List[float]], 
                      top_k: int = 10,
                      filters: Optional[str] = None,
                      search_params: Optional[Dict] = None) -> List[List[Dict]]:
        """
        Search for similar vectors.
        
        Args:
            query_vectors: List of query vectors
            top_k: Number of results to return
            filters: Filter expression
            search_params: Search parameters
            
        Returns:
            List of search results for each query
        """
        if not self.collection:
            raise ValueError("Collection not initialized")
            
        if search_params is None:
            search_params = {"nprobe": 10}
            
        try:
            output_fields = [
                "bucket", "key", "version_id", "chunk_index", 
                "start_offset", "end_offset", "text", "content_type", "tags"
            ]
            
            results = self.collection.search(
                data=query_vectors,
                anns_field="vector",
                param=search_params,
                limit=top_k,
                expr=filters,
                output_fields=output_fields
            )
            
            # Format results
            formatted_results = []
            for hits in results:
                hit_list = []
                for hit in hits:
                    hit_dict = {
                        "id": hit.id,
                        "distance": hit.distance,
                        "bucket": hit.entity.get("bucket"),
                        "key": hit.entity.get("key"),
                        "version_id": hit.entity.get("version_id"),
                        "chunk_index": hit.entity.get("chunk_index"),
                        "start_offset": hit.entity.get("start_offset"),
                        "end_offset": hit.entity.get("end_offset"),
                        "text": hit.entity.get("text"),
                        "content_type": hit.entity.get("content_type"),
                        "tags": hit.entity.get("tags"),
                    }
                    hit_list.append(hit_dict)
                formatted_results.append(hit_list)
                
            return formatted_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise
            
    def delete_vectors(self, expr: str):
        """
        Delete vectors matching expression.
        
        Args:
            expr: Filter expression (e.g., 'bucket == "my-bucket" && key == "file.txt"')
        """
        if not self.collection:
            raise ValueError("Collection not initialized")
            
        try:
            self.collection.delete(expr)
            self.collection.flush()
            logger.info(f"Deleted vectors matching: {expr}")
        except Exception as e:
            logger.error(f"Failed to delete vectors: {e}")
            raise
            
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        if not self.collection:
            raise ValueError("Collection not initialized")
            
        stats = self.collection.num_entities
        return {
            "num_entities": stats,
            "name": self.collection.name
        }
        
    def disconnect(self):
        """Disconnect from Milvus."""
        connections.disconnect("default")
        logger.info("Disconnected from Milvus")
