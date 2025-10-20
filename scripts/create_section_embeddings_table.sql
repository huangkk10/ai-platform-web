-- 創建段落向量表 (Section Embeddings Table)
-- 用途：儲存 Markdown 文檔的段落級別向量，支援精準的段落搜尋
-- 執行命令: docker exec postgres_db psql -U postgres -d ai_platform -f /docker-entrypoint-initdb.d/create_section_embeddings_table.sql
--
-- 設計特點：
-- 1. 通用設計：透過 source_table 欄位支援所有知識庫（protocol_guide, rvt_guide, qa_guide 等）
-- 2. 標準化向量：統一使用 1024 維向量（intfloat/multilingual-e5-large 模型）
-- 3. 結構化段落：保留 Markdown 標題層級和路徑資訊
-- 4. 高效索引：IVFFlat 向量索引 + 多個查詢優化索引

-- 創建段落向量表
CREATE TABLE IF NOT EXISTS document_section_embeddings (
    id SERIAL PRIMARY KEY,
    
    -- 來源關聯（通用設計，支援所有知識庫）
    source_table VARCHAR(100) NOT NULL,      -- 來源表名：'protocol_guide', 'rvt_guide', 'qa_guide' 等
    source_id INTEGER NOT NULL,              -- 來源記錄 ID
    section_id VARCHAR(50) NOT NULL,         -- 段落唯一 ID（如 'sec_1', 'sec_2_1'）
    
    -- 段落結構資訊
    heading_level INTEGER,                   -- 標題層級 (1-6，對應 H1-H6)
    heading_text VARCHAR(500),               -- 標題文字
    section_path TEXT,                       -- 完整路徑（麵包屑）如 'Guide > Chapter > Section'
    parent_section_id VARCHAR(50),           -- 父段落 ID（用於層級關係）
    
    -- 內容
    content TEXT,                            -- 段落內容（不含子段落）
    full_context TEXT,                       -- 完整上下文（含路徑資訊，用於向量生成）
    
    -- 向量數據（1024 維標準）
    embedding vector(1024),                  -- 1024 維語義向量
    
    -- 元數據
    word_count INTEGER DEFAULT 0,            -- 字數統計
    has_code BOOLEAN DEFAULT FALSE,          -- 是否包含代碼塊
    has_images BOOLEAN DEFAULT FALSE,        -- 是否包含圖片
    
    -- 時間戳記
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 唯一約束：確保每個來源記錄的每個段落只有一個向量
    UNIQUE(source_table, source_id, section_id)
);

-- ========================================
-- 索引創建（優化查詢效能）
-- ========================================

-- 1. 來源查詢索引（最常用）
CREATE INDEX IF NOT EXISTS idx_section_embeddings_source 
    ON document_section_embeddings(source_table, source_id);

-- 2. 向量相似度搜尋索引（IVFFlat，核心功能）
CREATE INDEX IF NOT EXISTS idx_section_embeddings_vector 
    ON document_section_embeddings 
    USING ivfflat (embedding vector_cosine_ops) 
    WITH (lists = 100);

-- 3. 標題層級過濾索引
CREATE INDEX IF NOT EXISTS idx_section_embeddings_level 
    ON document_section_embeddings(heading_level);

-- 4. 時間查詢索引
CREATE INDEX IF NOT EXISTS idx_section_embeddings_created 
    ON document_section_embeddings(created_at DESC);

-- 5. 複合索引：來源 + 層級（用於篩選特定來源的特定層級段落）
CREATE INDEX IF NOT EXISTS idx_section_embeddings_source_level 
    ON document_section_embeddings(source_table, source_id, heading_level);

-- ========================================
-- 觸發器：自動更新 updated_at
-- ========================================

CREATE OR REPLACE FUNCTION update_section_embeddings_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER IF NOT EXISTS section_embeddings_updated_at_trigger
    BEFORE UPDATE ON document_section_embeddings
    FOR EACH ROW
    EXECUTE FUNCTION update_section_embeddings_updated_at();

-- ========================================
-- 輔助視圖：段落統計分析
-- ========================================

CREATE OR REPLACE VIEW section_embeddings_statistics AS
SELECT 
    source_table,
    COUNT(*) as total_sections,
    COUNT(DISTINCT source_id) as total_documents,
    ROUND(AVG(word_count), 2) as avg_word_count,
    ROUND(AVG(heading_level), 2) as avg_heading_level,
    SUM(CASE WHEN has_code THEN 1 ELSE 0 END) as sections_with_code,
    SUM(CASE WHEN has_images THEN 1 ELSE 0 END) as sections_with_images,
    MAX(created_at) as latest_update
FROM document_section_embeddings
GROUP BY source_table
ORDER BY source_table;

-- ========================================
-- 輔助函數：計算段落密度
-- ========================================

CREATE OR REPLACE FUNCTION get_section_density(p_source_table VARCHAR, p_source_id INTEGER)
RETURNS TABLE(
    source_id INTEGER,
    total_sections INTEGER,
    sections_per_level JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p_source_id,
        COUNT(*)::INTEGER as total_sections,
        jsonb_object_agg(heading_level::TEXT, count) as sections_per_level
    FROM (
        SELECT 
            heading_level,
            COUNT(*)::INTEGER as count
        FROM document_section_embeddings
        WHERE source_table = p_source_table AND source_id = p_source_id
        GROUP BY heading_level
    ) level_counts;
END;
$$ LANGUAGE plpgsql;

-- ========================================
-- 完成訊息
-- ========================================

\echo '✅ document_section_embeddings 表創建完成'
\echo '✅ 5 個優化索引創建完成'
\echo '✅ updated_at 自動更新觸發器創建完成'
\echo '✅ 統計分析視圖創建完成'
\echo '✅ 輔助函數創建完成'
\echo ''
\echo '📊 表結構：'
\d document_section_embeddings
\echo ''
\echo '📈 統計視圖：'
\d section_embeddings_statistics
