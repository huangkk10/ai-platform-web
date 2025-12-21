# 帳號審核機制修復報告（Library 版本）

## 🐛 問題描述

**日期**：2025-12-21  
**問題**：新註冊的用戶無需管理員審核即可直接登入使用系統

**用戶報告**：  
> "abc 這個帳號建立，但是還沒被 admin 允許，為什麼還是可以登入使用"

## 🔍 根本原因分析

### 問題 1：註冊處理未設置審核狀態

**檔案**：`library/auth/api_handlers.py` (第 210-224 行)

**問題程式碼**：
```python
# ❌ 錯誤：創建用戶時沒有設置 is_active=False
user = User.objects.create_user(
    username=username,
    password=password,
    email=email,
    first_name=first_name,
    last_name=last_name
    # 缺少 is_active=False
)

# ❌ 錯誤：創建 UserProfile 時沒有設置 account_status='pending'
UserProfileService.create_or_update_user_profile(
    user=user,
    profile_data={'bio': f'歡迎 {first_name or username} 加入！'}
    # 缺少 account_status='pending'
)
```

### 問題 2：登入驗證未檢查審核狀態

**檔案**：`library/auth/authentication_service.py` (第 52-72 行)

**問題程式碼**：
```python
# ❌ 錯誤：只檢查 is_active，沒有檢查 account_status
user = authenticate(request, username=username, password=password)

if user is not None:
    if user.is_active:  # 只檢查這個
        # 允許登入
        # 缺少 account_status 的檢查
```

## ✅ 修復方案

### 修復 1：註冊處理添加審核機制

**檔案**：`library/auth/api_handlers.py`

**修改內容**：
```python
# ✅ 修正：獲取申請資訊
application_department = data.get('application_department', '').strip()
application_reason = data.get('application_reason', '').strip()

# ✅ 修正：驗證申請資訊
if not application_department or not application_reason:
    return Response({
        'success': False,
        'message': '請填寫申請部門和申請理由'
    }, status=status.HTTP_400_BAD_REQUEST)

# ✅ 修正：創建用戶時設置 is_active=False
user = User.objects.create_user(
    username=username,
    password=password,
    email=email,
    first_name=first_name,
    last_name=last_name,
    is_active=False  # ✅ 預設為未啟用
)

# ✅ 修正：設置審核狀態和申請資訊
UserProfileService.create_or_update_user_profile(
    user=user,
    profile_data={
        'bio': f'歡迎 {first_name or username} 加入！',
        'account_status': 'pending',  # ✅ 待審核
        'application_department': application_department,
        'application_reason': application_reason
    }
)

# ✅ 修正：返回訊息
return Response({
    'success': True,
    'message': '註冊申請已提交，請等待管理員審核。審核通過後會收到通知。',
    'status': 'pending',  # ✅ 告知前端狀態
    # ...
}, status=status.HTTP_201_CREATED)
```

### 修復 2：登入驗證添加審核狀態檢查

**檔案**：`library/auth/authentication_service.py`

**修改內容**：
```python
# Django 认证
user = authenticate(request, username=username, password=password)

if user is not None:
    # ✅ 新增：檢查帳號審核狀態
    try:
        from api.models import UserProfile
        profile = user.userprofile
        
        # ✅ 檢查待審核狀態
        if profile.account_status == 'pending':
            logger.warning(f"嘗試登入待審核帳號: {username}")
            return {
                'success': False,
                'user': None,
                'message': '您的帳號尚未通過審核，請耐心等待管理員審核通知',
                'error_code': 'ACCOUNT_PENDING',
                'account_status': 'pending'
            }
        
        # ✅ 檢查已拒絕狀態
        elif profile.account_status == 'rejected':
            rejection_reason = profile.rejection_reason or '未提供原因'
            logger.warning(f"嘗試登入已拒絕帳號: {username}")
            return {
                'success': False,
                'user': None,
                'message': f'您的帳號申請已被拒絕。原因：{rejection_reason}',
                'error_code': 'ACCOUNT_REJECTED',
                'account_status': 'rejected',
                'rejection_reason': rejection_reason
            }
        
        # ✅ 檢查已停用狀態
        elif profile.account_status == 'suspended':
            logger.warning(f"嘗試登入已停用帳號: {username}")
            return {
                'success': False,
                'user': None,
                'message': '您的帳號已被停用，請聯絡系統管理員',
                'error_code': 'ACCOUNT_SUSPENDED',
                'account_status': 'suspended'
            }
    
    except UserProfile.DoesNotExist:
        # ✅ 向後相容：舊用戶沒有 profile，自動創建並設為已批准
        profile = UserProfile.objects.create(
            user=user,
            account_status='approved'
        )
        logger.info(f"為現有用戶 {username} 自動創建 UserProfile")
    
    # ✅ 檢查用戶是否啟用
    if user.is_active:
        # ✅ SuperUser 豁免審核檢查
        if user.is_superuser and profile.account_status != 'approved':
            profile.account_status = 'approved'
            profile.save()
        
        # 用户存在且激活
        if request:
            login(request, user)
            logger.info(f"用户登录成功: {username}")
        
        return {
            'success': True,
            'user': user,
            'message': '认证成功',
            'error_code': None
        }
    else:
        # 用户存在但被停用
        logger.warning(f"尝试登录被停用账号: {username}")
        return {
            'success': False,
            'user': None,
            'message': '该账号已被停用',
            'error_code': 'USER_INACTIVE'
        }
```

## 🔧 已執行操作

1. ✅ **修改註冊處理** - `library/auth/api_handlers.py`
   - 添加申請資訊獲取和驗證
   - 設置 `is_active=False`
   - 設置 `account_status='pending'`
   - 修改回應訊息

2. ✅ **修改登入驗證** - `library/auth/authentication_service.py`
   - 添加 `account_status` 檢查邏輯
   - 三種審核狀態檢查（pending, rejected, suspended）
   - 向後相容處理（舊用戶自動創建 profile）
   - SuperUser 豁免審核

3. ✅ **重啟 Django 容器** - `docker restart ai-django`

## 📊 修復前後對比

### 修復前（錯誤行為）
```
1. 用戶註冊 → is_active=True, account_status='approved'
2. 立即可以登入 ❌ 不需要審核
3. 可以正常使用系統 ❌ 沒有權限控制
```

### 修復後（正確行為）
```
1. 用戶註冊 → is_active=False, account_status='pending'
2. 嘗試登入 → 被拒絕 ✅ 顯示「帳號待審核」
3. 管理員批准 → is_active=True, account_status='approved'
4. 用戶可以登入 ✅ 正常使用系統
```

## 🧪 測試步驟

### 步驟 1：清理測試環境（如果 abc 用戶存在）

```bash
# 檢查 abc 用戶是否存在
docker exec postgres_db psql -U postgres -d ai_platform -c "
SELECT au.id, au.username, au.is_active, up.account_status 
FROM auth_user au 
LEFT JOIN api_userprofile up ON au.id = up.user_id 
WHERE au.username = 'abc';
"

# 如果存在，刪除它（重新測試）
docker exec postgres_db psql -U postgres -d ai_platform -c "
DELETE FROM auth_user WHERE username = 'abc';
"
```

### 步驟 2：註冊新用戶

1. 訪問：http://10.10.172.127
2. 點擊「註冊」
3. 填寫資訊：
   ```
   用戶名：test_approval_001
   密碼：Test1234!
   電子郵件：test001@example.com
   姓氏：測試
   名字：用戶
   部門：測試部門
   申請理由：測試帳號審核系統修復
   ```
4. 提交

**預期結果**：
- ✅ 顯示「註冊申請已提交，請等待管理員審核。審核通過後會收到通知。」
- ✅ **不會**自動登入

### 步驟 3：嘗試登入（應該失敗）

1. 使用剛註冊的帳號登入
2. 輸入用戶名：`test_approval_001`
3. 輸入密碼：`Test1234!`

**預期結果**：
- ❌ 登入失敗
- ✅ 顯示警告 Modal：「帳號待審核」
- ✅ 訊息：「您的帳號尚未通過審核，請耐心等待管理員審核通知」

### 步驟 4：驗證資料庫狀態

```bash
# 檢查用戶狀態
docker exec postgres_db psql -U postgres -d ai_platform -c "
SELECT 
    au.username,
    au.is_active,
    up.account_status,
    up.application_department,
    up.application_reason
FROM auth_user au
JOIN api_userprofile up ON au.id = up.user_id
WHERE au.username = 'test_approval_001';
"
```

**預期結果**：
```
username          | is_active | account_status | application_department | application_reason
------------------+-----------+----------------+------------------------+--------------------
test_approval_001 | f         | pending        | 測試部門               | 測試帳號審核系統修復
```

### 步驟 5：管理員批准

1. 使用管理員帳號登入
2. 前往：「管理功能」→「待審核用戶」
3. 找到 `test_approval_001`
4. 點擊「批准」

**預期結果**：
- ✅ 顯示成功訊息
- ✅ 用戶狀態變為「已批准」

### 步驟 6：已批准用戶登入（應該成功）

1. 使用 `test_approval_001` 再次登入

**預期結果**：
- ✅ 登入成功
- ✅ 可以正常使用系統

### 步驟 7：驗證批准後的資料庫狀態

```bash
docker exec postgres_db psql -U postgres -d ai_platform -c "
SELECT 
    au.username,
    au.is_active,
    up.account_status,
    up.reviewed_by_id,
    up.reviewed_at
FROM auth_user au
JOIN api_userprofile up ON au.id = up.user_id
WHERE au.username = 'test_approval_001';
"
```

**預期結果**：
```
username          | is_active | account_status | reviewed_by_id | reviewed_at
------------------+-----------+----------------+----------------+-------------------------
test_approval_001 | t         | approved       | <admin_user_id>| <timestamp>
```

## 📝 向後相容性說明

### 既有用戶處理
- ✅ **所有既有用戶**自動設為 `account_status='approved'`
- ✅ 既有用戶**可以正常登入**，不受影響
- ✅ 沒有 UserProfile 的舊用戶會自動創建 profile（設為 approved）

### SuperUser 豁免
- ✅ **SuperUser** 始終能夠登入
- ✅ 如果 SuperUser 的 `account_status` 不是 `approved`，會自動修正

## ⚠️ 重要注意事項

### 1. Library vs Fallback
- 系統優先使用 **Library 實現**（`library/auth/`）
- 只有在 Library 不可用時才使用 **Fallback 實現**（`backend/api/views/auth_views.py`）
- **本次修復針對 Library 實現**

### 2. 兩處都需要修改
為了完整性，以下兩處都已修改：
- ✅ `library/auth/api_handlers.py` - Library 註冊處理
- ✅ `library/auth/authentication_service.py` - Library 登入驗證
- ✅ `backend/api/views/auth_views.py` - Fallback 實現（之前已修改）

### 3. 前端已支援
前端程式碼已經支援審核狀態顯示：
- ✅ `frontend/src/contexts/AuthContext.js` - 已修正登入回應處理
- ✅ `frontend/src/components/LoginForm.js` - 已支援審核狀態 Modal
- ✅ `frontend/src/components/RegisterForm.js` - 已支援申請資訊填寫

## 🔍 日誌監控

測試時可以監控日誌：

```bash
# 監控註冊日誌
docker logs ai-django --follow | grep -E "(registered|註冊|register)"

# 監控登入日誌
docker logs ai-django --follow | grep -E "(登入|login|authenticate)"

# 監控審核日誌
docker logs ai-django --follow | grep -E "(審核|pending|approved|rejected)"
```

## 📅 修復時間記錄

- **問題發現**：2025-12-21 12:50 (UTC+8)
- **根因分析**：2025-12-21 12:55 (UTC+8)
- **修復完成**：2025-12-21 13:10 (UTC+8)
- **總耗時**：約 20 分鐘

## ✅ 修復確認清單

- [x] 註冊處理已添加審核機制（Library 版本）
- [x] 登入驗證已添加審核檢查（Library 版本）
- [x] Django 容器已重啟
- [ ] 新用戶註冊測試（待執行）
- [ ] 待審核登入測試（待執行）
- [ ] 管理員審核測試（待執行）
- [ ] 已批准用戶登入測試（待執行）
- [ ] 向後相容性驗證（待執行）

---

**修復人員**：AI Assistant  
**影響範圍**：Library 認證系統（主要）+ Fallback 實現（備用）  
**狀態**：✅ 修復完成，等待測試驗證  
**優先級**：🔴 **HIGH** - 影響系統安全性
