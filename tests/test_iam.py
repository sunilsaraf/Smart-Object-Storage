"""
Tests for IAM authorization.
"""
import pytest
import sys
sys.path.insert(0, '../src/query_plane')
sys.path.insert(0, '../src/indexing_plane')

from iam_authorizer import IAMAuthorizer
from metadata_store import MetadataStore


class MockMetadataStore:
    """Mock metadata store for testing."""
    
    def __init__(self):
        self.policies = [
            {
                "id": "1",
                "principal": "user1",
                "resource_pattern": "bucket1/*",
                "actions": ["s3:GetObject"],
                "effect": "ALLOW",
                "conditions": {}
            },
            {
                "id": "2",
                "principal": "*",
                "resource_pattern": "public/*",
                "actions": ["s3:GetObject"],
                "effect": "ALLOW",
                "conditions": {}
            },
            {
                "id": "3",
                "principal": "user2",
                "resource_pattern": "secret/*",
                "actions": ["s3:*"],
                "effect": "DENY",
                "conditions": {}
            }
        ]
        
    def get_iam_policies(self, principal):
        """Get policies for principal."""
        matching = [
            p for p in self.policies 
            if p["principal"] == principal or p["principal"] == "*"
        ]
        return matching


class TestIAMAuthorizer:
    """Test IAM authorization."""
    
    def test_allow_policy(self):
        """Test ALLOW policy."""
        store = MockMetadataStore()
        authorizer = IAMAuthorizer(store)
        
        # user1 should have access to bucket1
        assert authorizer.authorize("user1", "bucket1/file.txt", "s3:GetObject")
        
    def test_wildcard_allow(self):
        """Test wildcard ALLOW policy."""
        store = MockMetadataStore()
        authorizer = IAMAuthorizer(store)
        
        # Any user should have access to public bucket
        assert authorizer.authorize("anyuser", "public/file.txt", "s3:GetObject")
        
    def test_deny_takes_precedence(self):
        """Test DENY takes precedence over ALLOW."""
        store = MockMetadataStore()
        authorizer = IAMAuthorizer(store)
        
        # user2 has explicit DENY for secret bucket
        assert not authorizer.authorize("user2", "secret/file.txt", "s3:GetObject")
        
    def test_no_matching_policy(self):
        """Test default deny when no matching policy."""
        store = MockMetadataStore()
        authorizer = IAMAuthorizer(store)
        
        # user3 has no policies
        assert not authorizer.authorize("user3", "bucket1/file.txt", "s3:GetObject")
        
    def test_filter_results(self):
        """Test filtering search results."""
        store = MockMetadataStore()
        authorizer = IAMAuthorizer(store)
        
        results = [
            {"bucket": "bucket1", "key": "file1.txt", "text": "content1"},
            {"bucket": "bucket2", "key": "file2.txt", "text": "content2"},
            {"bucket": "public", "key": "file3.txt", "text": "content3"}
        ]
        
        # user1 should only get bucket1 and public results
        filtered = authorizer.filter_results("user1", results)
        
        assert len(filtered) == 2
        assert any(r["bucket"] == "bucket1" for r in filtered)
        assert any(r["bucket"] == "public" for r in filtered)
        
    def test_resource_pattern_matching(self):
        """Test resource pattern matching with wildcards."""
        store = MockMetadataStore()
        authorizer = IAMAuthorizer(store)
        
        # Test wildcard matching
        assert authorizer._matches_resource("bucket1/*", "bucket1/file.txt")
        assert authorizer._matches_resource("bucket1/*", "bucket1/folder/file.txt")
        assert not authorizer._matches_resource("bucket1/*", "bucket2/file.txt")
        
        # Test exact match
        assert authorizer._matches_resource("bucket1/file.txt", "bucket1/file.txt")
        assert not authorizer._matches_resource("bucket1/file.txt", "bucket1/other.txt")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
