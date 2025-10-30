# 向量搜尋系統 - AI 助手專用指南

## 🎯 目的
本文檔為 AI 助手提供向量搜尋系統的操作指南，確保能正確協助使用者建立、維護和使用向量搜尋功能。

---

## 📋 系統概況

### 核心技術棧
- **向量資料庫**: PostgreSQL + pgvector 擴展
- **嵌入模型**: Sentence Transformers (開源)
- **整合介面**: Django REST API
- **應用場景**: Dify 外部知識庫

### 支援的知識庫
- **RVT Guide**: RVT 測試系統使用指南
- **可擴展**: 支援新增其他知識庫類型

---

## 🚀 快速檢查清單

### 環境檢查命令
```bash
# 1. 檢查 pgvector 擴展
docker exec postgres_db psql -U postgres -d ai_platform -c "SELECT * FROM pg_extension WHERE extname = 'vector';"

# 2. 檢查向量表存在
docker exec postgres_db psql -U postgres -d ai_platform -c "\dt document_embeddings"

# 3. 檢查 Django 容器狀態
docker ps | grep ai-django

# 4. 檢查 Python 套件
docker exec ai-django python -c "import sentence_transformers; print('✅ Sentence Transformers 已安裝')"
```

### 資料狀態檢查
```bash
# 檢查 RVT Guide 資料
docker exec postgres_db psql -U postgres -d ai_platform -c "SELECT COUNT(*) FROM api_rvtguide WHERE status = 'published';"

# 檢查向量資料
docker exec postgres_db psql -U postgres -d ai_platform -c "SELECT source_table, COUNT(*) FROM document_embeddings GROUP BY source_table;"
```

---

## 🔧 常用操作流程

### 1. 首次建立向量搜尋系統
```bash
# 步驟1: 確保 pgvector 擴展已安裝
docker exec postgres_db psql -U postgres -d ai_platform -f /scripts/init-pgvector.sql

# 步驟2: 安裝 Python 依賴
docker exec ai-django pip install sentence-transformers torch transformers

# 步驟3: 創建 RVT Guide 測試資料
docker exec ai-django python manage.py create_rvt_guide_data

# 步驟4: 生成向量嵌入
docker exec ai-django python manage.py generate_rvt_embeddings

# 步驟5: 測試搜尋功能
curl -X POST "http://10.10.172.127/api/dify/knowledge/retrieval/" \
  -H "Content-Type: application/json" \
  -d '{"knowledge_id": "rvt_guide_db", "query": "Jenkins 測試階段", "retrieval_setting": {"top_k": 3, "score_threshold": 0.3}}'
```

### 2. 重新生成向量（資料更新後）
```bash
# 強制重新生成所有向量
docker exec ai-django python manage.py generate_rvt_embeddings --force

# 使用不同模型
docker exec ai-django python manage.py generate_rvt_embeddings --model-name paraphrase-multilingual-mpnet-base-v2
```

### 3. 故障排除流程
```bash
# 檢查日誌
docker logs ai-django | tail -50 | grep -i "embedding\|vector"

# 重啟相關服務
docker compose restart ai-django postgres_db

# 清理重建（謹慎使用）
docker exec postgres_db psql -U postgres -d ai_platform -c "TRUNCATE document_embeddings;"
docker exec ai-django python manage.py generate_rvt_embeddings
```

---

## 🔍 搜尋測試案例

### API 測試範例
```bash
# 測試1: 基本搜尋
curl -X POST "http://10.10.172.127/api/dify/knowledge/retrieval/" \
  -H "Content-Type: application/json" \
  -d '{
    "knowledge_id": "rvt_guide_db",
    "query": "什麼是 RVT",
    "retrieval_setting": {"top_k": 3, "score_threshold": 0.3}
  }'

# 測試2: Jenkins 相關查詢
curl -X POST "http://10.10.172.127/api/dify/knowledge/retrieval/" \
  -H "Content-Type: application/json" \
  -d '{
    "knowledge_id": "rvt_guide_db",
    "query": "Jenkins 有哪些階段",
    "retrieval_setting": {"top_k": 5, "score_threshold": 0.2}
  }'

# 測試3: Ansible 配置查詢
curl -X POST "http://10.10.172.127/api/dify/knowledge/retrieval/" \
  -H "Content-Type: application/json" \
  -d '{
    "knowledge_id": "rvt_guide_db", 
    "query": "如何設定 Ansible 參數",
    "retrieval_setting": {"top_k": 3, "score_threshold": 0.3}
  }'
```

### 預期回應檢查
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

## 🚨 常見問題與解決方案

### 問題1: 向量表不存在
```
錯誤: relation "document_embeddings" does not exist
解決: docker exec postgres_db psql -U postgres -d ai_platform -f /scripts/init-pgvector.sql
```

### 問題2: 模型載入失敗
```
錯誤: ModuleNotFoundError: No module named 'sentence_transformers'
解決: docker exec ai-django pip install sentence-transformers torch
```

### 問題3: 向量維度不匹配
```
錯誤: dimension mismatch
解決: 
1. 檢查模型配置
2. 更新資料庫欄位: ALTER TABLE document_embeddings ALTER COLUMN embedding TYPE vector(768);
3. 重新生成向量
```

### 問題4: 搜尋無結果
```
檢查步驟:
1. 確認資料存在: SELECT COUNT(*) FROM document_embeddings;
2. 降低閾值: "score_threshold": 0.1
3. 檢查查詢處理: 在 Django 日誌中查看查詢向量生成
```

### 問題5: 效能問題
```
優化方案:
1. 調整索引: CREATE INDEX ... WITH (lists = 200);
2. 使用輕量級模型: --model-name paraphrase-multilingual-MiniLM-L12-v2
3. 減少批量大小: --batch-size 5
```

---

## 📊 效能監控指標

### 關鍵數據
```bash
# 向量資料量
docker exec postgres_db psql -U postgres -d ai_platform -c "SELECT COUNT(*) as total_vectors FROM document_embeddings;"

# 資料庫大小
docker exec postgres_db psql -U postgres -d ai_platform -c "SELECT pg_size_pretty(pg_database_size('ai_platform'));"

# 搜尋效能測試
time curl -X POST "http://10.10.172.127/api/dify/knowledge/retrieval/" \
  -H "Content-Type: application/json" \
  -d '{"knowledge_id": "rvt_guide_db", "query": "測試查詢"}'
```

### 日誌監控
```bash
# 查看嵌入生成日誌
docker logs ai-django 2>&1 | grep -E "(embedding|vector|成功|失敗)" | tail -20

# 查看搜尋請求日誌
docker logs ai-django 2>&1 | grep -E "(dify.*knowledge|rvt.*guide)" | tail -10
```

---

## 🎯 最佳協助實踐

### 對使用者的建議順序
1. **環境檢查**: 先確認 Docker 容器運行正常
2. **依賴檢查**: 確認 pgvector 和 Python 套件已安裝
3. **資料檢查**: 確認 RVT Guide 資料和向量已生成
4. **功能測試**: 進行 API 測試確認搜尋正常
5. **整合測試**: 在 Dify 中配置並測試外部知識庫

### 協助使用者時的注意事項
- **安全性**: 避免在日誌中記錄敏感資訊
- **效能**: 建議使用適當的批量大小和模型
- **維護性**: 提供清晰的操作步驟和回退方案
- **監控**: 教導使用者如何監控系統狀態

### 推薦的模型選擇
- **開發/測試**: `lightweight` (384維)
- **生產環境**: `standard` (768維)
- **高精度需求**: `high_precision` (768維)

---

## 📝 相關文檔連結
- **完整指南**: `/docs/vector-search-guide.md`
- **快速參考**: `/docs/vector-search-quick-reference.md`
- **API 整合**: `/docs/guide/api-integration.md`
- **Dify 整合**: `/docs/guide/dify-external-knowledge-api-guide.md`

---

*最後更新: 2024-09-21*