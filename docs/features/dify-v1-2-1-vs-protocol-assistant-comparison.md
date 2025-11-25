# Dify v1.2.1 (Dynamic Threshold) vs Protocol Assistant Chat 功能對比

## 📋 概述

本文檔詳細說明 **Dify 二階搜尋 v1.2.1（Dynamic Threshold + Title Boost）** 與 **原本 Protocol Assistant Chat 功能** 的差異。

**核心區別**：
- **Dify v1.2.1**：用於 **Benchmark 測試**（VSA 配置版本管理）
- **Protocol Assistant Chat**：用於 **實際對話功能**（前端聊天介面）

---

## 🎯 使用場景對比

### Scenario 1: 使用 Dify v1.2.1（Benchmark 測試）

**觸發時機**：在 **VSA 配置版本管理** 頁面執行批量測試

**流程**：
```
1. 管理員進入：/dify-benchmark/versions
2. 選擇 v1.2.1 版本
3. 點擊 "批量測試" 或 "測試" 按鈕
4. 系統讀取版本配置中的 rag_settings
5. 如果 use_dynamic_threshold=true：
   → 從資料庫（search_threshold_settings）讀取最新配置
   → 覆蓋 threshold, title_weight, content_weight
6. 使用 ProtocolGuideSearchService 執行搜尋
7. 將搜尋結果格式化為 Context
8. 發送到 Dify API 生成回應
9. 記錄測試結果（包含 actual_config）
```

**API 端點**：
```
POST /api/dify-batch-tests/run_batch_test/
```

**配置來源**：
- **Threshold/Weights**: 從 `search_threshold_settings` 表讀取（動態）
- **Title Boost**: 從 `rag_settings.stage1/stage2.title_match_bonus` 讀取（版本固定）
- **Top K**: 從 `rag_settings.stage1/stage2.top_k` 讀取（版本固定）

**Dify 配置**：
```json
{
  "app_id": "app-MgZZOhADkEmdUrj2DtQLJ23G",
  "api_url": "http://10.10.172.37/v1/chat-messages",
  "response_mode": "blocking"
}
```

---

### Scenario 2: 使用 Protocol Assistant Chat（前端聊天）

**觸發時機**：在 **Protocol Assistant** 聊天介面發送訊息

**流程**：
```
1. 用戶進入：/protocol-assistant
2. 在聊天框輸入問題並發送
3. 前端調用 POST /api/protocol-guides/chat/
4. 後端 ProtocolGuideViewSet.chat() 處理請求
5. 調用 ProtocolGuideAPIHandler.handle_chat_api()
6. 使用 ProtocolChatHandler 處理聊天
7. 讀取 Dify Protocol Known Issue 配置（固定配置）
8. 使用 ProtocolGuideSearchService 執行搜尋（無動態配置）
9. 將搜尋結果格式化為 Context
10. 發送到 Dify API 生成回應
11. 返回給前端顯示
```

**API 端點**：
```
POST /api/protocol-guides/chat/
```

**配置來源**：
- **Threshold/Weights**: 從 `ProtocolGuideSearchService` 的預設值（硬編碼）
- **Title Boost**: 無（或使用 search_service 內建邏輯）
- **Top K**: 從搜尋服務預設值

**Dify 配置**：
```python
# 從 library/config/dify_config_manager.py
{
  "app_name": "Protocol Known Issue System",
  "api_key": "app-xxxxxxxxxxxxx",  # 與 v1.2.1 可能不同
  "api_url": "http://10.10.172.37/v1/chat-messages",
  "response_mode": "blocking"
}
```

---

## 🔧 技術架構對比

### 1️⃣ Dify v1.2.1（Benchmark 測試）

#### 代碼路徑
```
frontend/src/pages/dify-benchmark/DifyVersionManagementPage.js
  → POST /api/dify-batch-tests/run_batch_test/
    → backend/api/views/viewsets/dify_benchmark_viewsets.py
      → DifyBatchTestViewSet.run_batch_test()
        → library/dify_integration/dynamic_threshold_loader.py
          → DynamicThresholdLoader.load_full_rag_settings()  # 🔄 動態載入
            → api/models.py: SearchThresholdSetting  # 讀取 DB
        → library/dify_benchmark/dify_api_client.py
          → DifyAPIClient._perform_backend_search()
            → library/protocol_guide/search_service.py
              → ProtocolGuideSearchService.search_knowledge(version_config=...)
                ✅ stage=1: threshold=85%, title_weight=90%, content_weight=10%
                ✅ stage=2: threshold=80%, title_weight=10%, content_weight=90%
                ✅ Title Boost: 15%/10%（版本固定）
          → requests.post(dify_api_url, context=搜尋結果)
```

#### 關鍵類別
- **DynamicThresholdLoader**: 動態配置載入器
  - `load_stage_config()`: 載入單階段配置
  - `load_full_rag_settings()`: 載入完整 RAG 配置
  - 優先順序：DB > 版本預設 > 程式碼預設

- **DifyAPIClient**: Dify API 客戶端
  - `_perform_backend_search()`: 執行後端搜尋
  - 整合 ProtocolGuideSearchService
  - 格式化搜尋結果為 Context

#### 配置結構
```json
{
  "assistant_type": "protocol_assistant",
  "stage1": {
    "use_dynamic_threshold": true,  // 🔄 啟用動態載入
    "assistant_type": "protocol_assistant",
    "threshold": 0.80,               // 預設值（DB 優先）
    "title_weight": 95,              // 預設值（DB 優先）
    "content_weight": 5,             // 預設值（DB 優先）
    "title_match_bonus": 15,         // 📌 版本固定（不從 DB）
    "min_keyword_length": 2,
    "top_k": 20
  },
  "stage2": {
    "use_dynamic_threshold": true,
    "threshold": 0.80,
    "title_weight": 10,
    "content_weight": 90,
    "title_match_bonus": 10,         // 📌 版本固定
    "top_k": 10
  },
  "retrieval_mode": "two_stage_with_title_boost",
  "use_backend_search": true,
  "search_service": "ProtocolGuideSearchService"
}
```

---

### 2️⃣ Protocol Assistant Chat（前端聊天）

#### 代碼路徑
```
frontend/src/pages/ProtocolAssistantChatPage.js
  → POST /api/protocol-guides/chat/
    → backend/api/views/viewsets/protocol_assistant_viewset.py
      → ProtocolGuideViewSet.chat()
        → library/protocol_guide/api_handlers.py
          → ProtocolGuideAPIHandler.handle_chat_api()
            → library/dify_integration/protocol_chat_handler.py
              → ProtocolChatHandler.handle_chat_request()
                → library/config/dify_config_manager.py
                  → get_protocol_known_issue_config()  # 固定配置
                → library/protocol_guide/search_service.py
                  → ProtocolGuideSearchService.search_knowledge()
                    ✅ 使用預設參數（硬編碼）
                    ❌ 無動態載入
                    ❌ 無 Title Boost（或預設值）
                → requests.post(dify_api_url, context=搜尋結果)
```

#### 關鍵類別
- **ProtocolChatHandler**: Protocol 聊天處理器
  - `handle_chat_request()`: 處理聊天請求
  - `_perform_backend_search()`: 執行後端搜尋
  - 支援 `version_config` 參數（但前端未傳遞）

- **ProtocolGuideSearchService**: 搜尋服務
  - `search_knowledge()`: 智能搜尋（向量+關鍵字）
  - 預設參數：從類別屬性或方法參數

#### 配置結構
```python
# 硬編碼在 search_service.py 或從參數傳入
{
  "threshold": 0.7,           # 方法參數預設值
  "limit": 5,                 # 方法參數預設值
  "use_vector": True,
  # ❌ 無 title_weight, content_weight 配置
  # ❌ 無 title_match_bonus 配置
  # ❌ 無 use_dynamic_threshold 標記
}
```

---

## 📊 功能對比表

| 功能項目 | Dify v1.2.1 (Benchmark) | Protocol Assistant Chat |
|---------|------------------------|------------------------|
| **使用場景** | VSA 配置版本測試 | 前端聊天對話 |
| **API 端點** | `/api/dify-batch-tests/run_batch_test/` | `/api/protocol-guides/chat/` |
| **動態配置** | ✅ 從 DB 讀取 `search_threshold_settings` | ❌ 無動態配置 |
| **配置來源** | DB > 版本預設 > 程式碼預設 | 硬編碼或方法參數 |
| **Title Boost** | ✅ 15%/10%（版本固定） | ❌ 無或預設 |
| **Threshold** | 🔄 動態（可調整） | 📌 固定 0.7 |
| **Title Weight** | 🔄 動態（可調整） | ❌ 無明確配置 |
| **Content Weight** | 🔄 動態（可調整） | ❌ 無明確配置 |
| **Top K** | 📌 20/10（版本固定） | 📌 5（參數固定） |
| **二階搜尋** | ✅ 支援（stage1 + stage2） | ❓ 取決於實作 |
| **配置記錄** | ✅ 記錄 `actual_config` | ❌ 無記錄 |
| **版本切換** | ✅ 可切換 Baseline | ❌ 使用固定配置 |
| **參數調整** | ✅ Web UI 即時調整 | ❌ 需修改程式碼 |
| **A/B 測試** | ✅ 支援快速對比 | ❌ 不支援 |
| **Dify App** | `app-MgZZOhADkEmdUrj2DtQLJ23G` | Protocol Known Issue System |
| **響應模式** | Blocking（同步） | Blocking（同步） |

---

## 🔍 關鍵差異總結

### 1. **配置靈活性**

**Dify v1.2.1**：
- ✅ 管理員可在 Web UI 調整 Threshold/Weights
- ✅ 調整後立即生效（無需創建新版本）
- ✅ 支援快速 A/B 測試（同版本不同配置）

**Protocol Assistant Chat**：
- ❌ 使用硬編碼的預設值
- ❌ 調整參數需修改程式碼並重啟
- ❌ 無法快速測試不同配置

### 2. **搜尋精準度**

**Dify v1.2.1**：
- ✅ **Title Boost**：標題匹配加分 15%/10%
- ✅ **動態 Threshold**：可根據測試結果調整
- ✅ **二階搜尋**：分段向量（標題偏重） + 全文向量（內容偏重）
- ✅ **權重配置**：Title 95%/5% → Title 10%/90%

**Protocol Assistant Chat**：
- ❌ **無 Title Boost**（或使用預設值）
- 📌 **固定 Threshold**：0.7（70%）
- ❓ **搜尋模式**：取決於實作（可能是單階段）
- ❌ **無權重配置**

### 3. **測試與追蹤**

**Dify v1.2.1**：
- ✅ **完整記錄**：`detailed_results.actual_config` 記錄實際使用的配置
- ✅ **配置來源**：`config_source: 'dynamic_from_db'` 或 `'version_default'`
- ✅ **版本管理**：可切換 Baseline，對比不同版本

**Protocol Assistant Chat**：
- ❌ **無配置記錄**
- ❌ **無追蹤機制**
- ❌ **無版本概念**

### 4. **使用者體驗**

**Dify v1.2.1**：
- 🎯 **目標用戶**：測試工程師、系統管理員
- 🎯 **使用場景**：效能測試、參數調優、版本對比
- 🎯 **操作方式**：批量測試、單版本測試、統計分析

**Protocol Assistant Chat**：
- 👤 **目標用戶**：一般用戶（測試人員、開發人員）
- 👤 **使用場景**：日常問答、查詢 Protocol 資訊
- 👤 **操作方式**：聊天對話、即時回應

---

## 🚀 實際範例對比

### 範例 1: 查詢 "USB IOL 測試流程"

#### 使用 Dify v1.2.1（Benchmark）

**步驟**：
1. 進入 `/dify-benchmark/versions`
2. 調整 Threshold 設定：85%, Title 90%, Content 10%
3. 選擇 v1.2.1 版本執行測試
4. 查詢："USB IOL 測試流程"

**搜尋過程**：
```
第一階段（分段向量搜尋）：
  - Threshold: 85%（從 DB 讀取）
  - Title Weight: 90%
  - Content Weight: 10%
  - Title Boost: +15%（如果標題包含 "USB IOL"）
  - 返回 20 個段落

第二階段（全文向量搜尋）：
  - Threshold: 80%
  - Title Weight: 10%
  - Content Weight: 90%
  - Title Boost: +10%
  - 返回 10 個文檔
```

**結果**：
- 找到標題為 "USB IOL 測試標準流程" 的文檔
- Title Boost 加分：85% × 1.15 = 97.75%（✨ 提升至頂部）
- 實際配置記錄在 `detailed_results.actual_config`

---

#### 使用 Protocol Assistant Chat

**步驟**：
1. 進入 `/protocol-assistant`
2. 輸入："USB IOL 測試流程"

**搜尋過程**：
```
標準向量搜尋：
  - Threshold: 70%（硬編碼）
  - 無權重配置
  - 無 Title Boost
  - 返回 5 個結果
```

**結果**：
- 找到相關文檔（基於向量相似度）
- 無加分機制，結果依賴向量語義
- 可能遺漏標題匹配度高的文檔

---

### 範例 2: A/B 測試不同 Threshold

#### 使用 Dify v1.2.1（支援）

**測試組 A**：
```
1. 設定 Threshold: 80%, Title 95%, Content 5%
2. 執行批量測試（記錄結果 A）
```

**測試組 B**：
```
1. 調整 Threshold: 85%, Title 90%, Content 10%
2. 執行批量測試（記錄結果 B）
```

**對比**：
- 查看兩組測試的平均分數、通過率
- 分析不同配置對檢索精準度的影響
- 選擇最佳配置作為 Baseline

---

#### 使用 Protocol Assistant Chat（不支援）

**問題**：
- ❌ 無法調整 Threshold（硬編碼 0.7）
- ❌ 無法進行 A/B 測試
- ❌ 需要修改程式碼並重啟才能測試不同配置

---

## 💡 何時使用哪個功能？

### 使用 Dify v1.2.1（Benchmark）的時機

✅ **效能調優**：
- 需要測試不同 Threshold/Weights 組合
- 需要找到最佳檢索參數
- 需要對比多個配置版本

✅ **版本管理**：
- 需要管理多個 RAG 配置版本
- 需要切換 Baseline 版本
- 需要追蹤配置歷史

✅ **批量測試**：
- 需要對多個版本執行相同測試
- 需要統計分析和結果對比
- 需要自動化測試流程

---

### 使用 Protocol Assistant Chat 的時機

✅ **日常使用**：
- 一般用戶查詢 Protocol 相關問題
- 即時對話、快速回應
- 不需要特定配置版本

✅ **生產環境**：
- 穩定的聊天功能
- 使用固定的搜尋配置
- 不需要頻繁調整參數

❓ **限制**：
- 無法調整搜尋參數
- 無法使用 Title Boost
- 無法追蹤配置來源

---

## 🔄 整合建議

### 方案 A: 將 Dify v1.2.1 配置應用到 Chat（推薦）

**目標**：讓 Protocol Assistant Chat 也使用動態配置和 Title Boost

**修改步驟**：

1. **修改 `ProtocolChatHandler`**：
   ```python
   # library/dify_integration/protocol_chat_handler.py
   
   def handle_chat_request(self, request):
       # 讀取當前 Baseline 版本配置
       baseline_config = self._load_baseline_config()
       
       # 傳遞給搜尋服務
       return self._execute_chat_request(
           message, conversation_id, dify_config, user,
           version_config=baseline_config  # 🆕 使用 Baseline 配置
       )
   
   def _load_baseline_config(self):
       from api.models import DifyConfigVersion
       baseline = DifyConfigVersion.objects.get(is_baseline=True)
       return {
           'rag_settings': baseline.rag_settings,
           'retrieval_mode': baseline.rag_settings.get('retrieval_mode')
       }
   ```

2. **修改 `_perform_backend_search`**：
   ```python
   # 傳遞 version_config 給搜尋服務
   results = search_service.search_knowledge(
       query=query,
       limit=5,
       use_vector=True,
       version_config=version_config  # 🆕 啟用動態配置
   )
   ```

3. **啟用動態載入**：
   - Chat 功能會自動使用當前 Baseline 的配置
   - 管理員調整 Threshold 後，Chat 也會使用新配置
   - Chat 結果也會受益於 Title Boost

**優點**：
- ✅ Chat 功能與 Benchmark 配置一致
- ✅ 自動使用最佳配置（Baseline）
- ✅ 享受 Title Boost 加分效果
- ✅ 配置調整後立即生效

**缺點**：
- ⚠️ Chat 配置會受 Baseline 切換影響
- ⚠️ 需要測試確保穩定性

---

### 方案 B: 保持 Chat 獨立配置（當前狀態）

**目標**：Benchmark 和 Chat 完全獨立

**優點**：
- ✅ Chat 功能穩定（不受測試影響）
- ✅ Benchmark 可自由調整配置

**缺點**：
- ❌ Chat 無法使用動態配置
- ❌ Chat 無法享受 Title Boost
- ❌ 配置不一致（需維護兩套）

---

## 📖 參考文檔

- **Dify v1.2.1 創建腳本**：`backend/scripts/create_dify_v1_2_1_dynamic_version.py`
- **動態配置載入器**：`library/dify_integration/dynamic_threshold_loader.py`
- **Protocol Chat Handler**：`library/dify_integration/protocol_chat_handler.py`
- **搜尋服務**：`library/protocol_guide/search_service.py`
- **版本管理頁面**：`frontend/src/pages/dify-benchmark/DifyVersionManagementPage.js`
- **聊天頁面**：`frontend/src/pages/ProtocolAssistantChatPage.js`

---

## ✅ 總結

| 面向 | Dify v1.2.1 | Protocol Assistant Chat |
|------|------------|------------------------|
| **目的** | 測試與調優 | 日常對話 |
| **用戶** | 測試工程師 | 一般用戶 |
| **配置** | 動態可調 | 固定硬編碼 |
| **精準度** | Title Boost + 動態權重 | 基礎向量搜尋 |
| **追蹤** | 完整記錄 | 無追蹤 |
| **靈活性** | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| **穩定性** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

**建議**：
- 💡 測試和調優使用 **Dify v1.2.1**
- 💡 日常對話使用 **Protocol Assistant Chat**
- 🚀 考慮將 Baseline 配置整合到 Chat（方案 A）

---

**文檔更新日期**：2025-01-20  
**版本**：v1.0  
**作者**：AI Platform Team
