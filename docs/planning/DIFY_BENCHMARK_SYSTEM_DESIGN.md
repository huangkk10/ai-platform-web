# 📊 Dify API 跑分系統完整設計規劃

## 📅 規劃日期
- **創建日期**: 2025-11-23
- **規劃階段**: 架構設計與需求分析
- **執行狀態**: 待執行

---

## 🎯 系統目標

創建一個**獨立的 Dify API 跑分系統**，用於評估不同版本的 Dify 配置（提示詞、RAG 設置、模型參數等）在相同測試案例下的表現。

### 核心需求
1. ✅ **版本管理**: 支援多個 Dify 配置版本（提示詞版本、RAG 參數版本等）
2. ✅ **批量測試**: 自動執行所有測試案例，評估每個版本的表現
3. ✅ **結果對比**: 提供版本間的詳細對比分析
4. ✅ **答案評分**: 使用 AI 或規則評估 Dify 回答的品質
5. ✅ **獨立性**: 與現有 Benchmark 測試系統完全隔離，互不影響

---

## 🏗️ 系統架構概覽

### 系統分層
```
┌─────────────────────────────────────────────────────────┐
│                    前端層 (React)                         │
├─────────────────────────────────────────────────────────┤
│  • DifyBenchmarkDashboard        (儀表板)                │
│  • DifyVersionManagementPage     (版本管理)              │
│  • DifyBatchTestExecutionPage    (批量測試執行)          │
│  • DifyBatchComparisonPage       (版本對比分析)          │
│  • DifyTestHistoryPage           (測試歷史記錄)          │
│  • DifyTestCaseDetailPage        (答案詳細查看)          │
└─────────────────────────────────────────────────────────┘
                            ↕ REST API
┌─────────────────────────────────────────────────────────┐
│                    API 層 (Django REST)                   │
├─────────────────────────────────────────────────────────┤
│  • DifyConfigVersionViewSet      (版本 CRUD)             │
│  • DifyBenchmarkTestCaseViewSet  (測試案例管理)          │
│  • DifyTestExecutionViewSet      (測試執行)              │
│  • DifyBatchTestViewSet          (批量測試)              │
│  • DifyComparisonViewSet         (結果對比)              │
└─────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────┐
│                  業務邏輯層 (Library)                     │
├─────────────────────────────────────────────────────────┤
│  library/dify_benchmark/                                 │
│    ├── dify_batch_tester.py      (批量測試器)           │
│    ├── dify_test_runner.py       (單次測試執行)         │
│    ├── dify_answer_evaluator.py  (答案評分器)           │
│    ├── dify_version_manager.py   (版本管理器)           │
│    └── dify_comparison_engine.py (對比分析引擎)         │
└─────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────┐
│                  資料層 (PostgreSQL)                      │
├─────────────────────────────────────────────────────────┤
│  • dify_config_version           (Dify 配置版本)        │
│  • dify_benchmark_test_case      (測試案例)             │
│  • dify_test_run                 (測試執行記錄)          │
│  • dify_test_result              (單題測試結果)          │
│  • dify_answer_evaluation        (答案評分記錄)          │
└─────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────┐
│                 外部服務 (Dify API)                       │
├─────────────────────────────────────────────────────────┤
│  • Dify Chat API (http://10.10.172.37/v1/chat-messages) │
│  • 動態切換不同配置版本的 Dify App                        │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 資料庫設計

### 1. `dify_config_version` - Dify 配置版本表
儲存不同的 Dify 配置版本（提示詞、RAG 設置等）

```sql
CREATE TABLE dify_config_version (
    id SERIAL PRIMARY KEY,
    version_name VARCHAR(200) NOT NULL UNIQUE,        -- 版本名稱 (如 "Protocol Assistant v1.0")
    description TEXT,                                 -- 版本描述
    
    -- Dify 配置資訊
    dify_app_id VARCHAR(100),                        -- Dify App ID
    dify_api_key VARCHAR(200),                       -- Dify API Key (加密儲存)
    dify_api_url VARCHAR(500),                       -- Dify API URL
    
    -- 配置內容 (JSON)
    system_prompt TEXT,                              -- 系統提示詞
    rag_settings JSONB,                              -- RAG 設置 (top_k, score_threshold 等)
    model_config JSONB,                              -- 模型配置 (temperature, max_tokens 等)
    
    -- 額外配置
    retrieval_mode VARCHAR(50),                      -- 檢索模式 (如 'two_stage')
    custom_config JSONB,                             -- 自訂配置
    
    -- 版本管理
    is_active BOOLEAN DEFAULT true,                  -- 是否啟用
    is_baseline BOOLEAN DEFAULT false,               -- 是否為基準版本
    created_by_id INTEGER REFERENCES auth_user(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_version_name UNIQUE (version_name)
);

-- 索引
CREATE INDEX idx_dify_config_version_active ON dify_config_version(is_active);
CREATE INDEX idx_dify_config_version_baseline ON dify_config_version(is_baseline);
```

**範例資料**:
```json
{
  "version_name": "Protocol Assistant 二階搜尋 v1.0",
  "description": "使用二階搜尋策略，先章節後文檔",
  "dify_app_id": "protocol-assistant-v1",
  "system_prompt": "你是 Protocol 測試專家...",
  "rag_settings": {
    "top_k_stage1": 20,
    "top_k_stage2": 10,
    "score_threshold": 0.7
  },
  "model_config": {
    "temperature": 0.2,
    "max_tokens": 4000
  },
  "retrieval_mode": "two_stage",
  "is_active": true
}
```

---

### 2. `dify_benchmark_test_case` - Dify 測試案例表
儲存用於評估 Dify 的測試問題

```sql
CREATE TABLE dify_benchmark_test_case (
    id SERIAL PRIMARY KEY,
    question TEXT NOT NULL,                          -- 測試問題
    test_class_name VARCHAR(200),                    -- 測試類別 (如 "CrystalDiskMark")
    
    -- 評分標準
    expected_answer TEXT,                            -- 期望答案 (參考答案)
    answer_keywords JSONB,                           -- 必須包含的關鍵字 ["keyword1", "keyword2"]
    evaluation_criteria JSONB,                       -- 評分標準
    
    -- 測試案例屬性
    difficulty_level VARCHAR(20),                    -- easy, medium, hard
    question_type VARCHAR(50),                       -- fact, procedure, comparison 等
    max_score DECIMAL(5,2) DEFAULT 100.00,          -- 滿分
    
    -- 管理欄位
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_dify_test_case_class ON dify_benchmark_test_case(test_class_name);
CREATE INDEX idx_dify_test_case_active ON dify_benchmark_test_case(is_active);
```

**範例資料**:
```json
{
  "question": "CrystalDiskMark 測試中，Sequential Q32T1 Read 的主要用途是什麼？",
  "test_class_name": "CrystalDiskMark",
  "expected_answer": "Sequential Q32T1 Read 測試模擬多執行緒高佇列深度的連續讀取情境...",
  "answer_keywords": ["連續讀取", "佇列深度", "Q32T1", "多執行緒"],
  "evaluation_criteria": {
    "completeness": 30,
    "accuracy": 40,
    "relevance": 30
  },
  "difficulty_level": "medium",
  "question_type": "fact"
}
```

---

### 3. `dify_test_run` - Dify 測試執行記錄表
儲存每次批量測試的總體資訊

```sql
CREATE TABLE dify_test_run (
    id SERIAL PRIMARY KEY,
    version_id INTEGER REFERENCES dify_config_version(id) ON DELETE CASCADE,
    
    -- 測試資訊
    run_name VARCHAR(300),                           -- 測試名稱
    run_type VARCHAR(50) DEFAULT 'batch_comparison', -- single, batch_comparison
    batch_id VARCHAR(100),                           -- 批次 ID (關聯相同批次的測試)
    
    -- 測試統計
    total_test_cases INTEGER DEFAULT 0,              -- 總測試案例數
    passed_cases INTEGER DEFAULT 0,                  -- 通過案例數
    failed_cases INTEGER DEFAULT 0,                  -- 失敗案例數
    
    -- 評分指標
    average_score DECIMAL(5,2),                      -- 平均分數
    total_score DECIMAL(10,2),                       -- 總分數
    pass_rate DECIMAL(5,2),                          -- 通過率 (%)
    
    -- 時間統計
    total_execution_time DECIMAL(10,2),              -- 總執行時間 (秒)
    average_response_time DECIMAL(10,2),             -- 平均響應時間 (秒)
    
    -- 詳細評分
    completeness_score DECIMAL(5,2),                 -- 完整性分數
    accuracy_score DECIMAL(5,2),                     -- 準確性分數
    relevance_score DECIMAL(5,2),                    -- 相關性分數
    
    -- 管理欄位
    notes TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_dify_test_run_version ON dify_test_run(version_id);
CREATE INDEX idx_dify_test_run_batch ON dify_test_run(batch_id);
CREATE INDEX idx_dify_test_run_created ON dify_test_run(created_at);
```

---

### 4. `dify_test_result` - Dify 單題測試結果表
儲存每個測試案例的詳細結果

```sql
CREATE TABLE dify_test_result (
    id SERIAL PRIMARY KEY,
    test_run_id INTEGER REFERENCES dify_test_run(id) ON DELETE CASCADE,
    test_case_id INTEGER REFERENCES dify_benchmark_test_case(id),
    
    -- 測試結果
    dify_answer TEXT,                                -- Dify 的回答
    dify_message_id VARCHAR(200),                    -- Dify 訊息 ID
    
    -- 評分結果
    score DECIMAL(5,2),                              -- 總分
    is_passed BOOLEAN,                               -- 是否通過
    
    -- 細項評分
    completeness_score DECIMAL(5,2),                 -- 完整性分數
    accuracy_score DECIMAL(5,2),                     -- 準確性分數
    relevance_score DECIMAL(5,2),                    -- 相關性分數
    
    -- 評分詳情
    evaluation_details JSONB,                        -- 評分詳細說明
    matched_keywords JSONB,                          -- 匹配到的關鍵字
    missing_keywords JSONB,                          -- 缺失的關鍵字
    
    -- 時間統計
    response_time DECIMAL(10,3),                     -- 響應時間 (秒)
    
    -- RAG 檢索資訊
    retrieved_documents JSONB,                       -- 檢索到的文檔
    retrieval_scores JSONB,                          -- 檢索分數
    
    -- 管理欄位
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_dify_result_run ON dify_test_result(test_run_id);
CREATE INDEX idx_dify_result_case ON dify_test_result(test_case_id);
CREATE INDEX idx_dify_result_passed ON dify_test_result(is_passed);
```

---

### 5. `dify_answer_evaluation` - 答案評分記錄表
儲存 AI 評分的詳細過程（使用 GPT-4 評分）

```sql
CREATE TABLE dify_answer_evaluation (
    id SERIAL PRIMARY KEY,
    test_result_id INTEGER REFERENCES dify_test_result(id) ON DELETE CASCADE,
    
    -- 評分輸入
    question TEXT,                                   -- 問題
    expected_answer TEXT,                            -- 期望答案
    actual_answer TEXT,                              -- 實際答案
    
    -- AI 評分結果
    evaluator_model VARCHAR(100),                    -- 評分模型 (如 "gpt-4")
    evaluation_prompt TEXT,                          -- 評分提示詞
    evaluation_response TEXT,                        -- AI 評分回應
    
    -- 評分細節
    scores JSONB,                                    -- 各項分數
    feedback TEXT,                                   -- 評分反饋
    
    -- 管理欄位
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_dify_evaluation_result ON dify_answer_evaluation(test_result_id);
```

---

## 🔧 後端 Library 設計

### 目錄結構
```
backend/library/dify_benchmark/
├── __init__.py
├── dify_batch_tester.py         # 批量測試器
├── dify_test_runner.py          # 單次測試執行器
├── dify_answer_evaluator.py     # 答案評分器
├── dify_version_manager.py      # 版本管理器
├── dify_comparison_engine.py    # 對比分析引擎
└── evaluators/
    ├── __init__.py
    ├── keyword_evaluator.py     # 關鍵字評分器
    ├── ai_evaluator.py          # AI 評分器 (GPT-4)
    └── rule_based_evaluator.py  # 規則評分器
```

---

### 1. `DifyBatchTester` - 批量測試器

```python
"""Dify 批量測試器"""
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class DifyBatchTester:
    """
    Dify 批量測試器
    
    功能：
    - 執行多個版本的批量測試
    - 自動評估每個版本的表現
    - 生成對比分析報告
    """
    
    def __init__(self, verbose=False):
        self.verbose = verbose
        
    def run_batch_test(
        self,
        version_ids: Optional[List[int]] = None,
        test_case_ids: Optional[List[int]] = None,
        batch_name: str = None,
        notes: str = "",
        use_ai_evaluator: bool = True
    ) -> Dict[str, Any]:
        """
        執行批量測試
        
        Args:
            version_ids: 要測試的版本 ID 列表 (None = 全部啟用版本)
            test_case_ids: 要測試的案例 ID 列表 (None = 全部啟用案例)
            batch_name: 批次名稱
            notes: 測試備註
            use_ai_evaluator: 是否使用 AI 評分器
            
        Returns:
            {
                'success': bool,
                'batch_id': str,
                'test_runs': [...],
                'comparison': {...},
                'summary': {...}
            }
        """
        from api.models import DifyConfigVersion, DifyBenchmarkTestCase
        
        # 生成批次 ID
        batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not batch_name:
            batch_name = f"Dify 批量測試 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # 準備版本
        versions = self._prepare_versions(version_ids)
        if not versions:
            return {
                "success": False,
                "error": "沒有版本需要測試",
                "batch_id": batch_id
            }
        
        # 準備測試案例
        test_cases = self._prepare_test_cases(test_case_ids)
        if not test_cases:
            return {
                "success": False,
                "error": "沒有可用的測試案例",
                "batch_id": batch_id
            }
        
        # 執行測試
        logger.info(f"準備測試 {len(versions)} 個版本，{len(test_cases)} 個測試案例")
        test_runs = []
        test_run_ids = []
        start_time = datetime.now()
        
        for idx, version in enumerate(versions, 1):
            logger.info(f"測試版本 {idx}/{len(versions)}: {version.version_name}")
            
            try:
                test_run = self._run_single_version_test(
                    version=version,
                    test_cases=test_cases,
                    batch_id=batch_id,
                    batch_name=batch_name,
                    notes=notes,
                    use_ai_evaluator=use_ai_evaluator
                )
                test_runs.append(test_run)
                test_run_ids.append(test_run.id)
                logger.info(f"  ✅ 完成 (平均分數: {test_run.average_score})")
                
            except Exception as e:
                logger.error(f"  ❌ 失敗: {str(e)}")
        
        # 計算執行時間
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # 生成對比分析
        comparison = self._generate_comparison(test_runs)
        
        # 生成摘要
        summary = self._generate_summary(test_runs, test_cases, execution_time)
        
        return {
            "success": True,
            "batch_id": batch_id,
            "batch_name": batch_name,
            "test_runs": test_runs,
            "test_run_ids": test_run_ids,
            "comparison": comparison,
            "summary": summary
        }
    
    def _prepare_versions(self, version_ids: Optional[List[int]]) -> List:
        """準備要測試的版本"""
        from api.models import DifyConfigVersion
        
        if version_ids:
            versions = list(DifyConfigVersion.objects.filter(
                id__in=version_ids,
                is_active=True
            ))
        else:
            versions = list(DifyConfigVersion.objects.filter(is_active=True))
        
        return versions
    
    def _prepare_test_cases(self, test_case_ids: Optional[List[int]]) -> List:
        """準備測試案例"""
        from api.models import DifyBenchmarkTestCase
        
        if test_case_ids:
            test_cases = list(DifyBenchmarkTestCase.objects.filter(
                id__in=test_case_ids,
                is_active=True
            ))
        else:
            test_cases = list(DifyBenchmarkTestCase.objects.filter(is_active=True))
        
        return test_cases
    
    def _run_single_version_test(
        self,
        version,
        test_cases: List,
        batch_id: str,
        batch_name: str,
        notes: str,
        use_ai_evaluator: bool
    ):
        """執行單個版本的測試"""
        from library.dify_benchmark.dify_test_runner import DifyTestRunner
        
        runner = DifyTestRunner(
            version=version,
            use_ai_evaluator=use_ai_evaluator,
            verbose=self.verbose
        )
        
        run_name = f"{batch_name} - {version.version_name}"
        run_notes = f"批次 ID: {batch_id}\n{notes}"
        
        return runner.run_batch_tests(
            test_cases=test_cases,
            run_name=run_name,
            run_type="batch_comparison",
            batch_id=batch_id,
            notes=run_notes
        )
    
    def _generate_comparison(self, test_runs: List) -> Dict[str, Any]:
        """生成對比分析"""
        versions_data = []
        
        for tr in test_runs:
            versions_data.append({
                "version_id": tr.version.id,
                "version_name": tr.version.version_name,
                "average_score": float(tr.average_score or 0),
                "pass_rate": float(tr.pass_rate or 0),
                "completeness_score": float(tr.completeness_score or 0),
                "accuracy_score": float(tr.accuracy_score or 0),
                "relevance_score": float(tr.relevance_score or 0),
                "average_response_time": float(tr.average_response_time or 0)
            })
        
        # 排名
        ranking = {
            "by_average_score": sorted(
                versions_data,
                key=lambda x: x["average_score"],
                reverse=True
            ),
            "by_pass_rate": sorted(
                versions_data,
                key=lambda x: x["pass_rate"],
                reverse=True
            )
        }
        
        return {
            "versions": versions_data,
            "ranking": ranking,
            "best_version": ranking["by_average_score"][0] if ranking["by_average_score"] else None
        }
    
    def _generate_summary(
        self,
        test_runs: List,
        test_cases: List,
        execution_time: float
    ) -> Dict[str, Any]:
        """生成測試摘要"""
        return {
            "total_versions_tested": len(test_runs),
            "total_test_cases": len(test_cases),
            "total_tests_executed": len(test_runs) * len(test_cases),
            "execution_time": execution_time
        }
```

---

### 2. `DifyTestRunner` - 測試執行器

```python
"""Dify 測試執行器"""
from datetime import datetime
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class DifyTestRunner:
    """
    Dify 測試執行器
    
    功能：
    - 執行單個版本的所有測試案例
    - 呼叫 Dify API 獲取答案
    - 使用評分器評估答案品質
    """
    
    def __init__(self, version, use_ai_evaluator=True, verbose=False):
        """
        Args:
            version: DifyConfigVersion 實例
            use_ai_evaluator: 是否使用 AI 評分器
            verbose: 是否輸出詳細日誌
        """
        self.version = version
        self.use_ai_evaluator = use_ai_evaluator
        self.verbose = verbose
        
        # 初始化評分器
        self._init_evaluators()
    
    def _init_evaluators(self):
        """初始化評分器"""
        from library.dify_benchmark.evaluators.keyword_evaluator import KeywordEvaluator
        from library.dify_benchmark.evaluators.ai_evaluator import AIEvaluator
        
        self.keyword_evaluator = KeywordEvaluator()
        
        if self.use_ai_evaluator:
            self.ai_evaluator = AIEvaluator()
        else:
            self.ai_evaluator = None
    
    def run_batch_tests(
        self,
        test_cases: List,
        run_name: str,
        run_type: str = "batch_comparison",
        batch_id: str = None,
        notes: str = ""
    ):
        """
        執行批量測試
        
        Returns:
            DifyTestRun 實例
        """
        from api.models import DifyTestRun, DifyTestResult
        
        # 創建測試記錄
        test_run = DifyTestRun.objects.create(
            version=self.version,
            run_name=run_name,
            run_type=run_type,
            batch_id=batch_id,
            notes=notes,
            total_test_cases=len(test_cases),
            started_at=datetime.now()
        )
        
        logger.info(f"開始測試 {self.version.version_name}, Test Run ID: {test_run.id}")
        
        # 執行每個測試案例
        passed_count = 0
        total_score = 0
        total_response_time = 0
        completeness_scores = []
        accuracy_scores = []
        relevance_scores = []
        
        for idx, test_case in enumerate(test_cases, 1):
            logger.info(f"  測試案例 {idx}/{len(test_cases)}: {test_case.question[:50]}...")
            
            try:
                # 執行單個測試
                result = self._run_single_test(test_run, test_case)
                
                # 累計統計
                if result.is_passed:
                    passed_count += 1
                
                total_score += result.score
                total_response_time += result.response_time
                
                completeness_scores.append(result.completeness_score)
                accuracy_scores.append(result.accuracy_score)
                relevance_scores.append(result.relevance_score)
                
                logger.info(f"    ✅ 分數: {result.score:.2f}, 通過: {result.is_passed}")
                
            except Exception as e:
                logger.error(f"    ❌ 測試失敗: {str(e)}")
        
        # 更新測試記錄
        test_run.passed_cases = passed_count
        test_run.failed_cases = len(test_cases) - passed_count
        test_run.average_score = total_score / len(test_cases) if test_cases else 0
        test_run.total_score = total_score
        test_run.pass_rate = (passed_count / len(test_cases) * 100) if test_cases else 0
        test_run.average_response_time = total_response_time / len(test_cases) if test_cases else 0
        
        # 計算細項平均分數
        test_run.completeness_score = sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0
        test_run.accuracy_score = sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else 0
        test_run.relevance_score = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0
        
        test_run.completed_at = datetime.now()
        test_run.total_execution_time = (test_run.completed_at - test_run.started_at).total_seconds()
        test_run.save()
        
        logger.info(f"測試完成: 平均分數={test_run.average_score:.2f}, 通過率={test_run.pass_rate:.2f}%")
        
        return test_run
    
    def _run_single_test(self, test_run, test_case):
        """執行單個測試案例"""
        from api.models import DifyTestResult
        from library.dify_integration.request_manager import DifyRequestManager
        import time
        
        # 1. 呼叫 Dify API
        start_time = time.time()
        
        request_manager = DifyRequestManager(
            api_url=self.version.dify_api_url,
            api_key=self.version.dify_api_key
        )
        
        # 發送問題到 Dify
        response = request_manager.send_chat_request(
            query=test_case.question,
            user_id=f"benchmark_test_{test_run.id}",
            conversation_id=None
        )
        
        response_time = time.time() - start_time
        
        if not response['success']:
            raise Exception(f"Dify API 調用失敗: {response.get('error')}")
        
        dify_answer = response['answer']
        dify_message_id = response.get('message_id')
        
        # 2. 評估答案
        evaluation = self._evaluate_answer(test_case, dify_answer)
        
        # 3. 儲存結果
        test_result = DifyTestResult.objects.create(
            test_run=test_run,
            test_case=test_case,
            dify_answer=dify_answer,
            dify_message_id=dify_message_id,
            score=evaluation['score'],
            is_passed=evaluation['is_passed'],
            completeness_score=evaluation['completeness_score'],
            accuracy_score=evaluation['accuracy_score'],
            relevance_score=evaluation['relevance_score'],
            evaluation_details=evaluation['details'],
            matched_keywords=evaluation.get('matched_keywords'),
            missing_keywords=evaluation.get('missing_keywords'),
            response_time=response_time,
            retrieved_documents=response.get('retrieved_documents'),
            retrieval_scores=response.get('retrieval_scores')
        )
        
        return test_result
    
    def _evaluate_answer(self, test_case, dify_answer: str) -> Dict[str, Any]:
        """評估答案"""
        # 關鍵字評分
        keyword_result = self.keyword_evaluator.evaluate(
            question=test_case.question,
            expected_answer=test_case.expected_answer,
            actual_answer=dify_answer,
            keywords=test_case.answer_keywords
        )
        
        # AI 評分 (如果啟用)
        if self.ai_evaluator:
            ai_result = self.ai_evaluator.evaluate(
                question=test_case.question,
                expected_answer=test_case.expected_answer,
                actual_answer=dify_answer,
                criteria=test_case.evaluation_criteria
            )
            
            # 綜合評分 (關鍵字 40% + AI 評分 60%)
            final_score = keyword_result['score'] * 0.4 + ai_result['score'] * 0.6
            
            evaluation = {
                'score': final_score,
                'is_passed': final_score >= 60,  # 60 分及格
                'completeness_score': ai_result['completeness_score'],
                'accuracy_score': ai_result['accuracy_score'],
                'relevance_score': ai_result['relevance_score'],
                'matched_keywords': keyword_result['matched_keywords'],
                'missing_keywords': keyword_result['missing_keywords'],
                'details': {
                    'keyword_evaluation': keyword_result,
                    'ai_evaluation': ai_result
                }
            }
        else:
            # 只使用關鍵字評分
            evaluation = {
                'score': keyword_result['score'],
                'is_passed': keyword_result['score'] >= 60,
                'completeness_score': keyword_result['score'],
                'accuracy_score': keyword_result['score'],
                'relevance_score': keyword_result['score'],
                'matched_keywords': keyword_result['matched_keywords'],
                'missing_keywords': keyword_result['missing_keywords'],
                'details': {
                    'keyword_evaluation': keyword_result
                }
            }
        
        return evaluation
```

---

## 🎨 前端設計

### 側邊欄選單結構
```javascript
// frontend/src/components/Sidebar.js

{
  key: 'dify-benchmark',
  icon: <RocketOutlined />,
  label: 'Dify 跑分',
  children: [
    {
      key: '/dify-benchmark/dashboard',
      label: 'Dashboard',
      onClick: () => navigate('/dify-benchmark/dashboard'),
    },
    {
      key: '/dify-benchmark/versions',
      label: '版本管理',
      onClick: () => navigate('/dify-benchmark/versions'),
    },
    {
      key: '/dify-benchmark/test-cases',
      label: '測試案例',
      onClick: () => navigate('/dify-benchmark/test-cases'),
    },
    {
      key: '/dify-benchmark/batch-test',
      label: '批量測試',
      onClick: () => navigate('/dify-benchmark/batch-test'),
    },
    {
      key: '/dify-benchmark/history',
      label: '測試歷史',
      onClick: () => navigate('/dify-benchmark/history'),
    }
  ],
}
```

---

### 前端頁面列表

#### 1. **DifyBenchmarkDashboard** - 儀表板
- **路由**: `/dify-benchmark/dashboard`
- **功能**:
  - 顯示總體統計數據
  - 版本效能對比圖表
  - 最近測試記錄
  - 快捷操作按鈕

#### 2. **DifyVersionManagementPage** - 版本管理
- **路由**: `/dify-benchmark/versions`
- **功能**:
  - 版本 CRUD 操作
  - 配置編輯器 (JSON 格式)
  - 設定基準版本
  - 啟用/停用版本

#### 3. **DifyBatchTestExecutionPage** - 批量測試執行
- **路由**: `/dify-benchmark/batch-test`
- **功能**:
  - 選擇版本（支援多選）
  - 選擇測試案例（支援多選）
  - 執行測試
  - 即時進度顯示
  - 完成後自動跳轉到對比頁面

#### 4. **DifyBatchComparisonPage** - 版本對比分析
- **路由**: `/dify-benchmark/comparison/:batchId`
- **功能**:
  - 版本效能對比表格
  - 雷達圖 (完整性、準確性、相關性)
  - 測試案例詳細表現表格
  - 答案查看（點擊查看每題的詳細答案）
  - 匯出報告

#### 5. **DifyTestHistoryPage** - 測試歷史記錄
- **路由**: `/dify-benchmark/history`
- **功能**:
  - 歷史測試記錄列表
  - 按 batch_id 搜尋
  - 快速跳轉到對比頁面
  - 刪除舊記錄

#### 6. **DifyTestCaseManagementPage** - 測試案例管理
- **路由**: `/dify-benchmark/test-cases`
- **功能**:
  - 測試案例 CRUD
  - 匯入/匯出測試案例
  - 設定評分標準
  - 預覽測試案例

---

## 📡 API 端點設計

### 1. 版本管理 API
```python
# DifyConfigVersionViewSet
GET    /api/dify-benchmark/versions/           # 列出所有版本
POST   /api/dify-benchmark/versions/           # 創建新版本
GET    /api/dify-benchmark/versions/:id/       # 獲取版本詳情
PUT    /api/dify-benchmark/versions/:id/       # 更新版本
DELETE /api/dify-benchmark/versions/:id/       # 刪除版本
POST   /api/dify-benchmark/versions/:id/set_baseline/  # 設定為基準版本
```

### 2. 測試案例 API
```python
# DifyBenchmarkTestCaseViewSet
GET    /api/dify-benchmark/test-cases/         # 列出所有測試案例
POST   /api/dify-benchmark/test-cases/         # 創建新測試案例
GET    /api/dify-benchmark/test-cases/:id/     # 獲取案例詳情
PUT    /api/dify-benchmark/test-cases/:id/     # 更新案例
DELETE /api/dify-benchmark/test-cases/:id/     # 刪除案例
```

### 3. 批量測試 API
```python
# DifyBatchTestViewSet
POST   /api/dify-benchmark/batch-test/execute/ # 執行批量測試
GET    /api/dify-benchmark/batch-test/status/:batchId/  # 獲取測試狀態
```

### 4. 測試結果 API
```python
# DifyTestResultViewSet
GET    /api/dify-benchmark/test-runs/          # 列出所有測試記錄
GET    /api/dify-benchmark/test-runs/:id/      # 獲取測試詳情
GET    /api/dify-benchmark/test-runs/:id/results/  # 獲取測試結果
```

### 5. 對比分析 API
```python
# DifyComparisonViewSet
GET    /api/dify-benchmark/comparison/:batchId/  # 獲取批次對比資料
POST   /api/dify-benchmark/comparison/export/    # 匯出對比報告
```

---

## 🔗 與現有系統的關係

### 完全獨立設計

| 項目 | Benchmark 測試系統 | Dify 跑分系統 | 是否隔離 |
|------|-------------------|--------------|---------|
| **資料表** | `search_algorithm_version`, `benchmark_test_case`, `benchmark_test_run` 等 | `dify_config_version`, `dify_benchmark_test_case`, `dify_test_run` 等 | ✅ 完全隔離 |
| **API 路由** | `/api/benchmark/*` | `/api/dify-benchmark/*` | ✅ 完全隔離 |
| **前端路由** | `/benchmark/*` | `/dify-benchmark/*` | ✅ 完全隔離 |
| **Library** | `library/benchmark/` | `library/dify_benchmark/` | ✅ 完全隔離 |
| **測試對象** | 搜尋演算法版本（Protocol 搜尋系統） | Dify 配置版本（Dify API） | ✅ 完全獨立 |
| **測試案例** | 可共用相同的測試問題 | 可複製 Benchmark 的測試案例 | ⚠️ 可選共用 |

### 可選的資料共用
雖然系統完全獨立，但可以選擇性地共用測試案例：

```python
# 選項 1: 完全獨立（推薦）
dify_benchmark_test_case  # 獨立的測試案例表

# 選項 2: 共用測試案例（未來擴展）
# 可以從 benchmark_test_case 複製測試問題
# 但評分標準可能不同（搜尋 vs. 回答品質）
```

---

## 🎯 核心差異對比

### Benchmark 測試系統 vs. Dify 跑分系統

| 維度 | Benchmark 測試系統 | Dify 跑分系統 |
|------|-------------------|--------------|
| **測試對象** | Protocol 搜尋演算法版本 | Dify 配置版本（提示詞、RAG 設置） |
| **測試方式** | 直接查詢 PostgreSQL + pgvector | 呼叫 Dify Chat API |
| **評分標準** | Precision, Recall, F1 Score | 答案品質評分（完整性、準確性、相關性） |
| **評分方法** | 比對檢索結果與期望文檔 ID | 關鍵字匹配 + AI 評分 (GPT-4) |
| **測試目標** | 搜尋準確度、召回率 | 回答品質、用戶滿意度 |
| **RAG 檢索** | 直接測試搜尋演算法 | 透過 Dify 的 RAG 系統 |

---

## 📝 實作步驟規劃

### Phase 1: 資料庫與 Models (1-2 天)
1. ✅ 創建資料庫表 (5 個表)
2. ✅ 創建 Django Models
3. ✅ 執行 Migration
4. ✅ 創建測試資料

### Phase 2: 後端 Library (2-3 天)
1. ✅ 實作 `DifyBatchTester`
2. ✅ 實作 `DifyTestRunner`
3. ✅ 實作 `KeywordEvaluator`
4. ✅ 實作 `AIEvaluator` (可選)
5. ✅ 測試 Library 功能

### Phase 3: API 層 (2-3 天)
1. ✅ 實作 ViewSets (5 個)
2. ✅ 註冊 URL 路由
3. ✅ 測試 API 端點
4. ✅ API 文檔

### Phase 4: 前端頁面 (3-4 天)
1. ✅ 創建 6 個頁面組件
2. ✅ 實作 API 客戶端
3. ✅ 添加路由配置
4. ✅ 更新側邊欄選單
5. ✅ 測試前端功能

### Phase 5: 整合測試 (1-2 天)
1. ✅ 端到端測試
2. ✅ 效能測試
3. ✅ 修復 Bug
4. ✅ 文檔完善

**預計總時間**: 10-15 天

---

## 🎨 UI 設計參考

### 版本對比頁面 (Radar Chart)
```
┌────────────────────────────────────────────────────────┐
│  版本效能對比                                            │
├────────────────────────────────────────────────────────┤
│                                                         │
│        完整性                                           │
│         ▲                                              │
│        ╱ ╲                                             │
│       ╱   ╲                                            │
│  相關性 ─────── 準確性                                  │
│       ╲   ╱                                            │
│        ╲ ╱                                             │
│         ▼                                              │
│      響應時間                                           │
│                                                         │
│  圖例:                                                  │
│  ━━━ Protocol Assistant 二階搜尋 v1.0                   │
│  ─ ─ Protocol Assistant 單階搜尋 v1.0                   │
│  ⋯⋯⋯ Protocol Assistant 優化版 v2.0                    │
└────────────────────────────────────────────────────────┘
```

### 測試案例詳細表現表格
```
┌───────────────────────────────────────────────────────────────────────────┐
│  測試案例詳細表現                                                           │
├─────┬──────────────────┬─────────┬─────────┬─────────┬─────────┬─────────┤
│ #   │ 問題             │ v1.0    │ v2.0    │ v3.0    │ 難度    │ 操作     │
├─────┼──────────────────┼─────────┼─────────┼─────────┼─────────┼─────────┤
│ 1   │ CrystalDisk...   │ 85.5 ✅ │ 92.3 ✅ │ 78.2 ❌ │ 中等    │ [查看]  │
│ 2   │ UNH-IOL...       │ 72.1 ❌ │ 88.7 ✅ │ 95.4 ✅ │ 困難    │ [查看]  │
│ 3   │ I3C 測試...      │ 90.2 ✅ │ 85.6 ✅ │ 89.9 ✅ │ 簡單    │ [查看]  │
└─────┴──────────────────┴─────────┴─────────┴─────────┴─────────┴─────────┘
```

---

## 🔐 安全考量

### API Key 安全
1. **加密儲存**: Dify API Key 使用 Django 的加密欄位儲存
2. **環境變數**: 敏感資訊從環境變數讀取
3. **權限控制**: 只有管理員可以查看完整的 API Key

### 權限設計
```python
# UserProfile 新增權限欄位
dify_benchmark_access = models.BooleanField(
    default=False,
    verbose_name="Dify 跑分系統權限"
)
dify_benchmark_admin = models.BooleanField(
    default=False,
    verbose_name="Dify 跑分系統管理員"
)
```

---

## 📊 效能考量

### 批量測試優化
1. **非同步執行**: 使用 Celery 非同步執行批量測試
2. **進度追蹤**: WebSocket 即時推送測試進度
3. **結果快取**: 快取測試結果，避免重複計算
4. **資料庫索引**: 在關鍵欄位建立索引

### Dify API 調用優化
1. **重試機制**: API 調用失敗自動重試
2. **超時控制**: 設定合理的超時時間
3. **速率限制**: 避免頻繁調用 Dify API
4. **連接池**: 複用 HTTP 連接

---

## 🧪 測試策略

### 單元測試
- Library 層函數測試
- 評分器測試
- API 端點測試

### 整合測試
- Dify API 調用測試
- 資料庫操作測試
- 前後端整合測試

### 端到端測試
- 完整的批量測試流程
- 版本對比功能
- 答案查看功能

---

## 📚 文檔規劃

### 開發文檔
- `docs/planning/DIFY_BENCHMARK_SYSTEM_DESIGN.md` (本文檔)
- `docs/development/DIFY_BENCHMARK_API_REFERENCE.md`
- `docs/development/DIFY_BENCHMARK_LIBRARY_GUIDE.md`

### 測試文檔
- `docs/testing/DIFY_BENCHMARK_TESTING_GUIDE.md`
- `docs/testing/DIFY_BENCHMARK_TEST_CASES.md`

### 用戶文檔
- `docs/user-guide/DIFY_BENCHMARK_USER_MANUAL.md`
- `docs/user-guide/DIFY_BENCHMARK_QUICK_START.md`

---

## ✅ 驗收標準

### 功能完整性
- [ ] 版本管理功能正常（CRUD）
- [ ] 測試案例管理功能正常（CRUD）
- [ ] 批量測試執行功能正常
- [ ] 版本對比分析功能正常
- [ ] 測試歷史查詢功能正常
- [ ] 答案詳細查看功能正常

### 資料正確性
- [ ] 評分結果準確
- [ ] 統計數據正確
- [ ] 對比分析合理
- [ ] 資料持久化正常

### 效能要求
- [ ] 批量測試 10 個版本 × 50 題 < 10 分鐘
- [ ] API 響應時間 < 2 秒
- [ ] 頁面載入時間 < 1 秒
- [ ] 資料庫查詢優化

### 用戶體驗
- [ ] UI 設計美觀
- [ ] 操作流程順暢
- [ ] 錯誤提示清晰
- [ ] 響應式設計

---

## 🎯 後續擴展計劃

### Phase 2 功能（未來）
1. **進階評分**:
   - 使用 GPT-4 進行語義評分
   - 多維度評分（完整性、準確性、相關性、語言流暢度）
   - 自訂評分規則

2. **A/B 測試**:
   - 支援兩個版本的 A/B 對比測試
   - 統計顯著性檢驗
   - 自動選出最佳版本

3. **持續監控**:
   - 定期自動執行測試
   - 效能趨勢分析
   - 異常告警

4. **測試報告**:
   - 自動生成 PDF/Excel 報告
   - 圖表可視化
   - 分享報告連結

5. **多 Dify App 支援**:
   - 支援多個不同的 Dify App
   - 跨 App 效能對比
   - 統一測試標準

---

## 📋 總結

### 系統特點
1. ✅ **完全獨立**: 與 Benchmark 測試系統完全隔離
2. ✅ **易於擴展**: 模組化設計，易於添加新功能
3. ✅ **通用性強**: 可用於任何 Dify App 的評估
4. ✅ **評分客觀**: 結合關鍵字匹配和 AI 評分
5. ✅ **操作簡便**: 與 Benchmark 系統相似的 UI

### 預期效益
1. **版本選擇**: 客觀評估不同 Dify 配置的效果
2. **持續優化**: 追蹤優化效果，確保改進方向正確
3. **品質保證**: 確保 Dify 回答品質符合標準
4. **效能監控**: 監控 Dify 效能變化趨勢

### 開發建議
1. **先做 MVP**: 先實作基本功能，後續再擴展
2. **參考現有**: 大量複用 Benchmark 系統的代碼和設計
3. **測試驅動**: 每個階段都進行充分測試
4. **文檔同步**: 開發過程中同步更新文檔

---

**規劃完成日期**: 2025-11-23  
**規劃作者**: AI Assistant  
**審核狀態**: 待用戶確認  
**執行狀態**: 待執行 ⏳
