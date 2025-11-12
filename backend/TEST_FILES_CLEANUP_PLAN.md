# 🗂️ Backend 測試檔案整理計劃

## 📋 現況分析

**backend/ 目錄下共有 40 個測試/工具檔案**（共約 270 KB）

---

## 🎯 整理策略

### ✅ **保留並移動到 tests/ 的檔案**（有價值的測試）

#### 1. **綜合系統測試** → `tests/test_system/`
- ✅ `test_comprehensive_protocol_system.py` (23K) - **最新綜合測試**
  - 目標：`tests/test_system/test_comprehensive_protocol_system.py`
  - 原因：完整的系統驗證，涵蓋 6 大測試組

#### 2. **搜尋功能測試** → `tests/test_search/`
- ✅ `test_protocol_search_mode.py` (17K) - 搜尋模式測試
- ✅ `test_explicit_search_mode.py` (7.8K) - 顯式搜尋模式
- ✅ `test_crystaldiskmark_search.py` (1.9K) - CrystalDiskMark 搜尋
- ✅ `test_full_search_pipeline.py` (4.4K) - 完整搜尋管道
- ✅ `test_search_version_in_container.py` (8.2K) - 容器內版本測試
- ✅ `test_v1_v2_comparison.py` (5.0K) - V1/V2 對比測試

#### 3. **Two-Tier 機制測試** → `tests/test_two_tier/`
- ✅ `test_protocol_two_tier_mechanism.py` (18K) - Protocol 兩階段
- ✅ `test_rvt_two_tier_mechanism.py` (12K) - RVT 兩階段
- ✅ `test_two_tier_mechanism.py` (22K) - 通用兩階段測試

#### 4. **上下文視窗測試** → `tests/test_context/`
- ✅ `test_context_window_v2.py` (26K) - V2 上下文視窗（最新）
- ⚠️ `test_context_window_expansion.py` (9.4K) - 可歸檔
- ⚠️ `test_context_window_regression.py` (3.1K) - 可歸檔
- ⚠️ `test_context_window_simple.py` (16K) - 可歸檔

#### 5. **對話管理測試** → `tests/test_conversation/`
- ✅ `test_conversation_history_pollution.py` (17K) - 對話歷史污染測試
- ✅ `test_dify_memory_interval_effect.py` (13K) - Dify 記憶間隔測試
- ✅ `test_protocol_crystaldiskmark_stability.py` (19K) - 穩定性測試

#### 6. **整合測試** → `tests/test_integration/`
- ✅ `test_web_frontend_chat.py` (8.4K) - 前端聊天整合
- ✅ `test_dify_chat_with_knowledge.py` (3.6K) - Dify 知識庫整合
- ✅ `verify_integration.py` (6.4K) - 整合驗證

#### 7. **特定功能測試** → `tests/test_features/`
- ✅ `test_uncertainty_detection_scenarios.py` (9.5K) - 不確定性檢測
- ✅ `test_fallback_combined_answer.py` (4.8K) - 降級回答機制
- ✅ `test_signals_verification.py` (5.4K) - 信號驗證
- ✅ `test_keyword_cleaning.py` (4.6K) - 關鍵字清理
- ✅ `test_keyword_score_improvement.py` (4.0K) - 關鍵字評分改進

#### 8. **向量/標題測試** → `tests/test_vectors/`
- ✅ `test_title_in_vector.py` (6.4K) - 標題向量測試
- ✅ `test_unh_iol_search.py` (2.5K) - UNH IOL 搜尋
- ✅ `test_unh_iol_score_detail.py` (4.3K) - UNH IOL 評分詳情
- ✅ `test_full_document_expansion.py` (2.7K) - 完整文檔展開

---

### 🗄️ **歸檔到 tests/archived/ 的檔案**（歷史參考）

#### 歸檔原因：功能已被新測試取代，但保留作為歷史參考

- 📦 `test_context_window_expansion.py` → `tests/archived/context_window/`
- 📦 `test_context_window_regression.py` → `tests/archived/context_window/`
- 📦 `test_context_window_simple.py` → `tests/archived/context_window/`
- 📦 `analyze_unh_iol_search_failure.py` → `tests/archived/analysis/`

---

### 🛠️ **保留在 backend/ 的工具檔案**（管理腳本）

#### 資料庫維護工具 → 保留在 `backend/`
- ✅ `fix_document_ids.py` (4.5K) - 修復文檔 ID
- ✅ `fix_unh_iol_vectors.py` (6.7K) - 修復 UNH IOL 向量
- ✅ `init_threshold_settings.py` (3.5K) - 初始化閾值設定

#### 向量生成工具 → 保留在 `backend/`
- ✅ `generate_all_protocol_sections.py` (3.4K) - 生成所有段落
- ✅ `generate_crystaldiskmark_sections.py` (1.8K) - 生成 CrystalDiskMark 段落
- ✅ `regenerate_cup_sections.py` (3.6K) - 重新生成 CUP 段落
- ✅ `regenerate_section_multi_vectors.py` (5.9K) - 重新生成多向量
- ✅ `regenerate_section_multi_vectors_v2.py` (4.9K) - 重新生成多向量 V2
- ✅ `regenerate_unh_iol_multi_vectors.py` (6.1K) - 重新生成 UNH IOL 向量

#### 資料創建工具 → 保留在 `backend/`
- ✅ `test_new_protocol_guide_creation.py` (5.4K) - 創建新 Protocol Guide

---

### ❌ **可以安全刪除的檔案**（已被取代或不再需要）

無！所有檔案都有保留價值，只是需要重新組織。

---

## 📁 建議的新目錄結構

```
tests/
├── test_system/                    # 綜合系統測試
│   └── test_comprehensive_protocol_system.py
├── test_search/                    # 搜尋功能測試
│   ├── test_protocol_search_mode.py
│   ├── test_explicit_search_mode.py
│   ├── test_crystaldiskmark_search.py
│   ├── test_full_search_pipeline.py
│   ├── test_search_version_in_container.py
│   └── test_v1_v2_comparison.py
├── test_two_tier/                  # Two-Tier 機制測試
│   ├── test_protocol_two_tier_mechanism.py
│   ├── test_rvt_two_tier_mechanism.py
│   └── test_two_tier_mechanism.py
├── test_context/                   # 上下文視窗測試
│   └── test_context_window_v2.py
├── test_conversation/              # 對話管理測試
│   ├── test_conversation_history_pollution.py
│   ├── test_dify_memory_interval_effect.py
│   └── test_protocol_crystaldiskmark_stability.py
├── test_integration/               # 整合測試
│   ├── test_web_frontend_chat.py
│   ├── test_dify_chat_with_knowledge.py
│   └── verify_integration.py
├── test_features/                  # 特定功能測試
│   ├── test_uncertainty_detection_scenarios.py
│   ├── test_fallback_combined_answer.py
│   ├── test_signals_verification.py
│   ├── test_keyword_cleaning.py
│   └── test_keyword_score_improvement.py
├── test_vectors/                   # 向量/標題測試
│   ├── test_title_in_vector.py
│   ├── test_unh_iol_search.py
│   ├── test_unh_iol_score_detail.py
│   └── test_full_document_expansion.py
└── archived/                       # 歷史歸檔
    ├── context_window/
    │   ├── test_context_window_expansion.py
    │   ├── test_context_window_regression.py
    │   └── test_context_window_simple.py
    └── analysis/
        └── analyze_unh_iol_search_failure.py

backend/                            # 資料庫管理工具
├── fix_document_ids.py
├── fix_unh_iol_vectors.py
├── init_threshold_settings.py
├── generate_all_protocol_sections.py
├── generate_crystaldiskmark_sections.py
├── regenerate_cup_sections.py
├── regenerate_section_multi_vectors.py
├── regenerate_section_multi_vectors_v2.py
├── regenerate_unh_iol_multi_vectors.py
└── test_new_protocol_guide_creation.py
```

---

## 🎯 執行計劃

### 階段 1：創建目錄結構 ✅
```bash
cd /home/user/codes/ai-platform-web/tests
mkdir -p test_system test_search test_two_tier test_context test_conversation
mkdir -p test_integration test_features test_vectors
mkdir -p archived/context_window archived/analysis
```

### 階段 2：移動測試檔案 ⏳
```bash
# 使用 git mv 保留版本歷史
cd /home/user/codes/ai-platform-web

# 系統測試
git mv backend/test_comprehensive_protocol_system.py tests/test_system/

# 搜尋測試
git mv backend/test_protocol_search_mode.py tests/test_search/
git mv backend/test_explicit_search_mode.py tests/test_search/
git mv backend/test_crystaldiskmark_search.py tests/test_search/
git mv backend/test_full_search_pipeline.py tests/test_search/
git mv backend/test_search_version_in_container.py tests/test_search/
git mv backend/test_v1_v2_comparison.py tests/test_search/

# Two-Tier 測試
git mv backend/test_protocol_two_tier_mechanism.py tests/test_two_tier/
git mv backend/test_rvt_two_tier_mechanism.py tests/test_two_tier/
git mv backend/test_two_tier_mechanism.py tests/test_two_tier/

# 上下文測試
git mv backend/test_context_window_v2.py tests/test_context/

# 對話測試
git mv backend/test_conversation_history_pollution.py tests/test_conversation/
git mv backend/test_dify_memory_interval_effect.py tests/test_conversation/
git mv backend/test_protocol_crystaldiskmark_stability.py tests/test_conversation/

# 整合測試
git mv backend/test_web_frontend_chat.py tests/test_integration/
git mv backend/test_dify_chat_with_knowledge.py tests/test_integration/
git mv backend/verify_integration.py tests/test_integration/

# 功能測試
git mv backend/test_uncertainty_detection_scenarios.py tests/test_features/
git mv backend/test_fallback_combined_answer.py tests/test_features/
git mv backend/test_signals_verification.py tests/test_features/
git mv backend/test_keyword_cleaning.py tests/test_features/
git mv backend/test_keyword_score_improvement.py tests/test_features/

# 向量測試
git mv backend/test_title_in_vector.py tests/test_vectors/
git mv backend/test_unh_iol_search.py tests/test_vectors/
git mv backend/test_unh_iol_score_detail.py tests/test_vectors/
git mv backend/test_full_document_expansion.py tests/test_vectors/

# 歸檔
git mv backend/test_context_window_expansion.py tests/archived/context_window/
git mv backend/test_context_window_regression.py tests/archived/context_window/
git mv backend/test_context_window_simple.py tests/archived/context_window/
git mv backend/analyze_unh_iol_search_failure.py tests/archived/analysis/
```

### 階段 3：更新 README 文檔 ⏳
```bash
# 創建各目錄的 README
echo "# 🧪 System Tests" > tests/test_system/README.md
echo "# 🔍 Search Tests" > tests/test_search/README.md
# ... 其他目錄
```

### 階段 4：驗證移動後的測試 ⏳
```bash
# 確認測試仍可正常執行
docker exec ai-django python -m pytest tests/test_system/
docker exec ai-django python -m pytest tests/test_search/
```

---

## 📊 整理效果

| 項目 | 整理前 | 整理後 |
|------|--------|--------|
| backend/ 測試檔案 | 40 個 (270 KB) | 10 個工具檔案 (40 KB) |
| tests/ 測試檔案 | 分散各處 | 7 個分類目錄 + 歸檔 |
| 檔案組織性 | ⚠️ 混亂 | ✅ 清晰分類 |
| 可維護性 | ⚠️ 困難 | ✅ 容易 |

---

## ✅ 優點

1. **清晰分類**：測試按功能分組，易於查找
2. **保留歷史**：使用 `git mv` 保留版本歷史
3. **工具分離**：管理工具留在 backend/，測試移到 tests/
4. **歸檔機制**：舊測試歸檔而非刪除，保留參考價值
5. **易於擴展**：新測試有明確的放置位置

---

## 🎯 建議執行時機

**現在！** 因為：
- ✅ 核心功能已穩定（搜尋、Two-Tier 機制都已測試通過）
- ✅ 測試檔案數量已達到需要整理的臨界點
- ✅ 使用 Git 分支可以安全進行重構
- ✅ 整理後的結構更利於團隊協作

---

**創建日期**: 2025-11-13  
**狀態**: 📋 計劃完成，等待執行  
**預計執行時間**: 15-20 分鐘
