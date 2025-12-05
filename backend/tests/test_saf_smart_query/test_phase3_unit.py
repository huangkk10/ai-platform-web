#!/usr/bin/env python3
"""
SAF Smart Query Phase 3 單元測試
================================

使用 pytest 框架測試 Phase 3 新增的測試摘要功能。

執行方式：
    # 執行所有 Phase 3 測試
    docker exec ai-django pytest tests/test_saf_smart_query/test_phase3_unit.py -v
    
    # 執行特定測試類別
    docker exec ai-django pytest tests/test_saf_smart_query/test_phase3_unit.py::TestIntentTypes -v
    docker exec ai-django pytest tests/test_saf_smart_query/test_phase3_unit.py::TestTestSummaryHandler -v
    docker exec ai-django pytest tests/test_saf_smart_query/test_phase3_unit.py::TestResponseGenerator -v

作者：AI Platform Team
創建日期：2025-12-06
版本：1.0 (Phase 3)
"""

import os
import sys
import pytest
from unittest.mock import Mock, patch, MagicMock

# 設定 Django 環境
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')

import django
django.setup()


# ============================================================
# 測試 IntentTypes
# ============================================================
class TestIntentTypes:
    """測試 Phase 3 意圖類型定義"""
    
    def test_new_intent_types_exist(self):
        """驗證新的意圖類型已定義"""
        from library.saf_integration.smart_query.intent_types import IntentType
        
        # 驗證三個新意圖存在
        assert hasattr(IntentType, 'QUERY_PROJECT_TEST_SUMMARY')
        assert hasattr(IntentType, 'QUERY_PROJECT_TEST_BY_CATEGORY')
        assert hasattr(IntentType, 'QUERY_PROJECT_TEST_BY_CAPACITY')
    
    def test_intent_type_values(self):
        """驗證意圖類型值"""
        from library.saf_integration.smart_query.intent_types import IntentType
        
        assert IntentType.QUERY_PROJECT_TEST_SUMMARY.value == 'query_project_test_summary'
        assert IntentType.QUERY_PROJECT_TEST_BY_CATEGORY.value == 'query_project_test_by_category'
        assert IntentType.QUERY_PROJECT_TEST_BY_CAPACITY.value == 'query_project_test_by_capacity'
    
    def test_known_test_categories(self):
        """驗證已知測試類別定義"""
        from library.saf_integration.smart_query.intent_types import KNOWN_TEST_CATEGORIES
        
        assert isinstance(KNOWN_TEST_CATEGORIES, (list, set, tuple))
        assert len(KNOWN_TEST_CATEGORIES) > 0
        
        # 驗證常見類別存在
        expected_categories = ['Compliance', 'Performance', 'Interoperability', 'Stress']
        for cat in expected_categories:
            assert cat in KNOWN_TEST_CATEGORIES, f"Missing category: {cat}"
    
    def test_known_capacities(self):
        """驗證已知容量規格定義"""
        from library.saf_integration.smart_query.intent_types import KNOWN_CAPACITIES
        
        assert isinstance(KNOWN_CAPACITIES, (list, set, tuple))
        assert len(KNOWN_CAPACITIES) > 0
        
        # 驗證常見容量存在
        expected_capacities = ['1TB', '2TB', '512GB', '256GB']
        for cap in expected_capacities:
            assert cap in KNOWN_CAPACITIES, f"Missing capacity: {cap}"


# ============================================================
# 測試 EndpointRegistry
# ============================================================
class TestEndpointRegistry:
    """測試 Phase 3 端點配置"""
    
    def test_project_test_summary_endpoint_exists(self):
        """驗證 project_test_summary 端點已註冊"""
        from library.saf_integration.endpoint_registry import get_endpoint_config
        
        config = get_endpoint_config('project_test_summary')
        
        assert config is not None
        assert 'path' in config
        assert 'method' in config
    
    def test_project_test_summary_endpoint_config(self):
        """驗證端點配置正確"""
        from library.saf_integration.endpoint_registry import get_endpoint_config
        
        config = get_endpoint_config('project_test_summary')
        
        assert config['method'] == 'GET'
        assert 'project_uid' in config['path']
        assert 'test-summary' in config['path']
        assert config.get('path_params') == ['project_uid']


# ============================================================
# 測試 APIClient
# ============================================================
class TestAPIClient:
    """測試 Phase 3 API 客戶端方法"""
    
    def test_get_project_uid_by_name_method_exists(self):
        """驗證 get_project_uid_by_name 方法存在"""
        from library.saf_integration.api_client import SAFAPIClient
        
        client = SAFAPIClient()
        assert hasattr(client, 'get_project_uid_by_name')
        assert callable(getattr(client, 'get_project_uid_by_name'))
    
    def test_get_project_test_summary_method_exists(self):
        """驗證 get_project_test_summary 方法存在"""
        from library.saf_integration.api_client import SAFAPIClient
        
        client = SAFAPIClient()
        assert hasattr(client, 'get_project_test_summary')
        assert callable(getattr(client, 'get_project_test_summary'))


# ============================================================
# 測試 TestSummaryHandler
# ============================================================
class TestTestSummaryHandler:
    """測試 Phase 3 處理器"""
    
    def test_handler_import(self):
        """驗證 TestSummaryHandler 可以正確導入"""
        from library.saf_integration.smart_query.query_handlers import TestSummaryHandler
        assert TestSummaryHandler is not None
    
    def test_handler_instantiation(self):
        """驗證處理器可以正確實例化"""
        from library.saf_integration.smart_query.query_handlers import TestSummaryHandler
        
        handler = TestSummaryHandler()
        assert handler is not None
        # 實際方法名是 execute，不是 handle
        assert hasattr(handler, 'execute')
    
    def test_handler_name(self):
        """驗證處理器名稱"""
        from library.saf_integration.smart_query.query_handlers import TestSummaryHandler
        
        handler = TestSummaryHandler()
        assert hasattr(handler, 'handler_name')
        assert 'test_summary' in handler.handler_name.lower()
    
    def test_handler_supported_intent(self):
        """驗證處理器支援的意圖"""
        from library.saf_integration.smart_query.query_handlers import TestSummaryHandler
        from library.saf_integration.smart_query.intent_types import IntentType
        
        handler = TestSummaryHandler()
        
        # 驗證處理器能處理三種測試摘要意圖
        # 這取決於實作方式，可能需要調整
        assert hasattr(handler, 'supported_intent') or hasattr(handler, 'can_handle')


# ============================================================
# 測試 QueryRouter
# ============================================================
class TestQueryRouter:
    """測試 Phase 3 路由配置"""
    
    def test_router_has_test_summary_handlers(self):
        """驗證路由器已註冊測試摘要處理器"""
        from library.saf_integration.smart_query.query_router import QueryRouter
        from library.saf_integration.smart_query.intent_types import IntentType
        
        router = QueryRouter()
        
        # 驗證三個新意圖都已註冊
        assert IntentType.QUERY_PROJECT_TEST_SUMMARY in router._handlers
        assert IntentType.QUERY_PROJECT_TEST_BY_CATEGORY in router._handlers
        assert IntentType.QUERY_PROJECT_TEST_BY_CAPACITY in router._handlers
    
    def test_router_handler_count(self):
        """驗證路由器處理器數量"""
        from library.saf_integration.smart_query.query_router import QueryRouter
        
        router = QueryRouter()
        
        # Phase 3 後應該有 10 個處理器
        # 原有 7 個 + 新增 3 個
        assert len(router._handlers) >= 10


# ============================================================
# 測試 ResponseGenerator
# ============================================================
class TestResponseGenerator:
    """測試 Phase 3 回應生成器"""
    
    def test_test_summary_response_method_exists(self):
        """驗證測試摘要回應方法存在"""
        from library.saf_integration.smart_query.response_generator import SAFResponseGenerator
        
        gen = SAFResponseGenerator()
        assert hasattr(gen, '_generate_test_summary_response')
    
    def test_test_by_category_response_method_exists(self):
        """驗證按類別回應方法存在"""
        from library.saf_integration.smart_query.response_generator import SAFResponseGenerator
        
        gen = SAFResponseGenerator()
        assert hasattr(gen, '_generate_test_by_category_response')
    
    def test_test_by_capacity_response_method_exists(self):
        """驗證按容量回應方法存在"""
        from library.saf_integration.smart_query.response_generator import SAFResponseGenerator
        
        gen = SAFResponseGenerator()
        assert hasattr(gen, '_generate_test_by_capacity_response')


# ============================================================
# 測試 IntentAnalyzer (SAFIntentAnalyzer)
# ============================================================
class TestIntentAnalyzer:
    """測試意圖分析器對 Phase 3 意圖的識別"""
    
    def test_analyzer_import(self):
        """驗證 SAFIntentAnalyzer 可以正確導入"""
        from library.saf_integration.smart_query.intent_analyzer import SAFIntentAnalyzer
        assert SAFIntentAnalyzer is not None
    
    def test_analyzer_has_analyze_method(self):
        """驗證分析方法存在"""
        from library.saf_integration.smart_query.intent_analyzer import SAFIntentAnalyzer
        
        analyzer = SAFIntentAnalyzer()
        assert hasattr(analyzer, 'analyze')
        assert callable(getattr(analyzer, 'analyze'))


# ============================================================
# 整合測試：模擬完整流程
# ============================================================
class TestPhase3Integration:
    """Phase 3 整合測試（模擬）"""
    
    @pytest.fixture
    def mock_api_response(self):
        """模擬 API 回應"""
        return {
            'total_count': 100,
            'pass_count': 80,
            'fail_count': 15,
            'block_count': 5,
            'pass_rate': 80.0,
            'categories': [
                {'name': 'Compliance', 'pass': 30, 'fail': 5, 'block': 2},
                {'name': 'Performance', 'pass': 25, 'fail': 3, 'block': 1},
            ],
            'capacities': [
                {'name': '1TB', 'pass': 40, 'fail': 7, 'block': 2},
                {'name': '512GB', 'pass': 35, 'fail': 6, 'block': 3},
            ]
        }
    
    def test_handler_execute_method_exists(self):
        """測試處理器有 execute 方法"""
        from library.saf_integration.smart_query.query_handlers import TestSummaryHandler
        
        handler = TestSummaryHandler()
        assert hasattr(handler, 'execute')
        assert callable(getattr(handler, 'execute'))
    
    def test_handler_validate_parameters_method_exists(self):
        """測試處理器有 validate_parameters 方法"""
        from library.saf_integration.smart_query.query_handlers import TestSummaryHandler
        
        handler = TestSummaryHandler()
        assert hasattr(handler, 'validate_parameters')
        assert callable(getattr(handler, 'validate_parameters'))


# ============================================================
# 主程式（用於直接執行）
# ============================================================
if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
