# Bug 修復：編輯 Modal 權重值與表格不同步

## 🐛 問題描述

### 症狀
在 Threshold Settings 管理頁面：
1. 表格顯示：標題權重 **0%**，內容權重 **100%**
2. 點擊「編輯」按鈕開啟 Modal
3. Modal 顯示：標題權重 **60%**，內容權重 **100%**
4. ⚠️ 警告提示：標題權重 + 內容權重 = 160%（不等於 100%）

### 影響範圍
當使用者設定權重為 **0%** 或其他 falsy 值時，編輯 Modal 無法正確載入實際的資料庫值。

---

## 🔍 根本原因

### 問題程式碼（修復前）

```javascript
// frontend/src/pages/admin/ThresholdSettingsPage.js - LINE 78-83

const handleEdit = (record) => {
  setEditingRecord(record);
  form.setFieldsValue({
    master_threshold: parseFloat(record.master_threshold) * 100,
    title_weight: record.title_weight || 60,        // ❌ 問題在這裡
    content_weight: record.content_weight || 40     // ❌ 問題在這裡
  });
  setEditModalVisible(true);
};
```

### 問題分析

JavaScript 的 `||` (邏輯 OR) 運算子行為：
- `0 || 60` → 回傳 `60`（因為 `0` 是 falsy 值）
- `null || 60` → 回傳 `60`
- `undefined || 60` → 回傳 `60`
- `100 || 60` → 回傳 `100`

**實際情境**：
```javascript
// 資料庫值：title_weight = 0, content_weight = 100

form.setFieldsValue({
  title_weight: 0 || 60,        // 結果：60 ❌ 錯誤！
  content_weight: 100 || 40     // 結果：100 ✅ 正確
});

// Modal 顯示：60% / 100% = 160% ⚠️ 警告
// 實際應該：0% / 100% = 100% ✅
```

---

## ✅ 解決方案

### 修復後的程式碼

```javascript
// frontend/src/pages/admin/ThresholdSettingsPage.js - LINE 78-83

const handleEdit = (record) => {
  setEditingRecord(record);
  form.setFieldsValue({
    master_threshold: parseFloat(record.master_threshold) * 100,
    // ✅ 使用明確的 null/undefined 檢查，而不是 falsy 檢查
    title_weight: record.title_weight !== null && record.title_weight !== undefined 
      ? record.title_weight 
      : 60,
    content_weight: record.content_weight !== null && record.content_weight !== undefined 
      ? record.content_weight 
      : 40
  });
  setEditModalVisible(true);
};
```

### 修復邏輯說明

使用明確的 `!== null && !== undefined` 檢查：
- `0 !== null && 0 !== undefined` → `true` → 使用 `0` ✅
- `100 !== null && 100 !== undefined` → `true` → 使用 `100` ✅
- `null !== null` → `false` → 使用預設值 `60`
- `undefined !== undefined` → `false` → 使用預設值 `60`

**實際情境（修復後）**：
```javascript
// 資料庫值：title_weight = 0, content_weight = 100

form.setFieldsValue({
  title_weight: 0 !== null && 0 !== undefined ? 0 : 60,        // 結果：0 ✅ 正確！
  content_weight: 100 !== null && 100 !== undefined ? 100 : 40 // 結果：100 ✅ 正確
});

// Modal 顯示：0% / 100% = 100% ✅ 正確！
```

---

## 🧪 測試驗證

### 測試場景 1：權重為 0%
1. 設定 Protocol Assistant 權重為 **0% / 100%**
2. 儲存並關閉 Modal
3. 重新開啟編輯 Modal
4. **預期結果**：顯示 **0% / 100%** ✅
5. **修復前**：顯示 **60% / 100%** ❌

### 測試場景 2：權重為 100%
1. 設定 Protocol Assistant 權重為 **100% / 0%**
2. 儲存並關閉 Modal
3. 重新開啟編輯 Modal
4. **預期結果**：顯示 **100% / 0%** ✅
5. **修復前**：顯示 **100% / 40%** ❌

### 測試場景 3：正常權重
1. 設定權重為 **60% / 40%**
2. 儲存並關閉 Modal
3. 重新開啟編輯 Modal
4. **預期結果**：顯示 **60% / 40%** ✅
5. **修復前**：顯示 **60% / 40%** ✅（這個案例沒問題）

### 測試場景 4：資料庫為 null（新記錄）
1. 假設資料庫中 `title_weight` 和 `content_weight` 為 `null`
2. 開啟編輯 Modal
3. **預期結果**：顯示預設值 **60% / 40%** ✅
4. **修復前後都正確** ✅

---

## 📊 部署狀態

### 修改的檔案
- ✅ `/frontend/src/pages/admin/ThresholdSettingsPage.js` (LINE 78-83)

### 服務重啟
- ✅ React 前端服務已重啟
- ✅ 新程式碼已生效

---

## 🎯 驗證步驟

### 1. 刷新瀏覽器
```bash
# 清除快取並重新載入
Ctrl + Shift + R  (Windows/Linux)
Cmd + Shift + R   (Mac)
```

### 2. 測試 0% 權重
1. 開啟 http://localhost/admin/threshold-settings
2. 點擊 Protocol Assistant 的「編輯」按鈕
3. **確認 Modal 顯示**：
   - 標題權重：**0%**（不是 60%）
   - 內容權重：**100%**
   - 無警告訊息 ⚠️
   - 即時預覽顯示：權重比例 **0 : 100**

### 3. 測試滑桿調整
1. 拖動標題權重滑桿到 **20%**
2. 確認內容權重自動變為 **80%**
3. 點擊「儲存」
4. 重新開啟 Modal
5. **確認顯示**：**20% / 80%**（不是 20% / 40%）

---

## 📚 相關 JavaScript 知識

### Falsy 值列表
JavaScript 中的 falsy 值（在布林上下文中視為 `false`）：
1. `false`
2. `0`
3. `-0`
4. `0n` (BigInt zero)
5. `""` (空字串)
6. `null`
7. `undefined`
8. `NaN`

### 最佳實踐

❌ **錯誤做法**（預設值處理）：
```javascript
const value = record.field || defaultValue;  // 0 會被當作 falsy
```

✅ **正確做法 1**（明確檢查）：
```javascript
const value = record.field !== null && record.field !== undefined 
  ? record.field 
  : defaultValue;
```

✅ **正確做法 2**（使用 Nullish Coalescing）：
```javascript
const value = record.field ?? defaultValue;  // 只有 null/undefined 才使用預設值
// 注意：需要現代瀏覽器支援 ES2020+
```

**比較**：
```javascript
const record = { title_weight: 0 };

// 錯誤：使用 ||
console.log(record.title_weight || 60);  // 輸出：60 ❌

// 正確：使用明確檢查
console.log(record.title_weight !== null && record.title_weight !== undefined 
  ? record.title_weight 
  : 60);  // 輸出：0 ✅

// 正確：使用 ?? (ES2020+)
console.log(record.title_weight ?? 60);  // 輸出：0 ✅
```

---

## 🎓 經驗教訓

### 1. 數字 0 是有效值
在權重、百分比、計數等場景中，`0` 是完全合法的值，不應該被視為「沒有值」。

### 2. 明確檢查 vs 隱式轉換
使用明確的 `!== null && !== undefined` 比依賴 JavaScript 的 truthy/falsy 轉換更安全。

### 3. 表單預設值設定
在設定表單預設值時，特別注意：
- 數字欄位可能為 `0`
- 布林欄位可能為 `false`
- 字串欄位可能為 `""`（空字串）

這些都是有效值，不應該被預設值覆蓋。

### 4. 測試邊界值
測試時應該包含邊界情況：
- 最小值（0, -1, 空字串等）
- 最大值（100, Infinity, 很長的字串等）
- null/undefined
- 特殊值（NaN, 負數等）

---

## 🔗 相關問題

### 問題 1：為什麼 Modal 顯示 160%？
因為載入了錯誤的預設值：
- 標題權重：60%（應該是 0%）
- 內容權重：100%（正確）
- 總和：160% ⚠️

### 問題 2：為什麼表格顯示正確？
表格直接從 API 獲取資料，沒有經過 `||` 運算子處理：
```javascript
render: (value) => <Text>{value}%</Text>  // 直接顯示 API 回傳的值
```

### 問題 3：儲存後為什麼表格會更新？
因為 `handleSave` 成功後會呼叫 `fetchSettings()`，重新從 API 載入資料。

---

## ✅ 總結

### 問題
Modal 編輯時，權重值 `0` 被錯誤地替換為預設值 `60`，因為使用了 `||` 運算子。

### 原因
JavaScript 的 `||` 運算子將 `0` 視為 falsy 值，導致使用了預設值。

### 修復
使用明確的 `!== null && !== undefined` 檢查，而不是依賴 truthy/falsy 轉換。

### 驗證
刷新瀏覽器後，開啟編輯 Modal 應該顯示正確的 `0%` 權重值。

---

**更新日期**：2025-11-06  
**修復者**：AI Assistant  
**狀態**：✅ 已修復並部署  
**測試狀態**：⚠️ 等待用戶驗證
