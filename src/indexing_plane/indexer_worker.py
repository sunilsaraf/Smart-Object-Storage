"""
Indexer worker for processing object storage events.
Handles extraction, chunking, embedding, and indexing into Milvus.
"""
import asyncio
import logging
import json
import uuid
from typing import Optional, Dict, Any
import yaml

from milvus_client import MilvusClient
from metadata_store import MetadataStore
from embedder import create_embedder, Embedder
from text_extractor import TextExtractor
from chunker import create_chunker, Chunker

logger = logging.getLogger(__name__)


class IndexerWorker:
    """Worker for indexing objects into vector database."""
    
    def __init__(self, config_path: str = "config/worker_config.yaml"):
        """
        Initialize indexer worker.
        
        Args:
            config_path: Path to worker configuration file
        """
        self.config = self._load_config(config_path)
        
        # Initialize components
        self.milvus_client = None
        self.metadata_store = None
        self.embedder = None
        self.chunker = None
        self.text_extractor = None
        self.storage_client = None
        self.running = False
        
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
            
    async def initialize(self):
        """Initialize all components."""
        logger.info("Initializing indexer worker...")
        
        # Initialize Milvus
        milvus_config = self._load_config("config/milvus_config.yaml")
        self.milvus_client = MilvusClient(
            host=milvus_config["milvus"]["host"],
            port=milvus_config["milvus"]["port"],
            user=milvus_config["milvus"]["user"],
            password=milvus_config["milvus"]["password"]
        )
        self.milvus_client.connect()
        
        # Create/load collection
        collection_config = milvus_config["milvus"]["collection"]
        schema_config = collection_config["schema"]
        self.milvus_client.create_collection(
            collection_name=collection_config["name"],
            dimension=schema_config["dimension"],
            metric_type=schema_config["metric_type"],
            index_type=schema_config["index_type"],
            index_params=milvus_config["milvus"]["index_params"]
        )
        self.milvus_client.load_collection(collection_config["name"])
        
        # Initialize metadata store
        db_config = self.config["database"]["postgresql"]
        connection_string = (
            f"postgresql://{db_config['user']}:{db_config['password']}"
            f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        )
        self.metadata_store = MetadataStore(connection_string)
        
        # Initialize embedder
        embedding_config = self._load_config("config/embedding_config.yaml")
        self.embedder = create_embedder(embedding_config["embedding"])
        
        # Initialize chunker
        self.chunker = create_chunker(self.config["chunking"])
        
        # Initialize text extractor
        text_config = self.config["text_extraction"]
        self.text_extractor = TextExtractor(
            enable_ocr=text_config["ocr"]["enabled"],
            ocr_language=text_config["ocr"]["language"]
        )
        
        # Initialize storage client
        self._init_storage_client()
        
        logger.info("Indexer worker initialized")
        
    def _init_storage_client(self):
        """Initialize object storage client."""
        storage_config = self.config["object_storage"]
        storage_type = storage_config["type"]
        
        if storage_type == "minio":
            from minio import Minio
            minio_config = storage_config["minio"]
            self.storage_client = Minio(
                minio_config["endpoint"],
                access_key=minio_config["access_key"],
                secret_key=minio_config["secret_key"],
                secure=minio_config["secure"]
            )
        elif storage_type == "s3":
            import boto3
            s3_config = storage_config["s3"]
            self.storage_client = boto3.client(
                's3',
                region_name=s3_config["region"],
                aws_access_key_id=s3_config["access_key"],
                aws_secret_access_key=s3_config["secret_key"]
            )
        else:
            raise ValueError(f"Unsupported storage type: {storage_type}")
            
    async def process_event(self, event_data: dict) -> bool:
        """
        Process an indexing event.
        
        Args:
            event_data: Event data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            event = event_data.get("event", {})
            obj = event.get("object", {})
            metadata = event.get("metadata", {})
            
            bucket = obj.get("bucket")
            key = obj.get("key")
            version_id = obj.get("version_id")
            
            logger.info(f"Processing object: {bucket}/{key}")
            
            # Fetch object content
            content = await self._fetch_object(bucket, key, version_id)
            if not content:
                logger.error(f"Failed to fetch object: {bucket}/{key}")
                return False
                
            # Extract text
            content_type = metadata.get("content_type", "application/octet-stream")
            text = self.text_extractor.extract(content, content_type, key)
            
            if not text:
                logger.warning(f"No text extracted from: {bucket}/{key}")
                return True  # Not an error, just nothing to index
                
            logger.info(f"Extracted {len(text)} characters from {bucket}/{key}")
            
            # Chunk text
            chunks = self.chunker.chunk(text)
            logger.info(f"Created {len(chunks)} chunks from {bucket}/{key}")
            
            if not chunks:
                return True
                
            # Generate embeddings
            chunk_texts = [chunk.text for chunk in chunks]
            embeddings = self.embedder.embed(chunk_texts)
            
            # Ensure embeddings is a list of lists
            if embeddings and isinstance(embeddings[0], (int, float)):
                embeddings = [embeddings]
                
            # Store object metadata
            object_id = self.metadata_store.upsert_object(
                bucket=bucket,
                key=key,
                version_id=version_id,
                content_type=content_type,
                size=obj.get("size"),
                etag=obj.get("etag"),
                tags=metadata.get("tags", {}),
                acl=metadata.get("acl", {})
            )
            
            # Prepare Milvus data
            milvus_data = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                milvus_id = str(uuid.uuid4())
                
                data = {
                    "id": milvus_id,
                    "vector": embedding,
                    "bucket": bucket,
                    "key": key,
                    "version_id": version_id or "",
                    "chunk_index": chunk.chunk_index,
                    "start_offset": chunk.start_offset,
                    "end_offset": chunk.end_offset,
                    "text": chunk.text[:1000],  # Truncate for storage
                    "content_type": content_type,
                    "tags": json.dumps(metadata.get("tags", {}))
                }
                milvus_data.append(data)
                
                # Store chunk metadata
                self.metadata_store.insert_chunk(
                    object_id=object_id,
                    milvus_id=milvus_id,
                    chunk_index=chunk.chunk_index,
                    start_offset=chunk.start_offset,
                    end_offset=chunk.end_offset,
                    text=chunk.text,
                    embedding_model=self.embedder.__class__.__name__
                )
                
            # Insert into Milvus
            self.milvus_client.insert_vectors(milvus_data)
            
            logger.info(f"Successfully indexed {bucket}/{key} with {len(chunks)} chunks")
            return True
            
        except Exception as e:
            logger.error(f"Failed to process event: {e}", exc_info=True)
            return False
            
    async def _fetch_object(self, bucket: str, key: str, 
                           version_id: Optional[str] = None) -> Optional[bytes]:
        """Fetch object content from storage."""
        try:
            if hasattr(self.storage_client, 'get_object'):
                # MinIO client
                response = self.storage_client.get_object(bucket, key, version_id=version_id)
                content = response.read()
                response.close()
                response.release_conn()
                return content
            else:
                # Boto3 S3 client
                params = {'Bucket': bucket, 'Key': key}
                if version_id:
                    params['VersionId'] = version_id
                response = self.storage_client.get_object(**params)
                return response['Body'].read()
                
        except Exception as e:
            logger.error(f"Failed to fetch object {bucket}/{key}: {e}")
            return None
            
    async def start(self):
        """Start the indexer worker."""
        self.running = True
        logger.info("Indexer worker started")
        
        # In a real implementation, this would consume from message queue
        # For now, it's a placeholder
        
    async def stop(self):
        """Stop the indexer worker."""
        self.running = False
        
        # Clean up
        if self.milvus_client:
            self.milvus_client.disconnect()
            
        logger.info("Indexer worker stopped")


async def main():
    """Main entry point for indexer worker."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    worker = IndexerWorker()
    await worker.initialize()
    
    try:
        await worker.start()
        # Keep running
        while worker.running:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main())
