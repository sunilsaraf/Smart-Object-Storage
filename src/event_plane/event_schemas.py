"""
Event schemas for object storage events.
Defines data models for events emitted by object storage systems.
"""
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Types of object storage events."""
    PUT_OBJECT = "s3:ObjectCreated:Put"
    POST_OBJECT = "s3:ObjectCreated:Post"
    COPY_OBJECT = "s3:ObjectCreated:Copy"
    COMPLETE_MULTIPART = "s3:ObjectCreated:CompleteMultipartUpload"
    PUT_TAGGING = "s3:ObjectTagging:Put"
    DELETE_OBJECT = "s3:ObjectRemoved:Delete"
    DELETE_MARKER = "s3:ObjectRemoved:DeleteMarkerCreated"


class ObjectIdentity(BaseModel):
    """Identity of an object in storage."""
    bucket: str = Field(..., description="Bucket name")
    key: str = Field(..., description="Object key")
    version_id: Optional[str] = Field(None, description="Version ID")
    etag: Optional[str] = Field(None, description="Entity tag")
    size: Optional[int] = Field(None, description="Object size in bytes")
    sequencer: Optional[str] = Field(None, description="Event sequencer for ordering")


class ObjectMetadataEvent(BaseModel):
    """Metadata associated with an object event."""
    content_type: Optional[str] = None
    user_metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: Dict[str, str] = Field(default_factory=dict)
    acl: Dict[str, Any] = Field(default_factory=dict)


class RequestParameters(BaseModel):
    """Request parameters from the storage operation."""
    source_ip: Optional[str] = None
    principal_id: Optional[str] = None
    region: Optional[str] = None


class StorageEvent(BaseModel):
    """
    Represents a storage event (S3-compatible).
    Based on AWS S3 Event Notification structure.
    """
    event_version: str = Field(default="2.1", description="Event schema version")
    event_source: str = Field(default="aws:s3", description="Event source")
    event_time: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    event_name: EventType = Field(..., description="Type of event")
    
    # Object identity
    object: ObjectIdentity = Field(..., description="Object identity")
    
    # Additional metadata
    metadata: ObjectMetadataEvent = Field(default_factory=ObjectMetadataEvent)
    
    # Request context
    request_parameters: RequestParameters = Field(default_factory=RequestParameters)
    
    # Response elements
    response_elements: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_version": "2.1",
                "event_source": "aws:s3",
                "event_time": "2024-01-15T10:30:00Z",
                "event_name": "s3:ObjectCreated:Put",
                "object": {
                    "bucket": "my-bucket",
                    "key": "documents/report.pdf",
                    "version_id": "abc123",
                    "etag": "d41d8cd98f00b204e9800998ecf8427e",
                    "size": 1024000
                },
                "metadata": {
                    "content_type": "application/pdf",
                    "tags": {
                        "department": "engineering",
                        "project": "alpha"
                    }
                },
                "request_parameters": {
                    "source_ip": "192.168.1.100",
                    "principal_id": "user123"
                }
            }
        }


class IndexingCommand(BaseModel):
    """Command to index an object."""
    event: StorageEvent
    priority: int = Field(default=0, description="Processing priority (higher = more urgent)")
    retry_count: int = Field(default=0, description="Number of retry attempts")
    
    
class DeletionCommand(BaseModel):
    """Command to delete object vectors."""
    bucket: str
    key: str
    version_id: Optional[str] = None
    delete_all_versions: bool = Field(default=False, description="Delete all versions of the object")
    event_time: datetime = Field(default_factory=datetime.utcnow)


class EventBatch(BaseModel):
    """Batch of events for bulk processing."""
    events: list[StorageEvent]
    batch_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
