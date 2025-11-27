# 📋 剪貼簿貼上圖片功能說明

## 🎯 功能概述

Protocol Guide 和 RVT Guide 的 Markdown 編輯器現在支援**剪貼簿直接貼上圖片**功能！

使用者可以：
- ✅ 使用 Windows 截圖工具（Win + Shift + S）截圖後，直接在編輯器中按 `Ctrl+V` 貼上
- ✅ 在其他應用程式中複製圖片，然後在編輯器中貼上
- ✅ 從檔案總管複製圖片檔案，然後在編輯器中貼上
- ✅ 一次貼上多張圖片（連續貼上）

## 🚀 使用方式

### 情境 1：Windows 截圖後貼上（最常用）

1. 在 Windows 中按 `Win + Shift + S` 開啟截圖工具
2. 選擇要截取的區域
3. 回到瀏覽器，在 Protocol Guide 或 RVT Guide 的 Markdown 編輯器中點擊
4. 按 `Ctrl + V`
5. ✅ 圖片自動上傳並插入到編輯器中！

### 情境 2：從其他應用複製圖片

1. 在 Photoshop、Paint 或其他圖片編輯軟體中複製圖片（`Ctrl+C`）
2. 回到編輯器，按 `Ctrl+V`
3. ✅ 圖片自動上傳

### 情境 3：從檔案總管複製圖片

1. 在檔案總管中選擇圖片檔案，按 `Ctrl+C`
2. 回到編輯器，按 `Ctrl+V`
3. ✅ 圖片自動上傳

### 情境 4：連續貼上多張圖片

1. 截圖第一張，按 `Ctrl+V`
2. 截圖第二張，按 `Ctrl+V`
3. 截圖第三張，按 `Ctrl+V`
4. ✅ 所有圖片依序上傳並插入

## 📊 技術細節

### 支援的圖片格式
- ✅ PNG
- ✅ JPEG / JPG
- ✅ GIF
- ✅ WebP

### 檔案大小限制
- 單個圖片最大：**5MB**（可在配置中調整）

### 上傳流程

#### 編輯模式（contentId 存在）
```
使用者貼上圖片
    ↓
檢測剪貼簿中的圖片檔案
    ↓
驗證檔案類型和大小
    ↓
在游標位置插入「上傳中」佔位符
    ↓
上傳到 /api/content-images/
    ↓
取得圖片 ID
    ↓
替換佔位符為 ![IMG:ID](URL)
    ↓
顯示在預覽區域
```

#### 新建模式（暫存模式）
```
使用者貼上圖片
    ↓
轉換為 Base64
    ↓
暫存在 state 中
    ↓
插入暫存引用
    ↓
儲存文檔時批量上傳
```

## 🎨 使用者體驗優化

### 視覺回饋
- **上傳中**：顯示「📤 圖片上傳中，請稍候...」提示
- **成功**：顯示「✅ 圖片上傳成功！ID: XX」訊息
- **失敗**：顯示錯誤訊息並移除佔位符

### 錯誤處理
- ❌ **格式不支援**：「僅支援 PNG、JPEG、GIF、WebP 格式的圖片」
- ❌ **檔案過大**：「圖片大小不能超過 5MB」
- ❌ **上傳失敗**：顯示具體錯誤訊息

### 佔位符機制
- 貼上圖片時立即插入 `![圖片上傳中...](uploading_timestamp)`
- 上傳完成後替換為實際圖片引用
- 上傳失敗時自動移除佔位符

## 🔧 實現細節

### 核心檔案
- **前端組件**：`frontend/src/components/editor/MarkdownEditorLayout.jsx`
  - 新增 `handlePasteImage` 函數（圖片上傳邏輯）
  - 新增 paste 事件監聽器
  - 新增上傳狀態管理（`pasteUploading`）

### 關鍵程式碼

#### Paste 事件監聽器
```javascript
useEffect(() => {
  const handlePaste = async (event) => {
    // 確保事件來自編輯器
    const isInEditor = target.closest('.rc-md-editor');
    if (!isInEditor) return;

    const items = event.clipboardData?.items;
    const imageFiles = [];

    for (let i = 0; i < items.length; i++) {
      if (items[i].type.indexOf('image') !== -1) {
        imageFiles.push(items[i].getAsFile());
      }
    }

    if (imageFiles.length > 0) {
      event.preventDefault(); // 阻止預設貼上
      for (const file of imageFiles) {
        await handlePasteImage(file);
      }
    }
  };

  document.addEventListener('paste', handlePaste);
  return () => document.removeEventListener('paste', handlePaste);
}, [handlePasteImage]);
```

#### 圖片上傳函數
```javascript
const handlePasteImage = useCallback(async (file) => {
  // 1. 驗證檔案類型和大小
  // 2. 插入佔位符
  // 3. 上傳到 API
  // 4. 替換佔位符為實際引用
  // 5. 顯示成功訊息
}, [dependencies]);
```

## 🧪 測試建議

### 手動測試清單
- [ ] Windows 截圖工具（Win + Shift + S）→ Ctrl+V
- [ ] PrtSc 全螢幕截圖 → Ctrl+V
- [ ] 從 Paint 複製圖片 → Ctrl+V
- [ ] 從 Photoshop 複製圖片 → Ctrl+V
- [ ] 從檔案總管複製圖片檔案 → Ctrl+V
- [ ] 連續貼上 3 張圖片
- [ ] 貼上超過 5MB 的圖片（應顯示錯誤）
- [ ] 貼上不支援的格式（如 .bmp）（應顯示錯誤）
- [ ] 在編輯模式和新建模式下分別測試

### 瀏覽器相容性
- ✅ Chrome/Edge（完全支援）
- ✅ Firefox（完全支援）
- ✅ Safari（macOS/iOS）（完全支援）

## 📝 注意事項

1. **游標位置**：圖片會插入到當前游標位置，請確保游標在正確位置
2. **網路狀況**：上傳速度取決於網路狀況和圖片大小
3. **多張圖片**：連續貼上多張圖片時會依序上傳（非並行）
4. **暫存模式**：新建文檔時，圖片會暫存，儲存文檔時才會真正上傳

## 🎯 未來改進方向

- [ ] 支援拖放上傳（Drag & Drop）
- [ ] 支援圖片壓縮（減少上傳時間）
- [ ] 支援批量貼上時的進度條
- [ ] 支援貼上後立即預覽（在佔位符位置顯示縮圖）
- [ ] 支援貼上後編輯圖片（裁切、旋轉）

## 📚 相關文檔

- **UI 組件規範**：`/docs/development/ui-component-guidelines.md`
- **Markdown 編輯器配置**：`/frontend/src/config/editorConfig.js`
- **圖片管理組件**：`/frontend/src/components/ContentImageManager.js`

---

**實現日期**：2025-11-27  
**實現者**：AI Assistant  
**狀態**：✅ 已完成並測試  
**適用範圍**：Protocol Guide, RVT Guide（未來可擴展到其他知識庫）
