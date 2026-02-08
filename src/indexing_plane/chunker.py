"""
Text chunking strategies for semantic search.
Implements semantic, fixed-size, and sliding window chunking.
"""
import logging
from typing import List, Dict, Any
import re

logger = logging.getLogger(__name__)


class TextChunk:
    """Represents a chunk of text."""
    
    def __init__(self, text: str, start_offset: int, end_offset: int, 
                 chunk_index: int, metadata: Dict[str, Any] = None):
        """
        Initialize text chunk.
        
        Args:
            text: Chunk text
            start_offset: Start position in original text
            end_offset: End position in original text
            chunk_index: Index of this chunk
            metadata: Additional metadata
        """
        self.text = text
        self.start_offset = start_offset
        self.end_offset = end_offset
        self.chunk_index = chunk_index
        self.metadata = metadata or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "text": self.text,
            "start_offset": self.start_offset,
            "end_offset": self.end_offset,
            "chunk_index": self.chunk_index,
            "metadata": self.metadata
        }


class Chunker:
    """Base class for text chunking."""
    
    def chunk(self, text: str) -> List[TextChunk]:
        """
        Chunk text into smaller pieces.
        
        Args:
            text: Input text
            
        Returns:
            List of text chunks
        """
        raise NotImplementedError


class SemanticChunker(Chunker):
    """
    Semantic chunking based on sentences and paragraphs.
    Preserves semantic boundaries.
    """
    
    def __init__(self, max_chunk_size: int = 512, 
                 overlap: int = 50,
                 min_chunk_size: int = 50):
        """
        Initialize semantic chunker.
        
        Args:
            max_chunk_size: Maximum chunk size in characters
            overlap: Overlap between chunks in characters
            min_chunk_size: Minimum chunk size in characters
        """
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap
        self.min_chunk_size = min_chunk_size
        
    def chunk(self, text: str) -> List[TextChunk]:
        """Chunk text semantically."""
        if not text:
            return []
            
        # Split into paragraphs
        paragraphs = self._split_paragraphs(text)
        
        chunks = []
        current_chunk = ""
        current_start = 0
        chunk_index = 0
        
        for para in paragraphs:
            # If paragraph alone exceeds max size, split by sentences
            if len(para) > self.max_chunk_size:
                sentences = self._split_sentences(para)
                
                for sentence in sentences:
                    # If adding sentence would exceed max size, create chunk
                    if len(current_chunk) + len(sentence) > self.max_chunk_size:
                        if len(current_chunk) >= self.min_chunk_size:
                            chunk = TextChunk(
                                text=current_chunk.strip(),
                                start_offset=current_start,
                                end_offset=current_start + len(current_chunk),
                                chunk_index=chunk_index
                            )
                            chunks.append(chunk)
                            chunk_index += 1
                            
                            # Start new chunk with overlap
                            overlap_text = current_chunk[-self.overlap:]
                            current_chunk = overlap_text + " " + sentence
                            current_start = current_start + len(current_chunk) - len(overlap_text) - len(sentence) - 1
                        else:
                            current_chunk = sentence
                    else:
                        if current_chunk:
                            current_chunk += " " + sentence
                        else:
                            current_chunk = sentence
            else:
                # Try to add whole paragraph
                if len(current_chunk) + len(para) > self.max_chunk_size:
                    if len(current_chunk) >= self.min_chunk_size:
                        chunk = TextChunk(
                            text=current_chunk.strip(),
                            start_offset=current_start,
                            end_offset=current_start + len(current_chunk),
                            chunk_index=chunk_index
                        )
                        chunks.append(chunk)
                        chunk_index += 1
                        
                        # Start new chunk with overlap
                        overlap_text = current_chunk[-self.overlap:]
                        current_chunk = overlap_text + "\n\n" + para
                        current_start = current_start + len(current_chunk) - len(overlap_text) - len(para) - 2
                    else:
                        current_chunk = para
                else:
                    if current_chunk:
                        current_chunk += "\n\n" + para
                    else:
                        current_chunk = para
                        
        # Add final chunk
        if len(current_chunk) >= self.min_chunk_size:
            chunk = TextChunk(
                text=current_chunk.strip(),
                start_offset=current_start,
                end_offset=current_start + len(current_chunk),
                chunk_index=chunk_index
            )
            chunks.append(chunk)
            
        return chunks
        
    def _split_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs."""
        # Split on double newlines or multiple spaces
        paragraphs = re.split(r'\n\s*\n', text)
        return [p.strip() for p in paragraphs if p.strip()]
        
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+\s+', text)
        return [s.strip() for s in sentences if s.strip()]


class FixedSizeChunker(Chunker):
    """Fixed-size chunking with optional overlap."""
    
    def __init__(self, chunk_size: int = 512, overlap: int = 50):
        """
        Initialize fixed-size chunker.
        
        Args:
            chunk_size: Size of each chunk
            overlap: Overlap between chunks
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        
    def chunk(self, text: str) -> List[TextChunk]:
        """Chunk text into fixed-size pieces."""
        if not text:
            return []
            
        chunks = []
        chunk_index = 0
        start = 0
        
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunk_text = text[start:end]
            
            chunk = TextChunk(
                text=chunk_text,
                start_offset=start,
                end_offset=end,
                chunk_index=chunk_index
            )
            chunks.append(chunk)
            
            chunk_index += 1
            start = end - self.overlap
            
        return chunks


class SlidingWindowChunker(Chunker):
    """Sliding window chunking."""
    
    def __init__(self, window_size: int = 512, stride: int = 256):
        """
        Initialize sliding window chunker.
        
        Args:
            window_size: Size of sliding window
            stride: Step size for sliding
        """
        self.window_size = window_size
        self.stride = stride
        
    def chunk(self, text: str) -> List[TextChunk]:
        """Chunk text using sliding window."""
        if not text:
            return []
            
        chunks = []
        chunk_index = 0
        
        for start in range(0, len(text), self.stride):
            end = min(start + self.window_size, len(text))
            chunk_text = text[start:end]
            
            chunk = TextChunk(
                text=chunk_text,
                start_offset=start,
                end_offset=end,
                chunk_index=chunk_index
            )
            chunks.append(chunk)
            
            chunk_index += 1
            
            if end >= len(text):
                break
                
        return chunks


def create_chunker(config: dict) -> Chunker:
    """
    Create chunker from configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Chunker instance
    """
    strategy = config.get("strategy", "semantic")
    
    if strategy == "semantic":
        return SemanticChunker(
            max_chunk_size=config.get("max_chunk_size", 512),
            overlap=config.get("overlap", 50),
            min_chunk_size=config.get("min_chunk_size", 50)
        )
    elif strategy == "fixed":
        return FixedSizeChunker(
            chunk_size=config.get("max_chunk_size", 512),
            overlap=config.get("overlap", 50)
        )
    elif strategy == "sliding":
        return SlidingWindowChunker(
            window_size=config.get("max_chunk_size", 512),
            stride=config.get("max_chunk_size", 512) - config.get("overlap", 50)
        )
    else:
        raise ValueError(f"Unknown chunking strategy: {strategy}")
