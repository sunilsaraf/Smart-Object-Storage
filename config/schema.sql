-- Create extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Objects table - stores metadata about objects in storage
CREATE TABLE objects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bucket VARCHAR(255) NOT NULL,
    key VARCHAR(1024) NOT NULL,
    version_id VARCHAR(255),
    content_type VARCHAR(255),
    size BIGINT,
    etag VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_accessed_at TIMESTAMP WITH TIME ZONE,
    tags JSONB DEFAULT '{}',
    acl JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(bucket, key, version_id)
);

CREATE INDEX idx_objects_bucket_key ON objects(bucket, key);
CREATE INDEX idx_objects_version ON objects(version_id);
CREATE INDEX idx_objects_created_at ON objects(created_at);
CREATE INDEX idx_objects_tags ON objects USING GIN(tags);
CREATE INDEX idx_objects_is_deleted ON objects(is_deleted);

-- Chunks table - stores chunk metadata and links to Milvus vectors
CREATE TABLE chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    object_id UUID NOT NULL REFERENCES objects(id) ON DELETE CASCADE,
    milvus_id VARCHAR(255) NOT NULL,
    chunk_index INTEGER NOT NULL,
    start_offset BIGINT NOT NULL,
    end_offset BIGINT NOT NULL,
    text TEXT,
    embedding_model VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(object_id, chunk_index)
);

CREATE INDEX idx_chunks_object_id ON chunks(object_id);
CREATE INDEX idx_chunks_milvus_id ON chunks(milvus_id);
CREATE INDEX idx_chunks_embedding_model ON chunks(embedding_model);

-- IAM policies table - stores access control policies
CREATE TABLE iam_policies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    principal VARCHAR(255) NOT NULL,
    resource_pattern VARCHAR(1024) NOT NULL,
    actions TEXT[] NOT NULL,
    effect VARCHAR(10) NOT NULL CHECK (effect IN ('ALLOW', 'DENY')),
    conditions JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    description TEXT
);

CREATE INDEX idx_iam_policies_principal ON iam_policies(principal);
CREATE INDEX idx_iam_policies_resource ON iam_policies(resource_pattern);
CREATE INDEX idx_iam_policies_effect ON iam_policies(effect);

-- Indexing jobs table - tracks indexing job status
CREATE TABLE indexing_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    object_id UUID NOT NULL REFERENCES objects(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    worker_id VARCHAR(255),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_indexing_jobs_status ON indexing_jobs(status);
CREATE INDEX idx_indexing_jobs_object_id ON indexing_jobs(object_id);
CREATE INDEX idx_indexing_jobs_created_at ON indexing_jobs(created_at);

-- Query logs table - stores query history for analytics
CREATE TABLE query_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query_text TEXT NOT NULL,
    user_id VARCHAR(255),
    top_k INTEGER,
    filters JSONB,
    results_count INTEGER,
    latency_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_query_logs_user_id ON query_logs(user_id);
CREATE INDEX idx_query_logs_created_at ON query_logs(created_at);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers to automatically update updated_at
CREATE TRIGGER update_objects_updated_at BEFORE UPDATE ON objects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_iam_policies_updated_at BEFORE UPDATE ON iam_policies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_indexing_jobs_updated_at BEFORE UPDATE ON indexing_jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert some default IAM policies for testing
INSERT INTO iam_policies (principal, resource_pattern, actions, effect, description)
VALUES 
    ('*', '*', ARRAY['s3:GetObject'], 'ALLOW', 'Default allow all read access'),
    ('admin', '*', ARRAY['s3:*'], 'ALLOW', 'Admin full access');
