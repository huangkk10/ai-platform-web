# RVT Assistant 二段搜尋快速參考

## 🚀 快速開始

### 測試命令
```bash
# 執行完整測試
docker exec ai-django python /app/test_rvt_two_tier_mechanism.py

# 即時監控日誌
docker logs ai-django --follow | grep "RVT"
```

---

## 📊 搜尋模式速查

### 模式 A：關鍵字觸發全文搜尋
**觸發條件**：查詢包含全文關鍵字  
**關鍵字清單**：「完整內容」、「全部內容」、「所有內容」、「完整」、「全部」、「所有」

**流程**：
```
用戶查詢（含關鍵字） 
  → SmartSearchRouter 檢測到關鍵字
    → KeywordTriggeredSearchHandler
      → 直接發送原查詢給 Dify
        → 返回全文搜尋結果
```

**範例查詢**：
- ✅ "請提供 RVT 測試的完整內容"
- ✅ "RVT 的全部資訊是什麼？"
- ✅ "給我所有 RVT 相關資料"

**API 回應**：
```json
{
  "mode": "mode_a",
  "stage": null,
  "is_fallback": false
}
```

---

### 模式 B：標準兩階段搜尋
**觸發條件**：查詢不包含全文關鍵字（預設模式）

**流程**：
```
用戶查詢（無關鍵字）
  → SmartSearchRouter 路由到模式 B
    → TwoTierSearchHandler
      
      階段 1：段落級搜尋
      ├─→ 發送原查詢給 Dify
      ├─→ 檢測 AI 回答是否不確定
      │   ├─→ 確定 ✅ → 返回結果（結束）
      │   └─→ 不確定 ⚠️ → 進入階段 2
      
      階段 2：全文級搜尋
      ├─→ 發送「原查詢 + 完整內容」給 Dify
      ├─→ 檢測 AI 回答是否不確定
      │   ├─→ 確定 ✅ → 返回結果（結束）
      │   └─→ 不確定 ⚠️ → 降級模式
      
      降級模式：
      └─→ 組合 AI 原始回答 + 友善提示 + 引用來源
```

**範例查詢**：
- ✅ "RVT 測試流程的第一步是什麼？" → Stage 1 成功
- ✅ "RVT 有什麼注意事項？" → Stage 1 成功
- ⚠️ "天氣如何？" → Stage 1 → Stage 2 → Fallback

**API 回應（Stage 1 成功）**：
```json
{
  "mode": "mode_b",
  "stage": 1,
  "is_fallback": false
}
```

**API 回應（Stage 2 成功）**：
```json
{
  "mode": "mode_b",
  "stage": 2,
  "is_fallback": false
}
```

**API 回應（降級模式）**：
```json
{
  "mode": "mode_b",
  "stage": 2,
  "is_fallback": true,
  "fallback_reason": "階段 2 AI 回答不確定 (含: 抱歉)"
}
```

---

## 🔍 不確定性檢測關鍵字

**觸發降級的關鍵字**（由 `is_uncertain_response()` 檢測）：
- ❌ "不確定"
- ❌ "無法"
- ❌ "不清楚"
- ❌ "抱歉"
- ❌ "不知道"
- ❌ "沒有"
- ❌ "找不到"

**範例**：
```
AI 回答: "抱歉，我無法提供天氣資訊。"
檢測結果: 不確定 (含關鍵字: 抱歉)
動作: 進入下一階段或降級
```

---

## 📋 日誌格式速查

### 智能路由日誌
```
🔍 RVT 智能路由: 用戶查詢='...'
   檢測全文關鍵字: True/False (含: 關鍵字)
   路由決策: mode_a / mode_b
```

### 模式 A 日誌
```
🔍 RVT 模式 A: 關鍵字優先全文搜尋
   查詢: ...
   ✅ RVT 模式 A 完成
   響應時間: X.XX 秒
```

### 模式 B 日誌
```
🔄 RVT 模式 B: 兩階段搜尋（方案 B）
   查詢: ...
   階段 1: 發送原查詢給 Dify（段落級搜尋）...
   ✅ 階段 1 回答確定  或
   ⚠️ 階段 1 回答不確定 (含關鍵字: XXX)
   🔄 進入階段 2: 發送「原查詢 + 完整內容」給 Dify（全文級搜尋）...
   📝 Stage 2 查詢重寫: 原查詢 → 原查詢 完整內容
   ✅ 階段 2 回答確定  或
   ⚠️ 階段 2 回答不確定 (含關鍵字: XXX)
   🔄 進入降級模式：組合 AI 原始回答 + 友善提示（保持透明度）
```

---

## 🛠️ 故障排查

### 問題 1：路由決策錯誤
**症狀**：應該觸發模式 A 但進入了模式 B

**檢查步驟**：
1. 查看日誌中的「檢測全文關鍵字」訊息
2. 確認查詢是否包含關鍵字清單中的詞彙
3. 檢查 `library/common/query_analysis/keyword_detector.py`

**解決方案**：
```bash
# 檢查關鍵字列表
docker exec ai-django python -c "
from library.common.query_analysis import contains_full_document_keywords
result = contains_full_document_keywords('請提供完整內容')
print(result)
"
```

### 問題 2：不確定性檢測失誤
**症狀**：AI 給出確定回答但系統仍進入 Stage 2

**檢查步驟**：
1. 查看日誌中的「不確定檢測」訊息
2. 確認 AI 回答是否包含不確定關鍵字
3. 檢查 `library/common/ai_response/uncertainty_detector.py`

**解決方案**：
```bash
# 測試不確定性檢測
docker exec ai-django python -c "
from library.common.ai_response import is_uncertain_response
result = is_uncertain_response('抱歉，我無法回答這個問題。')
print(f'不確定: {result[0]}, 關鍵字: {result[1]}')
"
```

### 問題 3：Dify 請求失敗
**症狀**：搜尋過程中出現錯誤

**檢查步驟**：
1. 查看錯誤日誌：`docker logs ai-django | grep "ERROR"`
2. 確認 Dify 配置是否正確
3. 測試 Dify 連接

**解決方案**：
```bash
# 驗證 RVT Guide 配置
docker exec ai-django python -c "
from library.config.dify_config_manager import get_rvt_guide_config
config = get_rvt_guide_config()
print(f'API URL: {config.api_url}')
print(f'API Key: {config.api_key[:10]}...')
print(f'Timeout: {config.timeout}')
"

# 測試 Dify 連接
docker exec ai-django python -c "
from library.dify_integration.chat_client import DifyChatClient
from library.config.dify_config_manager import get_rvt_guide_config
config = get_rvt_guide_config()
client = DifyChatClient(config.api_url, config.api_key, config.base_url)
response = client.chat('測試', user='test_user')
print(f'連接成功: {response.get(\"answer\")[:50]}...')
"
```

---

## 📊 監控指令

### 統計模式使用率
```bash
# 模式 A 使用次數
docker logs ai-django | grep "RVT 智能路由" | grep "mode_a" | wc -l

# 模式 B 使用次數
docker logs ai-django | grep "RVT 智能路由" | grep "mode_b" | wc -l

# Stage 1 成功率
total=$(docker logs ai-django | grep "階段 1:" | wc -l)
success=$(docker logs ai-django | grep "階段 1 回答確定" | wc -l)
echo "Stage 1 成功率: $success / $total"

# 降級率
total=$(docker logs ai-django | grep "RVT 模式 B" | wc -l)
fallback=$(docker logs ai-django | grep "進入降級模式" | wc -l)
echo "降級率: $fallback / $total"
```

### 效能監控
```bash
# 平均響應時間（需要進一步處理）
docker logs ai-django | grep "響應時間:" | grep "RVT" | tail -10

# 今日搜尋次數
docker logs ai-django --since $(date +%Y-%m-%d) | grep "RVT Guide Chat Request" | wc -l
```

---

## 🔗 相關檔案路徑

### 核心實作
```
library/rvt_guide/
├── smart_search_router.py          # 智能路由器
├── two_tier_handler.py             # 兩階段處理器
├── keyword_triggered_handler.py    # 關鍵字處理器
└── api_handlers.py                 # API 整合

library/common/
├── query_analysis/
│   └── keyword_detector.py         # 關鍵字檢測
└── ai_response/
    └── uncertainty_detector.py     # 不確定性檢測

library/dify_integration/
└── chat_client.py                  # Dify 客戶端

library/config/
└── dify_config_manager.py          # 配置管理
```

### 測試檔案
```
backend/test_rvt_two_tier_mechanism.py    # RVT 測試腳本
backend/test_two_tier_mechanism.py        # Protocol 測試腳本（參考）
```

### 文檔
```
docs/features/
└── rvt-assistant-two-tier-search-implementation.md  # 完整實作報告
```

---

## 🎯 API 使用範例

### cURL 測試
```bash
# 測試模式 A（關鍵字觸發）
curl -X POST http://localhost/api/rvt-guide/chat/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_TOKEN" \
  -d '{
    "message": "請提供 RVT 測試的完整內容",
    "conversation_id": ""
  }'

# 測試模式 B（標準查詢）
curl -X POST http://localhost/api/rvt-guide/chat/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_TOKEN" \
  -d '{
    "message": "RVT 測試流程的第一步是什麼？",
    "conversation_id": ""
  }'

# 測試降級模式（不相關問題）
curl -X POST http://localhost/api/rvt-guide/chat/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_TOKEN" \
  -d '{
    "message": "天氣如何？",
    "conversation_id": ""
  }'
```

### Python 測試
```python
import requests

# API 端點
url = "http://localhost/api/rvt-guide/chat/"

# 請求標頭
headers = {
    "Content-Type": "application/json",
    "Authorization": "Token YOUR_TOKEN"
}

# 測試案例 1：模式 A
payload1 = {
    "message": "請提供 RVT 測試的完整內容",
    "conversation_id": ""
}
response1 = requests.post(url, json=payload1, headers=headers)
print(f"模式: {response1.json().get('mode')}")

# 測試案例 2：模式 B
payload2 = {
    "message": "RVT 測試流程的第一步是什麼？",
    "conversation_id": ""
}
response2 = requests.post(url, json=payload2, headers=headers)
print(f"模式: {response2.json().get('mode')}")
print(f"階段: {response2.json().get('stage')}")
```

---

## 📞 支援資訊

### 問題回報
- **日誌路徑**：`docker logs ai-django`
- **測試腳本**：`/app/test_rvt_two_tier_mechanism.py`
- **配置檔案**：`library/config/dify_config_manager.py`

### 聯絡方式
- **團隊**：AI Platform Team
- **更新日期**：2025-11-11
- **版本**：v1.0

---

**💡 提示**：此功能與 Protocol Assistant 的二段搜尋機制完全一致，可參考 Protocol 的使用經驗。
