# 🧪 測試腳本整理日誌

## 📅 整理日期
2025-11-25

## 🎯 整理目的
將專案根目錄的測試腳本、驗證腳本和修復腳本移動到 `tests/` 和 `scripts/` 目錄的適當分類中，保持根目錄整潔。

---

## 📋 文件移動清單

### 🔍 搜尋相關測試 (`tests/test_search/`)

| 原檔名 | 新位置 | 內容描述 |
|--------|--------|---------|
| `test_unified_weights_modes.py` | `tests/test_search/` | 統一權重模式測試 |
| `test_two_stage_weights_validation.py` | `tests/test_search/` | 兩階段權重驗證測試 |
| `test_two_stage_search.py` | `tests/test_search/` | 兩階段搜尋功能測試 |
| `test_stage2_full_search.sh` | `tests/test_search/` | 第二階段完整搜尋測試 |

---

### 🖥️ 系統測試 (`tests/test_system/`)

| 原檔名 | 新位置 | 內容描述 |
|--------|--------|---------|
| `verify_threshold.sh` | `tests/test_system/` | 驗證向量搜尋閾值設定 |
| `test_threshold_settings.sh` | `tests/test_system/` | 閾值設定測試腳本 |

---

### 🌐 API 測試 (`tests/test_api/`)

| 原檔名 | 新位置 | 內容描述 |
|--------|--------|---------|
| `test_benchmark_api_curl.sh` | `tests/test_api/` | Benchmark API 測試（curl） |
| `test_batch_api.py` | `tests/test_api/` | 批量 API 測試 |

---

### 🤖 Dify 整合測試 (`tests/test_dify_integration/`)

| 原檔名 | 新位置 | 內容描述 |
|--------|--------|---------|
| `test_dify_multithreading.py` | `tests/test_dify_integration/` | Dify 多線程測試 |

---

### 💬 對話測試 (`tests/test_conversation/`)

| 原檔名 | 新位置 | 內容描述 |
|--------|--------|---------|
| `test_protocol_conversation_recording.sh` | `tests/test_conversation/` | Protocol 對話記錄驗證 |

---

### 🔗 整合測試 (`tests/test_integration/`)

| 原檔名 | 新位置 | 內容描述 |
|--------|--------|---------|
| `test_stage_final.py` | `tests/test_integration/` | 最終階段整合測試 |

---

### 📦 歸檔腳本 (`scripts/archived/`)

| 原檔名 | 新位置 | 內容描述 | 狀態 |
|--------|--------|---------|------|
| `fix_protocol_image_threshold.py` | `scripts/archived/` | 修復 Protocol 圖片閾值（一次性） | ✅ 已完成 |
| `fix_document_ids.py` | `scripts/archived/` | 修復向量 document_id 欄位（一次性） | ✅ 已完成 |

---

### 🗑️ 已刪除腳本

| 原檔名 | 刪除理由 |
|--------|---------|
| `verify_test_reorganization.sh` | 測試重組已完成，不再需要 |
| `test_query_fix.py` | 臨時 bug 修復測試，已完成 |

---

## 📊 整理統計

- **總共處理檔案**: 15 個
- **移動到 tests/test_search/**: 4 個
- **移動到 tests/test_system/**: 2 個
- **移動到 tests/test_api/**: 2 個
- **移動到 tests/test_dify_integration/**: 1 個
- **移動到 tests/test_conversation/**: 1 個
- **移動到 tests/test_integration/**: 1 個
- **歸檔到 scripts/archived/**: 2 個
- **已刪除**: 2 個

---

## ✅ 整理效果

### 移動前（根目錄散亂）
```
❌ verify_threshold.sh
❌ verify_test_reorganization.sh
❌ test_unified_weights_modes.py
❌ test_two_stage_weights_validation.py
❌ test_two_stage_search.py
❌ test_threshold_settings.sh
❌ test_stage2_full_search.sh
❌ test_stage_final.py
❌ test_query_fix.py
❌ test_protocol_conversation_recording.sh
❌ test_dify_multithreading.py
❌ test_benchmark_api_curl.sh
❌ test_batch_api.py
❌ fix_protocol_image_threshold.py
❌ fix_document_ids.py
```

### 移動後（結構化）
```
✅ tests/
   ├── test_search/
   │   ├── test_unified_weights_modes.py
   │   ├── test_two_stage_weights_validation.py
   │   ├── test_two_stage_search.py
   │   └── test_stage2_full_search.sh
   │
   ├── test_system/
   │   ├── verify_threshold.sh
   │   └── test_threshold_settings.sh
   │
   ├── test_api/
   │   ├── test_benchmark_api_curl.sh
   │   └── test_batch_api.py
   │
   ├── test_dify_integration/
   │   └── test_dify_multithreading.py
   │
   ├── test_conversation/
   │   └── test_protocol_conversation_recording.sh
   │
   └── test_integration/
       └── test_stage_final.py

✅ scripts/
   └── archived/
       ├── fix_protocol_image_threshold.py
       └── fix_document_ids.py
```

---

## 🎯 測試腳本使用指南

### 🔍 搜尋相關測試

**1. 統一權重模式測試**
```bash
docker exec ai-django python tests/test_search/test_unified_weights_modes.py
```

**2. 兩階段權重驗證**
```bash
docker exec ai-django python tests/test_search/test_two_stage_weights_validation.py
```

**3. 兩階段搜尋測試**
```bash
docker exec ai-django python tests/test_search/test_two_stage_search.py
```

**4. 第二階段完整搜尋**
```bash
bash tests/test_search/test_stage2_full_search.sh
```

---

### 🖥️ 系統測試

**1. 驗證閾值設定**
```bash
bash tests/test_system/verify_threshold.sh
```

**2. 閾值設定測試**
```bash
bash tests/test_system/test_threshold_settings.sh
```

---

### 🌐 API 測試

**1. Benchmark API 測試**
```bash
bash tests/test_api/test_benchmark_api_curl.sh
```

**2. 批量 API 測試**
```bash
docker exec ai-django python tests/test_api/test_batch_api.py
```

---

### 🤖 Dify 整合測試

**多線程測試**
```bash
docker exec ai-django python tests/test_dify_integration/test_dify_multithreading.py
```

---

### 💬 對話測試

**Protocol 對話記錄驗證**
```bash
bash tests/test_conversation/test_protocol_conversation_recording.sh
```

---

### 🔗 整合測試

**最終階段測試**
```bash
docker exec ai-django python tests/test_integration/test_stage_final.py
```

---

## 📦 歸檔腳本說明

### `scripts/archived/fix_protocol_image_threshold.py`
**用途**：修復 Protocol Assistant 圖片顯示問題（調整閾值到 0.85）
**狀態**：✅ 已完成，僅供參考
**執行**：`docker exec ai-django python scripts/archived/fix_protocol_image_threshold.py`

### `scripts/archived/fix_document_ids.py`
**用途**：修復向量記錄的 document_id 和 document_title 欄位
**狀態**：✅ 已完成，僅供參考
**執行**：`docker exec ai-django python scripts/archived/fix_document_ids.py`

---

## 📝 後續維護建議

### 1. **新測試腳本規範**
- 所有新測試應直接創建在對應的 `tests/` 子目錄中
- 避免在根目錄創建測試腳本

### 2. **測試腳本命名規範**
- Python 測試：`test_<feature_name>.py`
- Shell 測試：`test_<feature_name>.sh`
- 驗證腳本：`verify_<feature_name>.sh`

### 3. **目錄分類標準**
| 目錄 | 用途 | 範例 |
|------|------|------|
| `tests/test_search/` | 搜尋功能測試 | 權重測試、兩階段搜尋測試 |
| `tests/test_system/` | 系統配置驗證 | 閾值驗證、系統設定測試 |
| `tests/test_api/` | API 端點測試 | REST API 測試、curl 測試 |
| `tests/test_dify_integration/` | Dify 整合測試 | AI 助手整合測試 |
| `tests/test_conversation/` | 對話功能測試 | 對話記錄、持久化測試 |
| `tests/test_integration/` | 整合測試 | 端到端測試、階段測試 |
| `scripts/archived/` | 一次性腳本歸檔 | 修復腳本、遷移腳本 |

### 4. **定期檢查**
- 每月檢查根目錄是否有新的待整理測試腳本
- 及時移動到適當的分類目錄

### 5. **歸檔原則**
- 一次性修復腳本：移動到 `scripts/archived/`
- 臨時測試腳本：完成後刪除或歸檔
- 長期測試腳本：保留在 `tests/` 對應子目錄

---

## 🔍 根目錄剩餘腳本

### 監控腳本（建議保留在根目錄）
- `monitor_test_progress.sh` - 測試進度監控
- `quick_test_validation.sh` - 快速驗證測試

這些是常用的監控和快速驗證腳本，建議保留在根目錄以方便快速執行。

---

## ✅ 整理完成

**執行者**: AI Assistant  
**完成時間**: 2025-11-25  
**狀態**: ✅ 全部完成  
**影響**: 測試腳本結構化，根目錄更加整潔

---

## 📚 相關文檔

- **文檔整理日誌**: `docs/DOCUMENT_REORGANIZATION_LOG.md`
- **測試文檔索引**: `tests/README.md`
- **測試指南**: `docs/testing/`

---

**備註**: 
1. 本次整理不影響任何測試功能運作，僅重新組織文件結構
2. 所有移動的測試腳本保持完整內容不變
3. Git 歷史記錄保留完整的變更軌跡
4. 歸檔的修復腳本僅供參考，無需再次執行
