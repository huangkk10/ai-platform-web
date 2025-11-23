# Benchmark 測試系統架構規劃

## 📋 目標

建立兩個獨立的測試系統，分別驗證：
1. **純搜尋引擎效能** - 驗證向量搜尋 + 關鍵字搜尋的檢索能力
2. **完整 AI 系統效能** - 驗證 Dify API + 搜尋 + RAG + LLM 的端到端能力

---

## 🔍 當前 Protocol Assistant 搜尋架構分析

### 實際使用的搜尋流程

```
用戶查詢
    ↓
ProtocolGuideSearchService.search_knowledge()
    ↓
BaseKnowledgeBaseSearchService (基礎類別)
    ↓
┌─────────────────────────────────────────────┐
│ 🎯 兩階段混合搜尋策略                        │
├─────────────────────────────────────────────┤
│ Stage 1: 段落向量搜尋 (Section Search)       │
│   - 使用 section_multi_vectors 表            │
│   - 搜尋精確片段（更高精準度）               │
│   - threshold: 預設 0.7                      │
│   - 搜尋範圍：章節級內容                     │
│                                              │
│ ↓ (如果段落搜尋失敗或結果不足)               │
│                                              │
│ Stage 2: 全文向量搜尋 (Document Search)      │
│   - 使用 document_embeddings 表              │
│   - 搜尋完整文檔（更高召回率）               │
│   - threshold: 0.7 * 0.85 = 0.595           │
│   - 搜尋範圍：整篇文檔內容                   │
│                                              │
│ ↓ (如果向量搜尋結果不足)                     │
│                                              │
│ Stage 3: 關鍵字補充搜尋 (Keyword Search)     │
│   - 使用 PostgreSQL ILIKE                    │
│   - threshold: 0.7 * 0.5 = 0.35             │
│   - 智能分數計算（標題 0.7+, 內容 0.3+）    │
└─────────────────────────────────────────────┘
    ↓
合併、去重、排序
    ↓
返回 Top-K 結果
```

### 核心搜尋參數

| 參數 | 預設值 | 來源 | 說明 |
|------|--------|------|------|
| `threshold` | 0.7 | Dify Studio | 主要相似度閾值 |
| `limit` | 10 | API 參數 | 返回結果數量 |
| `use_vector` | True | API 參數 | 是否使用向量搜尋 |
| `search_mode` | 'auto' | API 參數 | 搜尋模式（auto/section_only/document_only） |
| `stage` | 1 | 內部邏輯 | 搜尋階段（1=段落, 2=全文） |

### 搜尋模式說明

```python
# Mode 1: 自動模式（預設）- 最智能
search_mode = 'auto'
# 流程：段落搜尋 → (失敗) → 全文搜尋 → (不足) → 關鍵字搜尋

# Mode 2: 只搜尋段落 - 最精準
search_mode = 'section_only'
# 流程：段落搜尋 → (無降級)

# Mode 3: 只搜尋文檔 - 最全面
search_mode = 'document_only'
# 流程：全文搜尋 → (無降級)
```

---

## 🎯 規劃方案：雙軌測試系統

### 系統 A：搜尋引擎 Benchmark（當前系統）

**目標**：驗證純搜尋能力，不涉及 LLM

**測試對象**：
- ✅ 向量搜尋精準度（Precision, Recall, F1, NDCG）
- ✅ 搜尋響應時間
- ✅ 兩階段搜尋策略效能
- ✅ 不同 threshold 設定的影響

**架構保持不變**：
```
BenchmarkTestRunner
    ↓
ProtocolGuideSearchService.search_knowledge()
    ↓
返回檢索文檔列表
    ↓
評分引擎計算指標
```

**測試案例結構**：
```python
{
    "question": "IOL USB 如何測試？",
    "expected_document_ids": [123, 456, 789],  # ✅ 預期應檢索到的文檔
    "min_required_matches": 2,                  # ✅ 最少需匹配數量
    "category": "資源路徑",
    "difficulty": "medium"
}
```

**評分指標**：
- Precision（精準度）
- Recall（召回率）
- F1 Score（綜合指標）
- NDCG（排序質量）
- Response Time（響應時間）
- Overall Score（綜合分數）

---

### 系統 B：AI Assistant Benchmark（新建系統）

**目標**：驗證完整 AI 系統效能，包含 RAG + LLM

**測試對象**：
- ✅ AI 回答的正確性（Answer Relevance）
- ✅ AI 回答的完整性（Answer Completeness）
- ✅ 檢索上下文的相關性（Context Relevance）
- ✅ 端到端響應時間
- ✅ Token 使用量

**架構（新開發）**：
```
AIBenchmarkTestRunner
    ↓
DifyRequestManager.send_chat_request()
    ↓
Dify API (Knowledge Retrieval + LLM)
    ↓
返回 AI 回答 + 檢索上下文
    ↓
AI 評分引擎計算指標
```

**測試案例結構**（新格式）：
```python
{
    "question": "請說明 IOL USB 的完整測試流程",
    "expected_answer_keywords": [          # ✅ 預期回答應包含的關鍵字
        "連接測試", 
        "速度測試", 
        "穩定性測試",
        "CrystalDiskMark"
    ],
    "expected_document_ids": [123, 456],   # ✅ 預期 RAG 應檢索的文檔
    "answer_type": "procedural",           # ✅ 回答類型（程序性/事實性/概念性）
    "category": "SOP 流程",
    "difficulty": "medium"
}
```

**評分指標（新設計）**：
- **Answer Relevance**（回答相關性）：AI 回答與問題的相關度
- **Answer Completeness**（回答完整性）：是否包含所有關鍵資訊
- **Context Precision**（上下文精準度）：檢索到的文檔是否相關
- **Context Recall**（上下文召回率）：是否檢索到所有必要文檔
- **Faithfulness**（忠實度）：AI 回答是否基於檢索到的上下文
- **Response Time**（端到端響應時間）
- **Token Usage**（Token 使用量）
- **Overall Score**（綜合分數）

---

## 📊 兩個系統的對比

| 維度 | 系統 A：搜尋引擎 Benchmark | 系統 B：AI Assistant Benchmark |
|------|--------------------------|-------------------------------|
| **測試對象** | 純搜尋引擎 | Dify API + RAG + LLM |
| **主要目標** | 驗證檢索能力 | 驗證 AI 回答質量 |
| **測試案例** | 問題 + 預期文檔 ID | 問題 + 預期回答要點 |
| **評分維度** | Precision, Recall, F1, NDCG | Answer Relevance, Completeness, Faithfulness |
| **響應時間** | 毫秒級（< 500ms） | 秒級（3-10s） |
| **成本** | 低（無 LLM 呼叫） | 中（LLM API 費用） |
| **用途** | 搜尋演算法優化 | AI 助手優化 |
| **迭代速度** | 快（秒級測試） | 慢（分鐘級測試） |

---

## 🔧 技術實現計畫

### Phase 1：保持系統 A（搜尋引擎 Benchmark）✅

**已完成功能**：
- ✅ 測試案例管理（BenchmarkTestCase）
- ✅ 測試執行管理（BenchmarkTestRun）
- ✅ 測試結果記錄（BenchmarkTestResult）
- ✅ 演算法版本管理（SearchAlgorithmVersion）
- ✅ 評分引擎（ScoringEngine）
- ✅ Dashboard 可視化
- ✅ 測試執行頁面

**需要優化**：
1. **修正演算法類型標記**
   ```sql
   UPDATE search_algorithm_version 
   SET algorithm_type = 'two_stage_hybrid',
       description = '兩階段混合搜尋：段落向量 → 全文向量 → 關鍵字補充'
   WHERE id = 3;
   ```

2. **支援 Parameters 配置**
   ```json
   {
     "stage1_threshold": 0.7,
     "stage2_threshold": 0.595,
     "keyword_threshold": 0.35,
     "search_mode": "auto",
     "use_section_search": true,
     "use_document_search": true,
     "use_keyword_search": true
   }
   ```

3. **實現版本參數化執行**
   ```python
   # BenchmarkTestRunner 根據 version.parameters 調整搜尋策略
   def run_single_test(self, test_case):
       params = self.version.parameters
       results = self.search_service.search_knowledge(
           query=test_case.question,
           threshold=params.get('stage1_threshold', 0.7),
           search_mode=params.get('search_mode', 'auto'),
           # ...
       )
   ```

---

### Phase 2：建立系統 B（AI Assistant Benchmark）🆕

#### Step 1：資料庫設計（新表）

```python
# 新 Model: AI 測試案例
class AIBenchmarkTestCase(models.Model):
    """AI Assistant 測試案例"""
    question = models.TextField(verbose_name="測試問題")
    
    # AI 回答評估標準
    expected_answer_keywords = models.JSONField(
        default=list, 
        verbose_name="預期回答關鍵字"
    )
    expected_answer_structure = models.JSONField(
        default=dict,
        verbose_name="預期回答結構",
        help_text="例如：{'introduction': True, 'steps': 5, 'conclusion': True}"
    )
    
    # RAG 檢索評估標準（與系統 A 兼容）
    expected_document_ids = models.JSONField(
        default=list, 
        verbose_name="預期檢索文檔 ID"
    )
    min_required_matches = models.IntegerField(
        default=1,
        verbose_name="最少需匹配文檔數"
    )
    
    # 元資料
    answer_type = models.CharField(
        max_length=50,
        choices=[
            ('factual', '事實性'),
            ('procedural', '程序性'),
            ('conceptual', '概念性'),
            ('comparative', '比較性'),
        ],
        default='factual'
    )
    category = models.CharField(max_length=100, blank=True)
    difficulty_level = models.CharField(max_length=20, blank=True)
    
    # 系統關聯
    system_type = models.CharField(
        max_length=50,
        choices=[
            ('protocol_assistant', 'Protocol Assistant'),
            ('rvt_assistant', 'RVT Assistant'),
        ],
        default='protocol_assistant'
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


# 新 Model: AI 測試執行
class AIBenchmarkTestRun(models.Model):
    """AI Assistant 測試執行記錄"""
    version = models.ForeignKey(
        'DifyAppVersion',  # 新 Model：Dify 應用版本
        on_delete=models.CASCADE
    )
    run_name = models.CharField(max_length=200)
    run_type = models.CharField(max_length=50, default='manual')
    
    # 測試統計
    total_test_cases = models.IntegerField(default=0)
    completed_test_cases = models.IntegerField(default=0)
    passed_test_cases = models.IntegerField(default=0)
    
    # AI 評分指標（平均值）
    answer_relevance_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    answer_completeness_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    context_precision_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    context_recall_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    faithfulness_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # 效能指標
    avg_response_time = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    avg_token_usage = models.IntegerField(default=0)
    
    # 綜合分數
    overall_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # 狀態
    status = models.CharField(max_length=20, default='pending')
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)


# 新 Model: AI 測試結果
class AIBenchmarkTestResult(models.Model):
    """AI Assistant 單次測試結果"""
    test_run = models.ForeignKey(AIBenchmarkTestRun, on_delete=models.CASCADE)
    test_case = models.ForeignKey(AIBenchmarkTestCase, on_delete=models.CASCADE)
    
    # 查詢與回答
    query = models.TextField()
    ai_answer = models.TextField()
    
    # RAG 檢索結果
    retrieved_document_ids = models.JSONField(default=list)
    retrieved_contexts = models.JSONField(default=list)
    
    # AI 評分
    answer_relevance = models.DecimalField(max_digits=5, decimal_places=4, default=0)
    answer_completeness = models.DecimalField(max_digits=5, decimal_places=4, default=0)
    context_precision = models.DecimalField(max_digits=5, decimal_places=4, default=0)
    context_recall = models.DecimalField(max_digits=5, decimal_places=4, default=0)
    faithfulness = models.DecimalField(max_digits=5, decimal_places=4, default=0)
    
    # 效能指標
    response_time = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    token_usage = models.IntegerField(default=0)
    
    # 通過狀態
    is_passed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


# 新 Model: Dify 應用版本
class DifyAppVersion(models.Model):
    """Dify 應用版本管理"""
    version_name = models.CharField(max_length=100)
    version_code = models.CharField(max_length=50, unique=True)
    
    # Dify 配置
    app_name = models.CharField(max_length=100)
    api_key = models.CharField(max_length=200)
    api_url = models.URLField()
    
    # 系統類型
    system_type = models.CharField(
        max_length=50,
        choices=[
            ('protocol_assistant', 'Protocol Assistant'),
            ('rvt_assistant', 'RVT Assistant'),
        ]
    )
    
    # RAG 配置（從 Dify Studio）
    rag_config = models.JSONField(
        default=dict,
        verbose_name="RAG 配置",
        help_text="例如：{'retrieval_mode': 'hybrid', 'top_k': 10, 'score_threshold': 0.7}"
    )
    
    is_active = models.BooleanField(default=True)
    is_baseline = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
```

#### Step 2：AI 評分引擎（核心邏輯）

```python
# library/ai_benchmark/ai_scoring_engine.py

class AIScoringEngine:
    """
    AI Assistant 評分引擎
    
    評分維度：
    1. Answer Relevance（回答相關性）
    2. Answer Completeness（回答完整性）
    3. Context Precision（上下文精準度）
    4. Context Recall（上下文召回率）
    5. Faithfulness（忠實度）
    """
    
    @staticmethod
    def calculate_answer_relevance(question: str, answer: str) -> float:
        """
        計算回答相關性
        
        方法：使用 LLM 評估回答是否直接回答問題
        
        Prompt:
        "Question: {question}
         Answer: {answer}
         
         Does the answer directly address the question? 
         Rate from 0.0 to 1.0."
        """
        pass
    
    @staticmethod
    def calculate_answer_completeness(
        expected_keywords: list, 
        answer: str
    ) -> float:
        """
        計算回答完整性
        
        方法：檢查預期關鍵字是否出現在回答中
        
        Score = 匹配的關鍵字數 / 總關鍵字數
        """
        matched = sum(1 for kw in expected_keywords if kw in answer)
        return matched / len(expected_keywords) if expected_keywords else 0.0
    
    @staticmethod
    def calculate_context_precision(
        retrieved_ids: list, 
        expected_ids: list
    ) -> float:
        """
        計算上下文精準度（與系統 A 的 Precision 相同）
        
        Precision = TP / (TP + FP)
        """
        tp = len(set(retrieved_ids) & set(expected_ids))
        return tp / len(retrieved_ids) if retrieved_ids else 0.0
    
    @staticmethod
    def calculate_context_recall(
        retrieved_ids: list, 
        expected_ids: list
    ) -> float:
        """
        計算上下文召回率（與系統 A 的 Recall 相同）
        
        Recall = TP / (TP + FN)
        """
        tp = len(set(retrieved_ids) & set(expected_ids))
        return tp / len(expected_ids) if expected_ids else 0.0
    
    @staticmethod
    def calculate_faithfulness(answer: str, contexts: list) -> float:
        """
        計算忠實度
        
        方法：檢查回答中的陳述是否能在檢索上下文中找到支持
        
        使用 LLM 評估：
        "Contexts: {contexts}
         Answer: {answer}
         
         What percentage of statements in the answer are supported by the contexts?
         Rate from 0.0 to 1.0."
        """
        pass
    
    @staticmethod
    def calculate_overall_score(metrics: dict) -> float:
        """
        計算綜合分數
        
        權重分配：
        - Answer Relevance: 25%
        - Answer Completeness: 25%
        - Context Precision: 15%
        - Context Recall: 15%
        - Faithfulness: 20%
        """
        weights = {
            'answer_relevance': 0.25,
            'answer_completeness': 0.25,
            'context_precision': 0.15,
            'context_recall': 0.15,
            'faithfulness': 0.20
        }
        
        score = sum(
            metrics.get(key, 0) * weight 
            for key, weight in weights.items()
        )
        
        return round(score * 100, 2)  # 0-100 分數
```

#### Step 3：AI 測試執行器

```python
# library/ai_benchmark/ai_test_runner.py

class AIBenchmarkTestRunner:
    """AI Assistant 測試執行器"""
    
    def __init__(self, version_id: int):
        self.version = DifyAppVersion.objects.get(id=version_id)
        self.dify_manager = self._create_dify_manager()
        self.scoring_engine = AIScoringEngine()
    
    def _create_dify_manager(self):
        """創建 Dify Request Manager"""
        from library.dify_integration.dify_request_manager import DifyRequestManager
        
        return DifyRequestManager(
            api_url=self.version.api_url,
            api_key=self.version.api_key,
            timeout=60  # AI 回答需要更長時間
        )
    
    def run_single_test(self, test_case):
        """執行單次 AI 測試"""
        try:
            start_time = time.time()
            
            # 1. 呼叫 Dify API
            response = self.dify_manager.send_chat_request(
                query=test_case.question,
                user_id=f"benchmark_test_{test_case.id}",
                conversation_id=None  # 每次獨立對話
            )
            
            response_time = (time.time() - start_time) * 1000
            
            # 2. 解析回應
            ai_answer = response.get('answer', '')
            retrieved_contexts = response.get('retrieval', {}).get('documents', [])
            retrieved_ids = [
                doc.get('metadata', {}).get('id') 
                for doc in retrieved_contexts
            ]
            token_usage = response.get('metadata', {}).get('usage', {}).get('total_tokens', 0)
            
            # 3. 計算評分
            scores = {
                'answer_relevance': self.scoring_engine.calculate_answer_relevance(
                    test_case.question, ai_answer
                ),
                'answer_completeness': self.scoring_engine.calculate_answer_completeness(
                    test_case.expected_answer_keywords, ai_answer
                ),
                'context_precision': self.scoring_engine.calculate_context_precision(
                    retrieved_ids, test_case.expected_document_ids
                ),
                'context_recall': self.scoring_engine.calculate_context_recall(
                    retrieved_ids, test_case.expected_document_ids
                ),
                'faithfulness': self.scoring_engine.calculate_faithfulness(
                    ai_answer, retrieved_contexts
                )
            }
            
            # 4. 判斷是否通過
            is_passed = (
                scores['answer_relevance'] >= 0.7 and
                scores['answer_completeness'] >= 0.7 and
                scores['faithfulness'] >= 0.7
            )
            
            return {
                'test_case': test_case,
                'ai_answer': ai_answer,
                'retrieved_document_ids': retrieved_ids,
                'retrieved_contexts': retrieved_contexts,
                'response_time': response_time,
                'token_usage': token_usage,
                'is_passed': is_passed,
                **scores
            }
            
        except Exception as e:
            logger.error(f"AI 測試失敗: {str(e)}")
            return self._create_failed_result(test_case, str(e))
    
    @transaction.atomic
    def run_batch_tests(self, test_cases, run_name, run_type='manual'):
        """執行批量 AI 測試"""
        # 類似於 BenchmarkTestRunner.run_batch_tests
        # 但使用 AIBenchmarkTestRun 和 AIBenchmarkTestResult
        pass
```

#### Step 4：前端實現

```javascript
// 新頁面：AI Assistant 測試執行
// frontend/src/pages/benchmark/AIBenchmarkTestExecutionPage.js

const AIBenchmarkTestExecutionPage = () => {
  // UI 類似於 BenchmarkTestExecutionPage
  // 但顯示不同的統計資訊：
  // - Answer Quality（回答質量）
  // - Context Quality（上下文質量）
  // - Response Time（響應時間）
  // - Token Usage（Token 使用）
  
  return (
    <div>
      {/* 版本選擇：Dify App 版本 */}
      {/* 測試配置：系統類型（Protocol/RVT） */}
      {/* 執行按鈕：快速測試 (5題) / 完整測試 (50題) */}
      {/* 進度顯示：包含 Token 使用量 */}
    </div>
  );
};
```

---

## 📊 使用場景對比

### 場景 1：優化搜尋演算法 → 使用系統 A

**例子**：調整 threshold 閾值

```python
# 創建版本 1：高精準度
SearchAlgorithmVersion.objects.create(
    version_name='高精準度搜尋',
    algorithm_type='two_stage_hybrid',
    parameters={
        'stage1_threshold': 0.8,  # 更高的閾值
        'stage2_threshold': 0.68,
        'keyword_threshold': 0.4
    }
)

# 創建版本 2：高召回率
SearchAlgorithmVersion.objects.create(
    version_name='高召回率搜尋',
    algorithm_type='two_stage_hybrid',
    parameters={
        'stage1_threshold': 0.6,  # 更低的閾值
        'stage2_threshold': 0.51,
        'keyword_threshold': 0.3
    }
)

# 執行測試對比
# 系統 A 可以在 1 分鐘內完成 50 題測試
# 立即看到 Precision/Recall 差異
```

### 場景 2：優化 AI 回答質量 → 使用系統 B

**例子**：調整 Dify Prompt 或 RAG 配置

```python
# 創建版本 1：預設 Prompt
DifyAppVersion.objects.create(
    version_name='基礎 Prompt v1.0',
    app_name='Protocol Assistant',
    rag_config={
        'retrieval_mode': 'hybrid',
        'top_k': 10,
        'score_threshold': 0.7
    }
)

# 創建版本 2：優化 Prompt
DifyAppVersion.objects.create(
    version_name='優化 Prompt v2.0',
    app_name='Protocol Assistant (Enhanced)',
    rag_config={
        'retrieval_mode': 'hybrid',
        'top_k': 15,  # 增加檢索數量
        'score_threshold': 0.65  # 降低閾值
    }
)

# 執行測試對比
# 系統 B 需要 5-10 分鐘完成 50 題測試（LLM 呼叫）
# 評估 Answer Quality 和 Faithfulness 差異
```

---

## 🎯 實施優先序

### P0 - 立即執行（本週）
1. ✅ 修正系統 A 的 `algorithm_type` 標記
2. ✅ 更新系統 A 的版本描述
3. ✅ 補充測試名稱為選填功能（已完成）

### P1 - 近期執行（下週）
4. 實現系統 A 的參數化版本執行
5. 創建多個測試版本（不同 threshold 配置）
6. 完善 Dashboard 的版本對比功能

### P2 - 中期執行（2-3 週）
7. 設計並實現系統 B 的資料庫架構
8. 開發 AI 評分引擎（核心邏輯）
9. 建立 AI 測試案例管理功能

### P3 - 長期執行（1 個月）
10. 完整實現系統 B 前後端
11. 整合 Dify API 測試流程
12. 建立雙系統統一儀表板

---

## 💡 關鍵優勢

### 系統分離的好處

1. **獨立優化**
   - 搜尋演算法迭代不影響 AI 回答測試
   - AI Prompt 調整不影響搜尋指標

2. **成本控制**
   - 系統 A：無 LLM 成本，可頻繁測試
   - 系統 B：有 LLM 成本，精準測試

3. **責任分明**
   - 搜尋團隊專注系統 A
   - AI 團隊專注系統 B

4. **數據洞察**
   - 可以量化「搜尋好 ≠ AI 回答好」的差異
   - 找出搜尋與 AI 回答的關聯性

---

## 🔍 未來擴展

### 可能的第三個系統：混合 Benchmark

**目標**：評估搜尋質量對 AI 回答質量的影響

```
系統 C：因果分析 Benchmark
    ↓
控制變量：固定 AI Prompt
    ↓
自變量：不同搜尋策略
    ↓
因變量：AI 回答質量變化
    ↓
分析：搜尋 Precision +10% → AI Relevance +X%
```

---

## 📅 時間表

| 階段 | 時間 | 目標 |
|------|------|------|
| Phase 1 | 本週 | 修正系統 A 標記，完善當前功能 |
| Phase 2 | 下週 | 實現系統 A 參數化，創建多版本 |
| Phase 3 | 2週後 | 設計系統 B 架構，建立資料庫 |
| Phase 4 | 3週後 | 開發系統 B 核心邏輯 |
| Phase 5 | 1個月後 | 系統 B 完整上線，雙系統並行 |

---

## 🎉 總結

✅ **系統 A（搜尋 Benchmark）**：專注驗證檢索能力，快速迭代，低成本

✅ **系統 B（AI Benchmark）**：專注驗證 AI 質量，端到端評估，高價值

✅ **雙軌並行**：各司其職，互補不重疊

✅ **可行性**：架構清晰，技術成熟，實施風險低

---

**📅 創建日期**：2025-11-23  
**📝 作者**：AI Development Team  
**🔖 標籤**：#benchmark #architecture #planning #dual-system
