# 🔍 Search Tests - 搜尋功能測試

## 📋 目的

驗證 Protocol Assistant 的各種搜尋功能和模式。

## 📁 測試檔案

### `test_protocol_search_mode.py` (17 KB)
**Protocol Assistant 搜尋模式完整測試**

**測試內容**：
- 搜尋模式參數傳遞
- auto / section_only / document_only 模式
- 閾值降級機制驗證

---

### `test_explicit_search_mode.py` (7.8 KB)
**顯式搜尋模式測試**

**測試內容**：
- 明確指定搜尋模式的行為
- 模式切換的正確性

---

### `test_crystaldiskmark_search.py` (1.9 KB)
**CrystalDiskMark 搜尋功能測試**

**測試內容**：
- CrystalDiskMark 相關查詢
- 向量搜尋準確度
- 關鍵字匹配

---

### `test_full_search_pipeline.py` (4.4 KB)
**完整搜尋管道測試**

**測試內容**：
- 從查詢到結果的完整流程
- 多層次搜尋機制
- 結果排序和過濾

---

### `test_search_version_in_container.py` (8.2 KB)
**容器內搜尋版本測試**

**測試內容**：
- V1 vs V2 搜尋版本對比
- 容器環境中的搜尋功能

---

### `test_v1_v2_comparison.py` (5.0 KB)
**V1/V2 搜尋版本對比測試**

**測試內容**：
- 基礎搜尋 (V1) vs 上下文搜尋 (V2)
- 性能和準確度比較
- 適用場景分析

---

## 🎯 執行所有搜尋測試

```bash
# 執行所有搜尋測試
docker exec ai-django python -m pytest tests/test_search/ -v

# 執行特定測試
docker exec ai-django python tests/test_search/test_protocol_search_mode.py
```

---

**創建日期**：2025-11-13  
**維護者**：AI Platform Team  
**相關文檔**：`/docs/vector-search/vector-search-guide.md`
