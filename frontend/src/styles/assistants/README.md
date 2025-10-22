# 🎨 AI Assistant 樣式模組

## 📋 概述

此目錄包含所有 AI Assistant（RVT、Protocol、QA 等）共用的基礎樣式模組。

## 📁 檔案結構

```
frontend/src/styles/assistants/
├── AssistantMarkdownBase.css    # Markdown 渲染基礎樣式
└── README.md                     # 使用說明（本檔案）
```

## 🎯 設計原則

### 1. **統一的 Markdown 渲染**
所有 Assistant 使用相同的 Markdown 渲染邏輯：
- ✅ `all: revert !important` - 清除 App.css 干擾
- ✅ `margin: revert !important` - 恢復瀏覽器預設間距
- ✅ 統一的列表符號：○ circle → ■ square → ● disc
- ✅ 依賴 ReactMarkdown.css 處理其他元素

### 2. **頁面前綴隔離**
每個 Assistant 使用自己的頁面前綴：
- `RvtAssistantChatPage.css` → `.rvt-assistant-chat-page`
- `ProtocolAssistantChatPage.css` → `.protocol-assistant-chat-page`
- 避免 CSS 樣式互相污染

### 3. **最小化覆蓋**
只覆蓋必要的樣式，其他依賴預設值：
- ❌ 不自定義詳細的標題樣式（h1-h6）
- ❌ 不自定義詳細的表格樣式
- ❌ 不自定義詳細的程式碼區塊樣式
- ✅ 只定義列表符號和間距

## 📦 使用方式

### 方法 1：參考模式（目前使用）

在頁面 CSS 中參考 `AssistantMarkdownBase.css` 的結構，使用頁面前綴覆蓋選擇器：

```css
/* YourAssistantChatPage.css */

/* 參考 AssistantMarkdownBase.css，使用自己的頁面前綴 */
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

/* 然後添加你的特定樣式 */
.your-assistant-chat-page {
  /* 你的自定義樣式 */
}
```

### 方法 2：直接引入（未來可選）

如果需要，可以使用 CSS `@import` 引入基礎樣式（需要額外配置）：

```css
/* YourAssistantChatPage.css */
@import '../../styles/assistants/AssistantMarkdownBase.css';

/* 然後使用你的頁面前綴覆蓋 */
```

## ✅ 已實現的 Assistant

### 1. RVT Assistant
- **檔案**：`frontend/src/pages/RvtAssistantChatPage.css`
- **前綴**：`.rvt-assistant-chat-page`
- **特色**：藍色主題、Ant Design Table 樣式

### 2. Protocol Assistant
- **檔案**：`frontend/src/pages/ProtocolAssistantChatPage.css`
- **前綴**：`.protocol-assistant-chat-page`
- **特色**：圖片顯示設定、精簡樣式

## 🚀 創建新 Assistant 的步驟

### 步驟 1：創建頁面 CSS 檔案
```bash
touch frontend/src/pages/YourAssistantChatPage.css
```

### 步驟 2：添加模組化標頭
```css
/* ============================================
 * Your Assistant 聊天頁面
 * ============================================
 * 📦 模組化架構：
 * - 共用 Markdown 樣式：參考 ../../styles/assistants/AssistantMarkdownBase.css
 * - 此檔案包含：Your 特定的樣式
 * 
 * 🎨 設計原則：
 * 1. 使用頁面前綴 .your-assistant-chat-page 避免 CSS 污染
 * 2. Markdown 渲染樣式與其他 Assistant 保持一致
 * 3. all: revert + margin: revert 策略
 * ============================================ */
```

### 步驟 3：複製核心 Markdown 樣式
從 `AssistantMarkdownBase.css` 複製樣式，並替換為你的頁面前綴：

```css
.your-assistant-chat-page .message-text {
  all: revert !important;
}

/* ... 其他核心樣式 ... */
```

### 步驟 4：添加特定樣式
根據需求添加你的 Assistant 特定樣式。

### 步驟 5：測試驗證
- [ ] 列表符號正確：○ → ■ → ●
- [ ] 間距與其他 Assistant 一致
- [ ] 沒有 CSS 污染其他頁面
- [ ] 使用 F12 DevTools 檢查計算樣式

## 📊 樣式優先級

```
頁面特定樣式 (最高優先級)
    ↓
AssistantMarkdownBase.css (參考模式)
    ↓
ReactMarkdown.css (基礎樣式)
    ↓
App.css (透過 all: revert 清除)
```

## 🔍 故障排除

### 問題 1：列表符號不顯示
**原因**：選擇器錯誤或被其他樣式覆蓋  
**解決**：檢查是否使用 `.markdown-preview-content.markdown-content` 選擇器

### 問題 2：間距與其他 Assistant 不一致
**原因**：缺少 `margin: revert !important`  
**解決**：確保添加了完整的 margin revert 規則

### 問題 3：樣式污染其他頁面
**原因**：缺少頁面前綴  
**解決**：所有選擇器都必須以 `.your-assistant-chat-page` 開頭

### 問題 4：App.css 干擾 Markdown 渲染
**原因**：缺少 `all: revert !important`  
**解決**：在 `.message-text` 上添加 `all: revert !important`

## 📚 參考文檔

- **Protocol Assistant CSS**：`frontend/src/pages/ProtocolAssistantChatPage.css`（最簡潔的實現）
- **RVT Assistant CSS**：`frontend/src/pages/RvtAssistantChatPage.css`（功能完整的實現）
- **基礎樣式模組**：`frontend/src/styles/assistants/AssistantMarkdownBase.css`

## 🎓 最佳實踐

1. **參考 Protocol Assistant**：它是最簡潔的實現，適合作為新 Assistant 的起點
2. **保持一致性**：所有 Assistant 的 Markdown 渲染應該看起來一樣
3. **最小化自定義**：只在必要時添加特定樣式
4. **充分測試**：使用相同的 Markdown 內容在多個 Assistant 中測試

## 📅 更新記錄

- **2025-10-23**：創建模組化架構，提取共用 Markdown 樣式
- **版本**：v1.0
- **狀態**：✅ 已在 RVT 和 Protocol Assistant 中驗證

---

**💡 提示**：當創建新的 AI Assistant 時，請務必遵循此模組化架構，確保一致的用戶體驗！
