"""
Metadata store for object and chunk metadata.
Uses PostgreSQL for relational data storage.
"""
import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Integer, BigInteger, Boolean, DateTime, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import uuid

logger = logging.getLogger(__name__)

Base = declarative_base()


class Object(Base):
    """Object metadata table."""
    __tablename__ = "objects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bucket = Column(String(255), nullable=False)
    key = Column(String(1024), nullable=False)
    version_id = Column(String(255))
    content_type = Column(String(255))
    size = Column(BigInteger)
    etag = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_accessed_at = Column(DateTime)
    tags = Column(JSON, default=dict)
    acl = Column(JSON, default=dict)
    metadata = Column(JSON, default=dict)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)


class Chunk(Base):
    """Chunk metadata table."""
    __tablename__ = "chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    object_id = Column(UUID(as_uuid=True), nullable=False)
    milvus_id = Column(String(255), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    start_offset = Column(BigInteger, nullable=False)
    end_offset = Column(BigInteger, nullable=False)
    text = Column(Text)
    embedding_model = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class IAMPolicy(Base):
    """IAM policy table."""
    __tablename__ = "iam_policies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    principal = Column(String(255), nullable=False)
    resource_pattern = Column(String(1024), nullable=False)
    actions = Column(JSON, nullable=False)  # Array of actions
    effect = Column(String(10), nullable=False)  # ALLOW or DENY
    conditions = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255))
    description = Column(Text)


class IndexingJob(Base):
    """Indexing job tracking table."""
    __tablename__ = "indexing_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    object_id = Column(UUID(as_uuid=True), nullable=False)
    status = Column(String(50), nullable=False)  # pending, processing, completed, failed
    worker_id = Column(String(255))
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MetadataStore:
    """PostgreSQL metadata store."""
    
    def __init__(self, connection_string: str):
        """
        Initialize metadata store.
        
        Args:
            connection_string: PostgreSQL connection string
        """
        self.engine = create_engine(connection_string, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
    def create_tables(self):
        """Create all tables."""
        Base.metadata.create_all(self.engine)
        logger.info("Created metadata store tables")
        
    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()
        
    def upsert_object(self, bucket: str, key: str, version_id: Optional[str],
                     content_type: Optional[str] = None,
                     size: Optional[int] = None,
                     etag: Optional[str] = None,
                     tags: Optional[Dict] = None,
                     acl: Optional[Dict] = None) -> str:
        """
        Insert or update object metadata.
        
        Returns:
            Object ID (UUID as string)
        """
        session = self.get_session()
        try:
            # Check if object exists
            obj = session.query(Object).filter(
                Object.bucket == bucket,
                Object.key == key,
                Object.version_id == version_id
            ).first()
            
            if obj:
                # Update existing
                obj.content_type = content_type or obj.content_type
                obj.size = size or obj.size
                obj.etag = etag or obj.etag
                obj.tags = tags or obj.tags
                obj.acl = acl or obj.acl
                obj.updated_at = datetime.utcnow()
                obj.is_deleted = False
            else:
                # Create new
                obj = Object(
                    bucket=bucket,
                    key=key,
                    version_id=version_id,
                    content_type=content_type,
                    size=size,
                    etag=etag,
                    tags=tags or {},
                    acl=acl or {}
                )
                session.add(obj)
                
            session.commit()
            object_id = str(obj.id)
            logger.debug(f"Upserted object: {bucket}/{key} (id: {object_id})")
            return object_id
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to upsert object: {e}")
            raise
        finally:
            session.close()
            
    def insert_chunk(self, object_id: str, milvus_id: str, chunk_index: int,
                    start_offset: int, end_offset: int, text: str,
                    embedding_model: str):
        """Insert chunk metadata."""
        session = self.get_session()
        try:
            chunk = Chunk(
                object_id=uuid.UUID(object_id),
                milvus_id=milvus_id,
                chunk_index=chunk_index,
                start_offset=start_offset,
                end_offset=end_offset,
                text=text,
                embedding_model=embedding_model
            )
            session.add(chunk)
            session.commit()
            logger.debug(f"Inserted chunk {chunk_index} for object {object_id}")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to insert chunk: {e}")
            raise
        finally:
            session.close()
            
    def get_object(self, bucket: str, key: str, 
                  version_id: Optional[str] = None) -> Optional[Dict]:
        """Get object metadata."""
        session = self.get_session()
        try:
            query = session.query(Object).filter(
                Object.bucket == bucket,
                Object.key == key
            )
            
            if version_id:
                query = query.filter(Object.version_id == version_id)
            else:
                # Get latest version
                query = query.order_by(Object.created_at.desc())
                
            obj = query.first()
            
            if obj:
                return {
                    "id": str(obj.id),
                    "bucket": obj.bucket,
                    "key": obj.key,
                    "version_id": obj.version_id,
                    "content_type": obj.content_type,
                    "size": obj.size,
                    "etag": obj.etag,
                    "tags": obj.tags,
                    "acl": obj.acl,
                    "created_at": obj.created_at.isoformat() if obj.created_at else None,
                    "is_deleted": obj.is_deleted
                }
            return None
        finally:
            session.close()
            
    def get_chunks_by_object(self, object_id: str) -> List[Dict]:
        """Get all chunks for an object."""
        session = self.get_session()
        try:
            chunks = session.query(Chunk).filter(
                Chunk.object_id == uuid.UUID(object_id)
            ).order_by(Chunk.chunk_index).all()
            
            return [
                {
                    "id": str(chunk.id),
                    "milvus_id": chunk.milvus_id,
                    "chunk_index": chunk.chunk_index,
                    "start_offset": chunk.start_offset,
                    "end_offset": chunk.end_offset,
                    "text": chunk.text,
                    "embedding_model": chunk.embedding_model
                }
                for chunk in chunks
            ]
        finally:
            session.close()
            
    def delete_object(self, bucket: str, key: str, version_id: Optional[str] = None):
        """Mark object as deleted."""
        session = self.get_session()
        try:
            query = session.query(Object).filter(
                Object.bucket == bucket,
                Object.key == key
            )
            
            if version_id:
                query = query.filter(Object.version_id == version_id)
                
            query.update({
                "is_deleted": True,
                "deleted_at": datetime.utcnow()
            })
            
            session.commit()
            logger.info(f"Marked object as deleted: {bucket}/{key}")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to delete object: {e}")
            raise
        finally:
            session.close()
            
    def delete_chunks_by_object(self, object_id: str):
        """Delete all chunks for an object."""
        session = self.get_session()
        try:
            session.query(Chunk).filter(
                Chunk.object_id == uuid.UUID(object_id)
            ).delete()
            session.commit()
            logger.info(f"Deleted chunks for object: {object_id}")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to delete chunks: {e}")
            raise
        finally:
            session.close()
            
    def get_iam_policies(self, principal: str) -> List[Dict]:
        """Get IAM policies for a principal."""
        session = self.get_session()
        try:
            policies = session.query(IAMPolicy).filter(
                (IAMPolicy.principal == principal) | (IAMPolicy.principal == "*")
            ).all()
            
            return [
                {
                    "id": str(p.id),
                    "principal": p.principal,
                    "resource_pattern": p.resource_pattern,
                    "actions": p.actions,
                    "effect": p.effect,
                    "conditions": p.conditions
                }
                for p in policies
            ]
        finally:
            session.close()
