# 🏆 搜尋演算法跑分系統設計文檔

**日期**: 2025-11-21  
**狀態**: 📋 規劃中  
**目標**: 建立一個可量化、可追蹤的搜尋演算法評分系統

---

## 🎯 系統目標

### 核心功能
1. **版本管理**: 追蹤不同版本的搜尋演算法
2. **評分廣度**: 支援多種評分維度（精準度、召回率、響應時間等）
3. **題庫管理**: 建立標準測試題目與預期答案
4. **自動評分**: 自動執行測試並計算得分
5. **結果對比**: 視覺化呈現不同版本的效能差異
6. **知識庫整合**: 使用 Protocol Assistant 知識庫作為測試資料源

---

## 📊 系統架構設計

### 1. 資料庫設計

#### 1.1 搜尋演算法版本表 (`search_algorithm_version`)
```sql
CREATE TABLE search_algorithm_version (
    id SERIAL PRIMARY KEY,
    version_name VARCHAR(100) NOT NULL,           -- 版本名稱 (如 "v2.1-hybrid-search")
    version_code VARCHAR(50) NOT NULL UNIQUE,     -- 版本代碼 (如 "v2.1.0")
    description TEXT,                             -- 版本說明
    algorithm_type VARCHAR(50),                   -- 演算法類型 (hybrid, vector_only, keyword_only)
    
    -- 演算法參數 (JSON 格式)
    parameters JSONB,                             -- 如: {"vector_weight": 0.7, "keyword_weight": 0.3}
    
    -- 版本狀態
    is_active BOOLEAN DEFAULT TRUE,               -- 是否啟用
    is_baseline BOOLEAN DEFAULT FALSE,            -- 是否為基準版本
    
    -- 時間戳記
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by_id INTEGER REFERENCES auth_user(id),
    
    -- 效能指標快照 (自動更新)
    avg_precision DECIMAL(5,4),                   -- 平均精準度
    avg_recall DECIMAL(5,4),                      -- 平均召回率
    avg_response_time DECIMAL(10,2),              -- 平均響應時間 (ms)
    total_tests INTEGER DEFAULT 0,                -- 總測試次數
    
    CONSTRAINT unique_version_code UNIQUE (version_code)
);

-- 索引
CREATE INDEX idx_search_version_active ON search_algorithm_version(is_active);
CREATE INDEX idx_search_version_created ON search_algorithm_version(created_at DESC);
```

**範例資料**:
```json
{
  "version_name": "Protocol Assistant v2.1 - Hybrid Search",
  "version_code": "v2.1.0",
  "algorithm_type": "hybrid",
  "parameters": {
    "vector_weight": 0.7,
    "keyword_weight": 0.3,
    "vector_threshold": 0.65,
    "keyword_threshold": 0.3,
    "top_k": 5,
    "use_reranking": true
  }
}
```

---

#### 1.2 評分維度表 (`benchmark_metric`)
```sql
CREATE TABLE benchmark_metric (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL UNIQUE,     -- 評分項目名稱
    metric_key VARCHAR(50) NOT NULL UNIQUE,       -- 評分項目鍵值 (用於程式碼)
    description TEXT,                              -- 說明
    metric_type VARCHAR(30),                       -- 類型 (precision, recall, speed, quality)
    
    -- 計算方式
    calculation_method TEXT,                       -- 計算邏輯說明
    max_score DECIMAL(5,2) DEFAULT 100.00,        -- 最高分數
    min_score DECIMAL(5,2) DEFAULT 0.00,          -- 最低分數
    
    -- 權重配置
    weight DECIMAL(3,2) DEFAULT 1.00,             -- 在總分中的權重
    
    -- 狀態
    is_active BOOLEAN DEFAULT TRUE,                -- 是否啟用
    display_order INTEGER DEFAULT 0,               -- 顯示順序
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_benchmark_metric_active ON benchmark_metric(is_active, display_order);
```

**預設評分維度**:
```python
METRICS = [
    {
        "metric_name": "精準度 (Precision)",
        "metric_key": "precision",
        "metric_type": "precision",
        "description": "回傳結果中正確答案的比例",
        "calculation_method": "TP / (TP + FP)",
        "weight": 0.35
    },
    {
        "metric_name": "召回率 (Recall)",
        "metric_key": "recall",
        "metric_type": "recall",
        "description": "正確答案被找回的比例",
        "calculation_method": "TP / (TP + FN)",
        "weight": 0.30
    },
    {
        "metric_name": "F1 分數 (F1-Score)",
        "metric_key": "f1_score",
        "metric_type": "quality",
        "description": "精準度和召回率的調和平均數",
        "calculation_method": "2 * (Precision * Recall) / (Precision + Recall)",
        "weight": 0.20
    },
    {
        "metric_name": "平均響應時間 (Avg Response Time)",
        "metric_key": "avg_response_time",
        "metric_type": "speed",
        "description": "搜尋查詢的平均處理時間 (ms)",
        "calculation_method": "sum(response_times) / count",
        "weight": 0.10
    },
    {
        "metric_name": "NDCG@5 (Normalized Discounted Cumulative Gain)",
        "metric_key": "ndcg_at_5",
        "metric_type": "quality",
        "description": "考慮排序的搜尋品質指標",
        "calculation_method": "DCG / IDCG (前5個結果)",
        "weight": 0.05
    }
]
```

---

#### 1.3 測試題庫表 (`benchmark_test_case`)
```sql
CREATE TABLE benchmark_test_case (
    id SERIAL PRIMARY KEY,
    
    -- 題目資訊
    question TEXT NOT NULL,                        -- 測試問題
    question_type VARCHAR(50),                     -- 問題類型 (fact, procedure, comparison, etc.)
    difficulty_level VARCHAR(20),                  -- 難度 (easy, medium, hard)
    
    -- 預期答案
    expected_document_ids INTEGER[],               -- 預期的文檔 ID 列表 (來自 protocol_guide)
    expected_keywords TEXT[],                      -- 預期包含的關鍵字
    expected_answer_summary TEXT,                  -- 預期答案摘要 (人工標註)
    
    -- 判斷標準
    min_required_matches INTEGER DEFAULT 1,        -- 至少需要匹配的文檔數量
    acceptable_document_ids INTEGER[],             -- 可接受的文檔 ID (不完全匹配但可接受)
    
    -- 元數據
    category VARCHAR(100),                         -- 類別 (如 "USB測試", "PCIe測試")
    tags TEXT[],                                   -- 標籤
    source VARCHAR(100),                           -- 來源 (如 "Protocol Assistant KB")
    
    -- 狀態
    is_active BOOLEAN DEFAULT TRUE,                -- 是否啟用
    is_validated BOOLEAN DEFAULT FALSE,            -- 是否已驗證
    
    -- 統計
    total_runs INTEGER DEFAULT 0,                  -- 總執行次數
    avg_score DECIMAL(5,2),                        -- 平均得分
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by_id INTEGER REFERENCES auth_user(id),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_test_case_active ON benchmark_test_case(is_active);
CREATE INDEX idx_test_case_category ON benchmark_test_case(category);
CREATE INDEX idx_test_case_difficulty ON benchmark_test_case(difficulty_level);
```

**範例測試案例**:
```json
{
  "question": "如何測試 USB 3.0 的傳輸速度？",
  "question_type": "procedure",
  "difficulty_level": "medium",
  "expected_document_ids": [45, 67, 89],
  "expected_keywords": ["USB 3.0", "傳輸速度", "CrystalDiskMark", "測試方法"],
  "expected_answer_summary": "使用 CrystalDiskMark 工具測試 USB 3.0 裝置的讀寫速度...",
  "min_required_matches": 2,
  "acceptable_document_ids": [45, 67, 89, 90, 112],
  "category": "USB測試",
  "tags": ["USB", "效能測試", "CrystalDiskMark"],
  "source": "Protocol Assistant KB"
}
```

---

#### 1.4 測試執行記錄表 (`benchmark_test_run`)
```sql
CREATE TABLE benchmark_test_run (
    id SERIAL PRIMARY KEY,
    
    -- 關聯
    version_id INTEGER REFERENCES search_algorithm_version(id) ON DELETE CASCADE,
    
    -- 執行資訊
    run_name VARCHAR(200),                         -- 執行名稱
    run_type VARCHAR(50) DEFAULT 'manual',         -- 執行類型 (manual, scheduled, ci_cd)
    
    -- 測試範圍
    total_test_cases INTEGER NOT NULL,             -- 總測試案例數
    completed_test_cases INTEGER DEFAULT 0,        -- 已完成數量
    
    -- 執行狀態
    status VARCHAR(30) DEFAULT 'pending',          -- pending, running, completed, failed
    
    -- 結果摘要
    overall_score DECIMAL(5,2),                    -- 總分
    avg_precision DECIMAL(5,4),                    -- 平均精準度
    avg_recall DECIMAL(5,4),                       -- 平均召回率
    avg_f1_score DECIMAL(5,4),                     -- 平均 F1 分數
    avg_response_time DECIMAL(10,2),               -- 平均響應時間 (ms)
    
    -- 時間追蹤
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds INTEGER,                      -- 執行總時間 (秒)
    
    -- 元數據
    triggered_by_id INTEGER REFERENCES auth_user(id),
    environment VARCHAR(50),                       -- 執行環境 (development, staging, production)
    git_commit_hash VARCHAR(40),                   -- Git commit hash (可選)
    notes TEXT,                                    -- 備註
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_test_run_version ON benchmark_test_run(version_id);
CREATE INDEX idx_test_run_status ON benchmark_test_run(status);
CREATE INDEX idx_test_run_created ON benchmark_test_run(created_at DESC);
```

---

#### 1.5 測試結果詳細表 (`benchmark_test_result`)
```sql
CREATE TABLE benchmark_test_result (
    id SERIAL PRIMARY KEY,
    
    -- 關聯
    test_run_id INTEGER REFERENCES benchmark_test_run(id) ON DELETE CASCADE,
    test_case_id INTEGER REFERENCES benchmark_test_case(id) ON DELETE CASCADE,
    
    -- 搜尋結果
    search_query TEXT,                             -- 實際查詢文本
    returned_document_ids INTEGER[],               -- 實際返回的文檔 ID
    returned_document_scores DECIMAL(5,4)[],       -- 對應的相似度分數
    
    -- 評分結果
    precision_score DECIMAL(5,4),                  -- 精準度分數
    recall_score DECIMAL(5,4),                     -- 召回率分數
    f1_score DECIMAL(5,4),                         -- F1 分數
    ndcg_score DECIMAL(5,4),                       -- NDCG 分數
    response_time DECIMAL(10,2),                   -- 響應時間 (ms)
    
    -- 匹配分析
    true_positives INTEGER,                        -- 正確匹配數
    false_positives INTEGER,                       -- 錯誤匹配數
    false_negatives INTEGER,                       -- 漏掉的正確答案數
    
    -- 判斷
    is_passed BOOLEAN,                             -- 是否通過
    pass_reason TEXT,                              -- 通過/失敗原因
    
    -- 詳細資料 (JSON)
    detailed_results JSONB,                        -- 完整搜尋結果和分析
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_test_result_run ON benchmark_test_result(test_run_id);
CREATE INDEX idx_test_result_case ON benchmark_test_result(test_case_id);
CREATE INDEX idx_test_result_passed ON benchmark_test_result(is_passed);
```

---

### 2. 評分計算邏輯

#### 2.1 精準度 (Precision)
```python
def calculate_precision(returned_ids: list, expected_ids: list) -> float:
    """
    精準度 = 返回結果中正確的數量 / 返回結果總數
    
    範例:
        returned_ids = [1, 2, 3, 4, 5]
        expected_ids = [2, 4, 6, 8]
        
        正確的: [2, 4] = 2 個
        precision = 2 / 5 = 0.4
    """
    if not returned_ids:
        return 0.0
    
    true_positives = len(set(returned_ids) & set(expected_ids))
    precision = true_positives / len(returned_ids)
    
    return round(precision, 4)
```

#### 2.2 召回率 (Recall)
```python
def calculate_recall(returned_ids: list, expected_ids: list) -> float:
    """
    召回率 = 返回結果中正確的數量 / 所有正確答案的數量
    
    範例:
        returned_ids = [1, 2, 3, 4, 5]
        expected_ids = [2, 4, 6, 8]
        
        找到的正確答案: [2, 4] = 2 個
        所有正確答案: [2, 4, 6, 8] = 4 個
        recall = 2 / 4 = 0.5
    """
    if not expected_ids:
        return 1.0  # 如果沒有預期答案，視為完全召回
    
    true_positives = len(set(returned_ids) & set(expected_ids))
    recall = true_positives / len(expected_ids)
    
    return round(recall, 4)
```

#### 2.3 F1 分數
```python
def calculate_f1_score(precision: float, recall: float) -> float:
    """
    F1 分數 = 2 * (Precision * Recall) / (Precision + Recall)
    
    調和平均數，平衡精準度和召回率
    """
    if precision + recall == 0:
        return 0.0
    
    f1 = 2 * (precision * recall) / (precision + recall)
    
    return round(f1, 4)
```

#### 2.4 NDCG@K (Normalized Discounted Cumulative Gain)
```python
import math

def calculate_dcg(relevance_scores: list, k: int = 5) -> float:
    """
    DCG@K = rel_1 + Σ(rel_i / log2(i+1)) for i=2 to k
    
    考慮排序位置的評分指標
    """
    dcg = 0.0
    for i, rel in enumerate(relevance_scores[:k], start=1):
        if i == 1:
            dcg += rel
        else:
            dcg += rel / math.log2(i + 1)
    
    return dcg

def calculate_ndcg(returned_ids: list, expected_ids: list, k: int = 5) -> float:
    """
    NDCG@K = DCG@K / IDCG@K
    
    範例:
        returned_ids = [2, 1, 4, 7, 3]  # 實際返回順序
        expected_ids = [2, 4, 6, 8]      # 預期正確答案
        
        relevance_scores = [1, 0, 1, 0, 0]  # 2和4是正確的
        DCG@5 = 1 + 1/log2(3) = 1 + 0.63 = 1.63
        
        ideal_scores = [1, 1, 0, 0, 0]  # 理想排序 (所有正確答案在前)
        IDCG@5 = 1 + 1/log2(3) = 1.63
        
        NDCG@5 = 1.63 / 1.63 = 1.0
    """
    # 計算實際返回結果的 relevance scores
    relevance_scores = [1 if doc_id in expected_ids else 0 for doc_id in returned_ids]
    
    # 計算 DCG
    dcg = calculate_dcg(relevance_scores, k)
    
    # 計算理想排序的 IDCG (所有正確答案都在前面)
    ideal_scores = [1] * min(len(expected_ids), k) + [0] * max(0, k - len(expected_ids))
    idcg = calculate_dcg(ideal_scores, k)
    
    if idcg == 0:
        return 0.0
    
    ndcg = dcg / idcg
    
    return round(ndcg, 4)
```

#### 2.5 響應時間評分
```python
def calculate_speed_score(response_time_ms: float, max_time: float = 1000.0) -> float:
    """
    響應時間評分 (反向計算，越快分數越高)
    
    範例:
        response_time = 200ms, max_time = 1000ms
        speed_score = (1000 - 200) / 1000 = 0.8
    """
    if response_time_ms >= max_time:
        return 0.0
    
    speed_score = (max_time - response_time_ms) / max_time
    
    return round(speed_score, 4)
```

#### 2.6 總分計算
```python
def calculate_overall_score(metrics: dict, weights: dict) -> float:
    """
    總分 = Σ(metric_score * weight)
    
    範例:
        metrics = {
            'precision': 0.8,
            'recall': 0.75,
            'f1_score': 0.77,
            'speed_score': 0.85,
            'ndcg': 0.82
        }
        weights = {
            'precision': 0.35,
            'recall': 0.30,
            'f1_score': 0.20,
            'speed_score': 0.10,
            'ndcg': 0.05
        }
        
        overall_score = (0.8*0.35) + (0.75*0.30) + (0.77*0.20) + (0.85*0.10) + (0.82*0.05)
                      = 0.28 + 0.225 + 0.154 + 0.085 + 0.041
                      = 0.785 (78.5 分)
    """
    overall = sum(metrics.get(key, 0) * weight for key, weight in weights.items())
    
    return round(overall * 100, 2)  # 轉換為 0-100 分
```

---

### 3. 前端介面設計

#### 3.1 主頁面: 跑分系統首頁 (`/admin/search-benchmark`)
```
┌─────────────────────────────────────────────────────────────┐
│  🏆 搜尋演算法跑分系統                             [+ 新增版本] │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  📊 版本對比圖表                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                                                         │  │
│  │  ▁▂▄█  Precision    ═══  v2.1.0                       │  │
│  │  ▁▃▅█  Recall       ─ ─  v2.0.5                       │  │
│  │  ▁▃▆█  F1-Score     ∙∙∙  v1.9.2 (Baseline)            │  │
│  │                                                         │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│  📋 版本列表                                                  │
│  ┌───┬────────┬─────────┬─────┬────────┬────────┬────────┐ │
│  │ ✓ │ 版本   │ 總分    │ P   │ R      │ F1     │ 時間   │ │
│  ├───┼────────┼─────────┼─────┼────────┼────────┼────────┤ │
│  │ ● │v2.1.0  │ 85.2    │0.88 │ 0.82   │ 0.85   │ 245ms  │ │
│  │ ○ │v2.0.5  │ 81.5    │0.85 │ 0.78   │ 0.81   │ 312ms  │ │
│  │ ⭐│v1.9.2  │ 78.0    │0.80 │ 0.76   │ 0.78   │ 389ms  │ │
│  └───┴────────┴─────────┴─────┴────────┴────────┴────────┘ │
│                                                               │
│  [查看詳細] [執行測試] [匯出報告]                             │
└─────────────────────────────────────────────────────────────┘
```

#### 3.2 測試題庫管理 (`/admin/benchmark-test-cases`)
```
┌─────────────────────────────────────────────────────────────┐
│  📝 測試題庫管理                        [+ 新增題目] [批量匯入] │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  🔍 篩選:  [類別: 全部▾] [難度: 全部▾] [狀態: 啟用中▾]       │
│                                                               │
│  ┌ID──┬問題────────────────┬類別────┬難度──┬狀態──┬操作──┐ │
│  │ 1  │如何測試USB 3.0速度? │USB測試 │中等  │✓啟用 │✏️ 🗑️ │ │
│  │ 2  │PCIe Gen4 檢測方法？ │PCIe測試│困難  │✓啟用 │✏️ 🗑️ │ │
│  │ 3  │NVMe 效能測試工具？  │NVMe測試│簡單  │✓啟用 │✏️ 🗑️ │ │
│  └────┴────────────────────┴────────┴──────┴──────┴──────┘ │
│                                                               │
│  顯示 1-10 / 共 156 題                          [1][2][3]..  │
└─────────────────────────────────────────────────────────────┘
```

#### 3.3 執行測試頁面 (`/admin/benchmark-run`)
```
┌─────────────────────────────────────────────────────────────┐
│  ▶️ 執行跑分測試                                              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  選擇版本: [v2.1.0 - Hybrid Search          ▾]               │
│  測試範圍: [● 全部題目 (156題)                               │
│            ○ 選擇類別  [___________]                          │
│            ○ 選擇難度  [___________]                          │
│                                                               │
│  執行名稱: [v2.1.0 完整測試 - 2025-11-21]                    │
│  執行環境: [Production          ▾]                            │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ ⚙️ 進階設定                                          │    │
│  │   □ 啟用快取                                         │    │
│  │   □ 記錄詳細日誌                                     │    │
│  │   □ 失敗時暫停                                       │    │
│  │   □ 並行執行 (Worker數: [4_])                       │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
│  預估時間: 約 8 分鐘 (156題 × 3秒/題)                        │
│                                                               │
│  [開始執行]  [排程執行]  [取消]                               │
└─────────────────────────────────────────────────────────────┘
```

#### 3.4 測試結果詳細頁 (`/admin/benchmark-result/:runId`)
```
┌─────────────────────────────────────────────────────────────┐
│  📊 測試結果詳情 - v2.1.0 完整測試                            │
│  執行時間: 2025-11-21 14:35:22 ~ 14:43:18 (7分56秒)          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  🎯 總體評分: 85.2 / 100                                      │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Precision:   ████████████████░░ 88.5%              │    │
│  │ Recall:      ██████████████░░░░ 82.3%              │    │
│  │ F1-Score:    ███████████████░░░ 85.1%              │    │
│  │ NDCG@5:      ████████████████░░ 87.2%              │    │
│  │ Avg Time:    ████████████░░░░░░ 245ms              │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
│  📈 分類別表現                                                │
│  ┌類別────────┬題數──┬通過率─┬平均分─┬Precision┬Recall─┐   │
│  │ USB測試    │ 45   │ 93.3% │ 87.2  │ 0.89    │ 0.85  │   │
│  │ PCIe測試   │ 38   │ 86.8% │ 82.5  │ 0.86    │ 0.79  │   │
│  │ NVMe測試   │ 32   │ 90.6% │ 85.8  │ 0.88    │ 0.84  │   │
│  │ 網路測試   │ 41   │ 78.0% │ 79.1  │ 0.82    │ 0.76  │   │
│  └────────────┴──────┴───────┴───────┴─────────┴───────┘   │
│                                                               │
│  🔍 失敗案例分析 (12題失敗)                                   │
│  ┌ID─┬問題─────────────┬預期─┬實際─┬Precision┬Recall─┐    │
│  │ 23│SATA vs NVMe差異?│ 3文檔│ 2  │ 0.67    │ 0.67  │    │
│  │ 45│Gen4 vs Gen3速度?│ 2文檔│ 1  │ 0.50    │ 0.50  │    │
│  └───┴─────────────────┴─────┴────┴─────────┴───────┘    │
│                                                               │
│  [匯出Excel] [匯出PDF] [與其他版本對比] [重新執行失敗案例]   │
└─────────────────────────────────────────────────────────────┘
```

#### 3.5 版本對比頁面 (`/admin/benchmark-compare`)
```
┌─────────────────────────────────────────────────────────────┐
│  🔀 版本對比分析                                              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  選擇版本對比:                                                │
│  版本A: [v2.1.0 ▾]  vs  版本B: [v2.0.5 ▾]                    │
│                                                               │
│  📊 雷達圖對比                                                │
│  ┌─────────────────────────────────────────────────────┐    │
│  │         Precision                                    │    │
│  │            ╱╲                                        │    │
│  │           ╱  ╲                                       │    │
│  │  NDCG ───●────●─── Recall                          │    │
│  │           ╲  ╱                                       │    │
│  │            ╲╱                                        │    │
│  │          F1-Score                                    │    │
│  │                                                       │    │
│  │  ■ v2.1.0   ■ v2.0.5                                │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
│  📈 指標對比表                                                │
│  ┌指標────────┬v2.1.0──┬v2.0.5──┬差異────┬改善──┐          │
│  │ Precision  │ 88.5%  │ 85.2%  │ +3.3%  │ ↗️ 🟢 │          │
│  │ Recall     │ 82.3%  │ 78.1%  │ +4.2%  │ ↗️ 🟢 │          │
│  │ F1-Score   │ 85.1%  │ 81.4%  │ +3.7%  │ ↗️ 🟢 │          │
│  │ Avg Time   │ 245ms  │ 312ms  │ -67ms  │ ↗️ 🟢 │          │
│  │ 總分       │ 85.2   │ 81.5   │ +3.7   │ ↗️ 🟢 │          │
│  └────────────┴────────┴────────┴────────┴──────┘          │
│                                                               │
│  💡 差異分析:                                                 │
│  • v2.1.0 在所有指標上都有顯著改善                            │
│  • 響應時間減少 21.5%，大幅提升用戶體驗                       │
│  • Recall 提升最明顯 (+4.2%)，更少遺漏正確答案                │
│                                                               │
│  [匯出對比報告] [查看詳細差異]                                │
└─────────────────────────────────────────────────────────────┘
```

---

### 4. 後端 API 設計

#### 4.1 版本管理 API
```python
# GET /api/search-benchmark/versions/
# 列出所有版本
{
    "data": [
        {
            "id": 1,
            "version_name": "Protocol Assistant v2.1",
            "version_code": "v2.1.0",
            "algorithm_type": "hybrid",
            "is_active": true,
            "is_baseline": false,
            "avg_precision": 0.885,
            "avg_recall": 0.823,
            "avg_response_time": 245.5,
            "total_tests": 12
        }
    ]
}

# POST /api/search-benchmark/versions/
# 創建新版本
{
    "version_name": "Protocol Assistant v2.2",
    "version_code": "v2.2.0",
    "description": "新增 reranking 機制",
    "algorithm_type": "hybrid",
    "parameters": {
        "vector_weight": 0.7,
        "keyword_weight": 0.3,
        "use_reranking": true
    }
}

# PATCH /api/search-benchmark/versions/{id}/
# 更新版本狀態
{
    "is_active": false,
    "is_baseline": true
}
```

#### 4.2 測試題庫 API
```python
# GET /api/search-benchmark/test-cases/
# 列出測試題目 (支援篩選)
# Query params: ?category=USB測試&difficulty=medium&is_active=true

# POST /api/search-benchmark/test-cases/
# 創建測試題目
{
    "question": "如何測試 USB 3.0 的傳輸速度？",
    "question_type": "procedure",
    "difficulty_level": "medium",
    "expected_document_ids": [45, 67, 89],
    "expected_keywords": ["USB 3.0", "傳輸速度"],
    "category": "USB測試",
    "tags": ["USB", "效能測試"]
}

# POST /api/search-benchmark/test-cases/batch-import/
# 批量匯入 (CSV/JSON)
{
    "format": "csv",
    "data": "base64_encoded_file_content"
}
```

#### 4.3 執行測試 API
```python
# POST /api/search-benchmark/runs/
# 啟動新的測試執行
{
    "version_id": 1,
    "run_name": "v2.1.0 完整測試",
    "test_case_filters": {
        "category": ["USB測試", "PCIe測試"],
        "difficulty": ["medium", "hard"]
    },
    "settings": {
        "use_cache": false,
        "parallel_workers": 4,
        "stop_on_failure": false
    }
}

# Response:
{
    "run_id": 123,
    "status": "pending",
    "total_test_cases": 156,
    "estimated_duration_seconds": 480
}

# GET /api/search-benchmark/runs/{id}/
# 獲取執行狀態
{
    "id": 123,
    "status": "running",
    "progress": 65,  # 0-100
    "completed_test_cases": 102,
    "total_test_cases": 156,
    "current_test_case": "如何測試 PCIe Gen4...",
    "elapsed_seconds": 312
}

# GET /api/search-benchmark/runs/{id}/results/
# 獲取詳細結果
{
    "run_id": 123,
    "overall_score": 85.2,
    "metrics": {
        "precision": 0.885,
        "recall": 0.823,
        "f1_score": 0.851,
        "ndcg_at_5": 0.872,
        "avg_response_time": 245.5
    },
    "category_breakdown": [...],
    "failed_cases": [...]
}
```

#### 4.4 對比分析 API
```python
# GET /api/search-benchmark/compare/
# 對比兩個版本
# Query params: ?version_a=1&version_b=2

{
    "version_a": {
        "id": 1,
        "version_code": "v2.1.0",
        "metrics": {...}
    },
    "version_b": {
        "id": 2,
        "version_code": "v2.0.5",
        "metrics": {...}
    },
    "improvements": {
        "precision": 0.033,
        "recall": 0.042,
        "response_time": -67
    }
}
```

---

### 5. 實作流程

#### Phase 1: 資料庫和模型 (Week 1)
1. ✅ 創建資料庫 migration
2. ✅ 建立 Django models
3. ✅ 建立 admin 介面 (快速測試)
4. ✅ 建立初始化腳本 (預設評分維度)

#### Phase 2: 測試題庫 (Week 2)
1. ✅ 實作測試案例 CRUD API
2. ✅ 建立測試案例管理頁面
3. ✅ 實作批量匯入功能
4. ✅ 從現有 Protocol Guide 知識庫提取初始題目

#### Phase 3: 評分引擎 (Week 3)
1. ✅ 實作評分計算邏輯
2. ✅ 建立測試執行引擎
3. ✅ 整合現有搜尋 API
4. ✅ 實作並行執行機制

#### Phase 4: 前端介面 (Week 4)
1. ✅ 版本管理頁面
2. ✅ 測試執行頁面
3. ✅ 結果展示頁面
4. ✅ 版本對比頁面

#### Phase 5: 視覺化和報表 (Week 5)
1. ✅ 整合圖表庫 (Recharts/ECharts)
2. ✅ 實作雷達圖、折線圖
3. ✅ 實作匯出功能 (PDF/Excel)
4. ✅ 建立趨勢分析頁面

---

### 6. 測試數據準備

#### 6.1 初始測試題目範例 (Protocol Assistant)
```python
INITIAL_TEST_CASES = [
    # USB 測試類別
    {
        "question": "如何測試 USB 3.0 的傳輸速度？",
        "category": "USB測試",
        "difficulty": "medium",
        "expected_keywords": ["USB 3.0", "CrystalDiskMark", "傳輸速度"],
        "expected_document_titles": ["USB 3.0 效能測試", "CrystalDiskMark 使用指南"]
    },
    {
        "question": "USB Type-C 和 USB 3.0 有什麼差異？",
        "category": "USB測試",
        "difficulty": "easy",
        "expected_keywords": ["Type-C", "USB 3.0", "差異", "接口"],
    },
    
    # PCIe 測試類別
    {
        "question": "如何檢測 PCIe Gen4 是否正常運行？",
        "category": "PCIe測試",
        "difficulty": "hard",
        "expected_keywords": ["PCIe Gen4", "檢測", "GPU-Z", "傳輸速度"],
    },
    {
        "question": "PCIe Gen3 和 Gen4 的速度差異是多少？",
        "category": "PCIe測試",
        "difficulty": "medium",
        "expected_keywords": ["Gen3", "Gen4", "速度", "16GT/s"],
    },
    
    # NVMe 測試類別
    {
        "question": "NVMe SSD 效能測試工具有哪些？",
        "category": "NVMe測試",
        "difficulty": "easy",
        "expected_keywords": ["NVMe", "CrystalDiskMark", "AS SSD", "ATTO"],
    },
    {
        "question": "如何測試 NVMe SSD 的 4K 隨機讀寫效能？",
        "category": "NVMe測試",
        "difficulty": "hard",
        "expected_keywords": ["4K", "隨機讀寫", "IOPS", "CrystalDiskMark"],
    },
    
    # 綜合測試
    {
        "question": "CrystalDiskMark 各項測試結果代表什麼意義？",
        "category": "工具使用",
        "difficulty": "medium",
        "expected_keywords": ["CrystalDiskMark", "Seq", "4K", "Q32T1"],
    },
]
```

#### 6.2 自動生成測試題目腳本
```python
# backend/scripts/generate_test_cases_from_kb.py

from api.models import ProtocolGuide, BenchmarkTestCase
import re

def extract_questions_from_knowledge_base():
    """
    從 Protocol Guide 知識庫自動提取潛在的測試題目
    
    策略:
    1. 尋找標題中含有「如何」、「什麼」等疑問詞
    2. 提取步驟性內容作為程序類問題
    3. 提取對比性內容作為比較類問題
    """
    
    question_patterns = [
        r'如何.*?[？\?]',
        r'什麼.*?[？\?]',
        r'為什麼.*?[？\?]',
        r'怎麼.*?[？\?]',
    ]
    
    guides = ProtocolGuide.objects.all()
    generated_cases = []
    
    for guide in guides:
        content = f"{guide.title} {guide.content}"
        
        # 方法1: 提取問題句
        for pattern in question_patterns:
            matches = re.findall(pattern, content)
            for question in matches:
                case = {
                    'question': question,
                    'expected_document_ids': [guide.id],
                    'source': f'auto_extracted_from_{guide.id}'
                }
                generated_cases.append(case)
        
        # 方法2: 基於標題生成問題
        if '測試' in guide.title:
            question = f"如何進行{guide.title}？"
            case = {
                'question': question,
                'expected_document_ids': [guide.id],
                'question_type': 'procedure'
            }
            generated_cases.append(case)
    
    return generated_cases
```

---

### 7. 擴展功能規劃

#### 7.1 自動化測試 (CI/CD 整合)
```yaml
# .github/workflows/search-benchmark.yml

name: Search Benchmark Test

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Run Search Benchmark
        run: |
          docker exec ai-django python manage.py run_search_benchmark \
            --version-code ${{ github.sha }} \
            --run-name "CI-Test-${{ github.run_number }}" \
            --min-score 80.0
      
      - name: Upload Results
        uses: actions/upload-artifact@v2
        with:
          name: benchmark-results
          path: benchmark_results_*.json
```

#### 7.2 A/B Testing 支援
```python
# 對比兩個版本在相同題目上的表現
# 自動識別哪些題目在新版本中表現變差

class ABTestAnalyzer:
    def compare_versions(self, version_a_id, version_b_id):
        """對比兩個版本，找出退步的題目"""
        
        results_a = BenchmarkTestResult.objects.filter(
            test_run__version_id=version_a_id
        )
        results_b = BenchmarkTestResult.objects.filter(
            test_run__version_id=version_b_id
        )
        
        regression_cases = []
        for result_a in results_a:
            result_b = results_b.get(test_case_id=result_a.test_case_id)
            
            if result_b.f1_score < result_a.f1_score - 0.05:  # 退步超過 5%
                regression_cases.append({
                    'test_case': result_a.test_case,
                    'old_score': result_a.f1_score,
                    'new_score': result_b.f1_score,
                    'degradation': result_a.f1_score - result_b.f1_score
                })
        
        return regression_cases
```

#### 7.3 歷史趨勢分析
```python
# 追蹤指標隨時間的變化
# 繪製演算法改進軌跡

class TrendAnalyzer:
    def get_historical_performance(self, metric_key='f1_score', days=30):
        """獲取歷史效能趨勢"""
        
        from datetime import datetime, timedelta
        start_date = datetime.now() - timedelta(days=days)
        
        runs = BenchmarkTestRun.objects.filter(
            created_at__gte=start_date,
            status='completed'
        ).order_by('created_at')
        
        trend_data = []
        for run in runs:
            trend_data.append({
                'date': run.created_at,
                'version': run.version.version_code,
                'score': getattr(run, f'avg_{metric_key}')
            })
        
        return trend_data
```

---

### 8. 使用情境範例

#### 情境 1: 測試新演算法
```
1. 開發人員實作新的混合搜尋演算法 (v2.2.0)
2. 在後台創建新版本記錄
3. 執行完整測試 (156 題)
4. 系統自動計算各項指標
5. 與 baseline (v1.9.2) 對比
6. 發現 Precision 提升 8%，Recall 提升 5%
7. 決定部署新版本到生產環境
```

#### 情境 2: 定期品質監控
```
1. 每週自動執行 benchmark 測試
2. 監控效能是否有退步
3. 如果總分低於 80 分，發送告警
4. 開發團隊檢查是否有資料品質問題
5. 調整參數或更新知識庫
```

#### 情境 3: 問題診斷
```
1. 用戶反應某類問題搜尋結果不佳
2. 在題庫中找到對應類別的測試案例
3. 單獨執行該類別的測試
4. 分析失敗原因 (關鍵字匹配不足? 向量不準?)
5. 針對性優化演算法
6. 重新測試驗證改善效果
```

---

## 📌 總結

### 核心價值
1. **量化評估**: 用數據說話，不再憑感覺判斷搜尋品質
2. **持續改進**: 追蹤每次改動的影響，避免無意中讓效能退步
3. **快速驗證**: 自動化測試，幾分鐘內知道新演算法是否更好
4. **問題定位**: 精準找出哪些類型的問題搜尋效果不佳
5. **歷史追溯**: 保留每個版本的測試記錄，可以回顧改進軌跡

### 實作優先級
1. **P0** (必須): 資料庫、基本 API、評分引擎
2. **P1** (重要): 測試題庫管理、執行測試功能
3. **P2** (增強): 視覺化圖表、版本對比
4. **P3** (進階): CI/CD 整合、自動化測試、趨勢分析

### 預期效益
- **開發效率**: 減少 70% 手動測試時間
- **品質保證**: 確保演算法改動不會意外降低品質
- **數據驅動**: 基於客觀指標做決策，而非主觀判斷
- **知識積累**: 建立標準測試題庫，成為團隊共享資產

---

**下一步**: 等待確認後開始實作 Phase 1 (資料庫和模型) 🚀
