# VSA 測試案例表單簡化與外部整合

**日期**：2025-11-27  
**版本**：v2.0  
**類型**：功能優化

---

## 📋 變更概述

根據用戶需求，對 VSA 測試案例管理頁面進行以下三項重要優化：

### ✅ 已完成的變更

1. **移除「類別」欄位**（基本資訊區塊）
2. **移除「測試類別」和「問題類型」欄位**（進階選項區塊）
3. **改用外部表單**：「新增測試案例」按鈕改為直接開啟外部 URL

---

## 🎯 變更詳情

### 1️⃣ 移除「類別」欄位

**位置**：新增/編輯 Modal → 基本資訊區塊

**變更前**：
```javascript
<Row gutter={16}>
  <Col span={12}>
    <Form.Item name="difficulty_level" label="難度等級" />
  </Col>
  <Col span={12}>
    <Form.Item name="category" label="類別" required />  // ❌ 已移除
  </Col>
</Row>
```

**變更後**：
```javascript
<Form.Item name="difficulty_level" label="難度等級" required />
// 類別欄位已完全移除
```

**影響**：
- ✅ 表單更簡潔
- ✅ 減少用戶填寫負擔
- ⚠️ 資料庫 `category` 欄位保留（但新增時不再要求填寫）

---

### 2️⃣ 移除「測試類別」和「問題類型」欄位

**位置**：新增/編輯 Modal → 進階選項區塊

**變更前**：
```javascript
<Divider orientation="left">進階選項</Divider>
<Row gutter={16}>
  <Col span={12}>
    <Form.Item label="測試類別" name="test_class_name" />  // ❌ 已移除
  </Col>
  <Col span={12}>
    <Form.Item label="問題類型" name="question_type" />    // ❌ 已移除
  </Col>
</Row>
<Form.Item name="tags" label="標籤" />
```

**變更後**：
```javascript
<Divider orientation="left">進階選項</Divider>
<Form.Item name="tags" label="標籤" />
<Form.Item name="source" label="來源" />
<Form.Item name="notes" label="備註" />
```

**影響**：
- ✅ 進階選項更精簡
- ✅ 只保留必要的標籤、來源、備註欄位
- ⚠️ 資料庫欄位保留（但不在表單中顯示）

---

### 3️⃣ 新增測試案例改用外部表單

**位置**：
- 頂部「新增問題」按鈕（App.js 觸發）
- 卡片內「新增測試案例」按鈕

**變更前**：
```javascript
// 點擊按鈕 → 打開 Modal 表單
<Button onClick={showAddModal}>新增測試案例</Button>
```

**變更後**：
```javascript
// 點擊按鈕 → 在新分頁開啟外部表單
<Button onClick={() => window.open('https://forms.gle/YOUR_GOOGLE_FORM_ID', '_blank')}>
  新增測試案例
</Button>
```

**功能說明**：

1. **頂部「新增問題」按鈕**（來自 App.js）
   - 事件：`vsa-test-case-create`
   - 行為：`window.open()` 開啟外部表單（新分頁）
   - Console 訊息：`收到新增問題事件 - 開啟外部表單`

2. **卡片內「新增測試案例」按鈕**
   - 直接點擊按鈕
   - 行為：`window.open()` 開啟外部表單（新分頁）

**優點**：
- ✅ 使用專業表單工具（Google Forms / Microsoft Forms）
- ✅ 更好的用戶體驗（表單驗證、自動儲存）
- ✅ 資料收集更彈性
- ✅ 可結合 Webhook 自動同步到系統

---

## 🔧 配置外部表單 URL

### 步驟 1：創建 Google Forms 表單

1. 訪問 [Google Forms](https://forms.google.com/)
2. 創建新表單，包含以下欄位：
   - 測試問題（長文本）
   - 難度等級（選擇題：簡單/中等/困難）
   - 期望答案（長文本）
   - 答案關鍵字（短文本，說明：多個關鍵字用逗號分隔）
   - 滿分（數字，預設 100）
   - 標籤（短文本，說明：多個標籤用逗號分隔）
   - 來源（短文本）
   - 備註（長文本）

### 步驟 2：獲取表單連結

1. 點擊「傳送」→ 「連結」
2. 複製完整 URL（格式：`https://forms.gle/xxxxx`）

### 步驟 3：更新程式碼中的 URL

**檔案**：`frontend/src/pages/dify-benchmark/DifyTestCasePage.js`

找到以下兩處並替換 URL：

```javascript
// 位置 1：頂部按鈕事件處理
const handleCreateEvent = () => {
  window.open('https://forms.gle/YOUR_GOOGLE_FORM_ID', '_blank');
  //          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ 替換為您的表單 URL
};

// 位置 2：卡片內按鈕
<Button onClick={() => {
  window.open('https://forms.gle/YOUR_GOOGLE_FORM_ID', '_blank');
  //          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ 替換為您的表單 URL
}}>
```

### 步驟 4：重啟服務

```bash
docker restart ai-react
```

---

## 📊 表單欄位對應

| Google Forms 欄位 | 資料庫欄位 | 類型 | 必填 |
|------------------|-----------|------|------|
| 測試問題 | `question` | 長文本 | ✅ |
| 難度等級 | `difficulty_level` | 選項 | ✅ |
| 期望答案 | `expected_answer` | 長文本 | ✅ |
| 答案關鍵字 | `answer_keywords` | JSON Array | ⚠️ 建議填寫 |
| 滿分 | `max_score` | 數字 | ❌（預設 100） |
| 標籤 | `tags` | JSON Array | ❌ |
| 來源 | `source` | 文本 | ❌ |
| 備註 | `notes` | 長文本 | ❌ |

---

## 🔗 整合方式選項

### 方案 A：手動匯入（簡單）

1. Google Forms 回應匯出為 CSV
2. 轉換為 JSON 格式
3. 使用「匯入」功能批量上傳

### 方案 B：自動同步（進階）

1. **使用 Google Apps Script**
   ```javascript
   function onFormSubmit(e) {
     var formResponse = e.response;
     var items = formResponse.getItemResponses();
     
     // 構建 JSON 資料
     var data = {
       question: items[0].getResponse(),
       difficulty_level: items[1].getResponse(),
       expected_answer: items[2].getResponse(),
       answer_keywords: items[3].getResponse().split(','),
       // ... 其他欄位
     };
     
     // POST 到 Django API
     var url = 'http://your-domain.com/api/dify-benchmark/test-cases/';
     UrlFetchApp.fetch(url, {
       method: 'POST',
       contentType: 'application/json',
       payload: JSON.stringify(data),
       headers: {
         'Authorization': 'Token YOUR_API_TOKEN'
       }
     });
   }
   ```

2. **設定觸發器**：表單提交時執行

### 方案 C：使用 Zapier / Make.com

1. 連接 Google Forms 和 Webhook
2. 設定資料轉換規則
3. 自動 POST 到 Django API

---

## 🧪 測試步驟

### 1. 測試外部表單連結

```bash
# 訪問頁面
http://localhost/benchmark/dify/test-cases

# 測試步驟
1. 點擊頂部「新增問題」按鈕
2. 確認新分頁開啟外部表單
3. 點擊卡片內「新增測試案例」按鈕
4. 確認新分頁開啟外部表單
5. 檢查 Console 是否有「開啟外部表單」訊息
```

### 2. 測試編輯功能

```bash
# 編輯現有測試案例
1. 點擊任一測試案例的「編輯」按鈕
2. 確認 Modal 正常打開
3. 確認不再顯示「類別」欄位
4. 確認不再顯示「測試類別」和「問題類型」欄位
5. 修改資料並儲存
6. 確認更新成功
```

### 3. 測試關鍵字功能

```bash
# 關鍵字添加/刪除
1. 開啟編輯 Modal
2. 在關鍵字輸入框輸入文字
3. 按 Enter 或點擊「添加」
4. 確認關鍵字顯示為紫色 Tag
5. 點擊 Tag 的 X 刪除關鍵字
6. 確認關鍵字移除
```

---

## 📝 資料庫影響

### 保留的欄位（不再在表單中顯示）

```sql
-- 這些欄位仍然存在於資料庫中
ALTER TABLE unified_benchmark_test_case
  -- category VARCHAR(100)           -- 保留但不要求填寫
  -- test_class_name VARCHAR(200)    -- 保留但不在表單中
  -- question_type VARCHAR(100)      -- 保留但不在表單中
;
```

### 新增測試案例的預設值

```python
# 透過外部表單新增時，可能需要補充以下預設值
{
    'test_type': 'vsa',              # 固定為 VSA
    'is_active': True,               # 預設啟用
    'max_score': 100,                # 預設滿分
    'category': None,                # 允許為空
    'test_class_name': None,         # 允許為空
    'question_type': None,           # 允許為空
}
```

---

## 🔄 回滾計畫

如果需要恢復原本的 Modal 表單：

### 步驟 1：恢復 showAddModal 函數

```javascript
const showAddModal = () => {
  setIsEditMode(false);
  setSelectedTestCase(null);
  form.resetFields();
  setKeywords([]);
  setKeywordInput('');
  form.setFieldsValue({
    test_type: 'vsa',
    difficulty_level: 'medium',
    is_active: true,
    max_score: 100,
  });
  setEditModalVisible(true);
};
```

### 步驟 2：恢復按鈕點擊事件

```javascript
// 頂部按鈕
const handleCreateEvent = () => {
  showAddModal();
};

// 卡片按鈕
<Button onClick={showAddModal}>新增測試案例</Button>
```

### 步驟 3：恢復欄位（如需要）

```javascript
// 恢復類別欄位
<Form.Item name="category" label="類別" required>
  <Select mode="tags" maxCount={1} />
</Form.Item>

// 恢復進階欄位
<Form.Item name="test_class_name" label="測試類別">
  <Input />
</Form.Item>
<Form.Item name="question_type" label="問題類型">
  <Input />
</Form.Item>
```

---

## 📚 相關文檔

- [VSA 測試案例管理測試指南](./vsa-test-case-management-testing-guide.md)
- [VSA 新增功能完整說明](./vsa-test-case-add-feature-summary.md)
- [關鍵字管理優化說明](./vsa-keyword-management-improvement.md)

---

## ✅ 變更檢查清單

開發完成後請確認：

- [x] 移除「類別」欄位
- [x] 移除「測試類別」欄位
- [x] 移除「問題類型」欄位
- [x] 頂部按鈕改為開啟外部 URL
- [x] 卡片按鈕改為開啟外部 URL
- [x] 移除未使用的 `showAddModal` 函數
- [x] 移除未使用的 `useCallback` import
- [x] React 編譯成功（無警告）
- [ ] 更新外部表單 URL（替換 `YOUR_GOOGLE_FORM_ID`）
- [ ] 測試頂部按鈕開啟外部表單
- [ ] 測試卡片按鈕開啟外部表單
- [ ] 測試編輯功能正常運作
- [ ] 建立 Google Forms 表單
- [ ] 設定表單與系統整合方式

---

**更新日期**：2025-11-27  
**狀態**：✅ 開發完成，等待表單 URL 配置  
**維護人員**：AI Platform Team
