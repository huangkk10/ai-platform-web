# Google Forms 表單範本 - VSA 測試案例

**用途**：用於收集 VSA 測試案例的外部表單範本

---

## 📋 表單基本設定

- **表單標題**：VSA 測試案例提交表單
- **表單說明**：
  ```
  此表單用於收集 VSA (Virtual Storage Assistant) 測試案例。
  請填寫完整的測試問題、期望答案和相關資訊。
  所有標記為「必填」的欄位都需要填寫。
  ```

---

## 📝 表單欄位配置

### 1. 測試問題 ⭐ 必填

- **欄位類型**：長文本（段落）
- **標題**：測試問題
- **說明**：請輸入完整的測試問題描述（例如：請問哪裡可以找到 Kingston Linux 韌卡的文件？）
- **驗證**：必填，最少 10 個字元
- **範例答案**：
  ```
  請問哪裡可以找到 Kingston Linux 韌卡的文件？
  ```

---

### 2. 難度等級 ⭐ 必填

- **欄位類型**：選擇題（單選）
- **標題**：難度等級
- **說明**：請選擇此測試案例的難度
- **選項**：
  - ⭕ 簡單（基礎知識問題）
  - ⭕ 中等（需要一定理解）
  - ⭕ 困難（複雜或需深入分析）
- **驗證**：必填

---

### 3. 期望答案 ⭐ 必填

- **欄位類型**：長文本（段落）
- **標題**：期望答案
- **說明**：請輸入此問題的標準答案或答案範例
- **驗證**：必填，最少 20 個字元
- **範例答案**：
  ```
  Kingston Linux 韌卡的文件可以在以下位置找到：
  1. 官方技術文檔網站
  2. 產品規格說明書
  3. 技術支援中心的知識庫
  ```

---

### 4. 答案關鍵字

- **欄位類型**：短文本（簡答）
- **標題**：答案關鍵字
- **說明**：
  ```
  請輸入評分時需要匹配的關鍵字，多個關鍵字請用「半形逗號」分隔。
  
  範例：Kingston, Linux, 葉卡, USB, 文件
  
  這些關鍵字將用於自動評分系統，當 AI 回應中包含這些關鍵字時會獲得分數。
  ```
- **驗證**：建議填寫（非必填）
- **範例答案**：
  ```
  Kingston, Linux, 葉卡, USB, 規格
  ```

---

### 5. 滿分

- **欄位類型**：數字（簡答）
- **標題**：滿分
- **說明**：此測試案例的最高分數（預設 100 分）
- **驗證**：
  - 數字類型
  - 最小值：1
  - 最大值：1000
- **預設值**：100
- **範例答案**：
  ```
  100
  ```

---

### 6. 標籤

- **欄位類型**：短文本（簡答）
- **標題**：標籤
- **說明**：
  ```
  請輸入相關標籤，多個標籤請用「半形逗號」分隔。
  
  範例：Kingston, Linux, 葉卡, USB測試, 規格查詢
  
  標籤用於分類和搜尋測試案例。
  ```
- **驗證**：選填
- **範例答案**：
  ```
  Kingston, Linux, 葉卡, USB測試
  ```

---

### 7. 來源

- **欄位類型**：短文本（簡答）
- **標題**：來源
- **說明**：
  ```
  此測試案例的來源（例如：實際測試案例、文檔範例、客戶反饋、內部測試）
  ```
- **驗證**：選填
- **範例答案**：
  ```
  實際測試案例 - 客戶詢問
  ```

---

### 8. 備註

- **欄位類型**：長文本（段落）
- **標題**：備註
- **說明**：其他說明或注意事項（選填）
- **驗證**：選填，最多 500 字元
- **範例答案**：
  ```
  此問題經常被客戶詢問，建議 AI 回應時提供具體的文件連結。
  ```

---

### 9. 提交者資訊（可選）

- **欄位類型**：短文本（簡答）
- **標題**：提交者姓名或 Email
- **說明**：方便後續聯繫或確認（選填）
- **驗證**：選填

---

## 🎨 表單外觀設定

### 主題顏色
- **建議**：使用專業的藍色或綠色系
- **標題字體**：Roboto 或 Noto Sans
- **背景**：淡色或白色

### 確認訊息
```
感謝您提交 VSA 測試案例！

您的提交已收到，我們會盡快處理。
測試案例經審核後將加入系統中。

如有疑問，請聯繫：[您的聯絡方式]
```

---

## 🔗 表單連結範例

完成後，您的表單連結格式為：
```
https://forms.gle/[您的表單ID]
```

將此連結複製並替換到程式碼中的 `YOUR_GOOGLE_FORM_ID` 位置。

---

## 📊 回應處理方式

### 方案 A：手動匯入

1. **匯出回應**
   - Google Forms → 回應 → 匯出為 CSV
   - 使用 Excel 或 Google Sheets 整理

2. **轉換格式**
   ```python
   # 範例 Python 腳本
   import pandas as pd
   import json
   
   # 讀取 CSV
   df = pd.read_csv('form_responses.csv')
   
   # 轉換為 JSON
   test_cases = []
   for _, row in df.iterrows():
       test_case = {
           'question': row['測試問題'],
           'difficulty_level': row['難度等級'].lower(),
           'expected_answer': row['期望答案'],
           'answer_keywords': row['答案關鍵字'].split(',') if pd.notna(row['答案關鍵字']) else [],
           'max_score': int(row['滿分']) if pd.notna(row['滿分']) else 100,
           'tags': row['標籤'].split(',') if pd.notna(row['標籤']) else [],
           'source': row['來源'] if pd.notna(row['來源']) else '',
           'notes': row['備註'] if pd.notna(row['備註']) else '',
           'test_type': 'vsa',
           'is_active': True
       }
       test_cases.append(test_case)
   
   # 輸出 JSON
   with open('test_cases.json', 'w', encoding='utf-8') as f:
       json.dump(test_cases, f, ensure_ascii=False, indent=2)
   ```

3. **匯入系統**
   - 在 VSA 測試案例管理頁面點擊「匯入」
   - 上傳轉換後的 JSON 檔案

---

### 方案 B：自動同步（Google Apps Script）

1. **開啟腳本編輯器**
   - Google Forms → 更多 → 指令碼編輯器

2. **貼上程式碼**
   ```javascript
   function onFormSubmit(e) {
     // 獲取表單回應
     var formResponse = e.response;
     var items = formResponse.getItemResponses();
     
     // 構建資料
     var data = {
       question: items[0].getResponse(),
       difficulty_level: items[1].getResponse().toLowerCase(),
       expected_answer: items[2].getResponse(),
       answer_keywords: items[3].getResponse() ? items[3].getResponse().split(',').map(k => k.trim()) : [],
       max_score: items[4].getResponse() ? parseInt(items[4].getResponse()) : 100,
       tags: items[5].getResponse() ? items[5].getResponse().split(',').map(t => t.trim()) : [],
       source: items[6].getResponse() || '',
       notes: items[7].getResponse() || '',
       test_type: 'vsa',
       is_active: true
     };
     
     // 發送到 Django API
     var url = 'http://your-domain.com/api/dify-benchmark/test-cases/';
     var options = {
       method: 'post',
       contentType: 'application/json',
       headers: {
         'Authorization': 'Token YOUR_API_TOKEN'
       },
       payload: JSON.stringify(data)
     };
     
     try {
       var response = UrlFetchApp.fetch(url, options);
       Logger.log('Success: ' + response.getContentText());
     } catch (error) {
       Logger.log('Error: ' + error);
     }
   }
   ```

3. **設定觸發器**
   - 左側選單 → 觸發器
   - 新增觸發器 → 選擇函數：`onFormSubmit`
   - 事件來源：表單
   - 事件類型：提交表單時

---

## 🧪 測試表單

### 測試資料範例

**測試案例 1：簡單問題**
```
測試問題：請問哪裡可以找到 Kingston Linux 韌卡的文件？
難度等級：簡單
期望答案：Kingston Linux 韌卡的文件可以在官方技術文檔網站、產品規格說明書及技術支援中心的知識庫中找到。
答案關鍵字：Kingston, Linux, 葉卡, 文件, 規格
滿分：100
標籤：Kingston, Linux, 文件查詢
來源：客戶常見問題
備註：請確保回應中包含具體連結
```

**測試案例 2：中等問題**
```
測試問題：有沒有關於 PyNvme3 的說明文件？
難度等級：中等
期望答案：PyNvme3 的說明文件可在 GitHub 專案頁面、官方文檔網站和技術社群論壇中找到。
答案關鍵字：PyNvme3, NVMe, 測試工具, 說明文件
滿分：100
標籤：PyNvme3, NVMe, 測試工具
來源：技術團隊內部測試
備註：需要提供最新版本的文檔
```

---

## ✅ 檢查清單

表單建立完成後請確認：

- [ ] 所有必填欄位已標記為「必填」
- [ ] 欄位說明清楚易懂
- [ ] 提供了範例答案
- [ ] 設定了適當的驗證規則
- [ ] 確認訊息已設定
- [ ] 表單連結已複製
- [ ] 已更新程式碼中的 URL
- [ ] 已測試表單提交流程
- [ ] 確認回應資料正確收集
- [ ] （可選）設定自動同步腳本

---

**建立日期**：2025-11-27  
**維護人員**：AI Platform Team  
**表單版本**：v1.0
