-- 文檔級搜尋功能：資料庫結構升級
-- 添加文檔層級欄位
ALTER TABLE document_section_embeddings 
ADD COLUMN IF NOT EXISTS document_id VARCHAR(100);

ALTER TABLE document_section_embeddings 
ADD COLUMN IF NOT EXISTS document_title TEXT;

ALTER TABLE document_section_embeddings 
ADD COLUMN IF NOT EXISTS is_document_title BOOLEAN DEFAULT FALSE;

-- 創建索引
CREATE INDEX IF NOT EXISTS idx_document_section_embeddings_doc_id 
    ON document_section_embeddings(document_id);

CREATE INDEX IF NOT EXISTS idx_document_section_embeddings_is_doc_title 
    ON document_section_embeddings(is_document_title);

-- 驗證
SELECT column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_name = 'document_section_embeddings' 
    AND column_name IN ('document_id', 'document_title', 'is_document_title');
