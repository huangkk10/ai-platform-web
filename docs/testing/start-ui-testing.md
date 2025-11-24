# 🚀 批量測試系統 - 前端 UI 測試啟動

## ✅ 系統狀態確認

### 容器運行狀態
```
✅ ai-react   - Up 2 hours (前端服務)
✅ ai-nginx   - Up 2 weeks (反向代理)
✅ ai-django  - Up 2 weeks (後端 API)
✅ postgres_db - Up 2 weeks (資料庫)
```

### 已完成準備工作
- ✅ 後端 batch_test API 已部署（/api/benchmark/versions/batch_test/）
- ✅ 前端頁面已建立（BatchTestExecutionPage.js, BatchComparisonPage.js）
- ✅ API 客戶端已配置（benchmarkApi.js - batchTest 方法）
- ✅ 路由已整合（/benchmark/batch-test, /benchmark/comparison/:batchId）
- ✅ CLI 測試已驗證（7 版本 × 2 測試案例 = 14 次測試成功）

---

## 🎯 開始測試

### 步驟 1：訪問測試頁面

**URL**：http://localhost/benchmark/batch-test

**登入憑證**（staff 用戶）：
- 用戶名：`Eric_huang` 或 `EdwardFu` 或 `admin_test`
- 密碼：[請使用實際設定的密碼]

### 步驟 2：開啟測試指南

完整的測試指南已經準備好，請查看：

```bash
# 在 VS Code 中打開測試指南
code /home/user/codes/ai-platform-web/docs/testing/BATCH_TESTING_UI_TEST_GUIDE.md
```

或直接在瀏覽器中查看：
```bash
# 使用 cat 查看
cat docs/testing/BATCH_TESTING_UI_TEST_GUIDE.md | less
```

### 步驟 3：按照指南執行測試

測試指南包含 6 個測試案例：

1. ✅ **頁面載入與版本選擇** - 驗證基本 UI 和資料載入
2. ✅ **測試案例選擇** - 驗證篩選和選擇功能
3. ✅ **執行批量測試** - 驗證核心功能和 API 整合 🔑
4. ✅ **API 回應處理** - 驗證成功/失敗處理
5. ✅ **對比頁面跳轉與顯示** - 驗證頁面跳轉
6. ✅ **錯誤處理測試** - 驗證異常情況處理

---

## 🔍 快速驗證腳本

執行以下命令確認系統準備就緒：

```bash
# 1. 確認容器狀態
echo "=== 容器狀態 ==="
docker compose ps | grep -E "(react|nginx|django|postgres)"

# 2. 確認資料準備
echo -e "\n=== 版本數量 ==="
docker exec postgres_db psql -U postgres -d ai_platform -c \
  "SELECT COUNT(*) as version_count FROM search_algorithm_version;" -t

echo -e "\n=== 測試案例數量 ==="
docker exec postgres_db psql -U postgres -d ai_platform -c \
  "SELECT COUNT(*) as testcase_count FROM benchmark_test_case WHERE is_active = true;" -t

# 3. 確認 API 端點存在
echo -e "\n=== API 端點確認 ==="
docker exec ai-django grep -n "def batch_test" /app/api/views/viewsets/benchmark_viewsets.py

# 4. 確認前端檔案存在
echo -e "\n=== 前端檔案確認 ==="
ls -lh frontend/src/pages/benchmark/BatchTestExecutionPage.js 2>/dev/null && echo "✅ BatchTestExecutionPage.js 存在" || echo "❌ 檔案不存在"
ls -lh frontend/src/pages/benchmark/BatchComparisonPage.js 2>/dev/null && echo "✅ BatchComparisonPage.js 存在" || echo "❌ 檔案不存在"
ls -lh frontend/src/services/benchmarkApi.js 2>/dev/null && echo "✅ benchmarkApi.js 存在" || echo "❌ 檔案不存在"

echo -e "\n✅ 系統準備就緒！請開始 UI 測試。"
```

---

## 🐛 如遇問題

### 問題 1：無法訪問頁面（404）

```bash
# 重啟 React 容器
docker compose restart react

# 等待 30 秒
sleep 30

# 再次訪問 http://localhost/benchmark/batch-test
```

### 問題 2：API 返回 403 Forbidden

**原因**：未登入或權限不足

**解決**：
1. 確保已登入系統
2. 使用 staff 用戶（Eric_huang, EdwardFu, admin_test）
3. 清除瀏覽器 Cookie 後重新登入

### 問題 3：看不到版本或測試案例

```bash
# 檢查資料庫資料
docker exec postgres_db psql -U postgres -d ai_platform -c \
  "SELECT id, name, is_active FROM search_algorithm_version ORDER BY id;"

docker exec postgres_db psql -U postgres -d ai_platform -c \
  "SELECT id, test_name, is_active FROM benchmark_test_case WHERE is_active = true LIMIT 5;"
```

### 問題 4：API 返回 500 Internal Server Error

```bash
# 查看 Django 日誌
docker logs ai-django --tail 100

# 重啟 Django 容器
docker compose restart django
sleep 5
```

---

## 📊 測試報告

測試完成後，請填寫測試報告：

**位置**：`docs/testing/BATCH_TESTING_UI_TEST_GUIDE.md` 的最後一節

**包含內容**：
- 測試通過/失敗統計
- 詳細測試結果（6 個測試案例）
- 發現的問題
- 改進建議
- 總體評價

---

## 📱 瀏覽器開發者工具使用指南

### 查看 API 請求

1. 打開 Chrome DevTools：按 **F12** 或 **Ctrl+Shift+I**
2. 切換到 **Network** 標籤
3. 篩選：選擇 **Fetch/XHR**
4. 點擊「執行批量測試」按鈕
5. 觀察 `batch_test` 請求

**預期看到**：
```
Request URL: http://localhost/api/benchmark/versions/batch_test/
Request Method: POST
Status Code: 201 Created

Request Payload:
{
  "version_ids": [3, 4, 5],
  "test_case_ids": [],
  "batch_name": "批量測試 2025-11-23 16:30:45",
  "notes": "",
  "force_retest": false
}

Response:
{
  "success": true,
  "batch_id": "20251123_163045",
  "test_run_ids": [42, 43, 44],
  ...
}
```

### 查看 Console 錯誤

1. 切換到 **Console** 標籤
2. 查看是否有紅色錯誤訊息
3. 如有錯誤，複製完整訊息用於排查

---

## 🎉 測試成功標準

全部通過以下檢查點即為測試成功：

- ✅ 頁面可以正常訪問（無 404）
- ✅ 版本列表正確載入
- ✅ 測試案例統計正確顯示
- ✅ 執行批量測試按鈕功能正常
- ✅ API 返回 201 Created 狀態
- ✅ 測試執行時間合理（< 30 秒）
- ✅ 成功訊息正確顯示
- ✅ 自動跳轉到對比頁面
- ✅ 對比頁面正常載入（mock 資料）
- ✅ 錯誤處理正常（未選擇版本時顯示警告）

---

**準備好了嗎？開始測試吧！** 🚀

如有任何問題，請隨時回報。祝測試順利！
