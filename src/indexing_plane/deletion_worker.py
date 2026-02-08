"""
Deletion worker for removing vectors from Milvus.
Handles object deletion and version cleanup.
"""
import asyncio
import logging
from typing import Optional
import yaml

from milvus_client import MilvusClient
from metadata_store import MetadataStore

logger = logging.getLogger(__name__)


class DeletionWorker:
    """Worker for deleting vectors from Milvus."""
    
    def __init__(self, config_path: str = "config/worker_config.yaml"):
        """
        Initialize deletion worker.
        
        Args:
            config_path: Path to worker configuration file
        """
        self.config = self._load_config(config_path)
        
        # Initialize components
        self.milvus_client = None
        self.metadata_store = None
        self.running = False
        
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
            
    async def initialize(self):
        """Initialize all components."""
        logger.info("Initializing deletion worker...")
        
        # Initialize Milvus
        milvus_config = self._load_config("config/milvus_config.yaml")
        self.milvus_client = MilvusClient(
            host=milvus_config["milvus"]["host"],
            port=milvus_config["milvus"]["port"],
            user=milvus_config["milvus"]["user"],
            password=milvus_config["milvus"]["password"]
        )
        self.milvus_client.connect()
        
        # Load collection
        collection_config = milvus_config["milvus"]["collection"]
        self.milvus_client.load_collection(collection_config["name"])
        
        # Initialize metadata store
        db_config = self.config["database"]["postgresql"]
        connection_string = (
            f"postgresql://{db_config['user']}:{db_config['password']}"
            f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        )
        self.metadata_store = MetadataStore(connection_string)
        
        logger.info("Deletion worker initialized")
        
    async def process_deletion(self, deletion_data: dict) -> bool:
        """
        Process a deletion event.
        
        Args:
            deletion_data: Deletion event data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            bucket = deletion_data.get("bucket")
            key = deletion_data.get("key")
            version_id = deletion_data.get("version_id")
            delete_all_versions = deletion_data.get("delete_all_versions", False)
            
            logger.info(f"Processing deletion: {bucket}/{key}")
            
            # Get object metadata
            obj_metadata = self.metadata_store.get_object(bucket, key, version_id)
            
            if not obj_metadata:
                logger.warning(f"Object not found in metadata: {bucket}/{key}")
                return True  # Not an error if already deleted
                
            object_id = obj_metadata["id"]
            
            # Delete vectors from Milvus
            if delete_all_versions:
                # Delete all versions of this object
                expr = f'bucket == "{bucket}" && key == "{key}"'
            else:
                # Delete specific version
                if version_id:
                    expr = f'bucket == "{bucket}" && key == "{key}" && version_id == "{version_id}"'
                else:
                    expr = f'bucket == "{bucket}" && key == "{key}" && version_id == ""'
                    
            self.milvus_client.delete_vectors(expr)
            logger.info(f"Deleted vectors from Milvus: {expr}")
            
            # Delete chunks from metadata store
            self.metadata_store.delete_chunks_by_object(object_id)
            
            # Mark object as deleted in metadata store
            self.metadata_store.delete_object(bucket, key, version_id)
            
            logger.info(f"Successfully processed deletion: {bucket}/{key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to process deletion: {e}", exc_info=True)
            return False
            
    async def cleanup_stale_vectors(self, max_age_days: int = 90):
        """
        Clean up stale vectors from deleted objects.
        
        Args:
            max_age_days: Maximum age of deleted objects to keep
        """
        try:
            # This would query the metadata store for objects marked as deleted
            # and delete their vectors from Milvus if they're older than max_age_days
            logger.info(f"Cleaning up vectors older than {max_age_days} days")
            
            # Implementation would go here
            
            logger.info("Cleanup completed")
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}", exc_info=True)
            
    async def start(self):
        """Start the deletion worker."""
        self.running = True
        logger.info("Deletion worker started")
        
        # In a real implementation, this would consume from message queue
        # For now, it's a placeholder
        
    async def stop(self):
        """Stop the deletion worker."""
        self.running = False
        
        # Clean up
        if self.milvus_client:
            self.milvus_client.disconnect()
            
        logger.info("Deletion worker stopped")


async def main():
    """Main entry point for deletion worker."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    worker = DeletionWorker()
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
