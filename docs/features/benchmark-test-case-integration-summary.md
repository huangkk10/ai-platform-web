# Benchmark Test Case 整合方案 - 執行摘要

## 🎯 整合目標

將 **Protocol Benchmark Test Case** 和 **VSA (Vector Search Algorithm) Test Case** 兩個獨立頁面整合為一個統一的測試案例管理系統。

---

## 📊 快速比較

| 項目 | Protocol Test Case | VSA Test Case |
|------|-------------------|---------------|
| **路徑** | `/benchmark/test-cases` | `/benchmark/dify/test-cases` |
| **功能** | 文檔匹配測試（只讀） | AI 評分測試（完整 CRUD） |
| **特色欄位** | 預期文檔 IDs、最少匹配數、關鍵字 | 期望答案、評分標準、滿分 |
| **操作權限** | 查看詳情 | 新增、編輯、刪除、匯入/匯出 |

---

## ✅ 推薦方案：統一頁面 + Tab 切換

### 核心設計
```
┌─────────────────────────────────────────────────────┐
│  統一測試案例管理頁面                                   │
├─────────────────────────────────────────────────────┤
│  Tab: [Protocol Test Cases] [VSA Test Cases]        │
├─────────────────────────────────────────────────────┤
│  統計卡片（動態顯示）                                   │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐              │
│  │總數  │ │啟用中│ │難度  │ │類別  │              │
│  └──────┘ └──────┘ └──────┘ └──────┘              │
├─────────────────────────────────────────────────────┤
│  篩選區域（共用）                                       │
│  [搜尋] [難度] [類別] [重新整理]                      │
├─────────────────────────────────────────────────────┤
│  資料表格（動態欄位）                                   │
│  ┌─────────────────────────────────────────┐       │
│  │ ID | 問題 | 類別 | 難度 | [動態欄位] | 操作 │       │
│  └─────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────┘
```

---

## 🏗️ 技術實作重點

### 1. 後端：統一資料模型（推薦）

```python
class UnifiedBenchmarkTestCase(models.Model):
    # 共用欄位
    question = models.TextField()
    test_class_name = models.CharField()
    difficulty_level = models.CharField()
    
    # 測試類型（關鍵欄位）
    test_type = models.CharField(
        choices=[('protocol', 'Protocol'), ('vsa', 'VSA')]
    )
    
    # Protocol 專用
    expected_document_ids = models.JSONField()
    min_required_matches = models.IntegerField()
    
    # VSA 專用
    expected_answer = models.TextField()
    max_score = models.DecimalField()
```

### 2. 前端：Tab 切換 + 動態欄位

```jsx
<Tabs activeKey={activeTab} onChange={handleTabChange}>
  <TabPane tab="Protocol Test Cases" key="protocol">
    <Table columns={getProtocolColumns()} ... />
  </TabPane>
  
  <TabPane tab="VSA Test Cases" key="vsa">
    <Table columns={getVSAColumns()} ... />
    <CRUDButtons />
  </TabPane>
</Tabs>
```

### 3. API：統一端點 + 類型篩選

```
GET  /api/unified-benchmark/test-cases/?test_type=protocol
POST /api/unified-benchmark/test-cases/
GET  /api/unified-benchmark/test-cases/statistics/?test_type=vsa
```

---

## 📅 實施時程

| 階段 | 任務 | 時間 |
|------|------|------|
| **階段 1** | 資料分析 + 技術評估 | 1 天 |
| **階段 2** | 後端整合（Model + API） | 2-3 天 |
| **階段 3** | 前端整合（統一頁面） | 3-4 天 |
| **階段 4** | 測試 + 驗證 | 2 天 |
| **總計** | | **10 天** |

---

## 💡 核心優勢

### 使用者體驗
- ✅ **單一入口**：不再需要記住兩個頁面位置
- ✅ **快速切換**：Tab 切換即時查看不同類型測試
- ✅ **統一操作**：相同的篩選、搜尋邏輯

### 開發效率
- ✅ **代碼重用**：共用 70% 的組件和邏輯
- ✅ **維護簡化**：只需維護一個頁面
- ✅ **易於擴展**：新增測試類型只需添加 Tab

### 資料管理
- ✅ **統一管理**：單一資料來源
- ✅ **跨類型統計**：可輕鬆統計所有測試案例
- ✅ **資料一致性**：避免重複和不一致

---

## ⚠️ 關鍵風險與對策

### 風險 1：資料遷移
**對策**：
- 完整備份現有資料
- 測試環境先行驗證
- 保留舊表作為備份（3 個月）

### 風險 2：向後相容性
**對策**：
- 保留舊 API（標記為 deprecated）
- 提供 3 個月過渡期
- 完整測試覆蓋

### 風險 3：效能影響
**對策**：
- 實作分頁載入（每頁 20-50 筆）
- 使用 Tab 分離資料載入
- 優化查詢 SQL

---

## 📊 預期效益評估

### 開發成本
- **時間投入**：10 個工作天
- **人力需求**：1-2 名全端開發者
- **技術風險**：低（使用現有技術棧）

### 效益回收
- **短期（1-3 個月）**：
  - 使用者滿意度提升
  - 維護時間減少 30%
  
- **中期（3-6 個月）**：
  - 開發效率提升 40%
  - Bug 數量減少
  
- **長期（6-12 個月）**：
  - 易於新增功能
  - 系統可維護性提升

---

## 🎯 決策建議

### 推薦指數：⭐⭐⭐⭐⭐ (5/5)

### 建議行動
1. ✅ **立即批准**：整合方案技術可行、效益明確
2. ✅ **優先排程**：建議納入下一個 Sprint
3. ✅ **分階段執行**：降低風險、確保品質

### 替代方案（不推薦）
❌ **保持現狀**：
- 維護成本持續增加
- 使用者體驗不佳
- 未來擴展困難

❌ **僅整合前端**：
- 後端邏輯複雜
- 效能影響大
- 無法發揮最大效益

---

## 📞 下一步

### 立即行動
1. 📋 審核並批准此規劃
2. 👥 指派開發團隊成員
3. 📅 安排開發時程
4. 📊 建立 Jira/Trello 任務

### 準備工作
1. 🗄️ 備份現有資料庫
2. 🌿 建立開發分支 `feature/unified-test-case`
3. 📝 通知相關使用者（如需要）
4. 🧪 準備測試環境

---

## 📚 相關文檔

- 📄 **完整規劃文檔**：`/docs/features/benchmark-test-case-integration-plan.md`
- 📁 **現有頁面代碼**：
  - `frontend/src/pages/benchmark/TestCasesListPage.js`
  - `frontend/src/pages/dify-benchmark/DifyTestCasePage.js`

---

**文檔版本**：v1.0  
**創建日期**：2025-11-25  
**狀態**：✅ 規劃完成，等待批准  
**建議優先級**：🔥 高優先級

**需要決策**：是否批准並開始實施？
