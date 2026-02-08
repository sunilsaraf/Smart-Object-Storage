"""
Embedding generation using various models.
Supports Sentence Transformers, OpenAI, and custom models.
"""
import logging
from typing import List, Union
import numpy as np

logger = logging.getLogger(__name__)


class Embedder:
    """Base class for embedding generation."""
    
    def embed(self, texts: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """
        Generate embeddings for text(s).
        
        Args:
            texts: Single text or list of texts
            
        Returns:
            Single embedding or list of embeddings
        """
        raise NotImplementedError
        
    def get_dimension(self) -> int:
        """Get embedding dimension."""
        raise NotImplementedError


class SentenceTransformerEmbedder(Embedder):
    """Embedder using Sentence Transformers."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", 
                 device: str = "cpu",
                 batch_size: int = 32,
                 normalize: bool = True):
        """
        Initialize Sentence Transformer embedder.
        
        Args:
            model_name: Model name from sentence-transformers
            device: Device to use (cpu, cuda)
            batch_size: Batch size for encoding
            normalize: Whether to normalize embeddings
        """
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name, device=device)
            self.batch_size = batch_size
            self.normalize = normalize
            logger.info(f"Loaded Sentence Transformer model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
            
    def embed(self, texts: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """Generate embeddings using Sentence Transformers."""
        single_input = isinstance(texts, str)
        if single_input:
            texts = [texts]
            
        try:
            embeddings = self.model.encode(
                texts,
                batch_size=self.batch_size,
                normalize_embeddings=self.normalize,
                convert_to_numpy=True
            )
            
            # Convert to list
            embeddings = embeddings.tolist()
            
            if single_input:
                return embeddings[0]
            return embeddings
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise
            
    def get_dimension(self) -> int:
        """Get embedding dimension."""
        return self.model.get_sentence_embedding_dimension()


class OpenAIEmbedder(Embedder):
    """Embedder using OpenAI API."""
    
    def __init__(self, api_key: str, model: str = "text-embedding-ada-002"):
        """
        Initialize OpenAI embedder.
        
        Args:
            api_key: OpenAI API key
            model: Model name
        """
        try:
            import openai
            openai.api_key = api_key
            self.client = openai.OpenAI(api_key=api_key)
            self.model = model
            logger.info(f"Initialized OpenAI embedder with model: {model}")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI: {e}")
            raise
            
    def embed(self, texts: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """Generate embeddings using OpenAI API."""
        single_input = isinstance(texts, str)
        if single_input:
            texts = [texts]
            
        try:
            response = self.client.embeddings.create(
                input=texts,
                model=self.model
            )
            
            embeddings = [item.embedding for item in response.data]
            
            if single_input:
                return embeddings[0]
            return embeddings
            
        except Exception as e:
            logger.error(f"OpenAI embedding failed: {e}")
            raise
            
    def get_dimension(self) -> int:
        """Get embedding dimension."""
        # Ada-002 has 1536 dimensions
        if "ada-002" in self.model:
            return 1536
        return 1536  # Default


class CachedEmbedder(Embedder):
    """Embedder with caching layer."""
    
    def __init__(self, base_embedder: Embedder, cache_size: int = 10000):
        """
        Initialize cached embedder.
        
        Args:
            base_embedder: Underlying embedder
            cache_size: Maximum cache size
        """
        self.base_embedder = base_embedder
        self.cache = {}
        self.cache_size = cache_size
        
    def embed(self, texts: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """Generate embeddings with caching."""
        single_input = isinstance(texts, str)
        if single_input:
            texts = [texts]
            
        # Check cache
        results = []
        texts_to_embed = []
        text_indices = []
        
        for i, text in enumerate(texts):
            if text in self.cache:
                results.append(self.cache[text])
            else:
                results.append(None)
                texts_to_embed.append(text)
                text_indices.append(i)
                
        # Embed uncached texts
        if texts_to_embed:
            new_embeddings = self.base_embedder.embed(texts_to_embed)
            if isinstance(new_embeddings[0], float):
                new_embeddings = [new_embeddings]
                
            # Update cache and results
            for i, embedding in zip(text_indices, new_embeddings):
                results[i] = embedding
                texts[i] in self.cache  # Simplified, should use LRU cache
                self.cache[texts[i]] = embedding
                
            # Limit cache size (simple approach)
            if len(self.cache) > self.cache_size:
                # Remove oldest entries
                keys_to_remove = list(self.cache.keys())[:len(self.cache) - self.cache_size]
                for key in keys_to_remove:
                    del self.cache[key]
                    
        if single_input:
            return results[0]
        return results
        
    def get_dimension(self) -> int:
        """Get embedding dimension."""
        return self.base_embedder.get_dimension()


def create_embedder(config: dict) -> Embedder:
    """
    Create embedder from configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Embedder instance
    """
    provider = config.get("provider", "sentence-transformers")
    
    if provider == "sentence-transformers":
        st_config = config.get("sentence_transformers", {})
        embedder = SentenceTransformerEmbedder(
            model_name=st_config.get("model_name", "all-MiniLM-L6-v2"),
            device=st_config.get("device", "cpu"),
            batch_size=st_config.get("batch_size", 32),
            normalize=st_config.get("normalize_embeddings", True)
        )
    elif provider == "openai":
        openai_config = config.get("openai", {})
        import os
        api_key = os.getenv("OPENAI_API_KEY") or openai_config.get("api_key")
        embedder = OpenAIEmbedder(
            api_key=api_key,
            model=openai_config.get("model", "text-embedding-ada-002")
        )
    else:
        raise ValueError(f"Unsupported embedding provider: {provider}")
        
    # Wrap with cache if enabled
    cache_config = config.get("cache", {})
    if cache_config.get("enabled", True):
        embedder = CachedEmbedder(
            embedder,
            cache_size=cache_config.get("max_size", 10000)
        )
        
    return embedder
