# 📋 Dify API 跑分系統 - 完整實作規劃

## 📅 規劃資訊
- **創建日期**: 2025-11-23
- **預計開發時間**: 10-15 天
- **狀態**: 規劃完成，待執行 ⏳
- **負責人**: AI Platform Team

---

## 🎯 專案概述

### 目標
創建一個**獨立的 Dify API 跑分系統**，用於評估不同版本的 Dify 配置在相同測試案例下的表現。

### 與 Benchmark 測試系統的差異

| 項目 | Benchmark 測試系統 | Dify 跑分系統 |
|------|-------------------|--------------|
| **測試對象** | 後端搜尋演算法 | Dify API 回答品質 |
| **測試方式** | 直接查詢資料庫 | Backend Search → Dify API → Evaluation |
| **評分標準** | Precision, Recall, F1 | 關鍵字匹配度 (100%) |
| **資料表** | `search_algorithm_version` 等 | `dify_config_version` 等 |
| **API 路由** | `/api/benchmark/*` | `/api/dify-benchmark/*` |
| **前端路由** | `/benchmark/*` | `/dify-benchmark/*` |

---

## 📊 第一個測試版本配置

### 版本資訊
```python
version_name = "Dify 二階搜尋 v1.1"
version_code = "dify-two-tier-v1.1"
dify_app_id = "app-MgZZOhADkEmdUrj2DtQLJ23G"  # Protocol Guide
```

### 實際權重配置（來自 Protocol Assistant）

根據系統目前的設定（來自 Threshold 設定頁面）：

**第一階段：分段向量搜尋（Section-level Vector Search）**
- 段落向量 Threshold: **80%**
- 標題權重: **95%**
- 內容權重: **5%**
- 說明: 極度強調標題匹配，適合查找特定章節

**第二階段：全文向量搜尋（Full Document Vector Search）**
- 段落向量 Threshold: **80%**
- 標題權重: **10%**
- 內容權重: **90%**
- 說明: 極度強調內容匹配，適合理解完整文檔脈絡

### 版本描述（完整版）
```
📝 Dify 二階搜尋版本
🎯 使用場景：Protocol 相關問題查詢，結合分段與全文搜尋策略

⚙️ 搜尋策略配置：
   
   第一階段：分段向量搜尋（Section-level Vector Search）
     • 段落向量 Threshold：80%
     • 標題權重：95%
     • 內容權重：5%
     • 說明：極度強調標題匹配，適合查找特定章節
   
   第二階段：全文向量搜尋（Full Document Vector Search）
     • 段落向量 Threshold：80%
     • 標題權重：10%
     • 內容權重：90%
     • 說明：極度強調內容匹配，適合理解完整文檔脈絡

⚙️ Dify 配置：
   - App ID: app-MgZZOhADkEmdUrj2DtQLJ23G (Protocol Guide)
   - 後端搜尋：使用 ProtocolGuideSearchService.search_knowledge(stage=1)
   - 上下文來源：二階搜尋結果（最多 20 筆文檔）
   - 響應模式：Blocking（同步回應）

📊 技術特點：
   - ✅ 第一階段：標題導向（95/5），快速定位章節位置
   - ✅ 第二階段：內容導向（10/90），深度理解文檔內容
   - ✅ 兩階段形成互補：先精準定位，後全文理解
   - ✅ Threshold 保持一致（80%），確保搜尋品質
   - ✅ 透過後端搜尋 API 提供高品質上下文給 Dify

🎯 預期效果：
   - 提高 Protocol SOP 類問題的精準度
   - 第一階段快速找到相關章節（標題匹配）
   - 第二階段深入理解內容細節（內容匹配）
   - 兼顧定位速度和理解深度
```

---

## 🗓️ Phase 1: 資料庫設計與 Models（1-2 天）

### 任務清單

#### 1.1 創建資料庫 Migration 檔案
```bash
# 在 Django 容器中執行
docker exec ai-django python manage.py makemigrations --name dify_benchmark_system
```

#### 1.2 資料表設計

**5 個核心資料表**：

```sql
-- 1. dify_config_version - Dify 配置版本表
CREATE TABLE dify_config_version (
    id SERIAL PRIMARY KEY,
    version_name VARCHAR(200) NOT NULL UNIQUE,
    version_code VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    
    -- Dify 配置
    dify_app_id VARCHAR(100),
    dify_api_key VARCHAR(200),
    dify_api_url VARCHAR(500) DEFAULT 'http://10.10.172.37/v1/chat-messages',
    
    -- 版本管理
    is_active BOOLEAN DEFAULT true,
    is_baseline BOOLEAN DEFAULT false,
    created_by_id INTEGER REFERENCES auth_user(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. dify_benchmark_test_case - 測試案例表
CREATE TABLE dify_benchmark_test_case (
    id SERIAL PRIMARY KEY,
    question TEXT NOT NULL,
    test_class_name VARCHAR(200),
    
    -- 評分標準
    expected_answer TEXT,
    answer_keywords JSONB,  -- ["keyword1", "keyword2"]
    
    -- 測試案例屬性
    difficulty_level VARCHAR(20),  -- easy, medium, hard
    question_type VARCHAR(50),
    max_score DECIMAL(5,2) DEFAULT 100.00,
    
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. dify_test_run - 測試執行記錄表
CREATE TABLE dify_test_run (
    id SERIAL PRIMARY KEY,
    version_id INTEGER REFERENCES dify_config_version(id) ON DELETE CASCADE,
    
    run_name VARCHAR(300),
    batch_id VARCHAR(100),
    
    -- 統計
    total_test_cases INTEGER DEFAULT 0,
    passed_cases INTEGER DEFAULT 0,
    average_score DECIMAL(5,2),
    pass_rate DECIMAL(5,2),
    average_response_time DECIMAL(10,2),
    
    -- 細項評分
    completeness_score DECIMAL(5,2),
    accuracy_score DECIMAL(5,2),
    relevance_score DECIMAL(5,2),
    
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. dify_test_result - 單題測試結果表
CREATE TABLE dify_test_result (
    id SERIAL PRIMARY KEY,
    test_run_id INTEGER REFERENCES dify_test_run(id) ON DELETE CASCADE,
    test_case_id INTEGER REFERENCES dify_benchmark_test_case(id),
    
    dify_answer TEXT,
    dify_message_id VARCHAR(200),
    
    score DECIMAL(5,2),
    is_passed BOOLEAN,
    
    completeness_score DECIMAL(5,2),
    accuracy_score DECIMAL(5,2),
    relevance_score DECIMAL(5,2),
    
    matched_keywords JSONB,
    missing_keywords JSONB,
    response_time DECIMAL(10,3),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. dify_answer_evaluation - 答案評分記錄表
CREATE TABLE dify_answer_evaluation (
    id SERIAL PRIMARY KEY,
    test_result_id INTEGER REFERENCES dify_test_result(id) ON DELETE CASCADE,
    
    question TEXT,
    expected_answer TEXT,
    actual_answer TEXT,
    
    evaluator_model VARCHAR(100),  -- "keyword_only"
    evaluation_response TEXT,
    scores JSONB,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 1.3 創建 Django Models

檔案：`backend/api/models.py`

```python
# 在現有 models.py 中添加

class DifyConfigVersion(models.Model):
    """Dify 配置版本"""
    version_name = models.CharField(max_length=200, unique=True, verbose_name="版本名稱")
    version_code = models.CharField(max_length=100, unique=True, verbose_name="版本代碼")
    description = models.TextField(blank=True, verbose_name="描述")
    
    dify_app_id = models.CharField(max_length=100, verbose_name="Dify App ID")
    dify_api_key = models.CharField(max_length=200, verbose_name="Dify API Key")
    dify_api_url = models.CharField(
        max_length=500,
        default='http://10.10.172.37/v1/chat-messages',
        verbose_name="Dify API URL"
    )
    
    is_active = models.BooleanField(default=True, verbose_name="啟用")
    is_baseline = models.BooleanField(default=False, verbose_name="基準版本")
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'dify_config_version'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.version_name} ({self.version_code})"


class DifyBenchmarkTestCase(models.Model):
    """Dify 測試案例"""
    question = models.TextField(verbose_name="測試問題")
    test_class_name = models.CharField(max_length=200, blank=True, verbose_name="測試類別")
    
    expected_answer = models.TextField(blank=True, verbose_name="期望答案")
    answer_keywords = models.JSONField(default=list, verbose_name="關鍵字")
    
    difficulty_level = models.CharField(
        max_length=20,
        choices=[('easy', '簡單'), ('medium', '中等'), ('hard', '困難')],
        default='medium',
        verbose_name="難度"
    )
    question_type = models.CharField(max_length=50, blank=True, verbose_name="問題類型")
    max_score = models.DecimalField(max_digits=5, decimal_places=2, default=100, verbose_name="滿分")
    
    is_active = models.BooleanField(default=True, verbose_name="啟用")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'dify_benchmark_test_case'
        ordering = ['id']
    
    def __str__(self):
        return f"{self.question[:50]}..."


class DifyTestRun(models.Model):
    """Dify 測試執行記錄"""
    version = models.ForeignKey(DifyConfigVersion, on_delete=models.CASCADE, related_name='test_runs')
    
    run_name = models.CharField(max_length=300, verbose_name="測試名稱")
    batch_id = models.CharField(max_length=100, blank=True, verbose_name="批次ID")
    
    total_test_cases = models.IntegerField(default=0, verbose_name="總測試案例數")
    passed_cases = models.IntegerField(default=0, verbose_name="通過案例數")
    average_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, verbose_name="平均分數")
    pass_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, verbose_name="通過率")
    average_response_time = models.DecimalField(max_digits=10, decimal_places=2, null=True, verbose_name="平均響應時間")
    
    completeness_score = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    accuracy_score = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    relevance_score = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    
    started_at = models.DateTimeField(null=True)
    completed_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'dify_test_run'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.run_name} - {self.version.version_name}"


class DifyTestResult(models.Model):
    """Dify 單題測試結果"""
    test_run = models.ForeignKey(DifyTestRun, on_delete=models.CASCADE, related_name='results')
    test_case = models.ForeignKey(DifyBenchmarkTestCase, on_delete=models.CASCADE)
    
    dify_answer = models.TextField(verbose_name="Dify 回答")
    dify_message_id = models.CharField(max_length=200, blank=True)
    
    score = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="分數")
    is_passed = models.BooleanField(verbose_name="通過")
    
    completeness_score = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    accuracy_score = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    relevance_score = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    
    matched_keywords = models.JSONField(default=list)
    missing_keywords = models.JSONField(default=list)
    response_time = models.DecimalField(max_digits=10, decimal_places=3, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'dify_test_result'
        ordering = ['id']


class DifyAnswerEvaluation(models.Model):
    """Dify 答案評分記錄"""
    test_result = models.ForeignKey(DifyTestResult, on_delete=models.CASCADE, related_name='evaluations')
    
    question = models.TextField()
    expected_answer = models.TextField(blank=True)
    actual_answer = models.TextField()
    
    evaluator_model = models.CharField(max_length=100, default='keyword_only')
    evaluation_response = models.TextField(blank=True)
    scores = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'dify_answer_evaluation'
```

#### 1.4 執行 Migration

```bash
# 生成 migration
docker exec ai-django python manage.py makemigrations

# 執行 migration
docker exec ai-django python manage.py migrate

# 驗證資料表
docker exec postgres_db psql -U postgres -d ai_platform -c "\dt dify*"
```

#### 1.5 創建第一個測試版本

創建腳本：`backend/scripts/create_dify_baseline_version.py`

```python
#!/usr/bin/env python
"""創建 Dify 基準測試版本"""
import os
import sys
import django

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.models import DifyConfigVersion
from django.contrib.auth.models import User

def create_baseline_version():
    """創建 Dify 二階搜尋 v1.1 版本"""
    
    admin_user = User.objects.filter(is_superuser=True).first()
    
    version, created = DifyConfigVersion.objects.get_or_create(
        version_code="dify-two-tier-v1.1",
        defaults={
            'version_name': "Dify 二階搜尋 v1.1",
            'dify_app_id': "app-MgZZOhADkEmdUrj2DtQLJ23G",
            'dify_api_key': "app-Lp4mlfIWHqMWPHTlzF9ywT4F",  # 需要實際的 API Key
            'description': """
📝 Dify 二階搜尋版本
🎯 使用場景：Protocol 相關問題查詢，結合分段與全文搜尋策略

⚙️ 搜尋策略配置：
   
   第一階段：分段向量搜尋（Section-level Vector Search）
     • 段落向量 Threshold：80%
     • 標題權重：95%
     • 內容權重：5%
     • 說明：極度強調標題匹配，適合查找特定章節
   
   第二階段：全文向量搜尋（Full Document Vector Search）
     • 段落向量 Threshold：80%
     • 標題權重：10%
     • 內容權重：90%
     • 說明：極度強調內容匹配，適合理解完整文檔脈絡

⚙️ Dify 配置：
   - App ID: app-MgZZOhADkEmdUrj2DtQLJ23G (Protocol Guide)
   - 後端搜尋：使用 ProtocolGuideSearchService.search_knowledge(stage=1)
   - 上下文來源：二階搜尋結果（最多 20 筆文檔）
   - 響應模式：Blocking（同步回應）

📊 技術特點：
   - ✅ 第一階段：標題導向（95/5），快速定位章節位置
   - ✅ 第二階段：內容導向（10/90），深度理解文檔內容
   - ✅ 兩階段形成互補：先精準定位，後全文理解
   - ✅ Threshold 保持一致（80%），確保搜尋品質
   - ✅ 透過後端搜尋 API 提供高品質上下文給 Dify

🎯 預期效果：
   - 提高 Protocol SOP 類問題的精準度
   - 第一階段快速找到相關章節（標題匹配）
   - 第二階段深入理解內容細節（內容匹配）
   - 兼顧定位速度和理解深度
            """,
            'is_active': True,
            'is_baseline': True,
            'created_by': admin_user
        }
    )
    
    if created:
        print(f"✅ 成功創建版本: {version.version_name}")
    else:
        print(f"⚠️ 版本已存在: {version.version_name}")
    
    print(f"   版本代碼: {version.version_code}")
    print(f"   App ID: {version.dify_app_id}")

if __name__ == "__main__":
    create_baseline_version()
```

---

## 🗓️ Phase 2: 後端 Library 實作（2-3 天）

### 目錄結構

```
backend/library/dify_benchmark/
├── __init__.py
├── dify_batch_tester.py         # 批量測試器
├── dify_test_runner.py          # 測試執行器
├── dify_api_client.py           # Dify API 客戶端
└── evaluators/
    ├── __init__.py
    └── keyword_evaluator.py     # 關鍵字評分器
```

### 核心組件設計

#### 2.1 DifyAPIClient - Dify API 客戶端

**整合流程**：
```
Question
  ↓
ProtocolGuideSearchService.search_knowledge(stage=1)  ← 後端搜尋
  ↓
Search Results (20 documents)
  ↓
DifyAPIClient.chat_with_context(question, search_results)  ← 發送到 Dify
  ↓
Dify Answer
  ↓
KeywordEvaluator.evaluate()  ← 評分
  ↓
Score & Results
```

檔案：`backend/library/dify_benchmark/dify_api_client.py`

```python
"""Dify API 客戶端 - 整合後端搜尋"""
import requests
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class DifyAPIClient:
    """
    Dify API 客戶端
    
    整合後端搜尋結果作為上下文，發送到 Dify API
    """
    
    def __init__(self, api_url: str, api_key: str, timeout: int = 60):
        self.api_url = api_url
        self.api_key = api_key
        self.timeout = timeout
    
    def chat_with_backend_search(
        self,
        question: str,
        user_id: str,
        conversation_id: str = None
    ) -> Dict[str, Any]:
        """
        使用後端搜尋結果作為上下文，發送問題到 Dify
        
        流程：
        1. 使用 ProtocolGuideSearchService 搜尋相關文檔
        2. 將搜尋結果格式化為上下文
        3. 發送到 Dify API
        
        Returns:
            {
                'success': bool,
                'answer': str,
                'message_id': str,
                'search_results': [...],
                'error': str (if failed)
            }
        """
        try:
            # Step 1: 使用後端搜尋獲取上下文
            from library.protocol_guide.search_service import ProtocolGuideSearchService
            
            search_service = ProtocolGuideSearchService()
            search_results = search_service.search_knowledge(
                query=question,
                limit=20,
                stage=1  # 使用 stage=1（二階搜尋）
            )
            
            logger.info(f"後端搜尋找到 {len(search_results)} 筆相關文檔")
            
            # Step 2: 格式化搜尋結果為上下文
            context = self._format_search_results_as_context(search_results)
            
            # Step 3: 發送到 Dify API
            payload = {
                "inputs": {
                    "context": context,  # 搜尋結果作為上下文
                },
                "query": question,
                "user": user_id,
                "response_mode": "blocking"
            }
            
            if conversation_id:
                payload["conversation_id"] = conversation_id
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'answer': data.get('answer', ''),
                    'message_id': data.get('message_id'),
                    'conversation_id': data.get('conversation_id'),
                    'search_results': search_results
                }
            else:
                logger.error(f"Dify API 錯誤: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f"API Error: {response.status_code}"
                }
        
        except Exception as e:
            logger.error(f"Dify API 調用失敗: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _format_search_results_as_context(self, search_results: List[Dict]) -> str:
        """將搜尋結果格式化為 Dify 可理解的上下文"""
        context_parts = []
        
        for idx, result in enumerate(search_results[:20], 1):  # 最多 20 筆
            title = result.get('title', 'Unknown')
            content = result.get('content', '')
            score = result.get('score', 0)
            
            context_parts.append(
                f"[文檔 {idx}] {title}\n"
                f"相關度: {score:.2f}\n"
                f"內容: {content}\n"
            )
        
        return "\n---\n".join(context_parts)
```

#### 2.2 KeywordEvaluator - 關鍵字評分器

檔案：`backend/library/dify_benchmark/evaluators/keyword_evaluator.py`

```python
"""關鍵字評分器 - 100% 關鍵字匹配評分"""
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class KeywordEvaluator:
    """
    關鍵字評分器
    
    評分方式：100% 基於關鍵字匹配
    - 匹配到的關鍵字越多，分數越高
    - 及格分數：60 分
    """
    
    def evaluate(
        self,
        question: str,
        expected_answer: str,
        actual_answer: str,
        keywords: List[str]
    ) -> Dict[str, Any]:
        """
        評估答案品質
        
        Returns:
            {
                'score': float (0-100),
                'is_passed': bool,
                'matched_keywords': List[str],
                'missing_keywords': List[str],
                'match_rate': float (0-1)
            }
        """
        if not keywords:
            # 如果沒有關鍵字，給予基本分數
            return {
                'score': 50.0,
                'is_passed': False,
                'matched_keywords': [],
                'missing_keywords': [],
                'match_rate': 0.0
            }
        
        # 計算關鍵字匹配
        matched = []
        missing = []
        
        actual_answer_lower = actual_answer.lower()
        
        for keyword in keywords:
            if keyword.lower() in actual_answer_lower:
                matched.append(keyword)
            else:
                missing.append(keyword)
        
        # 計算分數
        match_rate = len(matched) / len(keywords)
        score = match_rate * 100
        
        logger.info(
            f"關鍵字評分: {score:.2f} "
            f"(匹配: {len(matched)}/{len(keywords)})"
        )
        
        return {
            'score': round(score, 2),
            'is_passed': score >= 60,
            'matched_keywords': matched,
            'missing_keywords': missing,
            'match_rate': round(match_rate, 2),
            'completeness_score': round(score, 2),
            'accuracy_score': round(score, 2),
            'relevance_score': round(score, 2)
        }
```

#### 2.3 DifyTestRunner - 測試執行器

（參考 DIFY_BENCHMARK_SYSTEM_DESIGN.md 中的完整實作）

#### 2.4 DifyBatchTester - 批量測試器

（參考 DIFY_BENCHMARK_SYSTEM_DESIGN.md 中的完整實作）

---

## 🗓️ Phase 3: API ViewSets 實作（2-3 天）

### 3.1 創建 ViewSets

檔案：`backend/api/views/viewsets/dify_benchmark_viewsets.py`

```python
"""Dify Benchmark ViewSets"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from api.models import (
    DifyConfigVersion,
    DifyBenchmarkTestCase,
    DifyTestRun,
    DifyTestResult
)
from api.serializers import (
    DifyConfigVersionSerializer,
    DifyBenchmarkTestCaseSerializer,
    DifyTestRunSerializer,
    DifyTestResultSerializer
)
from library.dify_benchmark.dify_batch_tester import DifyBatchTester
import logging

logger = logging.getLogger(__name__)


class DifyConfigVersionViewSet(viewsets.ModelViewSet):
    """Dify 配置版本 ViewSet"""
    queryset = DifyConfigVersion.objects.all()
    serializer_class = DifyConfigVersionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=True, methods=['post'])
    def set_baseline(self, request, pk=None):
        """設定為基準版本"""
        version = self.get_object()
        
        # 清除其他基準版本
        DifyConfigVersion.objects.filter(is_baseline=True).update(is_baseline=False)
        
        # 設定為基準
        version.is_baseline = True
        version.save()
        
        return Response({
            'success': True,
            'message': f'已設定 {version.version_name} 為基準版本'
        })


class DifyBenchmarkTestCaseViewSet(viewsets.ModelViewSet):
    """Dify 測試案例 ViewSet"""
    queryset = DifyBenchmarkTestCase.objects.all()
    serializer_class = DifyBenchmarkTestCaseSerializer
    permission_classes = [permissions.IsAuthenticated]


class DifyBatchTestViewSet(viewsets.ViewSet):
    """Dify 批量測試 ViewSet"""
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def execute(self, request):
        """執行批量測試"""
        version_ids = request.data.get('version_ids')
        test_case_ids = request.data.get('test_case_ids')
        batch_name = request.data.get('batch_name')
        notes = request.data.get('notes', '')
        
        if not version_ids:
            return Response({
                'success': False,
                'error': '請選擇至少一個版本'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not test_case_ids:
            return Response({
                'success': False,
                'error': '請選擇至少一個測試案例'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 執行批量測試
        tester = DifyBatchTester(verbose=True)
        result = tester.run_batch_test(
            version_ids=version_ids,
            test_case_ids=test_case_ids,
            batch_name=batch_name,
            notes=notes,
            use_ai_evaluator=False  # 只使用關鍵字評分
        )
        
        return Response(result)


class DifyTestRunViewSet(viewsets.ReadOnlyModelViewSet):
    """Dify 測試記錄 ViewSet"""
    queryset = DifyTestRun.objects.all()
    serializer_class = DifyTestRunSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        """獲取測試結果"""
        test_run = self.get_object()
        results = test_run.results.all()
        serializer = DifyTestResultSerializer(results, many=True)
        return Response(serializer.data)


class DifyComparisonViewSet(viewsets.ViewSet):
    """Dify 對比分析 ViewSet"""
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def by_batch(self, request):
        """根據 batch_id 獲取對比資料"""
        batch_id = request.query_params.get('batch_id')
        
        if not batch_id:
            return Response({
                'success': False,
                'error': '缺少 batch_id 參數'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        test_runs = DifyTestRun.objects.filter(batch_id=batch_id)
        
        if not test_runs.exists():
            return Response({
                'success': False,
                'error': f'找不到 batch_id={batch_id} 的測試記錄'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # 生成對比資料
        comparison_data = self._generate_comparison(test_runs)
        
        return Response(comparison_data)
    
    def _generate_comparison(self, test_runs):
        """生成對比資料"""
        versions = []
        
        for tr in test_runs:
            versions.append({
                'version_id': tr.version.id,
                'version_name': tr.version.version_name,
                'test_run_id': tr.id,
                'average_score': float(tr.average_score or 0),
                'pass_rate': float(tr.pass_rate or 0),
                'completeness_score': float(tr.completeness_score or 0),
                'accuracy_score': float(tr.accuracy_score or 0),
                'relevance_score': float(tr.relevance_score or 0),
                'average_response_time': float(tr.average_response_time or 0)
            })
        
        return {
            'success': True,
            'batch_id': test_runs[0].batch_id if test_runs else None,
            'versions': versions
        }
```

### 3.2 註冊 URL 路由

檔案：`backend/api/urls.py`

```python
# 在現有的 router 中添加

from api.views.viewsets.dify_benchmark_viewsets import (
    DifyConfigVersionViewSet,
    DifyBenchmarkTestCaseViewSet,
    DifyBatchTestViewSet,
    DifyTestRunViewSet,
    DifyComparisonViewSet
)

# Dify Benchmark 路由
router.register(r'dify-benchmark/versions', DifyConfigVersionViewSet, basename='dify-version')
router.register(r'dify-benchmark/test-cases', DifyBenchmarkTestCaseViewSet, basename='dify-test-case')
router.register(r'dify-benchmark/batch-test', DifyBatchTestViewSet, basename='dify-batch-test')
router.register(r'dify-benchmark/test-runs', DifyTestRunViewSet, basename='dify-test-run')
router.register(r'dify-benchmark/comparison', DifyComparisonViewSet, basename='dify-comparison')
```

---

## 🗓️ Phase 4: 前端實作（3-4 天）

### 4.1 目錄結構

```
frontend/src/
├── pages/
│   └── dify-benchmark/
│       ├── DifyBenchmarkDashboard.js
│       ├── DifyVersionManagementPage.js
│       ├── DifyTestCaseManagementPage.js
│       ├── DifyBatchTestExecutionPage.js
│       ├── DifyBatchComparisonPage.js
│       └── DifyTestHistoryPage.js
├── services/
│   └── difyBenchmarkApi.js
└── components/
    └── dify-benchmark/
        ├── VersionTable.jsx
        ├── TestCaseTable.jsx
        └── ComparisonRadarChart.jsx
```

### 4.2 核心頁面實作

#### DifyBatchTestExecutionPage.js
```javascript
import React, { useState, useEffect } from 'react';
import { Card, Checkbox, Button, Progress, message } from 'antd';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';

const DifyBatchTestExecutionPage = () => {
  const navigate = useNavigate();
  const [versions, setVersions] = useState([]);
  const [testCases, setTestCases] = useState([]);
  const [selectedVersions, setSelectedVersions] = useState([]);
  const [selectedTestCases, setSelectedTestCases] = useState([]);
  const [testing, setTesting] = useState(false);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    fetchVersions();
    fetchTestCases();
  }, []);

  const fetchVersions = async () => {
    const response = await api.get('/api/dify-benchmark/versions/');
    setVersions(response.data.filter(v => v.is_active));
  };

  const fetchTestCases = async () => {
    const response = await api.get('/api/dify-benchmark/test-cases/');
    setTestCases(response.data.filter(tc => tc.is_active));
  };

  const handleExecuteTest = async () => {
    if (selectedVersions.length === 0 || selectedTestCases.length === 0) {
      message.error('請選擇版本和測試案例');
      return;
    }

    setTesting(true);
    setProgress(0);

    try {
      const response = await api.post('/api/dify-benchmark/batch-test/execute/', {
        version_ids: selectedVersions,
        test_case_ids: selectedTestCases,
        batch_name: `批量測試 ${new Date().toLocaleString()}`
      });

      if (response.data.success) {
        message.success('測試完成！');
        navigate(`/dify-benchmark/comparison/${response.data.batch_id}`);
      } else {
        message.error(response.data.error);
      }
    } catch (error) {
      message.error('測試失敗');
    } finally {
      setTesting(false);
    }
  };

  return (
    <div style={{ padding: '24px' }}>
      <Card title="Dify 批量測試執行">
        <div style={{ marginBottom: '24px' }}>
          <h3>選擇版本</h3>
          <Checkbox.Group
            value={selectedVersions}
            onChange={setSelectedVersions}
          >
            {versions.map(v => (
              <Checkbox key={v.id} value={v.id}>
                {v.version_name}
              </Checkbox>
            ))}
          </Checkbox.Group>
        </div>

        <div style={{ marginBottom: '24px' }}>
          <h3>選擇測試案例</h3>
          <Checkbox.Group
            value={selectedTestCases}
            onChange={setSelectedTestCases}
          >
            {testCases.map(tc => (
              <Checkbox key={tc.id} value={tc.id}>
                {tc.question.substring(0, 50)}...
              </Checkbox>
            ))}
          </Checkbox.Group>
        </div>

        {testing && (
          <Progress percent={progress} status="active" />
        )}

        <Button
          type="primary"
          size="large"
          onClick={handleExecuteTest}
          loading={testing}
          disabled={selectedVersions.length === 0 || selectedTestCases.length === 0}
        >
          開始測試
        </Button>
      </Card>
    </div>
  );
};

export default DifyBatchTestExecutionPage;
```

### 4.3 路由配置

檔案：`frontend/src/App.js`

```javascript
import DifyBenchmarkDashboard from './pages/dify-benchmark/DifyBenchmarkDashboard';
import DifyVersionManagementPage from './pages/dify-benchmark/DifyVersionManagementPage';
import DifyTestCaseManagementPage from './pages/dify-benchmark/DifyTestCaseManagementPage';
import DifyBatchTestExecutionPage from './pages/dify-benchmark/DifyBatchTestExecutionPage';
import DifyBatchComparisonPage from './pages/dify-benchmark/DifyBatchComparisonPage';
import DifyTestHistoryPage from './pages/dify-benchmark/DifyTestHistoryPage';

// 在 Routes 中添加
<Route path="/dify-benchmark/dashboard" element={<DifyBenchmarkDashboard />} />
<Route path="/dify-benchmark/versions" element={<DifyVersionManagementPage />} />
<Route path="/dify-benchmark/test-cases" element={<DifyTestCaseManagementPage />} />
<Route path="/dify-benchmark/batch-test" element={<DifyBatchTestExecutionPage />} />
<Route path="/dify-benchmark/comparison/:batchId" element={<DifyBatchComparisonPage />} />
<Route path="/dify-benchmark/history" element={<DifyTestHistoryPage />} />
```

### 4.4 側邊欄配置

檔案：`frontend/src/components/Sidebar.js`

```javascript
import { RocketOutlined } from '@ant-design/icons';

// 在選單中添加
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

## 🗓️ Phase 5: 整合測試（1-2 天）

### 5.1 後端邏輯測試

創建 CLI 測試工具：`backend/scripts/test_dify_benchmark.py`

```python
#!/usr/bin/env python
"""測試 Dify Benchmark 系統"""
import os
import sys
import django

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from library.dify_benchmark.dify_batch_tester import DifyBatchTester
from api.models import DifyConfigVersion, DifyBenchmarkTestCase

def test_dify_benchmark():
    """測試 Dify Benchmark 完整流程"""
    
    print("=" * 80)
    print("🧪 測試 Dify Benchmark 系統")
    print("=" * 80)
    
    # 1. 檢查版本
    versions = DifyConfigVersion.objects.filter(is_active=True)
    print(f"\n✅ 找到 {versions.count()} 個啟用的版本")
    for v in versions:
        print(f"   - {v.version_name}")
    
    # 2. 檢查測試案例
    test_cases = DifyBenchmarkTestCase.objects.filter(is_active=True)[:5]
    print(f"\n✅ 使用 {test_cases.count()} 個測試案例")
    
    # 3. 執行批量測試
    print(f"\n🚀 開始執行批量測試...")
    tester = DifyBatchTester(verbose=True)
    result = tester.run_batch_test(
        version_ids=[versions.first().id],
        test_case_ids=[tc.id for tc in test_cases],
        batch_name="系統測試",
        use_ai_evaluator=False
    )
    
    if result['success']:
        print(f"\n✅ 測試完成！")
        print(f"   Batch ID: {result['batch_id']}")
        print(f"   測試版本數: {result['summary']['total_versions_tested']}")
        print(f"   測試案例數: {result['summary']['total_test_cases']}")
        print(f"   執行時間: {result['summary']['execution_time']:.2f} 秒")
    else:
        print(f"\n❌ 測試失敗: {result.get('error')}")

if __name__ == "__main__":
    test_dify_benchmark()
```

執行測試：
```bash
docker exec ai-django python scripts/test_dify_benchmark.py
```

### 5.2 端到端測試流程

1. **創建版本** → 前往版本管理頁面，創建 "Dify 二階搜尋 v1.1"
2. **添加測試案例** → 從 Benchmark 複製 5 個測試案例
3. **執行測試** → 批量測試頁面，選擇 1 版本 × 5 案例
4. **查看結果** → 自動跳轉到對比分析頁面
5. **查看歷史** → 測試歷史頁面驗證記錄

---

## ✅ 驗收標準

### 功能完整性
- [ ] 版本 CRUD 功能正常
- [ ] 測試案例 CRUD 功能正常
- [ ] 批量測試執行成功（整合後端搜尋 + Dify API）
- [ ] 關鍵字評分器正常運作
- [ ] 對比分析頁面正常顯示
- [ ] 測試歷史查詢功能正常

### 資料正確性
- [ ] 後端搜尋結果正確傳遞到 Dify
- [ ] Dify 回答正確儲存
- [ ] 關鍵字匹配計算正確
- [ ] 統計數據準確

### 整合驗證
- [ ] ProtocolGuideSearchService.search_knowledge(stage=1) 正常工作
- [ ] Dify API 調用成功
- [ ] 權重配置（80%, 95/5, 10/90）正確應用
- [ ] 搜尋結果格式化正確

---

## 📚 預計時間表

| Phase | 任務 | 預計時間 | 依賴 |
|-------|------|---------|------|
| Phase 1 | 資料庫設計與 Models | 1-2 天 | - |
| Phase 2 | 後端 Library 實作 | 2-3 天 | Phase 1 |
| Phase 3 | API ViewSets 實作 | 2-3 天 | Phase 2 |
| Phase 4 | 前端頁面實作 | 3-4 天 | Phase 3 |
| Phase 5 | 整合測試 | 1-2 天 | Phase 4 |
| **總計** | | **10-15 天** | |

---

## 🎯 下一步行動

1. **確認規劃** - 用戶確認此規劃是否符合需求
2. **準備環境** - 確保 Docker 環境正常運行
3. **開始 Phase 1** - 創建資料庫表和 Models
4. **逐步執行** - 按照 Phase 順序執行
5. **持續測試** - 每個 Phase 完成後進行測試

---

**規劃完成日期**: 2025-11-23  
**規劃狀態**: ✅ 完成，待用戶確認  
**預計開始日期**: 待定  
**預計完成日期**: 開始後 10-15 天
