# 🎯 Protocol Assistant 搜尋版本切換 - 快速測試指南

## ✅ 現在可以測試了！

### 步驟 1：訪問 Protocol Assistant
```
URL: http://localhost/protocol-assistant-chat
```

### 步驟 2：強制刷新瀏覽器（重要！）
```
Ctrl + Shift + R  (Windows/Linux)
Cmd + Shift + R   (Mac)
```

這會清除緩存並載入最新的 JavaScript。

### 步驟 3：檢查切換開關
應該在輸入框上方看到：

```
┌─────────────────────────────────────┐
│  [ V1 基礎搜尋  ⇄  V2 上下文搜尋 ]  │ ← 這裡！
│  ┌───────────────────────────────┐  │
│  │ 輸入訊息...                   │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

**視覺特徵**：
- 🔵 V1：藍色，火箭圖示 🚀
- 🟢 V2：綠色，實驗圖示 🧪
- 位置：輸入框正上方，右對齊

### 步驟 4：測試 V1 搜尋
1. 確保開關在 **V1** 位置（藍色）
2. 發送測試訊息：`ULINK 測試流程`
3. 等待 AI 回應

**驗證**：
- 打開開發者工具 (F12)
- 切換到 Network 標籤
- 找到 `/chat/` 請求
- 檢查 Request Payload：
  ```json
  {
    "message": "ULINK 測試流程",
    "search_version": "v1"  ← 應該是 v1
  }
  ```

### 步驟 5：測試 V2 搜尋
1. 點擊開關，切換到 **V2** 位置（綠色）
2. 發送相同訊息：`ULINK 測試流程`
3. 等待 AI 回應

**驗證**：
- Network 標籤中的 `/chat/` 請求
- Request Payload：
  ```json
  {
    "message": "ULINK 測試流程",
    "search_version": "v2"  ← 應該是 v2
  }
  ```

**預期差異**：
- V2 回應可能更詳細（包含上下文）
- V2 執行時間可能稍長（+30-50%）

### 步驟 6：測試持久化
1. 切換到 V2（綠色）
2. 刷新頁面 (F5)
3. **確認**：刷新後仍然停留在 V2

**驗證 localStorage**：
```javascript
// 在瀏覽器控制台執行
console.log(localStorage.getItem('protocol_search_version'));
// 應該顯示: "v2"
```

---

## 🎨 UI 對比測試

### 測試相同的問題，對比 V1 vs V2

**測試問題**：
```
ULINK Protocol 測試環境如何配置？
```

| 項目 | V1 基礎搜尋 | V2 上下文搜尋 |
|------|-----------|-------------|
| 回應速度 | 快 (~1.5秒) | 中等 (~2.5秒) |
| 內容長度 | 簡潔 | 詳細（含上下文） |
| 適用場景 | 快速查找 | 深入理解 |
| 顏色標記 | 🔵 藍色 | 🟢 綠色 |

---

## 🔍 故障排除

### 問題 1：看不到切換開關
**解決方案**：
1. 確認訪問的是 `/protocol-assistant-chat`
2. 強制刷新：Ctrl + Shift + R
3. 打開無痕視窗重試

### 問題 2：切換無效（請求仍是 v1）
**解決方案**：
```javascript
// 瀏覽器控制台執行
localStorage.clear();
location.reload();
```

### 問題 3：容器問題
```bash
cd /home/user/codes/ai-platform-web
docker compose restart django react
sleep 10
docker compose logs react --tail 10
```

---

## ✅ 測試檢查清單

完成以下測試：

- [ ] 能訪問 Protocol Assistant 頁面
- [ ] 看到搜尋版本切換開關
- [ ] V1 搜尋正常工作
- [ ] V2 搜尋正常工作
- [ ] Network 請求中包含 `search_version`
- [ ] 切換開關會改變顏色（藍⇄綠）
- [ ] 刷新頁面後版本選擇保持
- [ ] Hover 時顯示 Tooltip
- [ ] V1 和 V2 回應有差異

---

## 📊 容器狀態

```bash
✅ Django: Up 59 seconds
✅ React: Up 58 seconds  
✅ React 編譯: webpack compiled successfully
```

**一切就緒！現在可以測試了！** 🚀

---

**創建時間**: 2025-11-09  
**測試環境**: Docker 容器 (已重啟)  
**React 狀態**: 已編譯成功
