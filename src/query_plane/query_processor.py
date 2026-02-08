"""
Query processor for embedding and preprocessing queries.
"""
import logging
from typing import List
import re

logger = logging.getLogger(__name__)


class QueryProcessor:
    """Process and prepare queries for vector search."""
    
    def __init__(self, embedder):
        """
        Initialize query processor.
        
        Args:
            embedder: Embedder instance for query embedding
        """
        self.embedder = embedder
        
    def process(self, query: str) -> dict:
        """
        Process a query.
        
        Args:
            query: Raw query string
            
        Returns:
            Processed query dict with embedding and metadata
        """
        # Clean query
        cleaned_query = self._clean_query(query)
        
        # Generate embedding
        embedding = self.embedder.embed(cleaned_query)
        
        # Extract query features
        features = self._extract_features(cleaned_query)
        
        return {
            "original_query": query,
            "cleaned_query": cleaned_query,
            "embedding": embedding,
            "features": features
        }
        
    def _clean_query(self, query: str) -> str:
        """Clean and normalize query text."""
        # Remove extra whitespace
        query = re.sub(r'\s+', ' ', query)
        
        # Strip leading/trailing whitespace
        query = query.strip()
        
        return query
        
    def _extract_features(self, query: str) -> dict:
        """Extract features from query."""
        return {
            "length": len(query),
            "word_count": len(query.split()),
            "has_question_mark": "?" in query
        }
        
    def batch_process(self, queries: List[str]) -> List[dict]:
        """
        Process multiple queries in batch.
        
        Args:
            queries: List of query strings
            
        Returns:
            List of processed queries
        """
        return [self.process(q) for q in queries]
