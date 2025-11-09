# ✅ 搜尋版本切換 - Protocol Assistant 已完成

## 問題說明

用戶在 **Protocol Assistant** 頁面 (`/protocol-assistant-chat`) 看不到切換開關，因為我們只修改了 RVT Assistant。

## 解決方案

已為 **Protocol Assistant** 添加搜尋版本切換功能（完全相同的實現）。

---

## 修改的檔案

### 1. 前端 Hook：`useProtocolAssistantChat.js`
- ✅ 添加 `searchVersion` 狀態（localStorage: `protocol_search_version`）
- ✅ 添加 `useEffect` 同步 localStorage
- ✅ 在請求中添加 `search_version` 參數
- ✅ 導出 `searchVersion` 和 `setSearchVersion`

### 2. 後端 ViewSet：`knowledge_viewsets.py` - ProtocolGuideViewSet
- ✅ `search_sections` action 添加 `version` 參數支援
- ✅ V1：使用 `search_sections()`（基礎搜尋）
- ✅ V2：使用 `search_with_context()`（上下文增強）
- ✅ 返回 `version` 和 `execution_time`

---

## 測試步驟

### 1. 訪問 Protocol Assistant
```
URL: http://localhost/protocol-assistant-chat
```

### 2. 檢查切換開關
- 應該在輸入框**正上方**看到版本切換開關
- 預設位置：V1（藍色 🚀）
- 可切換到：V2（綠色 🧪）

### 3. 測試功能
1. **V1 基礎搜尋**：
   - 保持在 V1 位置
   - 發送測試訊息：「ULINK 測試流程」
   - 檢查 Network 面板：`search_version: "v1"`
   
2. **V2 上下文搜尋**：
   - 切換到 V2
   - 發送相同訊息：「ULINK 測試流程」
   - 檢查 Network 面板：`search_version: "v2"`
   - 回應應該包含更多上下文資訊

3. **localStorage 持久化**：
   - 切換到 V2
   - 重新整理頁面 (F5)
   - 確認仍然停留在 V2 位置

### 4. 瀏覽器強制刷新
```
Chrome/Edge: Ctrl + Shift + R
Firefox: Ctrl + F5
```

這會清除瀏覽器緩存，確保載入最新的 JavaScript。

---

## 已支援的 Assistant

| Assistant | Hook 檔案 | localStorage Key | 狀態 |
|-----------|----------|------------------|------|
| RVT Assistant | `useRvtChat.js` | `rvt_search_version` | ✅ 完成 |
| Protocol Assistant | `useProtocolAssistantChat.js` | `protocol_search_version` | ✅ 完成 |

---

## 技術細節

### 前端請求格式
```javascript
{
  "message": "ULINK 測試流程",
  "conversation_id": "abc123",
  "user_id": "user456",
  "search_version": "v2"  // ✅ 新增
}
```

### 後端 API 回應
```json
{
  "success": true,
  "version": "v2",
  "results": [...],
  "total": 3,
  "execution_time": "2500ms"
}
```

---

## 快速驗證

### 方法 1：瀏覽器控制台
```javascript
// 檢查 localStorage
console.log('Protocol:', localStorage.getItem('protocol_search_version'));
console.log('RVT:', localStorage.getItem('rvt_search_version'));

// 手動切換
localStorage.setItem('protocol_search_version', 'v2');
location.reload();
```

### 方法 2：Network 面板
1. 打開開發者工具 (F12)
2. 切換到 Network 標籤
3. 發送測試訊息
4. 查找 `/chat/` 請求
5. 檢查 Request Payload 中的 `search_version`

---

## 如果還是看不到

### 立即解決方案
```bash
cd /home/user/codes/ai-platform-web

# 完全重啟
docker compose down
docker compose up -d

# 等待 30 秒讓 React 編譯
sleep 30

# 檢查狀態
docker compose logs react --tail 20 | grep "Compiled"
```

然後：
1. 打開**無痕視窗**（避免緩存）
2. 訪問：http://localhost/protocol-assistant-chat
3. 應該能看到切換開關

---

## 常見問題

### Q1: 為什麼 RVT 有切換開關，但 Protocol 沒有？
**A**: 因為 RVT 和 Protocol 使用不同的 Hook。每個 Assistant 都需要單獨修改其 Hook 來支援搜尋版本。

### Q2: 兩個 Assistant 的版本選擇會互相影響嗎？
**A**: 不會。它們使用不同的 localStorage key：
- RVT: `rvt_search_version`
- Protocol: `protocol_search_version`

### Q3: 如何添加其他 Assistant 的版本切換？
**A**: 只需：
1. 修改該 Assistant 的 Hook（參考 `useRvtChat.js`）
2. 確保 ViewSet 的 search 相關 action 支援 `version` 參數
3. 不需要修改 `CommonAssistantChatPage` 或 `SearchVersionToggle` 組件

---

## 相關文檔

- [搜尋版本切換實作報告](/docs/features/search-version-toggle-implementation-report.md)
- [測試檢查清單](/docs/testing/search-version-toggle-test-checklist.md)
- [故障排除指南](/docs/testing/TROUBLESHOOTING_SEARCH_TOGGLE.md)
- [快速指南](/docs/features/SEARCH_VERSION_TOGGLE_README.md)

---

**更新時間**: 2025-11-09  
**版本**: v1.1  
**狀態**: ✅ RVT 和 Protocol Assistant 都已支援
