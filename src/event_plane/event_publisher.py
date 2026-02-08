"""
Event publisher for publishing events to message queues.
Supports Kafka, AWS SQS, Google Pub/Sub.
"""
import asyncio
import json
import logging
from typing import Optional
from datetime import datetime

from event_schemas import StorageEvent, IndexingCommand, DeletionCommand

logger = logging.getLogger(__name__)


class EventPublisher:
    """Base class for event publishers."""
    
    async def publish_indexing_event(self, event: StorageEvent, priority: int = 0):
        """
        Publish an indexing event.
        
        Args:
            event: Storage event to publish
            priority: Priority level (higher = more urgent)
        """
        raise NotImplementedError
        
    async def publish_deletion_event(self, bucket: str, key: str, 
                                     version_id: Optional[str] = None):
        """
        Publish a deletion event.
        
        Args:
            bucket: Bucket name
            key: Object key
            version_id: Optional version ID
        """
        raise NotImplementedError
        
    async def close(self):
        """Close publisher connections."""
        pass


class KafkaEventPublisher(EventPublisher):
    """Kafka event publisher."""
    
    def __init__(self, bootstrap_servers: list[str], 
                 index_topic: str, delete_topic: str):
        """
        Initialize Kafka publisher.
        
        Args:
            bootstrap_servers: List of Kafka broker addresses
            index_topic: Topic for indexing events
            delete_topic: Topic for deletion events
        """
        self.bootstrap_servers = bootstrap_servers
        self.index_topic = index_topic
        self.delete_topic = delete_topic
        self.producer = None
        
    async def connect(self):
        """Connect to Kafka."""
        try:
            from aiokafka import AIOKafkaProducer
            
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            await self.producer.start()
            logger.info(f"Connected to Kafka: {self.bootstrap_servers}")
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            raise
            
    async def publish_indexing_event(self, event: StorageEvent, priority: int = 0):
        """Publish indexing event to Kafka topic."""
        if not self.producer:
            await self.connect()
            
        command = IndexingCommand(event=event, priority=priority)
        
        try:
            # Use object key as partition key for ordering
            key = f"{event.object.bucket}/{event.object.key}".encode('utf-8')
            
            await self.producer.send(
                self.index_topic,
                value=command.model_dump(),
                key=key
            )
            
            logger.debug(f"Published indexing event: {event.object.bucket}/{event.object.key}")
            
        except Exception as e:
            logger.error(f"Failed to publish indexing event: {e}")
            raise
            
    async def publish_deletion_event(self, bucket: str, key: str, 
                                     version_id: Optional[str] = None):
        """Publish deletion event to Kafka topic."""
        if not self.producer:
            await self.connect()
            
        command = DeletionCommand(
            bucket=bucket,
            key=key,
            version_id=version_id
        )
        
        try:
            # Use object key as partition key
            partition_key = f"{bucket}/{key}".encode('utf-8')
            
            await self.producer.send(
                self.delete_topic,
                value=command.model_dump(),
                key=partition_key
            )
            
            logger.debug(f"Published deletion event: {bucket}/{key}")
            
        except Exception as e:
            logger.error(f"Failed to publish deletion event: {e}")
            raise
            
    async def close(self):
        """Close Kafka producer."""
        if self.producer:
            await self.producer.stop()
            logger.info("Kafka producer closed")


class SQSEventPublisher(EventPublisher):
    """AWS SQS event publisher."""
    
    def __init__(self, index_queue_url: str, delete_queue_url: str, region: str = "us-east-1"):
        """
        Initialize SQS publisher.
        
        Args:
            index_queue_url: SQS queue URL for indexing events
            delete_queue_url: SQS queue URL for deletion events
            region: AWS region
        """
        self.index_queue_url = index_queue_url
        self.delete_queue_url = delete_queue_url
        self.region = region
        self.client = None
        
    async def connect(self):
        """Connect to AWS SQS."""
        try:
            import boto3
            self.client = boto3.client('sqs', region_name=self.region)
            logger.info(f"Connected to SQS in region: {self.region}")
        except Exception as e:
            logger.error(f"Failed to connect to SQS: {e}")
            raise
            
    async def publish_indexing_event(self, event: StorageEvent, priority: int = 0):
        """Publish indexing event to SQS queue."""
        if not self.client:
            await self.connect()
            
        command = IndexingCommand(event=event, priority=priority)
        
        try:
            self.client.send_message(
                QueueUrl=self.index_queue_url,
                MessageBody=command.model_dump_json(),
                MessageAttributes={
                    'Priority': {
                        'StringValue': str(priority),
                        'DataType': 'Number'
                    }
                }
            )
            
            logger.debug(f"Published indexing event to SQS: {event.object.bucket}/{event.object.key}")
            
        except Exception as e:
            logger.error(f"Failed to publish to SQS: {e}")
            raise
            
    async def publish_deletion_event(self, bucket: str, key: str, 
                                     version_id: Optional[str] = None):
        """Publish deletion event to SQS queue."""
        if not self.client:
            await self.connect()
            
        command = DeletionCommand(bucket=bucket, key=key, version_id=version_id)
        
        try:
            self.client.send_message(
                QueueUrl=self.delete_queue_url,
                MessageBody=command.model_dump_json()
            )
            
            logger.debug(f"Published deletion event to SQS: {bucket}/{key}")
            
        except Exception as e:
            logger.error(f"Failed to publish deletion to SQS: {e}")
            raise


class PubSubEventPublisher(EventPublisher):
    """Google Pub/Sub event publisher."""
    
    def __init__(self, project_id: str, index_topic: str, delete_topic: str):
        """
        Initialize Pub/Sub publisher.
        
        Args:
            project_id: Google Cloud project ID
            index_topic: Topic for indexing events
            delete_topic: Topic for deletion events
        """
        self.project_id = project_id
        self.index_topic = index_topic
        self.delete_topic = delete_topic
        self.publisher = None
        
    async def connect(self):
        """Connect to Google Pub/Sub."""
        try:
            from google.cloud import pubsub_v1
            self.publisher = pubsub_v1.PublisherClient()
            logger.info(f"Connected to Pub/Sub project: {self.project_id}")
        except Exception as e:
            logger.error(f"Failed to connect to Pub/Sub: {e}")
            raise
            
    async def publish_indexing_event(self, event: StorageEvent, priority: int = 0):
        """Publish indexing event to Pub/Sub topic."""
        if not self.publisher:
            await self.connect()
            
        command = IndexingCommand(event=event, priority=priority)
        topic_path = self.publisher.topic_path(self.project_id, self.index_topic)
        
        try:
            data = command.model_dump_json().encode('utf-8')
            future = self.publisher.publish(topic_path, data)
            future.result()  # Wait for publish to complete
            
            logger.debug(f"Published indexing event to Pub/Sub: {event.object.bucket}/{event.object.key}")
            
        except Exception as e:
            logger.error(f"Failed to publish to Pub/Sub: {e}")
            raise
            
    async def publish_deletion_event(self, bucket: str, key: str, 
                                     version_id: Optional[str] = None):
        """Publish deletion event to Pub/Sub topic."""
        if not self.publisher:
            await self.connect()
            
        command = DeletionCommand(bucket=bucket, key=key, version_id=version_id)
        topic_path = self.publisher.topic_path(self.project_id, self.delete_topic)
        
        try:
            data = command.model_dump_json().encode('utf-8')
            future = self.publisher.publish(topic_path, data)
            future.result()
            
            logger.debug(f"Published deletion event to Pub/Sub: {bucket}/{key}")
            
        except Exception as e:
            logger.error(f"Failed to publish deletion to Pub/Sub: {e}")
            raise
