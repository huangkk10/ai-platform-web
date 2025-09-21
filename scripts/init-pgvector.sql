-- 初始化 pgvector 擴展
CREATE EXTENSION IF NOT EXISTS vector;

-- 創建文檔向量嵌入表
CREATE TABLE IF NOT EXISTS document_embeddings (
    id SERIAL PRIMARY KEY,
    source_table VARCHAR(100) NOT NULL,
    source_id INTEGER NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    embedding vector(384),  -- 384維向量，適用於 MiniLM 模型
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(source_table, source_id)
);

-- 創建向量相似度搜索索引
CREATE INDEX IF NOT EXISTS document_embeddings_vector_idx 
ON document_embeddings USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- 創建複合索引用於查詢優化
CREATE INDEX IF NOT EXISTS document_embeddings_source_idx 
ON document_embeddings(source_table, source_id);

-- 添加更新時間觸發器
CREATE OR REPLACE FUNCTION update_embedding_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_document_embeddings_updated_at ON document_embeddings;
CREATE TRIGGER update_document_embeddings_updated_at
    BEFORE UPDATE ON document_embeddings
    FOR EACH ROW
    EXECUTE FUNCTION update_embedding_updated_at();