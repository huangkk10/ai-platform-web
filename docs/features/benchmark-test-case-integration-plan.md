# Benchmark Test Case 整合規劃文檔

## 📋 執行摘要

本文檔分析 **Protocol Benchmark Test Case** 和 **VSA (Vector Search Algorithm) Test Case** 兩個頁面的整合可行性，並提出統一管理方案。

---

## 🔍 現況分析

### 1. 兩個 Test Case 系統對比

| 項目 | Protocol Benchmark Test Case | VSA (Dify) Test Case |
|------|----------------------------|---------------------|
| **頁面路徑** | `/benchmark/test-cases` | `/benchmark/dify/test-cases` |
| **檔案位置** | `frontend/src/pages/benchmark/TestCasesListPage.js` | `frontend/src/pages/dify-benchmark/DifyTestCasePage.js` |
| **資料表** | `benchmark_test_case` | `dify_benchmark_test_case` |
| **Model 類別** | `BenchmarkTestCase` | `DifyBenchmarkTestCase` |
| **API 路徑** | `/api/benchmark/test-cases/` | `/api/dify-benchmark/test-cases/` |
| **主要用途** | Protocol 知識庫搜尋測試 | Dify AI 向量搜尋演算法測試 |

---

## 📊 功能差異分析

### Protocol Benchmark Test Case（當前頁面）

#### ✅ 特有功能
1. **文檔匹配機制**
   - `expected_document_ids`: 預期文檔 IDs（JSON 陣列）
   - `min_required_matches`: 最少匹配數（整數）
   - `acceptable_document_ids`: 可接受文檔 IDs（JSON 陣列）
   - `expected_keywords`: 預期關鍵字（JSON 陣列）
   - `expected_answer_summary`: 預期答案摘要（文字）

2. **測試分類**
   - `test_class_name`: 測試類別名稱（如 ULINK、UNH-IOL）
   - `question_type`: 題型（single_answer、multiple_answers、open_ended）
   - `category`: 自訂分類
   - `tags`: 標籤系統

3. **驗證機制**
   - `is_validated`: 是否已驗證
   - `total_runs`: 總執行次數
   - `avg_score`: 平均分數

4. **UI 特色**
   - 顯示關鍵字列表（前 3 個 + 更多）
   - 判斷條件欄位（文檔數、匹配數、關鍵字數）
   - 唯讀模式（無 CRUD 操作）
   - 詳細資訊 Modal 展示完整判斷條件

#### ❌ 缺少功能
- 無新增/編輯功能
- 無刪除功能
- 無批量匯入/匯出
- 無啟用/停用切換

---

### VSA (Dify) Test Case（VSA 頁面）

#### ✅ 特有功能
1. **AI 評分機制**
   - `expected_answer`: 期望答案（完整文字）
   - `answer_keywords`: 答案關鍵字（JSON 陣列）
   - `evaluation_criteria`: 評分標準（JSON 物件）
   - `max_score`: 滿分設定（Decimal，預設 100）

2. **測試管理**
   - `test_class_name`: 測試類別名稱
   - `question_type`: 問題類型
   - `difficulty_level`: 難度（easy、medium、hard）

3. **完整 CRUD 操作**
   - ✅ 新增測試案例（含表單驗證）
   - ✅ 編輯測試案例
   - ✅ 刪除測試案例（含確認）
   - ✅ 啟用/停用切換

4. **批量操作**
   - ✅ JSON 格式批量匯入
   - ✅ JSON 格式批量匯出
   - ✅ 範例格式說明

5. **UI 特色**
   - 標籤系統（可自訂）
   - 備註欄位（notes）
   - 統計卡片（總數、啟用、停用、難度分布）
   - 詳細資訊 Modal（展示期望答案）

#### ❌ 缺少功能
- 無文檔匹配機制（expected_document_ids）
- 無關鍵字列表顯示
- 無判斷條件摘要欄位

---

## 🎯 整合方案設計

### 方案選擇：**統一頁面 + 測試類型切換**

建議將兩個 Test Case 頁面整合為一個統一的測試案例管理頁面，透過頂部 Tab 或篩選器切換不同的測試類型。

---

## 🏗️ 整合架構設計

### 1. 統一資料模型（後端）

#### 選項 A：合併為單一 Model（推薦）⭐

```python
class UnifiedBenchmarkTestCase(models.Model):
    """統一的 Benchmark 測試案例"""
    
    # ===== 共用欄位 =====
    question = models.TextField(verbose_name="測試問題")
    test_class_name = models.CharField(max_length=200, blank=True, verbose_name="測試類別")
    difficulty_level = models.CharField(max_length=20, verbose_name="難度等級")
    question_type = models.CharField(max_length=50, blank=True, verbose_name="問題類型")
    category = models.CharField(max_length=100, blank=True, verbose_name="類別")
    tags = models.JSONField(default=list, verbose_name="標籤")
    is_active = models.BooleanField(default=True, verbose_name="是否啟用")
    
    # ===== 測試類型欄位（新增）=====
    test_type = models.CharField(
        max_length=50,
        choices=[
            ('protocol', 'Protocol 搜尋測試'),
            ('vsa', 'VSA 向量搜尋測試'),
            ('hybrid', '混合測試'),
        ],
        default='protocol',
        verbose_name="測試類型"
    )
    
    # ===== Protocol 專用欄位 =====
    expected_document_ids = models.JSONField(default=list, verbose_name="預期文檔IDs")
    min_required_matches = models.IntegerField(default=1, verbose_name="最少匹配數")
    acceptable_document_ids = models.JSONField(default=list, verbose_name="可接受文檔IDs")
    expected_keywords = models.JSONField(default=list, verbose_name="預期關鍵字")
    expected_answer_summary = models.TextField(blank=True, verbose_name="預期答案摘要")
    
    # ===== VSA 專用欄位 =====
    expected_answer = models.TextField(blank=True, verbose_name="期望答案")
    answer_keywords = models.JSONField(default=list, verbose_name="答案關鍵字")
    evaluation_criteria = models.JSONField(default=dict, verbose_name="評分標準")
    max_score = models.DecimalField(max_digits=5, decimal_places=2, default=100.00, verbose_name="滿分")
    
    # ===== 統計與驗證欄位 =====
    is_validated = models.BooleanField(default=False, verbose_name="是否已驗證")
    total_runs = models.IntegerField(default=0, verbose_name="總執行次數")
    avg_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="平均分數")
    
    # ===== 管理欄位 =====
    notes = models.TextField(blank=True, verbose_name="備註")
    source = models.CharField(max_length=100, blank=True, verbose_name="來源")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="創建時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="創建者")
    
    class Meta:
        db_table = 'unified_benchmark_test_case'
        ordering = ['test_type', 'category', 'difficulty_level']
        verbose_name = '統一測試案例'
        verbose_name_plural = '統一測試案例'
```

**優點**：
- ✅ 單一資料來源，易於管理
- ✅ 支援未來混合測試類型
- ✅ 統計分析更方便
- ✅ 減少資料冗餘

**缺點**：
- ⚠️ 需要資料遷移
- ⚠️ 欄位較多（但可透過 `test_type` 動態顯示）

#### 選項 B：保持兩個 Model + 統一 API（次選）

保持現有的 `BenchmarkTestCase` 和 `DifyBenchmarkTestCase`，透過統一的 API 層進行整合。

**優點**：
- ✅ 不需要資料遷移
- ✅ 保持現有邏輯不變

**缺點**：
- ❌ 後端邏輯複雜
- ❌ 統計分析困難
- ❌ 未來擴展性差

---

### 2. 前端整合設計

#### 統一頁面結構

```
UnifiedTestCasePage.js
├── 頂部 Tab 切換
│   ├── Protocol Test Cases
│   └── VSA Test Cases
│   
├── 統計卡片區域（動態）
│   ├── 總測試案例
│   ├── 啟用中
│   ├── 難度分布
│   └── 類別數量
│
├── 篩選區域（共用）
│   ├── 搜尋框
│   ├── 難度篩選
│   ├── 類別篩選
│   └── 測試類型篩選（新增）
│
├── 主要表格（動態欄位）
│   ├── 共用欄位
│   │   ├── ID
│   │   ├── 問題
│   │   ├── 測試類別
│   │   ├── 難度
│   │   └── 狀態
│   │
│   ├── Protocol 專用欄位
│   │   ├── 關鍵字
│   │   ├── 期望文檔數
│   │   ├── 最少匹配數
│   │   └── 判斷條件
│   │
│   └── VSA 專用欄位
│       ├── 標籤
│       ├── 滿分
│       └── 創建時間
│
└── 操作區域（動態）
    ├── Protocol 模式：查看詳情
    └── VSA 模式：查看/編輯/刪除/啟用切換
```

#### Tab 切換示意圖

```jsx
<Tabs defaultActiveKey="protocol" onChange={handleTabChange}>
  <TabPane 
    tab={
      <Space>
        <FileTextOutlined />
        Protocol Test Cases
        <Badge count={protocolCount} showZero />
      </Space>
    } 
    key="protocol"
  >
    {/* Protocol 專用表格 */}
  </TabPane>
  
  <TabPane 
    tab={
      <Space>
        <RobotOutlined />
        VSA Test Cases
        <Badge count={vsaCount} showZero />
      </Space>
    } 
    key="vsa"
  >
    {/* VSA 專用表格 */}
  </TabPane>
</Tabs>
```

---

### 3. 動態欄位配置

```javascript
const getColumns = (testType) => {
  // 共用欄位
  const baseColumns = [
    { title: 'ID', dataIndex: 'id', ... },
    { title: '問題', dataIndex: 'question', ... },
    { title: '測試類別', dataIndex: 'test_class_name', ... },
    { title: '難度', dataIndex: 'difficulty_level', ... },
  ];
  
  // Protocol 專用欄位
  const protocolColumns = [
    { title: '關鍵字', dataIndex: 'expected_keywords', ... },
    { title: '期望文檔數', dataIndex: 'expected_document_ids', ... },
    { title: '最少匹配數', dataIndex: 'min_required_matches', ... },
    { title: '判斷條件', key: 'evaluation_criteria', ... },
  ];
  
  // VSA 專用欄位
  const vsaColumns = [
    { title: '標籤', dataIndex: 'tags', ... },
    { title: '滿分', dataIndex: 'max_score', ... },
    { title: '創建時間', dataIndex: 'created_at', ... },
  ];
  
  // 操作欄位（動態）
  const actionColumn = {
    title: '操作',
    key: 'actions',
    render: (_, record) => {
      if (testType === 'protocol') {
        return <Button icon={<EyeOutlined />} onClick={() => showDetail(record)} />;
      } else {
        return (
          <Space>
            <Button icon={<EyeOutlined />} onClick={() => showDetail(record)} />
            <Button icon={<EditOutlined />} onClick={() => showEdit(record)} />
            <Button icon={<DeleteOutlined />} onClick={() => handleDelete(record)} />
          </Space>
        );
      }
    }
  };
  
  // 根據測試類型組合欄位
  if (testType === 'protocol') {
    return [...baseColumns, ...protocolColumns, actionColumn];
  } else {
    return [...baseColumns, ...vsaColumns, actionColumn];
  }
};
```

---

## 📋 實施步驟（分階段）

### 階段 1：準備工作（1 天）

#### 1.1 資料分析
- [ ] 分析現有資料量
  - `benchmark_test_case` 表記錄數
  - `dify_benchmark_test_case` 表記錄數
- [ ] 檢查欄位重疊與差異
- [ ] 評估資料遷移風險

#### 1.2 技術評估
- [ ] 確認 API 版本相容性
- [ ] 確認前端組件共用性
- [ ] 評估效能影響

---

### 階段 2：後端整合（2-3 天）

#### 2.1 資料庫遷移（選項 A）

**步驟 1：創建新表**
```bash
# 創建 migration
docker exec ai-django python manage.py makemigrations

# 檢查 SQL
docker exec ai-django python manage.py sqlmigrate api XXXX

# 執行 migration
docker exec ai-django python manage.py migrate
```

**步驟 2：資料遷移腳本**
```python
# backend/scripts/migrate_test_cases.py

def migrate_protocol_test_cases():
    """遷移 Protocol Test Cases"""
    from api.models import BenchmarkTestCase, UnifiedBenchmarkTestCase
    
    for old_case in BenchmarkTestCase.objects.all():
        UnifiedBenchmarkTestCase.objects.create(
            test_type='protocol',
            question=old_case.question,
            test_class_name=old_case.test_class_name,
            difficulty_level=old_case.difficulty_level,
            expected_document_ids=old_case.expected_document_ids,
            min_required_matches=old_case.min_required_matches,
            # ... 其他欄位
        )

def migrate_vsa_test_cases():
    """遷移 VSA Test Cases"""
    from api.models import DifyBenchmarkTestCase, UnifiedBenchmarkTestCase
    
    for old_case in DifyBenchmarkTestCase.objects.all():
        UnifiedBenchmarkTestCase.objects.create(
            test_type='vsa',
            question=old_case.question,
            test_class_name=old_case.test_class_name,
            difficulty_level=old_case.difficulty_level,
            expected_answer=old_case.expected_answer,
            answer_keywords=old_case.answer_keywords,
            # ... 其他欄位
        )
```

**步驟 3：驗證資料完整性**
```python
def validate_migration():
    """驗證遷移結果"""
    old_protocol_count = BenchmarkTestCase.objects.count()
    old_vsa_count = DifyBenchmarkTestCase.objects.count()
    new_total_count = UnifiedBenchmarkTestCase.objects.count()
    
    assert new_total_count == (old_protocol_count + old_vsa_count)
    print(f"✅ 資料遷移成功：{new_total_count} 筆")
```

#### 2.2 統一 API 端點

**新 API 路徑**：`/api/unified-benchmark/test-cases/`

**ViewSet 實作**：
```python
# backend/api/views/viewsets/unified_benchmark_viewsets.py

class UnifiedBenchmarkTestCaseViewSet(viewsets.ModelViewSet):
    """統一的 Benchmark 測試案例 ViewSet"""
    queryset = UnifiedBenchmarkTestCase.objects.all()
    serializer_class = UnifiedBenchmarkTestCaseSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """根據 test_type 篩選"""
        queryset = super().get_queryset()
        test_type = self.request.query_params.get('test_type', None)
        
        if test_type:
            queryset = queryset.filter(test_type=test_type)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """統計資料 API"""
        test_type = request.query_params.get('test_type', None)
        queryset = self.get_queryset()
        
        if test_type:
            queryset = queryset.filter(test_type=test_type)
        
        stats = {
            'total': queryset.count(),
            'active': queryset.filter(is_active=True).count(),
            'by_difficulty': {
                'easy': queryset.filter(difficulty_level='easy').count(),
                'medium': queryset.filter(difficulty_level='medium').count(),
                'hard': queryset.filter(difficulty_level='hard').count(),
            },
            'by_type': {
                'protocol': queryset.filter(test_type='protocol').count(),
                'vsa': queryset.filter(test_type='vsa').count(),
            }
        }
        
        return Response(stats)
```

#### 2.3 Serializer 設計

```python
# backend/api/serializers.py

class UnifiedBenchmarkTestCaseSerializer(serializers.ModelSerializer):
    """統一測試案例序列化器"""
    
    class Meta:
        model = UnifiedBenchmarkTestCase
        fields = '__all__'
    
    def to_representation(self, instance):
        """根據 test_type 動態返回欄位"""
        data = super().to_representation(instance)
        
        # Protocol 類型：移除 VSA 專用欄位
        if instance.test_type == 'protocol':
            data.pop('expected_answer', None)
            data.pop('answer_keywords', None)
            data.pop('evaluation_criteria', None)
            data.pop('max_score', None)
        
        # VSA 類型：移除 Protocol 專用欄位
        elif instance.test_type == 'vsa':
            data.pop('expected_document_ids', None)
            data.pop('min_required_matches', None)
            data.pop('acceptable_document_ids', None)
            data.pop('expected_answer_summary', None)
        
        return data
```

---

### 階段 3：前端整合（3-4 天）

#### 3.1 創建統一頁面組件

**檔案位置**：`frontend/src/pages/benchmark/UnifiedTestCasePage.js`

**核心結構**：
```jsx
const UnifiedTestCasePage = () => {
  const [activeTab, setActiveTab] = useState('protocol');
  const [testCases, setTestCases] = useState([]);
  const [statistics, setStatistics] = useState({});
  
  // 載入資料（根據 activeTab）
  const loadTestCases = async () => {
    const response = await unifiedBenchmarkApi.getTestCases({ 
      test_type: activeTab 
    });
    setTestCases(response.data);
  };
  
  // Tab 切換處理
  const handleTabChange = (key) => {
    setActiveTab(key);
    // 重新載入資料
  };
  
  // 動態欄位配置
  const columns = getColumns(activeTab);
  
  return (
    <div>
      <Tabs activeKey={activeTab} onChange={handleTabChange}>
        <TabPane tab="Protocol Test Cases" key="protocol">
          {/* 統計卡片 */}
          <StatisticsCards data={statistics} type="protocol" />
          
          {/* 篩選區域 */}
          <FilterArea />
          
          {/* 表格 */}
          <Table columns={columns} dataSource={testCases} />
        </TabPane>
        
        <TabPane tab="VSA Test Cases" key="vsa">
          {/* 統計卡片 */}
          <StatisticsCards data={statistics} type="vsa" />
          
          {/* 篩選區域 */}
          <FilterArea />
          
          {/* 表格 + CRUD 操作 */}
          <Table columns={columns} dataSource={testCases} />
          <CRUDModals />
        </TabPane>
      </Tabs>
    </div>
  );
};
```

#### 3.2 API Service 整合

**檔案位置**：`frontend/src/services/unifiedBenchmarkApi.js`

```javascript
import api from './api';

export const unifiedBenchmarkApi = {
  // 獲取測試案例列表
  getTestCases: (params) => {
    return api.get('/api/unified-benchmark/test-cases/', { params });
  },
  
  // 獲取統計資料
  getStatistics: (testType) => {
    return api.get('/api/unified-benchmark/test-cases/statistics/', {
      params: { test_type: testType }
    });
  },
  
  // 創建測試案例
  createTestCase: (data) => {
    return api.post('/api/unified-benchmark/test-cases/', data);
  },
  
  // 更新測試案例
  updateTestCase: (id, data) => {
    return api.put(`/api/unified-benchmark/test-cases/${id}/`, data);
  },
  
  // 刪除測試案例
  deleteTestCase: (id) => {
    return api.delete(`/api/unified-benchmark/test-cases/${id}/`);
  },
  
  // 批量匯入
  bulkImport: (testType, data) => {
    return api.post('/api/unified-benchmark/test-cases/bulk_import/', {
      test_type: testType,
      ...data
    });
  },
  
  // 批量匯出
  bulkExport: (testType) => {
    return api.get('/api/unified-benchmark/test-cases/bulk_export/', {
      params: { test_type: testType },
      responseType: 'blob'
    });
  },
};
```

#### 3.3 路由更新

**檔案位置**：`frontend/src/App.js`

```jsx
// 移除舊路由
// ❌ <Route path="/benchmark/test-cases" element={<TestCasesListPage />} />
// ❌ <Route path="/benchmark/dify/test-cases" element={<DifyTestCasePage />} />

// 新增統一路由
<Route 
  path="/benchmark/test-cases" 
  element={<UnifiedTestCasePage defaultTab="protocol" />} 
/>

// 可選：保留 VSA 入口，但導向統一頁面的 VSA Tab
<Route 
  path="/benchmark/dify/test-cases" 
  element={<UnifiedTestCasePage defaultTab="vsa" />} 
/>
```

#### 3.4 Sidebar 選單更新

**檔案位置**：`frontend/src/components/Sidebar.js`

```jsx
// Protocol Benchmark 分組
items.push({
  key: 'benchmark-test-cases',
  icon: <FileTextOutlined />,
  label: 'Test Cases',
  onClick: () => navigate('/benchmark/test-cases?tab=protocol')
});

// VSA Benchmark 分組
items.push({
  key: 'benchmark-dify-test-cases',
  icon: <FileSearchOutlined />,
  label: 'VSA Test Cases',
  onClick: () => navigate('/benchmark/test-cases?tab=vsa')  // ✅ 導向統一頁面
});
```

---

### 階段 4：測試與驗證（2 天）

#### 4.1 單元測試

```python
# backend/tests/test_unified_benchmark.py

class UnifiedBenchmarkTestCaseTests(TestCase):
    def test_create_protocol_test_case(self):
        """測試創建 Protocol 測試案例"""
        data = {
            'test_type': 'protocol',
            'question': 'Test question',
            'expected_document_ids': [1, 2, 3],
            'min_required_matches': 2,
        }
        response = self.client.post('/api/unified-benchmark/test-cases/', data)
        self.assertEqual(response.status_code, 201)
    
    def test_create_vsa_test_case(self):
        """測試創建 VSA 測試案例"""
        data = {
            'test_type': 'vsa',
            'question': 'Test question',
            'expected_answer': 'Expected answer',
            'max_score': 100,
        }
        response = self.client.post('/api/unified-benchmark/test-cases/', data)
        self.assertEqual(response.status_code, 201)
    
    def test_filter_by_test_type(self):
        """測試按類型篩選"""
        response = self.client.get('/api/unified-benchmark/test-cases/?test_type=protocol')
        self.assertEqual(response.status_code, 200)
        for item in response.data['results']:
            self.assertEqual(item['test_type'], 'protocol')
```

#### 4.2 整合測試

- [ ] Protocol Test Cases Tab 功能正常
- [ ] VSA Test Cases Tab 功能正常
- [ ] Tab 切換時資料正確載入
- [ ] 篩選和搜尋功能正常
- [ ] CRUD 操作（VSA 模式）正常
- [ ] 批量匯入/匯出功能正常
- [ ] 統計資料正確顯示

#### 4.3 效能測試

- [ ] 大量資料載入速度（1000+ 筆）
- [ ] Tab 切換響應時間
- [ ] API 響應時間
- [ ] 瀏覽器記憶體使用

---

## 📊 預期效益

### 1. 使用者體驗改善
- ✅ **統一入口**：不需要在兩個頁面間切換
- ✅ **一致性**：UI/UX 設計統一
- ✅ **效率提升**：快速比較不同類型的測試案例

### 2. 開發效率提升
- ✅ **代碼重用**：共用組件和邏輯
- ✅ **維護簡化**：只需維護一個頁面
- ✅ **擴展容易**：新增測試類型更容易

### 3. 資料管理優化
- ✅ **統一管理**：單一資料來源
- ✅ **統計便利**：跨類型統計分析
- ✅ **查詢效率**：單一查詢取得所有資料

---

## ⚠️ 風險與挑戰

### 1. 資料遷移風險
**風險**：資料遷移失敗或遺失
**緩解措施**：
- ✅ 完整備份現有資料
- ✅ 在測試環境先執行遷移
- ✅ 保留舊表作為備份（不立即刪除）
- ✅ 編寫資料驗證腳本

### 2. 向後相容性
**風險**：現有功能受影響
**緩解措施**：
- ✅ 保留舊 API 端點（標記為 deprecated）
- ✅ 提供過渡期（例如 3 個月）
- ✅ 完整的測試覆蓋

### 3. 效能影響
**風險**：單一頁面資料量過大
**緩解措施**：
- ✅ 實作分頁載入
- ✅ 使用虛擬滾動（大量資料時）
- ✅ API 端實作資料分頁

### 4. UI 複雜度
**風險**：動態欄位導致 UI 混亂
**緩解措施**：
- ✅ 清晰的 Tab 區分
- ✅ 根據類型顯示不同欄位
- ✅ 提供清晰的使用說明

---

## 🎯 推薦方案

### 建議採用：**選項 A - 完整整合方案**

**理由**：
1. ✅ **長期效益最大**：統一管理、易於擴展
2. ✅ **使用者體驗最佳**：單一入口、一致的操作
3. ✅ **開發效率最高**：減少重複代碼
4. ✅ **未來擴展容易**：可輕鬆新增新的測試類型

**實施建議**：
- 📅 **時間規劃**：10-12 個工作天
- 👥 **人力需求**：1-2 名全端開發者
- 🔧 **技術棧**：Django + React + Ant Design（現有技術棧）
- 📊 **優先級**：中高（建議在下一個 Sprint 執行）

---

## 📅 時程規劃

| 階段 | 任務 | 預計時間 | 開始日期 | 結束日期 |
|------|------|---------|---------|---------|
| 階段 1 | 準備工作 | 1 天 | Day 1 | Day 1 |
| 階段 2 | 後端整合 | 2-3 天 | Day 2 | Day 4 |
| 階段 3 | 前端整合 | 3-4 天 | Day 5 | Day 8 |
| 階段 4 | 測試驗證 | 2 天 | Day 9 | Day 10 |
| **總計** | | **10 天** | | |

---

## 📝 檢查清單

### 開始前
- [ ] 備份現有資料庫
- [ ] 建立開發分支
- [ ] 通知相關使用者（如有需要）

### 開發中
- [ ] 完成資料模型設計
- [ ] 完成資料遷移腳本
- [ ] 完成統一 API 開發
- [ ] 完成前端統一頁面
- [ ] 完成單元測試
- [ ] 完成整合測試

### 上線前
- [ ] 在測試環境完整測試
- [ ] 效能測試通過
- [ ] 使用者驗收測試（UAT）
- [ ] 撰寫使用者文檔
- [ ] 準備回滾方案

### 上線後
- [ ] 監控系統日誌
- [ ] 收集使用者反饋
- [ ] 效能監控
- [ ] 必要時進行調整

---

## 📚 相關文檔

- **現有頁面**：
  - `frontend/src/pages/benchmark/TestCasesListPage.js`
  - `frontend/src/pages/dify-benchmark/DifyTestCasePage.js`
  
- **資料模型**：
  - `backend/api/models.py` - `BenchmarkTestCase`
  - `backend/api/models.py` - `DifyBenchmarkTestCase`
  
- **API 服務**：
  - `frontend/src/services/benchmarkApi.js`
  - `frontend/src/services/difyBenchmarkApi.js`

---

## 💡 後續建議

### 短期（整合後 1-2 個月）
1. **新增混合測試類型**：同時測試 Protocol 和 VSA
2. **批量編輯功能**：支援批量修改測試案例屬性
3. **測試案例版本控制**：追蹤測試案例的歷史變更

### 中期（3-6 個月）
1. **AI 輔助生成測試案例**：利用 AI 自動生成測試問題和答案
2. **測試案例推薦系統**：根據知識庫內容推薦應該測試的問題
3. **視覺化測試覆蓋率**：顯示哪些知識點已被測試覆蓋

### 長期（6-12 個月）
1. **測試案例市場**：分享和下載社群貢獻的測試案例
2. **自動化測試執行**：定期自動執行測試並生成報告
3. **機器學習優化**：利用歷史測試資料優化測試案例設計

---

## 🎓 結論

整合 **Protocol Benchmark Test Case** 和 **VSA Test Case** 是一個可行且有價值的改進方案。透過統一的頁面和資料模型，可以顯著提升使用者體驗、開發效率和系統可維護性。

**建議優先級**：⭐⭐⭐⭐ (高)

**建議實施時間**：下一個 Sprint 或功能開發週期

**預期投資回報**：
- 💰 **開發成本**：10 個工作天
- 📈 **效益回收**：3-6 個月內顯現
- 🎯 **長期價值**：持續獲益

---

**文檔版本**：v1.0  
**創建日期**：2025-11-25  
**作者**：AI Platform Team  
**狀態**：✅ 規劃完成，等待審核批准
