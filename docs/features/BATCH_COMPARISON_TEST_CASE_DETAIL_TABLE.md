# 批量測試對比頁面 - 測試案例詳細表現表格

## 📋 功能概述

在批量測試對比報告頁面中新增了「測試案例詳細表現」表格，讓使用者可以查看每個測試案例在不同搜尋版本下的具體表現。

## 🎯 實作日期

**2025-11-23**

## ✨ 功能特點

### 1. **測試案例維度展示**
- **橫向對比**：每一行顯示一個測試案例
- **縱向對比**：每一列顯示一個搜尋版本的表現
- **一目了然**：可以快速看出哪個版本在哪些測試案例上表現更好

### 2. **詳細指標展示**
每個測試案例在每個版本下顯示：
- ✅ **通過狀態**：綠色勾選 = 通過，紅色標籤 = 未通過
- 📊 **Precision**：精準度百分比
- 📊 **Recall**：召回率百分比
- 📊 **F1 Score**：綜合指標百分比

### 3. **懸停詳細資訊**
將滑鼠懸停在任何測試結果上，可以看到：
- Precision、Recall、F1 Score 的精確值
- True Positives (TP)、False Positives (FP)、False Negatives (FN) 數量
- 響應時間（毫秒）

### 4. **版本標識**
- **基準版本**：顯示金色「基準」標籤
- **版本名稱**：清楚顯示每個版本的名稱

### 5. **難度標識**
- **Easy**：綠色標籤
- **Medium**：橙色標籤
- **Hard**：紅色標籤

## 📊 資料結構

### 輸入資料
```javascript
{
  test_case_id: 1,
  question: "CrystalDiskMark 測試問題",
  difficulty: "easy",
  versions: {
    "V1 - 純段落向量搜尋": {
      version_id: 1,
      precision: 0.8,
      recall: 0.9,
      f1_score: 0.85,
      is_passed: true,
      response_time: 150,
      true_positives: 8,
      false_positives: 2,
      false_negatives: 1
    },
    "V2 - 純全文向量搜尋": {
      // ... 類似結構
    }
  }
}
```

### 表格渲染邏輯
```javascript
// 動態生成版本列
...(comparisonData?.versions || []).map(version => ({
  title: version.version_name,
  key: `version_${version.version_id}`,
  render: (_, record) => {
    const versionResult = record.versions[version.version_name];
    // 渲染該版本的測試結果
  }
}))
```

## 🔧 技術實作

### 1. **資料載入流程**

```javascript
// 步驟 1: 載入批量測試記錄
const batchRuns = await benchmarkApi.getTestRuns({
  run_type: 'batch_comparison'
});

// 步驟 2: 為每個 test_run 獲取詳細結果
const detailsPromises = runs.map(run => 
  benchmarkApi.getTestResults({ test_run_id: run.id })
);
const detailsResponses = await Promise.all(detailsPromises);

// 步驟 3: 按測試案例分組整理資料
const resultsByTestCase = {};
runs.forEach((run, runIndex) => {
  const results = detailsResponses[runIndex]?.data || [];
  results.forEach(result => {
    // 將結果按 test_case_id 分組
  });
});
```

### 2. **表格列動態生成**

```javascript
const detailColumns = [
  // 固定列：測試案例、難度
  { title: '測試案例', dataIndex: 'question', ... },
  { title: '難度', dataIndex: 'difficulty', ... },
  
  // 動態列：為每個版本生成一列
  ...(comparisonData?.versions || []).map(version => ({
    title: version.version_name,
    key: `version_${version.version_id}`,
    render: (_, record) => {
      // 渲染該版本在該測試案例的表現
    }
  }))
];
```

### 3. **Tooltip 懸停資訊**

```javascript
<Tooltip
  title={
    <div>
      <div>Precision: {(precision * 100).toFixed(1)}%</div>
      <div>Recall: {(recall * 100).toFixed(1)}%</div>
      <div>F1 Score: {(f1_score * 100).toFixed(1)}%</div>
      <div>TP: {true_positives} | FP: {false_positives} | FN: {false_negatives}</div>
      <div>響應時間: {response_time.toFixed(0)}ms</div>
    </div>
  }
>
  {/* 表格內容 */}
</Tooltip>
```

## 📂 修改檔案

### 1. **frontend/src/pages/benchmark/BatchComparisonPage.js**

**新增功能**：
- ✅ 新增 `detailedResults` state 儲存測試案例詳細結果
- ✅ 新增 `loadingDetails` state 顯示載入狀態
- ✅ 新增 `loadDetailedResults()` 函數載入詳細結果
- ✅ 新增 `detailColumns` 定義測試案例詳細表格列
- ✅ 新增測試案例詳細表現卡片渲染

**主要變更**：
```javascript
// State 擴充
const [detailedResults, setDetailedResults] = useState([]);
const [loadingDetails, setLoadingDetails] = useState(false);

// 載入詳細結果
const loadDetailedResults = async (runs) => {
  // 為每個 test_run 獲取詳細結果
  // 按測試案例分組整理
};

// 動態表格列定義
const detailColumns = [
  // 測試案例、難度（固定列）
  // 每個版本的表現（動態列）
];

// 新增表格渲染
<Card title="🎯 測試案例詳細表現">
  <Table
    dataSource={detailedResults}
    columns={detailColumns}
    // ...
  />
</Card>
```

## 🎨 UI 設計

### 表格佈局
```
┌────────────────────────────────────────────────────────────────┐
│ 🎯 測試案例詳細表現                                            │
├────────────────────────────────────────────────────────────────┤
│ ℹ️ 提示說明（綠色勾選 = 通過，P/R/F1 指標說明）                │
├─────────────┬──────┬──────────┬──────────┬──────────┬─────────┤
│ 測試案例    │ 難度 │ V1 基準  │ V2       │ V3       │ ...     │
├─────────────┼──────┼──────────┼──────────┼──────────┼─────────┤
│ Crystal...  │ Easy │ ✓        │ ✓        │ ✗        │ ...     │
│             │      │ P: 80%   │ P: 85%   │ P: 60%   │         │
│             │      │ R: 90%   │ R: 95%   │ R: 70%   │         │
│             │      │ F1: 85%  │ F1: 90%  │ F1: 65%  │         │
├─────────────┼──────┼──────────┼──────────┼──────────┼─────────┤
│ I3C...      │ Hard │ ✗        │ ✓        │ ✓        │ ...     │
│             │      │ ...      │ ...      │ ...      │         │
└─────────────┴──────┴──────────┴──────────┴──────────┴─────────┘
```

### 顏色方案
- ✅ **通過**：綠色勾選圖示 (#52c41a)
- ❌ **未通過**：紅色「未通過」標籤
- 🥇 **基準版本**：金色「基準」標籤
- 📊 **F1 Score**：藍色文字 (#1890ff)，作為關鍵指標

### 難度標籤顏色
- **Easy**：`success` (綠色)
- **Medium**：`warning` (橙色)
- **Hard**：`error` (紅色)

## 📊 使用範例

### 查看批量測試對比報告

1. **執行批量測試**
   - 前往「批量測試執行」頁面
   - 選擇要測試的版本（例如：V1, V2, V3）
   - 選擇要測試的案例（或全部）
   - 點擊「開始批量測試」

2. **查看對比報告**
   - 測試完成後自動跳轉到對比報告頁面
   - 或從「批量測試歷史」中點擊「查看對比」

3. **分析測試案例表現**
   - 滾動到「🎯 測試案例詳細表現」表格
   - 檢視每個測試案例在不同版本的表現
   - 將滑鼠懸停在結果上查看詳細資訊

### 典型分析場景

#### 場景 1：找出最佳版本
```
觀察：V2 在大部分測試案例上都顯示綠色勾選
結論：V2 是綜合表現最好的版本
```

#### 場景 2：分析特定案例
```
觀察：「I3C 測試」在所有版本上都未通過（紅色標籤）
結論：這個測試案例可能需要改進或版本需要針對性優化
```

#### 場景 3：精準度 vs 召回率權衡
```
觀察：V1 的 Precision 高但 Recall 低
      V3 的 Recall 高但 Precision 低
結論：根據業務需求選擇合適的版本
```

## 🔍 故障排查

### 問題 1：表格顯示「暫無詳細測試結果資料」

**可能原因**：
- 批量測試執行失敗
- API 獲取結果失敗
- 測試執行尚未完成

**解決方案**：
1. 檢查瀏覽器 Console 是否有錯誤訊息
2. 確認批量測試是否成功執行
3. 重新整理頁面

### 問題 2：某些版本的列顯示 "-"

**原因**：該版本在該測試案例上沒有測試結果

**正常情況**：
- 如果批量測試中未包含該測試案例
- 或該測試執行失敗

### 問題 3：表格欄位太多，橫向滾動不便

**解決方案**：
- 表格已設定 `scroll={{ x: 1200 }}`
- 可以使用橫向滾動條查看更多版本
- 或減少一次測試的版本數量

## 📈 效能考量

### 資料載入優化
```javascript
// 使用 Promise.all 並行載入所有版本的詳細結果
const detailsPromises = runs.map(run => 
  benchmarkApi.getTestResults({ test_run_id: run.id })
);
const detailsResponses = await Promise.all(detailsPromises);
```

### 渲染優化
- 使用 Ant Design Table 的內建分頁功能
- 每頁顯示 10 個測試案例
- 支援修改每頁顯示數量

## 🚀 未來改進方向

### 1. **篩選與排序**
- [ ] 按難度篩選測試案例
- [ ] 按通過率排序
- [ ] 按 F1 Score 排序

### 2. **匯出功能**
- [ ] 匯出測試案例詳細報告為 Excel
- [ ] 匯出為 PDF 報告

### 3. **視覺化增強**
- [ ] 使用熱力圖顯示表現好壞
- [ ] 為 F1 Score 添加漸變色背景

### 4. **互動功能**
- [ ] 點擊測試案例查看更詳細的資訊
- [ ] 點擊版本欄位查看該版本的配置

## ✅ 測試檢查清單

- [x] 批量測試執行成功
- [x] 詳細結果 API 正常返回資料
- [x] 表格正確顯示所有測試案例
- [x] 表格正確顯示所有版本的結果
- [x] 懸停 Tooltip 顯示詳細資訊
- [x] 通過/未通過狀態正確標示
- [x] 難度標籤顏色正確
- [x] 基準版本標識正確
- [x] 分頁功能正常
- [x] 橫向滾動正常
- [x] 載入狀態正確顯示

## 📝 相關文檔

- **批量測試系統架構**：`/docs/architecture/BATCH_TESTING_SYSTEM_ARCHITECTURE.md`
- **批量測試執行頁面**：`/docs/features/BATCH_TEST_EXECUTION_PAGE.md`
- **批量測試 API**：`/docs/api/BENCHMARK_API.md`

---

**建立日期**: 2025-11-23  
**最後更新**: 2025-11-23  
**作者**: AI Platform Team  
**狀態**: ✅ 已實作並部署
