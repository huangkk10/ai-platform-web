# 📦 Archived Tests - 歷史歸檔測試

## 📋 說明

此目錄包含已被新版本取代但仍保留作為歷史參考的測試檔案。

⚠️ **這些測試不再主動維護，僅供參考。**

---

## 📁 目錄結構

### `context_window/` - 上下文視窗歷史測試

已被 `tests/test_context/test_context_window_v2.py` 取代：

- **`test_context_window_expansion.py`** (9.4 KB)
  - 初期上下文擴展測試
  - 歸檔日期：2025-11-13
  - 取代原因：功能已整合到 V2

- **`test_context_window_regression.py`** (3.1 KB)
  - 早期回歸測試
  - 歸檔日期：2025-11-13
  - 取代原因：V2 包含更完整的回歸測試

- **`test_context_window_simple.py`** (16 KB)
  - 簡化版上下文測試
  - 歸檔日期：2025-11-13
  - 取代原因：V2 提供更全面的測試覆蓋

---

### `analysis/` - 分析工具歷史檔案

- **`analyze_unh_iol_search_failure.py`** (5.8 KB)
  - UNH IOL 搜尋失敗分析工具
  - 歸檔日期：2025-11-13
  - 歸檔原因：問題已修復，保留作為故障排除參考

---

## 🔍 如何使用歸檔檔案

### 查看歷史實作

```bash
# 查看舊版本的實作方式
cat tests/archived/context_window/test_context_window_expansion.py
```

### 比較新舊版本

```bash
# 比較 V1 和 V2 的差異
diff tests/archived/context_window/test_context_window_simple.py \
     tests/test_context/test_context_window_v2.py
```

### Git 歷史追蹤

```bash
# 查看檔案的完整歷史
git log --follow tests/archived/context_window/test_context_window_expansion.py

# 查看特定版本
git show <commit_hash>:backend/test_context_window_expansion.py
```

---

## ⚠️ 注意事項

1. **不建議執行**：這些測試可能依賴舊的 API 或資料結構
2. **僅供參考**：用於理解功能演進和設計決策
3. **不保證可用**：環境變更可能導致無法執行
4. **版本追蹤**：使用 Git 查看完整演進歷史

---

## 📜 歸檔政策

**何時歸檔測試**：
- ✅ 功能已被新版本完全取代
- ✅ 保留對理解系統演進有價值
- ✅ 可能作為未來重構的參考
- ❌ 不刪除，保留 Git 歷史

**歸檔流程**：
```bash
# 使用 git mv 保留版本歷史
git mv backend/old_test.py tests/archived/category/
git commit -m "chore: archive old_test.py (replaced by new_test_v2.py)"
```

---

## 🗂️ 歸檔清單

| 檔案 | 原路徑 | 歸檔日期 | 取代者 |
|------|-------|---------|--------|
| test_context_window_expansion.py | backend/ | 2025-11-13 | test_context_window_v2.py |
| test_context_window_regression.py | backend/ | 2025-11-13 | test_context_window_v2.py |
| test_context_window_simple.py | backend/ | 2025-11-13 | test_context_window_v2.py |
| analyze_unh_iol_search_failure.py | backend/ | 2025-11-13 | - (問題已修復) |

---

**創建日期**：2025-11-13  
**維護者**：AI Platform Team  
**用途**：歷史參考、學習演進、故障排除
