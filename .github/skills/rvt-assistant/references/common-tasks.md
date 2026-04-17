# RVT Assistant — 常見任務操作指南

## 1. 新增全文搜尋關鍵字（Mode A 觸發）

**修改檔案**: `library/common/query_analysis/keyword_detector.py`

```python
FULL_DOCUMENT_KEYWORDS = [
    '完整', '全部', ...
    # 在此新增，RVT 和 Protocol Assistant 共用此列表
    'your_new_keyword',
]
```

> 新增後立即生效，不需重啟（Python 載入時讀取）。

---

## 2. 調整搜尋 threshold / top_k

RVT 的搜尋參數由 `ThresholdManager` 管理（不同於 Protocol 的 SmartSearchConfig）。

**查看設定位置**：
```bash
docker exec ai-django python manage.py shell -c "
from library.common.threshold_manager import ThresholdManager
tm = ThresholdManager()
print(tm.get_threshold('rvt_assistant', stage=1))
print(tm.get_threshold('rvt_assistant', stage=2))
"
```

若需修改，查找 `ThresholdManager` 中 `rvt_assistant` 的設定。

---

## 3. 新增/更新 RVT 文件到知識庫

### 方法 A：透過 Django Admin
開啟 `http://10.10.172.127/admin/api/rvtguide/`，新增/編輯文件。

### 方法 B：Django shell
```bash
docker exec ai-django python manage.py shell -c "
from api.models import RVTGuide
RVTGuide.objects.create(
    title='UCC 操作手冊',
    content='UCC (UART Control Center) 是...\n[IMG:14] board_count.png',
)
"
```

### 新增後產生向量（必要步驟）
```bash
docker exec ai-django python manage.py generate_rvt_embeddings
# 或
docker exec ai-django python manage.py generate_rvt_embeddings_1536
```

---

## 4. 新增圖片到文件（RVT 獨有功能）

### 上傳圖片
```bash
docker exec ai-django python manage.py shell -c "
from api.models import RVTGuide, ContentImage
rvt = RVTGuide.objects.get(title='UCC 操作手冊')
with open('/path/to/image.png', 'rb') as f:
    img_data = f.read()
img = ContentImage.objects.create(
    rvt_guide=rvt,
    filename='board_count.png',
    content_type_mime='image/png',
    file_size=len(img_data),
    image_data=img_data,
    display_order=1,
    is_primary=True,
)
print(f'Image ID: {img.id}')
"
```

### 在 content 中引用圖片
在 `RVTGuide.content` 中插入 `[IMG:{img.id}]`：
```
UART 板數量如下圖所示：[IMG:14] board_count.png
```

---

## 5. 切換 Dev / Prod Dify App

**修改檔案**: `docker-compose.yml`

```yaml
environment:
  - DIFY_ENV=development    # RVT_Guide_dev (app-xDXNUVPnPkP1We12RonI6Jk6)
  # - DIFY_ENV=production   # RVT_Guide (app-Lp4mlfIWHqMWPHTlzF9ywT4F)
```

切換後重啟：
```bash
docker compose restart ai-django ai-celery-worker
```

---

## 6. 測試 API

### 登入取得 session
```bash
curl -c /tmp/cookies.txt -X POST http://localhost/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "chunwei", "password": "YOUR_PASS"}'
```

### 測試聊天 API
```bash
CSRF=$(grep csrftoken /tmp/cookies.txt | awk '{print $7}')
curl -b /tmp/cookies.txt \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: $CSRF" \
  -X POST http://localhost/api/rvt-guide/chat/ \
  -d '{"message": "ucc 如何使用", "conversation_id": ""}'
```

### 直接測試 Dify Dev App
```bash
curl -X POST http://10.253.43.244/v1/chat-messages \
  -H "Authorization: Bearer app-xDXNUVPnPkP1We12RonI6Jk6" \
  -H "Content-Type: application/json" \
  -d '{"query": "ucc 如何使用", "inputs": {}, "response_mode": "blocking", "conversation_id": "", "user": "test"}'
```

### 測試外部知識庫 Callback
```bash
curl -X POST http://10.10.172.127/api/dify/knowledge/retrieval/ \
  -H "Content-Type: application/json" \
  -d '{
    "knowledge_id": "rvt_guide_db_dev",
    "query": "ucc 如何使用",
    "retrieval_setting": {"top_k": 3, "score_threshold": 0.8}
  }'
```

---

## 7. Dify 設定注意事項

### Reranking 必須關閉
- RVT_Guide_dev 和 RVT_Guide 都必須關閉 Reranking
- 開啟後 HTTP 400：`reranking_model_name Field required`
- 設定路徑：Dify → 工作台 → 選 App → 右上角設定 → Retrieval Setting → 關閉 Reranking

### 外部知識庫 URL
- 設定位置：Dify App → 上下文 → 外部知識庫 → 設定 URL
- 正確格式：`http://10.10.172.127/api/dify/knowledge/retrieval/`
- Dev app 的 knowledge_id 應設為 `rvt_guide_db_dev`
- Prod app 的 knowledge_id 應設為 `rvt_guide_db`

---

## 8. 常見問題排查

### 問題：顯示「建議您參考以下文件」

**步驟 1**：直接測試 Dify app
```bash
curl -X POST http://10.253.43.244/v1/chat-messages \
  -H "Authorization: Bearer app-xDXNUVPnPkP1We12RonI6Jk6" \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "inputs": {}, "response_mode": "blocking", "conversation_id": "", "user": "test"}'
```
- 若 HTTP 400 → 關閉 Reranking
- 若 timeout → 檢查外部 KB URL 中的 IP（應為 `10.10.172.127`）

**步驟 2**：查看 Django log
```bash
timeout 5 docker logs ai-django --tail 50 2>&1 | tail -30
```
找關鍵字：`ERROR`、`400`、`timeout`

### 問題：向量搜尋錯誤 `got an unexpected keyword argument 'stage'`

這是已知的非阻斷性錯誤。系統會自動回退到 `RVTGuideSearchService`（關鍵字搜尋）。
功能不受影響，可忽略或升級 `search_rvt_guide_with_vectors()` 函數簽名支援 `stage` 參數。

### 問題：Mode A/B 路由不正確

加 debug log 到 `SmartSearchRouter.route_search_strategy()`：
```python
logger.debug(f"[RVT Router] query={query[:50]}, mode={search_mode}")
```

### 問題：圖片不顯示

1. 確認 `ContentImage` 有資料：
   ```bash
   docker exec ai-django python manage.py shell -c "from api.models import ContentImage; print(ContentImage.objects.count())"
   ```
2. 確認 `[IMG:N]` ID 對應到正確的 ContentImage.id
3. 確認 `ContentImage.is_active = True`

---

## 9. 修改後驗證流程

1. 修改 Python 檔案（不需重啟，Django dev server 自動重載）
2. 或重啟 container：`docker compose restart ai-django`
3. 測試 Dify dev app 直接回應
4. 測試 web API 端點
5. 查看 log 確認無錯誤
