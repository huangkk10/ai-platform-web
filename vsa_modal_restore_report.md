# VSA 測試案例 - 恢復內部 Modal 新增功能報告

## 📋 問題描述

用戶點擊「新增問題」按鈕後，跳轉到 Google Forms 錯誤頁面（Dynamic Link Not Found），因為代碼中使用了佔位符 URL `https://forms.gle/YOUR_GOOGLE_FORM_ID`。

## 🔍 根本原因

之前誤解需求，將內部的 Modal 新增功能改成了外部 Google Forms 表單，但用戶實際需要的是**內部 Modal 彈窗**來新增測試案例。

## ✅ 修復內容

### 1. 恢復 `showAddModal` 函數

**位置**：`frontend/src/pages/dify-benchmark/DifyTestCasePage.js` 第 220-228 行

```javascript
// 顯示新增 Modal
const showAddModal = () => {
  setIsEditMode(false);
  setSelectedTestCase(null);
  setKeywords([]);
  setKeywordInput('');
  form.resetFields();
  setEditModalVisible(true);
};
```

**功能**：
- 清空表單狀態
- 重置關鍵字陣列
- 設定為新增模式（非編輯模式）
- 開啟編輯 Modal

### 2. 修改頂部按鈕事件處理

**位置**：第 147-150 行

**修改前**：
```javascript
const handleCreateEvent = () => {
  console.log('收到新增問題事件 - 開啟外部表單');
  window.open('https://forms.gle/YOUR_GOOGLE_FORM_ID', '_blank');
};
```

**修改後**：
```javascript
const handleCreateEvent = () => {
  console.log('收到新增問題事件 - 打開新增 Modal');
  showAddModal();
};
```

### 3. 修改頁面內「新增測試案例」按鈕

**位置**：第 703-708 行

**修改前**：
```javascript
<Button
  type="primary"
  icon={<PlusOutlined />}
  onClick={() => {
    window.open('https://forms.gle/YOUR_GOOGLE_FORM_ID', '_blank');
  }}
>
  新增測試案例
</Button>
```

**修改後**：
```javascript
<Button
  type="primary"
  icon={<PlusOutlined />}
  onClick={showAddModal}
>
  新增測試案例
</Button>
```

## 🎯 功能驗證

### 測試步驟

1. **瀏覽器訪問**：http://localhost/benchmark/dify/test-cases
2. **測試頂部按鈕**：點擊頁面右上角的「新增問題」按鈕
3. **測試卡片按鈕**：點擊卡片右上角的「新增測試案例」按鈕
4. **預期結果**：
   - ✅ 應該彈出內部 Modal 彈窗
   - ✅ Modal 標題為「新增測試案例」
   - ✅ 表單內所有欄位為空白（初始狀態）
   - ✅ 可以填寫並提交新測試案例

### 表單欄位檢查

Modal 中應該包含以下欄位：

**基本資訊**：
- ✅ 問題內容（question）- 必填
- ✅ 難度（difficulty）- 下拉選單：easy/medium/hard

**進階選項**：
- ✅ 預期答案（expected_answer）- 文本框
- ✅ 答案關鍵字（answer_keywords）- 動態標籤輸入
- ✅ 最高分數（max_score）- 數字輸入
- ✅ 標籤（tags）- 標籤選擇
- ✅ 來源（source）- 文本輸入
- ✅ 備註（notes）- 文本框
- ✅ 啟用狀態（is_active）- 開關

## 📊 編譯狀態

```
✅ webpack compiled successfully
✅ 無錯誤
✅ 無警告
```

## 🔄 與之前版本的對比

| 功能 | 之前（錯誤版本） | 現在（修復後） |
|------|-----------------|---------------|
| 點擊「新增問題」 | 跳轉到 Google Forms 錯誤頁面 | 打開內部 Modal 彈窗 |
| 點擊「新增測試案例」 | 跳轉到 Google Forms 錯誤頁面 | 打開內部 Modal 彈窗 |
| 新增方式 | 外部表單（不可用） | 內部 Modal（可用） |
| 資料流程 | 需要手動匯入 | 直接儲存到資料庫 |

## 📝 後續建議

### 選項 1：保持內部 Modal（推薦）
✅ 優點：
- 用戶體驗更好（不需要跳轉）
- 資料即時儲存到資料庫
- 支援即時驗證
- 完整的 CRUD 功能

❌ 缺點：
- 需要維護前端表單

### 選項 2：改用外部 Google Forms（如果未來需要）
✅ 優點：
- 減少前端維護成本
- 可以使用 Google Forms 的進階功能

❌ 缺點：
- 需要手動匯入資料
- 用戶體驗較差（需要跳轉）
- 需要創建並維護 Google Forms

## 🎉 完成狀態

- ✅ `showAddModal` 函數已恢復
- ✅ 頂部「新增問題」按鈕已修復
- ✅ 卡片「新增測試案例」按鈕已修復
- ✅ React 容器編譯成功
- ✅ 無任何錯誤或警告
- ⚠️ 需要在瀏覽器中測試驗證

## 📅 修復時間

**修復日期**：2024-11-27  
**修復人員**：AI Assistant  
**修復類型**：回滾外部表單功能，恢復內部 Modal

---

**下一步**：請在瀏覽器中測試點擊「新增問題」和「新增測試案例」按鈕，確認 Modal 彈窗正常顯示。
