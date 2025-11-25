# Title Boost 功能快速參考指南

**目標讀者**: Protocol Assistant 開發者、測試人員  
**更新日期**: 2025-01-20  
**版本**: v1.2  

---

## 🎯 快速概覽

**Title Boost** 是一個搜尋增強功能，當用戶查詢的關鍵字出現在文檔標題中時，會給予該文檔額外的分數加成，從而提升其排名。

### 關鍵特性
- ✅ **非侵入式**: 不修改原始搜尋函數，使用裝飾器模式
- ✅ **版本驅動**: 透過資料庫配置啟用/停用
- ✅ **可調參數**: 支援不同階段的加分比例
- ✅ **向後相容**: v1.1 baseline 不受影響

---

## 📋 配置格式

### 資料庫配置 (DifyConfigVersion)
```json
{
  "retrieval_mode": "dify_two_stage_v1.2",
  "stage1": {
    "title_match_bonus": 0.15
  },
  "stage2": {
    "title_match_bonus": 0.10
  }
}
```

### 配置說明
| 欄位 | 類型 | 說明 | 範例值 |
|-----|------|------|--------|
| `retrieval_mode` | String | 檢索模式識別碼（包含 "v1.2" 或 "title_boost" 時啟用） | `"dify_two_stage_v1.2"` |
| `stage1.title_match_bonus` | Float | 第一階段匹配加分（0.0-1.0） | `0.15`（15%） |
| `stage2.title_match_bonus` | Float | 第二階段匹配加分（0.0-1.0） | `0.10`（10%） |

---

## 🔧 使用方式

### 1. 前端發送請求（包含版本碼）
```javascript
// frontend/src/hooks/useProtocolAssistantChat.js

const useProtocolAssistantChat = (
  inputMessage,
  setInputMessage,
  messages,
  setMessages,
  isLoading,
  selectedVersion = null  // ✅ 傳入版本物件
) => {
  const sendMessage = useCallback(async (message) => {
    const requestBody = {
      message: message,
      conversation_id: currentConversationId,
      // ✅ 包含版本碼
      ...(selectedVersion?.version_code && { 
        version_code: selectedVersion.version_code 
      })
    };
    
    await api.post('/api/protocol-guide/chat/', requestBody);
  }, [currentConversationId, selectedVersion]);
};

// 使用範例
useProtocolAssistantChat(
  inputMessage,
  setInputMessage,
  messages,
  setMessages,
  isLoading,
  { version_code: 'v1.2' }  // ✅ 指定 v1.2
);
```

### 2. 後端處理流程
```python
# library/dify_integration/protocol_chat_handler.py

def handle_chat_request(self, request, *args, **kwargs):
    query = request.data.get('message')
    version_code = request.data.get('version_code')  # ✅ 接收版本碼
    
    # 載入版本配置
    version_config = self._load_version_config(version_code) if version_code else None
    
    # 執行搜尋（帶版本配置）
    search_results = self._perform_backend_search(query, version_config)
    
    # 傳遞給 Dify
    response = self.dify_manager.send_chat_request(
        query=query,
        inputs={'context': search_results}
    )
```

### 3. 搜尋服務整合
```python
# library/protocol_guide/search_service.py

def search_knowledge(
    self,
    query,
    threshold=0.5,
    limit=5,
    use_vector=True,
    stage='stage1',
    version_config=None  # ✅ 接收版本配置
):
    # 解析 Title Boost 配置
    enable_title_boost = False
    if version_config and 'v1.2' in version_config.get('retrieval_mode', ''):
        enable_title_boost = True
        title_boost_config = TitleBoostConfig.from_rag_settings(
            version_config['rag_settings'], 
            stage=stage
        )
    
    # 使用增強版搜尋
    if enable_title_boost:
        results = search_with_vectors_generic_v2(
            query=query,
            limit=limit,
            threshold=threshold,
            model_class=self.model_class,
            source_table=self.source_table,
            enable_title_boost=True,
            title_boost_config=title_boost_config
        )
```

---

## 🧪 測試方法

### 整合測試
```bash
# 在 Docker 容器中執行測試
docker exec ai-django python /tmp/test_v1_2_integration.py
```

### 預期輸出
```
✅ 找到 3 個結果
    [1] UNH-IOL SOP 測試流程 (15.00%) 🌟 [Title Boost]
        原始分數: 0.00% → 加分後: 15.00% (+15.00%)
    [2] Google AVL SOP (0.00%) 
    [3] WHQL SOP (0.00%) 
    
✅ 1/3 個結果獲得 Title Boost 加分
```

### 手動測試查詢
```bash
# 測試查詢 1: IOL 相關
curl -X POST http://localhost/api/protocol-guide/chat/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_TOKEN" \
  -d '{
    "message": "IOL SOP",
    "version_code": "v1.2"
  }'

# 測試查詢 2: USB 測試
curl -X POST http://localhost/api/protocol-guide/chat/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_TOKEN" \
  -d '{
    "message": "UNH USB 測試",
    "version_code": "v1.2"
  }'

# 測試查詢 3: CrystalDiskMark
curl -X POST http://localhost/api/protocol-guide/chat/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_TOKEN" \
  -d '{
    "message": "CrystalDiskMark 完整流程",
    "version_code": "v1.2"
  }'
```

---

## 🐛 故障排除

### 問題 1: Title Boost 未啟用
**症狀**: 查詢結果沒有顯示 🌟 標記

**檢查清單**:
```bash
# 1. 確認版本配置存在
docker exec postgres_db psql -U postgres -d ai_platform -c "
SELECT version_code, version_name, rag_settings 
FROM dify_config_version 
WHERE version_code = 'v1.2';
"

# 2. 確認 retrieval_mode 包含 "v1.2"
# 應該看到: "retrieval_mode": "dify_two_stage_v1.2"

# 3. 檢查 Django 日誌
docker logs ai-django --tail 100 | grep "Title Boost"
# 預期看到: "✅ Title Boost 配置已載入"
```

---

### 問題 2: 參數錯誤
**症狀**: `TypeError: got an unexpected keyword argument`

**解決方案**:
```python
# ❌ 錯誤
results = search_with_vectors_generic_v2(
    top_k=limit,  # 參數名錯誤
)

# ✅ 正確
results = search_with_vectors_generic_v2(
    limit=limit,  # 參數名正確
    model_class=self.model_class,  # 必須傳遞
    source_table=self.source_table,  # 必須傳遞
)
```

---

### 問題 3: 版本配置未載入
**症狀**: 後端日誌顯示 "版本 v1.2 不存在"

**檢查步驟**:
```bash
# 1. 確認版本啟用狀態
docker exec postgres_db psql -U postgres -d ai_platform -c "
SELECT version_code, version_name, is_active 
FROM dify_config_version;
"

# 2. 啟用版本（如果 is_active = false）
docker exec postgres_db psql -U postgres -d ai_platform -c "
UPDATE dify_config_version 
SET is_active = true 
WHERE version_code = 'v1.2';
"
```

---

## 📊 效能指標

### Title Boost 開銷
| 項目 | 時間 | 影響 |
|-----|------|------|
| 關鍵字匹配 | < 5ms | 可忽略 |
| 分數計算 | < 5ms | 可忽略 |
| 配置載入 | ~20ms | 可快取 |
| **總額外開銷** | **< 30ms** | **< 5% 影響** |

### 優化建議
```python
# 使用 Django cache 快取版本配置
from django.core.cache import cache

def _load_version_config(self, version_code):
    cache_key = f'dify_config:{version_code}'
    config = cache.get(cache_key)
    if not config:
        config = DifyConfigVersion.objects.get(...)
        cache.set(cache_key, config, timeout=300)  # 5 分鐘
    return config
```

---

## 🎓 最佳實踐

### DO's ✅
- ✅ 使用可選參數保持向後相容
- ✅ 在日誌中記錄 Title Boost 啟用狀態
- ✅ 編寫整合測試驗證端到端流程
- ✅ 在版本配置中使用語義化命名（如 "v1.2"）

### DON'Ts ❌
- ❌ 不要修改原始搜尋函數（使用包裝器）
- ❌ 不要假設版本配置總是存在（檢查 None）
- ❌ 不要在生產環境直接修改 baseline 版本
- ❌ 不要忘記在 useCallback 依賴中加入 selectedVersion

---

## 🔗 相關資源

### 文檔
- [完整整合報告](/docs/features/title-boost-v1.2-integration-report.md)
- [Title Boost 架構文檔](/docs/architecture/title-boost-architecture.md)
- [向量搜尋指南](/docs/vector-search/ai-vector-search-guide.md)

### 代碼檔案
- `/library/protocol_guide/search_service.py` - 搜尋服務
- `/library/dify_integration/protocol_chat_handler.py` - Chat Handler
- `/library/knowledge_base/title_boost/` - Title Boost 模組
- `/frontend/src/hooks/useProtocolAssistantChat.js` - 前端 Hook

### 測試檔案
- `/tests/test_search/test_v1_2_integration.py` - 整合測試
- `/backend/test_title_boost.py` - 單元測試

---

## 💡 常見問題 (FAQ)

### Q1: 如何切換回 v1.1？
**A**: 前端不傳 `version_code` 參數，或傳 `version_code: 'v1.1'`

### Q2: 可以自訂加分比例嗎？
**A**: 可以！修改資料庫中的 `rag_settings`：
```sql
UPDATE dify_config_version 
SET rag_settings = jsonb_set(
  rag_settings, 
  '{stage1,title_match_bonus}', 
  '0.20'  -- 改為 20%
)
WHERE version_code = 'v1.2';
```

### Q3: Title Boost 是否影響原始向量搜尋？
**A**: 不會！Title Boost 只是在向量搜尋**之後**增加額外分數，不修改原始搜尋邏輯。

### Q4: 如何知道哪些結果獲得了 Title Boost？
**A**: 查看搜尋結果的 `title_boost_applied` 欄位，或在日誌中查找 "🌟 [Title Boost]" 標記。

---

**最後更新**: 2025-01-20  
**維護者**: AI Platform Team  
**問題回報**: [GitHub Issues]  

---
