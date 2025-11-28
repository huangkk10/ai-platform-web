# 單一測試案例版本比較 - 快速實作指南

## 📋 功能概述

在 VSA 測試案例表格中，為每個問題添加「版本比較」按鈕，一鍵測試該問題在所有搜尋版本（V1-V5）的表現。

```
原本：測試 100 個問題 × 5 版本 = 40 分鐘
現在：測試   1 個問題 × 5 版本 = 30 秒

節省時間：99.2% ⚡
```

---

## 🎯 核心功能

### 1. 使用者操作流程
```
VSA 測試案例列表
    ↓
點擊「版本比較」按鈕 (🧪)
    ↓
彈出 Modal，顯示測試資訊
    ↓
自動開始測試 5 個版本
    ↓
顯示即時進度條（0% → 100%）
    ↓
顯示測試結果表格
    ↓
可排序、匯出、重新測試
```

### 2. UI 效果圖

```
┌─────────────────────────────────────────────────────────┐
│  🧪 版本比較測試 - ULINK 測試的安裝程式和測試腳本...        │
│  ─────────────────────────────────────────────────────  │
│  📊 測試資訊                                              │
│  問題：ULINK 測試的安裝程式和測試腳本本存放在 NAS ...      │
│  難度：easy  |  關鍵字：[20%] [100%] [33%]               │
│                                                         │
│  ⏳ 進度：[████████████████░░] 80% (4/5 完成)           │
│                                                         │
│  📋 測試結果                                              │
│  #  版本名稱          P     R     F1    狀態              │
│  1  V1-純段落搜尋    20%   100%  33%   ✅               │
│  2  V2-純全文搜尋    10%   100%  18%   ✅               │
│  3  V3-混合70-30    10%   100%  18%   ✅               │
│  4  V4-混合50-50    10%   100%  18%   ✅               │
│  5  V5-混合80-20    測試中...          🔄               │
│                                                         │
│  [💾 匯出]  [🔄 重測]                      [❌ 關閉]     │
└─────────────────────────────────────────────────────────┘
```

---

## 🏗️ 系統架構

### 技術棧
```
前端：React + Ant Design
後端：Django REST Framework
測試引擎：library/benchmark/
資料庫：PostgreSQL
```

### 檔案結構
```
frontend/src/
├── pages/benchmark/
│   ├── UnifiedTestCasePage.js          # 修改：添加按鈕
│   └── VersionComparisonModal.jsx      # 🆕 新增組件
└── services/
    └── unifiedBenchmarkApi.js          # 修改：添加 API

backend/
├── api/views/viewsets/
│   └── unified_benchmark_viewsets.py   # 修改：添加 action
└── library/benchmark/
    └── single_case_version_tester.py   # 🆕 新增類別
```

### API 設計
```
POST /api/unified-benchmark/test-cases/{id}/version_comparison/
Request:
{
  "version_ids": [1, 2, 3, 4, 5],  // 可選，預設全部
  "force_retest": false
}

Response (同步):
{
  "success": true,
  "task_id": "uuid-1234",
  "results": [
    {
      "version_id": 1,
      "version_name": "V1 - 純段落向量搜尋",
      "metrics": {
        "precision": 0.20,
        "recall": 1.00,
        "f1_score": 0.33
      },
      "response_time": 1.23,
      "status": "success"
    },
    // ... 其他 4 個版本
  ],
  "summary": {
    "total_versions": 5,
    "best_version": {...},
    "avg_response_time": 1.5
  }
}
```

---

## 🔧 實作步驟（5 天）

### Day 1: 後端核心邏輯
```python
# Step 1: 創建 library/benchmark/single_case_version_tester.py

class SingleCaseVersionTester:
    def __init__(self, test_case_id, version_ids=None):
        self.test_case_id = test_case_id
        self.version_ids = version_ids
    
    def run_comparison(self):
        """執行版本比較測試"""
        # 1. 獲取測試案例
        # 2. 獲取要測試的版本
        # 3. 逐個測試版本
        # 4. 返回結果
        pass
    
    def _test_single_version(self, test_case, version):
        """複用 BatchVersionTester 的邏輯"""
        from library.benchmark.batch_version_tester import BatchVersionTester
        batch_tester = BatchVersionTester(verbose=False)
        return batch_tester._execute_single_test(test_case, version)
```

### Day 2: 後端 API
```python
# Step 2: 修改 backend/api/views/viewsets/unified_benchmark_viewsets.py

class UnifiedBenchmarkTestCaseViewSet(viewsets.ModelViewSet):
    # ... 現有代碼
    
    @action(detail=True, methods=['post'])
    def version_comparison(self, request, pk=None):
        """單一測試案例的版本比較"""
        test_case = self.get_object()
        version_ids = request.data.get('version_ids', None)
        
        from library.benchmark.single_case_version_tester import SingleCaseVersionTester
        tester = SingleCaseVersionTester(test_case.id, version_ids)
        result = tester.run_comparison()
        
        return Response({
            'success': True,
            'results': result['results'],
            'summary': result['summary']
        })
```

### Day 3: 前端 Modal 組件
```javascript
// Step 3: 創建 frontend/src/pages/benchmark/VersionComparisonModal.jsx

const VersionComparisonModal = ({ visible, onClose, testCase }) => {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  
  const startTest = async () => {
    setLoading(true);
    const response = await unifiedBenchmarkApi.versionComparison(testCase.id);
    setResults(response.data.results);
    setLoading(false);
  };
  
  return (
    <Modal visible={visible} onCancel={onClose} width="90%">
      {/* 測試資訊卡片 */}
      {/* 進度條 */}
      {/* 結果表格 */}
    </Modal>
  );
};
```

### Day 4: 整合到主頁面
```javascript
// Step 4: 修改 frontend/src/pages/benchmark/UnifiedTestCasePage.js

// 1. 導入組件
import VersionComparisonModal from './VersionComparisonModal';

// 2. 添加按鈕到表格
{
  title: '操作',
  render: (_, record) => (
    <Space>
      {/* 現有按鈕 */}
      <Tooltip title="版本比較測試">
        <Button 
          icon={<ExperimentOutlined />}
          type="primary"
          ghost
          onClick={() => handleVersionComparison(record)}
        />
      </Tooltip>
    </Space>
  )
}

// 3. 添加 Modal
<VersionComparisonModal
  visible={versionComparisonVisible}
  onClose={() => setVersionComparisonVisible(false)}
  testCase={selectedTestCase}
/>
```

### Day 5: 測試與優化
```bash
# 功能測試
✅ 測試單一問題的版本比較
✅ 驗證結果準確性
✅ 測試錯誤處理

# 效能測試
✅ 5 個版本測試時間 < 30 秒
✅ UI 響應流暢

# 使用者體驗
✅ Loading 動畫
✅ 結果排序
✅ 匯出功能
```

---

## 📊 關鍵代碼片段

### 1. 後端測試邏輯（核心）
```python
def _test_single_version(self, test_case, version):
    """測試單一版本"""
    # 根據 version.parameters 配置搜尋策略
    search_params = version.parameters
    
    # 執行搜尋（複用現有邏輯）
    search_service = ProtocolGuideSearchService()
    results = search_service.search_with_vectors(
        query=test_case.question,
        **search_params
    )
    
    # 評估結果（P/R/F1）
    evaluator = SearchResultEvaluator()
    metrics = evaluator.evaluate(
        results=results,
        expected_keywords=test_case.answer_keywords
    )
    
    # 儲存到資料庫
    test_run = BenchmarkTestRun.objects.create(
        test_type='vsa',
        batch_name=f"單案例測試 - {test_case.question[:30]}",
        notes=f"版本比較測試",
        created_from='single_case_comparison'  # 標記來源
    )
    
    BenchmarkTestResult.objects.create(
        test_run=test_run,
        test_case=test_case,
        version=version,
        precision=metrics['precision'],
        recall=metrics['recall'],
        f1_score=metrics['f1_score']
    )
    
    return {
        'version_id': version.id,
        'version_name': version.version_name,
        'metrics': metrics,
        'status': 'success'
    }
```

### 2. 前端結果表格（UI）
```javascript
const columns = [
  {
    title: 'F1 Score',
    dataIndex: ['metrics', 'f1_score'],
    render: (value) => (
      <Tag color={value > 0.3 ? 'green' : value > 0.15 ? 'orange' : 'red'}>
        {(value * 100).toFixed(0)}%
      </Tag>
    ),
    sorter: (a, b) => a.metrics.f1_score - b.metrics.f1_score,
    defaultSortOrder: 'descend'  // 預設按 F1 降序排列
  }
];

<Table
  columns={columns}
  dataSource={results}
  rowKey="version_id"
  pagination={false}
  scroll={{ y: 400 }}
/>
```

### 3. API Service（前端）
```javascript
// frontend/src/services/unifiedBenchmarkApi.js

versionComparison: async (testCaseId, data = {}) => {
  return api.post(
    `/unified-benchmark/test-cases/${testCaseId}/version_comparison/`, 
    data
  );
}
```

---

## ⚡ 效能考量

### 同步 vs 非同步執行
```
📌 Phase 1 建議：同步執行
原因：
✅ 測試時間短（20-30 秒）
✅ 實作簡單
✅ 用戶體驗好（立即看到結果）

未來升級：如果版本數量 > 10，再考慮非同步
```

### 快取策略
```python
# 可選：添加結果快取（避免重複測試）
cache_key = f"vsa_comparison_{test_case.id}_{version_ids_hash}"
if cache_key in cache and not force_retest:
    return cache.get(cache_key)

# 執行測試...

cache.set(cache_key, result, timeout=3600)  # 快取 1 小時
```

---

## 🎯 使用場景範例

### 場景 1: 發現問題表現不佳
```
問題：「ULINK 測試的安裝程式和測試腳本本存放在 NAS 的哪個路徑？」
當前版本 (V3): F1 = 18%

操作：點擊「版本比較」
結果：
- V1: F1 = 33% ✅ （最佳）
- V2: F1 = 18%
- V3: F1 = 18% （當前）
- V4: F1 = 18%
- V5: F1 = 18%

結論：這個問題在 V1（純段落搜尋）表現最好！
```

### 場景 2: 調整關鍵字後驗證
```
問題：修改了某個問題的答案關鍵字

操作：
1. 修改關鍵字
2. 點擊「版本比較」
3. 查看所有版本的 P/R/F1 變化

結果：快速驗證關鍵字調整是否有效
```

### 場景 3: 新增問題後評估
```
問題：新增了一個測試案例

操作：立即進行版本比較測試

結果：
- 判斷問題品質（是否太難或太簡單）
- 找出最適合該問題的搜尋版本
```

---

## 📦 交付物清單

### 程式碼
- [ ] `backend/library/benchmark/single_case_version_tester.py`
- [ ] `backend/api/views/viewsets/unified_benchmark_viewsets.py` (修改)
- [ ] `frontend/src/pages/benchmark/VersionComparisonModal.jsx`
- [ ] `frontend/src/pages/benchmark/UnifiedTestCasePage.js` (修改)
- [ ] `frontend/src/services/unifiedBenchmarkApi.js` (修改)

### 測試
- [ ] 單元測試（後端）
- [ ] API 測試（Postman/curl）
- [ ] E2E 測試（前端）
- [ ] 效能測試報告

### 文檔
- [ ] API 文檔更新
- [ ] 使用者手冊
- [ ] 架構文檔（本文件）

---

## ✅ 驗收標準

### 功能性
- [x] 點擊按鈕後彈出 Modal
- [x] 自動開始測試 5 個版本
- [x] 顯示即時進度（0% → 100%）
- [x] 顯示結果表格（P/R/F1）
- [x] 支援結果排序
- [x] 支援匯出 CSV
- [x] 錯誤處理（顯示錯誤訊息）

### 效能性
- [x] 5 個版本測試完成時間 < 35 秒
- [x] UI 響應時間 < 200ms
- [x] 不阻塞其他操作

### 易用性
- [x] 按鈕位置明顯
- [x] Loading 動畫流暢
- [x] 結果易於理解（顏色編碼）
- [x] 可重複測試

---

## 🚀 後續擴展

### Phase 2 可能功能
1. **批量問題比較**：選擇 2-10 個問題，一次測試
2. **版本選擇器**：只測試指定的 2-3 個版本
3. **歷史記錄**：查看該問題的歷史測試記錄
4. **趨勢圖表**：視覺化版本效果差異
5. **智能推薦**：AI 推薦最佳版本

---

## 📞 聯絡資訊

**問題回報**：提交 Issue  
**功能建議**：提交 Feature Request  
**技術討論**：聯繫開發團隊

---

**文檔版本**: v1.0  
**最後更新**: 2025-11-28  
**狀態**: ✅ 規劃完成，待實作
