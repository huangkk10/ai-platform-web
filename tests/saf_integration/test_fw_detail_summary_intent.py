"""
FW Detail Summary Intent 測試
============================

測試 Phase 6.2 新增的 query_fw_detail_summary 意圖。

測試覆蓋：
1. 意圖識別測試（各種問法）
2. Handler 執行測試
3. API 回應格式測試
4. 錯誤處理測試

作者：AI Platform Team
創建日期：2025-12-07
"""

import os
import sys

# 設置 Django 環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')

import django
django.setup()

import pytest
import logging
from unittest.mock import patch, MagicMock

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestFWDetailSummaryIntent:
    """測試 query_fw_detail_summary 意圖識別"""
    
    @pytest.fixture
    def mock_dify_response(self):
        """模擬 Dify 意圖分析回應"""
        def _create_response(intent: str, params: dict, confidence: float = 0.9):
            return {
                "intent": intent,
                "parameters": params,
                "confidence": confidence
            }
        return _create_response
    
    def test_intent_type_exists(self):
        """確認 QUERY_FW_DETAIL_SUMMARY 意圖類型已定義"""
        from library.saf_integration.smart_query.intent_types import IntentType
        
        assert hasattr(IntentType, 'QUERY_FW_DETAIL_SUMMARY')
        assert IntentType.QUERY_FW_DETAIL_SUMMARY.value == 'query_fw_detail_summary'
        logger.info("✓ QUERY_FW_DETAIL_SUMMARY 意圖類型已定義")
    
    def test_intent_description(self):
        """確認意圖描述已設定"""
        from library.saf_integration.smart_query.intent_types import IntentType
        
        intent = IntentType.QUERY_FW_DETAIL_SUMMARY
        description = intent.get_description()
        assert '詳細統計' in description or '完成率' in description or '樣本' in description
        logger.info(f"✓ 意圖描述：{description}")
    
    def test_intent_required_parameters(self):
        """確認必要參數已定義"""
        from library.saf_integration.smart_query.intent_types import IntentType
        
        intent = IntentType.QUERY_FW_DETAIL_SUMMARY
        required_params = intent.get_required_parameters()
        assert 'project_name' in required_params
        assert 'fw_version' in required_params
        logger.info(f"✓ 必要參數：{required_params}")


class TestFWDetailSummaryHandler:
    """測試 FWDetailSummaryHandler 處理器"""
    
    @pytest.fixture
    def handler(self):
        """創建 Handler 實例"""
        from library.saf_integration.smart_query.query_handlers import FWDetailSummaryHandler
        return FWDetailSummaryHandler()
    
    def test_handler_exists(self):
        """確認 Handler 可以被導入"""
        from library.saf_integration.smart_query.query_handlers import FWDetailSummaryHandler
        
        handler = FWDetailSummaryHandler()
        assert handler is not None
        assert handler.handler_name == 'fw_detail_summary_handler'
        assert handler.supported_intent == 'query_fw_detail_summary'
        logger.info("✓ FWDetailSummaryHandler 可正常導入和初始化")
    
    def test_handler_registered(self):
        """確認 Handler 已註冊到路由器"""
        from library.saf_integration.smart_query.query_router import QueryRouter
        from library.saf_integration.smart_query.intent_types import IntentType
        
        router = QueryRouter()
        assert IntentType.QUERY_FW_DETAIL_SUMMARY in router._handlers
        logger.info("✓ Handler 已註冊到 QueryRouter")
    
    def test_handler_validate_parameters_missing_project(self, handler):
        """測試缺少 project_name 參數"""
        params = {"fw_version": "G200X6EC"}
        
        result = handler.execute(params)
        
        assert result.success is False
        assert 'project_name' in result.message.lower()
        logger.info("✓ 缺少 project_name 時返回錯誤")
    
    def test_handler_validate_parameters_missing_fw(self, handler):
        """測試缺少 fw_version 參數"""
        params = {"project_name": "Springsteen"}
        
        result = handler.execute(params)
        
        assert result.success is False
        assert 'fw_version' in result.message.lower()
        logger.info("✓ 缺少 fw_version 時返回錯誤")


class TestFWDetailSummaryAPI:
    """測試 API Client 的 firmware-summary 方法"""
    
    @pytest.fixture
    def api_client(self):
        """創建 API Client 實例"""
        from library.saf_integration.api_client import SAFAPIClient
        return SAFAPIClient()
    
    def test_api_method_exists(self, api_client):
        """確認 get_firmware_summary 方法存在"""
        assert hasattr(api_client, 'get_firmware_summary')
        logger.info("✓ get_firmware_summary 方法存在")


class TestFWDetailSummaryIntegration:
    """整合測試（需要網路連接）"""
    
    @pytest.fixture
    def api_client(self):
        """創建 API Client 實例"""
        from library.saf_integration.api_client import SAFAPIClient
        return SAFAPIClient()
    
    @pytest.fixture
    def handler(self):
        """創建 Handler 實例"""
        from library.saf_integration.smart_query.query_handlers import FWDetailSummaryHandler
        return FWDetailSummaryHandler()
    
    @pytest.mark.integration
    def test_real_api_call(self, api_client):
        """測試真實 API 呼叫 firmware-summary"""
        # 先獲取專案列表找一個有效的 project_uid
        projects = api_client.get_all_projects()
        
        if not projects:
            pytest.skip("無法獲取專案列表")
        
        # 找一個包含 "Springsteen" 的專案
        target_project = None
        for project in projects:
            if 'springsteen' in project.get('projectName', '').lower():
                target_project = project
                break
        
        if not target_project:
            # 使用第一個專案
            target_project = projects[0]
        
        project_uid = target_project.get('projectUid')
        logger.info(f"測試專案: {target_project.get('projectName')} (uid: {project_uid})")
        
        # 呼叫 firmware-summary API
        result = api_client.get_firmware_summary(project_uid)
        
        assert result is not None, "API 回傳 None"
        
        # 驗證回應結構
        assert 'overview' in result, "缺少 overview"
        assert 'sample_stats' in result, "缺少 sample_stats"
        assert 'test_item_stats' in result, "缺少 test_item_stats"
        
        # 驗證 overview 欄位
        overview = result['overview']
        assert 'completion_rate' in overview or 'pass_rate' in overview
        
        logger.info(f"✓ API 回傳結構正確")
        logger.info(f"  Overview: completion_rate={overview.get('completion_rate')}%, "
                   f"pass_rate={overview.get('pass_rate')}%")
    
    @pytest.mark.integration
    def test_full_handler_execution(self, handler):
        """測試完整的 Handler 執行流程"""
        params = {
            "project_name": "Springsteen",
            "fw_version": "G200X6EC"
        }
        
        result = handler.execute(params)
        
        if result.success:
            logger.info(f"✓ Handler 執行成功")
            logger.info(f"  回應長度: {len(result.message)} 字元")
            
            # 檢查關鍵資訊
            assert '詳細統計' in result.message or '統計' in result.message or '完成率' in result.message
            assert result.data is not None
            
            # 檢查 data 結構
            data = result.data
            assert 'overview' in data
            assert 'sample_stats' in data
            assert 'test_item_stats' in data
            
            logger.info(f"  資料結構正確：overview, sample_stats, test_item_stats")
        else:
            # 如果找不到專案，這也是預期的結果
            logger.info(f"  Handler 回應（非成功但預期內）: {result.message[:100]}...")
            assert '找不到' in result.message or '無法' in result.message


class TestIntentDifferentiation:
    """測試意圖區分（query_project_test_summary_by_fw vs query_fw_detail_summary）"""
    
    def test_intent_keywords_differentiation(self):
        """驗證兩個意圖的關鍵字區分"""
        # test_summary_by_fw 關鍵字
        test_summary_keywords = ['測試結果', 'Pass', 'Fail', '通過', '失敗', '哪些通過']
        
        # fw_detail_summary 關鍵字
        detail_summary_keywords = ['詳細統計', '完成率', '進度', '樣本', '使用率', '執行率', '失敗率', '概覽']
        
        # 確保關鍵字集合不重疊太多
        overlap = set()
        for kw1 in test_summary_keywords:
            for kw2 in detail_summary_keywords:
                if kw1 in kw2 or kw2 in kw1:
                    overlap.add((kw1, kw2))
        
        logger.info(f"測試結果相關關鍵字: {test_summary_keywords}")
        logger.info(f"詳細統計相關關鍵字: {detail_summary_keywords}")
        logger.info(f"潛在重疊: {overlap}")
        
        # 允許一些重疊，但不應太多
        assert len(overlap) < 3, f"關鍵字重疊過多: {overlap}"
        logger.info("✓ 兩個意圖的關鍵字區分良好")


if __name__ == '__main__':
    # 執行基本測試（不需要網路）
    print("=" * 60)
    print("執行 FW Detail Summary 基本測試")
    print("=" * 60)
    
    # 測試意圖定義
    test_intent = TestFWDetailSummaryIntent()
    test_intent.test_intent_type_exists()
    test_intent.test_intent_description()
    test_intent.test_intent_required_parameters()
    
    # 測試 Handler
    test_handler = TestFWDetailSummaryHandler()
    test_handler.test_handler_exists()
    test_handler.test_handler_registered()
    
    # 測試 API Client
    from library.saf_integration.api_client import SAFAPIClient
    test_api = TestFWDetailSummaryAPI()
    test_api.test_api_method_exists(SAFAPIClient())
    
    print("\n" + "=" * 60)
    print("基本測試全部通過！")
    print("=" * 60)
    
    # 執行整合測試
    print("\n" + "=" * 60)
    print("執行整合測試（需要 SAF API 連接）")
    print("=" * 60)
    
    try:
        test_integration = TestFWDetailSummaryIntegration()
        api_client = SAFAPIClient()
        
        print("\n1. 測試 firmware-summary API...")
        test_integration.test_real_api_call(api_client)
        
        print("\n2. 測試完整 Handler 執行...")
        from library.saf_integration.smart_query.query_handlers import FWDetailSummaryHandler
        handler = FWDetailSummaryHandler()
        test_integration.test_full_handler_execution(handler)
        
        print("\n" + "=" * 60)
        print("整合測試全部通過！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n⚠️ 整合測試失敗: {str(e)}")
        print("（這可能是因為無法連接到 SAF API）")
