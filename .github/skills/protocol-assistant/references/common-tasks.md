# Protocol Assistant — 常見任務操作指南

## 1. 新增全文搜尋關鍵字（Mode A 觸發）

當某個詞語應該觸發「取得完整文件」模式時：

**修改檔案**: `library/common/query_analysis/keyword_detector.py`

```python
FULL_DOCUMENT_KEYWORDS = [
    "完整",
    "overview",
    "全部",
    # 在這裡新增關鍵字
    "your_new_keyword",
]
```

> 注意：觸發 Mode A 後，keyword_triggered_handler 會在 query 前面加上 `__FULL_SEARCH__` 標記，Dify callback 的 `dify_knowledge_views.py` 收到後會用 top_k=50 搜尋整份文件。

---

## 2. 調整搜尋參數（top_k、分數門檻）

**修改檔案**: `library/protocol_guide/smart_search_config.py`

```python
@dataclass
class SmartSearchConfig:
    # Mode A 全文搜尋
    mode_a_top_k: int = 10
    mode_a_score_threshold: float = 0.5

    # Mode B Stage 1（初步搜尋）
    mode_b_stage1_top_k: int = 5
    mode_b_stage1_score_threshold: float = 0.6

    # Mode B Stage 2（精確重查）
    mode_b_stage2_top_k: int = 3
    mode_b_stage2_score_threshold: float = 0.7
```

常見調整場景：
- 結果太少：降低 `score_threshold`（例如 0.6 → 0.4）
- 結果太多/不精確：提高 `score_threshold` 或降低 `top_k`
- Stage 1 找不到但問題很明確：降低 `mode_b_stage1_score_threshold`

---

## 3. 調整不確定性偵測（Fallback 觸發條件）

當 AI 回答「建議您參考以下文件」等內容時，代表觸發了 Fallback。

**修改檔案**: `library/common/ai_response/uncertainty_detector.py`

```python
UNCERTAINTY_KEYWORDS = [
    "建議您參考",
    "請參閱",
    "I don't know",
    # 新增 fallback 關鍵字
]

MIN_RESPONSE_LENGTH = 20  # 回答少於 20 字元視為無效
```

> 若 `is_uncertain_response(answer)` = True，回應會附上文件列表而非原始 AI 回答。

---

## 4. 切換 Dev / Prod Dify App

**修改檔案**: `docker-compose.yml`

```yaml
environment:
  - DIFY_ENV=development    # 使用 dev app key
  # - DIFY_ENV=production   # 使用 prod app key
```

API Key 設定位置: `library/config/dify_config_manager.py`
- Dev Key: `app-4TbH1O7NkpOFsnxGEF3FLyqd` (Protocol_Guide_dev)
- Prod Key: `app-MgZZOhADkEmdUrj2DtQLJ23G` (Protocol_Guide_prod)

切換後需重啟 backend container：
```bash
docker-compose restart backend
```

---

## 5. 新增知識庫文件

### 步驟 1：新增資料到 DB
```python
# 透過 Django shell 或管理介面
from backend.api.models import ProtocolGuide

ProtocolGuide.objects.create(
    title="文件標題",
    content="文件內容...",
    protocol_type="CrystalDiskMark",  # 或其他類型
)
```

### 步驟 2：產生向量
```bash
cd /home/user/codes/ai-platform-web
python backend/generate_all_protocol_sections.py
```

或針對特定文件重跑向量生成：
```bash
python backend/regenerate_cup_sections.py
python backend/regenerate_section_multi_vectors.py
```

---

## 6. 測試 API

### 前端聊天 API
```bash
curl -X POST http://localhost/api/protocol-assistant/chat/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"message": "CrystalDiskMark 完整測試流程", "conversation_id": ""}'
```

### Dify 外部知識庫 callback（測試 retrieval）
```bash
curl -X POST http://10.10.172.127/api/dify/knowledge/retrieval/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_DIFY_KEY" \
  -d '{
    "knowledge_id": "protocol_guide_database",
    "query": "CrystalDiskMark",
    "retrieval_setting": {"top_k": 5, "score_threshold": 0.5}
  }'
```

### 直接測試搜尋
```bash
cd /home/user/codes/ai-platform-web
python backend/test_crystaldiskmark_search.py
python backend/test_direct_search.py
```

---

## 7. Dify 設定注意事項

### Reranking 必須關閉
- Protocol_Guide_dev 和 Protocol_Guide_prod 都必須**關閉 Reranking 選項**
- 開啟後若 `reranking_model_name` 未設定，Dify 會返回 HTTP 400
- 錯誤訊息：`reranking_model_name Field required`

### 外部知識庫 URL 格式
- 格式：`http://10.10.172.127/api/dify/knowledge/retrieval/`
- 路徑末尾需要有 `/`
- Authorization Header 必須對應 `backend/api/views/dify_knowledge_views.py` 的驗證設定

---

## 8. 常見問題排查

### 問題：Protocol Assistant 只顯示「建議您參考以下文件」

**診斷步驟**：
1. 檢查 Django log 中 Dify API 回傳狀態碼
2. 若 HTTP 400 → 確認 Reranking 已關閉
3. 若 HTTP 504/timeout → 確認外部知識庫 URL 中 IP 正確（`10.10.172.127`）
4. 若 `answer = ''` → 確認 Dify app 已發布（Published）

**快速診斷指令**：
```bash
# 確認 Dify dev app 可聯通
curl -X POST http://10.253.43.244/v1/chat-messages \
  -H "Authorization: Bearer app-4TbH1O7NkpOFsnxGEF3FLyqd" \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "inputs": {}, "response_mode": "blocking", "conversation_id": ""}'
```

### 問題：向量搜尋沒有結果

1. 確認 `ProtocolGuide` 資料表有資料：`SELECT COUNT(*) FROM protocol_guide;`
2. 確認向量已產生：檢查 `protocol_guide_vectors` 表
3. 確認 pgvector extension 已安裝：`SELECT * FROM pg_extension WHERE extname='vector';`

### 問題：Mode A/B 路由不正確

Debug 方式：加 log 在 `SmartSearchRouter.handle_smart_search()` 開頭：
```python
import logging
logger = logging.getLogger(__name__)
logger.debug(f"[Router] query={query}, has_full_keyword={contains_full_document_keywords(query)}")
```

---

## 9. 修改觸發閾值後的驗證流程

1. 修改 `smart_search_config.py`
2. 重啟 backend: `docker-compose restart backend`
3. 執行測試: `python backend/test_backend_core_features.py`
4. 發送測試問題至前端確認結果符合預期
