# 🧪 Markdown 測試頁面使用指南

## 📋 概述
這是一個專為測試和調試 Markdown 渲染而設計的開發工具頁面。使用與 RVT Assistant 完全相同的 Markdown 渲染邏輯，方便開發者驗證 Markdown 格式是否正確顯示。

## 🔗 訪問方式

### URL 路徑
```
http://10.10.172.127/dev/markdown-test
```
或
```
http://localhost/dev/markdown-test
```

### 權限要求
- **僅管理員可訪問** (`is_staff = true`)
- 非管理員訪問會看到 "開發工具存取受限" 提示
- 使用 `ProtectedRoute` 保護

### 選單訪問
如果是管理員用戶，可以在側邊欄找到：
```
開發工具 → Markdown 測試
```

## 🎯 主要功能

### 1. 雙面板編輯預覽
- **左側編輯器**：純文字 Markdown 編輯
  - 支援多行輸入
  - 使用等寬字體（Consolas, Monaco）
  - 實時字數和行數統計
  
- **右側預覽**：即時 Markdown 渲染
  - 使用 `ReactMarkdown` 渲染
  - 與 RVT Assistant 相同的樣式
  - 自動表格格式修復

### 2. 自動保存功能
- 編輯內容自動保存到 `localStorage`
- 鍵名：`dev_markdown_test`
- 防抖延遲：500ms
- 刷新頁面不會丟失內容

### 3. 工具按鈕

#### 左側編輯器按鈕：
- **📄 載入範例**：載入預設的 Markdown 範例
- **🗑️ 清除**：清空編輯器內容

#### 右側預覽區按鈕：
- **📋 複製 MD**：複製 Markdown 原始文本到剪貼簿
- **💾 匯出 HTML**：將渲染結果匯出為完整的 HTML 文件

## 📝 支援的 Markdown 語法

### 基本格式
```markdown
**粗體** *斜體* ~~刪除線~~ `inline code`
```

### 標題
```markdown
# H1 標題
## H2 標題
### H3 標題
```

### 列表
```markdown
- 無序列表項目 1
- 無序列表項目 2
  - 子項目

1. 有序列表項目 1
2. 有序列表項目 2

- [ ] 待辦事項
- [x] 已完成事項
```

### 表格
```markdown
| 欄位 1 | 欄位 2 | 欄位 3 |
|-------|-------|-------|
| A1    | B1    | C1    |
| A2    | B2    | C2    |

| 左對齊 | 置中 | 右對齊 |
|:------|:----:|------:|
| Left  | Center | Right |
```

### 程式碼區塊
````markdown
```python
def hello_world():
    print("Hello, World!")
```
````

### 引用
```markdown
> 這是引用文字
> 可以多行
> > 巢狀引用
```

### 連結
```markdown
[連結文字](https://example.com)
```

## 🔧 技術實現

### 核心組件
```javascript
// 使用與 RVT Assistant 相同的配置
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { markdownComponents } from '../components/markdown/MarkdownComponents';
import { fixAllMarkdownTables } from '../utils/markdownTableFixer';

const markdownConfig = {
  remarkPlugins: [remarkGfm],  // GitHub Flavored Markdown
  components: markdownComponents,  // 自定義組件
  disallowedElements: ['script', 'iframe', 'object', 'embed'],
  unwrapDisallowed: true
};
```

### 表格修復
```javascript
// 自動修復 Markdown 表格格式
const processed = fixAllMarkdownTables(markdownText);
```

### CSS 樣式
- 使用 `ReactMarkdown.css` 統一樣式
- 使用 `.markdown-content` 類別
- 與 RVT Assistant 完全一致的外觀

## 🎨 UI 設計特色

### 漸層背景
- 主頁背景：線性漸層 (`#f5f7fa` → `#c3cfe2`)
- 卡片標題：紫色漸層 (`#667eea` → `#764ba2`)

### 響應式設計
- 大螢幕（≥992px）：左右並排
- 小螢幕（<992px）：上下堆疊
- 每個面板高度：500px（移動裝置）

### 滾動條美化
- 寬度：10px
- 顏色：與主題一致的紫色漸層
- 圓角設計

### 動畫效果
- 卡片淡入動畫（300ms）
- 按鈕 hover 效果
- 平滑過渡

## 📊 實際使用場景

### 1. 測試 AI 回應格式
當開發新的 AI Assistant 時，可以在這裡測試：
- AI 生成的 Markdown 是否正確渲染
- 表格格式是否正常顯示
- 程式碼區塊語法高亮是否正確

### 2. 調試知識庫內容
編輯知識庫（RVT Guide, Protocol Guide）前：
- 預覽內容的渲染效果
- 確認格式是否符合預期
- 測試複雜的 Markdown 語法

### 3. 樣式問題排查
當 Markdown 顯示異常時：
- 隔離測試特定語法
- 對比預期和實際效果
- 快速定位 CSS 衝突

### 4. 文檔編寫輔助
撰寫技術文檔時：
- 即時預覽排版效果
- 確保表格對齊正確
- 驗證連結和圖片引用

## 🚀 快速開始

1. **登入系統**（需管理員帳號）
2. **訪問頁面**：`/dev/markdown-test`
3. **載入範例**：點擊 "載入範例" 按鈕
4. **開始編輯**：在左側輸入 Markdown
5. **查看結果**：右側即時顯示渲染效果

## ⚙️ 配置說明

### 路由配置
```javascript
// frontend/src/App.js
<Route path="/dev/markdown-test" element={
  <ProtectedRoute permission="isStaff" fallbackTitle="開發工具存取受限">
    <DevMarkdownTestPage />
  </ProtectedRoute>
} />
```

### 選單配置
```javascript
// frontend/src/components/Sidebar.js
const devToolsItem = {
  key: 'dev-tools',
  icon: <ExperimentOutlined />,
  label: '開發工具',
  children: [
    {
      key: 'markdown-test',
      icon: <FileTextOutlined />,
      label: 'Markdown 測試',
    },
  ],
};
```

## 📁 檔案結構

```
frontend/src/
├── pages/
│   ├── DevMarkdownTestPage.js      # 主頁面組件
│   └── DevMarkdownTestPage.css     # 專用樣式
├── components/
│   └── markdown/
│       ├── MarkdownComponents.jsx  # Markdown 組件配置
│       └── ReactMarkdown.css       # 統一樣式
├── utils/
│   └── markdownTableFixer.js       # 表格修復工具
└── App.js                           # 路由配置
```

## 🔍 故障排除

### 問題 1：無法訪問頁面
**可能原因**：
- 用戶不是管理員（`is_staff = false`）
- 未登入系統

**解決方法**：
- 使用管理員帳號登入
- 確認用戶資料 `is_staff = true`

### 問題 2：渲染結果與預期不符
**可能原因**：
- Markdown 語法錯誤
- 表格分隔線格式不正確
- CSS 樣式衝突

**解決方法**：
- 檢查 Markdown 語法是否正確
- 使用範例作為參考
- 確認是否使用了不支援的語法

### 問題 3：內容丟失
**可能原因**：
- 清除了瀏覽器 localStorage
- 使用無痕模式瀏覽

**解決方法**：
- 重新載入範例
- 使用 "複製 MD" 功能備份內容
- 使用 "匯出 HTML" 保存結果

## 📚 相關文檔

- **RVT Assistant 實現**：`frontend/src/pages/RvtAssistantChatPage.js`
- **Markdown 組件**：`frontend/src/components/markdown/MarkdownComponents.jsx`
- **MessageFormatter**：`frontend/src/components/chat/MessageFormatter.jsx`
- **表格修復工具**：`frontend/src/utils/markdownTableFixer.js`

## 🎯 未來擴展可能性

### 進階功能
- [ ] 語法高亮編輯器（CodeMirror）
- [ ] 分屏同步滾動
- [ ] Markdown 快捷鍵支援
- [ ] 匯出為 PDF
- [ ] 匯出為 Word
- [ ] 歷史版本記錄
- [ ] 範本庫管理
- [ ] 圖片上傳和管理

### 協作功能
- [ ] 分享預覽連結
- [ ] 協作編輯
- [ ] 評論功能

## 📅 更新記錄

**2025-10-21**：
- ✅ 初始版本完成
- ✅ 雙面板編輯預覽功能
- ✅ 自動保存到 localStorage
- ✅ 工具按鈕（載入範例、清除、複製、匯出）
- ✅ 權限保護（僅管理員）
- ✅ 側邊欄選單整合
- ✅ 響應式設計
- ✅ 與 RVT Assistant 相同的渲染邏輯

---

**📝 作者**：AI Platform Team  
**🎯 用途**：開發工具 - Markdown 測試和調試  
**🔐 權限**：管理員專用  
**📍 位置**：`/dev/markdown-test`
