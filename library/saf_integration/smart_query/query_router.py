"""
SAF 查詢路由器
==============

根據意圖類型選擇並執行對應的查詢處理器。

作者：AI Platform Team
創建日期：2025-12-05
"""

import logging
from typing import Dict, Any, Optional

from .intent_types import IntentType, IntentResult
from .query_handlers import (
    BaseHandler,
    QueryResult,
    CustomerHandler,
    ControllerHandler,
    PLHandler,
    DateHandler,
    ProjectDetailHandler,
    ProjectSummaryHandler,
    TestSummaryHandler,
    TestSummaryByFWHandler,
    CompareFWVersionsHandler,
    CompareLatestFWHandler,
    ListFWVersionsHandler,
    CompareMultipleFWHandler,
    FWDetailSummaryHandler,
    StatisticsHandler,
    # Phase 9: Sub Version 查詢處理器
    ListSubVersionsHandler,
    ListFWBySubVersionHandler,
    # Phase 10: 跨專案測試類別搜尋處理器
    TestCategorySearchHandler,
    # Phase 11: FW 測試類別查詢處理器
    FWTestCategoriesHandler,
    # Phase 12: FW 測項查詢處理器
    FWCategoryTestItemsHandler,
    FWAllTestItemsHandler,
)

logger = logging.getLogger(__name__)


class QueryRouter:
    """
    查詢路由器
    
    根據意圖分析結果，選擇並執行對應的查詢處理器。
    """
    
    def __init__(self):
        """初始化路由器，註冊所有處理器"""
        self._handlers: Dict[IntentType, BaseHandler] = {}
        self._statistics_handler = StatisticsHandler()
        
        # 註冊處理器
        self._register_handlers()
    
    def _register_handlers(self):
        """註冊所有處理器"""
        # Phase 3: TestSummaryHandler 處理測試摘要相關意圖
        test_summary_handler = TestSummaryHandler()
        
        # Phase 4: TestSummaryByFWHandler 處理 FW 版本查詢意圖
        test_summary_by_fw_handler = TestSummaryByFWHandler()
        
        # Phase 5.1: CompareFWVersionsHandler 處理指定 FW 版本比較意圖
        compare_fw_versions_handler = CompareFWVersionsHandler()
        
        # Phase 5.2: 智能版本選擇處理器
        compare_latest_fw_handler = CompareLatestFWHandler()
        list_fw_versions_handler = ListFWVersionsHandler()
        
        # Phase 5.4: 多版本趨勢比較處理器
        compare_multiple_fw_handler = CompareMultipleFWHandler()
        
        # Phase 6.2: FWDetailSummaryHandler 處理 FW 詳細統計意圖
        fw_detail_summary_handler = FWDetailSummaryHandler()
        
        # Phase 7: PLHandler 處理按專案負責人查詢意圖
        pl_handler = PLHandler()
        
        # Phase 8: DateHandler 處理日期/月份查詢意圖
        date_handler = DateHandler()
        
        # Phase 9: Sub Version 查詢處理器
        list_sub_versions_handler = ListSubVersionsHandler()
        list_fw_by_sub_version_handler = ListFWBySubVersionHandler()
        
        self._handlers = {
            # Phase 1-2 處理器
            IntentType.QUERY_PROJECTS_BY_CUSTOMER: CustomerHandler(),
            IntentType.QUERY_PROJECTS_BY_CONTROLLER: ControllerHandler(),
            IntentType.QUERY_PROJECT_DETAIL: ProjectDetailHandler(),
            IntentType.QUERY_PROJECT_SUMMARY: ProjectSummaryHandler(),
            
            # Phase 7: PL 查詢處理器
            IntentType.QUERY_PROJECTS_BY_PL: pl_handler,
            
            # Phase 3: 測試摘要處理器（3 個意圖共用）
            IntentType.QUERY_PROJECT_TEST_SUMMARY: test_summary_handler,
            IntentType.QUERY_PROJECT_TEST_BY_CATEGORY: test_summary_handler,
            IntentType.QUERY_PROJECT_TEST_BY_CAPACITY: test_summary_handler,
            
            # Phase 4: FW 版本查詢處理器
            IntentType.QUERY_PROJECT_TEST_SUMMARY_BY_FW: test_summary_by_fw_handler,
            
            # Phase 5.1: 指定 FW 版本比較處理器
            IntentType.COMPARE_FW_VERSIONS: compare_fw_versions_handler,
            
            # Phase 5.2: 智能版本選擇處理器
            IntentType.COMPARE_LATEST_FW: compare_latest_fw_handler,
            IntentType.LIST_FW_VERSIONS: list_fw_versions_handler,
            
            # Phase 5.4: 多版本趨勢比較處理器
            IntentType.COMPARE_MULTIPLE_FW: compare_multiple_fw_handler,
            
            # Phase 6.2: FW 詳細統計處理器
            IntentType.QUERY_FW_DETAIL_SUMMARY: fw_detail_summary_handler,
            
            # Phase 8: 日期/月份查詢處理器
            IntentType.QUERY_PROJECTS_BY_DATE: date_handler,
            IntentType.QUERY_PROJECTS_BY_MONTH: date_handler,
            
            # Phase 9: Sub Version 查詢處理器
            IntentType.LIST_SUB_VERSIONS: list_sub_versions_handler,
            IntentType.LIST_FW_BY_SUB_VERSION: list_fw_by_sub_version_handler,
            
            # Phase 10: 跨專案測試類別搜尋處理器
            IntentType.QUERY_PROJECTS_BY_TEST_CATEGORY: TestCategorySearchHandler(),
            
            # Phase 11: FW 測試類別查詢處理器
            IntentType.QUERY_PROJECT_FW_TEST_CATEGORIES: FWTestCategoriesHandler(),
            
            # Phase 12: FW 測項查詢處理器
            IntentType.QUERY_PROJECT_FW_CATEGORY_TEST_ITEMS: FWCategoryTestItemsHandler(),
            IntentType.QUERY_PROJECT_FW_ALL_TEST_ITEMS: FWAllTestItemsHandler(),
            
            # 統計類型使用專門的處理器
            IntentType.COUNT_PROJECTS: self._statistics_handler,
            IntentType.LIST_ALL_CUSTOMERS: self._statistics_handler,
            IntentType.LIST_ALL_CONTROLLERS: self._statistics_handler,
            IntentType.LIST_ALL_PLS: self._statistics_handler,
        }
        
        logger.info(f"QueryRouter 已註冊 {len(self._handlers)} 個處理器")
    
    def route(self, intent_result: IntentResult) -> QueryResult:
        """
        根據意圖結果路由到對應的處理器並執行查詢
        
        Args:
            intent_result: 意圖分析結果
            
        Returns:
            QueryResult: 查詢結果
        """
        intent_type = intent_result.intent
        parameters = intent_result.parameters.copy()
        
        logger.info(
            f"路由查詢: intent={intent_type.value}, "
            f"parameters={parameters}, "
            f"confidence={intent_result.confidence:.2f}"
        )
        
        # 處理未知意圖
        if intent_type == IntentType.UNKNOWN:
            return self._handle_unknown_intent(intent_result)
        
        # 獲取對應的處理器
        handler = self._handlers.get(intent_type)
        
        if handler is None:
            logger.warning(f"找不到意圖 {intent_type.value} 的處理器")
            return QueryResult.error(
                f"不支援的查詢類型: {intent_type.value}",
                query_type="router",
                parameters=parameters
            )
        
        try:
            # 特殊處理統計類型的查詢
            if intent_type in [
                IntentType.COUNT_PROJECTS,
                IntentType.LIST_ALL_CUSTOMERS,
                IntentType.LIST_ALL_CONTROLLERS,
                IntentType.LIST_ALL_PLS
            ]:
                return self._handle_statistics_query(intent_type, parameters)
            
            # 執行查詢
            result = handler.execute(parameters)
            
            # 添加意圖信息到 metadata
            result.metadata['intent'] = intent_type.value
            result.metadata['confidence'] = intent_result.confidence
            
            return result
            
        except Exception as e:
            logger.error(f"執行查詢時發生錯誤: {str(e)}")
            return QueryResult.error(
                f"查詢執行失敗: {str(e)}",
                query_type=intent_type.value,
                parameters=parameters
            )
    
    def _handle_statistics_query(self, intent_type: IntentType, 
                                  parameters: Dict[str, Any]) -> QueryResult:
        """
        處理統計類型的查詢
        
        Args:
            intent_type: 意圖類型
            parameters: 查詢參數
            
        Returns:
            QueryResult: 統計結果
        """
        handler = self._statistics_handler
        
        if intent_type == IntentType.COUNT_PROJECTS:
            return handler.count_projects(parameters)
        elif intent_type == IntentType.LIST_ALL_CUSTOMERS:
            return handler.list_customers(parameters)
        elif intent_type == IntentType.LIST_ALL_CONTROLLERS:
            return handler.list_controllers(parameters)
        elif intent_type == IntentType.LIST_ALL_PLS:
            return handler.list_pls(parameters)
        else:
            return QueryResult.error(
                f"未知的統計類型: {intent_type.value}",
                query_type="statistics",
                parameters=parameters
            )
    
    def _handle_unknown_intent(self, intent_result: IntentResult) -> QueryResult:
        """
        處理未知意圖
        
        Args:
            intent_result: 意圖分析結果
            
        Returns:
            QueryResult: 提示訊息
        """
        help_message = """
無法理解您的問題。

您可以嘗試以下查詢：
• 「WD 有哪些專案？」- 查詢指定客戶的專案
• 「SM2264 控制器用在哪些專案？」- 查詢使用指定控制器的專案
• 「DEMETER 專案的詳細資訊」- 查詢專案詳情
• 「DEMETER 的測試結果」- 查詢專案測試摘要
• 「DEMETER 專案 FW Y1114B 的測試結果」- 查詢特定 FW 版本的測試結果
• 「WD 有幾個專案？」- 統計專案數量
• 「有哪些客戶？」- 列出所有客戶
• 「有哪些控制器？」- 列出所有控制器
""".strip()
        
        return QueryResult(
            status=QueryResult.no_results().status,
            data={'help': help_message},
            count=0,
            query_type="unknown",
            parameters=intent_result.parameters,
            message="無法理解查詢意圖",
            metadata={
                'intent': IntentType.UNKNOWN.value,
                'confidence': intent_result.confidence,
                'raw_response': intent_result.raw_response
            }
        )
    
    def get_supported_intents(self) -> list:
        """
        獲取所有支援的意圖類型
        
        Returns:
            list: 支援的意圖類型列表
        """
        return [intent.value for intent in self._handlers.keys()]
    
    def get_handler(self, intent_type: IntentType) -> Optional[BaseHandler]:
        """
        獲取指定意圖類型的處理器
        
        Args:
            intent_type: 意圖類型
            
        Returns:
            Optional[BaseHandler]: 對應的處理器，如果不存在則返回 None
        """
        return self._handlers.get(intent_type)


class SmartQueryService:
    """
    智能查詢服務
    
    整合意圖分析和查詢路由，提供完整的智能查詢功能。
    """
    
    def __init__(self):
        """初始化服務"""
        from .intent_analyzer import SAFIntentAnalyzer
        
        self.intent_analyzer = SAFIntentAnalyzer()
        self.query_router = QueryRouter()
        
        logger.info("SmartQueryService 初始化完成")
    
    def query(self, user_query: str, user_id: str = "anonymous") -> Dict[str, Any]:
        """
        執行智能查詢
        
        Args:
            user_query: 用戶查詢
            user_id: 用戶 ID
            
        Returns:
            Dict: 查詢結果，包含意圖分析和查詢結果
        """
        import time
        start_time = time.time()
        
        logger.info(f"開始處理查詢: {user_query}")
        
        # 1. 意圖分析
        intent_result = self.intent_analyzer.analyze(user_query, user_id)
        
        logger.info(
            f"意圖分析完成: intent={intent_result.intent.value}, "
            f"confidence={intent_result.confidence:.2f}"
        )
        
        # 2. 路由並執行查詢
        query_result = self.query_router.route(intent_result)
        
        # 3. 計算總時間
        total_time = (time.time() - start_time) * 1000  # 毫秒
        
        # 4. 組合結果
        result = {
            'success': query_result.is_success(),
            'query': user_query,
            'intent': {
                'type': intent_result.intent.value,
                'parameters': intent_result.parameters,
                'confidence': intent_result.confidence,
                'is_valid': intent_result.is_valid()
            },
            'result': query_result.to_dict(),
            'metadata': {
                'query_time_ms': round(total_time, 2),
                'user_id': user_id,
                'source': 'saf_smart_query'
            }
        }
        
        logger.info(
            f"查詢完成: success={result['success']}, "
            f"time={total_time:.2f}ms"
        )
        
        return result


# 全局服務實例（延遲初始化）
_smart_query_service: Optional[SmartQueryService] = None


def get_smart_query_service() -> SmartQueryService:
    """
    獲取智能查詢服務單例
    
    Returns:
        SmartQueryService: 服務實例
    """
    global _smart_query_service
    
    if _smart_query_service is None:
        _smart_query_service = SmartQueryService()
    
    return _smart_query_service


def smart_query(user_query: str, user_id: str = "anonymous") -> Dict[str, Any]:
    """
    執行智能查詢的便利函數
    
    Args:
        user_query: 用戶查詢
        user_id: 用戶 ID
        
    Returns:
        Dict: 查詢結果
    """
    service = get_smart_query_service()
    return service.query(user_query, user_id)
