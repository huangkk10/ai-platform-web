# 🔬 上下文視窗 A/B 測試評估方案

**規劃日期**: 2025-11-09  
**目的**: 保留現有方法，與新方法進行客觀比較  
**策略**: 雙軌並行 + 數據驅動決策  
**原則**: 先不改 code，完整評估後再決定

---

## 📋 目錄

1. [評估目標](#1-評估目標)
2. [雙軌並行架構](#2-雙軌並行架構)
3. [評估維度設計](#3-評估維度設計)
4. [數據收集方案](#4-數據收集方案)
5. [API 設計（雙版本）](#5-api-設計雙版本)
6. [前端 A/B 測試介面](#6-前端-ab-測試介面)
7. [評估指標定義](#7-評估指標定義)
8. [數據分析計畫](#8-數據分析計畫)
9. [決策矩陣](#9-決策矩陣)
10. [實施時程](#10-實施時程)

---

## 1. 評估目標

### 🎯 核心問題

**我們想回答的問題**：
1. ✅ 新的上下文視窗方法是否真的解決了「段落不連續」問題？
2. ✅ 新方法是否提升了用戶滿意度？
3. ✅ 新方法的效能開銷是否可接受？
4. ✅ 哪些場景適合新方法，哪些適合舊方法？
5. ✅ 是否應該完全替換舊方法，還是兩者並存？

### 📊 評估維度

| 維度 | 現有方法 | 新方法 (上下文視窗) | 評估方式 |
|------|---------|-------------------|---------|
| **功能性** | ✅ 基礎搜尋 | ✅ 搜尋 + 上下文 | 用戶反饋 |
| **準確度** | 向量相似度 | 向量相似度（相同） | 比較相似度分數 |
| **完整性** | ❌ 缺少上下文 | ✅ 完整上下文 | 用戶理解速度 |
| **效能** | 快 (< 50ms) | 中 (< 100ms) | 回應時間測量 |
| **用戶體驗** | 需手動查找 | 自動提供上下文 | 滿意度評分 |
| **資源消耗** | 低 | 中（多 2-3 次 DB 查詢） | 監控資料 |

---

## 2. 雙軌並行架構

### 🏗️ 架構設計原則

✅ **完全獨立** - 兩種方法互不干擾  
✅ **公平比較** - 使用相同的資料和搜尋參數  
✅ **易於切換** - 透過配置或參數切換版本  
✅ **數據追蹤** - 記錄所有關鍵指標  

### 📐 架構圖

```
┌─────────────────────────────────────────────────────────────┐
│                    用戶發起搜尋請求                          │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│               API 路由層 (智能分流)                          │
│                                                              │
│  檢查參數:                                                   │
│  - search_version: 'v1' | 'v2' | 'ab_test'                 │
│  - user_id: 用於 A/B 分組                                   │
│  - ab_test_enabled: true/false                              │
└─────────┬───────────────────────────────┬───────────────────┘
          │                               │
          ▼                               ▼
┌─────────────────────┐       ┌─────────────────────────────┐
│   V1: 現有方法       │       │   V2: 新方法（上下文視窗）   │
│   (Baseline)        │       │   (Context Window)          │
├─────────────────────┤       ├─────────────────────────────┤
│ • search_sections() │       │ • search_sections_with_    │
│                     │       │   expanded_context()        │
│ • 單純向量搜尋       │       │                             │
│ • 無上下文擴展       │       │ • 向量搜尋 + 上下文         │
│ • 快速回應          │       │ • 相鄰段落 + 父子段落       │
│                     │       │ • 智能合併                  │
└──────────┬──────────┘       └──────────┬──────────────────┘
           │                             │
           │                             │
           └─────────┬───────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│               數據收集層 (統一追蹤)                          │
│                                                              │
│  記錄:                                                       │
│  - 搜尋參數 (query, threshold, limit)                       │
│  - 版本標識 (v1/v2)                                         │
│  - 回應時間 (execution_time)                                │
│  - 資料庫查詢次數 (db_query_count)                          │
│  - 結果數量 (result_count)                                  │
│  - 用戶反饋 (user_feedback)                                 │
│  - 時間戳記 (timestamp)                                     │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                   儲存到資料庫                               │
│                                                              │
│  • search_ab_test_logs (新表)                               │
│  • search_performance_metrics (新表)                        │
│  • user_feedback_records (新表)                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 評估維度設計

### 📊 量化指標（Quantitative Metrics）

#### 3.1 效能指標

| 指標 | V1 目標 | V2 目標 | 測量方式 |
|------|---------|---------|---------|
| **平均回應時間** | < 50ms | < 100ms | `execution_time` |
| **P95 回應時間** | < 80ms | < 150ms | 統計分析 |
| **P99 回應時間** | < 120ms | < 200ms | 統計分析 |
| **資料庫查詢次數** | 1-2 次 | 2-4 次 | SQL 日誌 |
| **記憶體使用** | < 10MB | < 30MB | 系統監控 |
| **CPU 使用率** | < 5% | < 10% | 系統監控 |

#### 3.2 搜尋品質指標

| 指標 | 測量方式 | V1 vs V2 比較 |
|------|---------|--------------|
| **平均相似度分數** | 取前 5 個結果的平均值 | 應該相同（相同向量搜尋） |
| **結果多樣性** | 結果中不同 source_id 的數量 | V2 可能更高（包含上下文） |
| **覆蓋率** | 有結果的搜尋佔比 | 應該相同 |

#### 3.3 上下文品質指標（僅 V2）

| 指標 | 測量方式 | 目標值 |
|------|---------|--------|
| **上下文命中率** | 匹配段落有有效上下文的比例 | > 80% |
| **平均上下文段落數** | before + after + parent + children | 2-5 個 |
| **上下文總字數** | 所有上下文段落的字數總和 | 500-2000 字 |

### 📝 質化指標（Qualitative Metrics）

#### 3.4 用戶體驗指標

```
用戶反饋問卷（5 點量表）:

1. 搜尋結果的相關性
   ⭐ ⭐ ⭐ ⭐ ⭐ (1=不相關, 5=非常相關)

2. 結果的完整性
   ⭐ ⭐ ⭐ ⭐ ⭐ (1=資訊不足, 5=資訊完整)

3. 理解的容易度
   ⭐ ⭐ ⭐ ⭐ ⭐ (1=難以理解, 5=容易理解)

4. 是否需要額外查找資料
   ⭐ ⭐ ⭐ ⭐ ⭐ (1=經常需要, 5=不需要)

5. 整體滿意度
   ⭐ ⭐ ⭐ ⭐ ⭐ (1=不滿意, 5=非常滿意)
```

#### 3.5 行為指標

| 指標 | 定義 | V1 vs V2 預期差異 |
|------|------|------------------|
| **點擊率** | 用戶點擊「查看完整文檔」的比例 | V2 應該更低（已有上下文） |
| **停留時間** | 用戶在結果頁面的停留時間 | V2 可能更長（閱讀上下文） |
| **重新搜尋率** | 同一用戶短時間內再次搜尋的比例 | V2 應該更低（一次找到） |
| **滿意點擊** | 用戶在結果上標記「有幫助」 | V2 應該更高 |

---

## 4. 數據收集方案

### 📊 資料庫表設計

#### 4.1 A/B 測試日誌表

```sql
-- 記錄每次搜尋的完整資訊
CREATE TABLE search_ab_test_logs (
    id SERIAL PRIMARY KEY,
    
    -- 搜尋資訊
    session_id VARCHAR(100) NOT NULL,           -- 搜尋 session
    user_id INTEGER REFERENCES auth_user(id),   -- 用戶 ID
    query TEXT NOT NULL,                        -- 搜尋查詢
    assistant_type VARCHAR(50) NOT NULL,        -- 'protocol_assistant', 'rvt_assistant'
    
    -- 版本資訊
    search_version VARCHAR(10) NOT NULL,        -- 'v1', 'v2'
    ab_group VARCHAR(10),                       -- 'A', 'B', NULL (手動選擇)
    
    -- 搜尋參數
    threshold DECIMAL(3,2),
    limit_count INTEGER,
    context_window INTEGER,                     -- V2 專用
    context_mode VARCHAR(20),                   -- V2 專用
    
    -- 效能指標
    execution_time_ms DECIMAL(10,2),            -- 執行時間（毫秒）
    db_query_count INTEGER,                     -- 資料庫查詢次數
    memory_usage_mb DECIMAL(10,2),              -- 記憶體使用（MB）
    
    -- 結果資訊
    result_count INTEGER,                       -- 返回結果數量
    avg_similarity DECIMAL(5,4),                -- 平均相似度分數
    has_context BOOLEAN DEFAULT FALSE,          -- 是否包含上下文（V2）
    context_sections_count INTEGER,             -- 上下文段落數量（V2）
    total_context_words INTEGER,                -- 上下文總字數（V2）
    
    -- 時間戳記
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- 索引
    INDEX idx_search_logs_user (user_id),
    INDEX idx_search_logs_version (search_version),
    INDEX idx_search_logs_session (session_id),
    INDEX idx_search_logs_created (created_at)
);
```

#### 4.2 用戶反饋表

```sql
-- 用戶對搜尋結果的反饋
CREATE TABLE search_user_feedback (
    id SERIAL PRIMARY KEY,
    
    -- 關聯到搜尋記錄
    search_log_id INTEGER REFERENCES search_ab_test_logs(id),
    user_id INTEGER REFERENCES auth_user(id),
    search_version VARCHAR(10) NOT NULL,
    
    -- 量化反饋（1-5 分）
    relevance_score INTEGER CHECK (relevance_score BETWEEN 1 AND 5),          -- 相關性
    completeness_score INTEGER CHECK (completeness_score BETWEEN 1 AND 5),    -- 完整性
    understanding_score INTEGER CHECK (understanding_score BETWEEN 1 AND 5),  -- 理解度
    need_more_info_score INTEGER CHECK (need_more_info_score BETWEEN 1 AND 5), -- 需要額外資訊
    overall_satisfaction INTEGER CHECK (overall_satisfaction BETWEEN 1 AND 5), -- 整體滿意度
    
    -- 質化反饋
    comment TEXT,                               -- 用戶評論
    
    -- 行為標記
    clicked_view_full BOOLEAN DEFAULT FALSE,    -- 是否點擊查看完整文檔
    marked_helpful BOOLEAN DEFAULT FALSE,       -- 是否標記有幫助
    
    -- 時間戳記
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- 索引
    INDEX idx_feedback_user (user_id),
    INDEX idx_feedback_version (search_version),
    INDEX idx_feedback_log (search_log_id)
);
```

#### 4.3 效能監控表

```sql
-- 定期採樣的效能數據
CREATE TABLE search_performance_metrics (
    id SERIAL PRIMARY KEY,
    
    -- 版本資訊
    search_version VARCHAR(10) NOT NULL,
    assistant_type VARCHAR(50) NOT NULL,
    
    -- 統計時間範圍
    metric_date DATE NOT NULL,
    metric_hour INTEGER CHECK (metric_hour BETWEEN 0 AND 23),
    
    -- 效能統計（每小時統計）
    total_searches INTEGER DEFAULT 0,
    avg_execution_time_ms DECIMAL(10,2),
    p50_execution_time_ms DECIMAL(10,2),
    p95_execution_time_ms DECIMAL(10,2),
    p99_execution_time_ms DECIMAL(10,2),
    max_execution_time_ms DECIMAL(10,2),
    
    avg_db_query_count DECIMAL(5,2),
    avg_memory_usage_mb DECIMAL(10,2),
    
    -- 結果品質統計
    avg_result_count DECIMAL(5,2),
    avg_similarity_score DECIMAL(5,4),
    
    -- 用戶滿意度統計
    avg_satisfaction_score DECIMAL(3,2),
    feedback_count INTEGER DEFAULT 0,
    
    -- 時間戳記
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- 唯一約束
    UNIQUE(search_version, assistant_type, metric_date, metric_hour),
    
    -- 索引
    INDEX idx_metrics_version (search_version),
    INDEX idx_metrics_date (metric_date)
);
```

---

## 5. API 設計（雙版本）

### 🔌 統一 API 端點（智能路由）

#### 5.1 主 API 端點（推薦）

```python
@action(detail=False, methods=['post'])
def search_sections_smart(self, request):
    """
    智能段落搜尋 API（支援 A/B 測試）
    
    POST /api/rvt-guides/search_sections_smart/
    
    Request Body:
    {
        "query": "軟體配置",
        "limit": 5,
        "threshold": 0.7,
        
        // 版本控制參數
        "search_version": "v2",          // 'v1', 'v2', 'auto' (自動 A/B)
        "ab_test_enabled": true,         // 是否啟用 A/B 測試
        
        // V2 專用參數（當 search_version='v2' 時）
        "context_window": 2,
        "context_mode": "both",
        
        // 追蹤參數
        "session_id": "uuid-xxx-xxx",    // 前端生成的 session ID
        "enable_tracking": true          // 是否記錄到 A/B 測試日誌
    }
    
    Response:
    {
        "success": true,
        "search_version": "v2",          // 實際使用的版本
        "ab_group": "B",                 // A/B 分組（如果啟用）
        "results": [...],
        "execution_time": "85ms",
        "tracking_id": 12345,            // 日誌記錄 ID（用於後續反饋）
        
        // 效能指標（用於前端展示比較）
        "performance": {
            "db_query_count": 3,
            "memory_usage_mb": 25.3,
            "result_count": 3,
            "avg_similarity": 0.85
        }
    }
    """
    try:
        # 1. 解析參數
        query = request.data.get('query', '')
        search_version = request.data.get('search_version', 'auto')
        ab_test_enabled = request.data.get('ab_test_enabled', False)
        session_id = request.data.get('session_id', str(uuid.uuid4()))
        enable_tracking = request.data.get('enable_tracking', True)
        
        # 2. 決定使用哪個版本
        if search_version == 'auto' and ab_test_enabled:
            # A/B 測試：根據 user_id 分組
            ab_group, actual_version = self._assign_ab_group(request.user.id)
        else:
            ab_group = None
            actual_version = search_version if search_version in ['v1', 'v2'] else 'v1'
        
        # 3. 初始化效能追蹤
        start_time = timezone.now()
        performance_tracker = PerformanceTracker()
        
        # 4. 執行對應版本的搜尋
        if actual_version == 'v1':
            results = self._search_v1(request, performance_tracker)
        else:  # v2
            results = self._search_v2(request, performance_tracker)
        
        execution_time = (timezone.now() - start_time).total_seconds() * 1000
        
        # 5. 記錄到 A/B 測試日誌
        tracking_id = None
        if enable_tracking:
            tracking_id = self._log_search_to_ab_test(
                session_id=session_id,
                user_id=request.user.id,
                query=query,
                search_version=actual_version,
                ab_group=ab_group,
                request_data=request.data,
                results=results,
                execution_time=execution_time,
                performance=performance_tracker.get_metrics()
            )
        
        # 6. 返回結果
        return Response({
            'success': True,
            'search_version': actual_version,
            'ab_group': ab_group,
            'results': results,
            'execution_time': f'{execution_time:.0f}ms',
            'tracking_id': tracking_id,
            'performance': performance_tracker.get_metrics()
        })
        
    except Exception as e:
        logger.error(f"智能搜尋失敗: {str(e)}", exc_info=True)
        return Response({'error': str(e)}, status=500)

def _search_v1(self, request, tracker):
    """V1: 現有方法（基準）"""
    tracker.start('db_query')
    
    from library.common.knowledge_base.section_search_service import SectionSearchService
    search_service = SectionSearchService()
    
    results = search_service.search_sections(
        query=request.data.get('query'),
        source_table='rvt_guide',
        limit=request.data.get('limit', 5),
        threshold=request.data.get('threshold', 0.7)
    )
    
    tracker.end('db_query')
    tracker.record('db_query_count', 1)
    
    return self._format_results_v1(results)

def _search_v2(self, request, tracker):
    """V2: 新方法（上下文視窗）"""
    tracker.start('db_query')
    
    from library.common.knowledge_base.section_search_service import SectionSearchService
    search_service = SectionSearchService()
    
    results = search_service.search_sections_with_expanded_context(
        query=request.data.get('query'),
        source_table='rvt_guide',
        limit=request.data.get('limit', 5),
        threshold=request.data.get('threshold', 0.7),
        context_window=request.data.get('context_window', 1),
        context_mode=request.data.get('context_mode', 'adjacent')
    )
    
    tracker.end('db_query')
    tracker.record('db_query_count', 2)  # 向量搜尋 + 上下文查詢
    
    return self._format_results_v2(results)

def _assign_ab_group(self, user_id):
    """
    A/B 分組邏輯
    
    策略: 根據 user_id 的奇偶數分組（穩定分組）
    - 偶數 user_id → A 組 (V1)
    - 奇數 user_id → B 組 (V2)
    """
    if user_id % 2 == 0:
        return ('A', 'v1')
    else:
        return ('B', 'v2')
```

#### 5.2 獨立 API 端點（備選）

如果希望兩個版本完全獨立：

```python
# V1: 現有方法（不變）
@action(detail=False, methods=['post'])
def search_sections(self, request):
    """現有的搜尋 API（V1 基準）"""
    # ... 現有實作不變

# V2: 新方法
@action(detail=False, methods=['post'])
def search_sections_with_context(self, request):
    """新的上下文搜尋 API（V2 實驗）"""
    # ... 新實作

# 比較端點
@action(detail=False, methods=['post'])
def compare_search_versions(self, request):
    """
    同時執行 V1 和 V2，返回兩者結果供比較
    
    POST /api/rvt-guides/compare_search_versions/
    """
    results_v1 = self._search_v1(request)
    results_v2 = self._search_v2(request)
    
    return Response({
        'v1_results': results_v1,
        'v2_results': results_v2,
        'comparison': self._generate_comparison(results_v1, results_v2)
    })
```

---

## 6. 前端 A/B 測試介面

### 🎨 測試頁面設計

#### 6.1 並排比較模式

```jsx
// frontend/src/pages/SearchComparisonPage.jsx

import React, { useState } from 'react';
import { Row, Col, Card, Button, Form, Input, Slider, Space, Typography, Tag, Statistic } from 'antd';
import { ThunderboltOutlined, ExperimentOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;

const SearchComparisonPage = () => {
  const [searchParams, setSearchParams] = useState({
    query: '',
    limit: 5,
    threshold: 0.7,
    context_window: 2
  });
  
  const [resultsV1, setResultsV1] = useState(null);
  const [resultsV2, setResultsV2] = useState(null);
  const [performanceV1, setPerformanceV1] = useState(null);
  const [performanceV2, setPerformanceV2] = useState(null);
  
  const handleCompareSearch = async () => {
    // 同時發送兩個請求
    const [responseV1, responseV2] = await Promise.all([
      api.post('/api/rvt-guides/search_sections_smart/', {
        ...searchParams,
        search_version: 'v1',
        enable_tracking: true
      }),
      api.post('/api/rvt-guides/search_sections_smart/', {
        ...searchParams,
        search_version: 'v2',
        enable_tracking: true
      })
    ]);
    
    setResultsV1(responseV1.data);
    setResultsV2(responseV2.data);
    setPerformanceV1(responseV1.data.performance);
    setPerformanceV2(responseV2.data.performance);
  };
  
  return (
    <div style={{ padding: 24 }}>
      <Title level={2}>
        <ExperimentOutlined /> A/B 測試：搜尋方法比較
      </Title>
      
      {/* 搜尋表單 */}
      <Card title="搜尋參數" style={{ marginBottom: 24 }}>
        <Form layout="vertical">
          <Form.Item label="搜尋查詢">
            <Input.TextArea
              value={searchParams.query}
              onChange={(e) => setSearchParams({...searchParams, query: e.target.value})}
              placeholder="例如: 軟體配置、測試流程..."
              rows={2}
            />
          </Form.Item>
          
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item label="結果數量">
                <Slider
                  min={1} max={10}
                  value={searchParams.limit}
                  onChange={(val) => setSearchParams({...searchParams, limit: val})}
                />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="相似度閾值">
                <Slider
                  min={0.5} max={1.0} step={0.05}
                  value={searchParams.threshold}
                  onChange={(val) => setSearchParams({...searchParams, threshold: val})}
                />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="上下文視窗 (V2)">
                <Slider
                  min={0} max={5}
                  value={searchParams.context_window}
                  onChange={(val) => setSearchParams({...searchParams, context_window: val})}
                />
              </Form.Item>
            </Col>
          </Row>
          
          <Button
            type="primary"
            size="large"
            icon={<ThunderboltOutlined />}
            onClick={handleCompareSearch}
            block
          >
            執行比較搜尋
          </Button>
        </Form>
      </Card>
      
      {/* 效能比較 */}
      {performanceV1 && performanceV2 && (
        <Card title="效能比較" style={{ marginBottom: 24 }}>
          <Row gutter={16}>
            <Col span={12}>
              <Card type="inner" title="V1: 現有方法">
                <Space direction="vertical" size="large" style={{ width: '100%' }}>
                  <Statistic
                    title="執行時間"
                    value={resultsV1.execution_time}
                    suffix="ms"
                    valueStyle={{ color: '#3f8600' }}
                  />
                  <Statistic
                    title="資料庫查詢"
                    value={performanceV1.db_query_count}
                    suffix="次"
                  />
                  <Statistic
                    title="結果數量"
                    value={performanceV1.result_count}
                  />
                  <Statistic
                    title="平均相似度"
                    value={(performanceV1.avg_similarity * 100).toFixed(1)}
                    suffix="%"
                  />
                </Space>
              </Card>
            </Col>
            
            <Col span={12}>
              <Card type="inner" title="V2: 上下文視窗">
                <Space direction="vertical" size="large" style={{ width: '100%' }}>
                  <Statistic
                    title="執行時間"
                    value={resultsV2.execution_time}
                    suffix="ms"
                    valueStyle={{ color: performanceV2.execution_time > performanceV1.execution_time ? '#cf1322' : '#3f8600' }}
                  />
                  <Statistic
                    title="資料庫查詢"
                    value={performanceV2.db_query_count}
                    suffix="次"
                  />
                  <Statistic
                    title="結果數量"
                    value={performanceV2.result_count}
                  />
                  <Statistic
                    title="平均相似度"
                    value={(performanceV2.avg_similarity * 100).toFixed(1)}
                    suffix="%"
                  />
                </Space>
              </Card>
            </Col>
          </Row>
        </Card>
      )}
      
      {/* 結果比較 */}
      {resultsV1 && resultsV2 && (
        <Row gutter={16}>
          <Col span={12}>
            <Card title={<><Tag color="blue">V1</Tag> 現有方法結果</>}>
              {resultsV1.results.map((result, idx) => (
                <ResultCard key={idx} result={result} version="v1" />
              ))}
            </Card>
          </Col>
          
          <Col span={12}>
            <Card title={<><Tag color="green">V2</Tag> 上下文視窗結果</>}>
              {resultsV2.results.map((result, idx) => (
                <ResultCard key={idx} result={result} version="v2" />
              ))}
            </Card>
          </Col>
        </Row>
      )}
      
      {/* 用戶反饋表單 */}
      {resultsV1 && resultsV2 && (
        <Card title="您的反饋" style={{ marginTop: 24 }}>
          <FeedbackForm
            trackingIdV1={resultsV1.tracking_id}
            trackingIdV2={resultsV2.tracking_id}
          />
        </Card>
      )}
    </div>
  );
};

export default SearchComparisonPage;
```

#### 6.2 用戶反饋組件

```jsx
// frontend/src/components/FeedbackForm.jsx

import React, { useState } from 'react';
import { Form, Rate, Input, Button, Radio, Space, message } from 'antd';

const FeedbackForm = ({ trackingIdV1, trackingIdV2 }) => {
  const [form] = Form.useForm();
  
  const handleSubmit = async (values) => {
    try {
      // 提交 V1 反饋
      await api.post('/api/search-feedback/', {
        search_log_id: trackingIdV1,
        search_version: 'v1',
        ...values.v1
      });
      
      // 提交 V2 反饋
      await api.post('/api/search-feedback/', {
        search_log_id: trackingIdV2,
        search_version: 'v2',
        ...values.v2
      });
      
      message.success('感謝您的反饋！');
      form.resetFields();
    } catch (error) {
      message.error('提交失敗，請稍後再試');
    }
  };
  
  return (
    <Form form={form} layout="vertical" onFinish={handleSubmit}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* V1 反饋 */}
        <div>
          <h3>V1 (現有方法) 評價</h3>
          <Form.Item label="相關性" name={['v1', 'relevance_score']}>
            <Rate />
          </Form.Item>
          <Form.Item label="完整性" name={['v1', 'completeness_score']}>
            <Rate />
          </Form.Item>
          <Form.Item label="理解度" name={['v1', 'understanding_score']}>
            <Rate />
          </Form.Item>
          <Form.Item label="整體滿意度" name={['v1', 'overall_satisfaction']}>
            <Rate />
          </Form.Item>
        </div>
        
        {/* V2 反饋 */}
        <div>
          <h3>V2 (上下文視窗) 評價</h3>
          <Form.Item label="相關性" name={['v2', 'relevance_score']}>
            <Rate />
          </Form.Item>
          <Form.Item label="完整性" name={['v2', 'completeness_score']}>
            <Rate />
          </Form.Item>
          <Form.Item label="理解度" name={['v2', 'understanding_score']}>
            <Rate />
          </Form.Item>
          <Form.Item label="整體滿意度" name={['v2', 'overall_satisfaction']}>
            <Rate />
          </Form.Item>
        </div>
        
        {/* 比較性問題 */}
        <Form.Item label="您更喜歡哪個版本？" name="preferred_version">
          <Radio.Group>
            <Radio value="v1">V1 (現有方法)</Radio>
            <Radio value="v2">V2 (上下文視窗)</Radio>
            <Radio value="neither">都不喜歡</Radio>
          </Radio.Group>
        </Form.Item>
        
        {/* 開放式評論 */}
        <Form.Item label="其他意見" name="comment">
          <Input.TextArea rows={3} placeholder="請分享您的想法..." />
        </Form.Item>
        
        <Button type="primary" htmlType="submit" size="large" block>
          提交反饋
        </Button>
      </Space>
    </Form>
  );
};

export default FeedbackForm;
```

---

## 7. 評估指標定義

### 📊 成功標準

#### 7.1 效能標準（必須滿足）

| 指標 | V1 (基準) | V2 (目標) | 可接受範圍 |
|------|----------|----------|-----------|
| **平均回應時間** | 50ms | < 100ms | V2 ≤ V1 × 2 |
| **P95 回應時間** | 80ms | < 150ms | V2 ≤ V1 × 2 |
| **資料庫查詢** | 1-2 次 | 2-4 次 | V2 ≤ V1 + 2 |

**判定**:
- ✅ **通過**: 所有指標都在可接受範圍內
- ⚠️ **需優化**: 超出範圍但 < 2.5 倍
- ❌ **不通過**: 超出 2.5 倍

#### 7.2 用戶體驗標準（核心目標）

| 指標 | V1 (基準) | V2 (目標) | 成功標準 |
|------|----------|----------|---------|
| **完整性評分** | 假設 3.0 | > 4.0 | V2 > V1 + 0.5 |
| **理解度評分** | 假設 3.2 | > 4.0 | V2 > V1 + 0.5 |
| **整體滿意度** | 假設 3.5 | > 4.2 | V2 > V1 + 0.5 |
| **用戶偏好** | - | > 60% | 超過 60% 用戶偏好 V2 |

**判定**:
- ✅ **顯著改善**: V2 在 3 項以上指標超出成功標準
- ⚠️ **輕微改善**: V2 在 2 項指標超出成功標準
- ❌ **無顯著差異**: V2 改善不明顯或更差

#### 7.3 業務指標

| 指標 | V1 (基準) | V2 (目標) | 成功標準 |
|------|----------|----------|---------|
| **重新搜尋率** | 假設 30% | < 20% | 降低 > 10% |
| **點擊查看完整文檔率** | 假設 50% | < 35% | 降低 > 15% |
| **標記有幫助率** | 假設 40% | > 55% | 提升 > 15% |

---

## 8. 數據分析計畫

### 📈 分析流程

#### 8.1 數據收集期（建議 2-4 週）

```sql
-- 每日數據摘要查詢
SELECT 
    search_version,
    DATE(created_at) as date,
    COUNT(*) as total_searches,
    AVG(execution_time_ms) as avg_time,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY execution_time_ms) as p95_time,
    AVG(avg_similarity) as avg_similarity_score,
    COUNT(DISTINCT user_id) as unique_users
FROM search_ab_test_logs
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY search_version, DATE(created_at)
ORDER BY date DESC, search_version;
```

#### 8.2 效能對比分析

```sql
-- V1 vs V2 效能對比
WITH v1_stats AS (
    SELECT 
        AVG(execution_time_ms) as avg_time,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY execution_time_ms) as p50_time,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY execution_time_ms) as p95_time,
        PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY execution_time_ms) as p99_time,
        AVG(db_query_count) as avg_queries,
        AVG(memory_usage_mb) as avg_memory
    FROM search_ab_test_logs
    WHERE search_version = 'v1'
),
v2_stats AS (
    SELECT 
        AVG(execution_time_ms) as avg_time,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY execution_time_ms) as p50_time,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY execution_time_ms) as p95_time,
        PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY execution_time_ms) as p99_time,
        AVG(db_query_count) as avg_queries,
        AVG(memory_usage_mb) as avg_memory,
        AVG(context_sections_count) as avg_context_sections,
        AVG(total_context_words) as avg_context_words
    FROM search_ab_test_logs
    WHERE search_version = 'v2'
)
SELECT 
    'V1' as version,
    v1.avg_time, v1.p50_time, v1.p95_time, v1.p99_time,
    v1.avg_queries, v1.avg_memory,
    NULL as avg_context_sections,
    NULL as avg_context_words
FROM v1_stats v1
UNION ALL
SELECT 
    'V2' as version,
    v2.avg_time, v2.p50_time, v2.p95_time, v2.p99_time,
    v2.avg_queries, v2.avg_memory,
    v2.avg_context_sections,
    v2.avg_context_words
FROM v2_stats v2;
```

#### 8.3 用戶滿意度分析

```sql
-- V1 vs V2 用戶滿意度對比
SELECT 
    search_version,
    COUNT(*) as feedback_count,
    AVG(relevance_score) as avg_relevance,
    AVG(completeness_score) as avg_completeness,
    AVG(understanding_score) as avg_understanding,
    AVG(need_more_info_score) as avg_need_more_info,
    AVG(overall_satisfaction) as avg_satisfaction,
    SUM(CASE WHEN marked_helpful THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 as helpful_rate,
    SUM(CASE WHEN clicked_view_full THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 as view_full_rate
FROM search_user_feedback
GROUP BY search_version;
```

#### 8.4 統計顯著性檢驗

使用 Python 進行 t-test：

```python
# backend/scripts/analyze_ab_test.py

import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt

# 讀取資料
v1_data = pd.read_sql("""
    SELECT execution_time_ms, avg_similarity 
    FROM search_ab_test_logs 
    WHERE search_version = 'v1'
""", conn)

v2_data = pd.read_sql("""
    SELECT execution_time_ms, avg_similarity, context_sections_count
    FROM search_ab_test_logs 
    WHERE search_version = 'v2'
""", conn)

# t-test: 執行時間比較
t_stat, p_value = stats.ttest_ind(v1_data['execution_time_ms'], v2_data['execution_time_ms'])
print(f"執行時間 t-test: t={t_stat:.4f}, p={p_value:.4f}")
if p_value < 0.05:
    print("✅ 差異顯著 (p < 0.05)")
else:
    print("⚠️ 差異不顯著")

# 繪製分佈圖
plt.figure(figsize=(12, 5))
plt.subplot(1, 2, 1)
plt.hist(v1_data['execution_time_ms'], bins=30, alpha=0.5, label='V1')
plt.hist(v2_data['execution_time_ms'], bins=30, alpha=0.5, label='V2')
plt.xlabel('執行時間 (ms)')
plt.ylabel('頻率')
plt.title('執行時間分佈比較')
plt.legend()

plt.subplot(1, 2, 2)
plt.boxplot([v1_data['execution_time_ms'], v2_data['execution_time_ms']], 
            labels=['V1', 'V2'])
plt.ylabel('執行時間 (ms)')
plt.title('執行時間箱型圖比較')

plt.tight_layout()
plt.savefig('ab_test_performance_comparison.png')
print("圖表已儲存: ab_test_performance_comparison.png")
```

---

## 9. 決策矩陣

### 🎯 決策樹

```
                        開始 A/B 測試
                              │
                              ▼
                ┌─────────────────────────┐
                │   收集 2-4 週資料       │
                │   (至少 100+ 樣本)      │
                └───────────┬─────────────┘
                            │
                            ▼
                ┌─────────────────────────┐
                │   效能指標檢查           │
                │   V2 ≤ V1 × 2 ?         │
                └───────────┬─────────────┘
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
            ✅ 通過                  ❌ 不通過
                │                       │
                ▼                       ▼
    ┌───────────────────┐   ┌─────────────────────┐
    │ 用戶體驗檢查      │   │ 決策: 效能優化       │
    │ V2 > V1 + 0.5 ?  │   │ - 優化 V2 效能       │
    └────────┬──────────┘   │ - 或放棄 V2         │
             │              └─────────────────────┘
    ┌────────┴────────┐
    ▼                 ▼
✅ 3+ 指標改善    ⚠️ 1-2 指標改善
    │                 │
    ▼                 ▼
┌─────────┐     ┌──────────┐
│ 決策:    │     │ 決策:     │
│ 全面採用 │     │ 部分採用  │
│ V2      │     │ 或繼續測試│
└─────────┘     └──────────┘
```

### 📋 決策矩陣表

| 效能 | 用戶體驗 | 用戶偏好 | 建議決策 | 實施方式 |
|------|---------|---------|---------|---------|
| ✅ 通過 | ✅ 顯著改善 (3+ 指標) | ✅ > 70% | **全面替換** | 廢棄 V1，V2 成為預設 |
| ✅ 通過 | ✅ 顯著改善 (3+ 指標) | ⚠️ 60-70% | **預設 V2，保留選項** | V2 預設，提供 V1 選項 |
| ✅ 通過 | ⚠️ 輕微改善 (2 指標) | ✅ > 60% | **並行提供** | 兩者並存，用戶選擇 |
| ✅ 通過 | ❌ 無差異 | ⚠️ < 60% | **繼續優化 V2** | 改善 UX，繼續測試 |
| ⚠️ 需優化 | ✅ 顯著改善 | ✅ > 70% | **優化後採用** | 優化效能後再評估 |
| ❌ 不通過 | * | * | **放棄 V2** | 保留 V1，研究其他方案 |

---

## 10. 實施時程

### 📅 完整時間表

#### Phase 0: 準備階段（3-5 天）

**Day 1-2: 資料庫設計**
- ✅ 創建 A/B 測試日誌表
- ✅ 創建用戶反饋表
- ✅ 創建效能監控表
- ✅ 建立必要索引

**Day 3-4: API 開發**
- ✅ 實作 `search_sections_smart()` API
- ✅ 實作 A/B 分組邏輯
- ✅ 實作日誌記錄功能
- ✅ 實作反饋提交 API

**Day 5: 前端開發**
- ✅ 創建比較頁面組件
- ✅ 創建反饋表單組件
- ✅ 整合 API

#### Phase 1: 實作 V2 功能（5-7 天）

**參考**: `/docs/development/context-window-implementation-plan.md`

- ✅ 實作 `_get_adjacent_sections()`
- ✅ 實作 `search_sections_with_expanded_context()`
- ✅ 單元測試和整合測試
- ✅ 效能測試

#### Phase 2: 小規模測試（1 週）

**Week 1: 內部測試**
- 🧪 開發團隊測試（5-10 人）
- 🐛 Bug 修復
- 📊 初步數據分析

#### Phase 3: A/B 測試期（2-4 週）

**Week 1-2: 50% 流量分配**
- 📊 每日監控效能指標
- 📝 收集用戶反饋
- 🔧 小幅調整優化

**Week 3-4: 100% 流量（如果穩定）**
- 📊 持續數據收集
- 📈 週報分析
- 💬 用戶訪談（可選）

#### Phase 4: 數據分析與決策（1 週）

**Day 1-3: 數據分析**
- 📊 統計分析（t-test, Chi-square）
- 📈 可視化報告
- 📝 撰寫分析報告

**Day 4-5: 團隊決策**
- 🎯 Review 分析結果
- 💬 團隊討論
- ✅ 決定最終方案

#### Phase 5: 實施決策（1-2 週）

根據決策矩陣結果：

**如果: 全面替換為 V2**
- 📝 更新文檔
- 🗑️ 標記 V1 為 deprecated
- 🚀 逐步移除 V1

**如果: 並行提供**
- 🎨 優化切換 UI
- 📝 撰寫用戶指南
- 🚀 發布功能說明

**如果: 繼續優化**
- 🔧 根據反饋改進 V2
- 🔄 進行第二輪測試

---

## 📊 範例分析報告模板

### A/B 測試結果報告

**測試期間**: 2025-11-10 ~ 2025-12-10 (30 天)  
**參與用戶**: 150 人  
**總搜尋次數**: 3,500 次 (V1: 1,750, V2: 1,750)

#### 1. 效能指標對比

| 指標 | V1 | V2 | 差異 | 判定 |
|------|----|----|------|------|
| 平均回應時間 | 45ms | 82ms | +82% | ✅ 通過 (< 2x) |
| P95 回應時間 | 75ms | 135ms | +80% | ✅ 通過 (< 2x) |
| P99 回應時間 | 110ms | 195ms | +77% | ✅ 通過 (< 2x) |
| 資料庫查詢 | 1.2 次 | 2.8 次 | +133% | ✅ 通過 (< +2) |
| 記憶體使用 | 8MB | 23MB | +188% | ⚠️ 需關注 |

**結論**: ✅ 效能指標全部通過，增加的開銷在可接受範圍內。

#### 2. 用戶體驗指標對比

| 指標 | V1 | V2 | 差異 | 判定 |
|------|----|----|------|------|
| 相關性評分 | 3.8 | 3.9 | +0.1 | ⚠️ 輕微改善 |
| **完整性評分** | 3.2 | **4.5** | **+1.3** | ✅ **顯著改善** |
| **理解度評分** | 3.4 | **4.3** | **+0.9** | ✅ **顯著改善** |
| 需要更多資訊 | 2.8 | 4.1 | +1.3 | ✅ 降低需求 |
| **整體滿意度** | 3.6 | **4.4** | **+0.8** | ✅ **顯著改善** |

**結論**: ✅ 用戶體驗顯著改善，3 項核心指標超過 +0.5 成功標準。

#### 3. 用戶偏好

- **偏好 V2**: 78% (117/150)
- **偏好 V1**: 15% (23/150)
- **無偏好**: 7% (10/150)

**結論**: ✅ 超過 70% 用戶偏好 V2。

#### 4. 最終建議

根據決策矩陣：

✅ **效能**: 通過  
✅ **用戶體驗**: 顯著改善 (3+ 指標)  
✅ **用戶偏好**: > 70%

**建議決策**: **全面替換為 V2**

**實施計畫**:
1. 將 V2 設為預設方法（2 週內）
2. 保留 V1 作為後備選項（3 個月）
3. 監控生產環境表現（持續）
4. 3 個月後完全移除 V1

---

## 🎯 最終採用方案：簡化版（Toggle 切換）

### ✅ 決定採用：樣式 1 - 頂部 Toggle Bar

**選擇理由**：
1. ✅ **實作簡單** - 1 天即可完成
2. ✅ **用戶友好** - 一目了然，易於切換
3. ✅ **快速驗證** - 立即可以看到差異
4. ✅ **低風險** - 不影響現有功能

### 📋 簡化方案特點

相比完整 A/B 測試方案：
- 🎯 **核心功能**: 保留 V1/V2 切換和基本統計
- ⚡ **快速上線**: 1 天開發 + 測試
- 📊 **輕量數據**: 僅記錄使用次數（可選）
- 🚀 **漸進式**: 先簡單驗證，再決定是否需要完整測試

### � 實作計畫（1-2 天）

#### Day 1: 核心功能（6-8 小時）
1. ✅ **後端 API 修改** (2 小時)
   - 修改 `search_sections` 支援 `version` 參數
   - V1/V2 邏輯分支

2. ✅ **前端 Hook 修改** (1 小時)
   - `useRvtChat` 添加版本狀態
   - `toggleVersion` 函數

3. ✅ **前端 UI 實作** (2 小時)
   - 頂部 Toggle Bar 組件
   - 版本標記顯示

4. ✅ **測試** (1-2 小時)
   - 功能測試
   - 切換測試
   - 多 Assistant 測試

#### Day 2: 優化和部署（可選）
1. ⭐ **UI 優化** (1 小時)
   - 美化 Toggle Bar
   - 添加 Tooltip 提示

2. ⭐ **使用統計** (1 小時，可選)
   - 創建統計表
   - 記錄版本使用次數

3. 📝 **文檔更新** (1 小時)
   - 用戶指南
   - 開發文檔

### 🎨 UI 設計規格（樣式 1）

```
┌────────────────────────────────────────────────┐
│ RVT Assistant      🔄 [V1 基礎] ⚫ [V2 增強]   │ ← 右上角固定
├────────────────────────────────────────────────┤
│                                                │
│  [搜尋輸入框]                                  │
│                                                │
│  ┌──────────────────────────────────────────┐ │
│  │ 🤖 Assistant (V2: 上下文增強)            │ │
│  │ 主要結果: ...                            │ │
│  │ ⬆️ 前置段落: ...                         │ │
│  │ ⬇️ 後續段落: ...                         │ │
│  └──────────────────────────────────────────┘ │
└────────────────────────────────────────────────┘
```

### � 觀察期計畫（1-2 週）

**觀察指標**（輕量級）：
1. 📈 **使用統計**: V1 vs V2 使用次數
2. 💬 **非正式反饋**: 團隊成員使用感受
3. 🐛 **Bug 回報**: 是否有異常問題

**決策點**（2 週後）：
- ✅ **V2 明顯更好** → 設為預設，考慮移除 V1
- ⚠️ **不確定** → 進行完整 A/B 測試（參考本文檔其他章節）
- ❌ **V2 無優勢** → 放棄 V2，保留 V1

### 🎯 下一步行動

1. ✅ **開始實作** - 按照 Day 1 計畫執行
2. 📝 **建立分支** - `feature/search-version-toggle`
3. 🧪 **內部測試** - 團隊試用 1-2 週
4. 🎯 **收集反饋** - 決定是否需要完整 A/B 測試

---

**文檔版本**: v2.0（簡化版）  
**更新日期**: 2025-11-09  
**採用方案**: 樣式 1 - 頂部 Toggle Bar  
**預計完成**: 1-2 天  
**決策時間點**: 試用 1-2 週後

---

## 附錄：完整 A/B 測試方案

如果簡化版試用後需要更嚴謹的評估，可參考本文檔前面章節：
- 第 4 節：數據收集方案（3 個統計表）
- 第 6 節：並排比較介面
- 第 7 節：評估指標定義
- 第 8 節：數據分析計畫
- 第 9 節：決策矩陣

**聯絡方式**: 透過專案 issue 追蹤進度
