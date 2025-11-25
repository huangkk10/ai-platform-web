# Dify v1.2.1 Task 8 範圍調整說明

**文檔編號**: DIFY-V1.2.1-TASK8-SCOPE  
**創建日期**: 2025-01-20  
**狀態**: 已修正 ✅  
**作者**: AI Platform Team

---

## 📋 原始計劃（Task 8）

**原始目標**: 整合 Baseline 版本配置到 Protocol Assistant 聊天中

**預期實作**:
```python
# backend/api/views/viewsets/protocol_assistant_viewset.py
@action(detail=False, methods=['post'])
def chat(self, request):
    # 1. 獲取 Baseline 版本
    baseline = DifyConfigVersion.objects.filter(is_baseline=True, is_active=True).first()
    
    # 2. 如果是動態版本，載入最新配置
    if baseline and DynamicThresholdLoader.is_dynamic_version(baseline.rag_settings):
        rag_settings = DynamicThresholdLoader.load_full_rag_settings(baseline.rag_settings)
    else:
        rag_settings = baseline.rag_settings if baseline else default_settings
    
    # 3. 使用 rag_settings 執行搜尋和聊天
    ...
```

---

## 🔍 技術調查結果

### 1. Protocol Assistant 聊天架構

**實際調用流程**:
```
ProtocolAssistantViewSet.chat()
  ↓
ProtocolGuideAPIHandler.handle_chat_api()
  ↓
SmartSearchRouter.handle_smart_search()
  ↓
TwoTierSearchHandler / KeywordTriggeredSearchHandler
  ↓
DifyChatClient.chat()  ← 調用 Dify Chat Messages API
  ↓
Dify 內建知識庫（不是外部知識庫 API）
```

### 2. Dify Chat API 限制

**核心發現**: Dify Chat Messages API (`/v1/chat-messages`) **不支援動態覆蓋檢索參數**！

**API 請求格式**:
```python
POST /v1/chat-messages
{
    "query": "用戶問題",
    "inputs": {
        "search_mode": "auto",          # ✅ 自定義變數（會傳遞到 Workflow）
        "rag_settings": {...}           # ❌ 無效！不會影響檢索參數
    },
    "conversation_id": "...",
    "user": "..."
}
```

**Dify 工作室配置**:
- Dify 的知識庫檢索參數（`top_k`, `score_threshold`, `rerank`）在 **Dify 工作室的知識庫設置** 中配置
- 這些參數是 **靜態的**，無法通過 Chat API 動態修改
- `inputs` 參數只會傳遞到 **Workflow 變數**，不影響檢索參數

### 3. 外部知識庫 API vs 內建知識庫

| 特性 | 外部知識庫 API | Dify 內建知識庫 |
|------|--------------|----------------|
| **使用場景** | Benchmark 批量測試 | Protocol/RVT Assistant 聊天 |
| **API 端點** | `/api/dify/knowledge/retrieval/` | Dify `/v1/chat-messages` |
| **參數控制** | ✅ 完全可控（threshold, top_k, stage） | ❌ 靜態配置（Dify 工作室） |
| **動態配置** | ✅ 支援 Baseline 動態載入 | ❌ 不支援 |
| **調用方** | `DifySearchHandler` | `DifyChatClient` |

---

## 🎯 修正後的實作範圍

### Task 8（修正版）: 說明與文檔更新

**實際可行範圍**:

#### 1. ✅ **Baseline 配置用於 Benchmark 測試**（已完成）
- `DifyTestRunner` 在批量測試時使用 Baseline 版本的 `rag_settings`
- 動態載入 `SearchThresholdSetting` 配置
- 記錄實際使用的配置到測試結果

**代碼位置**:
```python
# backend/api/views/viewsets/dify_benchmark_viewsets.py
def run_batch_test(self, request, pk=None):
    version = self.get_object()
    
    # 使用 Baseline 版本的配置
    if version.use_dynamic_threshold:
        rag_settings = DynamicThresholdLoader.load_full_rag_settings(version.rag_settings)
    else:
        rag_settings = version.rag_settings
    
    # 執行測試（傳遞配置到外部知識庫 API）
    ...
```

#### 2. ✅ **前端顯示 Baseline 資訊**（待實作）
- 在版本管理頁面顯示當前 Baseline（⭐ 圖標）
- 在聊天頁面顯示當前 Baseline 版本名稱和動態標記
- **僅供參考，不實際控制聊天配置**

**UI 設計**:
```jsx
// VersionManagementPage.js
<Tag color="gold" icon={<StarFilled />}>
  Baseline
</Tag>

{record.rag_settings?.stage1?.use_dynamic_threshold && (
  <Tag color="orange" icon={<SyncOutlined spin />}>
    動態 Threshold
  </Tag>
)}

// ProtocolAssistantChatPage.js
<Alert
  message={`當前 Baseline: ${baselineVersion.version_name}`}
  description="注意：Chat 配置在 Dify 工作室中設定，動態 Threshold 僅用於 Benchmark 測試"
  type="info"
  showIcon
/>
```

#### 3. ❌ **Protocol Assistant Chat 不使用動態配置**（技術限制）
- Dify Chat API 不支援動態覆蓋檢索參數
- 如需調整 Chat 的檢索參數，應在 **Dify 工作室** 手動修改
- Baseline 配置對 Chat 功能 **無實際影響**

---

## 📊 功能對照表

| 功能 | Baseline 配置是否生效 | 配置方式 |
|------|-------------------|---------|
| **Benchmark 批量測試** | ✅ 是 | 動態載入（從 DB） |
| **外部知識庫 API 測試** | ✅ 是 | 傳遞到 API 參數 |
| **Protocol Assistant Chat** | ❌ 否 | Dify 工作室靜態配置 |
| **RVT Assistant Chat** | ❌ 否 | Dify 工作室靜態配置 |

---

## 🛠️ 實作方案總結

### 已完成項目 ✅
1. `DynamicThresholdLoader` - 動態配置載入器
2. Benchmark API 整合 - 使用 Baseline 動態配置
3. 配置記錄 - 測試結果包含 `config_source` 和 `actual_config`
4. v1.2.1 版本創建 - 動態版本已存在於資料庫
5. Baseline API - `set_baseline` 和 `get_baseline` endpoints
6. 後端測試 - 6/6 測試全部通過

### 待完成項目 ⏳
7. **前端 UI** - 版本管理頁面和聊天頁面的 Baseline 資訊顯示（僅供參考）
8. **文檔更新** - 說明 Baseline 配置的適用範圍（本文檔）
9. **端到端測試** - 驗證 Baseline 切換和 Benchmark 測試流程

### 取消項目 ❌
- ~~Protocol Assistant Chat 使用動態配置~~ → 技術不可行

---

## 💡 建議與後續改進

### 1. 如果需要動態控制 Chat 檢索參數
**可能的方案**:
- 使用 Dify Workflow 的 **知識檢索節點**（支援變數覆蓋參數）
- 或者，部署多個 Dify App（每個 App 不同的靜態配置），通過前端選擇調用哪個 App

### 2. 當前 Baseline 機制的最佳實踐
**推薦使用流程**:
1. 在 Baseline Management 頁面設定版本為 Baseline
2. 在 Threshold Setting 頁面調整動態參數（Stage 1/2 閾值）
3. 執行 **Benchmark 批量測試** 評估效果
4. 滿意後，在 **Dify 工作室** 手動更新 Chat App 的檢索參數

### 3. 監控與報表
**已有功能**:
- ✅ Benchmark 測試結果包含配置來源（`config_source: 'dynamic_from_db'`）
- ✅ 測試結果顯示實際使用的 `actual_config`（threshold, top_k, weights）
- ✅ 前端可視化顯示配置對比（靜態 vs 動態）

---

## 📚 相關文檔

- `/docs/features/dify-v1-2-1-implementation-summary.md` - 完整實作計劃
- `/docs/testing/dify-v1-2-1-backend-test-report.md` - 後端測試報告
- `/docs/testing/dify-v1-2-1-api-quick-test-guide.md` - API 測試指南
- `/backend/scripts/create_dify_v1_2_1_dynamic_version.py` - 版本創建腳本

---

## ✅ 結論

**Task 8 的實際範圍調整為**:
1. ✅ 已完成 Baseline 配置在 **Benchmark 測試** 中的完整整合
2. ⏳ 待完成前端 UI 顯示 Baseline 資訊（**僅供參考，不影響 Chat**）
3. ✅ 明確說明技術限制（本文檔）

**關鍵認知**:
- **Baseline 動態配置僅用於 Benchmark 測試**
- **Chat 功能使用 Dify 工作室的靜態配置**
- **這是 Dify API 的架構限制，不是實作缺陷**

---

**文檔狀態**: ✅ 已完成  
**更新日期**: 2025-01-20  
**審核者**: AI Platform Team
