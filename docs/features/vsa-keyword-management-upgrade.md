# VSA 測試案例 - Keyword 管理介面升級

## 📋 更新概述

將原本的 `Select Tags` 模式升級為更直觀的 **Input + Button + Tag List** 介面，大幅提升用戶體驗。

**更新日期**：2025-11-26  
**影響範圍**：VSA 測試案例編輯功能

---

## 🎨 新版介面設計

### 視覺佈局

```
┌─────────────────────────────────────────────────────────────┐
│ * Keyword 判斷條件                                  📄 提示  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ┌──────────────────────────────────────┐  ┌──────────┐     │
│ │ 輸入關鍵字後按 Enter 或點擊添加...    │  │ ➕ 添加  │     │
│ └──────────────────────────────────────┘  └──────────┘     │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 已添加的關鍵字 (4)：            [ 🗑️ 清空全部 ]       │ │
│ │                                                         │ │
│ │  [Kingston ❌]  [Linux ❌]  [磁卡 ❌]                   │ │
│ │  [Kingston Linux ❌]                                    │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ 💡 提示：輸入關鍵字後按 Enter 也可快速添加                 │
└─────────────────────────────────────────────────────────────┘
```

---

## ✨ 主要改進

### 1. **更直觀的操作**

**舊版**：
- ❌ 用戶不知道要按 Enter
- ❌ 添加方式不明確
- ❌ 標籤太小，不易點擊

**新版**：
- ✅ 明確的「添加」按鈕
- ✅ 支援兩種添加方式（按鈕 + Enter）
- ✅ 大標籤易於識別和刪除

### 2. **視覺反饋更好**

**新增功能**：
- 📊 顯示關鍵字數量 `(4)`
- 🎨 關鍵字以紫色大標籤呈現
- 📦 獨立的展示區域（灰色背景）
- 🗑️ 批量清空按鈕
- 💡 友好的提示文字

### 3. **錯誤處理**

**防護機制**：
- 🚫 不允許添加空白關鍵字
- 🚫 不允許添加重複關鍵字
- ⚠️ 保存時驗證至少有一個關鍵字
- 📝 清空全部需要二次確認

---

## 🔧 技術實現

### State 管理

```javascript
// 新增的 state
const [keywordInput, setKeywordInput] = useState('');  // 輸入框內容
const [keywords, setKeywords] = useState([]);          // 關鍵字陣列
```

### 核心函數

#### 1. **添加關鍵字**
```javascript
const handleAddKeyword = () => {
  const trimmedKeyword = keywordInput.trim();
  
  // 驗證：不允許空白
  if (!trimmedKeyword) {
    message.warning('請輸入關鍵字');
    return;
  }
  
  // 驗證：不允許重複
  if (keywords.includes(trimmedKeyword)) {
    message.warning('此關鍵字已存在');
    return;
  }
  
  // 添加到陣列
  setKeywords([...keywords, trimmedKeyword]);
  setKeywordInput(''); // 清空輸入框
};
```

#### 2. **刪除關鍵字**
```javascript
const handleRemoveKeyword = (keywordToRemove) => {
  setKeywords(keywords.filter(k => k !== keywordToRemove));
};
```

#### 3. **清空全部**
```javascript
const handleClearAllKeywords = () => {
  Modal.confirm({
    title: '確認清空',
    content: '確定要清空所有關鍵字嗎？',
    onOk: () => {
      setKeywords([]);
      message.success('已清空所有關鍵字');
    },
  });
};
```

#### 4. **保存驗證**
```javascript
const handleSaveEdit = async () => {
  // 驗證關鍵字
  if (keywords.length === 0) {
    message.error('請至少添加一個關鍵字');
    return;
  }
  
  // ... 其他邏輯
  const updateData = {
    answer_keywords: keywords, // 使用 keywords state
    // ...
  };
};
```

---

## 🎯 使用流程

### 1. **打開編輯頁面**
用戶點擊測試案例的「編輯」按鈕

### 2. **查看現有關鍵字**
自動載入現有的關鍵字並顯示在展示區域

### 3. **添加新關鍵字**

**方式 A：使用按鈕**
1. 在輸入框輸入關鍵字
2. 點擊「添加」按鈕
3. 關鍵字出現在展示區域

**方式 B：使用快捷鍵**
1. 在輸入框輸入關鍵字
2. 按 `Enter` 鍵
3. 關鍵字出現在展示區域

### 4. **刪除關鍵字**

**刪除單個**：點擊標籤上的 `❌` 圖標

**刪除全部**：點擊「清空全部」按鈕，確認後清空

### 5. **保存修改**
點擊「保存修改」按鈕

---

## 🎨 UI 元素說明

### 輸入區域
```javascript
<div style={{ display: 'flex', gap: 8 }}>
  <Input 
    placeholder="輸入關鍵字後按 Enter 或點擊添加..."
    onPressEnter={handleAddKeyword}
  />
  <Button type="primary" icon={<PlusOutlined />}>
    添加
  </Button>
</div>
```

### 展示區域
```javascript
<div style={{ 
  padding: '12px', 
  background: '#fafafa',  // 淺灰背景
  borderRadius: '6px',
  border: '1px solid #d9d9d9',
  minHeight: '80px'       // 最小高度
}}>
  {/* 標題列 */}
  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
    <span>已添加的關鍵字 ({keywords.length})：</span>
    <Button danger size="small">清空全部</Button>
  </div>
  
  {/* 關鍵字標籤 */}
  <Space wrap>
    {keywords.map(keyword => (
      <Tag 
        closable 
        color="purple"
        style={{ fontSize: '14px', padding: '6px 10px' }}
      >
        {keyword}
      </Tag>
    ))}
  </Space>
</div>
```

### 空狀態
```javascript
{keywords.length === 0 && (
  <div style={{ 
    textAlign: 'center', 
    color: '#bfbfbf',
    padding: '20px 0'
  }}>
    尚未添加關鍵字
  </div>
)}
```

---

## ⚠️ 錯誤處理

### 1. **輸入驗證**
| 情況 | 處理方式 | 訊息 |
|------|----------|------|
| 空白輸入 | 阻止添加 | "請輸入關鍵字" |
| 重複關鍵字 | 阻止添加 | "此關鍵字已存在" |
| 保存時無關鍵字 | 阻止保存 | "請至少添加一個關鍵字" |

### 2. **操作確認**
```javascript
// 清空全部需要確認
Modal.confirm({
  title: '確認清空',
  content: '確定要清空所有關鍵字嗎？',
  onOk: () => { /* 清空 */ }
});
```

---

## 📊 對比分析

| 特性 | 舊版 (Select Tags) | 新版 (Input + Button + Tag List) |
|------|-------------------|----------------------------------|
| **直觀性** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **易用性** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **視覺反饋** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **錯誤提示** | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **批量操作** | ❌ | ✅ (清空全部) |
| **關鍵字數量顯示** | ❌ | ✅ |
| **大標籤顯示** | ❌ | ✅ |
| **快捷鍵支援** | ✅ | ✅ |
| **防重複檢查** | ❌ | ✅ |
| **空值檢查** | ❌ | ✅ |

---

## 🚀 未來擴展

### 可能的改進方向

1. **關鍵字模板**
   - 保存常用關鍵字組合
   - 快速套用模板

2. **關鍵字分類**
   - 品牌、型號、功能等分類
   - 不同分類使用不同顏色

3. **智能建議**
   - 根據問題內容自動建議關鍵字
   - 顯示歷史常用關鍵字

4. **批量導入**
   - 從 CSV 導入關鍵字
   - 從其他測試案例複製

5. **關鍵字統計**
   - 顯示每個關鍵字的使用頻率
   - 推薦熱門關鍵字

6. **拖拽排序**
   - 調整關鍵字順序
   - 支援優先級設定

---

## 📝 修改文件

### 前端文件
- `frontend/src/pages/benchmark/UnifiedTestCasePage.js`
  - 新增 `keywordInput` state
  - 新增 `keywords` state
  - 新增 `handleAddKeyword()` 函數
  - 新增 `handleRemoveKeyword()` 函數
  - 新增 `handleClearAllKeywords()` 函數
  - 修改 `handleEdit()` 初始化邏輯
  - 修改 `handleSaveEdit()` 驗證邏輯
  - 修改 `handleCancelEdit()` 清理邏輯
  - 更新 Keyword 表單項 UI

### 文檔文件
- `docs/features/vsa-keyword-management-upgrade.md` (本文件)
- `docs/features/vsa-test-case-edit-feature.md` (已更新)

---

## ✅ 測試檢查清單

### 功能測試
- [ ] 輸入框輸入並點擊「添加」按鈕
- [ ] 輸入框輸入並按 Enter 鍵
- [ ] 點擊標籤的 X 刪除單個關鍵字
- [ ] 點擊「清空全部」刪除所有關鍵字
- [ ] 嘗試添加空白關鍵字（應該被阻止）
- [ ] 嘗試添加重複關鍵字（應該被阻止）
- [ ] 清空所有關鍵字後保存（應該被阻止）
- [ ] 正常添加關鍵字並保存
- [ ] 取消編輯後重新打開（狀態正確重置）

### UI 測試
- [ ] 關鍵字數量顯示正確
- [ ] 標籤顏色正確（紫色）
- [ ] 標籤大小適中（易於點擊）
- [ ] 展示區域最小高度正確
- [ ] 空狀態提示顯示正常
- [ ] 提示文字顯示正常
- [ ] 清空全部按鈕在有關鍵字時才顯示

### 邏輯測試
- [ ] 編輯不同測試案例，關鍵字正確載入
- [ ] 保存後表格數據正確更新
- [ ] 錯誤訊息正確顯示
- [ ] 成功訊息正確顯示

---

## 🎓 用戶培訓要點

1. **兩種添加方式**：按鈕或 Enter 鍵
2. **不允許重複**：系統會自動檢查
3. **必須有關鍵字**：保存時至少要有一個
4. **批量清空**：點擊「清空全部」可快速清空
5. **數量提示**：可以隨時看到已添加多少個關鍵字

---

## 📞 問題反饋

如果遇到問題，請提供：
1. 操作步驟
2. 預期行為
3. 實際行為
4. 截圖（如果可能）

---

**更新時間**：2025-11-26  
**版本**：v2.0  
**負責人**：AI Platform Team  
**狀態**：✅ 已完成並部署
