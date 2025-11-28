# 單一測試案例多版本搜尋比較功能 - 詳細規劃

## 📋 需求概述

在 VSA 測試案例管理頁面的表格中，為每個測試案例（問題）添加一個「版本比較」按鈕，點擊後可以立即對**單一問題**執行所有搜尋版本的測試，並以表格形式展示比較結果。

### 🎯 核心目標
- ✅ 快速測試單一問題在不同搜尋版本下的效果
- ✅ 不需要執行完整的批量測試（節省時間）
- ✅ 立即看到各版本的 P/R/F1 指標對比
- ✅ 複用現有的 Batch Test 架構和版本配置

---

## 🏗️ 系統架構設計

### 1. 前端架構

#### 📁 組件結構
```
frontend/src/
├── pages/benchmark/
│   ├── UnifiedTestCasePage.js          # 主頁面（需修改）
│   └── VersionComparisonModal.jsx      # 🆕 版本比較 Modal
├── services/
│   └── unifiedBenchmarkApi.js          # API 服務（需新增方法）
└── styles/
    └── VersionComparisonModal.css      # 🆕 樣式文件
```

#### 🎨 UI/UX 設計

##### 1.1 表格操作列新增按鈕
```javascript
// 在 UnifiedTestCasePage.js 的 columns 配置中
{
  title: '操作',
  key: 'action',
  fixed: 'right',
  width: 180,
  render: (_, record) => (
    <Space size="small">
      {/* 現有按鈕 */}
      <Tooltip title="查看詳情">
        <Button icon={<EyeOutlined />} onClick={() => handleViewDetail(record)} />
      </Tooltip>
      <Tooltip title="編輯">
        <Button icon={<EditOutlined />} onClick={() => handleEdit(record)} />
      </Tooltip>
      
      {/* 🆕 新增：版本比較按鈕 */}
      <Tooltip title="版本比較測試">
        <Button 
          icon={<ExperimentOutlined />}  // 使用實驗圖標
          type="primary"
          ghost
          onClick={() => handleVersionComparison(record)}
        />
      </Tooltip>
      
      {/* 現有按鈕 */}
      <Popconfirm title="確定刪除?" onConfirm={() => handleDelete(record.id)}>
        <Button icon={<DeleteOutlined />} danger />
      </Popconfirm>
    </Space>
  )
}
```

##### 1.2 版本比較 Modal（彈窗）
```javascript
// VersionComparisonModal.jsx - 主要組件

功能特性：
✅ 全螢幕 Modal (width: 90%, fullscreen mode)
✅ 即時測試進度顯示（Progress Bar）
✅ 測試結果表格（類似附件 3）
✅ 支援匯出報告（CSV/JSON）
✅ 錯誤處理和重試機制

UI 佈局：
┌─────────────────────────────────────────────────────────┐
│  🧪 版本比較測試 - ULINK 測試的安裝程式和測試腳本本...     │
│  ─────────────────────────────────────────────────────  │
│                                                         │
│  📊 測試資訊                                              │
│  ├─ 問題：ULINK 測試的安裝程式和測試腳本本存放在 NAS...   │
│  ├─ 難度：easy                                           │
│  └─ 關鍵字：[20%] [100%] [33%]                           │
│                                                         │
│  ⏳ 測試進度：[████████████░░░░░░░░] 60% (3/5 完成)      │
│                                                         │
│  📋 測試結果                                              │
│  ┌────────────────────────────────────────────────┐    │
│  │ # │ 版本名稱        │ P    │ R    │ F1   │ 狀態│    │
│  ├───┼────────────────┼──────┼──────┼──────┼────┤    │
│  │ 1 │ V1-純段落搜尋   │ 20%  │ 100% │ 33%  │ ✅ │    │
│  │ 2 │ V2-純全文搜尋   │ 10%  │ 100% │ 18%  │ ✅ │    │
│  │ 3 │ V3-混合70-30   │ 10%  │ 100% │ 18%  │ ✅ │    │
│  │ 4 │ V4-混合50-50   │ 測試中... │      │      │ 🔄│    │
│  │ 5 │ V5-混合80-20   │ 等待中... │      │      │ ⏸️ │    │
│  └────────────────────────────────────────────────┘    │
│                                                         │
│  [💾 匯出報告]  [🔄 重新測試]           [❌ 關閉]         │
└─────────────────────────────────────────────────────────┘
```

##### 1.3 測試狀態指示器
```javascript
狀態類型：
- ⏸️  等待中 (pending)     - 灰色
- 🔄  測試中 (running)     - 藍色動畫
- ✅  成功 (success)       - 綠色
- ❌  失敗 (failed)        - 紅色
- ⚠️  部分成功 (warning)   - 橙色
```

---

### 2. 後端架構

#### 📁 文件結構
```
backend/
├── api/views/viewsets/
│   └── unified_benchmark_viewsets.py  # 需新增 action
├── library/benchmark/
│   ├── single_case_version_tester.py  # 🆕 單案例測試器
│   └── batch_version_tester.py        # 現有（可複用）
└── api/serializers.py
    └── # 需新增序列化器
```

#### 🔧 API 端點設計

##### 2.1 單一測試案例版本比較 API
```python
# POST /api/unified-benchmark/test-cases/{id}/version_comparison/

Request Body:
{
  "version_ids": [1, 2, 3, 4, 5],  // 要測試的版本 ID（可選，預設全部）
  "force_retest": false             // 是否強制重新測試（可選）
}

Response (立即返回任務 ID):
{
  "success": true,
  "task_id": "uuid-1234-5678",
  "test_case_id": 123,
  "test_case_question": "ULINK 測試的安裝程式...",
  "version_count": 5,
  "estimated_time": "30s"
}
```

##### 2.2 測試進度查詢 API
```python
# GET /api/unified-benchmark/test-cases/version_comparison_progress/{task_id}/

Response:
{
  "task_id": "uuid-1234-5678",
  "status": "running",  // pending, running, completed, failed
  "progress": {
    "total": 5,
    "completed": 3,
    "current_version": "V4 - 混合權重 50-50"
  },
  "results": [
    {
      "version_id": 1,
      "version_name": "V1 - 純段落向量搜尋",
      "version_code": "v3.1-section-only",
      "status": "success",
      "metrics": {
        "precision": 0.20,
        "recall": 1.00,
        "f1_score": 0.33
      },
      "response_time": 1.23,
      "test_run_id": 456
    },
    // ... 其他版本結果
  ],
  "error": null,
  "completed_at": null
}
```

##### 2.3 測試結果儲存
```python
# 複用現有的 BenchmarkTestRun 和 BenchmarkTestResult 模型
# 但標記為 "single_case_comparison" 類型

BenchmarkTestRun:
- test_type = 'vsa'
- batch_name = f"單案例測試 - {test_case.question[:30]}"
- notes = f"版本比較測試 (Task: {task_id})"
- created_from = 'single_case_comparison'  # 🆕 新增標記

BenchmarkTestResult:
- test_run_id
- test_case_id
- version_id
- metrics (P/R/F1)
```

---

### 3. 核心業務邏輯

#### 🎯 SingleCaseVersionTester 類別設計

```python
# backend/library/benchmark/single_case_version_tester.py

class SingleCaseVersionTester:
    """
    單一測試案例的多版本比較測試器
    
    特點：
    - 只測試一個問題
    - 測試所有活躍的搜尋版本（或指定版本）
    - 支援即時進度回報
    - 複用 BatchVersionTester 的搜尋邏輯
    """
    
    def __init__(self, test_case_id: int, version_ids: List[int] = None):
        """
        初始化
        
        Args:
            test_case_id: 要測試的案例 ID
            version_ids: 要測試的版本 ID 列表（None = 測試所有活躍版本）
        """
        self.test_case_id = test_case_id
        self.version_ids = version_ids
        self.task_id = str(uuid.uuid4())
        self.results = []
        self.status = 'pending'
        
    def run_comparison(self, progress_callback=None):
        """
        執行版本比較測試
        
        Args:
            progress_callback: 進度回調函數 callback(current, total, version_name)
            
        Returns:
            {
                'success': True,
                'task_id': '...',
                'results': [...],
                'summary': {...}
            }
        """
        try:
            self.status = 'running'
            
            # 1. 獲取測試案例
            test_case = UnifiedBenchmarkTestCase.objects.get(id=self.test_case_id)
            
            # 2. 獲取要測試的版本
            if self.version_ids:
                versions = SearchAlgorithmVersion.objects.filter(
                    id__in=self.version_ids, 
                    is_active=True
                )
            else:
                versions = SearchAlgorithmVersion.objects.filter(is_active=True)
            
            # 3. 逐個版本測試
            for idx, version in enumerate(versions, 1):
                if progress_callback:
                    progress_callback(idx, len(versions), version.version_name)
                
                # 執行單個版本測試
                result = self._test_single_version(test_case, version)
                self.results.append(result)
            
            self.status = 'completed'
            
            return {
                'success': True,
                'task_id': self.task_id,
                'results': self.results,
                'summary': self._generate_summary()
            }
            
        except Exception as e:
            self.status = 'failed'
            logger.error(f"版本比較測試失敗: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _test_single_version(self, test_case, version):
        """
        測試單一版本
        
        複用 BatchVersionTester 的邏輯：
        1. 根據 version.parameters 配置搜尋策略
        2. 執行搜尋
        3. 評估結果（P/R/F1）
        4. 儲存到資料庫
        """
        from library.benchmark.batch_version_tester import BatchVersionTester
        
        # 複用現有測試邏輯
        batch_tester = BatchVersionTester(verbose=False)
        
        # 只測試這一個案例和這一個版本
        result = batch_tester._execute_single_test(
            test_case=test_case,
            version=version
        )
        
        return result
    
    def _generate_summary(self):
        """生成測試摘要"""
        return {
            'total_versions': len(self.results),
            'best_version': max(self.results, key=lambda x: x['metrics']['f1_score']),
            'avg_response_time': sum(r['response_time'] for r in self.results) / len(self.results)
        }
```

---

### 4. 實作步驟（分階段）

#### Phase 1: 後端 API 開發（Day 1-2）

**Step 1.1: 創建 SingleCaseVersionTester**
```bash
✅ 建立 library/benchmark/single_case_version_tester.py
✅ 實作核心測試邏輯
✅ 複用 BatchVersionTester 的搜尋執行器
✅ 單元測試
```

**Step 1.2: 新增 ViewSet Action**
```python
# backend/api/views/viewsets/unified_benchmark_viewsets.py

@action(detail=True, methods=['post'])
def version_comparison(self, request, pk=None):
    """
    單一測試案例的版本比較測試
    
    URL: POST /api/unified-benchmark/test-cases/{id}/version_comparison/
    """
    try:
        test_case = self.get_object()
        version_ids = request.data.get('version_ids', None)
        force_retest = request.data.get('force_retest', False)
        
        # 啟動測試（非同步或同步）
        from library.benchmark.single_case_version_tester import SingleCaseVersionTester
        
        tester = SingleCaseVersionTester(
            test_case_id=test_case.id,
            version_ids=version_ids
        )
        
        # ⚠️ 決策點：同步 vs 非同步
        # 方案 A：同步執行（簡單，適合測試數量少）
        result = tester.run_comparison()
        
        return Response({
            'success': True,
            'task_id': result['task_id'],
            'results': result['results'],
            'summary': result['summary']
        })
        
        # 方案 B：非同步執行（複雜，適合測試數量多）
        # task_id = tester.start_async()
        # return Response({'task_id': task_id, 'status': 'pending'})
        
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@action(detail=False, methods=['get'], url_path='version_comparison_progress/(?P<task_id>[^/.]+)')
def version_comparison_progress(self, request, task_id=None):
    """
    查詢版本比較測試進度
    
    URL: GET /api/unified-benchmark/test-cases/version_comparison_progress/{task_id}/
    """
    # 從 cache 或資料庫獲取進度
    # （如果使用非同步方案）
    pass
```

**Step 1.3: 測試 API**
```bash
# 測試腳本
curl -X POST http://localhost/api/unified-benchmark/test-cases/1/version_comparison/ \
  -H "Content-Type: application/json" \
  -d '{"version_ids": [1, 2, 3, 4, 5]}'
```

---

#### Phase 2: 前端 UI 開發（Day 3-4）

**Step 2.1: 創建 VersionComparisonModal 組件**
```javascript
// frontend/src/pages/benchmark/VersionComparisonModal.jsx

import React, { useState, useEffect } from 'react';
import { Modal, Table, Progress, Tag, Space, Button, message } from 'antd';
import { ExperimentOutlined, DownloadOutlined, ReloadOutlined } from '@ant-design/icons';

const VersionComparisonModal = ({ visible, onClose, testCase }) => {
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [results, setResults] = useState([]);
  const [taskId, setTaskId] = useState(null);
  
  // 開始測試
  const startTest = async () => {
    setLoading(true);
    try {
      const response = await unifiedBenchmarkApi.versionComparison(testCase.id);
      
      // 同步方案：直接獲取結果
      setResults(response.data.results);
      setProgress(100);
      
      // 非同步方案：輪詢進度
      // setTaskId(response.data.task_id);
      // pollProgress(response.data.task_id);
      
    } catch (error) {
      message.error('測試失敗');
    } finally {
      setLoading(false);
    }
  };
  
  // 表格欄位
  const columns = [
    {
      title: '#',
      dataIndex: 'index',
      width: 60,
      render: (_, __, index) => index + 1
    },
    {
      title: '版本名稱',
      dataIndex: 'version_name',
      width: 200,
      render: (text, record) => (
        <div>
          <div>{text}</div>
          <Tag color="blue">{record.version_code}</Tag>
        </div>
      )
    },
    {
      title: 'Precision',
      dataIndex: ['metrics', 'precision'],
      width: 100,
      render: (value) => (
        <Tag color={value > 0.3 ? 'green' : value > 0.1 ? 'orange' : 'red'}>
          {(value * 100).toFixed(0)}%
        </Tag>
      ),
      sorter: (a, b) => a.metrics.precision - b.metrics.precision
    },
    {
      title: 'Recall',
      dataIndex: ['metrics', 'recall'],
      width: 100,
      render: (value) => (
        <Tag color={value === 1.0 ? 'green' : 'orange'}>
          {(value * 100).toFixed(0)}%
        </Tag>
      )
    },
    {
      title: 'F1 Score',
      dataIndex: ['metrics', 'f1_score'],
      width: 100,
      render: (value) => (
        <Tag color={value > 0.3 ? 'green' : value > 0.15 ? 'orange' : 'red'}>
          {(value * 100).toFixed(0)}%
        </Tag>
      ),
      sorter: (a, b) => a.metrics.f1_score - b.metrics.f1_score,
      defaultSortOrder: 'descend'
    },
    {
      title: '狀態',
      dataIndex: 'status',
      width: 80,
      render: (status) => {
        const statusConfig = {
          'success': { icon: '✅', color: 'green', text: '成功' },
          'failed': { icon: '❌', color: 'red', text: '失敗' },
          'running': { icon: '🔄', color: 'blue', text: '測試中' },
        };
        const config = statusConfig[status] || statusConfig['success'];
        return <Tag color={config.color}>{config.icon} {config.text}</Tag>;
      }
    }
  ];
  
  return (
    <Modal
      title={
        <Space>
          <ExperimentOutlined />
          版本比較測試 - {testCase?.question?.substring(0, 30)}...
        </Space>
      }
      open={visible}
      onCancel={onClose}
      width="90%"
      style={{ top: 20 }}
      footer={[
        <Button key="export" icon={<DownloadOutlined />} onClick={handleExport}>
          匯出報告
        </Button>,
        <Button key="retry" icon={<ReloadOutlined />} onClick={startTest}>
          重新測試
        </Button>,
        <Button key="close" onClick={onClose}>
          關閉
        </Button>
      ]}
    >
      {/* 測試資訊卡片 */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <div><strong>問題：</strong>{testCase?.question}</div>
          <div><strong>難度：</strong><Tag>{testCase?.difficulty_level}</Tag></div>
          <div>
            <strong>答案關鍵字：</strong>
            {testCase?.answer_keywords?.map((kw, idx) => (
              <Tag key={idx}>{kw}</Tag>
            ))}
          </div>
        </Space>
      </Card>
      
      {/* 進度條 */}
      {loading && (
        <Progress 
          percent={progress} 
          status="active"
          strokeColor={{ '0%': '#108ee9', '100%': '#87d068' }}
        />
      )}
      
      {/* 結果表格 */}
      <Table
        columns={columns}
        dataSource={results}
        loading={loading}
        rowKey="version_id"
        pagination={false}
        scroll={{ y: 400 }}
        size="small"
      />
    </Modal>
  );
};

export default VersionComparisonModal;
```

**Step 2.2: 整合到 UnifiedTestCasePage**
```javascript
// frontend/src/pages/benchmark/UnifiedTestCasePage.js

// 1. 導入組件
import VersionComparisonModal from './VersionComparisonModal';

// 2. 添加 State
const [versionComparisonVisible, setVersionComparisonVisible] = useState(false);
const [selectedTestCase, setSelectedTestCase] = useState(null);

// 3. 添加處理函數
const handleVersionComparison = (record) => {
  setSelectedTestCase(record);
  setVersionComparisonVisible(true);
};

// 4. 在表格 columns 中添加按鈕（如上所述）

// 5. 在 JSX 中添加 Modal
return (
  <div>
    {/* ... 現有內容 ... */}
    
    <VersionComparisonModal
      visible={versionComparisonVisible}
      onClose={() => setVersionComparisonVisible(false)}
      testCase={selectedTestCase}
    />
  </div>
);
```

**Step 2.3: 更新 API Service**
```javascript
// frontend/src/services/unifiedBenchmarkApi.js

const unifiedBenchmarkApi = {
  // ... 現有方法
  
  // 🆕 新增：版本比較測試
  versionComparison: async (testCaseId, data = {}) => {
    return api.post(`/unified-benchmark/test-cases/${testCaseId}/version_comparison/`, data);
  },
  
  // 🆕 新增：查詢測試進度（如果使用非同步方案）
  getComparisonProgress: async (taskId) => {
    return api.get(`/unified-benchmark/test-cases/version_comparison_progress/${taskId}/`);
  }
};
```

---

#### Phase 3: 測試與優化（Day 5）

**Step 3.1: 功能測試**
```
✅ 測試單一問題的版本比較
✅ 測試不同難度級別的問題
✅ 測試結果準確性驗證
✅ 測試錯誤處理
✅ 測試 UI 響應性
```

**Step 3.2: 效能優化**
```
✅ 測試 5 個版本的總執行時間（目標 < 30 秒）
✅ 前端進度條動畫流暢度
✅ 資料庫查詢優化
```

**Step 3.3: 使用者體驗優化**
```
✅ 添加 Loading 動畫
✅ 添加結果排序功能
✅ 添加匯出 CSV 功能
✅ 添加測試結果快取（避免重複測試）
```

---

## 🎯 技術決策

### 決策 1: 同步 vs 非同步執行

**方案 A: 同步執行（推薦）**
```
優點：
✅ 實作簡單，無需任務佇列
✅ 即時返回結果，UX 更好
✅ 測試量小（5 個版本 × 1 個問題），執行快速（預計 20-30 秒）

缺點：
❌ 可能阻塞 HTTP 連接（但時間短可接受）
❌ 無法取消進行中的測試

適用場景：
✅ 版本數量 <= 10
✅ 測試執行時間 < 60 秒
```

**方案 B: 非同步執行（複雜）**
```
優點：
✅ 不阻塞 HTTP 連接
✅ 支援進度即時更新
✅ 可以取消測試
✅ 可以同時執行多個測試

缺點：
❌ 需要 Celery 或 Redis
❌ 需要輪詢機制
❌ 實作複雜度高

適用場景：
✅ 版本數量 > 10
✅ 測試執行時間 > 60 秒
```

**📌 建議：Phase 1 使用方案 A（同步），如未來需要再升級為方案 B**

---

### 決策 2: 結果儲存策略

**方案 A: 完整儲存（推薦）**
```python
# 每次測試都創建新的 BenchmarkTestRun 和 BenchmarkTestResult
# 標記為 "single_case_comparison" 類型

優點：
✅ 完整的歷史記錄
✅ 可追溯性強
✅ 支援後續分析

缺點：
❌ 資料庫成長較快

適用場景：
✅ 需要完整審計記錄
✅ 需要歷史趨勢分析
```

**方案 B: 臨時儲存（輕量）**
```python
# 使用 cache (Redis) 暫存結果
# 不寫入資料庫

優點：
✅ 資料庫負擔小
✅ 快速存取

缺點：
❌ 結果會過期
❌ 無歷史記錄

適用場景：
✅ 純粹的即時比較
✅ 不需要歷史記錄
```

**📌 建議：使用方案 A（完整儲存），但添加 `created_from` 標記方便區分**

---

### 決策 3: 前端表格設計

**表格欄位設計（參考附件 3）**
```javascript
columns = [
  { title: '#', width: 60 },
  { title: '版本名稱', width: 200 },
  { title: 'Precision', width: 100, sortable: true },
  { title: 'Recall', width: 100, sortable: true },
  { title: 'F1 Score', width: 100, sortable: true, defaultSort: 'desc' },
  { title: '響應時間', width: 100 },
  { title: '狀態', width: 80 }
]
```

**顏色編碼（一致性）**
```javascript
Precision/F1 顏色規則：
- 綠色 (green): > 30%
- 橙色 (orange): 10-30%
- 紅色 (red): < 10%

Recall 顏色規則：
- 綠色 (green): 100%
- 橙色 (orange): < 100%

狀態顏色：
- 成功 (success): 綠色 + ✅
- 失敗 (failed): 紅色 + ❌
- 測試中 (running): 藍色 + 🔄
```

---

## 📊 預期效果

### 使用流程
```
1. 用戶在 VSA 測試案例列表中看到某個問題
   └→ 點擊「版本比較」按鈕（實驗圖標）

2. 彈出 Modal，顯示測試資訊
   └→ 自動開始測試（或點擊「開始測試」按鈕）

3. 顯示進度條（20% → 40% → 60% → 80% → 100%）
   └→ 即時更新測試結果表格

4. 測試完成，顯示完整結果表格
   └→ 可以排序、匯出、重新測試

5. 關閉 Modal，返回列表
   └→ 測試結果已儲存在資料庫中
```

### 時間估算
```
單個版本測試時間: 4-6 秒
總測試時間（5 個版本）: 20-30 秒
前端 UI 響應時間: < 100ms
```

### 資料量估算
```
假設：
- 100 個測試案例
- 每個案例平均測試 3 次（不同時間點）
- 每次測試 5 個版本

資料量：
- BenchmarkTestRun: 100 × 3 = 300 筆
- BenchmarkTestResult: 100 × 3 × 5 = 1,500 筆

存儲空間: < 10 MB（可忽略不計）
```

---

## ✅ 優勢分析

### vs 完整批量測試
```
完整批量測試：
- 時間：測試 100 個問題 × 5 個版本 = 500 次測試 ≈ 40-50 分鐘
- 成本：高計算資源消耗
- 用途：定期全面評估

單問題版本比較：
- 時間：測試 1 個問題 × 5 個版本 = 5 次測試 ≈ 20-30 秒
- 成本：低計算資源消耗
- 用途：快速問題診斷

📌 節省時間：99.2%（30 秒 vs 40 分鐘）
```

### 使用場景
```
✅ 場景 1: 發現某個問題在當前版本表現不佳
   → 立即測試該問題在其他版本的表現
   → 快速判斷是版本問題還是問題本身問題

✅ 場景 2: 調整某個問題的關鍵字
   → 修改後立即測試所有版本
   → 驗證調整效果

✅ 場景 3: 添加新問題後
   → 立即測試該問題在所有版本的表現
   → 評估問題品質

✅ 場景 4: 開發新版本時
   → 挑選代表性問題快速測試
   → 初步評估新版本效果
```

---

## 🚀 擴展功能（Phase 2）

### 未來可能的增強功能
```
1. 批量問題比較
   - 選擇多個問題（2-10 個）
   - 一次性測試所有問題的所有版本
   - 生成對比矩陣

2. 版本選擇器
   - 只測試指定的 2-3 個版本
   - 快速對比兩個版本的差異

3. 歷史記錄查看
   - 查看該問題的歷史測試記錄
   - 趨勢分析圖表

4. 即時通知
   - 測試完成後發送通知
   - 郵件或系統通知

5. 智能推薦
   - 根據問題類型推薦最佳版本
   - AI 分析版本適用性
```

---

## 📝 開發檢查清單

### 後端開發
- [ ] 創建 `SingleCaseVersionTester` 類別
- [ ] 實作 `version_comparison` API endpoint
- [ ] 實作 `version_comparison_progress` API endpoint（如果使用非同步）
- [ ] 添加結果序列化器
- [ ] 單元測試
- [ ] API 測試
- [ ] 效能測試

### 前端開發
- [ ] 創建 `VersionComparisonModal` 組件
- [ ] 添加版本比較按鈕到表格
- [ ] 實作測試執行邏輯
- [ ] 實作進度顯示
- [ ] 實作結果表格
- [ ] 添加匯出功能
- [ ] 添加錯誤處理
- [ ] 樣式優化
- [ ] 響應式設計測試

### 整合測試
- [ ] 端到端測試
- [ ] 不同瀏覽器測試
- [ ] 行動裝置測試
- [ ] 效能測試
- [ ] 負載測試

### 文檔
- [ ] API 文檔更新
- [ ] 使用者手冊
- [ ] 開發者文檔
- [ ] CHANGELOG 更新

---

## 🎓 總結

這個功能將為 VSA 測試系統帶來顯著的便利性提升：

1. **快速驗證**：20-30 秒內完成單問題的所有版本測試
2. **精準診斷**：立即發現問題在不同版本的表現差異
3. **節省資源**：不需要每次都執行完整的批量測試
4. **使用者友善**：直覺的 UI，一鍵操作
5. **可擴展性**：基礎架構支援未來的功能擴展

**預計開發時間：5 個工作天**
**預計上線後使用率：80% 的測試場景（取代完整批量測試）**

---

**文檔版本**: v1.0  
**創建日期**: 2025-11-28  
**作者**: AI Platform Team  
**狀態**: 規劃完成，待審核
