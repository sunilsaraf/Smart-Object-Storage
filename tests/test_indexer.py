"""
Tests for indexing pipeline.
"""
import pytest
import sys
sys.path.insert(0, '../src/indexing_plane')

from chunker import SemanticChunker, FixedSizeChunker
from text_extractor import TextExtractor


class TestChunker:
    """Test text chunking."""
    
    def test_semantic_chunker_basic(self):
        """Test basic semantic chunking."""
        chunker = SemanticChunker(max_chunk_size=100, overlap=20, min_chunk_size=10)
        
        text = "This is the first sentence. This is the second sentence. This is the third sentence."
        chunks = chunker.chunk(text)
        
        assert len(chunks) > 0
        assert all(chunk.text for chunk in chunks)
        assert all(chunk.start_offset >= 0 for chunk in chunks)
        assert all(chunk.end_offset > chunk.start_offset for chunk in chunks)
        
    def test_semantic_chunker_paragraphs(self):
        """Test semantic chunking with paragraphs."""
        chunker = SemanticChunker(max_chunk_size=200, overlap=20)
        
        text = """This is the first paragraph. It has multiple sentences.
        
        This is the second paragraph. It also has content.
        
        This is the third paragraph."""
        
        chunks = chunker.chunk(text)
        assert len(chunks) > 0
        
    def test_fixed_size_chunker(self):
        """Test fixed-size chunking."""
        chunker = FixedSizeChunker(chunk_size=50, overlap=10)
        
        text = "A" * 200  # 200 character string
        chunks = chunker.chunk(text)
        
        assert len(chunks) > 1
        # Check overlap
        if len(chunks) > 1:
            assert chunks[0].end_offset - chunks[1].start_offset == 10
            
    def test_empty_text(self):
        """Test chunking empty text."""
        chunker = SemanticChunker()
        chunks = chunker.chunk("")
        assert len(chunks) == 0


class TestTextExtractor:
    """Test text extraction."""
    
    def test_extract_plain_text(self):
        """Test extracting plain text."""
        extractor = TextExtractor()
        
        content = b"This is plain text content"
        text = extractor.extract(content, "text/plain")
        
        assert text == "This is plain text content"
        
    def test_extract_html(self):
        """Test extracting HTML."""
        extractor = TextExtractor()
        
        content = b"<html><body><p>Hello World</p></body></html>"
        text = extractor.extract(content, "text/html")
        
        assert "Hello World" in text
        
    def test_unsupported_format(self):
        """Test unsupported format returns empty."""
        extractor = TextExtractor()
        
        content = b"binary data"
        text = extractor.extract(content, "application/octet-stream")
        
        # Should return empty or handle gracefully
        assert isinstance(text, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
