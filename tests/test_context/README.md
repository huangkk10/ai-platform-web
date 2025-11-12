# 🪟 Context Window Tests - 上下文視窗測試

## 📋 目的

驗證 AI 對話的上下文視窗管理和擴展功能。

## 📁 當前測試檔案

### `test_context_window_v2.py` (26 KB)
**V2 上下文視窗測試（最新版本）**

**測試內容**：
- 上下文視窗大小管理
- 歷史對話保留機制
- 上下文擴展策略
- 記憶體使用優化

**執行方式**：
```bash
docker exec ai-django python tests/test_context/test_context_window_v2.py
```

---

## 📦 歸檔的測試檔案

以下檔案已移至 `tests/archived/context_window/`：

- `test_context_window_expansion.py` (9.4 KB) - 初期擴展測試
- `test_context_window_regression.py` (3.1 KB) - 回歸測試
- `test_context_window_simple.py` (16 KB) - 簡化版本測試

**歸檔原因**：功能已被 V2 版本取代，保留作為歷史參考。

---

## 🎯 測試重點

1. **上下文長度限制**
   - Token 數量控制
   - 自動截斷機制

2. **上下文質量**
   - 相關性保持
   - 關鍵資訊不遺失

3. **性能優化**
   - 記憶體使用
   - 回應速度

---

**創建日期**：2025-11-13  
**維護者**：AI Platform Team  
**狀態**：✅ V2 版本為主要測試
