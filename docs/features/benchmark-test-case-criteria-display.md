# Benchmark Test Case 判斷條件顯示功能

## 📋 功能概述
在 Web Benchmark 測試的 Test Case 頁面中，為每個問題添加了一個「判斷條件」欄位，方便用戶快速了解每個測試案例的評分標準和判斷依據。

## 🎯 更新內容

### 1. 新增「判斷條件」欄位
在測試案例列表表格中新增了一個欄位，顯示每個問題的判斷條件摘要：

**顯示內容包括：**
- 預期文檔數量
- 最少匹配數
- 預期關鍵字數量
- 可接受文檔數量

**UI 特色：**
- 使用紫色 Tag 顯示各項條件
- 小字體設計節省空間
- Tooltip 顯示完整詳細資訊
- 當滑鼠懸停時顯示具體的文檔 ID、關鍵字內容等

### 2. 增強詳細資訊 Modal
在測試案例詳細資訊彈窗中，添加了更完整的判斷條件說明：

**新增顯示項目：**
- **可接受文檔 ID**：顯示所有可接受的文檔（綠色 Tag）
- **預期關鍵字**：顯示所有預期的關鍵字（藍色 Tag）
- **預期答案摘要**：顯示完整的答案摘要文字
- **判斷條件摘要**：用自然語言描述評分規則
  - 例如：「需匹配 5 個預期文檔中的至少 3 個」
  - 例如：「需包含 8 個關鍵字」
  - 例如：「10 個可接受文檔」

## 📊 資料欄位說明

根據 `BenchmarkTestCase` 模型，判斷條件相關的欄位包括：

| 欄位名稱 | 類型 | 說明 |
|---------|------|------|
| `expected_document_ids` | JSONField | 預期文檔 IDs（陣列） |
| `min_required_matches` | IntegerField | 最少匹配數（預設 1） |
| `expected_keywords` | JSONField | 預期關鍵字（陣列） |
| `expected_answer_summary` | TextField | 預期答案摘要 |
| `acceptable_document_ids` | JSONField | 可接受文檔 IDs（陣列） |

## 🎨 UI 設計

### 表格欄位顯示邏輯
```javascript
{
  title: '判斷條件',
  key: 'evaluation_criteria',
  width: 180,
  align: 'center',
  render: (_, record) => {
    // 收集所有條件並以 Tag 形式顯示
    // Tooltip 顯示完整詳細資訊
  }
}
```

### 顏色編碼
- **紫色 (purple)**：判斷條件摘要 Tag
- **青色 (cyan)**：預期文檔 ID
- **橙色 (orange)**：最少匹配數
- **綠色 (green)**：可接受文檔 ID
- **藍色 (blue)**：預期關鍵字
- **灰色 (default)**：無設定或停用狀態

## 📱 響應式設計
- 表格水平滾動寬度從 1400px 增加到 1600px
- 判斷條件欄位寬度設為 180px
- 使用垂直 Space 排列多個條件標籤
- 小字體（11px）節省顯示空間

## 🔍 使用場景

### 場景 1：快速檢視判斷標準
用戶在列表中瀏覽測試案例時，可以立即看到每個問題的判斷標準摘要，無需點擊詳情。

### 場景 2：詳細了解評分規則
點擊「查看詳情」後，可以看到完整的判斷條件說明，包括具體的文檔 ID 和關鍵字內容。

### 場景 3：Tooltip 快速預覽
滑鼠懸停在「判斷條件」欄位上時，Tooltip 會顯示所有條件的完整內容，方便快速查看。

## 🚀 未來改進方向

1. **條件編輯功能**：允許直接在列表中編輯判斷條件
2. **條件模板**：提供常用判斷條件的預設模板
3. **條件驗證**：檢查判斷條件的合理性（如 min_required_matches 是否超過 expected_document_ids 的數量）
4. **條件統計**：統計各種判斷條件的使用頻率
5. **批量設定**：支援批量設定相似測試案例的判斷條件

## 📝 相關文件

- **前端組件**：`frontend/src/pages/benchmark/TestCasesListPage.js`
- **資料模型**：`backend/api/models.py` - `BenchmarkTestCase`
- **API 服務**：`frontend/src/services/benchmarkApi.js`
- **序列化器**：`backend/api/serializers.py` - `BenchmarkTestCaseSerializer`

## ✅ 測試檢查清單

- [ ] 列表頁面正確顯示判斷條件欄位
- [ ] Tooltip 顯示完整的條件詳情
- [ ] 條件為空時顯示「無設定」
- [ ] 詳細資訊 Modal 顯示所有判斷條件
- [ ] 各種判斷條件的顏色編碼正確
- [ ] 表格水平滾動正常
- [ ] 響應式設計在不同螢幕尺寸下正常顯示

## 📅 更新記錄

**2025-11-25**：
- ✅ 新增「判斷條件」欄位到測試案例列表
- ✅ 增強詳細資訊 Modal 的判斷條件顯示
- ✅ 添加 Tooltip 顯示完整條件詳情
- ✅ 調整表格寬度以適應新欄位
- ✅ 添加顏色編碼和視覺化設計

---

**作者**: AI Platform Team  
**版本**: v1.0  
**狀態**: ✅ 已完成
