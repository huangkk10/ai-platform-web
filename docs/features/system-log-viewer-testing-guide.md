# 系統日誌查看器 - 測試指南

## 📋 功能概述

系統日誌查看器是一個基於 Web 的日誌管理工具，提供以下功能：
- 📂 **列出日誌檔案**：顯示所有可用的日誌檔案及其統計資訊
- 👁️ **查看日誌**：實時查看日誌內容，支援語法高亮
- 🔍 **搜尋過濾**：按日誌等級、關鍵字、日期範圍過濾
- ⬇️ **下載日誌**：支援 TXT 和 JSON 格式下載
- 📊 **統計資訊**：顯示日誌等級分佈和檔案資訊

---

## 🚀 快速開始

### 1️⃣ 訪問系統日誌頁面

**URL**: http://localhost/admin/system-logs

**權限要求**: 
- 必須是 `is_staff` 或 `is_superuser`
- 非管理員用戶會看到「系統管理功能存取受限」提示

**側邊欄路徑**:
```
管理功能 (Admin) → 系統日誌 (System Logs)
```

---

## 🧪 測試場景

### ✅ 場景 1：列出日誌檔案

**預期行為**:
1. 進入頁面後自動載入日誌檔案列表
2. 左側 Sider 顯示所有日誌檔案
3. 每個檔案顯示：
   - 檔案名稱（如 `django.log`）
   - 檔案大小（如 `2.3 MB`）
   - 行數（如 `1,234 行`）
   - 修改時間（如 `2025-10-31 07:58`）

**測試步驟**:
```bash
# 1. 在瀏覽器中訪問
http://localhost/admin/system-logs

# 2. 檢查左側檔案列表
# 應該看到以下檔案（如果存在）：
- django.log
- django_error.log
- dify_requests.log
- rvt_analytics.log
- protocol_analytics.log
- vector_operations.log
- api_access.log
- celery.log
```

**API 驗證**:
```bash
# 使用 curl 測試 API（需要認證）
curl -X GET "http://localhost/api/system/logs/list/" \
  -H "Cookie: sessionid=YOUR_SESSION_ID"
```

---

### ✅ 場景 2：查看日誌內容

**預期行為**:
1. 點擊檔案名稱後，右側顯示日誌內容
2. 日誌按等級顯示不同顏色：
   - 🔵 **INFO**: 藍色
   - 🟠 **WARNING**: 橙色
   - 🔴 **ERROR**: 紅色
   - 🟣 **CRITICAL**: 紫色
   - ⚪ **DEBUG**: 灰色
3. 顯示行號
4. 預設顯示最後 100 行

**測試步驟**:
```bash
# 1. 點擊 "django.log"
# 2. 觀察右側日誌內容
# 3. 檢查顏色編碼是否正確
# 4. 檢查行號是否從 1 開始
```

**API 驗證**:
```bash
# 查看最後 100 行
curl -X GET "http://localhost/api/system/logs/view/?file=django.log&lines=100&tail=true" \
  -H "Cookie: sessionid=YOUR_SESSION_ID"
```

---

### ✅ 場景 3：過濾日誌

#### 3.1 按等級過濾

**測試步驟**:
1. 選擇日誌檔案（如 `django.log`）
2. 在「日誌等級」下拉選單中選擇 `ERROR`
3. 點擊「重新整理」

**預期行為**:
- 只顯示 ERROR 等級的日誌
- 日誌內容全部為紅色

**API 驗證**:
```bash
curl -X GET "http://localhost/api/system/logs/view/?file=django.log&level=ERROR" \
  -H "Cookie: sessionid=YOUR_SESSION_ID"
```

#### 3.2 按關鍵字搜尋

**測試步驟**:
1. 在「搜尋關鍵字」輸入框輸入 `Library`
2. 點擊「重新整理」

**預期行為**:
- 只顯示包含 "Library" 關鍵字的日誌行
- 關鍵字可能被高亮顯示（取決於實作）

**API 驗證**:
```bash
curl -X GET "http://localhost/api/system/logs/view/?file=django.log&search=Library" \
  -H "Cookie: sessionid=YOUR_SESSION_ID"
```

#### 3.3 調整顯示行數

**測試步驟**:
1. 在「顯示行數」選擇器中選擇 `500`
2. 點擊「重新整理」

**預期行為**:
- 顯示最後 500 行日誌
- 頁面可能需要滾動

---

### ✅ 場景 4：下載日誌

**測試步驟**:
1. 選擇日誌檔案（如 `django.log`）
2. 點擊「下載」按鈕

**預期行為**:
- 瀏覽器下載 `django.log` 檔案
- 檔案格式為 TXT（原始格式）
- 檔案內容與顯示的相同

**API 驗證**:
```bash
# 下載 TXT 格式
curl -X GET "http://localhost/api/system/logs/download/?file=django.log&format=txt" \
  -H "Cookie: sessionid=YOUR_SESSION_ID" \
  -o django.log

# 下載 JSON 格式（已解析）
curl -X GET "http://localhost/api/system/logs/download/?file=django.log&format=json" \
  -H "Cookie: sessionid=YOUR_SESSION_ID" \
  -o django.log.json
```

---

### ✅ 場景 5：自動重新整理

**測試步驟**:
1. 勾選「自動重新整理」選項
2. 觀察日誌內容是否每 10 秒更新一次
3. 檢查右上角是否顯示倒數計時

**預期行為**:
- 每 10 秒自動重新載入日誌
- 顯示「下次重新整理：X 秒」
- 新的日誌條目自動出現

---

### ✅ 場景 6：日誌統計

**預期功能**（如果已實作）:
- 在左側 Sider 顯示統計卡片
- 顯示各等級日誌數量：
  - INFO: 1,234
  - WARNING: 56
  - ERROR: 12
  - CRITICAL: 1
- 顯示進度條

**API 驗證**:
```bash
curl -X GET "http://localhost/api/system/logs/stats/?file=django.log&days=7" \
  -H "Cookie: sessionid=YOUR_SESSION_ID"
```

---

## 🔍 進階搜尋測試（POST API）

### 測試場景：精確搜尋

```bash
# 使用 POST 進行複雜搜尋
curl -X POST "http://localhost/api/system/logs/search/" \
  -H "Content-Type: application/json" \
  -H "Cookie: sessionid=YOUR_SESSION_ID" \
  -d '{
    "file": "django.log",
    "search": "LogFileReader",
    "case_sensitive": false,
    "regex": false,
    "context_lines": 3,
    "max_results": 50
  }'
```

**預期回應**:
```json
{
  "success": true,
  "results": [
    {
      "line_number": 42,
      "content": "[INFO] 2025-10-31 07:58:51,345 ... LogFileReader ...",
      "context_before": ["...", "...", "..."],
      "context_after": ["...", "...", "..."]
    }
  ],
  "total_matches": 5,
  "search_time_ms": 123
}
```

---

## 🛡️ 安全性測試

### ✅ 測試 1：非管理員訪問

**測試步驟**:
1. 使用普通用戶登入（非 staff/superuser）
2. 訪問 http://localhost/admin/system-logs

**預期行為**:
- 顯示「系統管理功能存取受限」錯誤頁面
- 無法訪問日誌內容

### ✅ 測試 2：路徑遍歷攻擊

**測試步驟**:
```bash
# 嘗試訪問系統外的檔案
curl -X GET "http://localhost/api/system/logs/view/?file=../../etc/passwd" \
  -H "Cookie: sessionid=YOUR_SESSION_ID"
```

**預期行為**:
- 返回 400 Bad Request
- 錯誤訊息：`Invalid log file: ../../etc/passwd`

### ✅ 測試 3：檔案白名單檢查

**測試步驟**:
```bash
# 嘗試訪問不在白名單的檔案
curl -X GET "http://localhost/api/system/logs/view/?file=secret.log" \
  -H "Cookie: sessionid=YOUR_SESSION_ID"
```

**預期行為**:
- 返回 400 Bad Request
- 只允許訪問預定義的日誌檔案

---

## 🐛 故障排除

### 問題 1：404 Not Found

**可能原因**:
- URL 路由未正確配置
- Django 容器未重啟

**解決方案**:
```bash
# 檢查 URL 配置
grep -r "system/logs" backend/api/urls.py

# 重啟 Django
docker restart ai-django

# 檢查路由是否載入
docker logs ai-django | grep -i "system/logs"
```

### 問題 2：403 Forbidden

**可能原因**:
- 用戶沒有管理員權限
- Session 過期

**解決方案**:
1. 檢查用戶權限：
   ```bash
   docker exec ai-django python manage.py shell -c "
   from django.contrib.auth.models import User
   user = User.objects.get(username='YOUR_USERNAME')
   print(f'is_staff: {user.is_staff}')
   print(f'is_superuser: {user.is_superuser}')
   "
   ```

2. 重新登入

### 問題 3：空白頁面或組件未載入

**可能原因**:
- 前端編譯錯誤
- 組件路徑錯誤

**解決方案**:
```bash
# 檢查 React 編譯日誌
docker logs ai-react --tail 50

# 重新編譯
docker restart ai-react

# 等待編譯完成
docker logs ai-react --follow | grep "Compiled successfully"
```

### 問題 4：日誌檔案列表為空

**可能原因**:
- 日誌目錄路徑錯誤
- 日誌檔案不存在

**解決方案**:
```bash
# 檢查日誌目錄
docker exec ai-django ls -la /app/logs/

# 檢查 LogFileReader 設定
docker exec ai-django python manage.py shell -c "
from library.system_monitoring import LogFileReader
print(LogFileReader.LOG_DIR)
print(LogFileReader.ALLOWED_LOG_FILES)
"
```

---

## 📊 效能測試

### 測試大檔案載入

```bash
# 創建測試用大檔案（僅測試環境）
docker exec ai-django bash -c "
for i in {1..10000}; do
  echo '[INFO] 2025-10-31 12:00:00,000 test_module Test log line \$i' >> /app/logs/test.log
done
"

# 測試讀取 tail（應該很快）
time curl -X GET "http://localhost/api/system/logs/view/?file=test.log&lines=100" \
  -H "Cookie: sessionid=YOUR_SESSION_ID"

# 測試讀取全部（可能較慢）
time curl -X GET "http://localhost/api/system/logs/view/?file=test.log&lines=10000&tail=false" \
  -H "Cookie: sessionid=YOUR_SESSION_ID"
```

---

## ✅ 驗收標準

系統日誌查看器需要滿足以下標準才算測試通過：

### 功能性
- [ ] 能夠列出所有可用的日誌檔案
- [ ] 能夠查看日誌內容並正確顯示
- [ ] 能夠按等級過濾日誌
- [ ] 能夠按關鍵字搜尋日誌
- [ ] 能夠下載日誌檔案（TXT 格式）
- [ ] 能夠調整顯示行數（100/500/1000/全部）

### 安全性
- [ ] 非管理員無法訪問
- [ ] 無法訪問白名單外的檔案
- [ ] 防止路徑遍歷攻擊

### 效能
- [ ] 載入 100 行日誌 < 1 秒
- [ ] 載入 1000 行日誌 < 3 秒
- [ ] 搜尋功能響應時間 < 2 秒

### 用戶體驗
- [ ] UI 響應式設計，適配不同螢幕
- [ ] 日誌顏色編碼清晰易讀
- [ ] 錯誤訊息友好明確
- [ ] 載入狀態有明確指示

---

## 📚 相關文檔

- **後端 API**: `/backend/api/views/log_viewer_views.py`
- **前端服務**: `/frontend/src/services/logService.js`
- **前端 Hook**: `/frontend/src/hooks/useLogViewer.js`
- **前端頁面**: `/frontend/src/pages/admin/SystemLogViewerPage.js`
- **日誌讀取器**: `/library/system_monitoring/log_reader.py`
- **日誌解析器**: `/library/system_monitoring/log_parser.py`

---

**📅 文檔創建日期**: 2025-10-31  
**✍️ 作者**: AI Platform Team  
**🎯 用途**: 系統日誌查看器功能測試指南
