# VSA 測試案例顯示問題修復報告

## 問題描述

**現象**：VSA 測試案例頁面只顯示 20 題，但預期應該顯示 55 題

**截圖顯示**：
- 總測試案例：20
- 啟用中：20
- 已停用：0

## 問題分析

### 1. 資料庫狀態確認

✅ **資料庫中確實有 55 筆測試案例**

```sql
SELECT COUNT(*) FROM dify_benchmark_test_case WHERE is_active = true;
-- 結果：55 筆
```

測試案例分類分布：
| 分類 | 數量 |
|------|------|
| 問題排除 | 3 |
| 安裝設定 | 3 |
| 專案概述 | 1 |
| 專案流程 | 1 |
| 專案規格 | 2 |
| 工具對比 | 4 |
| 文章標題查詢 | 5 |
| 測試執行 | 7 |
| 測試工具 | 11 |
| 測試工具進階 | 1 |
| 測試準備 | 8 |
| 測試策略 | 2 |
| 測試設定 | 1 |
| 測試開發 | 1 |
| 結果分析 | 3 |
| 資源路徑 | 2 |
| **總計** | **55** |

### 2. 根本原因

❌ **Django REST Framework 的預設分頁設定限制**

在 `backend/ai_platform/settings.py` 中：
```python
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,  # ← 這裡限制每頁只返回 20 筆資料
}
```

雖然前端發送 `page_size: 1000` 的請求，但因為 ViewSet 沒有明確覆蓋分頁設定，所以使用了全域的 20 筆限制。

## 解決方案

### 方案 1：修改全域 PAGE_SIZE（已實施）

**檔案**：`backend/ai_platform/settings.py`

**修改內容**：
```python
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100,  # 從 20 增加到 100
}
```

**優點**：一次性解決所有 API 的分頁問題
**缺點**：可能影響其他 API 的效能（如果有大量資料）

### 方案 2：在 ViewSet 中禁用分頁（已實施，推薦）

**檔案**：`backend/api/views/viewsets/dify_benchmark_viewsets.py`

**修改內容**：

#### DifyBenchmarkTestCaseViewSet
```python
class DifyBenchmarkTestCaseViewSet(viewsets.ModelViewSet):
    queryset = DifyBenchmarkTestCase.objects.all().order_by('test_class_name', 'id')
    serializer_class = DifyBenchmarkTestCaseSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None  # ← 新增：禁用分頁，返回所有測試案例
```

#### DifyConfigVersionViewSet
```python
class DifyConfigVersionViewSet(viewsets.ModelViewSet):
    queryset = DifyConfigVersion.objects.all().order_by('-created_at')
    serializer_class = DifyConfigVersionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None  # ← 新增：禁用分頁，返回所有版本
```

**優點**：
- 針對性解決問題，不影響其他 API
- 測試案例和版本數量不會太多，適合一次性返回所有資料
- 前端不需要實作分頁邏輯

**缺點**：需要逐個 ViewSet 設定

## 驗證步驟

### 1. 重啟 Django 容器
```bash
docker restart ai-django
```

### 2. 驗證資料庫
```bash
docker exec ai-django python manage.py shell -c \
  "from api.models import DifyBenchmarkTestCase; \
   print(f'總計: {DifyBenchmarkTestCase.objects.count()} 筆')"
```

預期輸出：
```
資料庫中共有 55 筆測試案例
啟用的測試案例: 55 筆
```

### 3. 測試前端

1. 重新整理瀏覽器（清除快取）：`Ctrl + Shift + R` 或 `Cmd + Shift + R`
2. 進入 VSA 測試案例頁面
3. 確認顯示：
   - 總測試案例：**55**
   - 啟用中：**55**
   - 表格中顯示 55 筆資料

### 4. 瀏覽器開發者工具檢查

打開 Network 面板，查看 API 請求：
```
GET /api/dify-benchmark/test-cases/
```

回應應該是一個包含 55 個元素的陣列（不是分頁物件）。

## 預期結果

修復後，VSA 測試案例頁面應該顯示：

```
總測試案例      啟用中        已停用
   55           55            0
```

表格中應該可以看到所有 55 筆測試案例，分布在以下類別：
- 測試工具：11 題（最多）
- 測試準備：8 題
- 測試執行：7 題
- 文章標題查詢：5 題
- 工具對比：4 題
- 其他類別：各 1-3 題

## 相關檔案

- `backend/ai_platform/settings.py` - Django 全域設定
- `backend/api/views/viewsets/dify_benchmark_viewsets.py` - Dify Benchmark ViewSets
- `frontend/src/pages/dify-benchmark/DifyTestCasePage.js` - 前端測試案例頁面
- `frontend/src/services/difyBenchmarkApi.js` - API 服務層

## 注意事項

1. **快取問題**：修改後需要重新整理瀏覽器（硬重新整理）
2. **其他 API**：如果其他 API 也遇到類似問題，可以使用相同方式修復
3. **效能考量**：如果未來測試案例超過 1000 筆，可能需要重新啟用分頁

## 後續建議

1. **前端優化**：對於 55 筆資料，前端表格可以考慮：
   - 虛擬滾動（Virtual Scrolling）
   - 客戶端分頁
   - 資料過濾和搜尋優化

2. **監控**：定期檢查測試案例數量，確保在合理範圍內

3. **文檔更新**：在開發文檔中記錄此問題，避免未來遇到類似情況

## 修復日期

**日期**：2025-11-25
**修復者**：AI Assistant
**狀態**：✅ 已完成

---

**總結**：問題的根本原因是 Django REST Framework 的預設分頁設定（PAGE_SIZE = 20），透過在相關 ViewSet 中設定 `pagination_class = None` 即可解決。資料庫中確實有完整的 55 筆測試案例。
