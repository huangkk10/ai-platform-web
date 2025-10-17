"""
Dify Config API Views
管理所有與 Dify 配置相關的 API 端點

包含的 API：
- dify_config_info: Dify Protocol Known Issue 配置資訊
- rvt_guide_config: RVT Guide 配置資訊
- protocol_guide_config: Protocol Guide 配置資訊
"""

import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status, permissions
from django.views.decorators.csrf import csrf_exempt

# 設置日誌
logger = logging.getLogger(__name__)


# ============= 檢查 Library 可用性 =============

# Protocol Known Issue Config
get_protocol_known_issue_config = None

try:
    from library.config.dify_app_configs import get_protocol_known_issue_config
except ImportError as e:
    logger.warning(f"⚠️  Protocol Known Issue Config 無法載入: {str(e)}")


# RVT Guide Library
RVT_GUIDE_LIBRARY_AVAILABLE = False
RVTGuideAPIHandler = None
fallback_rvt_guide_config = None

try:
    from library.rvt_guide import RVTGuideAPIHandler
    from library.rvt_guide.fallback_handlers import fallback_rvt_guide_config
    RVT_GUIDE_LIBRARY_AVAILABLE = True
except ImportError as e:
    logger.warning(f"⚠️  RVT Guide Library 無法載入: {str(e)}")


# Protocol Guide Library
PROTOCOL_GUIDE_LIBRARY_AVAILABLE = False
ProtocolGuideAPIHandler = None

try:
    from library.protocol_guide import ProtocolGuideAPIHandler
    PROTOCOL_GUIDE_LIBRARY_AVAILABLE = True
    logger.info("✅ Protocol Guide Library 載入成功")
except ImportError as e:
    logger.warning(f"⚠️  Protocol Guide Library 無法載入: {str(e)}")


# ============= Config API 端點 =============

@api_view(['GET'])
@permission_classes([AllowAny])
def dify_config_info(request):
    """
    獲取 Dify 配置資訊 - 用於前端顯示（使用 Protocol Known Issue 配置）
    """
    try:
        # 檢查 library 是否可用
        if get_protocol_known_issue_config is None:
            logger.warning("Protocol Known Issue Config library 不可用，返回預設配置")
            return Response({
                'success': True,
                'config': {
                    'name': 'Protocol Known Issue System',
                    'description': 'Protocol 測試問題追蹤系統',
                    'version': '1.0.0',
                    'features': ['chat', 'knowledge_search', 'issue_tracking'],
                    'library_available': False
                }
            }, status=status.HTTP_200_OK)
        
        # 使用 Protocol Known Issue 配置
        config = get_protocol_known_issue_config()
        
        # 只返回安全的配置資訊
        safe_config = config.get_safe_config()
        
        return Response({
            'success': True,
            'config': safe_config
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Get Dify config error: {str(e)}")
        return Response({
            'success': False,
            'error': f'獲取配置失敗: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def rvt_guide_config(request):
    """
    獲取 RVT Guide 配置信息 - 使用 library 統一實現
    """
    try:
        if RVT_GUIDE_LIBRARY_AVAILABLE and RVTGuideAPIHandler:
            return RVTGuideAPIHandler.handle_config_api(request)
        elif fallback_rvt_guide_config:
            # 使用 library 中的備用實現
            return fallback_rvt_guide_config(request)
        else:
            # library 完全不可用時的最終錯誤處理
            logger.error("RVT Guide library 完全不可用")
            return Response({
                'success': False,
                'error': 'RVT Guide configuration service temporarily unavailable'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        logger.error(f"Get RVT Guide config error: {str(e)}")
        return Response({
            'success': False,
            'error': f'獲取 RVT Guide 配置失敗: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def protocol_guide_config(request):
    """Protocol Guide 配置 API"""
    if PROTOCOL_GUIDE_LIBRARY_AVAILABLE and ProtocolGuideAPIHandler:
        return ProtocolGuideAPIHandler.handle_config_api(request)
    else:
        return Response({
            'name': 'Protocol Guide System',
            'description': 'Protocol 測試指南系統',
            'version': '1.0.0',
            'features': ['search', 'basic_crud'],
            'library_available': False
        })
