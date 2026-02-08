"""
Event listener for object storage events.
Listens to various event sources (S3, MinIO) and converts them to standard format.
"""
import asyncio
import json
import logging
from typing import Callable, Optional
from datetime import datetime

from event_schemas import StorageEvent, EventType, ObjectIdentity, ObjectMetadataEvent, RequestParameters

logger = logging.getLogger(__name__)


class EventListener:
    """
    Listens to object storage events from various sources.
    Supports S3 Event Notifications, MinIO bucket notifications, etc.
    """
    
    def __init__(self, event_callback: Callable[[StorageEvent], None]):
        """
        Initialize event listener.
        
        Args:
            event_callback: Callback function to process received events
        """
        self.event_callback = event_callback
        self.running = False
        
    async def start(self):
        """Start listening for events."""
        self.running = True
        logger.info("Event listener started")
        
    async def stop(self):
        """Stop listening for events."""
        self.running = False
        logger.info("Event listener stopped")
        
    def parse_s3_event(self, raw_event: dict) -> Optional[StorageEvent]:
        """
        Parse S3/MinIO event notification into StorageEvent.
        
        Args:
            raw_event: Raw event dict from S3/MinIO
            
        Returns:
            Parsed StorageEvent or None if invalid
        """
        try:
            # S3 events come in Records array
            records = raw_event.get("Records", [])
            if not records:
                logger.warning("No records in S3 event")
                return None
                
            record = records[0]  # Process first record
            
            # Extract event details
            event_name = record.get("eventName", "")
            event_time_str = record.get("eventTime", "")
            
            # Parse S3 object details
            s3_info = record.get("s3", {})
            bucket_info = s3_info.get("bucket", {})
            object_info = s3_info.get("object", {})
            
            # Create object identity
            obj_identity = ObjectIdentity(
                bucket=bucket_info.get("name", ""),
                key=object_info.get("key", ""),
                version_id=object_info.get("versionId"),
                etag=object_info.get("eTag"),
                size=object_info.get("size"),
                sequencer=object_info.get("sequencer")
            )
            
            # Extract metadata
            user_metadata = record.get("userMetadata", {})
            
            metadata = ObjectMetadataEvent(
                content_type=user_metadata.get("content-type"),
                user_metadata=user_metadata,
                tags=user_metadata.get("tags", {})
            )
            
            # Extract request parameters
            request_params = record.get("requestParameters", {})
            req = RequestParameters(
                source_ip=request_params.get("sourceIPAddress"),
                principal_id=record.get("userIdentity", {}).get("principalId")
            )
            
            # Parse event time
            try:
                event_time = datetime.fromisoformat(event_time_str.replace("Z", "+00:00"))
            except:
                event_time = datetime.utcnow()
            
            # Map event name to EventType
            event_type = self._map_event_type(event_name)
            
            event = StorageEvent(
                event_version=record.get("eventVersion", "2.1"),
                event_source=record.get("eventSource", "aws:s3"),
                event_time=event_time,
                event_name=event_type,
                object=obj_identity,
                metadata=metadata,
                request_parameters=req,
                response_elements=record.get("responseElements", {})
            )
            
            return event
            
        except Exception as e:
            logger.error(f"Failed to parse S3 event: {e}", exc_info=True)
            return None
            
    def _map_event_type(self, event_name: str) -> EventType:
        """Map S3 event name to EventType enum."""
        mapping = {
            "s3:ObjectCreated:Put": EventType.PUT_OBJECT,
            "s3:ObjectCreated:Post": EventType.POST_OBJECT,
            "s3:ObjectCreated:Copy": EventType.COPY_OBJECT,
            "s3:ObjectCreated:CompleteMultipartUpload": EventType.COMPLETE_MULTIPART,
            "s3:ObjectTagging:Put": EventType.PUT_TAGGING,
            "s3:ObjectRemoved:Delete": EventType.DELETE_OBJECT,
            "s3:ObjectRemoved:DeleteMarkerCreated": EventType.DELETE_MARKER,
        }
        return mapping.get(event_name, EventType.PUT_OBJECT)
        
    async def process_event(self, raw_event: dict):
        """
        Process a raw event and invoke callback.
        
        Args:
            raw_event: Raw event dictionary
        """
        event = self.parse_s3_event(raw_event)
        if event:
            try:
                await self.event_callback(event)
            except Exception as e:
                logger.error(f"Error in event callback: {e}", exc_info=True)


class S3EventListener(EventListener):
    """Listener for S3 Event Notifications (SQS, SNS, etc.)."""
    
    def __init__(self, event_callback: Callable[[StorageEvent], None], queue_url: str):
        super().__init__(event_callback)
        self.queue_url = queue_url
        
    async def start(self):
        """Start listening to SQS queue for S3 events."""
        await super().start()
        # Implementation would use boto3 SQS client to poll for messages
        logger.info(f"S3 event listener started for queue: {self.queue_url}")


class MinIOEventListener(EventListener):
    """Listener for MinIO bucket notifications."""
    
    def __init__(self, event_callback: Callable[[StorageEvent], None], 
                 minio_endpoint: str, bucket: str):
        super().__init__(event_callback)
        self.minio_endpoint = minio_endpoint
        self.bucket = bucket
        
    async def start(self):
        """Start listening to MinIO bucket notifications."""
        await super().start()
        # Implementation would use MinIO client to listen to bucket notifications
        logger.info(f"MinIO event listener started for bucket: {self.bucket}")
