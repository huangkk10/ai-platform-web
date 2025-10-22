# 🚀 AI Assistant 模組化快速參考

## 📦 目錄結構
```
frontend/src/styles/assistants/
├── AssistantMarkdownBase.css       # 共用 Markdown 基礎樣式
├── README.md                        # 完整使用說明
├── VALIDATION_CHECKLIST.md         # 驗證測試清單
└── QUICK_REFERENCE.md              # 本檔案
```

## ⚡ 快速開始：創建新 Assistant

### 步驟 1：創建 CSS 檔案（1 分鐘）
```bash
cd frontend/src/pages
touch YourAssistantChatPage.css
```

### 步驟 2：複製基礎模板（2 分鐘）
從 `ProtocolAssistantChatPage.css` 複製以下核心樣式：

```css
/* 你的 Assistant 前綴 */
.your-assistant-chat-page .message-text {
  all: revert !important;
}

.your-assistant-chat-page .markdown-preview-content.markdown-content p,
.your-assistant-chat-page .markdown-preview-content.markdown-content h1,
.your-assistant-chat-page .markdown-preview-content.markdown-content h2,
.your-assistant-chat-page .markdown-preview-content.markdown-content h3,
.your-assistant-chat-page .markdown-preview-content.markdown-content ul,
.your-assistant-chat-page .markdown-preview-content.markdown-content ol {
  margin: revert !important;
}

.your-assistant-chat-page .markdown-preview-content.markdown-content ul {
  list-style-type: circle !important;
  margin: 0 !important;
  padding-left: 24px !important;
  color: #000 !important;
}

.your-assistant-chat-page .markdown-preview-content.markdown-content ul ul {
  list-style-type: square !important;
}

.your-assistant-chat-page .markdown-preview-content.markdown-content ul ul ul {
  list-style-type: disc !important;
}

.your-assistant-chat-page .markdown-preview-content.markdown-content li {
  margin-bottom: 0 !important;
  line-height: 1.5 !important;
  color: #333 !important;
}
```

### 步驟 3：測試驗證（5 分鐘）
```bash
# 1. 重啟前端
docker compose restart ai-react

# 2. 瀏覽器測試（Ctrl+Shift+R 清快取）
# 3. 發送測試訊息，確認列表符號：○ → ■ → ●
```

## 🔑 核心規則（必須記住）

### 規則 1：清除 App.css 干擾
```css
.your-assistant-chat-page .message-text {
  all: revert !important;  /* 🔥 關鍵！ */
}
```

### 規則 2：恢復瀏覽器預設間距
```css
.your-assistant-chat-page .markdown-preview-content.markdown-content p,
.your-assistant-chat-page .markdown-preview-content.markdown-content h1,
/* ... */ {
  margin: revert !important;  /* 🔥 關鍵！ */
}
```

### 規則 3：統一列表符號
```css
/* 第一層：○ circle */
.your-assistant-chat-page .markdown-preview-content.markdown-content ul {
  list-style-type: circle !important;
}

/* 第二層：■ square */
.your-assistant-chat-page .markdown-preview-content.markdown-content ul ul {
  list-style-type: square !important;
}

/* 第三層：● disc */
.your-assistant-chat-page .markdown-preview-content.markdown-content ul ul ul {
  list-style-type: disc !important;
}
```

## 🎨 選擇器模式

### ✅ 正確的選擇器
```css
/* 使用 .markdown-preview-content.markdown-content */
.your-assistant-chat-page .markdown-preview-content.markdown-content ul {
  /* 樣式 */
}
```

### ❌ 錯誤的選擇器
```css
/* 不要使用 .message-text .markdown-content */
.your-assistant-chat-page .message-text .markdown-content ul {
  /* 這個不會生效！ */
}
```

## 📋 必備檢查清單

創建新 Assistant 時，確認：
- [ ] 使用頁面前綴（`.your-assistant-chat-page`）
- [ ] 添加 `all: revert !important` 到 `.message-text`
- [ ] 添加 `margin: revert !important` 到 p/h1/h2/h3/ul/ol
- [ ] 列表符號：circle → square → disc
- [ ] 使用 `.markdown-preview-content.markdown-content` 選擇器
- [ ] 列表顏色：`color: #000` (ul), `color: #333` (li)
- [ ] 列表間距：`margin: 0`, `padding-left: 24px`, `margin-bottom: 0`

## 🧪 快速測試命令

### 測試 Markdown 渲染
在 Assistant 中發送：
```
請測試列表：
- 第一層
  - 第二層
    - 第三層
```

預期結果：
```
○ 第一層
  ■ 第二層
    ● 第三層
```

### 檢查 CSS 規則（瀏覽器 Console）
```javascript
// 檢查 list-style-type
getComputedStyle(document.querySelector('.your-assistant-chat-page .markdown-preview-content.markdown-content ul')).listStyleType
// 預期：'circle'

// 檢查 margin
getComputedStyle(document.querySelector('.your-assistant-chat-page .markdown-preview-content.markdown-content p')).margin
// 預期：'16px 0px'（瀏覽器預設值）
```

## 🐛 故障排除速查

| 問題 | 可能原因 | 解決方案 |
|------|---------|---------|
| 列表符號不顯示 | 選擇器錯誤 | 使用 `.markdown-preview-content.markdown-content` |
| 間距異常 | 缺少 revert | 添加 `margin: revert !important` |
| CSS 污染其他頁面 | 缺少前綴 | 所有選擇器加上頁面前綴 |
| App.css 干擾渲染 | 缺少 all: revert | 添加到 `.message-text` |

## 📚 參考檔案

- **最簡潔實現**：`ProtocolAssistantChatPage.css`（96 行）
- **功能完整實現**：`RvtAssistantChatPage.css`（307 行）
- **基礎樣式模組**：`AssistantMarkdownBase.css`（120 行）

## 💡 最佳實踐

1. **複製 Protocol** - 使用 Protocol Assistant 作為起點（最簡潔）
2. **測試充分** - 使用相同 Markdown 在所有 Assistant 中測試
3. **保持一致** - 所有 Assistant 的列表符號應該相同
4. **最小化覆蓋** - 只在必要時添加自定義樣式

## ⏱️ 時間估算

- 創建新 Assistant CSS：**5-10 分鐘**
- 測試驗證：**5 分鐘**
- 修正問題（如有）：**10-15 分鐘**
- **總計**：約 **20-30 分鐘**

## 🎯 成功標準

新 Assistant 與 RVT/Protocol 的 Markdown 渲染：
- ✅ 列表符號完全相同
- ✅ 間距完全相同
- ✅ 無 CSS 污染
- ✅ DevTools 顯示的 Computed Styles 相同

---

**📅 更新日期**：2025-10-23  
**📝 版本**：v1.0  
**⚡ 目標**：5 分鐘內完成基礎設置！
