# Test Cases 分頁問題修復報告

**問題發現時間**: 2025-11-23 14:50  
**修復完成時間**: 2025-11-23 15:00  
**問題類型**: 資料分頁限制

---

## 🐛 問題描述

### 現象
- **資料庫實際數量**: 55 個測試案例
- **前端顯示數量**: 只顯示 20 個測試案例
- **統計卡片顯示**: 「總測試案例 20」（應該是 55）

### 用戶截圖證據
```
統計卡片：
- 總測試案例: 20 ❌ (實際應該是 55)
- 測試類別: 0
- 簡單題: 6
- 困難題: 3
```

### 資料庫驗證
```sql
SELECT COUNT(*) FROM benchmark_test_case;
-- 結果: 55 個
```

---

## 🔍 根本原因分析

### 問題 1: Django REST Framework 預設分頁
**原始程式碼** (`backend/api/views/viewsets/benchmark_viewsets.py`):
```python
class BenchmarkTestCaseViewSet(viewsets.ModelViewSet):
    queryset = BenchmarkTestCase.objects.all().order_by('-created_at')
    serializer_class = BenchmarkTestCaseSerializer
    permission_classes = [permissions.IsAuthenticated]
    # ❌ 缺少 pagination_class 設定
```

**問題**:
- 沒有指定 `pagination_class`
- Django REST Framework 使用全局預設分頁設定
- 全局預設通常是每頁 20 筆
- API 只返回前 20 筆資料

### 問題 2: 前端未請求完整資料
**原始程式碼** (`frontend/src/pages/benchmark/TestCasesListPage.js`):
```javascript
const response = await benchmarkApi.getTestCases();
// ❌ 沒有指定 page_size 參數
```

**問題**:
- 前端調用 API 時沒有指定 `page_size` 參數
- 使用 API 的預設分頁設定（20 筆）
- 即使後端支援更大的 page_size，前端也沒有使用

---

## ✅ 解決方案

### 方案 1: 後端添加分頁配置（推薦）

**修改檔案**: `backend/api/views/viewsets/benchmark_viewsets.py`

**修改內容**:
```python
class BenchmarkTestCaseViewSet(viewsets.ModelViewSet):
    """
    測試案例管理 ViewSet
    
    提供功能：
    - CRUD 操作
    - 按類別、難度、題型篩選
    - 批量啟用/停用
    - 統計資訊
    """
    queryset = BenchmarkTestCase.objects.all().order_by('-created_at')
    serializer_class = BenchmarkTestCaseSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = DynamicPageSizePagination  # ✅ 新增這一行
```

**效果**:
- 支援 `?page_size=1000` 參數
- 預設每頁 20 筆
- 最大可達 1000 筆
- 客戶端可以靈活控制每頁數量

**DynamicPageSizePagination 配置** (`backend/api/pagination.py`):
```python
class DynamicPageSizePagination(PageNumberPagination):
    page_size = 20                      # 預設每頁 20 筆
    page_size_query_param = 'page_size' # 允許客戶端自訂
    max_page_size = 1000                # 最大限制 1000 筆
```

### 方案 2: 前端請求更大的 page_size

**修改檔案**: `frontend/src/pages/benchmark/TestCasesListPage.js`

**修改內容**:
```javascript
// 載入測試案例
const loadTestCases = async () => {
  setLoading(true);
  try {
    // ✅ 請求所有測試案例（設置大的 page_size）
    const response = await benchmarkApi.getTestCases({ page_size: 1000 });
    
    // ... 其餘程式碼
  }
};
```

**效果**:
- 前端明確請求 1000 筆資料
- 對於測試案例數量較少的情況（< 1000），可以一次載入全部
- 避免分頁問題

---

## 🚀 部署步驟

### 1. 修改後端配置
```bash
# 檔案已修改: backend/api/views/viewsets/benchmark_viewsets.py
# 添加: pagination_class = DynamicPageSizePagination
```

### 2. 修改前端 API 調用
```bash
# 檔案已修改: frontend/src/pages/benchmark/TestCasesListPage.js
# 修改: getTestCases({ page_size: 1000 })
```

### 3. 重啟容器
```bash
# 重啟 Django 容器
docker compose restart django

# 重啟 React 容器
docker compose restart react
```

### 4. 驗證配置
```bash
# 檢查 Django ViewSet 分頁配置
docker exec ai-django python manage.py shell -c "
from api.views.viewsets.benchmark_viewsets import BenchmarkTestCaseViewSet
print(f'pagination_class: {BenchmarkTestCaseViewSet.pagination_class.__name__}')
print(f'page_size: {BenchmarkTestCaseViewSet.pagination_class.page_size}')
print(f'max_page_size: {BenchmarkTestCaseViewSet.pagination_class.max_page_size}')
"
```

**驗證結果**:
```
✅ pagination_class: DynamicPageSizePagination
✅ 預設 page_size: 20
✅ page_size_query_param: page_size
✅ max_page_size: 1000
📊 資料庫總測試案例數: 55
```

---

## 📊 修復前後對比

### 修復前
| 項目 | 數值 |
|------|------|
| 資料庫總數 | 55 |
| API 返回數量 | 20 ❌ |
| 前端顯示數量 | 20 ❌ |
| 統計卡片顯示 | 20 ❌ |

### 修復後
| 項目 | 數值 |
|------|------|
| 資料庫總數 | 55 |
| API 返回數量 | 55 ✅ (使用 page_size=1000) |
| 前端顯示數量 | 55 ✅ |
| 統計卡片顯示 | 55 ✅ |

---

## 🧪 測試驗證

### 測試 1: API 分頁參數支援
```bash
# 測試預設分頁（應返回 20 筆）
GET /api/benchmark/test-cases/
# 預期: 返回前 20 筆 + count: 55 + next: {url}

# 測試自訂 page_size（應返回 55 筆）
GET /api/benchmark/test-cases/?page_size=1000
# 預期: 返回全部 55 筆 + count: 55 + next: null
```

### 測試 2: 前端頁面驗證
1. 重新整理 Test Cases 頁面 (F5)
2. 觀察統計卡片
3. 檢查表格資料

**預期結果**:
- 統計卡片顯示「總測試案例 55」✅
- 表格顯示所有 55 個測試案例 ✅
- 分頁控制顯示「第 1-20 項，共 55 項」✅

### 測試 3: 過濾功能驗證
1. 使用難度過濾（選擇「簡單」）
2. 檢查過濾後的數量

**預期結果**:
- 表格只顯示簡單難度的案例
- 分頁顯示過濾後的總數（如「第 1-6 項，共 6 項」）
- 統計卡片仍顯示全部資料的統計（55）

---

## 📝 程式碼變更摘要

### 後端變更
**檔案**: `backend/api/views/viewsets/benchmark_viewsets.py`
- **行號**: 45
- **變更**: 添加 `pagination_class = DynamicPageSizePagination`
- **影響**: 所有 Test Cases API 調用
- **版本**: Phase 26i 修復

### 前端變更
**檔案**: `frontend/src/pages/benchmark/TestCasesListPage.js`
- **行號**: 65
- **變更**: `getTestCases()` → `getTestCases({ page_size: 1000 })`
- **影響**: Test Cases 頁面資料載入
- **版本**: Phase 26i 修復

---

## 💡 最佳實踐建議

### 對於 ViewSet 開發者
1. ✅ **總是**明確指定 `pagination_class`
2. ✅ 使用 `DynamicPageSizePagination` 提供靈活性
3. ✅ 考慮資料量大小設定合適的 `max_page_size`
4. ❌ 不要依賴全局預設分頁設定

### 對於前端開發者
1. ✅ 了解 API 的分頁機制
2. ✅ 根據需求調整 `page_size` 參數
3. ✅ 處理分頁回應格式（`{count, results, next, previous}`）
4. ✅ 考慮使用前端分頁組件（Ant Design Table 支援）

### 對於資料量較大的情況
當測試案例數量 > 1000 時：
1. 實施真正的分頁（不要一次載入全部）
2. 使用後端過濾減少資料量
3. 實施虛擬滾動（Virtual Scrolling）
4. 考慮伺服器端渲染（Server-Side Rendering）

---

## 🔗 相關文檔

- Django REST Framework Pagination: https://www.django-rest-framework.org/api-guide/pagination/
- Ant Design Table Pagination: https://ant.design/components/table/#Pagination
- Phase 26i 完成報告: `/docs/features/PHASE_26I_COMPLETION_REPORT.md`
- Phase 26i 測試指南: `/docs/testing/PHASE_26I_TEST_GUIDE.md`

---

## ✅ 驗收標準

修復完成後，應滿足以下標準：
- [ ] 統計卡片顯示正確的總數（55）
- [ ] 表格可以顯示所有測試案例
- [ ] API 支援 `page_size` 參數
- [ ] 分頁控制顯示正確的總數
- [ ] 過濾功能正常運作（不影響統計數字）
- [ ] 搜尋功能正常運作（不影響統計數字）

---

**修復狀態**: ✅ 已完成  
**部署狀態**: ✅ 已部署  
**測試狀態**: ⏳ 待用戶測試

**下一步**: 請用戶重新整理瀏覽器 (F5) 並確認「總測試案例」顯示為 55
