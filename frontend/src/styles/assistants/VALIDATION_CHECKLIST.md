# ✅ AI Assistant 模組化驗證清單

## 📋 測試概述

驗證 RVT 和 Protocol Assistant 的 Markdown 渲染在模組化後保持一致性。

## 🧪 測試步驟

### 1️⃣ 重啟前端容器
```bash
docker compose restart ai-react
```

### 2️⃣ 清除瀏覽器快取
- 開啟 RVT Assistant：`http://localhost/rvt-assistant-chat`
- 按 `Ctrl + Shift + R`（硬重新載入）
- 開啟 Protocol Assistant：`http://localhost/protocol-assistant-chat`
- 按 `Ctrl + Shift + R`（硬重新載入）

### 3️⃣ 測試 Markdown 內容

複製以下測試內容，分別在 **RVT Assistant** 和 **Protocol Assistant** 中發送：

```markdown
請幫我測試以下 Markdown 渲染：

# 標題 1
## 標題 2
### 標題 3

段落文字測試，這是一個普通段落。

- 第一層列表項目 1
- 第一層列表項目 2
  - 第二層列表項目 A
  - 第二層列表項目 B
    - 第三層列表項目 i
    - 第三層列表項目 ii
- 第一層列表項目 3

1. 有序列表項目 1
2. 有序列表項目 2
3. 有序列表項目 3

**粗體文字** 和 *斜體文字*

`程式碼片段`

```python
# 程式碼區塊
def hello():
    print("Hello World")
```

> 這是引用區塊
> 第二行引用

| 欄位 1 | 欄位 2 | 欄位 3 |
|--------|--------|--------|
| 值 A   | 值 B   | 值 C   |
| 值 D   | 值 E   | 值 F   |
```

### 4️⃣ 視覺對比檢查

使用以下檢查清單，比較 RVT 和 Protocol 的渲染結果：

#### ✅ 列表符號
- [ ] 第一層：○（空心圓）- **兩邊一致**
- [ ] 第二層：■（方塊）- **兩邊一致**
- [ ] 第三層：●（實心圓）- **兩邊一致**
- [ ] 列表符號顏色：黑色 (#000) - **兩邊一致**
- [ ] 列表項目顏色：深灰 (#333) - **兩邊一致**

#### ✅ 間距
- [ ] 標題上下間距 - **兩邊一致**
- [ ] 段落間距 - **兩邊一致**
- [ ] 列表間距 - **兩邊一致**
- [ ] 列表項目內間距 (margin-bottom: 0) - **兩邊一致**

#### ✅ 其他元素
- [ ] 粗體和斜體文字 - **兩邊一致**
- [ ] 行內程式碼樣式 - **兩邊一致**
- [ ] 程式碼區塊樣式 - **兩邊一致**
- [ ] 引用區塊樣式 - **兩邊一致**
- [ ] 表格樣式 - **兩邊一致**

### 5️⃣ 開發者工具檢查

#### 檢查計算樣式（Computed Styles）

在 **RVT Assistant** 中：
1. 右鍵點擊第一層列表項目 → 檢查元素
2. 查看 Computed 標籤
3. 記錄以下屬性值：
   - `list-style-type`: ___________
   - `margin-bottom`: ___________
   - `line-height`: ___________
   - `color`: ___________
   - `padding-left`: ___________

在 **Protocol Assistant** 中：
1. 重複相同步驟
2. 比較數值是否完全一致 ✅

#### 檢查 CSS 規則來源

1. 查看 Styles 標籤
2. 確認以下規則存在：
   - [ ] `.rvt-assistant-chat-page .message-text { all: revert !important; }`
   - [ ] `.rvt-assistant-chat-page .markdown-preview-content.markdown-content ul { list-style-type: circle !important; }`
   - [ ] `.protocol-assistant-chat-page .message-text { all: revert !important; }`
   - [ ] `.protocol-assistant-chat-page .markdown-preview-content.markdown-content ul { list-style-type: circle !important; }`

### 6️⃣ CSS 污染檢查

#### 測試 A：RVT 不影響 Protocol
1. 先進入 RVT Assistant
2. 發送測試訊息
3. 切換到 Protocol Assistant
4. 發送相同測試訊息
5. 確認 Protocol 的列表符號正常 ✅

#### 測試 B：Protocol 不影響 RVT
1. 先進入 Protocol Assistant
2. 發送測試訊息
3. 切換到 RVT Assistant
4. 發送相同測試訊息
5. 確認 RVT 的列表符號正常 ✅

### 7️⃣ 響應式測試

#### 桌面版（>768px）
- [ ] 列表符號正確顯示
- [ ] 間距正常
- [ ] 文字可讀

#### 平板版（768px）
- [ ] 列表符號正確顯示
- [ ] 間距正常
- [ ] 文字可讀

#### 手機版（<480px）
- [ ] 列表符號正確顯示
- [ ] 間距正常
- [ ] 文字可讀

## 🐛 常見問題排查

### 問題 1：列表符號變成數字或消失
**診斷步驟**：
```bash
# 1. 檢查 CSS 是否正確載入
# 在瀏覽器 Console 執行：
document.querySelector('.rvt-assistant-chat-page .markdown-preview-content.markdown-content ul')

# 2. 查看 computed style
getComputedStyle(document.querySelector('.rvt-assistant-chat-page .markdown-preview-content.markdown-content ul')).listStyleType
# 預期輸出：'circle'
```

**可能原因**：
- CSS 快取未清除 → 解決：Ctrl+Shift+R
- 選擇器錯誤 → 檢查是否使用 `.markdown-preview-content.markdown-content`
- 優先級被覆蓋 → 確認有 `!important`

### 問題 2：間距與之前不同
**診斷步驟**：
```bash
# 檢查 margin 是否使用 revert
getComputedStyle(document.querySelector('.rvt-assistant-chat-page .markdown-preview-content.markdown-content p')).margin
```

**可能原因**：
- 缺少 `margin: revert !important` → 添加規則
- 其他樣式覆蓋 → 檢查 Styles 標籤的優先級

### 問題 3：兩個 Assistant 渲染不一致
**診斷步驟**：
1. 使用相同測試內容
2. 使用 DevTools 比較 Computed Styles
3. 找出差異的屬性
4. 檢查對應的 CSS 規則

## 📊 測試結果記錄

### 測試環境
- **日期**：___________
- **瀏覽器**：___________（Chrome / Firefox / Edge）
- **版本**：___________
- **容器狀態**：□ ai-react 已重啟

### 測試結果
- **RVT Assistant**：
  - 列表符號：□ 正常 / □ 異常（描述：__________）
  - 間距：□ 正常 / □ 異常（描述：__________）
  - 其他元素：□ 正常 / □ 異常（描述：__________）

- **Protocol Assistant**：
  - 列表符號：□ 正常 / □ 異常（描述：__________）
  - 間距：□ 正常 / □ 異常（描述：__________）
  - 其他元素：□ 正常 / □ 異常（描述：__________）

- **一致性檢查**：
  - RVT vs Protocol：□ 完全一致 / □ 有差異（描述：__________）

- **CSS 污染檢查**：
  - RVT → Protocol：□ 無污染 / □ 有污染（描述：__________）
  - Protocol → RVT：□ 無污染 / □ 有污染（描述：__________）

### 總體評估
- □ ✅ 通過所有測試
- □ ⚠️ 部分測試失敗（需要修正）
- □ ❌ 多項測試失敗（需要重新檢視）

### 備註
```
（記錄任何額外發現或需要注意的事項）
```

## 🎯 成功標準

模組化成功的標準：
1. ✅ RVT 和 Protocol 的 Markdown 渲染**完全一致**
2. ✅ 兩個 Assistant 之間**沒有 CSS 污染**
3. ✅ 所有測試項目**全部通過**
4. ✅ 響應式設計**在各尺寸都正常**
5. ✅ 開發者工具顯示的計算樣式**完全相同**

---

**📅 建立日期**：2025-10-23  
**📝 版本**：v1.0  
**✍️ 用途**：驗證 AI Assistant 模組化後的一致性
