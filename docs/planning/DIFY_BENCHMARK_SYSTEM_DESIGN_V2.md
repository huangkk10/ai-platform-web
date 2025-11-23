# 📊 Dify API 跑分系統設計規劃 v2.0

## 📅 規劃資訊
- **創建日期**: 2025-11-23
- **版本**: 2.0 (基於用戶反饋調整)
- **規劃階段**: 架構設計與需求分析
- **執行狀態**: 待執行

---

## 🎯 系統目標

創建一個**獨立的 Dify API 跑分系統**，用於評估不同 Dify 配置版本在相同測試案例下的回答品質。

### 核心需求
1. ✅ **版本管理**: 管理不同的 Dify App（每個 App 有獨立的 API Key 和配置）
2. ✅ **批量測試**: 自動執行所有測試案例，評估每個版本的表現
3. ✅ **結果對比**: 提供版本間的詳細對比分析
4. ✅ **關鍵字評分**: 使用關鍵字匹配評估答案品質（不需要 GPT-4）
5. ✅ **獨立性**: 與現有 Benchmark 測試系統完全隔離

---

## 🔍 對 Protocol Assistant 運作方式的理解

### 現有架構分析

根據代碼檢查，您的 Protocol Assistant 使用：

#### 1. **ProtocolGuideSearchService** (後端搜尋服務)
```python
# library/protocol_guide/search_service.py

class ProtocolGuideSearchService(BaseKnowledgeBaseSearchService):
    """
    Protocol Guide 搜索服務
    
    功能：
    - search_knowledge() - 智能搜索（向量+關鍵字）
    - 支援兩階段搜尋 (stage=1, stage=2)
    - 文檔級搜尋功能
    """
    
    # Stage 1: 段落級搜尋 (章節搜尋)
    # Stage 2: 全文級搜尋 (完整文檔搜尋)
```

#### 2. **SearchThresholdSetting** (搜尋配置)
```python
# 資料庫中的配置
assistant_type = "protocol_assistant"

【第一階段配置（段落搜尋）】
- stage1_title_weight: 標題權重 %
- stage1_content_weight: 內容權重 %
- stage1_threshold: 相似度閾值

【第二階段配置（全文搜尋）】
- stage2_title_weight: 標題權重 %
- stage2_content_weight: 內容權重 %
- stage2_threshold: 相似度閾值
```

#### 3. **測試案例示例**
```python
# backend/test_two_stage_search.py

service = ProtocolGuideSearchService()

# 第一階段搜尋（段落級）
results_stage1 = service.search_knowledge(
    query="IOL",
    limit=5,
    use_vector=True,
    threshold=0.7,
    stage=1  # ← 指定第一階段
)

# 第二階段搜尋（全文級）
results_stage2 = service.search_knowledge(
    query="IOL",
    limit=5,
    use_vector=True,
    threshold=0.7,
    stage=2  # ← 指定第二階段
)
```

---

## 💡 關鍵洞察與設計調整

### 問題 1: "為什麼要手動錄入 Dify 配置？"

**原本設計的問題**:
- ❌ 要求用戶手動將 Dify 工作室的提示詞、RAG 設置複製到資料庫
- ❌ 增加管理負擔，容易不同步
- ❌ 不符合實際使用情境

**調整後的設計** ✅:
```python
# 版本 = Dify App (直接使用工作室配置)

class DifyConfigVersion:
    version_name = "Protocol Assistant v1.0"
    dify_app_id = "your-app-id"          # Dify 工作室的 App ID
    dify_api_key = "app-xxxxxxxxxxxx"    # Dify 工作室的 API Key
    dify_api_url = "http://10.10.172.37/v1/chat-messages"
    
    # ❌ 移除：不再儲存提示詞、RAG 設置等（這些在 Dify 工作室管理）
    # system_prompt = ...
    # rag_settings = ...
    
    # ✅ 新增：僅儲存版本描述和標籤
    description = "使用二階搜尋策略的版本"
    tags = ["二階搜尋", "生產環境"]
```

**優勢**:
1. ✅ **配置集中管理**: 所有配置都在 Dify 工作室管理
2. ✅ **無需同步**: 修改 Dify 配置後，跑分系統自動使用最新配置
3. ✅ **簡化操作**: 只需提供 App ID 和 API Key

---

### 問題 2: "如何使用後端搜尋 API 驗證？"

**您的需求**:
- 想使用現有的 `ProtocolGuideSearchService.search_knowledge()` 進行驗證
- 而不是只調用 Dify Chat API

**設計方案** ✅:

#### 方案 A: Dify-Only 模式（推薦）
```python
# 純粹測試 Dify 回答品質
# 測試流程：問題 → Dify API → 回答 → 關鍵字評分

優勢：
✅ 簡單直接
✅ 測試端到端用戶體驗
✅ 包含 Dify 的 RAG 檢索和回答生成

劣勢：
❌ 無法單獨測試搜尋品質
```

#### 方案 B: Hybrid 模式（進階）
```python
# 同時測試搜尋和回答
# 測試流程：
# 1. 後端搜尋 API → 檢索結果 → 評估檢索品質（Precision, Recall）
# 2. Dify API → 回答 → 評估回答品質（關鍵字匹配）

優勢：
✅ 可以對比 Dify 檢索 vs. 後端搜尋
✅ 更全面的評估

劣勢：
❌ 複雜度增加
❌ 需要兩套評分標準
```

**建議**:
- **MVP 階段**: 使用方案 A（Dify-Only）
- **未來擴展**: 可選擇性支援方案 B

---

## 📊 調整後的資料庫設計

### 1. `dify_config_version` - Dify 配置版本表（簡化版）

```sql
CREATE TABLE dify_config_version (
    id SERIAL PRIMARY KEY,
    version_name VARCHAR(200) NOT NULL UNIQUE,        -- 版本名稱
    description TEXT,                                 -- 版本描述
    
    -- Dify App 資訊（核心欄位）
    dify_app_id VARCHAR(100) NOT NULL,               -- Dify App ID
    dify_api_key VARCHAR(200) NOT NULL,              -- Dify API Key (加密)
    dify_api_url VARCHAR(500) DEFAULT 'http://10.10.172.37/v1/chat-messages',
    
    -- 版本標籤（可選）
    tags JSONB,                                      -- 標籤 ["二階搜尋", "v1.0"]
    
    -- 版本管理
    is_active BOOLEAN DEFAULT true,
    is_baseline BOOLEAN DEFAULT false,               -- 基準版本（用於對比）
    created_by_id INTEGER REFERENCES auth_user(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_dify_version_active ON dify_config_version(is_active);
CREATE INDEX idx_dify_version_baseline ON dify_config_version(is_baseline);
```

**範例資料**:
```json
{
  "version_name": "Protocol Assistant v1.0",
  "description": "使用二階搜尋策略，先章節後文檔",
  "dify_app_id": "your-app-id-here",
  "dify_api_key": "app-xxxxxxxxxxxxxxxxxxx",
  "dify_api_url": "http://10.10.172.37/v1/chat-messages",
  "tags": ["二階搜尋", "生產環境", "v1.0"],
  "is_active": true,
  "is_baseline": true
}
```

---

### 2. `dify_benchmark_test_case` - 測試案例表（複製自 benchmark_test_case）

```sql
CREATE TABLE dify_benchmark_test_case (
    id SERIAL PRIMARY KEY,
    
    -- ✅ 從 benchmark_test_case 複製
    original_test_case_id INTEGER REFERENCES benchmark_test_case(id),  -- 來源案例
    
    question TEXT NOT NULL,                          -- 測試問題
    test_class_name VARCHAR(200),                    -- 測試類別
    
    -- 評分標準（關鍵字匹配）
    expected_answer TEXT,                            -- 期望答案（參考）
    answer_keywords JSONB,                           -- 必須包含的關鍵字
    keyword_weights JSONB,                           -- 關鍵字權重（可選）
    
    -- 測試案例屬性
    difficulty_level VARCHAR(20),                    -- easy, medium, hard
    question_type VARCHAR(50),                       -- fact, procedure, comparison
    passing_score DECIMAL(5,2) DEFAULT 60.00,       -- 及格分數
    
    -- 管理欄位
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_dify_test_case_class ON dify_benchmark_test_case(test_class_name);
CREATE INDEX idx_dify_test_case_active ON dify_benchmark_test_case(is_active);
CREATE INDEX idx_dify_test_case_original ON dify_benchmark_test_case(original_test_case_id);
```

**範例資料**:
```json
{
  "original_test_case_id": 15,
  "question": "CrystalDiskMark 測試中，Sequential Q32T1 Read 的主要用途是什麼？",
  "test_class_name": "CrystalDiskMark",
  "expected_answer": "測試模擬多執行緒高佇列深度的連續讀取情境...",
  "answer_keywords": [
    "連續讀取",
    "佇列深度",
    "Q32T1",
    "多執行緒",
    "Sequential"
  ],
  "keyword_weights": {
    "連續讀取": 0.25,
    "佇列深度": 0.25,
    "Q32T1": 0.20,
    "多執行緒": 0.20,
    "Sequential": 0.10
  },
  "difficulty_level": "medium",
  "question_type": "fact",
  "passing_score": 60.0
}
```

---

### 3. `dify_test_run` - 測試執行記錄表

```sql
CREATE TABLE dify_test_run (
    id SERIAL PRIMARY KEY,
    version_id INTEGER REFERENCES dify_config_version(id) ON DELETE CASCADE,
    
    -- 測試資訊
    run_name VARCHAR(300),
    run_type VARCHAR(50) DEFAULT 'batch_comparison',
    batch_id VARCHAR(100),                           -- 批次 ID
    
    -- 測試統計
    total_test_cases INTEGER DEFAULT 0,
    passed_cases INTEGER DEFAULT 0,
    failed_cases INTEGER DEFAULT 0,
    
    -- 評分指標（關鍵字匹配）
    average_score DECIMAL(5,2),                      -- 平均分數
    total_score DECIMAL(10,2),                       -- 總分數
    pass_rate DECIMAL(5,2),                          -- 通過率 (0-1)
    
    -- 時間統計
    total_execution_time DECIMAL(10,2),              -- 總執行時間 (秒)
    average_response_time DECIMAL(10,2),             -- 平均響應時間 (秒)
    
    -- 關鍵字匹配統計
    average_keyword_match_rate DECIMAL(5,2),         -- 平均關鍵字匹配率
    
    -- 管理欄位
    notes TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_dify_run_version ON dify_test_run(version_id);
CREATE INDEX idx_dify_run_batch ON dify_test_run(batch_id);
CREATE INDEX idx_dify_run_created ON dify_test_run(created_at);
```

---

### 4. `dify_test_result` - 單題測試結果表

```sql
CREATE TABLE dify_test_result (
    id SERIAL PRIMARY KEY,
    test_run_id INTEGER REFERENCES dify_test_run(id) ON DELETE CASCADE,
    test_case_id INTEGER REFERENCES dify_benchmark_test_case(id),
    
    -- Dify 回答
    dify_answer TEXT,                                -- Dify 的回答
    dify_message_id VARCHAR(200),                    -- Dify 訊息 ID
    dify_conversation_id VARCHAR(200),               -- Dify 對話 ID
    
    -- 評分結果（關鍵字匹配）
    score DECIMAL(5,2),                              -- 總分 (0-100)
    is_passed BOOLEAN,                               -- 是否通過
    
    -- 關鍵字匹配詳情
    matched_keywords JSONB,                          -- 匹配到的關鍵字
    missing_keywords JSONB,                          -- 缺失的關鍵字
    keyword_match_rate DECIMAL(5,2),                 -- 關鍵字匹配率 (0-100)
    
    -- 評分詳情
    evaluation_details JSONB,                        -- 評分詳細說明
    
    -- 時間統計
    response_time DECIMAL(10,3),                     -- 響應時間 (秒)
    
    -- Dify 檢索資訊（如果 Dify 回傳）
    retrieved_documents JSONB,                       -- 檢索到的文檔
    retrieval_metadata JSONB,                        -- 檢索元資料
    
    -- 管理欄位
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_dify_result_run ON dify_test_result(test_run_id);
CREATE INDEX idx_dify_result_case ON dify_test_result(test_case_id);
CREATE INDEX idx_dify_result_passed ON dify_test_result(is_passed);
```

---

## 🔧 後端 Library 設計（簡化版）

### 目錄結構
```
backend/library/dify_benchmark/
├── __init__.py
├── dify_batch_tester.py         # 批量測試器
├── dify_test_runner.py          # 單次測試執行器
├── keyword_evaluator.py         # 關鍵字評分器（唯一評分方式）
└── comparison_engine.py         # 對比分析引擎
```

---

### 1. `KeywordEvaluator` - 關鍵字評分器（唯一評分方式）

```python
"""關鍵字評分器 - Dify 跑分系統的唯一評分方式"""
import re
from typing import Dict, List, Any


class KeywordEvaluator:
    """
    關鍵字評分器
    
    評分邏輯：
    1. 檢查答案中是否包含必要的關鍵字
    2. 計算關鍵字匹配率
    3. 根據權重計算總分
    
    評分公式：
    score = Σ (matched_keyword_weight) / Σ (all_keyword_weight) * 100
    
    Example:
        關鍵字：["連續讀取" (25%), "佇列深度" (25%), "Q32T1" (20%)]
        答案包含：["連續讀取", "Q32T1"]
        分數：(25 + 20) / (25 + 25 + 20) * 100 = 64.3 分
    """
    
    def __init__(self):
        pass
    
    def evaluate(
        self,
        question: str,
        expected_answer: str,
        actual_answer: str,
        keywords: List[str],
        keyword_weights: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """
        評估答案
        
        Args:
            question: 問題
            expected_answer: 期望答案（參考）
            actual_answer: 實際答案
            keywords: 關鍵字列表
            keyword_weights: 關鍵字權重（可選）
            
        Returns:
            {
                'score': float,              # 總分 (0-100)
                'is_passed': bool,           # 是否通過 (>= 60)
                'matched_keywords': list,    # 匹配到的關鍵字
                'missing_keywords': list,    # 缺失的關鍵字
                'keyword_match_rate': float, # 匹配率 (0-100)
                'details': dict              # 詳細說明
            }
        """
        if not keywords:
            return {
                'score': 0,
                'is_passed': False,
                'matched_keywords': [],
                'missing_keywords': [],
                'keyword_match_rate': 0,
                'details': {'error': '沒有提供關鍵字'}
            }
        
        # 預處理答案（轉小寫、去除多餘空格）
        actual_answer_lower = actual_answer.lower()
        
        # 如果沒有提供權重，均分權重
        if not keyword_weights:
            equal_weight = 1.0 / len(keywords)
            keyword_weights = {kw: equal_weight for kw in keywords}
        
        # 檢查每個關鍵字
        matched_keywords = []
        missing_keywords = []
        matched_weight = 0.0
        total_weight = sum(keyword_weights.values())
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            weight = keyword_weights.get(keyword, 0)
            
            # 檢查關鍵字是否在答案中
            if keyword_lower in actual_answer_lower:
                matched_keywords.append(keyword)
                matched_weight += weight
            else:
                missing_keywords.append(keyword)
        
        # 計算分數
        if total_weight > 0:
            score = (matched_weight / total_weight) * 100
        else:
            score = 0
        
        # 計算匹配率
        keyword_match_rate = (len(matched_keywords) / len(keywords)) * 100 if keywords else 0
        
        # 是否通過（60 分及格）
        is_passed = score >= 60
        
        return {
            'score': round(score, 2),
            'is_passed': is_passed,
            'matched_keywords': matched_keywords,
            'missing_keywords': missing_keywords,
            'keyword_match_rate': round(keyword_match_rate, 2),
            'details': {
                'total_keywords': len(keywords),
                'matched_count': len(matched_keywords),
                'missing_count': len(missing_keywords),
                'matched_weight': round(matched_weight, 3),
                'total_weight': round(total_weight, 3)
            }
        }
```

---

### 2. `DifyTestRunner` - 測試執行器

```python
"""Dify 測試執行器"""
from datetime import datetime
from typing import List, Dict, Any
import logging
import time
import requests

logger = logging.getLogger(__name__)


class DifyTestRunner:
    """
    Dify 測試執行器
    
    功能：
    - 執行單個 Dify 版本的所有測試案例
    - 呼叫 Dify Chat API 獲取答案
    - 使用關鍵字評分器評估答案品質
    """
    
    def __init__(self, version, verbose=False):
        """
        Args:
            version: DifyConfigVersion 實例
            verbose: 是否輸出詳細日誌
        """
        self.version = version
        self.verbose = verbose
        
        # 初始化評分器
        from library.dify_benchmark.keyword_evaluator import KeywordEvaluator
        self.evaluator = KeywordEvaluator()
    
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
        total_keyword_match_rate = 0
        
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
                total_keyword_match_rate += result.keyword_match_rate
                
                logger.info(f"    ✅ 分數: {result.score:.2f}, 通過: {result.is_passed}")
                
            except Exception as e:
                logger.error(f"    ❌ 測試失敗: {str(e)}")
        
        # 更新測試記錄
        test_run.passed_cases = passed_count
        test_run.failed_cases = len(test_cases) - passed_count
        test_run.average_score = total_score / len(test_cases) if test_cases else 0
        test_run.total_score = total_score
        test_run.pass_rate = (passed_count / len(test_cases)) if test_cases else 0
        test_run.average_response_time = total_response_time / len(test_cases) if test_cases else 0
        test_run.average_keyword_match_rate = total_keyword_match_rate / len(test_cases) if test_cases else 0
        
        test_run.completed_at = datetime.now()
        test_run.total_execution_time = (test_run.completed_at - test_run.started_at).total_seconds()
        test_run.save()
        
        logger.info(f"測試完成: 平均分數={test_run.average_score:.2f}, 通過率={test_run.pass_rate*100:.2f}%")
        
        return test_run
    
    def _run_single_test(self, test_run, test_case):
        """執行單個測試案例"""
        from api.models import DifyTestResult
        
        # 1. 呼叫 Dify API
        start_time = time.time()
        
        try:
            dify_response = self._call_dify_api(test_case.question)
            response_time = time.time() - start_time
            
            dify_answer = dify_response.get('answer', '')
            dify_message_id = dify_response.get('message_id')
            dify_conversation_id = dify_response.get('conversation_id')
            retrieved_documents = dify_response.get('metadata', {}).get('retrieval_sources')
            
        except Exception as e:
            logger.error(f"Dify API 調用失敗: {str(e)}")
            raise
        
        # 2. 評估答案（關鍵字匹配）
        evaluation = self.evaluator.evaluate(
            question=test_case.question,
            expected_answer=test_case.expected_answer,
            actual_answer=dify_answer,
            keywords=test_case.answer_keywords,
            keyword_weights=test_case.keyword_weights
        )
        
        # 3. 儲存結果
        test_result = DifyTestResult.objects.create(
            test_run=test_run,
            test_case=test_case,
            dify_answer=dify_answer,
            dify_message_id=dify_message_id,
            dify_conversation_id=dify_conversation_id,
            score=evaluation['score'],
            is_passed=evaluation['is_passed'],
            matched_keywords=evaluation['matched_keywords'],
            missing_keywords=evaluation['missing_keywords'],
            keyword_match_rate=evaluation['keyword_match_rate'],
            evaluation_details=evaluation['details'],
            response_time=response_time,
            retrieved_documents=retrieved_documents
        )
        
        return test_result
    
    def _call_dify_api(self, question: str) -> Dict[str, Any]:
        """
        呼叫 Dify Chat API
        
        Args:
            question: 用戶問題
            
        Returns:
            {
                'answer': str,
                'message_id': str,
                'conversation_id': str,
                'metadata': dict
            }
        """
        url = self.version.dify_api_url
        headers = {
            'Authorization': f'Bearer {self.version.dify_api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'inputs': {},
            'query': question,
            'response_mode': 'blocking',  # 阻塞模式，等待完整回答
            'user': f'benchmark_test_{self.version.id}'
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            data = response.json()
            
            return {
                'answer': data.get('answer', ''),
                'message_id': data.get('message_id'),
                'conversation_id': data.get('conversation_id'),
                'metadata': data.get('metadata', {})
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Dify API 請求失敗: {str(e)}")
            raise Exception(f"Dify API 調用失敗: {str(e)}")
```

---

## 🎨 前端設計（簡化版）

### 側邊欄選單
```javascript
{
  key: 'dify-benchmark',
  icon: <RocketOutlined />,
  label: 'Dify 跑分',
  children: [
    {
      key: '/dify-benchmark/dashboard',
      label: 'Dashboard',
    },
    {
      key: '/dify-benchmark/versions',
      label: '版本管理',
    },
    {
      key: '/dify-benchmark/test-cases',
      label: '測試案例',
    },
    {
      key: '/dify-benchmark/batch-test',
      label: '批量測試',
    },
    {
      key: '/dify-benchmark/history',
      label: '測試歷史',
    }
  ],
}
```

---

## 📝 MVP 實作步驟

### Phase 1: 資料庫與 Models (1 天)
1. ✅ 創建 4 個資料表
2. ✅ 創建 Django Models
3. ✅ 執行 Migration
4. ✅ 從 `benchmark_test_case` 複製測試案例

### Phase 2: 後端 Library (1-2 天)
1. ✅ 實作 `KeywordEvaluator` (關鍵字評分器)
2. ✅ 實作 `DifyTestRunner` (測試執行器)
3. ✅ 實作 `DifyBatchTester` (批量測試器)
4. ✅ CLI 測試工具

### Phase 3: API 層 (1-2 天)
1. ✅ 實作 ViewSets (4 個)
2. ✅ 註冊 URL 路由
3. ✅ 測試 API 端點

### Phase 4: 前端頁面 (2-3 天)
1. ✅ 版本管理頁面
2. ✅ 測試案例頁面（複製功能）
3. ✅ 批量測試執行頁面
4. ✅ 版本對比頁面
5. ✅ 測試歷史頁面

### Phase 5: 整合測試 (1 天)
1. ✅ 端到端測試
2. ✅ 修復 Bug
3. ✅ 文檔完善

**預計總時間**: 6-9 天

---

## ✅ 驗收標準

### 功能完整性
- [ ] 可以新增 Dify App 版本（只需 App ID 和 API Key）
- [ ] 可以從 `benchmark_test_case` 複製測試案例
- [ ] 可以執行批量測試（多版本 × 多測試案例）
- [ ] 關鍵字評分正常運作
- [ ] 可以查看版本對比分析
- [ ] 可以查看每題的詳細答案和評分

### 資料正確性
- [ ] 關鍵字匹配率計算正確
- [ ] 分數計算正確（根據權重）
- [ ] 通過率統計正確

---

## 🎯 總結

### 核心調整
1. ✅ **簡化版本管理**: 不儲存 Dify 配置，只儲存 App ID 和 API Key
2. ✅ **單一評分方式**: 只使用關鍵字評分（不需要 GPT-4）
3. ✅ **測試案例複製**: 從 `benchmark_test_case` 複製問題和關鍵字
4. ✅ **直接使用 Dify 工作室配置**: 所有配置在 Dify 管理，跑分系統只負責測試

### 與 Benchmark 系統的區別
| 項目 | Benchmark 測試 | Dify 跑分 |
|------|---------------|----------|
| **測試對象** | Protocol 搜尋演算法 | Dify App 回答品質 |
| **測試方式** | 直接查詢資料庫 | 調用 Dify Chat API |
| **評分標準** | Precision, Recall, F1 | 關鍵字匹配率 |
| **配置管理** | 資料庫 (SearchThresholdSetting) | Dify 工作室 |

---

**規劃完成日期**: 2025-11-23  
**版本**: 2.0  
**執行狀態**: 待確認後執行 ⏳
