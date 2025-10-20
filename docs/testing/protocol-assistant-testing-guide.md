# Protocol Assistant 測試指南

## 🎯 快速測試步驟

### 前置條件
```bash
# 1. 確認 Django 容器已重啟
docker compose ps | grep django

# 2. 確認 Migration 已執行
docker exec ai-django python manage.py showmigrations api | grep web_protocol_assistant

# 3. 檢查 API 端點是否註冊
docker exec ai-django python manage.py show_urls | grep protocol-assistant
```

### 測試 1: 授予測試用戶權限

#### 方法 1: 透過 Django Shell（推薦）
```bash
# 進入 Django Shell
docker exec -it ai-django python manage.py shell

# 在 Shell 中執行
from api.models import User, UserProfile

# 查找測試用戶（替換為您的用戶名）
user = User.objects.get(username='your_username')

# 獲取或創建 UserProfile
profile, created = UserProfile.objects.get_or_create(user=user)

# 授予 Protocol Assistant 權限
profile.web_protocol_assistant = True
profile.save()

print(f"✅ 已授予 {user.username} Protocol Assistant 權限")

# 驗證權限
print(f"web_protocol_assistant: {profile.web_protocol_assistant}")

# 退出 Shell
exit()
```

#### 方法 2: 透過 Web 介面
1. 以管理員身份登入系統
2. 進入「用戶管理」頁面 (`/admin/user-management`)
3. 點擊要授予權限的用戶的「編輯」按鈕
4. 在「Web 功能」區塊中，勾選「Web Protocol Assistant」
5. 點擊「保存」

### 測試 2: 驗證 Sidebar 顯示

1. 以授權用戶登入系統
2. 檢查左側 Sidebar
3. 應該能在「RVT Assistant」下方看到「Protocol Assistant」選單項目

**預期結果**：
```
📱 Web AI Assistant
  ├─ Known Issue Chat
  ├─ RVT Assistant
  └─ Protocol Assistant  ← 應該出現在這裡
```

### 測試 3: 測試聊天功能

1. 點擊「Protocol Assistant」選單項目
2. 應該導航到 `/protocol-assistant-chat` 頁面
3. 在輸入框中輸入測試問題，例如：
   - "請介紹 Protocol 測試流程"
   - "如何進行 ULINK 測試？"
   - "Protocol 測試的常見問題有哪些？"
4. 點擊「發送」按鈕或按 Enter 鍵

**預期結果**：
- ✅ 用戶訊息顯示在聊天區域
- ✅ 顯示「正在輸入...」載入狀態
- ✅ AI 回應正確顯示
- ✅ Markdown 格式正確渲染

### 測試 4: 測試權限控制

#### 測試未授權訪問
1. 登出當前用戶
2. 以未授權用戶登入（或創建新用戶）
3. 嘗試訪問 `/protocol-assistant-chat`

**預期結果**：
- ❌ Sidebar 中不應顯示「Protocol Assistant」選項
- ❌ 直接訪問 URL 應顯示「權限拒絕」頁面

#### 測試權限撤銷
1. 撤銷測試用戶的 `web_protocol_assistant` 權限
2. 重新整理頁面

**預期結果**：
- ❌ 立即失去訪問權限
- ❌ 選單項目消失
- ❌ 訪問頁面顯示權限拒絕

### 測試 5: 測試訊息持久化

1. 發送幾條訊息並獲得回應
2. 重新整理瀏覽器頁面
3. 檢查訊息列表

**預期結果**：
- ✅ 所有訊息仍然顯示
- ✅ 對話歷史完整保留

### 測試 6: 測試「新聊天」功能

1. 在聊天頁面點擊頂部的「新聊天」按鈕
2. 檢查訊息列表

**預期結果**：
- ✅ 所有訊息被清空
- ✅ 顯示歡迎訊息
- ✅ localStorage 被清空

### 測試 7: 測試用戶反饋功能

1. 等待 AI 回應完成
2. 在回應訊息下方應該有「點讚」和「點踩」按鈕
3. 點擊「點讚」按鈕

**預期結果**：
- ✅ 按鈕狀態改變（變為實心）
- ✅ 顯示「反饋已提交」訊息
- ✅ 反饋發送到 Dify API

### 測試 8: 測試停止生成功能

1. 發送一個複雜問題（會導致較長回應）
2. 在 AI 回應過程中，點擊「停止生成」按鈕

**預期結果**：
- ✅ 請求被中斷
- ✅ 顯示部分已生成的回應
- ✅ 介面恢復正常狀態

### 測試 9: 後端 API 直接測試

#### 獲取配置
```bash
# 替換 YOUR_TOKEN 為實際的認證 Token
curl -X GET "http://localhost/api/protocol-assistant/config/" \
  -H "Authorization: Token YOUR_TOKEN"
```

**預期回應**：
```json
{
  "success": true,
  "config": {
    "app_name": "Protocol Guide",
    "description": "Dify Chat 應用，用於 Protocol 相關指導和協助",
    "features": ["Protocol 指導", "技術支援", "Protocol 流程管理"],
    "workspace": "Protocol_Guide"
  }
}
```

#### 發送聊天請求
```bash
curl -X POST "http://localhost/api/protocol-assistant/chat/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_TOKEN" \
  -d '{
    "query": "如何進行 Protocol 測試？"
  }'
```

**預期回應**：
```json
{
  "success": true,
  "answer": "...[AI 回答內容]...",
  "conversation_id": "xxx-xxx-xxx",
  "message_id": "xxx-xxx-xxx"
}
```

#### 測試權限拒絕
```bash
# 使用未授權的 Token
curl -X POST "http://localhost/api/protocol-assistant/chat/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Token INVALID_TOKEN" \
  -d '{"query": "test"}'
```

**預期回應**：
```json
{
  "detail": "Authentication credentials were not provided."
}
```
或
```json
{
  "detail": "You do not have permission to perform this action."
}
```

## 🐛 故障排除

### 問題 1: Sidebar 中看不到 Protocol Assistant
**可能原因**：
- 用戶未授權 `web_protocol_assistant` 權限
- 前端未正確重載

**解決方案**：
```bash
# 1. 檢查用戶權限
docker exec ai-django python manage.py shell
>>> from api.models import User
>>> user = User.objects.get(username='your_username')
>>> print(user.profile.web_protocol_assistant)

# 2. 授予權限（如果為 False）
>>> user.profile.web_protocol_assistant = True
>>> user.profile.save()

# 3. 重新登入前端
```

### 問題 2: 點擊選單項目後返回 404
**可能原因**：
- 路由未正確配置
- 前端未重新編譯

**解決方案**：
```bash
# 檢查 App.js 中是否有路由配置
grep -n "protocol-assistant-chat" frontend/src/App.js

# 重新啟動前端容器
docker compose restart react
```

### 問題 3: API 返回 500 錯誤
**可能原因**：
- Django 後端未重啟
- ViewSet 未正確註冊
- Dify 配置錯誤

**解決方案**：
```bash
# 1. 檢查 Django 日誌
docker logs ai-django --tail 100

# 2. 檢查 API 端點是否註冊
docker exec ai-django python manage.py show_urls | grep protocol-assistant

# 3. 重啟 Django
docker compose restart django

# 4. 驗證 Dify 配置
docker exec ai-django python manage.py shell
>>> from library.config.dify_config_manager import get_protocol_guide_config
>>> config = get_protocol_guide_config()
>>> print(config.validate())  # 應該返回 True
```

### 問題 4: Dify API 連接失敗
**可能原因**：
- Dify 服務不可用
- API Key 錯誤
- 網絡問題

**解決方案**：
```bash
# 1. 測試 Dify API 連接
curl -X POST "http://10.10.172.37/v1/chat-messages" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer app-MgZZOhADkEmdUrj2DtQLJ23G" \
  -d '{
    "inputs": {},
    "query": "test",
    "response_mode": "blocking",
    "user": "test-user"
  }'

# 2. 檢查 Dify 服務狀態
ping 10.10.172.37

# 3. 驗證 API Key
docker exec ai-django python manage.py shell
>>> from library.config.dify_config_manager import get_protocol_guide_config
>>> config = get_protocol_guide_config()
>>> print(config.api_key)  # 應該是 app-MgZZOhADkEmdUrj2DtQLJ23G
```

## ✅ 測試檢查清單

### 基本功能
- [ ] 授予用戶權限成功
- [ ] Sidebar 顯示 Protocol Assistant 選單
- [ ] 點擊選單可以導航到聊天頁面
- [ ] 發送訊息功能正常
- [ ] AI 回應正確顯示
- [ ] Markdown 格式正確渲染

### 權限控制
- [ ] 未授權用戶無法看到選單
- [ ] 未授權用戶訪問頁面顯示權限拒絕
- [ ] 撤銷權限後立即失效

### 高級功能
- [ ] 訊息持久化正常工作
- [ ] 新聊天功能清空訊息
- [ ] 用戶反饋功能正常
- [ ] 停止生成功能正常

### API 測試
- [ ] config 端點返回正確配置
- [ ] chat 端點正確處理請求
- [ ] 權限檢查正確執行
- [ ] 錯誤處理正常

### 用戶管理
- [ ] 管理介面顯示權限 Checkbox
- [ ] 勾選權限後保存成功
- [ ] 權限標籤正確顯示

## 📊 測試報告範本

```markdown
# Protocol Assistant 測試報告

## 測試環境
- 日期: YYYY-MM-DD
- 測試者: [姓名]
- 瀏覽器: Chrome/Firefox/Safari [版本]
- 後端版本: [git commit hash]

## 測試結果

### 基本功能測試
- [✅/❌] 權限授予
- [✅/❌] 選單顯示
- [✅/❌] 聊天功能
- [✅/❌] Markdown 渲染

### 權限測試
- [✅/❌] 權限控制
- [✅/❌] 未授權訪問

### 高級功能測試
- [✅/❌] 訊息持久化
- [✅/❌] 新聊天功能
- [✅/❌] 用戶反饋
- [✅/❌] 停止生成

### API 測試
- [✅/❌] Config API
- [✅/❌] Chat API
- [✅/❌] Feedback API

## 發現的問題
1. [問題描述]
   - 重現步驟: ...
   - 預期結果: ...
   - 實際結果: ...
   - 嚴重程度: 高/中/低

## 總體評價
[✅ 通過 / ❌ 需要修復]

## 建議
- [建議 1]
- [建議 2]
```

---

**更新日期**: 2025-01-XX  
**版本**: v1.0  
**作者**: AI Platform Team
