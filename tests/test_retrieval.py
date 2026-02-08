"""
Tests for retrieval and search.
"""
import pytest
import sys
sys.path.insert(0, '../src/query_plane')
sys.path.insert(0, '../src/indexing_plane')

from query_processor import QueryProcessor


class MockEmbedder:
    """Mock embedder for testing."""
    
    def embed(self, text):
        """Return mock embedding."""
        if isinstance(text, str):
            return [0.1] * 768
        return [[0.1] * 768 for _ in text]
        
    def get_dimension(self):
        return 768


class TestQueryProcessor:
    """Test query processing."""
    
    def test_process_query(self):
        """Test basic query processing."""
        embedder = MockEmbedder()
        processor = QueryProcessor(embedder)
        
        result = processor.process("test query")
        
        assert result["original_query"] == "test query"
        assert result["cleaned_query"] == "test query"
        assert len(result["embedding"]) == 768
        assert "features" in result
        
    def test_clean_query(self):
        """Test query cleaning."""
        embedder = MockEmbedder()
        processor = QueryProcessor(embedder)
        
        # Test whitespace normalization
        result = processor.process("test   query   with   spaces")
        assert result["cleaned_query"] == "test query with spaces"
        
        # Test leading/trailing whitespace
        result = processor.process("  test query  ")
        assert result["cleaned_query"] == "test query"
        
    def test_extract_features(self):
        """Test feature extraction."""
        embedder = MockEmbedder()
        processor = QueryProcessor(embedder)
        
        result = processor.process("Is this a question?")
        
        assert result["features"]["has_question_mark"] is True
        assert result["features"]["word_count"] == 4
        assert result["features"]["length"] > 0
        
    def test_batch_process(self):
        """Test batch query processing."""
        embedder = MockEmbedder()
        processor = QueryProcessor(embedder)
        
        queries = ["query 1", "query 2", "query 3"]
        results = processor.batch_process(queries)
        
        assert len(results) == 3
        assert all("embedding" in r for r in results)


class TestRetrieval:
    """Test retrieval logic."""
    
    def test_citation_formatting(self):
        """Test citation string formatting."""
        # This would test the _format_citation method
        # from the Retriever class
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
