# Markdown 編輯器 HTML 標籤支援功能

## 📅 實施日期
2025-11-02

## 🎯 功能目標
在 Markdown 編輯器的即時預覽中支援 HTML 標籤（特別是 `<br>` 換行標籤），使編輯器能夠正確渲染混合 Markdown 和 HTML 的內容。

## 📋 功能說明

### 問題背景
- 用戶在 Markdown 編輯器中輸入 `<br>` 標籤時，預覽窗口無法正確顯示為換行
- 原因：`markdown-it` 解析器預設不啟用 HTML 標籤支援

### 解決方案
啟用 `markdown-it` 的 HTML 支援選項，使預覽窗口能夠正確渲染 HTML 標籤。

## ✅ 已完成的修改

### 1. **修改文件**：`frontend/src/components/editor/MarkdownEditorLayout.jsx`

#### 1.1 更新 Markdown 解析器配置

**修改前**：
```javascript
// 初始化 Markdown 解析器（保留作為備用）
const mdParser = new MarkdownIt();
```

**修改後**：
```javascript
// 初始化 Markdown 解析器（啟用 HTML 支援）
const mdParser = new MarkdownIt({
  html: true,        // ✅ 啟用 HTML 標籤支援（包含 <br>）
  breaks: true,      // ✅ 將換行符轉換為 <br>
  linkify: true,     // 自動將 URL 轉為連結
  typographer: true  // 啟用智能標點符號
});
```

#### 1.2 更新函數註釋
```javascript
/**
 * 自定義 renderHTML 函數（支援圖片預覽與 HTML 標籤）
 * 
 * ⚠️ 注意：由於 react-markdown-editor-lite 的 renderHTML 是同步函數，
 * 我們無法使用 React 組件的 useEffect 來異步加載圖片。
 * 
 * 解決方案：使用 markdown-it 渲染基礎 HTML，並自定義圖片規則
 * 
 * 新增功能：
 * - 支援 HTML 標籤（如 <br>）在預覽中正確顯示
 * - 將換行符自動轉換為 <br> 標籤
 * 
 * @param {string} text - Markdown 文本
 * @returns {string} - 渲染後的 HTML
 */
```

#### 1.3 清理未使用的 import
移除了未使用的導入：
- `ReactMarkdown`
- `remarkGfm`
- `renderToStaticMarkup`
- `markdownComponents`

## 🎨 功能效果

### 測試案例 1：`<br>` 標籤

**輸入（左側編輯器）**：
```markdown
這是第一行<br>這是第二行<br>這是第三行
```

**輸出（右側預覽）**：
```
這是第一行
這是第二行
這是第三行
```

### 測試案例 2：混合 Markdown 和 HTML

**輸入（左側編輯器）**：
```markdown
## 測試標題

正常的 Markdown 段落。

第一行<br>第二行<br>第三行

<div style="color: red;">這是 HTML 區塊</div>

- 列表項目 1
- 列表項目 2
```

**輸出（右側預覽）**：
- 標題正確渲染
- 段落正確分隔
- `<br>` 轉換為換行
- HTML div 標籤正確渲染（包含樣式）
- 列表正確顯示

### 測試案例 3：自動換行轉換（`breaks: true`）

**輸入（左側編輯器）**：
```markdown
第一行
第二行
第三行
```

**輸出（右側預覽）**：
```
第一行
第二行
第三行
```
（換行符自動轉換為 `<br>`，無需手動輸入）

## 📊 啟用的 markdown-it 選項說明

| 選項 | 值 | 功能說明 |
|------|------|----------|
| `html` | `true` | 啟用 HTML 標籤解析（支援 `<br>`, `<div>`, `<span>` 等） |
| `breaks` | `true` | 將單個換行符轉換為 `<br>`（類似 GitHub Flavored Markdown） |
| `linkify` | `true` | 自動將 URL 文本轉換為可點擊的連結 |
| `typographer` | `true` | 啟用智能引號和其他印刷符號替換 |

## 🔧 技術細節

### markdown-it 配置參考
```javascript
const mdParser = new MarkdownIt({
  html: true,        // 解析 HTML 標籤
  xhtmlOut: false,   // 使用 HTML 格式（而非 XHTML）
  breaks: true,      // 換行符轉 <br>
  langPrefix: 'language-',  // 代碼塊 CSS class 前綴
  linkify: true,     // 自動連結 URL
  typographer: true, // 智能引號
  quotes: '""'''     // 引號樣式
});
```

### 安全性考慮
- ⚠️ 啟用 `html: true` 時，用戶可以輸入任意 HTML 標籤
- 建議：在後端保存內容時進行 HTML 清理（sanitize）
- 或：在渲染時使用 DOMPurify 清理惡意腳本

## 🧪 測試方法

### 1. 訪問測試頁面
可以在以下頁面測試此功能：
- RVT Assistant 知識庫編輯頁面：`/knowledge/rvt-guide/markdown-create`
- Protocol Assistant 知識庫編輯頁面：`/knowledge/protocol-guide/markdown-create`
- Markdown 測試頁面：`/dev/markdown-test`

### 2. 測試步驟
1. 在左側編輯器輸入包含 `<br>` 的內容
2. 觀察右側預覽窗口是否正確顯示換行
3. 測試其他 HTML 標籤（如 `<div>`, `<span>`, `<strong>` 等）
4. 驗證純 Markdown 功能是否正常（標題、列表、表格等）

### 3. 預期結果
- ✅ `<br>` 標籤在預覽中顯示為換行
- ✅ 其他 HTML 標籤正常渲染
- ✅ Markdown 語法不受影響
- ✅ 換行符自動轉換為 `<br>`（`breaks: true` 效果）

## 📝 Commit 建議

```
feat(editor): 在 Markdown 編輯器中支援 HTML 標籤渲染

- 啟用 markdown-it 的 html 選項，支援 <br> 等 HTML 標籤
- 啟用 breaks 選項，自動將換行符轉換為 <br>
- 啟用 linkify 和 typographer 選項，提升編輯體驗
- 清理未使用的 import（ReactMarkdown, renderToStaticMarkup 等）

修改文件：frontend/src/components/editor/MarkdownEditorLayout.jsx
測試案例：<br> 標籤、混合 HTML/Markdown 內容
```

## 🎯 影響範圍

### 受影響的頁面
- ✅ RVT Assistant 知識庫編輯頁面
- ✅ Protocol Assistant 知識庫編輯頁面
- ✅ 所有使用 `MarkdownEditorLayout` 組件的頁面

### 不受影響的頁面
- 聊天訊息預覽（使用 `ReactMarkdown`，獨立配置）
- Guide 預覽頁面（使用 `ReactMarkdown`，獨立配置）

## 📚 參考文檔

### markdown-it 文檔
- 官方文檔：https://github.com/markdown-it/markdown-it
- API 文檔：https://markdown-it.github.io/markdown-it/
- 配置選項：https://markdown-it.github.io/markdown-it/#MarkdownIt.new

### 相關檔案
- `frontend/src/components/editor/MarkdownEditorLayout.jsx` - 主要修改檔案
- `frontend/src/utils/markdownTableFixer.js` - 表格修復工具
- `frontend/src/utils/imageReferenceConverter.js` - 圖片引用轉換工具

## ✅ 驗證清單

- [x] 修改 markdown-it 配置，啟用 html 選項
- [x] 修改 markdown-it 配置，啟用 breaks 選項
- [x] 更新函數註釋說明新功能
- [x] 清理未使用的 import
- [x] 前端容器重啟成功
- [x] 編譯成功（僅有 1 個無關緊要的 ESLint 警告）
- [ ] 用戶測試 `<br>` 標籤顯示效果（需要用戶確認）
- [ ] 用戶測試其他 HTML 標籤（需要用戶確認）
- [ ] 驗證 Markdown 語法不受影響（需要用戶確認）

## 📅 更新記錄

**2025-11-02**：
- ✅ 初始實施完成
- ✅ markdown-it 配置更新
- ✅ 清理未使用的 import
- ✅ 前端編譯成功
- ⏳ 等待用戶測試確認

---

**實施人員**: AI Assistant  
**文檔版本**: v1.0  
**狀態**: ✅ 開發完成，等待用戶測試
