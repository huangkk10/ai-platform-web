# 註冊審核系統 - 完整測試指南

## 📋 系統概述

本系統實現了用戶註冊需要管理員審核的功能流程：
1. **用戶註冊** → 帳號狀態設為 `pending`（待審核），無法登入
2. **管理員審核** → 批准/拒絕/停用用戶帳號
3. **用戶登入** → 只有 `approved` 狀態的帳號可以登入

## 🎯 功能完成清單

### ✅ 後端功能
- [x] 資料庫 Migration（0051_add_account_approval_system.py）
  - `account_status` 欄位（pending/approved/rejected/suspended）
  - `reviewed_by` 欄位（審核者）
  - `reviewed_at` 欄位（審核時間）
  - `rejection_reason` 欄位（拒絕原因）
  - `application_reason` 欄位（申請理由）
  - `application_department` 欄位（申請部門）

- [x] 註冊 API 修改（`user_register`）
  - 新用戶 `is_active=False`，`account_status='pending'`
  - 要求必填 `application_department` 和 `application_reason`

- [x] 登入 API 修改（`user_login_api`）
  - 檢查 `account_status` 狀態
  - 返回適當的錯誤訊息（pending/rejected/suspended）

- [x] 管理 ViewSet（`PendingUserViewSet`）
  - 列出待審核用戶（GET `/api/admin/pending-users/`）
  - 批准用戶（POST `/api/admin/pending-users/{id}/approve/`）
  - 拒絕用戶（POST `/api/admin/pending-users/{id}/reject/`）
  - 停用用戶（POST `/api/admin/pending-users/{id}/suspend/`）

- [x] 所有用戶管理 ViewSet（`AllUsersViewSet`）
  - 列出所有用戶（GET `/api/admin/all-users/`）
  - 支援批量操作

### ✅ 前端功能
- [x] 註冊表單（`RegisterForm.js`）
  - 添加 `application_department` 欄位（必填，最多 100 字）
  - 添加 `application_reason` 欄位（必填，10-500 字）
  - 註冊成功後顯示等待審核訊息

- [x] 登入表單（`LoginForm.js`）
  - 待審核狀態：顯示警告 Modal
  - 已拒絕狀態：顯示錯誤 Modal 和拒絕原因
  - 已停用狀態：顯示錯誤 Modal

- [x] 認證上下文（`AuthContext.js`）
  - 處理登入時的帳號狀態檢查
  - 返回 `{success, message, status, rejection_reason}`

- [x] 待審核用戶管理頁面（`PendingUsersPage.js`）
  - 待審核用戶列表（Table）
  - 批准按鈕（綠色勾勾）
  - 拒絕按鈕（紅色叉叉，需輸入原因）
  - 查看詳情按鈕（眼睛 icon）
  - 重新整理按鈕

- [x] 側邊欄選單（`Sidebar.js`）
  - 添加「待審核用戶」選單項目（UserAddOutlined icon）
  - 僅管理員可見

- [x] 路由配置（`App.js`）
  - `/admin/pending-users` 路由
  - `ProtectedRoute` 保護（需要 `isStaff` 權限）
  - 頁面標題：「待審核用戶管理」

## 🧪 完整測試流程

### 測試 1：新用戶註冊流程

#### 步驟 1.1：註冊新用戶
1. 打開瀏覽器：http://10.10.172.127
2. 點擊右上角「註冊」按鈕
3. 填寫註冊資訊：
   - 用戶名：`test_user_001`
   - Email：`test001@example.com`
   - 密碼：`TestPass123!`
   - 確認密碼：`TestPass123!`
   - **申請部門**：`測試部門` ⭐ 新增欄位
   - **申請理由**：`我需要使用 AI 平台進行測試工作和資料分析` ⭐ 新增欄位
4. 點擊「註冊」

**預期結果**：
- ✅ 顯示成功 Modal：「註冊成功！您的帳號申請已提交，請等待管理員審核。」
- ✅ Modal 包含說明：「您將在審核通過後收到通知，屆時即可登入系統。」

#### 步驟 1.2：嘗試登入（應該失敗）
1. 使用剛註冊的帳號登入：`test_user_001` / `TestPass123!`
2. 點擊「登入」

**預期結果**：
- ✅ 顯示警告 Modal：「帳號待審核」
- ✅ Modal 內容：「您的帳號申請正在審核中，請耐心等待管理員審核。」
- ✅ 無法成功登入

#### 步驟 1.3：檢查資料庫狀態
```bash
docker exec postgres_db psql -U postgres -d ai_platform -c "
SELECT 
    u.id, 
    u.username, 
    u.email, 
    u.is_active,
    up.account_status,
    up.application_department,
    up.application_reason,
    u.date_joined
FROM auth_user u
JOIN userprofile up ON u.id = up.user_id
WHERE u.username = 'test_user_001';
"
```

**預期結果**：
```
 id | username      | email               | is_active | account_status | application_department | application_reason
----+---------------+---------------------+-----------+----------------+------------------------+-------------------
  X | test_user_001 | test001@example.com | f         | pending        | 測試部門                | 我需要使用 AI 平台...
```

---

### 測試 2：管理員審核流程

#### 步驟 2.1：管理員登入
1. 使用管理員帳號登入
2. 在側邊欄點擊「管理功能」→「待審核用戶」

**預期結果**：
- ✅ 進入「待審核用戶管理」頁面
- ✅ 頁面標題顯示「待審核用戶」和橘色 Badge（數量）
- ✅ 表格顯示 `test_user_001` 的申請資訊

#### 步驟 2.2：查看用戶詳情
1. 點擊 `test_user_001` 行的「查看詳情」按鈕（眼睛 icon）

**預期結果**：
- ✅ 彈出詳情 Modal
- ✅ 顯示所有用戶資訊：
  - 用戶名：`test_user_001`
  - Email：`test001@example.com`
  - 申請部門：`測試部門`（藍色 Tag）
  - 申請理由：完整文字
  - 申請時間：格式化的時間
  - 帳號狀態：「待審核」（橘色 Tag）
- ✅ Modal 底部有「批准」和「拒絕」按鈕

#### 步驟 2.3：批准用戶
1. 在詳情 Modal 中點擊「批准」按鈕（或在表格中直接點擊批准按鈕）
2. 確認批准對話框出現，顯示用戶名、Email、部門
3. 點擊「批准」

**預期結果**：
- ✅ 顯示成功訊息：「已批准用戶 test_user_001 的註冊申請」
- ✅ 用戶從待審核列表中消失
- ✅ 表格自動重新整理

#### 步驟 2.4：檢查資料庫狀態
```bash
docker exec postgres_db psql -U postgres -d ai_platform -c "
SELECT 
    u.username, 
    u.is_active,
    up.account_status,
    up.reviewed_at,
    up.reviewed_by_id,
    reviewer.username as reviewed_by_username
FROM auth_user u
JOIN userprofile up ON u.id = up.user_id
LEFT JOIN auth_user reviewer ON up.reviewed_by_id = reviewer.id
WHERE u.username = 'test_user_001';
"
```

**預期結果**：
```
 username      | is_active | account_status | reviewed_at         | reviewed_by_id | reviewed_by_username
---------------+-----------+----------------+---------------------+----------------+---------------------
 test_user_001 | t         | approved       | 2025-01-20 10:30:00 | 1              | admin
```

#### 步驟 2.5：用戶登入測試（應該成功）
1. 登出管理員帳號
2. 使用 `test_user_001` / `TestPass123!` 登入

**預期結果**：
- ✅ 成功登入系統
- ✅ 可以正常訪問所有允許的頁面

---

### 測試 3：拒絕用戶流程

#### 步驟 3.1：註冊另一個測試用戶
1. 註冊新用戶：`test_user_002`
2. 填寫所有必填欄位
3. 等待審核狀態

#### 步驟 3.2：管理員拒絕申請
1. 管理員登入
2. 進入「待審核用戶」頁面
3. 點擊 `test_user_002` 的「拒絕」按鈕
4. 在彈出的 Modal 中輸入拒絕原因：
   ```
   申請資料不完整，請補充詳細的工作需求說明。
   ```
5. 點擊「確認拒絕」

**預期結果**：
- ✅ 顯示成功訊息：「已拒絕用戶 test_user_002 的註冊申請」
- ✅ 用戶從待審核列表中消失

#### 步驟 3.3：被拒絕用戶登入測試
1. 登出管理員
2. 嘗試使用 `test_user_002` 登入

**預期結果**：
- ✅ 顯示錯誤 Modal：「帳號申請已被拒絕」
- ✅ Modal 內容包含拒絕原因：
  ```
  您的帳號申請已被管理員拒絕。
  拒絕原因：申請資料不完整，請補充詳細的工作需求說明。
  如有疑問，請聯絡系統管理員。
  ```

#### 步驟 3.4：檢查資料庫狀態
```bash
docker exec postgres_db psql -U postgres -d ai_platform -c "
SELECT 
    u.username, 
    u.is_active,
    up.account_status,
    up.rejection_reason,
    up.reviewed_at
FROM auth_user u
JOIN userprofile up ON u.id = up.user_id
WHERE u.username = 'test_user_002';
"
```

**預期結果**：
```
 username      | is_active | account_status | rejection_reason          | reviewed_at
---------------+-----------+----------------+---------------------------+-------------------
 test_user_002 | f         | rejected       | 申請資料不完整，請補充... | 2025-01-20 10:35:00
```

---

### 測試 4：表單驗證測試

#### 測試 4.1：申請部門欄位驗證
1. 嘗試註冊時不填寫「申請部門」
2. 點擊「註冊」

**預期結果**：
- ✅ 顯示錯誤：「請輸入申請部門」
- ✅ 無法提交表單

#### 測試 4.2：申請理由長度驗證
1. 嘗試輸入少於 10 個字的申請理由
2. 點擊「註冊」

**預期結果**：
- ✅ 顯示錯誤：「申請理由至少需要 10 個字」

#### 測試 4.3：拒絕原因必填驗證
1. 管理員點擊「拒絕」按鈕
2. 不輸入拒絕原因，直接點擊「確認拒絕」

**預期結果**：
- ✅ 顯示警告訊息：「請輸入拒絕原因」
- ✅ Modal 不關閉

---

### 測試 5：權限測試

#### 測試 5.1：非管理員訪問測試
1. 使用普通用戶登入（非管理員）
2. 嘗試訪問：http://10.10.172.127/admin/pending-users

**預期結果**：
- ✅ 顯示「存取受限」頁面
- ✅ 側邊欄中看不到「待審核用戶」選單項目

#### 測試 5.2：未登入訪問測試
1. 登出所有帳號
2. 嘗試直接訪問：http://10.10.172.127/admin/pending-users

**預期結果**：
- ✅ 重定向到登入頁面
- ✅ 或顯示「存取受限」頁面

---

## 🔧 API 測試指令

### 測試 1：獲取待審核用戶列表
```bash
# 需要先獲取管理員 Token
TOKEN="your_admin_token_here"

curl -X GET "http://10.10.172.127/api/admin/pending-users/" \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json"
```

**預期回應**：
```json
{
  "success": true,
  "message": "獲取待審核用戶成功",
  "data": [
    {
      "id": 123,
      "username": "test_user_001",
      "email": "test001@example.com",
      "first_name": "",
      "last_name": "",
      "application_department": "測試部門",
      "application_reason": "我需要使用 AI 平台進行測試工作和資料分析",
      "date_joined": "2025-01-20T10:00:00Z"
    }
  ]
}
```

### 測試 2：批准用戶
```bash
USER_ID=123

curl -X POST "http://10.10.172.127/api/admin/pending-users/$USER_ID/approve/" \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json"
```

**預期回應**：
```json
{
  "success": true,
  "message": "用戶 test_user_001 已批准"
}
```

### 測試 3：拒絕用戶
```bash
USER_ID=124

curl -X POST "http://10.10.172.127/api/admin/pending-users/$USER_ID/reject/" \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "申請資料不完整"
  }'
```

**預期回應**：
```json
{
  "success": true,
  "message": "用戶 test_user_002 已拒絕"
}
```

### 測試 4：停用用戶
```bash
USER_ID=125

curl -X POST "http://10.10.172.127/api/admin/pending-users/$USER_ID/suspend/" \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "違反使用條款"
  }'
```

**預期回應**：
```json
{
  "success": true,
  "message": "用戶 test_user_003 已停用"
}
```

---

## 📊 資料庫查詢指令

### 查詢所有待審核用戶
```bash
docker exec postgres_db psql -U postgres -d ai_platform -c "
SELECT 
    u.id,
    u.username,
    u.email,
    u.is_active,
    up.account_status,
    up.application_department,
    LEFT(up.application_reason, 50) as reason_preview,
    u.date_joined
FROM auth_user u
JOIN userprofile up ON u.id = up.user_id
WHERE up.account_status = 'pending'
ORDER BY u.date_joined DESC;
"
```

### 查詢所有審核記錄
```bash
docker exec postgres_db psql -U postgres -d ai_platform -c "
SELECT 
    u.username as user,
    up.account_status as status,
    reviewer.username as reviewed_by,
    up.reviewed_at,
    up.rejection_reason
FROM auth_user u
JOIN userprofile up ON u.id = up.user_id
LEFT JOIN auth_user reviewer ON up.reviewed_by_id = reviewer.id
WHERE up.reviewed_at IS NOT NULL
ORDER BY up.reviewed_at DESC
LIMIT 10;
"
```

### 統計各狀態用戶數量
```bash
docker exec postgres_db psql -U postgres -d ai_platform -c "
SELECT 
    up.account_status,
    COUNT(*) as user_count
FROM userprofile up
GROUP BY up.account_status
ORDER BY user_count DESC;
"
```

---

## 🐛 故障排除

### 問題 1：註冊時沒有要求填寫部門和理由
**檢查**：
```bash
# 檢查前端文件是否正確更新
docker exec ai-react ls -la /app/src/components/RegisterForm.js

# 檢查容器是否重啟
docker ps --filter "name=ai-react"
```

**解決方案**：
```bash
docker restart ai-react
```

### 問題 2：管理員看不到「待審核用戶」選單
**檢查**：
```bash
# 檢查 Sidebar.js 是否正確更新
docker exec ai-react grep -n "pending-users" /app/src/components/Sidebar.js

# 檢查 App.js 路由是否註冊
docker exec ai-react grep -n "/admin/pending-users" /app/src/App.js
```

### 問題 3：批准/拒絕操作失敗
**檢查後端日誌**：
```bash
docker logs ai-django --tail 50 | grep -i "pending\|approve\|reject"
```

**檢查 API 端點是否註冊**：
```bash
docker exec ai-django python manage.py shell -c "
from django.urls import get_resolver
resolver = get_resolver()
for pattern in resolver.url_patterns:
    print(pattern)
" | grep pending
```

### 問題 4：資料庫欄位不存在
**檢查 migration 是否執行**：
```bash
docker exec ai-django python manage.py showmigrations api | grep -A 5 "0051"
```

**重新執行 migration**：
```bash
docker exec ai-django python manage.py migrate api
```

---

## ✅ 驗收標準

### 前端功能
- [ ] 註冊表單包含部門和理由欄位
- [ ] 註冊成功顯示等待審核訊息
- [ ] 待審核帳號登入顯示適當提示
- [ ] 被拒絕帳號登入顯示拒絕原因
- [ ] 管理員可以看到「待審核用戶」選單
- [ ] 待審核用戶列表正確顯示
- [ ] 批准/拒絕操作成功執行

### 後端功能
- [ ] 新註冊用戶 `is_active=False`
- [ ] 新註冊用戶 `account_status='pending'`
- [ ] 待審核用戶無法登入
- [ ] 批准後用戶可以登入
- [ ] 拒絕原因正確記錄
- [ ] 審核記錄包含審核者和時間

### 資料庫
- [ ] Migration 正確執行
- [ ] 6 個新欄位存在於 `userprofile` 表
- [ ] `account_status` 預設值為 `approved`（向後相容）
- [ ] 審核記錄可追溯

---

## 📅 部署檢查清單

部署到生產環境前，確認：
- [ ] Django 容器已重啟
- [ ] React 容器已重啟
- [ ] Migration 已執行
- [ ] 所有測試通過
- [ ] API 端點可訪問
- [ ] 前端頁面正常載入
- [ ] 權限控制正確
- [ ] 日誌無錯誤訊息

---

**測試完成後，請在此記錄測試結果和發現的問題**

測試日期：__________
測試人員：__________
測試環境：__________

| 測試項目 | 狀態 | 備註 |
|---------|------|------|
| 測試 1：新用戶註冊 | ⬜ Pass / ⬜ Fail | |
| 測試 2：管理員審核 | ⬜ Pass / ⬜ Fail | |
| 測試 3：拒絕用戶 | ⬜ Pass / ⬜ Fail | |
| 測試 4：表單驗證 | ⬜ Pass / ⬜ Fail | |
| 測試 5：權限測試 | ⬜ Pass / ⬜ Fail | |

問題記錄：
```
（記錄發現的問題）
```
