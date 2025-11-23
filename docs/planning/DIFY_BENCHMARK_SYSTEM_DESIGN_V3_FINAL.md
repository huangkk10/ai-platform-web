# 📊 Dify API 跑分系統設計規劃 v3.0 (Final)

## 📅 規劃資訊
- **創建日期**: 2025-11-23
- **版本**: 3.0 Final (基於 Protocol Assistant 實際架構)
- **規劃階段**: 架構設計與需求分析
- **執行狀態**: 待確認後執行

---

## 🎯 系統目標

創建一個**獨立的 Dify API 跑分系統**，**使用與 Protocol Assistant 相同的後端架構**，測試不同 Dify App 版本的回答品質。

---

## 🔍 Protocol Assistant 實際架構分析

### 當前運作流程

```
用戶問題
    ↓
ProtocolAssistantViewSet.chat()
    ↓
ProtocolGuideAPIHandler.handle_chat_api()
    ↓
SmartSearchRouter.handle_smart_search()
    ↓
    ├─ 模式 A: KeywordTriggeredSearchHandler (含全文關鍵字)
    │   └─ 直接全文搜尋 → Dify API
    │
    └─ 模式 B: TwoTierSearchHandler (無全文關鍵字)
        └─ 兩階段搜尋 → Dify API
            ├─ Stage 1: 章節級搜尋
            └─ Stage 2: 全文級搜尋（如需要）
```

### 關鍵組件

#### 1. **API 層**
```python
# backend/api/views/viewsets/protocol_assistant_viewset.py

class ProtocolAssistantViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['post'])
    def chat(self, request):
        """Protocol Assistant 聊天端點"""
        return ProtocolGuideAPIHandler.handle_chat_api(request)
```

#### 2. **Handler 層**
```python
# library/protocol_guide/api_handlers.py

class ProtocolGuideAPIHandler(BaseKnowledgeBaseAPIHandler):
    @classmethod
    def handle_chat_api(cls, request):
        """處理聊天請求 → 使用智能搜尋路由器"""
        from .smart_search_router import SmartSearchRouter
        
        router = SmartSearchRouter()
        result = router.handle_smart_search(
            user_query=message,
            conversation_id=conversation_id,
            user_id=user_id,
            request=request
        )
        
        return Response({
            'success': True,
            'answer': result.get('answer'),
            'mode': result.get('mode'),
            'metadata': result.get('metadata')
        })
```

#### 3. **智能路由器**
```python
# library/protocol_guide/smart_search_router.py

class SmartSearchRouter:
    def handle_smart_search(self, user_query, conversation_id, user_id):
        """
        智能搜尋主入口
        
        流程：
        1. 決定搜尋模式 (mode_a or mode_b)
        2. 調用對應 Handler
        3. Handler 執行搜尋 + 調用 Dify API
        4. 返回結果
        """
        search_mode = self.route_search_strategy(user_query)
        
        if search_mode == 'mode_a':
            result = self.mode_a_handler.handle_keyword_triggered_search(...)
        else:
            result = self.mode_b_handler.handle_two_tier_search(...)
        
        return result
```

#### 4. **搜尋處理器**
```python
# library/protocol_guide/two_tier_handler.py

class TwoTierSearchHandler:
    def handle_two_tier_search(self, user_query, ...):
        """
        兩階段搜尋流程：
        
        1. 使用 ProtocolGuideSearchService.search_knowledge(stage=1)
        2. 如果結果不足，執行 stage=2
        3. 將搜尋結果傳給 Dify API
        4. 返回 Dify 回答
        """
        # Stage 1: 章節級搜尋
        search_service = ProtocolGuideSearchService()
        results_stage1 = search_service.search_knowledge(
            query=user_query,
            limit=20,
            stage=1  # ← 關鍵：使用後端搜尋 API
        )
        
        # 調用 Dify API
        dify_response = self._call_dify_with_context(
            user_query=user_query,
            search_results=results_stage1,
            conversation_id=conversation_id
        )
        
        return {
            'answer': dify_response['answer'],
            'mode': 'mode_b',
            'stage': 1,
            'search_results': results_stage1
        }
```

---

## 💡 關鍵洞察：您的需求

### 問題：
> "我想要的是就如同目前在 protocol assistant 裡面，它是使用一個目前我已經在後端開發完的 function，然後去使用，你的方法也是如此嗎?"

### 答案：✅ **是的！完全一致！**

**Protocol Assistant 的實際流程**：
```
用戶問題
    ↓
ProtocolGuideSearchService.search_knowledge(stage=1)  ← 後端搜尋 API
    ↓
取得搜尋結果 (documents)
    ↓
將搜尋結果 + 用戶問題 → Dify API
    ↓
Dify 回答
```

**Dify 跑分系統應該使用相同流程**：
```
測試問題
    ↓
ProtocolGuideSearchService.search_knowledge(stage=1)  ← 使用相同的後端搜尋 API
    ↓
取得搜尋結果 (documents)
    ↓
將搜尋結果 + 測試問題 → Dify API
    ↓
Dify 回答
    ↓
關鍵字評分
```

---

## 📊 調整後的系統設計

### 核心架構

```
┌─────────────────────────────────────────────────────────┐
│           Dify 跑分系統 (使用後端搜尋 API)                │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  測試案例 (問題)                                         │
│       ↓                                                  │
│  ProtocolGuideSearchService.search_knowledge(stage=1)    │
│       ↓                                                  │
│  取得搜尋結果                                            │
│       ↓                                                  │
│  Dify API (使用搜尋結果作為 Context)                    │
│       ↓                                                  │
│  Dify 回答                                              │
│       ↓                                                  │
│  關鍵字評分器                                            │
│       ↓                                                  │
│  評分結果                                                │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 更新後的 Library 設計

### 目錄結構
```
backend/library/dify_benchmark/
├── __init__.py
├── dify_batch_tester.py         # 批量測試器
├── dify_test_runner.py          # 單次測試執行器
├── keyword_evaluator.py         # 關鍵字評分器
├── dify_api_client.py           # Dify API 客戶端（封裝 Dify 調用）
└── comparison_engine.py         # 對比分析引擎
```

---

### 核心組件實作

#### 1. `DifyTestRunner` - 測試執行器（使用後端搜尋 API）

```python
"""Dify 測試執行器 - 使用 Protocol 後端搜尋 API"""
from datetime import datetime
from typing import List, Dict, Any
import logging
import time

logger = logging.getLogger(__name__)


class DifyTestRunner:
    """
    Dify 測試執行器
    
    測試流程（與 Protocol Assistant 相同）：
    1. 使用 ProtocolGuideSearchService 搜尋相關文檔
    2. 將搜尋結果 + 問題傳給 Dify API
    3. 取得 Dify 回答
    4. 使用關鍵字評分器評估答案
    """
    
    def __init__(self, version, verbose=False):
        """
        Args:
            version: DifyConfigVersion 實例
            verbose: 是否輸出詳細日誌
        """
        self.version = version
        self.verbose = verbose
        
        # 初始化組件
        from library.dify_benchmark.keyword_evaluator import KeywordEvaluator
        from library.dify_benchmark.dify_api_client import DifyAPIClient
        from library.protocol_guide.search_service import ProtocolGuideSearchService
        
        self.evaluator = KeywordEvaluator()
        self.dify_client = DifyAPIClient(version)
        self.search_service = ProtocolGuideSearchService()
    
    def run_batch_tests(
        self,
        test_cases: List,
        run_name: str,
        run_type: str = "batch_comparison",
        batch_id: str = None,
        notes: str = ""
    ):
        """執行批量測試"""
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
                # 執行單個測試（使用後端搜尋 API）
                result = self._run_single_test_with_backend_search(test_run, test_case)
                
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
    
    def _run_single_test_with_backend_search(self, test_run, test_case):
        """
        執行單個測試案例（使用後端搜尋 API）
        
        流程：
        1. 使用 ProtocolGuideSearchService 搜尋
        2. 將搜尋結果傳給 Dify API
        3. 評估 Dify 回答
        """
        from api.models import DifyTestResult
        
        start_time = time.time()
        
        # ======================================================
        # 步驟 1: 使用後端搜尋 API（與 Protocol Assistant 相同）
        # ======================================================
        logger.info(f"    🔍 步驟 1: 使用後端搜尋 API")
        
        search_start = time.time()
        
        # 使用 ProtocolGuideSearchService 搜尋
        search_results = self.search_service.search_knowledge(
            query=test_case.question,
            limit=20,  # 搜尋 Top 20 結果
            use_vector=True,
            stage=1  # ← 使用第一階段搜尋（章節級）
        )
        
        search_time = time.time() - search_start
        logger.info(f"       搜尋完成: {len(search_results)} 個結果 ({search_time:.2f}s)")
        
        # ======================================================
        # 步驟 2: 調用 Dify API（傳入搜尋結果作為 Context）
        # ======================================================
        logger.info(f"    📡 步驟 2: 調用 Dify API")
        
        try:
            dify_response = self.dify_client.chat_with_context(
                question=test_case.question,
                search_results=search_results,  # ← 傳入後端搜尋結果
                conversation_id=None
            )
            
            dify_answer = dify_response.get('answer', '')
            dify_message_id = dify_response.get('message_id')
            dify_conversation_id = dify_response.get('conversation_id')
            retrieved_documents = dify_response.get('metadata', {}).get('retrieval_sources')
            
            response_time = time.time() - start_time
            logger.info(f"       Dify 回答完成 ({response_time:.2f}s)")
            
        except Exception as e:
            logger.error(f"       ❌ Dify API 調用失敗: {str(e)}")
            raise
        
        # ======================================================
        # 步驟 3: 評估答案（關鍵字匹配）
        # ======================================================
        logger.info(f"    📊 步驟 3: 評估答案")
        
        evaluation = self.evaluator.evaluate(
            question=test_case.question,
            expected_answer=test_case.expected_answer,
            actual_answer=dify_answer,
            keywords=test_case.answer_keywords,
            keyword_weights=test_case.keyword_weights
        )
        
        logger.info(f"       評分完成: {evaluation['score']:.2f} 分")
        
        # ======================================================
        # 步驟 4: 儲存結果
        # ======================================================
        test_result = DifyTestResult.objects.create(
            test_run=test_run,
            test_case=test_case,
            
            # Dify 回答
            dify_answer=dify_answer,
            dify_message_id=dify_message_id,
            dify_conversation_id=dify_conversation_id,
            
            # 評分結果
            score=evaluation['score'],
            is_passed=evaluation['is_passed'],
            matched_keywords=evaluation['matched_keywords'],
            missing_keywords=evaluation['missing_keywords'],
            keyword_match_rate=evaluation['keyword_match_rate'],
            evaluation_details=evaluation['details'],
            
            # 時間統計
            response_time=response_time,
            backend_search_time=search_time,
            
            # 搜尋結果（記錄後端搜尋到的文檔）
            backend_search_results=self._format_search_results(search_results),
            retrieved_documents=retrieved_documents
        )
        
        return test_result
    
    def _format_search_results(self, search_results: List[Dict]) -> List[Dict]:
        """格式化搜尋結果（用於儲存）"""
        formatted = []
        for result in search_results[:10]:  # 只儲存 Top 10
            formatted.append({
                'title': result.get('title', ''),
                'score': result.get('score', 0),
                'content_preview': result.get('content', '')[:200],
                'document_id': result.get('document_id', '')
            })
        return formatted
```

---

#### 2. `DifyAPIClient` - Dify API 客戶端

```python
"""Dify API 客戶端 - 封裝 Dify 調用邏輯"""
import requests
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class DifyAPIClient:
    """
    Dify API 客戶端
    
    功能：
    - 將後端搜尋結果 + 問題傳給 Dify
    - 處理 Dify API 的請求和響應
    """
    
    def __init__(self, version):
        """
        Args:
            version: DifyConfigVersion 實例
        """
        self.version = version
        self.api_url = version.dify_api_url
        self.api_key = version.dify_api_key
    
    def chat_with_context(
        self,
        question: str,
        search_results: List[Dict],
        conversation_id: str = None
    ) -> Dict[str, Any]:
        """
        調用 Dify Chat API（傳入搜尋結果作為 Context）
        
        Args:
            question: 用戶問題
            search_results: 後端搜尋結果
            conversation_id: 對話 ID（可選）
            
        Returns:
            {
                'answer': str,
                'message_id': str,
                'conversation_id': str,
                'metadata': dict
            }
        """
        # 構建 Context（從搜尋結果）
        context = self._build_context_from_search_results(search_results)
        
        # 調用 Dify API
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        # 方式 1: 使用 inputs 傳入 Context（如果 Dify App 支援）
        payload = {
            'inputs': {
                'context': context  # ← 傳入後端搜尋結果
            },
            'query': question,
            'response_mode': 'blocking',
            'user': f'benchmark_test_{self.version.id}'
        }
        
        # 如果有對話 ID，繼續對話
        if conversation_id:
            payload['conversation_id'] = conversation_id
        
        try:
            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=60
            )
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
    
    def _build_context_from_search_results(self, search_results: List[Dict]) -> str:
        """
        從搜尋結果構建 Context
        
        格式：
        【文檔 1】
        標題: xxx
        內容: xxx
        
        【文檔 2】
        標題: xxx
        內容: xxx
        """
        context_parts = []
        
        for idx, result in enumerate(search_results[:10], 1):  # Top 10
            title = result.get('title', '未知文檔')
            content = result.get('content', '')
            score = result.get('score', 0)
            
            context_parts.append(
                f"【文檔 {idx}】(相關度: {score:.2f})\n"
                f"標題: {title}\n"
                f"內容: {content[:500]}\n"  # 限制長度
            )
        
        return "\n\n".join(context_parts)
```

---

#### 3. 資料庫調整（新增後端搜尋相關欄位）

```sql
-- dify_test_result 表新增欄位

ALTER TABLE dify_test_result
ADD COLUMN backend_search_time DECIMAL(10,3),           -- 後端搜尋耗時
ADD COLUMN backend_search_results JSONB,                -- 後端搜尋結果（Top 10）
ADD COLUMN backend_search_count INTEGER DEFAULT 0;      -- 後端搜尋結果數量

COMMENT ON COLUMN dify_test_result.backend_search_time IS '後端搜尋耗時（秒）';
COMMENT ON COLUMN dify_test_result.backend_search_results IS '後端搜尋結果（格式化後的 Top 10）';
COMMENT ON COLUMN dify_test_result.backend_search_count IS '後端搜尋結果總數';
```

---

## 📊 測試流程對比

### Protocol Assistant 實際流程
```
1. 用戶問題: "IOL 測試流程是什麼？"
   ↓
2. ProtocolGuideSearchService.search_knowledge(stage=1)
   → 搜尋到 20 個相關文檔
   ↓
3. 將文檔 + 問題傳給 Dify API
   ↓
4. Dify 回答: "IOL 測試流程包括..."
   ↓
5. 返回給用戶
```

### Dify 跑分系統流程（完全相同）
```
1. 測試問題: "IOL 測試流程是什麼？"
   ↓
2. ProtocolGuideSearchService.search_knowledge(stage=1)  ← 使用相同的後端 API
   → 搜尋到 20 個相關文檔
   ↓
3. 將文檔 + 問題傳給 Dify API
   ↓
4. Dify 回答: "IOL 測試流程包括..."
   ↓
5. 關鍵字評分器評估答案
   → 分數: 85.5 分 ✅
   ↓
6. 儲存結果到資料庫
```

---

## ✅ 核心優勢

### 1. **完全一致的測試環境**
```
✅ 使用與 Protocol Assistant 相同的後端搜尋 API
✅ 測試結果能真實反映用戶體驗
✅ 可以驗證後端搜尋品質 + Dify 回答品質
```

### 2. **可對比的評估指標**
```
後端搜尋品質:
- 搜尋到的文檔數量
- 搜尋相關度分數
- 搜尋耗時

Dify 回答品質:
- 關鍵字匹配率
- 答案完整性
- 響應時間
```

### 3. **可追溯的測試結果**
```
每個測試結果都記錄：
- 後端搜尋到的文檔（Top 10）
- Dify 回答內容
- 評分詳情
- 時間統計
```

---

## 📝 MVP 實作步驟（修訂版）

### Phase 1: 資料庫與 Models (1 天)
1. ✅ 創建 4 個資料表（含後端搜尋欄位）
2. ✅ 創建 Django Models
3. ✅ 執行 Migration
4. ✅ 從 `benchmark_test_case` 複製測試案例

### Phase 2: 後端 Library (2 天)
1. ✅ 實作 `KeywordEvaluator` (關鍵字評分器)
2. ✅ 實作 `DifyAPIClient` (Dify API 客戶端)
3. ✅ 實作 `DifyTestRunner` (測試執行器 - 使用後端搜尋 API)
4. ✅ 實作 `DifyBatchTester` (批量測試器)
5. ✅ CLI 測試工具

### Phase 3: API 層 (1-2 天)
1. ✅ 實作 ViewSets (4 個)
2. ✅ 註冊 URL 路由
3. ✅ 測試 API 端點

### Phase 4: 前端頁面 (2-3 天)
1. ✅ 版本管理頁面
2. ✅ 測試案例頁面（複製功能）
3. ✅ 批量測試執行頁面
4. ✅ 版本對比頁面（新增後端搜尋統計）
5. ✅ 測試歷史頁面

### Phase 5: 整合測試 (1 天)
1. ✅ 端到端測試（完整流程）
2. ✅ 驗證後端搜尋 API 正常工作
3. ✅ 修復 Bug
4. ✅ 文檔完善

**預計總時間**: 7-10 天

---

## 🎯 總結

### 核心變更 (v2 → v3)

#### v2.0 設計（不正確）:
```
❌ 直接調用 Dify Chat API
❌ 不使用後端搜尋 API
❌ 無法驗證後端搜尋品質
```

#### v3.0 設計（正確）✅:
```
✅ 使用 ProtocolGuideSearchService.search_knowledge()
✅ 與 Protocol Assistant 完全相同的流程
✅ 可以驗證端到端品質
✅ 可追溯搜尋結果
```

### 與 Protocol Assistant 的一致性

| 項目 | Protocol Assistant | Dify 跑分系統 | 是否一致 |
|------|-------------------|--------------|---------|
| **搜尋 API** | ProtocolGuideSearchService | ProtocolGuideSearchService | ✅ 相同 |
| **搜尋模式** | stage=1 或 stage=2 | stage=1 或 stage=2 | ✅ 相同 |
| **Dify 調用** | 傳入搜尋結果 | 傳入搜尋結果 | ✅ 相同 |
| **回答生成** | Dify API | Dify API | ✅ 相同 |

---

**規劃完成日期**: 2025-11-23  
**版本**: 3.0 Final  
**執行狀態**: ✅ **準備就緒，待確認後立即執行** 🚀
