# Markdown 編輯器 Toolbar 固定問題修復

## 📋 問題描述

在 Protocol Guide / RVT Guide 編輯器中，工具列（toolbar）在頁面滾動時會消失，無法點擊。

### 問題根源

```
外層容器滾動 → 整個編輯器（包括 toolbar）被滾走
```

有兩個滾動層級：
1. **外層容器滾動**：整個頁面內容超出視窗時產生（問題所在）
2. **編輯器內部滾動**：編輯區域的正常滾動（預期行為）

`position: sticky` 只在其直接滾動容器內有效，無法跨越父容器生效。

## 🔧 解決方案

採用 **方案 1（強化 Sticky 定位）+ 方案 A（防止外層滾動）** 的組合：

### 核心策略

1. **防止外層滾動**：確保只有編輯器內部可以滾動
2. **強化 Sticky 定位**：提高 z-index 和完善樣式
3. **優化 Flex 佈局**：確保高度計算正確

## 📝 修改清單

### 1. MarkdownEditorLayout.jsx（整頁編輯器）

#### 修改 1：外層容器
```jsx
// 前
<div style={{
  flex: 1,
  padding: '16px',
  display: 'flex',
  flexDirection: 'column',
  gap: '16px'
}}>

// 後
<div style={{
  flex: 1,
  padding: '16px',
  display: 'flex',
  flexDirection: 'column',
  gap: '16px',
  overflow: 'hidden'  // ✅ 防止外層產生滾動
}}>
```

#### 修改 2：Card 容器
```jsx
// 前
<Card
  style={{
    flex: 1,
    display: 'flex',
    flexDirection: 'column'
  }}
  bodyStyle={{
    flex: 1,
    padding: '16px',
    display: 'flex',
    flexDirection: 'column'
  }}
>

// 後
<Card
  style={{
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    minHeight: 0  // ✅ 允許 flex 子元素正確收縮
  }}
  bodyStyle={{
    flex: 1,
    padding: '16px',
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',  // ✅ 防止 Card 內部產生外層滾動
    minHeight: 0         // ✅ 確保高度受控
  }}
>
```

### 2. MarkdownEditorForm.jsx（Modal 編輯器）

#### 修改 1：Modal bodyStyle
```jsx
// 前
bodyStyle={{ 
  height: 'calc(90vh - 108px)', 
  padding: '16px',
  display: 'flex',
  flexDirection: 'column'
}}

// 後
bodyStyle={{ 
  height: 'calc(90vh - 108px)', 
  padding: '16px',
  display: 'flex',
  flexDirection: 'column',
  overflow: 'hidden'  // ✅ 防止 Modal body 產生滾動
}}
```

#### 修改 2：內容容器
```jsx
// 前
<div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>

// 後
<div style={{ 
  height: '100%', 
  display: 'flex', 
  flexDirection: 'column',
  overflow: 'hidden'  // ✅ 防止外層產生滾動
}}>
```

#### 修改 3：編輯器容器
```jsx
// 前
<div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>

// 後
<div style={{ 
  flex: 1, 
  display: 'flex', 
  flexDirection: 'column',
  minHeight: 0,        // ✅ 允許 flex 子元素正確收縮
  overflow: 'hidden'   // ✅ 防止這層產生滾動
}}>
```

### 3. MarkdownEditorForm.css

#### 修改 1：容器樣式
```css
/* 前 */
.markdown-editor-container {
  overflow: visible !important;
}

/* 後 */
.markdown-editor-container {
  overflow: visible !important;
  display: flex !important;
  flex-direction: column !important;
}

.markdown-editor-container .rc-md-editor {
  flex: 1 !important;  /* ✅ 填滿容器 */
}
```

#### 修改 2：工具列 Sticky
```css
.rc-md-editor .header {
  position: sticky !important;
  position: -webkit-sticky !important;
  top: 0 !important;
  z-index: 10000 !important;  /* ✅ 提高到 10000 */
  flex-shrink: 0 !important;  /* ✅ 防止工具列被壓縮 */
}
```

#### 修改 3：編輯區域滾動
```css
.rc-md-editor .editor-container {
  overflow-y: auto !important;  /* ✅ 唯一應該滾動的地方 */
  min-height: 0 !important;     /* ✅ 允許 flex 子元素正確收縮 */
}

.rc-md-editor .editor-container .section-container {
  height: auto !important;      /* ✅ 讓內容自然撐開 */
  min-height: 100% !important;  /* ✅ 確保至少填滿容器 */
}
```

## 🎯 最終效果

### 滾動層級結構

```
┌─────────────────────────────────────┐
│ 最外層 (overflow: hidden)           │ ❌ 不滾動
│ ┌─────────────────────────────────┐ │
│ │ Card body (overflow: hidden)    │ │ ❌ 不滾動
│ │ ┌─────────────────────────────┐ │ │
│ │ │ .rc-md-editor               │ │ │
│ │ │ ┌─────────────────────────┐ │ │ │
│ │ │ │ Toolbar (sticky)        │ │ │ │ ✅ 固定在頂部
│ │ │ ├─────────────────────────┤ │ │ │
│ │ │ │ .editor-container       │ │ │ │ ✅ 這裡滾動
│ │ │ │ (overflow-y: auto)      │ │ │ │
│ │ │ │ ┌───────────────────┐   │ │ │ │
│ │ │ │ │ 編輯區域          │   │ │ │ │
│ │ │ │ │ (可滾動)          │   │ │ │ │
│ │ │ │ └───────────────────┘   │ │ │ │
│ │ │ └─────────────────────────┘ │ │ │
│ │ └─────────────────────────────┘ │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

### 用戶體驗

- ✅ 向下滾動時，工具列固定在編輯器頂部
- ✅ 工具列按鈕隨時可以點擊
- ✅ 編輯區域可以正常滾動
- ✅ 預覽面板可以獨立滾動
- ✅ 全螢幕模式正常工作
- ✅ 圖片管理功能正常

## 🧪 測試場景

### 基本功能測試
- [ ] 向下滾動，工具列是否固定
- [ ] 點擊工具列按鈕（加粗、斜體等）
- [ ] 插入圖片、連結、表格
- [ ] 全螢幕模式切換

### 不同環境測試
- [ ] Protocol Guide 編輯頁面（整頁）
- [ ] RVT Guide 編輯頁面（整頁）
- [ ] Modal 彈窗編輯器
- [ ] 全螢幕模式

### 瀏覽器相容性
- [ ] Chrome/Edge
- [ ] Firefox
- [ ] Safari
- [ ] 手機瀏覽器

## 🔍 關鍵技術點

### 1. Flex 佈局的 minHeight: 0

```css
/* 問題：flex 子元素預設 min-height: auto */
/* 導致子元素不會收縮到小於內容高度 */

/* 解決：設定 minHeight: 0 */
.container {
  flex: 1;
  minHeight: 0;  /* 允許收縮 */
}
```

### 2. Overflow 層級控制

```
外層：overflow: hidden   → 阻止外層滾動
編輯器：overflow: visible → 讓 sticky 生效
編輯區：overflow-y: auto  → 提供內部滾動
```

### 3. Sticky 定位條件

1. 父元素不能有 `overflow: hidden` 或 `overflow: auto`
2. 必須指定 `top`、`bottom`、`left` 或 `right` 其中之一
3. 元素必須在滾動容器內

## 📚 參考資料

- [CSS Sticky Position](https://developer.mozilla.org/en-US/docs/Web/CSS/position#sticky)
- [Flexbox minHeight Issue](https://stackoverflow.com/questions/36247140/why-doesnt-flex-item-shrink-past-content-size)
- [react-markdown-editor-lite](https://github.com/HarryChen0506/react-markdown-editor-lite)

## 📅 修改歷史

- 2025-10-29: 初始修復 - 方案 1 + 方案 A 組合
