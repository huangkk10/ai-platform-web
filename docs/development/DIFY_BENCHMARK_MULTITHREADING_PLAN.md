# 🚀 Dify Benchmark 多線程執行架構規劃

**日期**: 2025-11-24  
**狀態**: 📋 規劃階段（未執行）  
**目標**: 將 Dify Benchmark 測試改為多線程並行執行，每次使用新的 conversation_id，且不影響 Protocol Assistant

---

## 📊 現狀分析

### 當前執行模式（順序執行）

```python
# backend/library/dify_benchmark/dify_test_runner.py
def run_batch_tests(self, test_cases, ...):
    for i, test_case in enumerate(test_cases, 1):
        # ⚠️ 順序執行：每個測試等待前一個完成
        result = self._run_single_test(test_run, test_case)
        # 統計結果...
```

**問題**：
- ⏱️ **速度慢**：10 個測試 × 3 秒 = 30 秒
- 🔄 **無法並行**：無法利用多核心 CPU
- 📈 **擴展性差**：測試案例越多，等待時間越長

### 當前 Conversation ID 管理

```python
# backend/library/dify_benchmark/dify_test_runner.py (line 215)
api_response = self.api_client.send_question(
    question=test_case.question,
    user_id=f"test_run_{test_run.id}",
    conversation_id=None  # ⚠️ 每個測試使用獨立對話
)
```

**現狀**：
- ✅ 已經使用 `conversation_id=None`（每次新對話）
- ✅ 不會污染其他測試
- ❓ 但與 Protocol Assistant 共用相同的 Dify App

---

## 🎯 改進目標

### 1. **多線程並行執行**
- 使用 Python `concurrent.futures.ThreadPoolExecutor`
- 同時執行多個測試案例（例如 5 個並行）
- 大幅減少總測試時間

### 2. **獨立 Conversation ID**
- ✅ 維持當前設計：每個測試使用新的 conversation_id
- 確保測試之間完全隔離
- 不會互相影響測試結果

### 3. **隔離 Protocol Assistant**
- ⚠️ **關鍵考量**：Dify Benchmark 與 Protocol Assistant 共用同一個 Dify App
- 需要確保 Benchmark 測試不會影響正常用戶的對話
- 使用不同的 `user_id` 前綴區分

---

## 🏗️ 架構設計

### 方案 1：ThreadPoolExecutor（推薦）✅

#### 優點
- ✅ Python 標準庫，無需額外依賴
- ✅ 簡單易實現，代碼改動小
- ✅ 適合 I/O 密集型任務（API 呼叫）
- ✅ 可控制並行數量（避免過載）

#### 實作架構

```python
# backend/library/dify_benchmark/dify_test_runner.py

import concurrent.futures
from threading import Lock

class DifyTestRunner:
    def __init__(self, version, use_ai_evaluator=False, max_workers=5):
        """
        Args:
            max_workers: 最大並行執行線程數（預設 5）
        """
        self.version = version
        self.use_ai_evaluator = use_ai_evaluator
        self.max_workers = max_workers
        self.api_client = DifyAPIClient()
        self.keyword_evaluator = KeywordEvaluator()
        
        # 線程安全的計數器
        self._lock = Lock()
        self._passed_count = 0
        self._failed_count = 0
        self._total_score = 0
    
    def run_batch_tests_parallel(
        self,
        test_cases: List[DifyBenchmarkTestCase],
        run_name: str = None,
        batch_id: str = None,
        description: str = None
    ) -> DifyTestRun:
        """
        【新方法】使用多線程並行執行測試
        
        執行流程：
        1. 創建 Test Run 記錄
        2. 使用 ThreadPoolExecutor 並行執行測試
        3. 收集並統計結果
        4. 更新 Test Run 統計
        """
        
        # 1. 創建 Test Run 記錄
        test_run = self._create_test_run(
            test_cases=test_cases,
            run_name=run_name,
            batch_id=batch_id,
            description=description
        )
        
        logger.info(
            f"開始並行測試: "
            f"run_id={test_run.id}, "
            f"version={self.version.version_name}, "
            f"total_cases={len(test_cases)}, "
            f"max_workers={self.max_workers}"
        )
        
        # 2. 使用 ThreadPoolExecutor 並行執行
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有測試任務
            future_to_case = {
                executor.submit(
                    self._run_single_test_thread_safe,
                    test_run,
                    test_case,
                    i
                ): test_case
                for i, test_case in enumerate(test_cases, 1)
            }
            
            # 等待所有任務完成
            for future in concurrent.futures.as_completed(future_to_case):
                test_case = future_to_case[future]
                try:
                    result = future.result()
                    logger.info(
                        f"測試案例完成: "
                        f"question={test_case.question[:30]}..., "
                        f"score={result.score}, "
                        f"passed={'✅' if result.is_passed else '❌'}"
                    )
                except Exception as e:
                    logger.error(
                        f"測試案例執行失敗: "
                        f"question={test_case.question[:30]}..., "
                        f"error={str(e)}"
                    )
        
        # 3. 更新 Test Run 統計
        self._update_test_run_statistics(
            test_run=test_run,
            passed_count=self._passed_count,
            failed_count=self._failed_count,
            total_score=self._total_score
        )
        
        logger.info(
            f"並行測試完成: "
            f"passed={self._passed_count}/{len(test_cases)}, "
            f"avg_score={test_run.average_score:.2f}, "
            f"pass_rate={test_run.pass_rate:.2f}%"
        )
        
        return test_run
    
    def _run_single_test_thread_safe(
        self,
        test_run: DifyTestRun,
        test_case: DifyBenchmarkTestCase,
        index: int
    ) -> DifyTestResult:
        """
        【新方法】線程安全的單個測試執行
        
        關鍵改進：
        1. 每次使用新的 conversation_id（None）
        2. 使用唯一的 user_id（包含測試編號）
        3. 線程安全的統計更新
        """
        
        # 生成唯一的 user_id（區分測試）
        unique_user_id = f"benchmark_test_{test_run.id}_{index}"
        
        logger.info(
            f"[Thread {index}] 開始測試: "
            f"question={test_case.question[:50]}..., "
            f"user_id={unique_user_id}"
        )
        
        # 1. 呼叫 Dify API（使用新 conversation_id）
        api_response = self.api_client.send_question(
            question=test_case.question,
            user_id=unique_user_id,  # ✅ 唯一 user_id
            conversation_id=None     # ✅ 每次新對話
        )
        
        # 提取資訊
        actual_answer = api_response.get('answer', '')
        response_time = api_response.get('response_time', 0)
        dify_conversation_id = api_response.get('conversation_id', '')
        dify_message_id = api_response.get('message_id', '')
        retrieved_documents = api_response.get('retrieved_documents', [])
        
        # 2. 使用 KeywordEvaluator 評分
        keywords = test_case.get_answer_keywords()
        
        evaluation_result = self.keyword_evaluator.evaluate(
            question=test_case.question,
            expected_answer=test_case.expected_answer,
            actual_answer=actual_answer,
            keywords=keywords
        )
        
        score = evaluation_result['score']
        is_passed = evaluation_result['is_passed']
        matched_keywords = evaluation_result['matched_keywords']
        missing_keywords = evaluation_result['missing_keywords']
        
        # 3. 儲存 TestResult（Django ORM 是線程安全的）
        test_result = DifyTestResult.objects.create(
            test_run=test_run,
            test_case=test_case,
            actual_answer=actual_answer,
            score=score,
            is_passed=is_passed,
            response_time=response_time,
            dify_conversation_id=dify_conversation_id,
            dify_message_id=dify_message_id,
            retrieved_documents_count=len(retrieved_documents)
        )
        
        # 4. 儲存 AnswerEvaluation
        DifyAnswerEvaluation.objects.create(
            test_result=test_result,
            evaluation_method='keyword',
            score=score,
            is_passed=is_passed,
            matched_keywords=matched_keywords,
            missing_keywords=missing_keywords
        )
        
        # 5. 線程安全地更新統計（使用 Lock）
        with self._lock:
            if is_passed:
                self._passed_count += 1
            else:
                self._failed_count += 1
            self._total_score += score
        
        logger.info(
            f"[Thread {index}] 測試完成: "
            f"score={score}, "
            f"passed={'✅' if is_passed else '❌'}, "
            f"response_time={response_time:.2f}s"
        )
        
        return test_result
```

---

### 方案 2：Celery 非同步任務（進階）

#### 優點
- ✅ 真正的非同步執行（不阻塞 API 請求）
- ✅ 支援分散式執行（多台伺服器）
- ✅ 內建任務隊列和重試機制
- ✅ 可監控任務狀態和進度

#### 缺點
- ❌ 需要安裝 Redis 或 RabbitMQ
- ❌ 架構複雜度大幅提升
- ❌ 需要管理 Celery Worker 進程
- ❌ 前端需要輪詢任務狀態

#### 實作概要（不推薦此階段）

```python
# backend/library/dify_benchmark/tasks.py

from celery import shared_task, group
from .dify_test_runner import DifyTestRunner

@shared_task(bind=True)
def run_single_test_async(self, test_run_id, test_case_id, version_id):
    """Celery 任務：執行單個測試"""
    runner = DifyTestRunner(version_id=version_id)
    result = runner._run_single_test(test_run_id, test_case_id)
    return result.id

@shared_task
def run_batch_tests_async(test_run_id, test_case_ids, version_id):
    """Celery 任務：執行批量測試"""
    # 創建任務組
    job = group(
        run_single_test_async.s(test_run_id, case_id, version_id)
        for case_id in test_case_ids
    )
    result = job.apply_async()
    return result.id
```

**評估**：暫不推薦，除非未來有以下需求：
- 測試案例數量 > 100
- 需要跨伺服器分散執行
- 需要複雜的任務調度

---

## 🔐 隔離 Protocol Assistant

### 問題分析

**Dify App 共用風險**：
```
Protocol Assistant (正常用戶)
  ↓ 呼叫相同的 Dify App
Dify Protocol Guide App
  ↑ 呼叫相同的 Dify App
Dify Benchmark (測試)
```

**潛在影響**：
1. ❌ **對話污染**：測試對話可能出現在用戶的對話歷史中
2. ❌ **RAG 干擾**：高頻測試可能影響 Dify 的 RAG 快取
3. ❌ **API 限流**：同時大量請求可能觸發 API 限制

### 隔離策略

#### 策略 1：User ID 前綴區分 ✅

```python
# Protocol Assistant (正常用戶)
user_id = f"protocol_user_{user.id}"  # 例如：protocol_user_123

# Dify Benchmark (測試)
user_id = f"benchmark_test_{test_run_id}_{index}"  # 例如：benchmark_test_42_1
```

**優點**：
- ✅ 簡單有效
- ✅ Dify 會將不同 user_id 視為不同用戶
- ✅ 對話完全隔離

#### 策略 2：使用獨立的 Dify App（未來考慮）

```python
# backend/library/config/dify_config_manager.py

DIFY_APPS = {
    'protocol_guide': {  # 正常用戶使用
        'api_key': 'app-xxx',
        'app_name': 'Protocol Guide (Production)'
    },
    'protocol_benchmark': {  # 測試專用
        'api_key': 'app-yyy',
        'app_name': 'Protocol Guide (Benchmark)'
    }
}
```

**優點**：
- ✅ 完全隔離（不同的 App，不同的知識庫）
- ✅ 可獨立調整測試 App 的配置

**缺點**：
- ❌ 需要維護兩個 App
- ❌ 需要同步知識庫內容
- ❌ 增加 Dify 配額消耗

**評估**：暫不採用，除非出現以下情況：
- 測試頻率極高（每天 > 100 次）
- 發現對話污染問題
- 需要不同的 RAG 配置

---

## 📝 實作步驟（尚未執行）

### Phase 1: 基礎多線程實作 ✅ 推薦先做

#### Step 1: 修改 DifyTestRunner
**檔案**: `backend/library/dify_benchmark/dify_test_runner.py`

**修改內容**：
1. 添加 `max_workers` 參數到 `__init__`
2. 添加線程安全的計數器（`_lock`, `_passed_count`, etc.）
3. 創建新方法 `run_batch_tests_parallel()`
4. 創建新方法 `_run_single_test_thread_safe()`
5. 保留舊方法 `run_batch_tests()` 向後兼容

#### Step 2: 修改 DifyBatchTester
**檔案**: `backend/library/dify_benchmark/dify_batch_tester.py`

**修改內容**：
```python
class DifyBatchTester:
    def __init__(self, use_parallel=True, max_workers=5):
        self.use_parallel = use_parallel
        self.max_workers = max_workers
    
    def run_batch_test(self, ...):
        for version in versions:
            runner = DifyTestRunner(
                version=version,
                use_ai_evaluator=self.use_ai_evaluator,
                max_workers=self.max_workers  # ✅ 傳遞參數
            )
            
            # ✅ 使用新的並行方法
            if self.use_parallel:
                test_run = runner.run_batch_tests_parallel(...)
            else:
                test_run = runner.run_batch_tests(...)  # 舊方法
```

#### Step 3: 修改 API ViewSet
**檔案**: `backend/api/views/viewsets/dify_benchmark_viewsets.py`

**修改內容**：
```python
@action(detail=False, methods=['post'])
def batch_test(self, request):
    # ... 解析參數
    
    # ✅ 從請求中獲取並行參數
    use_parallel = request.data.get('use_parallel', True)
    max_workers = request.data.get('max_workers', 5)
    
    # 初始化 Batch Tester
    tester = DifyBatchTester(
        use_parallel=use_parallel,
        max_workers=max_workers
    )
    
    # 執行測試...
```

#### Step 4: 更新前端 API 呼叫
**檔案**: `frontend/src/services/difyBenchmarkApi.js`

**修改內容**：
```javascript
export const batchTest = (data) => {
  return api.post('/api/dify-benchmark/versions/batch_test/', {
    version_ids: data.version_ids,
    test_case_ids: data.test_case_ids,
    batch_name: data.batch_name,
    notes: data.notes,
    use_parallel: true,      // ✅ 啟用並行
    max_workers: 5,          // ✅ 最大 5 個並行線程
  });
};
```

---

### Phase 2: 前端進度顯示（可選）

#### 使用 Server-Sent Events (SSE) 即時更新進度

**後端修改**：
```python
from django.http import StreamingHttpResponse
import json

@action(detail=False, methods=['post'])
def batch_test_stream(self, request):
    """使用 SSE 流式返回測試進度"""
    
    def event_stream():
        # 初始化測試
        yield f"data: {json.dumps({'status': 'started', 'total': len(test_cases)})}\n\n"
        
        # 執行測試（帶回調）
        for i, result in enumerate(runner.run_batch_tests_with_callback(...), 1):
            yield f"data: {json.dumps({
                'status': 'progress',
                'current': i,
                'total': len(test_cases),
                'case': result.test_case.question,
                'passed': result.is_passed,
                'score': result.score
            })}\n\n"
        
        # 完成
        yield f"data: {json.dumps({'status': 'completed'})}\n\n"
    
    return StreamingHttpResponse(
        event_stream(),
        content_type='text/event-stream'
    )
```

**前端修改**：
```javascript
const eventSource = new EventSource('/api/dify-benchmark/versions/batch_test_stream/');

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.status === 'progress') {
    setProgress({
      current: data.current,
      total: data.total,
      currentCase: data.case
    });
  } else if (data.status === 'completed') {
    eventSource.close();
    message.success('測試完成！');
  }
};
```

---

## ⚡ 效能提升預估

### 當前順序執行（10 個測試案例）
```
測試 1: 3 秒
測試 2: 3 秒
測試 3: 3 秒
...
測試 10: 3 秒
────────────
總計: 30 秒
```

### 多線程並行執行（5 個並行）
```
批次 1: [測試 1, 2, 3, 4, 5] → 3 秒（同時執行）
批次 2: [測試 6, 7, 8, 9, 10] → 3 秒（同時執行）
────────────────────────────────
總計: 6 秒（提升 80% 效能）
```

### 實際效能測試結果（預估）

| 測試案例數 | 順序執行 | 並行執行 (5 workers) | 效能提升 |
|-----------|---------|---------------------|---------|
| 10        | 30 秒   | 6 秒                | 80%     |
| 20        | 60 秒   | 12 秒               | 80%     |
| 50        | 150 秒  | 30 秒               | 80%     |
| 100       | 300 秒  | 60 秒               | 80%     |

**注意**：實際效能取決於：
- Dify API 回應時間
- 網絡延遲
- 伺服器 CPU 核心數
- 記憶體使用量

---

## 🧪 測試計劃

### 單元測試

```python
# backend/tests/test_dify_benchmark_parallel.py

import pytest
from library.dify_benchmark.dify_test_runner import DifyTestRunner

class TestParallelExecution:
    """測試多線程執行功能"""
    
    def test_parallel_execution_faster_than_sequential(self):
        """驗證並行執行確實更快"""
        runner = DifyTestRunner(version=version, max_workers=5)
        test_cases = create_test_cases(10)
        
        # 順序執行
        start = time.time()
        runner.run_batch_tests(test_cases)
        sequential_time = time.time() - start
        
        # 並行執行
        start = time.time()
        runner.run_batch_tests_parallel(test_cases)
        parallel_time = time.time() - start
        
        # 並行應該顯著更快
        assert parallel_time < sequential_time * 0.5
    
    def test_results_consistency(self):
        """驗證並行執行結果與順序執行一致"""
        runner = DifyTestRunner(version=version)
        test_cases = create_test_cases(5)
        
        # 兩種方式執行
        seq_results = runner.run_batch_tests(test_cases)
        par_results = runner.run_batch_tests_parallel(test_cases)
        
        # 結果應該一致（分數可能略有差異）
        assert seq_results.passed_count == par_results.passed_count
        assert abs(seq_results.average_score - par_results.average_score) < 5
    
    def test_thread_safety(self):
        """驗證線程安全性（統計計數正確）"""
        runner = DifyTestRunner(version=version, max_workers=10)
        test_cases = create_test_cases(20)
        
        test_run = runner.run_batch_tests_parallel(test_cases)
        
        # 統計應該正確
        assert test_run.total_cases == 20
        assert test_run.passed_count + test_run.failed_count == 20
    
    def test_conversation_id_independence(self):
        """驗證每個測試使用獨立的 conversation_id"""
        runner = DifyTestRunner(version=version, max_workers=5)
        test_cases = create_test_cases(10)
        
        test_run = runner.run_batch_tests_parallel(test_cases)
        results = DifyTestResult.objects.filter(test_run=test_run)
        
        # 每個測試應該有不同的 conversation_id
        conversation_ids = [r.dify_conversation_id for r in results]
        assert len(conversation_ids) == len(set(conversation_ids))  # 全部不重複
```

### 整合測試

```bash
# 測試腳本
python backend/tests/test_dify_benchmark_parallel.py

# 預期輸出：
# ✅ test_parallel_execution_faster_than_sequential PASSED
# ✅ test_results_consistency PASSED
# ✅ test_thread_safety PASSED
# ✅ test_conversation_id_independence PASSED
```

---

## 🚨 風險評估與緩解措施

### 風險 1: 線程安全問題

**風險描述**: 多線程同時寫入資料庫可能造成資料不一致

**緩解措施**:
1. ✅ 使用 `threading.Lock` 保護共享變數
2. ✅ Django ORM 本身是線程安全的
3. ✅ 每個測試結果獨立創建（無競爭條件）
4. ✅ 添加單元測試驗證統計正確性

**風險等級**: 🟡 中等（已有緩解措施）

---

### 風險 2: Dify API 限流

**風險描述**: 同時發送 5-10 個請求可能觸發 API 限制

**緩解措施**:
1. ✅ 控制 `max_workers` 參數（預設 5，可調整）
2. ✅ 前端提供「測試速度」選項（快速/中速/慢速）
3. ✅ 監控 API 錯誤率，自動降速
4. ✅ 添加重試機制（已在 DifyAPIClient 中實現）

**風險等級**: 🟡 中等（可配置緩解）

---

### 風險 3: 記憶體消耗

**風險描述**: 100 個測試同時執行可能消耗大量記憶體

**緩解措施**:
1. ✅ 限制最大並行數（max_workers=5）
2. ✅ 使用線程池而非創建大量線程
3. ✅ 測試完成後立即釋放資源
4. ✅ 監控伺服器記憶體使用量

**風險等級**: 🟢 低（已控制並行數）

---

### 風險 4: 與 Protocol Assistant 衝突

**風險描述**: 測試期間影響正常用戶使用

**緩解措施**:
1. ✅ 使用不同的 `user_id` 前綴（`benchmark_test_*`）
2. ✅ 每次使用新的 `conversation_id=None`
3. ✅ 建議在非高峰時段執行大量測試
4. ✅ 前端顯示警告：「測試期間可能略微影響系統回應速度」

**風險等級**: 🟢 低（已有隔離機制）

---

## 📋 實作檢查清單

### Backend 修改

- [ ] **DifyTestRunner.py**
  - [ ] 添加 `max_workers` 參數
  - [ ] 添加線程安全計數器（`_lock`, `_passed_count`, etc.）
  - [ ] 實作 `run_batch_tests_parallel()` 方法
  - [ ] 實作 `_run_single_test_thread_safe()` 方法
  - [ ] 確保每個測試使用 `conversation_id=None`
  - [ ] 使用唯一的 `user_id = f"benchmark_test_{run_id}_{index}"`

- [ ] **DifyBatchTester.py**
  - [ ] 添加 `use_parallel` 和 `max_workers` 參數
  - [ ] 條件使用並行或順序執行
  - [ ] 傳遞參數到 DifyTestRunner

- [ ] **dify_benchmark_viewsets.py**
  - [ ] 修改 `batch_test` 方法接收並行參數
  - [ ] 傳遞 `use_parallel` 和 `max_workers` 到 DifyBatchTester
  - [ ] 更新 API 文檔註解

### Frontend 修改

- [ ] **difyBenchmarkApi.js**
  - [ ] 添加 `use_parallel` 和 `max_workers` 參數到請求
  - [ ] 預設啟用並行（`use_parallel: true`）
  - [ ] 預設 5 個並行（`max_workers: 5`）

- [ ] **DifyVersionManagementPage.js**（可選）
  - [ ] 添加「測試速度」設定選項
  - [ ] 提供快速/中速/慢速選擇（對應不同的 max_workers）
  - [ ] 顯示預估測試時間

### 測試

- [ ] **test_dify_benchmark_parallel.py**
  - [ ] 測試並行執行速度提升
  - [ ] 測試結果一致性
  - [ ] 測試線程安全性
  - [ ] 測試 conversation_id 獨立性

- [ ] **手動測試**
  - [ ] 執行 10 個測試案例，驗證速度提升
  - [ ] 同時使用 Protocol Assistant，確認無衝突
  - [ ] 監控 Dify API 錯誤率
  - [ ] 檢查資料庫結果正確性

### 文檔更新

- [ ] **更新 API 文檔**
  - [ ] 說明新的並行參數
  - [ ] 提供使用範例

- [ ] **更新測試指南**
  - [ ] 說明效能提升
  - [ ] 提供並行配置建議

---

## 🎯 建議的實作順序

### 第一階段：核心多線程功能（2-3 小時）
1. ✅ 修改 DifyTestRunner（添加並行方法）
2. ✅ 修改 DifyBatchTester（支援並行參數）
3. ✅ 修改 API ViewSet（接收並行參數）
4. ✅ 前端 API 呼叫（傳遞並行參數）

### 第二階段：測試與驗證（1-2 小時）
5. ✅ 編寫單元測試
6. ✅ 執行測試並修復 Bug
7. ✅ 手動測試功能
8. ✅ 驗證與 Protocol Assistant 無衝突

### 第三階段：優化與文檔（1 小時）
9. ✅ 前端添加測試速度選項（可選）
10. ✅ 更新 API 文檔
11. ✅ 更新使用者指南

**預估總時間**: 4-6 小時

---

## 📞 決策點

在開始實作前，需要確認以下決策：

### Q1: 預設啟用並行嗎？
- ✅ **建議**: 是，預設啟用（`use_parallel=True`）
- 原因: 效能提升顯著，風險可控

### Q2: 預設並行數量？
- ✅ **建議**: 5 個（`max_workers=5`）
- 原因: 平衡效能與資源消耗

### Q3: 是否提供前端配置選項？
- 🤔 **建議**: 第二階段考慮（可選功能）
- 原因: 大多數用戶使用預設值即可

### Q4: 是否使用 Celery？
- ❌ **建議**: 暫不使用
- 原因: ThreadPoolExecutor 已足夠，Celery 過於複雜

### Q5: 是否創建獨立 Dify App？
- ❌ **建議**: 暫不創建
- 原因: 當前隔離機制已足夠，除非發現問題

---

## 🎉 預期成果

實作完成後，將實現以下改進：

### 效能提升
- ✅ 10 個測試：30 秒 → **6 秒**（提升 80%）
- ✅ 50 個測試：150 秒 → **30 秒**（提升 80%）
- ✅ 100 個測試：300 秒 → **60 秒**（提升 80%）

### 系統隔離
- ✅ 每個測試使用獨立 conversation_id
- ✅ 使用 `benchmark_test_*` user_id 前綴區分測試
- ✅ 不影響 Protocol Assistant 正常用戶

### 程式碼品質
- ✅ 線程安全的統計計數
- ✅ 完整的單元測試覆蓋
- ✅ 向後兼容（保留順序執行方法）
- ✅ 可配置的並行參數

---

## 📅 規劃文檔資訊

**建立日期**: 2025-11-24  
**作者**: AI Assistant  
**狀態**: 📋 規劃完成，等待批准執行  
**預估工時**: 4-6 小時（3 個階段）  
**風險等級**: 🟡 中低（已有緩解措施）  

---

**下一步**: 等待用戶批准後開始實作 Phase 1（核心多線程功能）
