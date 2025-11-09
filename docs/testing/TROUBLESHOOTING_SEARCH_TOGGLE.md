# 🔧 搜尋版本切換開關故障排除指南

## 問題：在瀏覽器中看不到切換開關

### ✅ 快速診斷步驟

#### 1. 確認正確的 URL
訪問：**http://localhost/rvt-assistant-chat**

⚠️ **不是** `/rvt-chat`，而是 `/rvt-assistant-chat`

#### 2. 強制刷新瀏覽器
```
Chrome/Edge: Ctrl + Shift + R (Windows/Linux) 或 Cmd + Shift + R (Mac)
Firefox: Ctrl + F5 (Windows/Linux) 或 Cmd + Shift + R (Mac)
```

這會清除緩存並重新載入所有 JavaScript 和 CSS。

#### 3. 清除瀏覽器緩存
如果強制刷新不行：
1. 打開開發者工具 (F12)
2. 右鍵點擊重新整理按鈕
3. 選擇「清空緩存並重新整理」

#### 4. 檢查 React 容器狀態
```bash
cd /home/user/codes/ai-platform-web
docker compose logs react --tail 50 | grep -E "Compiled|webpack"
```

應該看到：
```
webpack compiled with 1 warning
```

如果沒有看到，重啟 React 容器：
```bash
docker compose restart react
sleep 10  # 等待編譯
```

#### 5. 驗證檔案是否存在
```bash
ls -la /home/user/codes/ai-platform-web/frontend/src/components/chat/SearchVersionToggle.jsx
```

應該顯示檔案存在（~3KB）。

#### 6. 檢查瀏覽器控制台
1. 打開開發者工具 (F12)
2. 切換到 Console 標籤
3. 刷新頁面
4. 查看是否有錯誤訊息

**常見錯誤**：
- `Module not found: SearchVersionToggle` - 檔案不存在或路徑錯誤
- `undefined is not a function` - Hook 返回值問題

---

## 🔍 深度診斷

### 檢查 1：確認 SearchVersionToggle 組件已載入
在瀏覽器控制台中執行：
```javascript
// 查看 React 組件樹
console.log(document.querySelector('.input-area'));
```

應該能看到輸入區域的 DOM。

### 檢查 2：確認 useRvtChat Hook 返回了 searchVersion
在 `/frontend/src/hooks/useRvtChat.js` 中臨時添加：
```javascript
// 在 return 語句之前
console.log('🔍 useRvtChat 返回值:', {
  searchVersion,
  setSearchVersion: typeof setSearchVersion
});
```

重啟 React 容器，刷新頁面，應該在控制台看到：
```
🔍 useRvtChat 返回值: { searchVersion: 'v1', setSearchVersion: 'function' }
```

### 檢查 3：確認條件渲染邏輯
在瀏覽器控制台執行：
```javascript
// 檢查切換組件的父容器
const inputArea = document.querySelector('.input-area');
if (inputArea) {
  console.log('✅ 找到 input-area');
  console.log('子元素數量:', inputArea.children.length);
} else {
  console.log('❌ 找不到 input-area');
}
```

### 檢查 4：確認 localStorage
在瀏覽器控制台執行：
```javascript
// 檢查 localStorage
console.log('localStorage.rvt_search_version:', localStorage.getItem('rvt_search_version'));

// 手動設置並刷新
localStorage.setItem('rvt_search_version', 'v2');
console.log('已設置為 v2，請刷新頁面');
```

---

## 🚨 已知問題和解決方案

### 問題 1：看不到切換開關，但沒有錯誤
**原因**：條件渲染失敗（`searchVersion === undefined`）

**診斷**：
```bash
# 檢查 useRvtChat.js 是否正確返回 searchVersion
grep -A 5 "return {" /home/user/codes/ai-platform-web/frontend/src/hooks/useRvtChat.js | grep searchVersion
```

**應該看到**：
```javascript
searchVersion,
setSearchVersion,
```

**解決方案**：
如果沒有看到，重新修改 useRvtChat.js：

```bash
# 備份原始檔案
cp /home/user/codes/ai-platform-web/frontend/src/hooks/useRvtChat.js /home/user/codes/ai-platform-web/frontend/src/hooks/useRvtChat.js.backup

# 檢查是否需要重新修改
cat /home/user/codes/ai-platform-web/frontend/src/hooks/useRvtChat.js | grep -A 20 "return {"
```

### 問題 2：切換開關顯示但無法點擊
**原因**：`setSearchVersion` 未正確綁定

**診斷**：在瀏覽器控制台
```javascript
// 查看組件 props
const toggle = document.querySelector('[class*="ant-switch"]');
console.log('Switch 元素:', toggle);
```

### 問題 3：瀏覽器顯示舊版本
**原因**：Service Worker 或瀏覽器緩存

**解決方案**：
```javascript
// 在瀏覽器控制台執行
navigator.serviceWorker.getRegistrations().then(registrations => {
  registrations.forEach(registration => {
    registration.unregister();
    console.log('已註銷 Service Worker');
  });
});

// 然後按 Ctrl + Shift + R 強制刷新
```

---

## ✅ 終極解決方案：完整重啟

如果以上都不行，執行完整重啟：

```bash
cd /home/user/codes/ai-platform-web

# 1. 停止所有服務
docker compose down

# 2. 清除 React build 緩存
sudo rm -rf frontend/node_modules/.cache
sudo rm -rf frontend/build

# 3. 重新啟動
docker compose up -d

# 4. 等待 React 編譯完成（約 30-60 秒）
echo "等待 React 編譯..."
sleep 30

# 5. 檢查 React 日誌
docker compose logs react --tail 50 | grep "Compiled"

# 6. 驗證服務狀態
docker compose ps
```

然後：
1. 打開新的無痕視窗（避免緩存）
2. 訪問：http://localhost/rvt-assistant-chat
3. 應該能看到切換開關

---

## 📍 正確的 UI 位置

切換開關應該出現在：

```
┌─────────────────────────────────────┐
│                                     │
│      聊天訊息區域                    │
│                                     │
├─────────────────────────────────────┤
│  [ V1 基礎搜尋  ⇄  V2 上下文搜尋 ] ← 這裡！
│  ┌───────────────────────────────┐  │
│  │ 請描述你的 RVT 問題...        │  │
│  │                               │  │
│  └───────────────────────────────┘  │
│                              [發送]  │
└─────────────────────────────────────┘
```

**視覺特徵**：
- 🔵 **V1**：藍色，火箭圖示 🚀
- 🟢 **V2**：綠色，實驗圖示 🧪
- Hover 時顯示 Tooltip
- 位於輸入框**正上方**
- 右對齊

---

## 🎯 快速驗證清單

完成以下檢查：

- [ ] 訪問正確 URL：`/rvt-assistant-chat`
- [ ] 強制刷新：Ctrl + Shift + R
- [ ] React 容器狀態：running
- [ ] React 編譯狀態：compiled successfully
- [ ] 瀏覽器控制台：無錯誤
- [ ] SearchVersionToggle.jsx：檔案存在
- [ ] useRvtChat.js：返回 searchVersion
- [ ] CommonAssistantChatPage.jsx：導入並使用 SearchVersionToggle
- [ ] localStorage：可以讀寫 `rvt_search_version`

全部 ✅ = 切換開關應該可見！

---

## 📞 需要幫助？

如果以上步驟都無法解決：

1. **截圖**：提供瀏覽器截圖和控制台截圖
2. **日誌**：運行以下命令並提供輸出
   ```bash
   docker compose logs react --tail 100 > react_logs.txt
   docker compose logs django --tail 100 > django_logs.txt
   ```
3. **檢查清單**：標記以上哪些步驟完成了

---

**更新日期**: 2025-11-09  
**版本**: v1.0  
**適用於**: 搜尋版本切換功能 UI 問題排查
