-- PostgreSQL + pgvector 初始化腳本
-- 此腳本在容器首次啟動時自動執行
-- 
-- 維護說明：
-- - 此文件由主專案 ai-platform-web 統一管理
-- - 修改後需要重新同步到 10.10.173.29
-- - 如果資料庫已存在，此腳本不會重複執行
-- 
-- ⚠️ 重要：遷移資料庫時的注意事項
-- - 使用 pg_restore 還原備份時，此腳本會先執行
-- - 如果此腳本創建的表結構與備份不同，會導致 pg_restore 跳過表創建
-- - 因此此腳本的表結構必須與實際專案中的表結構完全一致
-- - 建議遷移時：先還原備份，再執行此腳本（僅創建擴展和觸發器）
--
-- 更新日期：2025-12-11
-- 修正：document_embeddings 表結構與實際專案一致（1024維 + 多向量欄位）

-- 初始化 pgvector 擴展
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================
-- 創建文檔向量嵌入表（多向量架構：embedding + title + content）
-- 用於 Protocol Assistant 和 RVT Assistant
-- ============================================================
CREATE TABLE IF NOT EXISTS document_embeddings (
    id SERIAL PRIMARY KEY,
    source_table VARCHAR(100) NOT NULL,
    source_id INTEGER NOT NULL,
    text_content TEXT,                          -- 原始文本內容
    content_hash VARCHAR(64),                   -- 內容雜湊（可為空）
    embedding vector(1024),                     -- 主向量（1024維 multilingual-e5-large）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    title_embedding vector(1024),               -- 標題向量（1024維）
    content_embedding vector(1024),             -- 內容向量（1024維）
    UNIQUE(source_table, source_id)
);

-- ============================================================
-- 創建 1024 維向量表（獨立表，用於特定應用）
-- 用於 Know Issue 等
-- ============================================================
CREATE TABLE IF NOT EXISTS document_embeddings_1024 (
    id SERIAL PRIMARY KEY,
    source_table VARCHAR(100) NOT NULL,
    source_id INTEGER NOT NULL,
    text_content TEXT,
    content_hash VARCHAR(64),
    embedding vector(1024),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,                             -- 額外的元數據
    UNIQUE(source_table, source_id)
);

-- ============================================================
-- 創建向量相似度搜索索引
-- ============================================================

-- document_embeddings 主向量索引（1024維）
CREATE INDEX IF NOT EXISTS document_embeddings_vector_idx 
ON document_embeddings USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- document_embeddings 標題向量索引
CREATE INDEX IF NOT EXISTS document_embeddings_title_vector_idx 
ON document_embeddings USING ivfflat (title_embedding vector_cosine_ops)
WITH (lists = 100);

-- document_embeddings 內容向量索引
CREATE INDEX IF NOT EXISTS document_embeddings_content_vector_idx 
ON document_embeddings USING ivfflat (content_embedding vector_cosine_ops)
WITH (lists = 100);

-- document_embeddings_1024 向量索引
CREATE INDEX IF NOT EXISTS document_embeddings_1024_vector_idx 
ON document_embeddings_1024 USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- ============================================================
-- 創建複合索引用於查詢優化
-- ============================================================
CREATE INDEX IF NOT EXISTS document_embeddings_source_idx 
ON document_embeddings(source_table, source_id);

CREATE INDEX IF NOT EXISTS document_embeddings_1024_source_idx 
ON document_embeddings_1024(source_table, source_id);

-- 添加更新時間觸發器
CREATE OR REPLACE FUNCTION update_embedding_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 384維表的觸發器
DROP TRIGGER IF EXISTS update_document_embeddings_updated_at ON document_embeddings;
CREATE TRIGGER update_document_embeddings_updated_at
    BEFORE UPDATE ON document_embeddings
    FOR EACH ROW
    EXECUTE FUNCTION update_embedding_updated_at();

-- 1024維表的觸發器
DROP TRIGGER IF EXISTS update_document_embeddings_1024_updated_at ON document_embeddings_1024;
CREATE TRIGGER update_document_embeddings_1024_updated_at
    BEFORE UPDATE ON document_embeddings_1024
    FOR EACH ROW
    EXECUTE FUNCTION update_embedding_updated_at();

-- 輸出初始化完成訊息
DO $$
BEGIN
    RAISE NOTICE '✅ pgvector 初始化完成';
    RAISE NOTICE '✅ document_embeddings 表已建立（1024維 + 多向量：title + content）';
    RAISE NOTICE '✅ document_embeddings_1024 表已建立（1024維 + metadata）';
    RAISE NOTICE '';
    RAISE NOTICE '⚠️  注意：此腳本僅創建空表結構';
    RAISE NOTICE '⚠️  如果是遷移場景，請使用 pg_restore 還原資料';
END $$;
