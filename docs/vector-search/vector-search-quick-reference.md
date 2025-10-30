# 向量搜尋快速參考指南

## 🚀 快速開始

### 1. 環境檢查
```bash
# 檢查 pgvector 擴展
docker exec postgres_db psql -U postgres -d ai_platform -c "SELECT * FROM pg_extension WHERE extname = 'vector';"

# 檢查向量表
docker exec postgres_db psql -U postgres -d ai_platform -c "SELECT COUNT(*) FROM document_embeddings;"
```

### 2. 資料準備
```bash
# 創建 RVT Guide 測試資料
docker exec ai-django python manage.py create_rvt_guide_data

# 生成向量嵌入
docker exec ai-django python manage.py generate_rvt_embeddings
```

### 3. 測試搜尋
```bash
# API 測試
curl -X POST "http://10.10.172.127/api/dify/knowledge/retrieval/" \
  -H "Content-Type: application/json" \
  -d '{
    "knowledge_id": "rvt_guide_db",
    "query": "Jenkins 測試階段",
    "retrieval_setting": {
      "top_k": 3,
      "score_threshold": 0.3
    }
  }'
```

## 📝 常用命令

### Django 管理命令
```bash
# 創建資料
docker exec ai-django python manage.py create_rvt_guide_data

# 生成向量（標準模型）
docker exec ai-django python manage.py generate_rvt_embeddings

# 強制重新生成
docker exec ai-django python manage.py generate_rvt_embeddings --force

# 使用輕量級模型
docker exec ai-django python manage.py generate_rvt_embeddings --model-name paraphrase-multilingual-MiniLM-L12-v2
```

### 資料庫查詢
```sql
-- 檢查向量資料
SELECT source_table, COUNT(*) FROM document_embeddings GROUP BY source_table;

-- 檢查 RVT Guide 資料
SELECT COUNT(*) FROM api_rvtguide WHERE status = 'published';

-- 測試向量搜尋（需要實際向量）
SELECT source_id, 1 - (embedding <=> '[0.1,0.2,...]') as similarity 
FROM document_embeddings 
WHERE source_table = 'rvt_guide' 
ORDER BY similarity DESC LIMIT 3;
```

## 🔧 程式碼範例

### Python 向量搜尋
```python
from api.services.embedding_service import search_rvt_guide_with_vectors

# 基本搜尋
results = search_rvt_guide_with_vectors(
    query="Jenkins 有哪些階段？",
    limit=5,
    threshold=0.3
)

# 處理結果
for result in results:
    print(f"標題: {result['title']}")
    print(f"相似度: {result['score']:.3f}")
    print(f"內容片段: {result['content'][:100]}...")
    print("-" * 50)
```

### Django API 使用
```python
from api.services.embedding_service import get_embedding_service

# 獲取嵌入服務
service = get_embedding_service('standard')

# 生成單個向量
embedding = service.generate_embedding("測試文本")

# 儲存文檔向量
success = service.store_document_embedding(
    source_table='rvt_guide',
    source_id=1,
    content="文檔內容"
)

# 搜尋相似文檔
results = service.search_similar_documents(
    query="搜尋查詢",
    source_table='rvt_guide',
    limit=5
)
```

## 🎯 效能調校

### 模型選擇
- **測試/開發**: `lightweight` (384維, 快速)
- **生產環境**: `standard` (768維, 平衡)
- **高精度需求**: `high_precision` (768維, 英文優化)

### 搜尋參數調校
```python
# 相似度閾值建議
threshold_settings = {
    'strict': 0.7,      # 高精度，少結果
    'balanced': 0.5,    # 平衡
    'loose': 0.3,       # 廣泛搜尋
    'very_loose': 0.1   # 最大覆蓋
}

# 結果數量建議
top_k_settings = {
    'quick_answer': 3,
    'detailed_search': 5,
    'comprehensive': 10
}
```

## 🚨 故障排除

### 常見錯誤
```bash
# 1. 模組未安裝
pip install sentence-transformers torch

# 2. pgvector 擴展缺失
docker exec postgres_db psql -U postgres -d ai_platform -c "CREATE EXTENSION IF NOT EXISTS vector;"

# 3. 向量維度不匹配
# 檢查模型維度，更新資料庫欄位定義

# 4. 記憶體不足
# 使用較小的批量大小或輕量級模型
```

### 除錯技巧
```python
# 檢查向量生成
embedding = service.generate_embedding("測試")
print(f"向量維度: {len(embedding)}")
print(f"向量範例: {embedding[:5]}")

# 檢查搜尋結果
results = search_rvt_guide_with_vectors("測試查詢", threshold=0.0)
print(f"找到 {len(results)} 個結果")
```

## 📊 監控指標

### 關鍵指標
- 向量生成速度 (docs/second)
- 搜尋回應時間 (milliseconds)
- 搜尋準確率 (relevance score)
- 資料庫大小 (MB)

### 日誌檢查
```bash
# Django 日誌
docker logs ai-django | grep -i "embedding\|vector"

# PostgreSQL 日誌
docker logs postgres_db | grep -i "vector\|embedding"
```

## 🔗 相關連結

- **完整文檔**: `/docs/vector-search-guide.md`
- **API 文檔**: `/docs/api-integration.md`
- **Dify 整合**: `/docs/dify-external-knowledge-api-guide.md`
- **程式碼**: `/backend/api/services/embedding_service.py`