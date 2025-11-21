# 🗺️ 搜尋演算法跑分系統 - 分階段實施計劃

**日期**: 2025-11-21  
**狀態**: 📋 實施計劃  
**預計完成時間**: 8-10 週

---

## 📋 總覽

### 三大系統整合

本實施計劃整合以下三個設計文檔：

1. **搜尋演算法跑分系統** (`search-benchmark-system-design.md`)
2. **搜尋演算法版本管理系統** (`search-algorithm-version-management-design.md`)
3. **測試題庫生成計劃** (`benchmark-test-case-generation-plan.md`)

### 核心目標

- ✅ 建立可量化的搜尋品質評估系統
- ✅ 支援多版本搜尋演算法並存和切換
- ✅ 自動化測試和持續監控
- ✅ 提供視覺化的效能對比

---

## 🎯 實施策略

### 核心原則

1. **MVP 優先**：先實現核心功能，再擴展進階特性
2. **增量開發**：每個階段都能獨立運作和驗證
3. **風險控制**：不影響現有系統的正常運作
4. **快速驗證**：每週都有可交付的成果

### 優先級定義

- **P0** (必須): 核心功能，沒有就無法運作
- **P1** (重要): 關鍵功能，影響使用體驗
- **P2** (增強): 改善功能，提升效率
- **P3** (進階): 進階功能，可後續擴展

---

## 📅 分階段實施計劃

---

## 🔵 Phase 1: 資料庫與核心模型 (Week 1-2)

**目標**: 建立完整的資料結構基礎

### Week 1: 資料庫設計與 Migration

#### 任務 1.1: 創建資料庫 Migration (P0)

**檔案**: `backend/api/migrations/004X_search_benchmark_tables.py`

**任務清單**:
```sql
-- ✅ 搜尋演算法版本表
CREATE TABLE search_algorithm_version (
    id SERIAL PRIMARY KEY,
    version_name VARCHAR(100) NOT NULL,
    version_code VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    algorithm_type VARCHAR(50),
    parameters JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    is_baseline BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by_id INTEGER REFERENCES auth_user(id),
    avg_precision DECIMAL(5,4),
    avg_recall DECIMAL(5,4),
    avg_response_time DECIMAL(10,2),
    total_tests INTEGER DEFAULT 0
);

-- ✅ 評分維度表
CREATE TABLE benchmark_metric (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL UNIQUE,
    metric_key VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    metric_type VARCHAR(30),
    calculation_method TEXT,
    max_score DECIMAL(5,2) DEFAULT 100.00,
    min_score DECIMAL(5,2) DEFAULT 0.00,
    weight DECIMAL(3,2) DEFAULT 1.00,
    is_active BOOLEAN DEFAULT TRUE,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ✅ 測試題庫表
CREATE TABLE benchmark_test_case (
    id SERIAL PRIMARY KEY,
    question TEXT NOT NULL,
    question_type VARCHAR(50),
    difficulty_level VARCHAR(20),
    expected_document_ids INTEGER[],
    expected_keywords TEXT[],
    expected_answer_summary TEXT,
    min_required_matches INTEGER DEFAULT 1,
    acceptable_document_ids INTEGER[],
    category VARCHAR(100),
    tags TEXT[],
    source VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    is_validated BOOLEAN DEFAULT FALSE,
    total_runs INTEGER DEFAULT 0,
    avg_score DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by_id INTEGER REFERENCES auth_user(id),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ✅ 測試執行記錄表
CREATE TABLE benchmark_test_run (
    id SERIAL PRIMARY KEY,
    version_id INTEGER REFERENCES search_algorithm_version(id) ON DELETE CASCADE,
    run_name VARCHAR(200),
    run_type VARCHAR(50) DEFAULT 'manual',
    total_test_cases INTEGER NOT NULL,
    completed_test_cases INTEGER DEFAULT 0,
    status VARCHAR(30) DEFAULT 'pending',
    overall_score DECIMAL(5,2),
    avg_precision DECIMAL(5,4),
    avg_recall DECIMAL(5,4),
    avg_f1_score DECIMAL(5,4),
    avg_response_time DECIMAL(10,2),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds INTEGER,
    triggered_by_id INTEGER REFERENCES auth_user(id),
    environment VARCHAR(50),
    git_commit_hash VARCHAR(40),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ✅ 測試結果詳細表
CREATE TABLE benchmark_test_result (
    id SERIAL PRIMARY KEY,
    test_run_id INTEGER REFERENCES benchmark_test_run(id) ON DELETE CASCADE,
    test_case_id INTEGER REFERENCES benchmark_test_case(id) ON DELETE CASCADE,
    search_query TEXT,
    returned_document_ids INTEGER[],
    returned_document_scores DECIMAL(5,4)[],
    precision_score DECIMAL(5,4),
    recall_score DECIMAL(5,4),
    f1_score DECIMAL(5,4),
    ndcg_score DECIMAL(5,4),
    response_time DECIMAL(10,2),
    true_positives INTEGER,
    false_positives INTEGER,
    false_negatives INTEGER,
    is_passed BOOLEAN,
    pass_reason TEXT,
    detailed_results JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**驗證指令**:
```bash
# 創建 migration
docker exec ai-django python manage.py makemigrations

# 執行 migration
docker exec ai-django python manage.py migrate

# 驗證表是否創建
docker exec postgres_db psql -U postgres -d ai_platform -c "\dt benchmark*"
docker exec postgres_db psql -U postgres -d ai_platform -c "\dt search_algorithm*"
```

**預期成果**: 5 張新表成功創建 ✅

---

#### 任務 1.2: 創建 Django Models (P0)

**檔案**: `backend/api/models.py`

**任務清單**:
- ✅ 創建 `SearchAlgorithmVersion` Model
- ✅ 創建 `BenchmarkMetric` Model
- ✅ 創建 `BenchmarkTestCase` Model
- ✅ 創建 `BenchmarkTestRun` Model
- ✅ 創建 `BenchmarkTestResult` Model
- ✅ 添加 Model 方法和屬性
- ✅ 配置 Meta 資訊 (ordering, indexes, verbose_name)

**程式碼範例**:
```python
# backend/api/models.py

class SearchAlgorithmVersion(models.Model):
    """搜尋演算法版本"""
    version_name = models.CharField(max_length=100)
    version_code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    algorithm_type = models.CharField(max_length=50, blank=True)
    parameters = models.JSONField(default=dict)
    
    is_active = models.BooleanField(default=True)
    is_baseline = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    # 效能指標快照
    avg_precision = models.DecimalField(max_digits=5, decimal_places=4, null=True)
    avg_recall = models.DecimalField(max_digits=5, decimal_places=4, null=True)
    avg_response_time = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    total_tests = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'search_algorithm_version'
        ordering = ['-created_at']
        verbose_name = '搜尋演算法版本'
        verbose_name_plural = '搜尋演算法版本'
    
    def __str__(self):
        return f"{self.version_name} ({self.version_code})"

# ... 其他 Models
```

**驗證指令**:
```bash
# 進入 Django shell 測試
docker exec -it ai-django python manage.py shell

from api.models import SearchAlgorithmVersion
version = SearchAlgorithmVersion.objects.create(
    version_name="Test Version",
    version_code="v1.0.0-test"
)
print(version)  # 應該正常顯示
version.delete()  # 清理測試資料
```

**預期成果**: 所有 Models 正常運作 ✅

---

### Week 2: 初始化資料與 Serializers

#### 任務 1.3: 初始化預設評分維度 (P0)

**檔案**: `backend/scripts/init_benchmark_metrics.py`

**任務清單**:
- ✅ 創建初始化腳本
- ✅ 插入 5 個預設評分維度
- ✅ 設定權重和計算方式

**程式碼範例**:
```python
# backend/scripts/init_benchmark_metrics.py

from api.models import BenchmarkMetric

def init_metrics():
    """初始化預設評分維度"""
    
    metrics = [
        {
            "metric_name": "精準度 (Precision)",
            "metric_key": "precision",
            "metric_type": "precision",
            "description": "回傳結果中正確答案的比例",
            "calculation_method": "TP / (TP + FP)",
            "weight": 0.35,
            "display_order": 1
        },
        {
            "metric_name": "召回率 (Recall)",
            "metric_key": "recall",
            "metric_type": "recall",
            "description": "正確答案被找回的比例",
            "calculation_method": "TP / (TP + FN)",
            "weight": 0.30,
            "display_order": 2
        },
        {
            "metric_name": "F1 分數 (F1-Score)",
            "metric_key": "f1_score",
            "metric_type": "quality",
            "description": "精準度和召回率的調和平均數",
            "calculation_method": "2 * (Precision * Recall) / (Precision + Recall)",
            "weight": 0.20,
            "display_order": 3
        },
        {
            "metric_name": "平均響應時間 (Avg Response Time)",
            "metric_key": "avg_response_time",
            "metric_type": "speed",
            "description": "搜尋查詢的平均處理時間 (ms)",
            "calculation_method": "sum(response_times) / count",
            "weight": 0.10,
            "display_order": 4
        },
        {
            "metric_name": "NDCG@5",
            "metric_key": "ndcg_at_5",
            "metric_type": "quality",
            "description": "考慮排序的搜尋品質指標",
            "calculation_method": "DCG / IDCG (前5個結果)",
            "weight": 0.05,
            "display_order": 5
        }
    ]
    
    for metric_data in metrics:
        metric, created = BenchmarkMetric.objects.update_or_create(
            metric_key=metric_data['metric_key'],
            defaults=metric_data
        )
        print(f"{'✅ 創建' if created else '✅ 更新'}: {metric.metric_name}")
    
    print(f"\n✅ 預設評分維度初始化完成！")

if __name__ == '__main__':
    init_metrics()
```

**執行指令**:
```bash
docker exec ai-django python scripts/init_benchmark_metrics.py
```

**預期成果**: 5 個評分維度成功創建 ✅

---

#### 任務 1.4: 創建 Serializers (P0)

**檔案**: `backend/api/serializers/benchmark_serializers.py`

**任務清單**:
- ✅ `SearchAlgorithmVersionSerializer`
- ✅ `BenchmarkMetricSerializer`
- ✅ `BenchmarkTestCaseSerializer`
- ✅ `BenchmarkTestRunSerializer`
- ✅ `BenchmarkTestResultSerializer`

**驗證方式**: 單元測試

**預期成果**: 所有 Serializers 正常序列化/反序列化 ✅

---

### Week 1-2 驗收標準 ✅

- [ ] 資料庫 Migration 成功執行
- [ ] 5 張新表正確創建（含索引）
- [ ] 5 個 Django Models 正常運作
- [ ] 5 個預設評分維度已初始化
- [ ] 5 個 Serializers 測試通過
- [ ] Django Admin 可查看所有 Models

---

## 🟢 Phase 2: 測試題庫建立 (Week 3-4)

**目標**: 建立高品質的測試題目資料

### Week 3: 手動創建核心題目

#### 任務 2.1: 手動創建 50 題核心題目 (P0)

**負責人**: QA + AI 協助

**任務清單**:
- ✅ 選擇 10 篇核心文章
  - ULINK (ID: 28)
  - UNH-IOL (ID: 10) - **包含密碼題目** 🆕
  - CrystalDiskMark 5 (ID: 16) - **包含 SOP 題目** 🆕
  - Burn in Test (ID: 15) - **包含 SOP 題目** 🆕
  - Oakgate (ID: 29)
  - PyNvme3 (ID: 34)
  - SANBlaze (ID: 33)
  - WHQL (ID: 32)
  - Kingston Linux 開卡 (ID: 25)
  - Google AVL (ID: 26)

- ✅ 每篇文章產出 5 題
  - 2 題簡單 (事實查詢)
  - 2 題中等 (程序或設定)
  - 1 題困難 (對比或故障排除)

**工具**: `benchmark-test-case-generation-plan.md` 中的 15 個範例題目

**檔案**: `backend/scripts/create_initial_test_cases.py`

**程式碼範例**:
```python
# backend/scripts/create_initial_test_cases.py

from api.models import BenchmarkTestCase

def create_initial_test_cases():
    """創建初始 50 題測試題目"""
    
    test_cases = [
        # === ULINK (5 題) ===
        {
            "question": "ULINK 測試的安裝程式和測試腳本存放在 NAS 的哪個路徑？",
            "question_type": "path",
            "difficulty_level": "easy",
            "expected_document_ids": [28],
            "expected_keywords": ["ULINK", "nas01", "TestTools", "Release"],
            "category": "測試工具",
            "tags": ["ULINK", "路徑", "NAS"],
            "min_required_matches": 1
        },
        # ... (從 benchmark-test-case-generation-plan.md 複製 15 題)
        
        # === 新增的 3 題 ===
        {
            "question": "UNH-IOL 測試的密碼是什麼？",
            "question_type": "fact",
            "difficulty_level": "easy",
            "expected_document_ids": [10],
            "expected_keywords": ["UNH-IOL", "密碼", "sudo su", "1"],
            "category": "測試工具",
            "tags": ["UNH-IOL", "密碼"],
        },
        {
            "question": "CrystalDiskMark 5 的完整測試流程或 SOP 是什麼？",
            "question_type": "procedure",
            "difficulty_level": "medium",
            "expected_document_ids": [16],
            "expected_keywords": ["CrystalDiskMark", "SOP"],
            "category": "測試執行",
        },
        {
            "question": "Burn in Test 的測試 SOP 或操作流程是什麼？",
            "question_type": "procedure",
            "difficulty_level": "medium",
            "expected_document_ids": [15],
            "expected_keywords": ["Burn in Test", "SOP"],
            "category": "測試執行",
        },
        
        # ... (繼續添加至 50 題)
    ]
    
    for case_data in test_cases:
        case = BenchmarkTestCase.objects.create(**case_data)
        print(f"✅ 創建題目: {case.question[:50]}...")
    
    print(f"\n✅ 共創建 {len(test_cases)} 題測試題目")

if __name__ == '__main__':
    create_initial_test_cases()
```

**執行指令**:
```bash
docker exec ai-django python scripts/create_initial_test_cases.py
```

**驗證指令**:
```bash
# 檢查題目數量
docker exec postgres_db psql -U postgres -d ai_platform -c \
  "SELECT difficulty_level, COUNT(*) FROM benchmark_test_case GROUP BY difficulty_level;"

# 檢查類別分布
docker exec postgres_db psql -U postgres -d ai_platform -c \
  "SELECT category, COUNT(*) FROM benchmark_test_case GROUP BY category;"
```

**預期成果**: 50 題核心題目成功創建 ✅

---

#### 任務 2.2: 人工驗證題目品質 (P0)

**驗證方式**:
1. 使用現有搜尋系統測試每一題
2. 確認預期文檔是否能被找到
3. 調整關鍵字和閾值（如需要）

**工具**: 手動測試 + 簡單腳本

**程式碼範例**:
```python
# backend/scripts/validate_test_cases.py

from api.models import BenchmarkTestCase, ProtocolGuide
from library.protocol_guide.search_service import ProtocolGuideSearchService

def validate_test_cases():
    """驗證測試題目品質"""
    
    service = ProtocolGuideSearchService()
    cases = BenchmarkTestCase.objects.filter(is_validated=False)
    
    passed = 0
    failed = 0
    
    for case in cases:
        # 執行搜尋
        results = service.search_knowledge(
            query=case.question,
            top_k=5
        )
        
        # 檢查預期文檔是否在結果中
        returned_ids = [r['id'] for r in results]
        expected_ids = case.expected_document_ids
        
        found = any(exp_id in returned_ids for exp_id in expected_ids)
        
        if found:
            case.is_validated = True
            case.save()
            passed += 1
            print(f"✅ 通過: {case.question[:50]}...")
        else:
            failed += 1
            print(f"❌ 失敗: {case.question[:50]}...")
            print(f"   預期: {expected_ids}, 實際: {returned_ids}")
    
    print(f"\n✅ 驗證完成: {passed} 題通過, {failed} 題失敗")
    print(f"   通過率: {passed/(passed+failed)*100:.1f}%")

if __name__ == '__main__':
    validate_test_cases()
```

**執行指令**:
```bash
docker exec ai-django python scripts/validate_test_cases.py
```

**預期成果**: 通過率 >= 80% ✅

---

### Week 4: 半自動擴充題庫

#### 任務 2.3: 開發題目生成工具 (P1)

**檔案**: `backend/scripts/generate_test_cases_from_kb.py`

**任務清單**:
- ✅ 實作 `TestCaseGenerator` 類別
- ✅ 實作 `generate_fact_questions()` 方法
- ✅ 實作 `generate_procedure_questions()` 方法
- ✅ 實作 `generate_path_questions()` 方法

**程式碼範例**: 參考 `benchmark-test-case-generation-plan.md` 中的範例

**預期成果**: 半自動生成工具可運作 ✅

---

#### 任務 2.4: 擴充至 100 題 (P1)

**執行指令**:
```bash
docker exec ai-django python scripts/generate_test_cases_from_kb.py --target 100
docker exec ai-django python scripts/validate_test_cases.py
```

**預期成果**: 總題庫達到 100 題（通過率 >= 75%）✅

---

### Week 3-4 驗收標準 ✅

- [ ] 50 題核心題目手動創建
- [ ] 題目品質驗證通過率 >= 80%
- [ ] 半自動生成工具開發完成
- [ ] 總題庫達到 100 題
- [ ] 難度分布符合預期（簡單 40%, 中等 45%, 困難 15%）
- [ ] 類別覆蓋完整（8 種題型）

---

## 🟡 Phase 3: 評分引擎與測試執行 (Week 5-6)

**目標**: 實作核心評分邏輯和測試執行引擎

### Week 5: 評分計算邏輯

#### 任務 3.1: 實作評分計算模組 (P0)

**檔案**: `backend/library/benchmark/scoring_engine.py`

**任務清單**:
- ✅ 實作 `calculate_precision()`
- ✅ 實作 `calculate_recall()`
- ✅ 實作 `calculate_f1_score()`
- ✅ 實作 `calculate_ndcg()`
- ✅ 實作 `calculate_speed_score()`
- ✅ 實作 `calculate_overall_score()`

**程式碼範例**:
```python
# backend/library/benchmark/scoring_engine.py

class ScoringEngine:
    """評分引擎"""
    
    @staticmethod
    def calculate_precision(returned_ids: list, expected_ids: list) -> float:
        """計算精準度"""
        if not returned_ids:
            return 0.0
        
        true_positives = len(set(returned_ids) & set(expected_ids))
        precision = true_positives / len(returned_ids)
        
        return round(precision, 4)
    
    @staticmethod
    def calculate_recall(returned_ids: list, expected_ids: list) -> float:
        """計算召回率"""
        if not expected_ids:
            return 1.0
        
        true_positives = len(set(returned_ids) & set(expected_ids))
        recall = true_positives / len(expected_ids)
        
        return round(recall, 4)
    
    # ... 其他方法
```

**單元測試**:
```python
# backend/tests/test_scoring_engine.py

def test_precision():
    returned = [1, 2, 3, 4, 5]
    expected = [2, 4, 6, 8]
    
    precision = ScoringEngine.calculate_precision(returned, expected)
    assert precision == 0.4  # 2 out of 5
```

**預期成果**: 所有評分函數測試通過 ✅

---

#### 任務 3.2: 實作測試執行引擎 (P0)

**檔案**: `backend/library/benchmark/test_runner.py`

**任務清單**:
- ✅ 實作 `BenchmarkTestRunner` 類別
- ✅ 實作 `run_single_test()` 方法
- ✅ 實作 `run_batch_tests()` 方法
- ✅ 整合搜尋服務
- ✅ 記錄測試結果

**程式碼範例**:
```python
# backend/library/benchmark/test_runner.py

from api.models import BenchmarkTestCase, BenchmarkTestRun, BenchmarkTestResult
from library.protocol_guide.search_service import ProtocolGuideSearchService
from .scoring_engine import ScoringEngine

class BenchmarkTestRunner:
    """測試執行引擎"""
    
    def __init__(self, version_id: int):
        self.version_id = version_id
        self.search_service = ProtocolGuideSearchService()
        self.scoring_engine = ScoringEngine()
    
    def run_single_test(self, test_case: BenchmarkTestCase) -> dict:
        """執行單一測試"""
        import time
        
        # 記錄開始時間
        start_time = time.time()
        
        # 執行搜尋
        results = self.search_service.search_knowledge(
            query=test_case.question,
            top_k=5
        )
        
        # 計算響應時間
        response_time = (time.time() - start_time) * 1000  # ms
        
        # 提取返回的文檔 IDs
        returned_ids = [r['id'] for r in results]
        returned_scores = [r['similarity'] for r in results]
        
        # 計算評分
        precision = self.scoring_engine.calculate_precision(
            returned_ids, test_case.expected_document_ids
        )
        recall = self.scoring_engine.calculate_recall(
            returned_ids, test_case.expected_document_ids
        )
        f1_score = self.scoring_engine.calculate_f1_score(precision, recall)
        ndcg_score = self.scoring_engine.calculate_ndcg(
            returned_ids, test_case.expected_document_ids, k=5
        )
        
        # 計算 TP, FP, FN
        true_positives = len(set(returned_ids) & set(test_case.expected_document_ids))
        false_positives = len(set(returned_ids) - set(test_case.expected_document_ids))
        false_negatives = len(set(test_case.expected_document_ids) - set(returned_ids))
        
        # 判斷是否通過
        is_passed = true_positives >= test_case.min_required_matches
        
        return {
            'search_query': test_case.question,
            'returned_document_ids': returned_ids,
            'returned_document_scores': returned_scores,
            'precision_score': precision,
            'recall_score': recall,
            'f1_score': f1_score,
            'ndcg_score': ndcg_score,
            'response_time': response_time,
            'true_positives': true_positives,
            'false_positives': false_positives,
            'false_negatives': false_negatives,
            'is_passed': is_passed,
            'pass_reason': f"找到 {true_positives}/{len(test_case.expected_document_ids)} 個預期文檔"
        }
    
    def run_batch_tests(self, test_run: BenchmarkTestRun, test_cases: list):
        """批量執行測試"""
        
        # 更新狀態
        test_run.status = 'running'
        test_run.started_at = timezone.now()
        test_run.save()
        
        results = []
        
        for test_case in test_cases:
            try:
                # 執行單一測試
                result_data = self.run_single_test(test_case)
                
                # 儲存結果
                result = BenchmarkTestResult.objects.create(
                    test_run=test_run,
                    test_case=test_case,
                    **result_data
                )
                
                results.append(result)
                
                # 更新進度
                test_run.completed_test_cases += 1
                test_run.save()
                
            except Exception as e:
                print(f"❌ 測試失敗: {test_case.question} - {str(e)}")
        
        # 計算總體結果
        test_run.status = 'completed'
        test_run.completed_at = timezone.now()
        test_run.duration_seconds = (test_run.completed_at - test_run.started_at).seconds
        
        # 計算平均分數
        test_run.avg_precision = sum(r.precision_score for r in results) / len(results)
        test_run.avg_recall = sum(r.recall_score for r in results) / len(results)
        test_run.avg_f1_score = sum(r.f1_score for r in results) / len(results)
        test_run.avg_response_time = sum(r.response_time for r in results) / len(results)
        
        # 計算總分
        test_run.overall_score = self.scoring_engine.calculate_overall_score({
            'precision': test_run.avg_precision,
            'recall': test_run.avg_recall,
            'f1_score': test_run.avg_f1_score,
            'speed_score': self.scoring_engine.calculate_speed_score(test_run.avg_response_time)
        })
        
        test_run.save()
        
        return results
```

**預期成果**: 測試執行引擎可運作 ✅

---

### Week 6: 命令列工具與驗證

#### 任務 3.3: 創建 Django Management Command (P0)

**檔案**: `backend/api/management/commands/run_benchmark.py`

**任務清單**:
- ✅ 實作 `run_benchmark` command
- ✅ 支援參數：版本、題目過濾、並行數
- ✅ 顯示進度條

**程式碼範例**:
```python
# backend/api/management/commands/run_benchmark.py

from django.core.management.base import BaseCommand
from api.models import SearchAlgorithmVersion, BenchmarkTestCase, BenchmarkTestRun
from library.benchmark.test_runner import BenchmarkTestRunner

class Command(BaseCommand):
    help = '執行搜尋演算法跑分測試'
    
    def add_arguments(self, parser):
        parser.add_argument('--version-id', type=int, required=True, help='版本 ID')
        parser.add_argument('--run-name', type=str, default='Manual Test', help='執行名稱')
        parser.add_argument('--category', type=str, help='篩選類別')
        parser.add_argument('--difficulty', type=str, help='篩選難度')
    
    def handle(self, *args, **options):
        version_id = options['version_id']
        run_name = options['run_name']
        
        # 獲取版本
        version = SearchAlgorithmVersion.objects.get(id=version_id)
        
        # 獲取測試案例
        test_cases = BenchmarkTestCase.objects.filter(is_active=True)
        
        if options['category']:
            test_cases = test_cases.filter(category=options['category'])
        
        if options['difficulty']:
            test_cases = test_cases.filter(difficulty_level=options['difficulty'])
        
        # 創建測試執行記錄
        test_run = BenchmarkTestRun.objects.create(
            version=version,
            run_name=run_name,
            total_test_cases=test_cases.count()
        )
        
        # 執行測試
        self.stdout.write(f"🚀 開始執行測試: {run_name}")
        self.stdout.write(f"   版本: {version.version_name}")
        self.stdout.write(f"   題目數: {test_cases.count()}")
        
        runner = BenchmarkTestRunner(version_id=version_id)
        results = runner.run_batch_tests(test_run, test_cases)
        
        # 顯示結果
        self.stdout.write(self.style.SUCCESS(f"\n✅ 測試完成！"))
        self.stdout.write(f"   總分: {test_run.overall_score:.2f}")
        self.stdout.write(f"   精準度: {test_run.avg_precision:.2%}")
        self.stdout.write(f"   召回率: {test_run.avg_recall:.2%}")
        self.stdout.write(f"   平均時間: {test_run.avg_response_time:.2f}ms")
```

**執行範例**:
```bash
# 執行完整測試
docker exec ai-django python manage.py run_benchmark \
  --version-id 1 \
  --run-name "v2.1.0 完整測試"

# 只測試特定類別
docker exec ai-django python manage.py run_benchmark \
  --version-id 1 \
  --run-name "USB 測試" \
  --category "USB測試"
```

**預期成果**: 命令列工具可正常執行測試 ✅

---

#### 任務 3.4: 首次完整跑分測試 (P0)

**測試內容**:
1. 創建當前版本記錄
2. 執行 100 題測試
3. 驗證結果正確性
4. 檢查效能指標

**執行指令**:
```bash
# 1. 創建版本記錄
docker exec -it ai-django python manage.py shell
>>> from api.models import SearchAlgorithmVersion
>>> version = SearchAlgorithmVersion.objects.create(
...     version_name="Protocol Assistant - Current",
...     version_code="v2.1.0-current",
...     algorithm_type="hybrid",
...     is_baseline=True
... )
>>> exit()

# 2. 執行測試
docker exec ai-django python manage.py run_benchmark \
  --version-id 1 \
  --run-name "Baseline Test - 2025-11-21"

# 3. 檢查結果
docker exec postgres_db psql -U postgres -d ai_platform -c \
  "SELECT run_name, status, overall_score, avg_precision, avg_recall 
   FROM benchmark_test_run 
   ORDER BY created_at DESC LIMIT 1;"
```

**預期成果**: 
- 測試成功執行 ✅
- 總分 >= 70 ✅
- 無錯誤或異常 ✅

---

### Week 5-6 驗收標準 ✅

- [ ] 評分計算模組所有函數通過單元測試
- [ ] 測試執行引擎可正常運作
- [ ] Django management command 可用
- [ ] 首次完整跑分測試成功執行
- [ ] 測試結果正確儲存到資料庫
- [ ] 效能指標計算正確

---

## 🟣 Phase 4: 基礎 API 與前端頁面 (Week 7-8)

**目標**: 建立基本的 Web 管理介面

### Week 7: 後端 API 開發

#### 任務 4.1: 創建 ViewSets (P0)

**檔案**: `backend/api/views/viewsets/benchmark_viewsets.py`

**任務清單**:
- ✅ `SearchAlgorithmVersionViewSet` (CRUD)
- ✅ `BenchmarkTestCaseViewSet` (CRUD + 批量匯入)
- ✅ `BenchmarkTestRunViewSet` (CRUD + 執行測試)
- ✅ `BenchmarkTestResultViewSet` (ReadOnly)

**程式碼範例**:
```python
# backend/api/views/viewsets/benchmark_viewsets.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

class BenchmarkTestRunViewSet(viewsets.ModelViewSet):
    """測試執行 ViewSet"""
    queryset = BenchmarkTestRun.objects.all()
    serializer_class = BenchmarkTestRunSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def execute(self, request):
        """執行新的測試"""
        version_id = request.data.get('version_id')
        run_name = request.data.get('run_name')
        test_case_filters = request.data.get('test_case_filters', {})
        
        # 創建測試執行記錄
        test_run = BenchmarkTestRun.objects.create(
            version_id=version_id,
            run_name=run_name,
            triggered_by=request.user
        )
        
        # 非同步執行測試（後續改為 Celery）
        from library.benchmark.test_runner import BenchmarkTestRunner
        
        runner = BenchmarkTestRunner(version_id=version_id)
        test_cases = BenchmarkTestCase.objects.filter(is_active=True)
        
        # 應用篩選
        if test_case_filters.get('category'):
            test_cases = test_cases.filter(category__in=test_case_filters['category'])
        
        test_run.total_test_cases = test_cases.count()
        test_run.save()
        
        # 執行測試
        runner.run_batch_tests(test_run, test_cases)
        
        return Response({
            'run_id': test_run.id,
            'status': test_run.status,
            'message': '測試執行中'
        })
    
    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        """獲取測試結果"""
        test_run = self.get_object()
        results = test_run.results.all()
        
        return Response({
            'run_id': test_run.id,
            'overall_score': test_run.overall_score,
            'metrics': {
                'precision': test_run.avg_precision,
                'recall': test_run.avg_recall,
                'f1_score': test_run.avg_f1_score,
                'response_time': test_run.avg_response_time
            },
            'results': BenchmarkTestResultSerializer(results, many=True).data
        })
```

**URL 配置**:
```python
# backend/api/urls.py

router.register(r'benchmark/versions', views.SearchAlgorithmVersionViewSet)
router.register(r'benchmark/test-cases', views.BenchmarkTestCaseViewSet)
router.register(r'benchmark/test-runs', views.BenchmarkTestRunViewSet)
router.register(r'benchmark/test-results', views.BenchmarkTestResultViewSet)
```

**測試 API**:
```bash
# 獲取版本列表
curl -X GET http://localhost/api/benchmark/versions/

# 執行測試
curl -X POST http://localhost/api/benchmark/test-runs/execute/ \
  -H "Content-Type: application/json" \
  -d '{
    "version_id": 1,
    "run_name": "API Test",
    "test_case_filters": {"category": ["USB測試"]}
  }'

# 獲取測試結果
curl -X GET http://localhost/api/benchmark/test-runs/1/results/
```

**預期成果**: 所有 API 端點正常運作 ✅

---

### Week 8: 前端基礎頁面

#### 任務 4.2: 創建版本列表頁面 (P1)

**檔案**: `frontend/src/pages/admin/SearchBenchmarkPage.js`

**任務清單**:
- ✅ 版本列表展示（Table）
- ✅ 基本指標顯示（Precision, Recall, 總分）
- ✅ 新增版本按鈕
- ✅ 執行測試按鈕

**UI 元件**:
```jsx
// frontend/src/pages/admin/SearchBenchmarkPage.js

import React, { useState, useEffect } from 'react';
import { Table, Button, Space, Tag, Statistic, Row, Col } from 'antd';
import { PlayCircleOutlined, PlusOutlined } from '@ant-design/icons';
import api from '../../services/api';

const SearchBenchmarkPage = () => {
  const [versions, setVersions] = useState([]);
  const [loading, setLoading] = useState(false);
  
  useEffect(() => {
    fetchVersions();
  }, []);
  
  const fetchVersions = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/benchmark/versions/');
      setVersions(response.data);
    } finally {
      setLoading(false);
    }
  };
  
  const columns = [
    {
      title: '狀態',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (is_active, record) => (
        <>
          {is_active && <Tag color="green">啟用中</Tag>}
          {record.is_baseline && <Tag color="gold">基準版本</Tag>}
        </>
      ),
      width: 120,
    },
    {
      title: '版本',
      dataIndex: 'version_code',
      key: 'version_code',
      width: 150,
    },
    {
      title: '名稱',
      dataIndex: 'version_name',
      key: 'version_name',
    },
    {
      title: '總分',
      dataIndex: 'avg_precision',
      key: 'overall_score',
      render: (_, record) => {
        const score = (
          (record.avg_precision || 0) * 0.35 +
          (record.avg_recall || 0) * 0.30 +
          ((record.avg_precision && record.avg_recall) 
            ? (2 * record.avg_precision * record.avg_recall / (record.avg_precision + record.avg_recall)) 
            : 0) * 0.20
        ) * 100;
        
        return <Statistic value={score} precision={1} suffix="/100" />;
      },
      width: 120,
    },
    {
      title: 'Precision',
      dataIndex: 'avg_precision',
      key: 'avg_precision',
      render: (val) => val ? (val * 100).toFixed(1) + '%' : '-',
      width: 100,
    },
    {
      title: 'Recall',
      dataIndex: 'avg_recall',
      key: 'avg_recall',
      render: (val) => val ? (val * 100).toFixed(1) + '%' : '-',
      width: 100,
    },
    {
      title: '響應時間',
      dataIndex: 'avg_response_time',
      key: 'avg_response_time',
      render: (val) => val ? val.toFixed(0) + 'ms' : '-',
      width: 100,
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button 
            type="primary" 
            icon={<PlayCircleOutlined />}
            onClick={() => handleRunTest(record.id)}
          >
            執行測試
          </Button>
        </Space>
      ),
      width: 120,
    },
  ];
  
  const handleRunTest = async (versionId) => {
    // TODO: 開啟測試執行對話框
    console.log('執行測試:', versionId);
  };
  
  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between' }}>
        <h1>🏆 搜尋演算法跑分系統</h1>
        <Button type="primary" icon={<PlusOutlined />}>
          新增版本
        </Button>
      </div>
      
      <Table 
        columns={columns}
        dataSource={versions}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 10 }}
      />
    </div>
  );
};

export default SearchBenchmarkPage;
```

**預期成果**: 基礎頁面可正常顯示和操作 ✅

---

#### 任務 4.3: 側邊欄選單整合 (P1)

**檔案**: `frontend/src/components/Sidebar.js`

**修改內容**:
```jsx
// 在 Admin 子選單中添加
{
  key: 'admin',
  icon: <SettingOutlined />,
  label: 'Admin',
  children: [
    // ... 現有項目
    {
      key: '/admin/search-benchmark',
      label: '搜尋跑分系統',
      onClick: () => navigate('/admin/search-benchmark'),
    },
  ],
}
```

**路由配置**: `frontend/src/App.js`

**預期成果**: 可從側邊欄訪問跑分系統 ✅

---

### Week 7-8 驗收標準 ✅

- [ ] 4 個 ViewSets 全部實作完成
- [ ] API 端點測試通過
- [ ] 版本列表頁面可正常顯示
- [ ] 側邊欄選單整合完成
- [ ] 基本操作流程可用（查看版本、執行測試）

---

## 🔴 Phase 5: 進階功能與視覺化 (Week 9-10)

**目標**: 完善功能和使用者體驗

### Week 9: 測試執行與結果頁面

#### 任務 5.1: 測試執行對話框 (P1)

**任務清單**:
- ✅ 執行測試 Modal
- ✅ 參數選擇（類別、難度）
- ✅ 執行名稱輸入
- ✅ 進度顯示

#### 任務 5.2: 測試結果詳細頁 (P1)

**任務清單**:
- ✅ 總體評分展示
- ✅ 各項指標圖表
- ✅ 分類別表現統計
- ✅ 失敗案例列表

---

### Week 10: 視覺化與對比

#### 任務 5.3: 版本對比功能 (P2)

**任務清單**:
- ✅ 選擇兩個版本對比
- ✅ 雷達圖展示
- ✅ 指標差異計算
- ✅ 改善/退步分析

#### 任務 5.4: 圖表整合 (P2)

**技術選擇**: Recharts 或 ECharts

**任務清單**:
- ✅ 折線圖（趨勢分析）
- ✅ 雷達圖（多維度對比）
- ✅ 長條圖（分類表現）
- ✅ 環形圖（通過率）

---

### Week 9-10 驗收標準 ✅

- [ ] 測試執行流程完整
- [ ] 結果詳細頁面完成
- [ ] 版本對比功能可用
- [ ] 至少 3 種圖表正常顯示
- [ ] 使用者體驗流暢

---

## ⚫ Phase 6: 版本管理系統整合 (Week 11-12)

**目標**: 整合搜尋演算法版本管理功能

### Week 11: 版本配置儲存

#### 任務 6.1: 擴展 SearchAlgorithmVersion Model (P1)

**任務清單**:
- ✅ 添加 JSONB 配置欄位
  - `router_config` (Mode A/B 設定)
  - `search_config` (top_k, thresholds)
  - `weight_config` (title/content weights)
  - `dify_config` (API settings)
- ✅ 版本狀態管理（draft, testing, production, deprecated）

---

### Week 12: 版本切換功能

#### 任務 6.2: 實作 SearchVersionManager (P1)

**檔案**: `backend/library/search_version/version_manager.py`

**任務清單**:
- ✅ 版本 CRUD 操作
- ✅ 版本切換邏輯
- ✅ 配置載入和應用
- ✅ 版本切換日誌

#### 任務 6.3: 前端版本管理頁面 (P2)

**任務清單**:
- ✅ 版本配置編輯器
- ✅ 一鍵切換版本
- ✅ 版本對比工具
- ✅ 版本歷史記錄

---

### Week 11-12 驗收標準 ✅

- [ ] 版本配置可完整儲存
- [ ] 版本切換功能正常
- [ ] 新版本不影響舊版本測試結果
- [ ] 版本管理介面完成
- [ ] A/B 測試基礎架構就緒

---

## 🎯 完成標準總覽

### 🔵 Phase 1-2: 基礎建設 (Week 1-4)

**核心成果**:
- ✅ 5 張資料表 + 5 個 Models
- ✅ 100 題測試題目
- ✅ 半自動題目生成工具

**可交付**:
- 資料庫完整
- 題庫可用
- 為後續開發奠定基礎

---

### 🟢 Phase 3-4: 核心功能 (Week 5-8)

**核心成果**:
- ✅ 評分引擎完整
- ✅ 測試執行引擎
- ✅ 基本 Web 介面

**可交付**:
- 可執行完整跑分測試
- 可查看測試結果
- 基本功能可用

---

### 🟡 Phase 5-6: 完善系統 (Week 9-12)

**核心成果**:
- ✅ 進階視覺化
- ✅ 版本管理整合
- ✅ 完整使用者體驗

**可交付**:
- 生產環境可用
- 完整功能覆蓋
- 可持續運營

---

## 📊 資源與時間估算

### 人力需求

| 階段 | 後端開發 | 前端開發 | QA 測試 | 總計工時 |
|-----|---------|---------|---------|---------|
| Phase 1-2 | 60h | 0h | 20h | 80h |
| Phase 3-4 | 40h | 40h | 20h | 100h |
| Phase 5-6 | 20h | 40h | 20h | 80h |
| **總計** | **120h** | **80h** | **60h** | **260h** |

### 時間軸

```
Week 1-2   [████████████] Phase 1: 資料庫 + Models
Week 3-4   [████████████] Phase 2: 測試題庫
Week 5-6   [████████████] Phase 3: 評分引擎
Week 7-8   [████████████] Phase 4: API + 基礎頁面
Week 9-10  [██████      ] Phase 5: 進階功能 (可選)
Week 11-12 [████        ] Phase 6: 版本管理 (可選)
```

---

## 🚀 快速啟動指南

### MVP 最小可行版本 (6 週)

**只實作 Phase 1-4**，可達成：
- ✅ 完整的跑分系統
- ✅ 100 題測試題庫
- ✅ 基本 Web 介面
- ✅ 可量化搜尋品質

**跳過內容**:
- ⏭️ 進階視覺化（Phase 5）
- ⏭️ 版本管理整合（Phase 6）
- ⏭️ CI/CD 整合
- ⏭️ A/B 測試

**適用場景**: 快速驗證概念，盡早獲得搜尋品質數據

---

### 完整版本 (10-12 週)

**實作 Phase 1-6**，可達成：
- ✅ 完整跑分系統
- ✅ 150+ 題測試題庫
- ✅ 完整 Web 介面
- ✅ 多版本管理
- ✅ 視覺化對比
- ✅ 生產環境就緒

**適用場景**: 長期使用，持續改進搜尋演算法

---

## 📝 風險與應對

### 風險 1: 題目品質不足

**表現**: 驗證通過率 < 70%

**應對**:
1. 人工審核前 50 題
2. 調整搜尋閾值
3. 優化題目描述

### 風險 2: 測試執行太慢

**表現**: 100 題測試 > 10 分鐘

**應對**:
1. 實作並行執行（Celery）
2. 增加快取機制
3. 優化搜尋演算法

### 風險 3: 前端開發延遲

**表現**: Phase 4 超時

**應對**:
1. 優先使用 Django Admin
2. 簡化 UI 設計
3. 使用現有組件庫

---

## 🎉 總結

### 關鍵里程碑

| 週次 | 里程碑 | 可交付成果 |
|-----|-------|-----------|
| Week 2 | 資料庫就緒 | 可手動創建測試資料 |
| Week 4 | 題庫完成 | 100 題可用測試題目 |
| Week 6 | 核心功能 | 可執行完整跑分測試 |
| Week 8 | 基礎介面 | 可透過 Web 管理 |
| Week 10 | 進階功能 | 視覺化對比可用 |
| Week 12 | 系統完善 | 生產環境就緒 |

### 成功指標

**Phase 1-4 完成後**:
- ✅ 可執行 100 題測試（< 5 分鐘）
- ✅ 測試通過率 >= 70%
- ✅ 可透過 Web 介面管理
- ✅ 有至少 1 個 baseline 版本

**Phase 5-6 完成後**:
- ✅ 支援多版本並存
- ✅ 視覺化對比功能完整
- ✅ 可一鍵切換版本
- ✅ 測試題庫 >= 150 題

---

**📅 計劃制定日期**: 2025-11-21  
**📝 版本**: v1.0  
**✍️ 作者**: AI Platform Team  
**🎯 目標**: 建立可持續改進的搜尋品質評估體系
