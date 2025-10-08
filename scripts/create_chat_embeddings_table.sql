-- 創建專門的聊天消息向量表
-- 執行命令: docker exec postgres_db psql -U postgres -d ai_platform -f /scripts/create_chat_embeddings_table.sql

-- 創建 chat_message_embeddings_1024 表
CREATE TABLE IF NOT EXISTS chat_message_embeddings_1024 (
    id SERIAL PRIMARY KEY,
    
    -- 聊天消息關聯
    chat_message_id INTEGER NOT NULL,
    conversation_id INTEGER,
    
    -- 向量數據
    text_content TEXT NOT NULL,
    embedding vector(1024),
    content_hash VARCHAR(64) UNIQUE,
    
    -- 聊天專屬 metadata
    user_role VARCHAR(20) DEFAULT 'user',  -- user/assistant
    message_length INTEGER,
    question_keywords TEXT[],  -- 提取的關鍵字
    language_detected VARCHAR(10) DEFAULT 'zh',  -- zh/en
    
    -- 分類相關
    predicted_category VARCHAR(50),
    confidence_score FLOAT DEFAULT 0.0,
    cluster_id INTEGER,  -- 聚類 ID
    similarity_threshold FLOAT DEFAULT 0.7,
    
    -- 時間戳記
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 外鍵約束（如果需要強制約束的話，可以取消註解）
    -- FOREIGN KEY (chat_message_id) REFERENCES chat_messages(id) ON DELETE CASCADE,
    -- FOREIGN KEY (conversation_id) REFERENCES conversation_sessions(id) ON DELETE CASCADE
    
    -- 唯一約束
    UNIQUE(chat_message_id)
);

-- 創建專門的索引優化
-- 主要向量搜索索引
CREATE INDEX IF NOT EXISTS chat_embeddings_vector_idx 
ON chat_message_embeddings_1024 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- 聊天專屬查詢索引
CREATE INDEX IF NOT EXISTS chat_embeddings_conversation_idx 
ON chat_message_embeddings_1024(conversation_id);

CREATE INDEX IF NOT EXISTS chat_embeddings_category_idx 
ON chat_message_embeddings_1024(predicted_category);

CREATE INDEX IF NOT EXISTS chat_embeddings_cluster_idx 
ON chat_message_embeddings_1024(cluster_id);

CREATE INDEX IF NOT EXISTS chat_embeddings_hash_idx 
ON chat_message_embeddings_1024(content_hash);

CREATE INDEX IF NOT EXISTS chat_embeddings_message_id_idx 
ON chat_message_embeddings_1024(chat_message_id);

-- 複合索引 for 聚類分析
CREATE INDEX IF NOT EXISTS chat_embeddings_cluster_confidence_idx 
ON chat_message_embeddings_1024(cluster_id, confidence_score);

-- 複合索引 for 時間查詢
CREATE INDEX IF NOT EXISTS chat_embeddings_created_category_idx 
ON chat_message_embeddings_1024(created_at DESC, predicted_category);

-- 添加更新時間觸發器
CREATE OR REPLACE FUNCTION update_chat_embeddings_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER IF NOT EXISTS chat_embeddings_updated_at_trigger
    BEFORE UPDATE ON chat_message_embeddings_1024
    FOR EACH ROW
    EXECUTE FUNCTION update_chat_embeddings_updated_at();

-- 創建視圖便於查詢分析
CREATE OR REPLACE VIEW chat_embedding_analysis AS
SELECT 
    ce.id,
    ce.chat_message_id,
    ce.conversation_id,
    ce.predicted_category,
    ce.cluster_id,
    ce.confidence_score,
    ce.message_length,
    ce.language_detected,
    LEFT(ce.text_content, 100) as content_preview,
    ce.created_at,
    -- 聚類統計
    COUNT(*) OVER (PARTITION BY ce.cluster_id) as cluster_size,
    -- 類別統計
    COUNT(*) OVER (PARTITION BY ce.predicted_category) as category_count
FROM chat_message_embeddings_1024 ce
WHERE ce.user_role = 'user'  -- 只分析用戶問題
ORDER BY ce.created_at DESC;

-- 輸出創建結果
\echo '✅ chat_message_embeddings_1024 表創建完成'
\echo '✅ 向量索引創建完成'
\echo '✅ 觸發器創建完成'
\echo '✅ 分析視圖創建完成'

-- 顯示表結構
\d chat_message_embeddings_1024