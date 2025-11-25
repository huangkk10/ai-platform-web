# Dify v1.2.1 API 快速測試指南

**目的**: 在不需要前端 UI 的情況下，快速驗證 Baseline API 和動態配置功能

**測試環境**: 使用 `curl` 命令行工具

---

## 🎯 測試前準備

### 1. 獲取 API Token
```bash
# 方法 1：使用 Django shell
docker exec -it ai-django python manage.py shell

# 在 shell 中執行
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
user = User.objects.get(username='your_username')
token, created = Token.objects.get_or_create(user=user)
print(f"Token: {token.key}")
```

### 2. 設定環境變數
```bash
# 將 Token 儲存為環境變數
export API_TOKEN="your_token_here"
export API_BASE="http://localhost"  # 或 http://10.10.172.127
```

---

## 📡 API 測試

### 測試 1: 獲取所有版本

**目的**: 查看所有可用的 Dify 配置版本

```bash
curl -X GET "${API_BASE}/api/dify-benchmark/versions/" \
  -H "Authorization: Token ${API_TOKEN}" \
  -H "Content-Type: application/json" \
  | jq .
```

**預期回應**:
```json
[
  {
    "id": 1,
    "version_name": "Dify 二階搜尋 v1.1",
    "version_code": "dify-two-tier-v1.1",
    "is_baseline": false,
    "is_active": true
  },
  {
    "id": 2,
    "version_name": "Dify 二階搜尋 v1.2 (Title Boost)",
    "version_code": "dify-two-tier-v1.2",
    "is_baseline": false,
    "is_active": true
  },
  {
    "id": 3,
    "version_name": "Dify 二階搜尋 v1.2.1 (Dynamic Threshold + Title Boost)",
    "version_code": "dify-two-tier-v1.2.1",
    "is_baseline": true,  // ← 當前 Baseline
    "is_active": true,
    "rag_settings": {
      "stage1": {
        "use_dynamic_threshold": true  // ← 動態版本
      }
    }
  }
]
```

---

### 測試 2: 獲取當前 Baseline 版本

**目的**: 查詢當前作為 Baseline 的版本

```bash
curl -X GET "${API_BASE}/api/dify-benchmark/versions/get_baseline/" \
  -H "Authorization: Token ${API_TOKEN}" \
  -H "Content-Type: application/json" \
  | jq .
```

**預期回應**:
```json
{
  "success": true,
  "version_id": 3,
  "version_name": "Dify 二階搜尋 v1.2.1 (Dynamic Threshold + Title Boost)",
  "version_code": "dify-two-tier-v1.2.1",
  "is_dynamic": true,
  "rag_settings": {
    "assistant_type": "protocol_assistant",
    "stage1": {
      "threshold": 0.80,          // ← 從 DB 動態載入
      "title_weight": 95,         // ← 從 DB 動態載入
      "content_weight": 5,        // ← 從 DB 動態載入
      "title_match_bonus": 15,    // ← 版本固定
      "top_k": 20,                // ← 版本固定
      "loaded_from_db": true,
      "use_dynamic_threshold": true
    },
    "stage2": {
      "threshold": 0.80,
      "title_weight": 10,
      "content_weight": 90,
      "title_match_bonus": 10,
      "top_k": 10,
      "loaded_from_db": true,
      "use_dynamic_threshold": true
    }
  }
}
```

**關鍵驗證點**:
- ✅ `is_dynamic: true` - 確認為動態版本
- ✅ `loaded_from_db: true` - 確認從資料庫載入
- ✅ `threshold` 和 `weights` 來自 DB
- ✅ `title_match_bonus` 和 `top_k` 保留版本定義

---

### 測試 3: 設定 Baseline 版本

**目的**: 將指定版本設為新的 Baseline

```bash
# 設定 v1.2.1 (ID=3) 為 Baseline
curl -X POST "${API_BASE}/api/dify-benchmark/versions/3/set_baseline/" \
  -H "Authorization: Token ${API_TOKEN}" \
  -H "Content-Type: application/json" \
  | jq .
```

**預期回應**:
```json
{
  "success": true,
  "message": "版本 Dify 二階搜尋 v1.2.1 (Dynamic Threshold + Title Boost) 已設定為 Baseline",
  "version_id": 3,
  "version_name": "Dify 二階搜尋 v1.2.1 (Dynamic Threshold + Title Boost)",
  "is_dynamic": true,
  "timestamp": "2025-11-26T03:00:00Z"
}
```

**測試切換回 v1.1**:
```bash
# 設定 v1.1 (ID=1) 為 Baseline
curl -X POST "${API_BASE}/api/dify-benchmark/versions/1/set_baseline/" \
  -H "Authorization: Token ${API_TOKEN}" \
  -H "Content-Type: application/json" \
  | jq .
```

**預期回應**:
```json
{
  "success": true,
  "message": "版本 Dify 二階搜尋 v1.1 已設定為 Baseline",
  "version_id": 1,
  "version_name": "Dify 二階搜尋 v1.1",
  "is_dynamic": false,  // ← 靜態版本
  "timestamp": "2025-11-26T03:00:00Z"
}
```

---

### 測試 4: 調整 Threshold 設定（Web UI 模擬）

**目的**: 驗證動態配置變更

**步驟 1**: 使用 Django shell 修改 Threshold
```bash
docker exec -it ai-django python manage.py shell
```

```python
from api.models import SearchThresholdSetting
from decimal import Decimal

# 獲取 Protocol Assistant 設定
setting = SearchThresholdSetting.objects.get(assistant_type='protocol_assistant')

# 修改第一階段 Threshold
print(f"原始 Stage 1 Threshold: {setting.stage1_threshold}")
setting.stage1_threshold = Decimal('0.85')
setting.stage1_title_weight = 90
setting.stage1_content_weight = 10
setting.save()

print(f"新 Stage 1 Threshold: {setting.stage1_threshold}")
print(f"新 Title/Content 權重: {setting.stage1_title_weight}/{setting.stage1_content_weight}")
```

**步驟 2**: 清除快取並重新獲取 Baseline
```bash
# 重新獲取 Baseline（會從 DB 讀取最新配置）
curl -X GET "${API_BASE}/api/dify-benchmark/versions/get_baseline/" \
  -H "Authorization: Token ${API_TOKEN}" \
  -H "Content-Type: application/json" \
  | jq '.rag_settings.stage1'
```

**預期回應** (動態載入最新值):
```json
{
  "threshold": 0.85,           // ← 已更新！
  "title_weight": 90,          // ← 已更新！
  "content_weight": 10,        // ← 已更新！
  "title_match_bonus": 15,     // ← 保持不變（版本固定）
  "top_k": 20,
  "loaded_from_db": true,
  "use_dynamic_threshold": true
}
```

---

### 測試 5: 執行批量測試（VSA）

**目的**: 使用最新的動態配置執行測試

**創建測試案例** (如果沒有):
```bash
docker exec -it ai-django python manage.py shell
```

```python
from api.models import DifyTestCase

# 創建測試案例
test_case = DifyTestCase.objects.create(
    question="ULINK 是什麼？",
    expected_answer_keywords=["ULINK", "協議", "測試"],
    category="protocol",
    difficulty="easy"
)
print(f"創建測試案例 ID: {test_case.id}")
```

**執行批量測試**:
```bash
curl -X POST "${API_BASE}/api/dify-benchmark/versions/batch_test/" \
  -H "Authorization: Token ${API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "batch_id": "dynamic_test_001",
    "version_ids": [3],
    "test_case_ids": [1, 2, 3]
  }' \
  | jq .
```

**預期回應**:
```json
{
  "success": true,
  "batch_id": "dynamic_test_001",
  "total_tests": 3,
  "results": [
    {
      "test_case_id": 1,
      "version_id": 3,
      "passed": true,
      "evaluation_details": {
        "config_source": "dynamic",  // ← 使用動態配置
        "actual_config": {
          "stage1": {
            "threshold": 0.85,       // ← 實際使用的值
            "title_weight": 90,
            "content_weight": 10,
            "title_match_bonus": 15
          }
        }
      }
    }
  ]
}
```

---

### 測試 6: 查詢測試結果

**目的**: 驗證測試結果記錄了實際配置

```bash
# 獲取測試結果詳情
curl -X GET "${API_BASE}/api/dify-benchmark/results/?batch_id=dynamic_test_001" \
  -H "Authorization: Token ${API_TOKEN}" \
  -H "Content-Type: application/json" \
  | jq '.results[0].evaluation_details'
```

**預期回應**:
```json
{
  "config_source": "dynamic",
  "actual_config": {
    "stage1": {
      "threshold": 0.85,
      "title_weight": 90,
      "content_weight": 10,
      "title_match_bonus": 15,
      "top_k": 20
    },
    "stage2": {
      "threshold": 0.80,
      "title_weight": 10,
      "content_weight": 90,
      "title_match_bonus": 10,
      "top_k": 10
    }
  },
  "match_details": {
    // ... 其他詳情
  }
}
```

**關鍵驗證**:
- ✅ `config_source: "dynamic"` - 使用動態配置
- ✅ `actual_config` 記錄了實際使用的 threshold 和 weights
- ✅ 配置與 DB 中的最新值一致

---

## 🔍 驗證檢查清單

執行完以上測試後，確認：

- [ ] ✅ v1.2.1 版本存在且配置正確
- [ ] ✅ 可以獲取當前 Baseline
- [ ] ✅ 可以切換 Baseline（v1.1 ↔ v1.2.1）
- [ ] ✅ 動態版本顯示 `is_dynamic: true`
- [ ] ✅ 動態配置從 DB 載入（`loaded_from_db: true`）
- [ ] ✅ 調整 Threshold 後重新獲取 Baseline，看到最新值
- [ ] ✅ 執行批量測試，`evaluation_details` 記錄 `config_source: "dynamic"`
- [ ] ✅ 測試結果的 `actual_config` 與 DB 一致

---

## 🐛 故障排除

### 問題 1: 401 Unauthorized
**原因**: Token 無效或過期  
**解決**: 重新獲取 Token

### 問題 2: 找不到 Baseline
**回應**: `{"success": false, "error": "沒有設定 Baseline 版本"}`  
**解決**: 執行測試 3 設定 Baseline

### 問題 3: 動態配置沒有更新
**原因**: 快取未清除  
**解決**: 
```bash
docker exec -it ai-django python manage.py shell
```
```python
from library.common.threshold_manager import get_threshold_manager
manager = get_threshold_manager()
manager.clear_cache()
```

### 問題 4: `loaded_from_db: false`
**原因**: DB 中沒有 Protocol Assistant 的 Threshold 設定  
**解決**: 
```python
from api.models import SearchThresholdSetting
from decimal import Decimal

SearchThresholdSetting.objects.create(
    assistant_type='protocol_assistant',
    stage1_threshold=Decimal('0.80'),
    stage1_title_weight=95,
    stage1_content_weight=5,
    stage2_threshold=Decimal('0.80'),
    stage2_title_weight=10,
    stage2_content_weight=90
)
```

---

## 🎯 完整測試流程

```bash
# 1. 設定環境變數
export API_TOKEN="your_token"
export API_BASE="http://localhost"

# 2. 獲取所有版本
curl -X GET "${API_BASE}/api/dify-benchmark/versions/" \
  -H "Authorization: Token ${API_TOKEN}" | jq .

# 3. 獲取當前 Baseline
curl -X GET "${API_BASE}/api/dify-benchmark/versions/get_baseline/" \
  -H "Authorization: Token ${API_TOKEN}" | jq .

# 4. 設定 v1.2.1 為 Baseline
curl -X POST "${API_BASE}/api/dify-benchmark/versions/3/set_baseline/" \
  -H "Authorization: Token ${API_TOKEN}" | jq .

# 5. 調整 Threshold（Django shell）
docker exec -it ai-django python manage.py shell
# ... 修改設定

# 6. 重新獲取 Baseline（應該看到新值）
curl -X GET "${API_BASE}/api/dify-benchmark/versions/get_baseline/" \
  -H "Authorization: Token ${API_TOKEN}" | jq '.rag_settings.stage1'

# 7. 執行批量測試
curl -X POST "${API_BASE}/api/dify-benchmark/versions/batch_test/" \
  -H "Authorization: Token ${API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"batch_id":"test_001","version_ids":[3],"test_case_ids":[1,2,3]}' \
  | jq .

# 8. 查詢測試結果
curl -X GET "${API_BASE}/api/dify-benchmark/results/?batch_id=test_001" \
  -H "Authorization: Token ${API_TOKEN}" \
  | jq '.results[0].evaluation_details'
```

---

## 📊 預期測試時長

- **測試 1-3** (Baseline API): 約 10-30 秒
- **測試 4** (調整 Threshold): 約 1-2 分鐘
- **測試 5-6** (批量測試): 約 2-5 分鐘（視測試案例數量）

**總計**: 約 5-10 分鐘

---

## ✅ 成功指標

所有測試通過後，您應該能夠：
- ✅ 使用 API 切換 Baseline 版本
- ✅ 在 Web UI 調整 Threshold，API 獲取最新值
- ✅ 執行測試時使用動態配置
- ✅ 測試結果記錄實際使用的配置

**🎉 如果以上都正常，代表動態 Threshold 功能後端已完全就緒！**

---

**文檔更新日期**: 2025-11-26  
**版本**: v1.0  
**作者**: AI Platform Team
