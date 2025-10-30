# AI Platform 向量搜尋系統完整指南

## 📋 概述

本文檔詳細記錄了 AI Platform 中向量搜尋系統的建立、配置和使用方法。向量搜尋系統使用開源的 Sentence Transformers 模型，結合 PostgreSQL + pgvector 擴展，為 Dify 外部知識庫提供語義搜尋能力。

---

## 🏗️ 系統架構

### 核心組件
1. **PostgreSQL + pgvector** - 向量資料庫儲存
2. **Sentence Transformers** - 開源向量嵌入模型
3. **Django 服務層** - 向量生成和搜尋 API
4. **Dify 整合** - 外部知識庫接口

### 資料流程
```
文檔內容 → Sentence Transformers → 向量嵌入 → PostgreSQL(pgvector) → 搜尋結果
```

---

## 🚀 系統安裝與設置

### 1. 資料庫初始化

#### 安裝 pgvector 擴展
```sql
-- 初始化 pgvector 擴展
CREATE EXTENSION IF NOT EXISTS vector;
```

#### 創建向量嵌入表
```sql
-- 創建文檔向量嵌入表
CREATE TABLE IF NOT EXISTS document_embeddings (
    id SERIAL PRIMARY KEY,
    source_table VARCHAR(100) NOT NULL,
    source_id INTEGER NOT NULL,
    text_content TEXT,                  -- 新增：儲存原始文本內容
    content_hash VARCHAR(64) NOT NULL,
    embedding vector(768),              -- 768維向量，適用於標準模型
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
```

#### 執行初始化腳本
```bash
# 在 Docker 容器中執行
docker exec postgres_db psql -U postgres -d ai_platform -f /docker-entrypoint-initdb.d/init-pgvector.sql
```

### 2. Python 依賴安裝

#### requirements.txt 添加
```txt
sentence-transformers>=2.2.2
torch>=1.9.0
transformers>=4.21.0
numpy>=1.21.0
```

#### Docker 容器中安裝
```bash
docker exec ai-django pip install sentence-transformers torch transformers numpy
```

---

## 🤖 模型配置

### 支援的模型類型

#### 1. 輕量級模型 (lightweight)
```python
MODEL_CONFIG = {
    'name': 'paraphrase-multilingual-MiniLM-L12-v2',
    'dimension': 384,
    'description': '輕量級多語言模型，平衡效能與精準度',
    'use_case': '小規模應用，快速回應'
}
```

#### 2. 標準模型 (standard) - 推薦
```python
MODEL_CONFIG = {
    'name': 'paraphrase-multilingual-mpnet-base-v2', 
    'dimension': 768,
    'description': '標準多語言模型，更高精準度',
    'use_case': '生產環境推薦，平衡精準度與效能'
}
```

#### 3. 高精準度模型 (high_precision)
```python
MODEL_CONFIG = {
    'name': 'sentence-transformers/all-mpnet-base-v2',
    'dimension': 768,
    'description': '高精準度模型，主要支援英文',
    'use_case': '英文內容為主的高精準度需求'
}
```

---

## 📝 資料模型與結構

### RVTGuide 模型結構
```python
class RVTGuide(models.Model):
    document_name = models.CharField('文檔名稱', max_length=200, unique=True)
    title = models.CharField('標題', max_length=200)
    version = models.CharField('版本', max_length=50, default='1.0')
    main_category = models.CharField('主分類', max_length=50, choices=MAIN_CATEGORY_CHOICES)
    sub_category = models.CharField('子分類', max_length=50, choices=SUB_CATEGORY_CHOICES)
    content = models.TextField('內容')
    keywords = models.TextField('關鍵字', blank=True, null=True)
    question_type = models.CharField('問題類型', max_length=50, choices=QUESTION_TYPE_CHOICES)
    target_user = models.CharField('目標使用者', max_length=50, choices=TARGET_USER_CHOICES)
    status = models.CharField('狀態', max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField('創建時間', auto_now_add=True)
    updated_at = models.DateTimeField('更新時間', auto_now=True)
```

### 向量嵌入表結構
```sql
document_embeddings (
    id: SERIAL PRIMARY KEY,
    source_table: VARCHAR(100),     -- 'rvt_guide'
    source_id: INTEGER,             -- RVTGuide 的 ID
    text_content: TEXT,             -- 原始文本內容
    content_hash: VARCHAR(64),      -- 內容哈希值
    embedding: vector(768),         -- 768維向量
    created_at: TIMESTAMP,
    updated_at: TIMESTAMP
)
```

---

## 🔧 管理命令使用

### 1. 創建 RVT Guide 測試數據
```bash
# 創建基礎的 RVT Guide 文檔
docker exec ai-django python manage.py create_rvt_guide_data

# 輸出範例：
# ✅ 創建文檔: RVT 系統架構概念說明
# ✅ 創建文檔: 解讀 Jenkins 測試階段 (Stages)
# ✅ 創建文檔: 系統安裝前的先決條件
# 🎉 RVT Guide 數據建立完成！
```

### 2. 生成向量嵌入
```bash
# 基本使用 - 使用預設模型
docker exec ai-django python manage.py generate_rvt_embeddings

# 強制重新生成所有向量
docker exec ai-django python manage.py generate_rvt_embeddings --force

# 指定批量大小
docker exec ai-django python manage.py generate_rvt_embeddings --batch-size 5

# 指定模型
docker exec ai-django python manage.py generate_rvt_embeddings --model-name paraphrase-multilingual-mpnet-base-v2

# 輸出範例：
# 🚀 開始為 RVT Guide 生成向量嵌入
# 🔧 初始化嵌入服務...
# 🧠 載入 Sentence Transformers 模型...
# ✅ 模型載入成功！向量維度: 768
# 📚 找到 6 篇 RVT Guide 文檔
# 📦 處理批次 1 (6 個文檔)...
#   ✅ RVT 系統架構概念說明
#   ✅ 解讀 Jenkins 測試階段 (Stages)
# 🎉 向量生成完成！
```

---

## 🔍 搜尋 API 使用

### 1. 向量搜尋服務
```python
from api.services.embedding_service import get_embedding_service

# 初始化服務
service = get_embedding_service('standard')  # 或 'lightweight', 'high_precision'

# 單文檔向量生成
embedding = service.generate_embedding("Jenkins 測試階段")

# 批量生成
embeddings = service.generate_embeddings_batch(["文檔1", "文檔2"])

# 儲存文檔向量
success = service.store_document_embedding(
    source_table='rvt_guide',
    source_id=1,
    content="文檔內容..."
)

# 搜尋相似文檔
results = service.search_similar_documents(
    query="Jenkins 有哪些階段",
    source_table='rvt_guide',
    limit=5,
    threshold=0.3
)
```

### 2. RVT Guide 專用搜尋
```python
from api.services.embedding_service import search_rvt_guide_with_vectors

# 搜尋 RVT Guide
results = search_rvt_guide_with_vectors(
    query="如何設定 Ansible 參數",
    limit=5,
    threshold=0.3
)

# 結果格式
# [
#     {
#         'id': '4',
#         'title': 'Ansible 配置與參數設定',
#         'content': '設定有三大部分：設定、測試平台、測項...',
#         'score': 0.85,
#         'metadata': {
#             'document_name': 'RVT-配置管理-Ansible設定',
#             'main_category': 'configuration_management',
#             'sub_category': 'machine_configuration',
#             'source': 'rvt_guide_vector_search'
#         }
#     }
# ]
```

---

## 🌐 Dify 外部知識庫整合

### 1. API 端點配置
```
主要端點: http://10.10.172.127/api/dify/knowledge/retrieval/
RVT專用: http://10.10.172.127/api/dify/rvt-guide/retrieval/
```

### 2. Knowledge ID 支援
```
- rvt_guide_db
- rvt_guide  
- rvt-guide
- rvt_user_guide
```

### 3. API 請求格式
```json
{
    "knowledge_id": "rvt_guide_db",
    "query": "Jenkins 有哪些測試階段",
    "retrieval_setting": {
        "top_k": 5,
        "score_threshold": 0.3
    }
}
```

### 4. API 回應格式
```json
{
    "records": [
        {
            "content": "文檔標題: 解讀 Jenkins 測試階段...",
            "score": 0.85,
            "title": "解讀 Jenkins 測試階段 (Stages)",
            "metadata": {
                "document_name": "RVT-操作流程-Jenkins測試階段",
                "main_category": "operation_flow",
                "source": "rvt_guide_vector_search"
            }
        }
    ]
}
```

---

## 🛠️ 維護與管理

### 1. 效能優化

#### 索引優化
```sql
-- 檢查索引使用情況
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM document_embeddings 
ORDER BY embedding <=> '[0.1,0.2,...]' 
LIMIT 5;

-- 調整 ivfflat 索引的 lists 參數
DROP INDEX document_embeddings_vector_idx;
CREATE INDEX document_embeddings_vector_idx 
ON document_embeddings USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 200);  -- 根據資料量調整
```

#### 模型載入優化
```python
# 預熱模型（在應用啟動時）
service = get_embedding_service()
service.generate_embedding("測試文本")  # 觸發模型載入
```

### 2. 資料同步策略

#### 增量更新
```python
# 檢查內容是否變更
content_hash = service.get_content_hash(new_content)
# 只有內容變更時才重新生成向量
```

#### 批量重建
```bash
# 重建所有向量（維護視窗期間）
docker exec ai-django python manage.py generate_rvt_embeddings --force --batch-size 20
```

### 3. 監控與日誌
```python
import logging
logger = logging.getLogger(__name__)

# 向量生成日誌
logger.info(f"成功生成向量，維度: {len(embedding)}")

# 搜尋效能日誌  
logger.info(f"向量搜尋完成，耗時: {elapsed:.2f}s，結果數: {len(results)}")
```

---

## 📊 故障排除

### 常見問題與解決方案

#### 1. 模型載入失敗
```bash
# 問題：ModuleNotFoundError: No module named 'sentence_transformers'
# 解決：
docker exec ai-django pip install sentence-transformers

# 問題：CUDA memory error
# 解決：使用 CPU 版本或調整批量大小
export CUDA_VISIBLE_DEVICES=""
```

#### 2. pgvector 擴展問題
```sql
-- 檢查擴展是否安裝
SELECT * FROM pg_extension WHERE extname = 'vector';

-- 重新安裝擴展
DROP EXTENSION IF EXISTS vector CASCADE;
CREATE EXTENSION vector;
```

#### 3. 向量維度不匹配
```python
# 問題：dimension mismatch
# 解決：確保模型維度與資料庫欄位一致

# 更新資料庫向量維度
ALTER TABLE document_embeddings 
ALTER COLUMN embedding TYPE vector(768);
```

#### 4. 搜尋結果為空
```python
# 檢查資料是否存在
SELECT COUNT(*) FROM document_embeddings WHERE source_table = 'rvt_guide';

# 降低相似度閾值
results = search_rvt_guide_with_vectors(query, threshold=0.1)

# 檢查查詢文本處理
logger.debug(f"查詢向量: {query_embedding[:5]}...")
```

---

## 🎯 最佳實踐

### 1. 模型選擇建議
- **小規模應用** (< 1000 文檔): lightweight (384維)
- **生產環境** (1000-10000 文檔): standard (768維)
- **大規模應用** (> 10000 文檔): high_precision (768維)

### 2. 資料預處理
```python
def prepare_document_content(rvt_guide):
    """準備用於向量化的文檔內容"""
    content_parts = [
        f"標題: {rvt_guide.title}",
        f"主分類: {rvt_guide.get_main_category_display()}",
        f"子分類: {rvt_guide.get_sub_category_display()}",
        f"內容: {rvt_guide.content}",
        f"關鍵字: {rvt_guide.keywords}",
        f"問題類型: {rvt_guide.get_question_type_display()}"
    ]
    return "\n".join(content_parts)
```

### 3. 查詢優化
```python
# 中文查詢預處理
def preprocess_chinese_query(query):
    # 移除問號和標點符號
    processed = query.replace('？', '').replace('?', '')
    
    # 關鍵字擴展
    keyword_expansions = {
        '什麼是RVT': 'RVT 系統架構',
        'Jenkins有哪些階段': 'Jenkins 測試階段',
        'Ansible如何設定': 'Ansible 配置'
    }
    
    for pattern, replacement in keyword_expansions.items():
        if pattern in processed:
            return replacement
    
    return processed
```

### 4. 效能監控
```python
import time

def monitor_search_performance(query, limit=5):
    start_time = time.time()
    results = search_rvt_guide_with_vectors(query, limit=limit)
    elapsed = time.time() - start_time
    
    logger.info(f"搜尋查詢: '{query}', 結果數: {len(results)}, 耗時: {elapsed:.2f}s")
    
    return results
```

---

## 📅 版本歷史

- **v1.0** (2024-09-21): 初始版本，支援基本向量搜尋
- **v1.1** (2024-09-21): 新增多模型支援，優化中文搜尋
- **v1.2** (2024-09-21): 整合 Dify 外部知識庫，新增管理命令


---

*本文檔最後更新時間: 2024-09-21*