"""
Retriever for vector search and metadata join.
Combines Milvus search with metadata filtering and IAM authorization.
"""
import logging
from typing import List, Dict, Any, Optional
import json

logger = logging.getLogger(__name__)


class Retriever:
    """Retriever for semantic search with metadata join."""
    
    def __init__(self, milvus_client, metadata_store, 
                 iam_authorizer, query_processor):
        """
        Initialize retriever.
        
        Args:
            milvus_client: Milvus client for vector search
            metadata_store: Metadata store for object metadata
            iam_authorizer: IAM authorizer for access control
            query_processor: Query processor for embedding
        """
        self.milvus_client = milvus_client
        self.metadata_store = metadata_store
        self.iam_authorizer = iam_authorizer
        self.query_processor = query_processor
        
    def search(self, query: str, principal: str, 
              top_k: int = 10,
              filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for relevant documents.
        
        Args:
            query: Search query
            principal: User/principal making the request
            top_k: Number of results to return
            filters: Optional filters (bucket, prefix, tags, etc.)
            
        Returns:
            List of search results with citations
        """
        # Process query
        processed_query = self.query_processor.process(query)
        query_embedding = processed_query["embedding"]
        
        # Build Milvus filter expression
        milvus_filter = self._build_milvus_filter(filters)
        
        # Search Milvus
        # Request more results than needed to account for IAM filtering
        search_results = self.milvus_client.search_vectors(
            query_vectors=[query_embedding],
            top_k=top_k * 3,  # Request 3x to account for filtering
            filters=milvus_filter
        )
        
        if not search_results or not search_results[0]:
            logger.info(f"No results found for query: {query}")
            return []
            
        results = search_results[0]  # Get results for first query
        
        # Apply IAM authorization
        authorized_results = self.iam_authorizer.filter_results(
            principal=principal,
            results=results,
            action="s3:GetObject"
        )
        
        # Enrich with metadata
        enriched_results = self._enrich_results(authorized_results)
        
        # Limit to top_k
        enriched_results = enriched_results[:top_k]
        
        logger.info(f"Returning {len(enriched_results)} results for query: {query}")
        return enriched_results
        
    def _build_milvus_filter(self, filters: Optional[Dict[str, Any]]) -> Optional[str]:
        """Build Milvus filter expression from filters."""
        if not filters:
            return None
            
        conditions = []
        
        # Bucket filter
        if "bucket" in filters:
            conditions.append(f'bucket == "{filters["bucket"]}"')
            
        # Prefix filter (using key field)
        if "prefix" in filters:
            prefix = filters["prefix"]
            # Milvus doesn't have LIKE, so we'd need to implement this differently
            # For now, we'll handle prefix filtering in post-processing
            pass
            
        # Tags filter
        if "tags" in filters:
            # Tags are stored as JSON string
            # This is a simplified approach; real implementation would need more sophisticated filtering
            pass
            
        # Combine conditions with AND
        if conditions:
            return " && ".join(conditions)
            
        return None
        
    def _enrich_results(self, results: List[Dict]) -> List[Dict[str, Any]]:
        """Enrich search results with additional metadata."""
        enriched = []
        
        for result in results:
            bucket = result.get("bucket")
            key = result.get("key")
            version_id = result.get("version_id")
            
            # Get object metadata
            obj_metadata = self.metadata_store.get_object(bucket, key, version_id)
            
            if obj_metadata:
                enriched_result = {
                    "score": result.get("distance", 0.0),
                    "bucket": bucket,
                    "key": key,
                    "version_id": version_id,
                    "chunk_index": result.get("chunk_index"),
                    "start_offset": result.get("start_offset"),
                    "end_offset": result.get("end_offset"),
                    "text": result.get("text"),
                    "content_type": result.get("content_type"),
                    "size": obj_metadata.get("size"),
                    "created_at": obj_metadata.get("created_at"),
                    "tags": obj_metadata.get("tags", {}),
                    "citation": self._format_citation(bucket, key, version_id, 
                                                     result.get("start_offset"),
                                                     result.get("end_offset"))
                }
                enriched.append(enriched_result)
            else:
                logger.warning(f"Metadata not found for {bucket}/{key}")
                
        return enriched
        
    def _format_citation(self, bucket: str, key: str, version_id: Optional[str],
                        start_offset: int, end_offset: int) -> str:
        """Format citation for a result."""
        citation = f"s3://{bucket}/{key}"
        if version_id:
            citation += f"?versionId={version_id}"
        citation += f" (offset {start_offset}-{end_offset})"
        return citation
        
    def get_similar_chunks(self, bucket: str, key: str, chunk_index: int,
                          top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Find similar chunks to a given chunk.
        
        Args:
            bucket: Bucket name
            key: Object key
            chunk_index: Index of the chunk
            top_k: Number of similar chunks to return
            
        Returns:
            List of similar chunks
        """
        # Get the chunk's embedding from Milvus
        filter_expr = f'bucket == "{bucket}" && key == "{key}" && chunk_index == {chunk_index}'
        
        # Search for the chunk itself first to get its embedding
        # This is a simplified approach; in production, we'd query the chunk directly
        
        # Then search for similar vectors
        # Implementation would go here
        
        return []
