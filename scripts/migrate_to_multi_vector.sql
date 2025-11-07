-- ==========================================
-- 多向量表結構遷移腳本
-- 日期：2025-11-06
-- 用途：為 document_embeddings 添加標題和內容向量欄位
-- ==========================================

BEGIN;

-- Step 1: 檢查當前表結構
\echo '===== Step 1: 檢查當前表結構 ====='
\d document_embeddings

-- Step 2: 添加新欄位（允許 NULL）
\echo '===== Step 2: 添加標題和內容向量欄位 ====='
ALTER TABLE document_embeddings 
    ADD COLUMN IF NOT EXISTS title_embedding vector(1024),
    ADD COLUMN IF NOT EXISTS content_embedding vector(1024);

-- Step 3: 確認欄位已添加
\echo '===== Step 3: 確認新欄位 ====='
\d document_embeddings

-- Step 4: 創建標題向量索引
\echo '===== Step 4: 創建標題向量索引 ====='
CREATE INDEX IF NOT EXISTS idx_document_embeddings_title_vector 
    ON document_embeddings 
    USING ivfflat (title_embedding vector_cosine_ops) 
    WITH (lists = 100);

-- Step 5: 創建內容向量索引
\echo '===== Step 5: 創建內容向量索引 ====='
CREATE INDEX IF NOT EXISTS idx_document_embeddings_content_vector 
    ON document_embeddings 
    USING ivfflat (content_embedding vector_cosine_ops) 
    WITH (lists = 100);

-- Step 6: 確認索引已創建
\echo '===== Step 6: 確認所有索引 ====='
SELECT 
    indexname, 
    indexdef 
FROM pg_indexes 
WHERE tablename = 'document_embeddings'
ORDER BY indexname;

-- Step 7: 查看表統計
\echo '===== Step 7: 表統計資訊 ====='
SELECT 
    count(*) as total_records,
    count(embedding) as old_vectors,
    count(title_embedding) as title_vectors,
    count(content_embedding) as content_vectors
FROM document_embeddings;

\echo '===== 遷移完成！ ====='

COMMIT;

-- ==========================================
-- 回滾指令（如果需要，請手動執行）
-- ==========================================
-- BEGIN;
-- DROP INDEX IF EXISTS idx_document_embeddings_content_vector;
-- DROP INDEX IF EXISTS idx_document_embeddings_title_vector;
-- ALTER TABLE document_embeddings DROP COLUMN IF EXISTS content_embedding;
-- ALTER TABLE document_embeddings DROP COLUMN IF EXISTS title_embedding;
-- COMMIT;
