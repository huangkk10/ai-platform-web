"""
SAF Smart Query 模組
====================

提供智能 API 路由功能，讓 LLM 能夠：
1. 分析用戶問題的意圖
2. 自動選擇正確的 API 進行精準查詢
3. 返回精確的資料結果
4. 生成準確的回答

模組結構：
- intent_types.py: 意圖類型定義
- intent_analyzer.py: LLM 意圖分析器
- query_router.py: 查詢路由器
- response_generator.py: 回答生成器
- query_handlers/: 各種查詢處理器

作者：AI Platform Team
創建日期：2025-12-05
"""

# 延遲導入，避免循環依賴
def _get_intent_type():
    from .intent_types import IntentType
    return IntentType

def _get_intent_result():
    from .intent_types import IntentResult
    return IntentResult

def _get_intent_analyzer():
    from .intent_analyzer import SAFIntentAnalyzer
    return SAFIntentAnalyzer

def _get_query_router():
    from .query_router import QueryRouter
    return QueryRouter

def _get_smart_query_service():
    from .query_router import SmartQueryService
    return SmartQueryService

def _get_response_generator():
    from .response_generator import SAFResponseGenerator
    return SAFResponseGenerator


# 使用 property 風格的延遲導入
class _LazyModule:
    """延遲導入模組包裝器"""
    
    @property
    def IntentType(self):
        return _get_intent_type()
    
    @property
    def IntentResult(self):
        return _get_intent_result()
    
    @property
    def SAFIntentAnalyzer(self):
        return _get_intent_analyzer()
    
    @property
    def QueryRouter(self):
        return _get_query_router()
    
    @property
    def SmartQueryService(self):
        return _get_smart_query_service()
    
    @property
    def SAFResponseGenerator(self):
        return _get_response_generator()


# 實際導出（在需要時才導入）
__all__ = [
    'IntentType',
    'IntentResult',
    'SAFIntentAnalyzer',
    'QueryRouter',
    'SmartQueryService',
    'SAFResponseGenerator',
]

# 模組版本
__version__ = '1.0.0'

# 為了向後兼容，提供直接導入
try:
    from .intent_types import IntentType, IntentResult
    from .intent_analyzer import SAFIntentAnalyzer
    from .query_router import QueryRouter, SmartQueryService
    from .response_generator import SAFResponseGenerator
except ImportError:
    # 如果導入失敗，使用延遲導入
    pass
