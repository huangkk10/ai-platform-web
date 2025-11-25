# Dify v1.2.1 動態 Threshold 版本實作規劃

**文檔版本**: v1.0  
**創建日期**: 2025-11-25  
**作者**: AI Platform Team  
**狀態**: 📋 規劃中（未執行）

---

## 📋 目錄

1. [需求說明](#需求說明)
2. [核心概念](#核心概念)
3. [系統架構](#系統架構)
4. [實作步驟](#實作步驟)
5. [檔案清單](#檔案清單)
6. [測試計畫](#測試計畫)
7. [風險評估](#風險評估)
8. [執行檢查清單](#執行檢查清單)

---

## 需求說明

### 背景

目前的 Dify 版本系統（v1.1, v1.2）使用**靜態配置**，權重值寫死在版本配置中：

```python
# 現狀：靜態配置（v1.2）
rag_settings = {
    "stage1": {
        "threshold": 0.80,      # 寫死
        "title_weight": 95,     # 寫死
        "content_weight": 5,    # 寫死
    }
}
```

**問題**：
- ❌ 調整參數需要創建新版本
- ❌ 版本數量爆炸（每個參數組合一個版本）
- ❌ 無法快速 A/B 測試不同配置
- ❌ 與 Web UI「搜尋 Threshold 設定」頁面脫節

### 需求目標

創建新版本 **"Dify 二階搜尋 v1.2.1 (Title Boost)"**，實現：

✅ **動態讀取** Web UI「搜尋 Threshold 設定」頁面的配置  
✅ **即時生效**：管理員在 UI 調整設定後，測試立即使用新值  
✅ **保留特性**：Title Boost 加分機制仍由版本定義（不從 DB 讀取）  
✅ **向後兼容**：不影響 v1.1, v1.2 等現有靜態版本  

### 使用情境

#### 情境 1：快速參數調優
```
1. 管理員在「搜尋 Threshold 設定」調整 Protocol Assistant:
   - 第一階段：Threshold 80% → 85%, 標題 95% → 90%, 內容 5% → 10%
   - 第二階段：Threshold 80% → 75%, 標題 10%, 內容 90%

2. 選擇 v1.2.1 版本執行批量測試
   ✅ 自動使用新設定（85%, 90%, 10%）
   ✅ 無需創建新版本

3. 查看測試結果
   ✅ detailed_results 記錄實際使用的配置
   ✅ 可追蹤參數變化對結果的影響
```

#### 情境 2：A/B 對比測試
```
測試組 A：
- 設定：80%, 95%, 5%
- 執行測試 → 記錄 Batch ID: A
- 平均分數：0.85

測試組 B：
- 設定：85%, 90%, 10%
- 執行測試 → 記錄 Batch ID: B
- 平均分數：0.87

✅ 同一個版本，不同配置，快速對比
```

---

## 核心概念

### 動態配置 vs 靜態配置

| 特性 | 靜態配置（v1.1, v1.2） | 動態配置（v1.2.1） |
|------|----------------------|-------------------|
| **配置來源** | 版本 rag_settings | Web UI + 版本 |
| **修改方式** | 創建新版本 | 調整 UI 設定 |
| **生效時間** | 需重新創建版本 | 立即生效 |
| **版本數量** | 多（每個參數組合一個） | 少（一個版本多種配置） |
| **適用場景** | 固定配置、基準測試 | 參數調優、A/B 測試 |

### 配置優先順序

```
┌─────────────────────────────────────────┐
│ 1. Web UI Threshold 設定（最高優先）    │
│    - 從 search_threshold_settings 讀取  │
│    - 管理員可調整                        │
│    - 包含：threshold, title_weight, ... │
└──────────────┬──────────────────────────┘
               │ 如果 DB 無設定 ↓
┌─────────────────────────────────────────┐
│ 2. 版本預設值（備援）                    │
│    - 從 DifyConfigVersion.rag_settings  │
│    - 作為預設值                          │
└──────────────┬──────────────────────────┘
               │ 如果版本無設定 ↓
┌─────────────────────────────────────────┐
│ 3. 程式碼預設值（最低優先）              │
│    - 硬編碼在程式碼中                    │
│    - 0.7, 60%, 40% 等                   │
└─────────────────────────────────────────┘
```

### 哪些配置動態？哪些固定？

#### 🔄 **動態配置**（從 Web UI 讀取）
- ✅ `threshold`（段落向量相似度閾值）
- ✅ `title_weight`（標題權重百分比）
- ✅ `content_weight`（內容權重百分比）

#### 📌 **固定配置**（由版本定義）
- 📌 `title_match_bonus`（Title Boost 加分，v1.2 特性）
- 📌 `min_keyword_length`（最小關鍵詞長度）
- 📌 `top_k`（返回結果數量）
- 📌 `retrieval_mode`（檢索模式）
- 📌 `search_service`（搜尋服務）

**原因**：固定配置是**版本特性**，不應該被 UI 設定影響。

---

## 系統架構

### 整體流程圖

```
┌──────────────────────────────────────────────────────────┐
│ Step 1: 管理員在 Web UI 調整 Threshold 設定               │
│         http://localhost/threshold-settings               │
│         Protocol Assistant: 80%, 95%, 5% (第一階段)       │
│                            80%, 10%, 90% (第二階段)       │
└────────────────┬─────────────────────────────────────────┘
                 │ 儲存到資料庫
                 ▼
┌──────────────────────────────────────────────────────────┐
│ Database: search_threshold_settings                       │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ assistant_type: 'protocol_assistant'                 │ │
│ │ stage1_threshold: 0.80                               │ │
│ │ stage1_title_weight: 95                              │ │
│ │ stage1_content_weight: 5                             │ │
│ │ stage2_threshold: 0.80                               │ │
│ │ stage2_title_weight: 10                              │ │
│ │ stage2_content_weight: 90                            │ │
│ └──────────────────────────────────────────────────────┘ │
└────────────────┬─────────────────────────────────────────┘
                 │ ThresholdManager 快取（5分鐘 TTL）
                 ▼
┌──────────────────────────────────────────────────────────┐
│ Step 2: 選擇版本 v1.2.1 進行批量測試                      │
│         VSA 版本管理頁面 → 勾選 v1.2.1 → 開始測試         │
└────────────────┬─────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────┐
│ Step 3: DifyBenchmarkViewSet.run_batch_test()            │
│         檢查版本配置中的 use_dynamic_threshold 標記       │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ if version.rag_settings['stage1']['use_dynamic']:   │ │
│ │     # 動態載入                                        │ │
│ │     rag_settings = DynamicThresholdLoader.load()    │ │
│ │ else:                                                 │ │
│ │     # 靜態配置（v1.1, v1.2）                          │ │
│ │     rag_settings = version.rag_settings             │ │
│ └──────────────────────────────────────────────────────┘ │
└────────────────┬─────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────┐
│ Step 4: DynamicThresholdLoader.load_full_rag_settings()  │
│         從資料庫讀取最新設定並合併版本特性                 │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ # 從 DB 讀取（動態）                                  │ │
│ │ threshold: 0.80 ← search_threshold_settings          │ │
│ │ title_weight: 95 ← search_threshold_settings         │ │
│ │ content_weight: 5 ← search_threshold_settings        │ │
│ │                                                       │ │
│ │ # 從版本讀取（固定）                                  │ │
│ │ title_match_bonus: 15 ← DifyConfigVersion            │ │
│ │ top_k: 20 ← DifyConfigVersion                        │ │
│ └──────────────────────────────────────────────────────┘ │
└────────────────┬─────────────────────────────────────────┘
                 │ 合併後的完整配置
                 ▼
┌──────────────────────────────────────────────────────────┐
│ Step 5: 執行測試                                          │
│         ProtocolGuideSearchService.search_knowledge()     │
│         使用動態載入的配置進行搜尋                         │
└────────────────┬─────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────┐
│ Step 6: 儲存測試結果                                      │
│         BenchmarkTestResult.detailed_results              │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ {                                                     │ │
│ │   "config_source": "dynamic",                        │ │
│ │   "loaded_from_db": true,                            │ │
│ │   "actual_config": {                                 │ │
│ │     "stage1": { "threshold": 0.80, ... },           │ │
│ │     "stage2": { "threshold": 0.80, ... }            │ │
│ │   }                                                   │ │
│ │ }                                                     │ │
│ └──────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

### 資料表關聯

```
┌─────────────────────────────────┐
│ SearchThresholdSetting (DB)     │
│ -------------------------------- │
│ id (PK)                          │
│ assistant_type (UNIQUE)          │
│ stage1_threshold                 │
│ stage1_title_weight              │
│ stage1_content_weight            │
│ stage2_threshold                 │
│ stage2_title_weight              │
│ stage2_content_weight            │
│ use_unified_weights              │
│ is_active                        │
│ updated_at                       │
└────────────┬────────────────────┘
             │ 1:N
             │ 被多個版本動態讀取
             ▼
┌─────────────────────────────────┐
│ DifyConfigVersion (DB)          │
│ -------------------------------- │
│ id (PK)                          │
│ version_code (UNIQUE)            │
│ version_name                     │
│ rag_settings (JSON)              │
│   ├─ stage1                      │
│   │   ├─ use_dynamic_threshold ✨│
│   │   ├─ assistant_type ✨       │
│   │   └─ title_match_bonus       │
│   └─ stage2                      │
│       ├─ use_dynamic_threshold ✨│
│       └─ title_match_bonus       │
│ is_baseline                      │
│ is_active                        │
└────────────┬────────────────────┘
             │ 1:N
             │ 產生多個測試結果
             ▼
┌─────────────────────────────────┐
│ BenchmarkTestRun (DB)           │
│ -------------------------------- │
│ id (PK)                          │
│ version_id (FK) ────────────────┤
│ run_type                         │
│ overall_score                    │
│ notes                            │
│ created_at                       │
└────────────┬────────────────────┘
             │ 1:N
             ▼
┌─────────────────────────────────┐
│ BenchmarkTestResult (DB)        │
│ -------------------------------- │
│ id (PK)                          │
│ test_run_id (FK)                 │
│ detailed_results (JSON)          │
│   └─ actual_config ✨            │
│       ├─ loaded_from_db          │
│       ├─ stage1 {...}            │
│       └─ stage2 {...}            │
└─────────────────────────────────┘
```

---

## 實作步驟

### Step 1: 創建動態 Threshold 載入器

**檔案**: `library/dify_integration/dynamic_threshold_loader.py` (新增)

**功能**:
- 檢查版本配置中的 `use_dynamic_threshold` 標記
- 從 `SearchThresholdSetting` 資料表讀取最新設定
- 合併動態設定（DB）+ 固定設定（版本）
- 支援快取機制（透過 ThresholdManager）
- 錯誤處理：DB 無設定時使用預設值

**核心邏輯**:
```python
class DynamicThresholdLoader:
    
    @staticmethod
    def load_stage_config(stage_config, assistant_type="protocol_assistant"):
        """載入單階段配置"""
        
        # 檢查是否啟用動態讀取
        if not stage_config.get('use_dynamic_threshold', False):
            return stage_config  # 靜態配置，直接返回
        
        # 從 ThresholdManager 讀取（有快取）
        manager = get_threshold_manager()
        db_settings = manager.get_settings(assistant_type)
        
        # 合併配置
        merged_config = {
            # 🔄 動態（從 DB）
            "threshold": float(db_settings.get('stage1_threshold', 0.80)),
            "title_weight": int(db_settings.get('stage1_title_weight', 95)),
            "content_weight": int(db_settings.get('stage1_content_weight', 5)),
            
            # 📌 固定（從版本）
            "title_match_bonus": stage_config.get('title_match_bonus', 0),
            "min_keyword_length": stage_config.get('min_keyword_length', 2),
            "top_k": stage_config.get('top_k', 20),
            
            # 元數據
            "use_dynamic_threshold": True,
            "loaded_from_db": True,
            "assistant_type": assistant_type,
        }
        
        return merged_config
    
    @staticmethod
    def load_full_rag_settings(rag_settings):
        """載入完整 RAG 設定（兩階段）"""
        
        assistant_type = rag_settings.get('assistant_type', 'protocol_assistant')
        
        return {
            "stage1": DynamicThresholdLoader.load_stage_config(
                rag_settings.get('stage1', {}), 
                assistant_type
            ),
            "stage2": DynamicThresholdLoader.load_stage_config(
                rag_settings.get('stage2', {}), 
                assistant_type
            ),
            "retrieval_mode": rag_settings.get('retrieval_mode'),
            "use_backend_search": rag_settings.get('use_backend_search', True),
            "search_service": rag_settings.get('search_service'),
            "assistant_type": assistant_type,
        }
```

**錯誤處理**:
- ✅ DB 無設定 → 使用版本預設值
- ✅ ThresholdManager 異常 → Fallback 到靜態配置
- ✅ 記錄完整日誌（debug, info, error）

---

### Step 2: 整合到 Benchmark API

**檔案**: `backend/api/views/viewsets/dify_benchmark_viewsets.py` (修改)

**修改位置**: `run_batch_test` 方法

**修改前**:
```python
@action(detail=False, methods=['post'])
def run_batch_test(self, request):
    """執行批量測試"""
    
    version_ids = request.data.get('version_ids', [])
    
    for version_id in version_ids:
        version = DifyConfigVersion.objects.get(id=version_id)
        
        # 直接使用版本配置
        rag_settings = version.rag_settings
        
        # 執行測試
        self._run_single_version_test(version, rag_settings, test_cases)
```

**修改後**:
```python
from library.dify_integration.dynamic_threshold_loader import DynamicThresholdLoader

@action(detail=False, methods=['post'])
def run_batch_test(self, request):
    """執行批量測試"""
    
    version_ids = request.data.get('version_ids', [])
    
    for version_id in version_ids:
        version = DifyConfigVersion.objects.get(id=version_id)
        
        # 🆕 檢查是否啟用動態載入
        if version.rag_settings.get('stage1', {}).get('use_dynamic_threshold'):
            logger.info(f"🔄 版本 {version.version_name} 使用動態 Threshold")
            
            # 動態載入最新配置
            rag_settings = DynamicThresholdLoader.load_full_rag_settings(
                version.rag_settings
            )
            
            logger.info(f"載入配置: Stage1 {rag_settings['stage1']['threshold']}, "
                       f"Title {rag_settings['stage1']['title_weight']}%")
        else:
            logger.info(f"📌 版本 {version.version_name} 使用靜態配置")
            rag_settings = version.rag_settings
        
        # 執行測試（使用動態或靜態配置）
        self._run_single_version_test(version, rag_settings, test_cases)
```

**新增功能**:
- ✅ 自動偵測 `use_dynamic_threshold` 標記
- ✅ 靜態版本（v1.1, v1.2）不受影響
- ✅ 記錄實際使用的配置到 `detailed_results`

---

### Step 3: 記錄實際使用的配置

**檔案**: `backend/api/views/viewsets/dify_benchmark_viewsets.py` (修改)

**修改位置**: `_run_single_version_test` 方法

**目的**: 在測試結果中記錄實際使用的配置（追蹤性）

**實作**:
```python
def _run_single_version_test(self, version, rag_settings, test_cases):
    """執行單一版本測試"""
    
    # ... 執行測試邏輯 ...
    
    # 建立測試結果記錄
    test_result = BenchmarkTestResult.objects.create(
        test_run=test_run,
        test_case=test_case,
        # ... 其他欄位 ...
        detailed_results={
            # 🆕 記錄實際配置
            "config_source": "dynamic" if rag_settings.get('stage1', {}).get('loaded_from_db') else "static",
            "actual_config": {
                "stage1": {
                    "threshold": rag_settings['stage1']['threshold'],
                    "title_weight": rag_settings['stage1']['title_weight'],
                    "content_weight": rag_settings['stage1']['content_weight'],
                    "title_match_bonus": rag_settings['stage1'].get('title_match_bonus', 0),
                },
                "stage2": {
                    "threshold": rag_settings['stage2']['threshold'],
                    "title_weight": rag_settings['stage2']['title_weight'],
                    "content_weight": rag_settings['stage2']['content_weight'],
                    "title_match_bonus": rag_settings['stage2'].get('title_match_bonus', 0),
                },
            },
            "loaded_from_db": rag_settings.get('stage1', {}).get('loaded_from_db', False),
            "assistant_type": rag_settings.get('assistant_type', 'unknown'),
            # ... 其他測試結果 ...
        }
    )
```

**好處**:
- ✅ 追蹤每次測試使用的實際配置
- ✅ A/B 測試時可對比參數差異
- ✅ 除錯時可確認配置來源

---

### Step 4: 創建版本腳本

**檔案**: `backend/scripts/create_dify_v1_2_1_dynamic_version.py` (新增)

**功能**: 創建 v1.2.1 版本記錄到資料庫

**完整腳本結構**:
```python
#!/usr/bin/env python
"""創建 Dify v1.2.1 版本（動態 Threshold）"""

def create_v1_2_1_dynamic_version():
    """創建版本"""
    
    # 版本描述（詳細說明動態特性）
    description = """
    📝 Dify 二階搜尋 v1.2.1 (Title Boost - Dynamic Threshold)
    
    🆕 核心特性：
    ✅ 動態讀取 Web UI「搜尋 Threshold 設定」
    ✅ 管理員可即時調整參數無需創建新版本
    ✅ 保留 Title Boost 加分機制（版本特性）
    ✅ 向後兼容所有靜態版本
    
    ... (詳細說明)
    """
    
    # 🆕 動態 RAG 設定
    rag_settings = {
        "assistant_type": "protocol_assistant",
        
        "stage1": {
            # 🆕 啟用動態載入
            "use_dynamic_threshold": True,
            "assistant_type": "protocol_assistant",
            
            # 📌 版本特定設定（固定）
            "title_match_bonus": 15,
            "min_keyword_length": 2,
            "top_k": 20,
            
            # ⚠️ 預設值（當 DB 無設定時使用）
            "threshold": 0.80,
            "title_weight": 95,
            "content_weight": 5,
        },
        
        "stage2": {
            "use_dynamic_threshold": True,
            "assistant_type": "protocol_assistant",
            
            "title_match_bonus": 10,
            "min_keyword_length": 2,
            "top_k": 10,
            
            "threshold": 0.80,
            "title_weight": 10,
            "content_weight": 90,
        },
        
        "retrieval_mode": "two_stage_with_title_boost",
        "use_backend_search": True,
        "search_service": "ProtocolGuideSearchService"
    }
    
    # 創建版本記錄
    version, created = DifyConfigVersion.objects.get_or_create(
        version_code="dify-two-tier-v1.2.1",
        defaults={
            'version_name': "Dify 二階搜尋 v1.2.1 (Title Boost)",
            'dify_app_id': "app-MgZZOhADkEmdUrj2DtQLJ23G",
            'dify_api_key': "app-MgZZOhADkEmdUrj2DtQLJ23G",
            'dify_api_url': "http://10.10.172.37/v1/chat-messages",
            'description': description,
            'rag_settings': rag_settings,
            'model_config': {...},
            'retrieval_mode': 'two_stage_with_title_boost',
            'is_active': True,
            'is_baseline': False,
            'created_by': admin_user
        }
    )
    
    # 輸出確認資訊
    if created:
        print("✅ 成功創建動態 Threshold 版本")
        print(f"   Stage 1 動態: {rag_settings['stage1']['use_dynamic_threshold']}")
        print(f"   Stage 1 Title Boost: {rag_settings['stage1']['title_match_bonus']}%")
        # ...
```

**執行命令**:
```bash
docker exec ai-django python backend/scripts/create_dify_v1_2_1_dynamic_version.py
```

---

### Step 5: 前端顯示（可選）

**可選功能**: 在 VSA 版本管理頁面顯示「動態」標記

**檔案**: `frontend/src/pages/benchmark/VersionManagementPage.js` (可選修改)

**顯示邏輯**:
```jsx
// 版本列表中顯示動態標記
{version.rag_settings?.stage1?.use_dynamic_threshold && (
  <Tag color="orange" icon={<SyncOutlined spin />}>
    動態 Threshold
  </Tag>
)}
```

**Tooltip 說明**:
```jsx
<Tooltip title="此版本會動態讀取「搜尋 Threshold 設定」頁面的最新配置">
  <Tag color="orange">動態</Tag>
</Tooltip>
```

---

## 檔案清單

### 需要創建的檔案

| 檔案路徑 | 類型 | 說明 | 優先級 |
|---------|------|------|--------|
| `library/dify_integration/dynamic_threshold_loader.py` | 新增 | 動態配置載入器（核心） | 🔴 高 |
| `backend/scripts/create_dify_v1_2_1_dynamic_version.py` | 新增 | 版本創建腳本 | 🔴 高 |
| `docs/features/dify-v1-2-1-dynamic-threshold-implementation-plan.md` | 新增 | 本規劃文檔 | 🟡 中 |

### 需要修改的檔案

| 檔案路徑 | 修改內容 | 影響範圍 | 優先級 |
|---------|---------|---------|--------|
| `backend/api/views/viewsets/dify_benchmark_viewsets.py` | `run_batch_test` 方法整合動態載入 | Benchmark API | 🔴 高 |
| `backend/api/views/viewsets/dify_benchmark_viewsets.py` | `_run_single_version_test` 記錄實際配置 | 測試結果追蹤 | 🟡 中 |
| `frontend/src/pages/benchmark/VersionManagementPage.js` | 顯示「動態」標記（可選） | UI 顯示 | 🟢 低 |

### 無需修改的檔案（已支援）

| 檔案路徑 | 說明 |
|---------|------|
| `backend/api/models.py` | `SearchThresholdSetting` 已存在 ✅ |
| `backend/api/models.py` | `DifyConfigVersion` 支援 JSON 欄位 ✅ |
| `library/common/threshold_manager.py` | ThresholdManager 已有快取機制 ✅ |
| `backend/api/views/viewsets/threshold_viewsets.py` | Threshold API 已完整 ✅ |

---

## 測試計畫

### 單元測試

#### 測試 1: 動態載入器功能測試

**檔案**: `backend/tests/test_dynamic_threshold_loader.py` (新增)

**測試案例**:
```python
class TestDynamicThresholdLoader(TestCase):
    
    def test_load_static_config_unchanged(self):
        """靜態配置不應該被修改"""
        static_config = {
            "use_dynamic_threshold": False,
            "threshold": 0.75,
            "title_weight": 80,
        }
        
        result = DynamicThresholdLoader.load_stage_config(static_config)
        
        self.assertEqual(result, static_config)
    
    def test_load_dynamic_config_from_db(self):
        """動態配置應該從 DB 讀取"""
        # 準備 DB 資料
        SearchThresholdSetting.objects.create(
            assistant_type='protocol_assistant',
            stage1_threshold=0.85,
            stage1_title_weight=90,
            stage1_content_weight=10
        )
        
        dynamic_config = {
            "use_dynamic_threshold": True,
            "assistant_type": "protocol_assistant",
            "title_match_bonus": 15,
        }
        
        result = DynamicThresholdLoader.load_stage_config(dynamic_config)
        
        # 驗證動態載入
        self.assertEqual(result['threshold'], 0.85)
        self.assertEqual(result['title_weight'], 90)
        self.assertEqual(result['content_weight'], 10)
        
        # 驗證固定配置保留
        self.assertEqual(result['title_match_bonus'], 15)
        
        # 驗證元數據
        self.assertTrue(result['loaded_from_db'])
    
    def test_fallback_when_db_empty(self):
        """DB 無設定時應該使用預設值"""
        dynamic_config = {
            "use_dynamic_threshold": True,
            "assistant_type": "nonexistent_assistant",
            "threshold": 0.70,  # 預設值
        }
        
        result = DynamicThresholdLoader.load_stage_config(dynamic_config)
        
        # 應該使用預設值
        self.assertEqual(result['threshold'], 0.70)
```

#### 測試 2: Benchmark API 整合測試

**檔案**: `backend/tests/test_dify_benchmark_dynamic.py` (新增)

**測試案例**:
```python
class TestDifyBenchmarkDynamic(TestCase):
    
    def test_static_version_unchanged(self):
        """靜態版本（v1.1, v1.2）不應受影響"""
        # 測試 v1.1 和 v1.2 仍正常運作
        pass
    
    def test_dynamic_version_loads_from_db(self):
        """動態版本應該從 DB 載入配置"""
        # 創建 v1.2.1 版本
        # 調整 SearchThresholdSetting
        # 執行測試
        # 驗證使用 DB 配置
        pass
    
    def test_config_recorded_in_results(self):
        """測試結果應該記錄實際配置"""
        # 執行測試
        # 檢查 detailed_results 中的 actual_config
        pass
```

### 整合測試

#### 測試場景 1: 端到端動態配置測試

**步驟**:
1. ✅ 在 Web UI 設定 Protocol Assistant 參數
   - 第一階段：85%, 90%, 10%
   - 第二階段：75%, 15%, 85%

2. ✅ 選擇 v1.2.1 版本執行批量測試

3. ✅ 驗證測試過程
   - 檢查日誌：確認「動態載入」訊息
   - 檢查 DB 查詢：ThresholdManager 快取命中

4. ✅ 驗證測試結果
   - `detailed_results.config_source` = "dynamic"
   - `detailed_results.actual_config` 包含 85%, 90%, 10%
   - Title Boost 仍為 15%（固定）

#### 測試場景 2: A/B 對比測試

**步驟**:
1. ✅ 測試組 A
   - 設定：80%, 95%, 5%
   - 執行測試 → Batch ID: A
   - 記錄平均分數

2. ✅ 測試組 B
   - 修改設定：85%, 90%, 10%
   - 執行測試 → Batch ID: B
   - 記錄平均分數

3. ✅ 對比結果
   - 在批量測試對比頁面查看兩組差異
   - 分析參數變化對分數的影響

### 效能測試

#### 測試 1: 快取機制驗證

**目的**: 確認 ThresholdManager 快取正常運作

**測試方法**:
```python
def test_cache_performance():
    # 第一次載入（從 DB）
    start = time.time()
    config1 = DynamicThresholdLoader.load_stage_config(...)
    time1 = time.time() - start
    
    # 第二次載入（從快取）
    start = time.time()
    config2 = DynamicThresholdLoader.load_stage_config(...)
    time2 = time.time() - start
    
    # 驗證快取生效
    assert time2 < time1 * 0.1  # 快取應該快 10 倍以上
    assert config1 == config2
```

**預期結果**:
- 第一次載入：< 50ms（含 DB 查詢）
- 快取命中：< 5ms

#### 測試 2: 批量測試效能

**目的**: 確認動態載入不影響測試效能

**測試方法**:
- 執行 100 個測試案例
- 對比靜態版本 vs 動態版本的執行時間

**預期結果**:
- 動態版本耗時 ≈ 靜態版本 + 5% (快取機制生效)

---

## 風險評估

### 高風險項目

#### 風險 1: 並行測試配置混淆

**描述**: 
如果多個用戶同時執行測試，且期間有人修改 Threshold 設定，可能導致配置不一致。

**影響**: 
- 測試結果難以復現
- A/B 測試結果不可靠

**緩解措施**:
1. ✅ 在測試結果中記錄實際使用的配置（`detailed_results.actual_config`）
2. ✅ 建議測試前記錄當前設定值
3. 🔄 進階方案（未實作）：測試開始時鎖定配置快照

**優先級**: 🔴 高

---

#### 風險 2: 快取不同步

**描述**: 
ThresholdManager 有 5 分鐘快取，修改 UI 設定後可能不會立即生效。

**影響**: 
- 管理員調整參數後測試仍使用舊值
- 需要等待 5 分鐘或手動刷新快取

**緩解措施**:
1. ✅ 提供「刷新快取」API：`POST /api/threshold-settings/refresh-cache/`
2. ✅ Web UI 提供「刷新」按鈕
3. ✅ 調整設定後自動刷新快取（建議實作）

**優先級**: 🟡 中

---

### 中風險項目

#### 風險 3: DB 設定被誤刪

**描述**: 
如果 `SearchThresholdSetting` 記錄被刪除，動態版本會 Fallback 到預設值。

**影響**: 
- 測試結果與預期不符
- 管理員困惑為何設定不生效

**緩解措施**:
1. ✅ 錯誤日誌記錄：明確記錄「找不到 DB 設定，使用預設值」
2. ✅ 監控告警：DB 設定被刪除時發送通知
3. ✅ 資料庫約束：防止意外刪除（ON DELETE RESTRICT）

**優先級**: 🟡 中

---

### 低風險項目

#### 風險 4: 版本配置錯誤

**描述**: 
創建版本時設定錯誤的 `assistant_type` 或遺漏 `use_dynamic_threshold` 標記。

**影響**: 
- 版本無法動態載入
- 但會 Fallback 到靜態配置，不會崩潰

**緩解措施**:
1. ✅ 版本創建腳本包含完整驗證
2. ✅ 詳細的日誌輸出確認配置
3. ✅ 單元測試覆蓋所有配置組合

**優先級**: 🟢 低

---

## 執行檢查清單

### 開發階段

- [ ] **Step 1**: 創建 `dynamic_threshold_loader.py`
  - [ ] 實作 `load_stage_config` 方法
  - [ ] 實作 `load_full_rag_settings` 方法
  - [ ] 添加錯誤處理和日誌記錄
  - [ ] 撰寫單元測試

- [ ] **Step 2**: 修改 `dify_benchmark_viewsets.py`
  - [ ] 整合動態載入邏輯到 `run_batch_test`
  - [ ] 修改 `_run_single_version_test` 記錄實際配置
  - [ ] 添加日誌輸出
  - [ ] 撰寫整合測試

- [ ] **Step 3**: 創建版本腳本
  - [ ] 撰寫 `create_dify_v1_2_1_dynamic_version.py`
  - [ ] 定義完整的 `rag_settings` 結構
  - [ ] 撰寫詳細的版本描述
  - [ ] 添加執行驗證邏輯

- [ ] **Step 4**: 撰寫測試
  - [ ] 單元測試：動態載入器
  - [ ] 整合測試：Benchmark API
  - [ ] 端到端測試：完整流程
  - [ ] 效能測試：快取機制

### 測試階段

- [ ] **功能測試**
  - [ ] 靜態版本（v1.1, v1.2）不受影響
  - [ ] 動態版本（v1.2.1）正確載入 DB 設定
  - [ ] DB 無設定時使用預設值
  - [ ] 快取機制正常運作

- [ ] **整合測試**
  - [ ] 端到端流程測試
  - [ ] A/B 對比測試
  - [ ] 並行測試驗證

- [ ] **效能測試**
  - [ ] 快取命中率 > 95%
  - [ ] 動態載入耗時 < 10ms
  - [ ] 批量測試效能無明顯下降

### 部署階段

- [ ] **資料庫準備**
  - [ ] 確認 `search_threshold_settings` 表存在
  - [ ] 確認 Protocol Assistant 設定已初始化
  - [ ] 備份現有測試資料

- [ ] **執行版本創建**
  - [ ] 執行腳本：`docker exec ai-django python backend/scripts/create_dify_v1_2_1_dynamic_version.py`
  - [ ] 驗證版本創建成功
  - [ ] 確認版本在 VSA 頁面顯示

- [ ] **驗證測試**
  - [ ] 調整 Threshold 設定
  - [ ] 執行 v1.2.1 測試
  - [ ] 檢查測試結果中的實際配置
  - [ ] 確認 Title Boost 正常運作

### 監控階段

- [ ] **日誌監控**
  - [ ] 檢查動態載入日誌
  - [ ] 監控 Fallback 觸發次數
  - [ ] 檢查快取命中率

- [ ] **效能監控**
  - [ ] 測試執行時間
  - [ ] DB 查詢次數
  - [ ] API 回應時間

- [ ] **使用者回饋**
  - [ ] 測試結果是否符合預期
  - [ ] 參數調整是否即時生效
  - [ ] UI 提示是否清楚

---

## 附錄

### A. 配置範例對比

#### v1.1 (靜態配置 - Baseline)
```json
{
  "stage1": {
    "threshold": 0.80,
    "title_weight": 95,
    "content_weight": 5,
    "top_k": 20
  },
  "stage2": {
    "threshold": 0.80,
    "title_weight": 10,
    "content_weight": 90,
    "top_k": 10
  },
  "retrieval_mode": "two_stage"
}
```

#### v1.2 (靜態配置 + Title Boost)
```json
{
  "stage1": {
    "threshold": 0.80,
    "title_weight": 95,
    "content_weight": 5,
    "title_match_bonus": 15,  // 🆕 Title Boost
    "top_k": 20
  },
  "stage2": {
    "threshold": 0.80,
    "title_weight": 10,
    "content_weight": 90,
    "title_match_bonus": 10,  // 🆕 Title Boost
    "top_k": 10
  },
  "retrieval_mode": "two_stage_with_title_boost"
}
```

#### v1.2.1 (動態配置 + Title Boost)
```json
{
  "assistant_type": "protocol_assistant",  // 🆕 指定 Assistant
  
  "stage1": {
    // 🆕 動態標記
    "use_dynamic_threshold": true,
    "assistant_type": "protocol_assistant",
    
    // 🔄 從 DB 讀取（管理員可調整）
    "threshold": 0.80,        // ← search_threshold_settings.stage1_threshold
    "title_weight": 95,       // ← search_threshold_settings.stage1_title_weight
    "content_weight": 5,      // ← search_threshold_settings.stage1_content_weight
    
    // 📌 固定配置（版本特性）
    "title_match_bonus": 15,
    "min_keyword_length": 2,
    "top_k": 20
  },
  
  "stage2": {
    "use_dynamic_threshold": true,
    "assistant_type": "protocol_assistant",
    
    // 🔄 從 DB 讀取
    "threshold": 0.80,
    "title_weight": 10,
    "content_weight": 90,
    
    // 📌 固定配置
    "title_match_bonus": 10,
    "top_k": 10
  },
  
  "retrieval_mode": "two_stage_with_title_boost"
}
```

### B. API 使用範例

#### 查詢當前 Threshold 設定
```bash
curl -X GET "http://localhost/api/threshold-settings/" \
  -H "Authorization: Token YOUR_TOKEN"
```

**回應**:
```json
[
  {
    "id": 1,
    "assistant_type": "protocol_assistant",
    "assistant_type_display": "Protocol Assistant",
    "stage1_threshold": "0.80",
    "stage1_title_weight": 95,
    "stage1_content_weight": 5,
    "stage2_threshold": "0.80",
    "stage2_title_weight": 10,
    "stage2_content_weight": 90,
    "is_active": true,
    "updated_at": "2025-11-25T10:00:00Z"
  }
]
```

#### 刷新快取
```bash
curl -X POST "http://localhost/api/threshold-settings/refresh-cache/" \
  -H "Authorization: Token YOUR_TOKEN"
```

**回應**:
```json
{
  "message": "快取已刷新",
  "cache_cleared": true,
  "timestamp": "2025-11-25T10:05:00Z"
}
```

#### 執行批量測試（勾選 v1.2.1）
```bash
curl -X POST "http://localhost/api/dify-benchmark/run-batch-test/" \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "version_ids": [1, 2, 3],  // 包含 v1.2.1
    "test_case_ids": [1, 2, 3, 4, 5]
  }'
```

### C. 故障排查指南

#### 問題 1: 動態配置沒有生效

**症狀**: 調整 Web UI 設定後，測試結果沒有變化

**檢查步驟**:
1. ✅ 確認版本配置中 `use_dynamic_threshold: true`
   ```python
   version = DifyConfigVersion.objects.get(version_code="dify-two-tier-v1.2.1")
   print(version.rag_settings['stage1']['use_dynamic_threshold'])
   ```

2. ✅ 確認 DB 設定存在
   ```python
   setting = SearchThresholdSetting.objects.get(assistant_type='protocol_assistant')
   print(setting.stage1_threshold, setting.stage1_title_weight)
   ```

3. ✅ 刷新快取
   ```bash
   curl -X POST "http://localhost/api/threshold-settings/refresh-cache/"
   ```

4. ✅ 檢查日誌
   ```bash
   docker logs ai-django --tail 100 | grep "動態載入\|DynamicThresholdLoader"
   ```

---

#### 問題 2: 測試結果中看不到實際配置

**症狀**: `detailed_results` 中沒有 `actual_config` 欄位

**檢查步驟**:
1. ✅ 確認 Benchmark API 已修改
   ```python
   # 檢查 _run_single_version_test 方法
   # 應該有記錄 actual_config 的邏輯
   ```

2. ✅ 檢查測試結果
   ```python
   result = BenchmarkTestResult.objects.latest('created_at')
   print(result.detailed_results.get('actual_config'))
   ```

---

#### 問題 3: Title Boost 沒有作用

**症狀**: 測試結果與 v1.1 相同，沒有標題加分效果

**檢查步驟**:
1. ✅ 確認 `retrieval_mode` 為 `two_stage_with_title_boost`
2. ✅ 確認 `title_match_bonus` 存在且 > 0
3. ✅ 檢查搜尋服務是否支援 Title Boost
   ```python
   # library/protocol_guide/search_service.py
   # 應該有 Title Boost 邏輯
   ```

---

## 總結

本規劃文檔詳細說明了 **Dify v1.2.1 動態 Threshold 版本**的完整實作方案。

**核心特性**:
- 🔄 動態讀取 Web UI 設定（管理員可調整）
- 📌 保留 Title Boost 特性（版本定義）
- ✅ 向後兼容所有現有版本
- 📊 完整的測試結果追蹤

**預期效果**:
- 快速參數調優（無需創建新版本）
- 靈活的 A/B 測試（同版本不同配置）
- 更好的可追蹤性（記錄實際配置）
- 減少版本爆炸（一個版本多種配置）

**下一步**: 確認此規劃後，開始執行實作步驟。

---

**文檔狀態**: ✅ 規劃完成（含 Baseline 切換功能）  
**等待**: 用戶確認後開始實作

---

## 📌 附加功能：Baseline 版本切換機制

### 功能需求

在 VSA 版本管理頁面添加「設為 Baseline」按鈕，允許管理員：
1. ✅ 將任何版本設為 Protocol Assistant 的預設版本
2. ✅ Protocol Assistant 聊天時自動使用該 Baseline 版本的配置
3. ✅ 如果 Baseline 是動態版本（v1.2.1），則自動讀取最新 Threshold 設定
4. ✅ 支援快速切換不同版本進行生產環境測試

### 系統架構擴充

#### 現有 Baseline 機制

**資料庫層面**：
```python
class DifyConfigVersion(models.Model):
    is_baseline = models.BooleanField(default=False)  # 已存在
    # 目前：只是標記，沒有實際切換功能
```

**問題**：
- ❌ `is_baseline` 只是標記，沒有與 Protocol Assistant 聊天功能連動
- ❌ 切換 Baseline 需要手動修改程式碼
- ❌ 無法在 UI 上快速切換版本

#### 新增：Baseline 切換與應用機制

```
┌────────────────────────────────────────────────────────┐
│ VSA 版本管理頁面                                        │
│ ┌────────────────────────────────────────────────────┐ │
│ │ 版本列表                                            │ │
│ │ ✅ v1.1 (Baseline)        [切換為 Baseline]        │ │
│ │ ⭐ v1.2 Title Boost       [設為 Baseline] ←Click   │ │
│ │ 🔄 v1.2.1 Dynamic         [設為 Baseline]          │ │
│ └────────────────────────────────────────────────────┘ │
└────────────────┬───────────────────────────────────────┘
                 │ API: POST /api/dify-versions/{id}/set-baseline/
                 ▼
┌────────────────────────────────────────────────────────┐
│ Backend: 更新 Baseline 標記                            │
│ 1. 清除所有版本的 is_baseline = False                  │
│ 2. 設定選定版本的 is_baseline = True                   │
│ 3. 記錄切換日誌                                        │
└────────────────┬───────────────────────────────────────┘
                 │ 
                 ▼
┌────────────────────────────────────────────────────────┐
│ Protocol Assistant 聊天                                 │
│ 使用者發送訊息 → 自動使用 Baseline 版本               │
└────────────────┬───────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────┐
│ 檢查 Baseline 版本配置                                 │
│ - 如果是 v1.2.1 (動態) → 讀取最新 Threshold 設定     │
│ - 如果是 v1.2 (靜態) → 使用版本固定配置              │
│ - 如果是 v1.1 (靜態) → 使用版本固定配置              │
└────────────────────────────────────────────────────────┘
```

### 實作步驟

#### **Step 1: 擴充 DifyConfigVersion API**

**檔案**: `backend/api/views/viewsets/dify_benchmark_viewsets.py` (修改)

**新增 Action**:
```python
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction

class DifyConfigVersionViewSet(viewsets.ModelViewSet):
    # ... 現有程式碼 ...
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def set_baseline(self, request, pk=None):
        """
        設定指定版本為 Baseline
        
        POST /api/dify-versions/{id}/set-baseline/
        
        功能：
        1. 清除所有版本的 is_baseline 標記
        2. 設定選定版本為 Baseline
        3. 記錄操作日誌
        4. 刷新快取（如果是動態版本）
        
        權限：僅管理員
        """
        version = self.get_object()
        
        with transaction.atomic():
            # 清除所有 Baseline 標記
            DifyConfigVersion.objects.filter(is_baseline=True).update(is_baseline=False)
            
            # 設定新的 Baseline
            version.is_baseline = True
            version.save()
            
            # 🆕 如果是動態版本，刷新 Threshold 快取
            if version.rag_settings.get('stage1', {}).get('use_dynamic_threshold'):
                from library.common.threshold_manager import get_threshold_manager
                manager = get_threshold_manager()
                manager.clear_cache()
                logger.info(f"🔄 動態版本 {version.version_name} 設為 Baseline，已刷新快取")
            
            # 記錄操作日誌
            logger.info(
                f"✅ 版本切換: {version.version_name} (ID: {version.id}) "
                f"已設為 Baseline，操作者: {request.user.username}"
            )
        
        return Response({
            'message': f'版本 {version.version_name} 已設為 Baseline',
            'version_id': version.id,
            'version_name': version.version_name,
            'is_dynamic': version.rag_settings.get('stage1', {}).get('use_dynamic_threshold', False),
            'timestamp': timezone.now().isoformat(),
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def get_baseline(self, request):
        """
        獲取當前 Baseline 版本
        
        GET /api/dify-versions/get-baseline/
        
        回應：
        {
            "version_id": 1,
            "version_name": "Dify 二階搜尋 v1.2.1",
            "version_code": "dify-two-tier-v1.2.1",
            "is_dynamic": true,
            "rag_settings": {...},
            "description": "..."
        }
        """
        baseline = DifyConfigVersion.objects.filter(is_baseline=True, is_active=True).first()
        
        if not baseline:
            return Response({
                'error': '找不到 Baseline 版本',
                'message': '請在版本管理中設定一個 Baseline 版本'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # 🆕 如果是動態版本，載入最新配置
        if baseline.rag_settings.get('stage1', {}).get('use_dynamic_threshold'):
            from library.dify_integration.dynamic_threshold_loader import DynamicThresholdLoader
            rag_settings = DynamicThresholdLoader.load_full_rag_settings(baseline.rag_settings)
        else:
            rag_settings = baseline.rag_settings
        
        serializer = self.get_serializer(baseline)
        data = serializer.data
        data['rag_settings'] = rag_settings  # 返回動態載入後的配置
        
        return Response(data, status=status.HTTP_200_OK)
```

---

#### **Step 2: Protocol Assistant 聊天整合**

**檔案**: `backend/api/views/viewsets/protocol_guide_viewsets.py` (修改)

**修改 chat action**:
```python
class ProtocolGuideViewSet(viewsets.ModelViewSet):
    # ... 現有程式碼 ...
    
    @action(detail=False, methods=['post'])
    def chat(self, request):
        """
        Protocol Assistant 聊天
        
        🆕 自動使用 Baseline 版本的配置
        """
        user_message = request.data.get('message', '')
        conversation_id = request.data.get('conversation_id', None)
        
        # 🆕 獲取 Baseline 版本配置
        baseline = DifyConfigVersion.objects.filter(
            is_baseline=True, 
            is_active=True
        ).first()
        
        if not baseline:
            logger.warning("⚠️ 找不到 Baseline 版本，使用預設配置")
            # Fallback: 使用程式碼預設配置
            rag_settings = self._get_default_rag_settings()
        else:
            logger.info(f"✅ 使用 Baseline 版本: {baseline.version_name}")
            
            # 🆕 如果是動態版本，載入最新配置
            if baseline.rag_settings.get('stage1', {}).get('use_dynamic_threshold'):
                from library.dify_integration.dynamic_threshold_loader import DynamicThresholdLoader
                rag_settings = DynamicThresholdLoader.load_full_rag_settings(
                    baseline.rag_settings
                )
                logger.info(
                    f"🔄 動態載入配置: Stage1 Threshold={rag_settings['stage1']['threshold']}, "
                    f"Title={rag_settings['stage1']['title_weight']}%"
                )
            else:
                rag_settings = baseline.rag_settings
                logger.info(f"📌 使用靜態配置: {baseline.version_name}")
        
        # 執行搜尋和聊天
        try:
            # 使用 rag_settings 進行搜尋
            search_results = self._search_with_config(user_message, rag_settings)
            
            # 呼叫 Dify API
            dify_response = self._call_dify_api(
                user_message, 
                search_results, 
                conversation_id,
                baseline_version=baseline.version_name if baseline else "default"
            )
            
            return Response({
                'answer': dify_response['answer'],
                'conversation_id': dify_response['conversation_id'],
                'message_id': dify_response['message_id'],
                'baseline_version': baseline.version_name if baseline else "default",  # 🆕
                'is_dynamic_config': rag_settings.get('stage1', {}).get('loaded_from_db', False),  # 🆕
            })
            
        except Exception as e:
            logger.error(f"❌ 聊天失敗: {str(e)}")
            return Response({
                'error': '聊天失敗，請稍後再試'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_default_rag_settings(self):
        """預設 RAG 設定（Fallback）"""
        return {
            "stage1": {
                "threshold": 0.80,
                "title_weight": 95,
                "content_weight": 5,
                "top_k": 20
            },
            "stage2": {
                "threshold": 0.80,
                "title_weight": 10,
                "content_weight": 90,
                "top_k": 10
            }
        }
```

---

#### **Step 3: 前端 UI 實作**

**檔案**: `frontend/src/pages/benchmark/VersionManagementPage.js` (修改)

**新增「設為 Baseline」按鈕**:
```jsx
import { StarOutlined, StarFilled, SyncOutlined } from '@ant-design/icons';
import { message, Modal } from 'antd';

const VersionManagementPage = () => {
  const [versions, setVersions] = useState([]);
  const [baselineVersion, setBaselineVersion] = useState(null);
  
  // 載入版本列表
  const loadVersions = async () => {
    const response = await api.get('/api/dify-versions/');
    setVersions(response.data);
    
    // 找出當前 Baseline
    const baseline = response.data.find(v => v.is_baseline);
    setBaselineVersion(baseline);
  };
  
  // 🆕 設定 Baseline
  const handleSetBaseline = async (version) => {
    Modal.confirm({
      title: '確認設定 Baseline 版本',
      content: (
        <div>
          <p>確定要將 <strong>{version.version_name}</strong> 設為 Baseline 嗎？</p>
          <p style={{ color: '#ff4d4f', marginTop: 8 }}>
            ⚠️ 此操作會影響 Protocol Assistant 聊天功能，將使用此版本的配置。
          </p>
          {version.rag_settings?.stage1?.use_dynamic_threshold && (
            <p style={{ color: '#1890ff', marginTop: 8 }}>
              🔄 此版本為動態版本，將讀取「搜尋 Threshold 設定」頁面的最新配置。
            </p>
          )}
        </div>
      ),
      okText: '確定設定',
      cancelText: '取消',
      onOk: async () => {
        try {
          const response = await api.post(`/api/dify-versions/${version.id}/set-baseline/`);
          
          message.success(`✅ ${version.version_name} 已設為 Baseline`);
          
          if (response.data.is_dynamic) {
            message.info('🔄 動態配置已刷新，將使用最新的 Threshold 設定', 5);
          }
          
          // 重新載入版本列表
          loadVersions();
          
        } catch (error) {
          console.error('設定 Baseline 失敗:', error);
          message.error('設定 Baseline 失敗，請稍後再試');
        }
      }
    });
  };
  
  // 表格欄位定義
  const columns = [
    {
      title: '版本名稱',
      dataIndex: 'version_name',
      key: 'version_name',
      render: (name, record) => (
        <Space>
          {record.is_baseline && (
            <StarFilled style={{ color: '#faad14', fontSize: 18 }} />
          )}
          <Text strong={record.is_baseline}>{name}</Text>
          {record.rag_settings?.stage1?.use_dynamic_threshold && (
            <Tag color="orange" icon={<SyncOutlined spin />}>動態</Tag>
          )}
        </Space>
      ),
    },
    {
      title: '版本代碼',
      dataIndex: 'version_code',
      key: 'version_code',
      render: (code) => <Text code>{code}</Text>,
    },
    {
      title: '狀態',
      key: 'status',
      width: 150,
      render: (_, record) => (
        <Space direction="vertical" size={4}>
          {record.is_baseline && <Tag color="gold">Baseline</Tag>}
          {record.is_active ? (
            <Tag color="green">啟用</Tag>
          ) : (
            <Tag color="default">停用</Tag>
          )}
        </Space>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 200,
      fixed: 'right',
      render: (_, record) => (
        <Space>
          {/* 🆕 設為 Baseline 按鈕 */}
          {!record.is_baseline && (
            <Tooltip title="設定此版本為 Protocol Assistant 的預設版本">
              <Button
                icon={<StarOutlined />}
                size="small"
                onClick={() => handleSetBaseline(record)}
              >
                設為 Baseline
              </Button>
            </Tooltip>
          )}
          
          {record.is_baseline && (
            <Tag icon={<StarFilled />} color="gold">
              當前 Baseline
            </Tag>
          )}
          
          {/* 其他按鈕... */}
        </Space>
      ),
    },
  ];
  
  return (
    <Card title="版本管理">
      {/* 🆕 顯示當前 Baseline 資訊 */}
      {baselineVersion && (
        <Alert
          message={
            <Space>
              <StarFilled style={{ color: '#faad14' }} />
              <Text strong>當前 Baseline:</Text>
              <Text>{baselineVersion.version_name}</Text>
              {baselineVersion.rag_settings?.stage1?.use_dynamic_threshold && (
                <Tag color="orange" icon={<SyncOutlined />}>動態配置</Tag>
              )}
            </Space>
          }
          type="info"
          showIcon={false}
          style={{ marginBottom: 16 }}
        />
      )}
      
      <Table
        columns={columns}
        dataSource={versions}
        rowKey="id"
        // ...
      />
    </Card>
  );
};
```

---

#### **Step 4: 前端聊天頁面顯示**

**檔案**: `frontend/src/pages/ProtocolAssistantChatPage.js` (修改)

**顯示當前使用的版本**:
```jsx
const ProtocolAssistantChatPage = () => {
  const [currentBaselineVersion, setCurrentBaselineVersion] = useState(null);
  const [isDynamicConfig, setIsDynamicConfig] = useState(false);
  
  // 載入當前 Baseline 版本
  useEffect(() => {
    const loadBaselineInfo = async () => {
      try {
        const response = await api.get('/api/dify-versions/get-baseline/');
        setCurrentBaselineVersion(response.data.version_name);
        setIsDynamicConfig(response.data.is_dynamic);
      } catch (error) {
        console.error('載入 Baseline 版本失敗:', error);
      }
    };
    
    loadBaselineInfo();
  }, []);
  
  return (
    <div className="protocol-assistant-chat-page">
      <Card 
        title={
          <Space>
            <RobotOutlined />
            <span>Protocol Assistant</span>
            {/* 🆕 顯示當前版本 */}
            {currentBaselineVersion && (
              <Tooltip title={
                isDynamicConfig 
                  ? "使用動態配置（跟隨 Threshold 設定頁面）" 
                  : "使用靜態配置"
              }>
                <Tag 
                  color={isDynamicConfig ? "orange" : "blue"}
                  icon={isDynamicConfig ? <SyncOutlined /> : <CheckCircleOutlined />}
                >
                  {currentBaselineVersion}
                </Tag>
              </Tooltip>
            )}
          </Space>
        }
        extra={
          <Space>
            {/* 🆕 重新載入 Baseline 按鈕 */}
            <Tooltip title="重新載入 Baseline 配置">
              <Button 
                icon={<ReloadOutlined />} 
                onClick={() => window.location.reload()}
              >
                重新載入
              </Button>
            </Tooltip>
            <Button icon={<HistoryOutlined />}>歷史記錄</Button>
          </Space>
        }
      >
        {/* 聊天內容... */}
      </Card>
    </div>
  );
};
```

---

### 使用流程示範

#### 情境 1: 切換到動態版本進行生產測試

```
1. 管理員進入 VSA 版本管理頁面
   - 看到版本列表：
     ✅ v1.1 (Baseline)
     ⭐ v1.2 Title Boost
     🔄 v1.2.1 Dynamic

2. 點擊 v1.2.1 的「設為 Baseline」按鈕
   - 系統提示：「此版本為動態版本，將讀取最新的 Threshold 設定」
   - 點擊確定

3. 系統更新 Baseline
   ✅ v1.1 → is_baseline = False
   ✅ v1.2.1 → is_baseline = True
   🔄 清除 ThresholdManager 快取

4. 使用者使用 Protocol Assistant 聊天
   - 自動使用 v1.2.1 的配置
   - 動態讀取最新的 Threshold 設定（80%, 95%, 5%）
   - Title Boost 15% 生效

5. 管理員調整 Threshold 設定
   - 修改為 85%, 90%, 10%
   - 刷新快取（或等待 5 分鐘）

6. 下一次聊天
   - 自動使用新的設定（85%, 90%, 10%）
   - 無需切換版本
```

#### 情境 2: 切換回靜態版本

```
1. 測試發現動態版本不穩定
   - 管理員決定切換回 v1.1

2. 點擊 v1.1 的「設為 Baseline」按鈕
   - 系統提示：「使用靜態配置」
   - 點擊確定

3. 系統更新 Baseline
   ✅ v1.2.1 → is_baseline = False
   ✅ v1.1 → is_baseline = True

4. Protocol Assistant 聊天
   - 使用 v1.1 固定配置（80%, 95%, 5%）
   - 不受 Threshold 設定頁面影響
```

---

### 資料庫變更

**無需修改資料表結構**，`is_baseline` 欄位已存在：
```python
class DifyConfigVersion(models.Model):
    is_baseline = models.BooleanField(default=False)  # ✅ 已存在
```

**需要的資料操作**：
```python
# 確保只有一個版本是 Baseline
with transaction.atomic():
    DifyConfigVersion.objects.filter(is_baseline=True).update(is_baseline=False)
    version.is_baseline = True
    version.save()
```

---

### API 端點總覽

| 端點 | 方法 | 功能 | 權限 |
|-----|------|------|------|
| `/api/dify-versions/{id}/set-baseline/` | POST | 設定指定版本為 Baseline | 管理員 |
| `/api/dify-versions/get-baseline/` | GET | 獲取當前 Baseline 版本和配置 | 所有用戶 |
| `/api/protocol-guide/chat/` | POST | 聊天（自動使用 Baseline 配置） | 所有用戶 |

---

### 檢查清單

#### 開發階段
- [ ] **Backend API**
  - [ ] 新增 `set_baseline` action
  - [ ] 新增 `get_baseline` action
  - [ ] 修改 Protocol Assistant `chat` action
  - [ ] 添加日誌記錄
  - [ ] 撰寫單元測試

- [ ] **Frontend UI**
  - [ ] 版本管理頁面添加「設為 Baseline」按鈕
  - [ ] 顯示當前 Baseline 標記（⭐）
  - [ ] 聊天頁面顯示當前使用版本
  - [ ] 添加確認對話框
  - [ ] 錯誤處理和用戶反饋

#### 測試階段
- [ ] **功能測試**
  - [ ] 切換到靜態版本（v1.1, v1.2）
  - [ ] 切換到動態版本（v1.2.1）
  - [ ] 聊天功能使用正確的 Baseline 配置
  - [ ] 動態版本讀取最新 Threshold 設定

- [ ] **整合測試**
  - [ ] 切換版本 → 調整 Threshold → 聊天測試
  - [ ] 多用戶並行聊天（使用相同 Baseline）
  - [ ] 快取刷新機制驗證

#### 部署階段
- [ ] 確認所有版本都有 `is_baseline` 欄位
- [ ] 設定初始 Baseline 版本（v1.1）
- [ ] 驗證 API 權限設定
- [ ] 檢查前端路由和權限

---

### 優點與注意事項

#### ✅ 優點
1. **靈活切換**：管理員可在 UI 快速切換版本，無需修改程式碼
2. **動態配置**：支援動態版本（v1.2.1），即時反映 Threshold 設定變更
3. **生產測試**：可在生產環境快速測試不同版本效果
4. **向後兼容**：不影響現有批量測試功能
5. **可追蹤**：聊天回應包含使用的版本資訊

#### ⚠️ 注意事項
1. **全局影響**：切換 Baseline 會影響所有 Protocol Assistant 用戶
2. **需要權限**：只有管理員可以切換 Baseline
3. **快取延遲**：動態版本有 5 分鐘快取（可手動刷新）
4. **測試建議**：建議先在測試環境驗證新版本，再設為生產 Baseline
5. **回退機制**：如果新版本有問題，可立即切換回舊版本

---

### 風險評估

| 風險 | 影響 | 緩解措施 | 優先級 |
|-----|------|---------|--------|
| 誤切換版本 | 生產環境使用錯誤配置 | 添加確認對話框、記錄操作日誌 | 🟡 中 |
| 動態配置不穩定 | 聊天結果不一致 | 測試結果記錄實際配置、支援快速回退 | 🟡 中 |
| 權限控制不足 | 非管理員誤操作 | 使用 `IsAdminUser` 權限檢查 | 🟢 低 |

---

### 實作優先級

**Phase 1（高優先級）**：
1. ✅ Backend API：`set_baseline` 和 `get_baseline`
2. ✅ Protocol Assistant 聊天整合
3. ✅ 基本日誌記錄

**Phase 2（中優先級）**：
4. ✅ Frontend UI：版本管理頁面按鈕
5. ✅ 聊天頁面顯示當前版本
6. ✅ 確認對話框和用戶反饋

**Phase 3（可選）**：
7. 🔄 進階功能：版本切換歷史記錄
8. 🔄 監控告警：Baseline 切換通知
9. 🔄 AB 測試：部分用戶使用不同版本

---

**文檔狀態**: ✅ 規劃完成（含 Baseline 切換功能）  
**等待**: 用戶確認後開始實作
