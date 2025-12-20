# Migration 修復報告

## 🚨 問題發現

**日期**：2025-12-21  
**問題**：用戶註冊後可以直接登入，未經管理員審核

## 🔍 根本原因分析

### 1. Migration 未執行
- **Migration 0051** (`add_account_approval_system`) **未被應用到資料庫**
- Django 記錄顯示 Migration 已執行（記錄在 `django_migrations` 表）
- 但實際上資料表欄位**未創建**

### 2. 影響範圍
以下欄位未創建：
- `account_status` - 帳號審核狀態（pending/approved/rejected/suspended）
- `application_department` - 申請部門
- `application_reason` - 申請理由
- `rejection_reason` - 拒絕原因
- `reviewed_at` - 審核時間
- `reviewed_by_id` - 審核者

### 3. 連帶影響
- 0042 到 0051 共 **10 個 Migration** 都標記為未執行 (`[X]`)
- 但資料庫記錄顯示它們都已執行
- 表示可能存在**資料庫狀態不一致**的問題

## ✅ 解決方案

### 手動執行 SQL 創建欄位

```sql
-- 1. account_status 欄位
ALTER TABLE api_userprofile ADD COLUMN account_status varchar(20) DEFAULT 'approved' NOT NULL;

-- 2. application_department 欄位
ALTER TABLE api_userprofile ADD COLUMN application_department varchar(100);

-- 3. application_reason 欄位
ALTER TABLE api_userprofile ADD COLUMN application_reason text;

-- 4. rejection_reason 欄位
ALTER TABLE api_userprofile ADD COLUMN rejection_reason text;

-- 5. reviewed_at 欄位
ALTER TABLE api_userprofile ADD COLUMN reviewed_at timestamp with time zone;

-- 6. reviewed_by_id 欄位（外鍵）
ALTER TABLE api_userprofile ADD COLUMN reviewed_by_id integer REFERENCES auth_user(id);

-- 7. 索引
CREATE INDEX api_userprofile_reviewed_by_idx ON api_userprofile(reviewed_by_id);

-- 8. 記錄 Migration
INSERT INTO django_migrations (app, name, applied) 
VALUES ('api', '0051_add_account_approval_system', NOW());
```

### 執行狀態
✅ **所有 SQL 語句已成功執行**  
✅ **6 個欄位已創建**  
✅ **索引已創建**  
✅ **Migration 記錄已添加**  

## 📊 當前資料庫狀態

### 欄位驗證結果
```
column_name            | data_type                | is_nullable | column_default
-----------------------+--------------------------+-------------+-------------------------------
account_status         | character varying        | NO          | 'approved'::character varying
application_department | character varying        | YES         | 
application_reason     | text                     | YES         | 
rejection_reason       | text                     | YES         | 
reviewed_at            | timestamp with time zone | YES         | 
reviewed_by_id         | integer                  | YES         | 
```

## 🔄 系統重啟

✅ **Django 容器已重啟** - 確保代碼讀取新的資料庫結構

## 📝 向後相容性

### 既有用戶處理
- **`account_status` 預設值**：`'approved'`
- **所有既有用戶**自動設為 `approved` 狀態
- **不影響既有用戶登入**

## 🧪 需要測試的功能

### 測試 1：新用戶註冊（待審核狀態）
**步驟**：
1. 訪問：http://10.10.172.127
2. 點擊「註冊」
3. 填寫所有資訊（包括部門和理由）
4. 提交

**預期結果**：
- ✅ 顯示「註冊成功，等待審核」訊息
- ✅ 用戶的 `account_status` 為 `pending`
- ✅ 用戶的 `is_active` 為 `false`

### 測試 2：待審核用戶登入（應該失敗）
**步驟**：
1. 使用剛註冊的帳號登入

**預期結果**：
- ❌ 登入失敗
- ✅ 顯示「帳號待審核」警告 Modal
- ✅ 提示訊息：「您的帳號尚未通過審核，請耐心等待管理員審核通知」

### 測試 3：管理員審核
**步驟**：
1. 管理員登入
2. 側邊欄：「管理功能」→「待審核用戶」
3. 找到新註冊的用戶
4. 點擊「批准」

**預期結果**：
- ✅ 顯示成功訊息
- ✅ 用戶的 `account_status` 更新為 `approved`
- ✅ 用戶的 `is_active` 更新為 `true`
- ✅ 記錄審核者和審核時間

### 測試 4：已批准用戶登入（應該成功）
**步驟**：
1. 使用已批准的帳號登入

**預期結果**：
- ✅ 成功登入
- ✅ 可以正常使用系統

### 測試 5：拒絕用戶
**步驟**：
1. 註冊另一個測試用戶
2. 管理員點擊「拒絕」並輸入原因
3. 被拒絕用戶嘗試登入

**預期結果**：
- ✅ 登入失敗
- ✅ 顯示「帳號申請已被拒絕」錯誤 Modal
- ✅ 顯示拒絕原因

## 🔧 技術細節

### Migration 檔案位置
- **本地**：`backend/api/migrations/0051_add_account_approval_system.py`
- **容器**：`/app/api/migrations/0051_add_account_approval_system.py`

### 相關代碼文件
**後端**：
- `backend/api/models.py` - UserProfile 模型定義
- `backend/api/views/auth_views.py` - 註冊和登入邏輯
- `backend/api/views/user_approval_views.py` - 審核管理 ViewSet

**前端**：
- `frontend/src/components/RegisterForm.js` - 註冊表單
- `frontend/src/components/LoginForm.js` - 登入表單
- `frontend/src/contexts/AuthContext.js` - 認證上下文
- `frontend/src/pages/admin/PendingUsersPage.js` - 待審核用戶管理頁面

## ⚠️ 注意事項

### 1. Migration 記錄不一致
- **問題**：0042-0050 的 Migration 在資料庫中有記錄，但 Django showmigrations 顯示為未執行
- **可能原因**：
  - 容器重建時 Migration 記錄丟失
  - `.pyc` 快取問題
  - Migration 依賴關係錯誤
- **影響**：可能導致後續 Migration 無法正確執行
- **建議**：未來創建新 Migration 時，先驗證資料庫狀態

### 2. 資料庫快照建議
在重大結構變更前，建議創建資料庫快照：
```bash
docker exec postgres_db pg_dump -U postgres ai_platform > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 3. 測試環境建議
- 在測試環境先驗證 Migration
- 使用 `sqlmigrate` 命令查看 SQL
- 手動測試資料庫變更

## 📅 修復時間記錄

- **問題發現**：2025-12-21 12:19 (UTC+8)
- **修復開始**：2025-12-21 12:25 (UTC+8)
- **修復完成**：2025-12-21 12:35 (UTC+8)
- **總耗時**：約 16 分鐘

## ✅ 修復確認清單

- [x] 資料庫欄位已創建（6 個欄位）
- [x] 索引已創建
- [x] Migration 記錄已添加
- [x] Django 容器已重啟
- [ ] 新用戶註冊測試（待執行）
- [ ] 待審核登入測試（待執行）
- [ ] 管理員審核測試（待執行）
- [ ] 已批准用戶登入測試（待執行）
- [ ] 拒絕用戶測試（待執行）

## 🎯 下一步行動

1. **立即測試**：按照上述測試步驟驗證功能
2. **文檔更新**：更新測試指南的實際結果
3. **監控日誌**：觀察是否有其他相關錯誤
4. **用戶通知**：（可選）通知現有用戶系統已修復

---

**修復人員**：AI Assistant  
**確認人員**：（待填）  
**狀態**：✅ 資料庫修復完成，等待功能測試
