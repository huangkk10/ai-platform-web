"""
Dify Chat API Views
管理所有與 Dify 聊天功能相關的 API 端點

包含的 API：
- dify_chat_with_file: 帶檔案上傳的 Dify 聊天
- dify_chat: Protocol RAG 聊天
- dify_ocr_chat: AI OCR 聊天
- rvt_guide_chat: RVT Assistant 聊天
- protocol_guide_chat: Protocol Guide 聊天
- chat_usage_statistics: 聊天使用統計
- record_chat_usage: 記錄聊天使用情況
"""

import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt

# 設置日誌
logger = logging.getLogger(__name__)


# ============= 檢查 Library 可用性 =============

# AI OCR Library
AI_OCR_LIBRARY_AVAILABLE = False
AIOCRAPIHandler = None
dify_ocr_chat_api = None
fallback_dify_chat_with_file = None

try:
    from library.ai_ocr import AIOCRAPIHandler
    from library.ai_ocr.fallback_handlers import fallback_dify_chat_with_file
    AI_OCR_LIBRARY_AVAILABLE = True
    # 導入便利函數
    from library.ai_ocr.api_handlers import dify_ocr_chat_api
except ImportError as e:
    logger.warning(f"⚠️  AI OCR Library 無法載入: {str(e)}")


# Protocol Chat Library
dify_protocol_chat_api = None
fallback_protocol_chat_api = None

try:
    from library.dify_integration.protocol_chat_handler import dify_protocol_chat_api
    from library.dify_integration.fallback_handlers import fallback_protocol_chat_api
except ImportError as e:
    logger.warning(f"⚠️  Protocol Chat Library 無法載入: {str(e)}")


# Chat Analytics Library
CHAT_ANALYTICS_LIBRARY_AVAILABLE = False
handle_chat_usage_statistics_api = None
handle_record_chat_usage_api = None

try:
    from library.chat_analytics import (
        handle_chat_usage_statistics_api,
        handle_record_chat_usage_api
    )
    CHAT_ANALYTICS_LIBRARY_AVAILABLE = True
except ImportError as e:
    logger.warning(f"⚠️  Chat Analytics Library 無法載入: {str(e)}")


# RVT Guide Library
RVT_GUIDE_LIBRARY_AVAILABLE = False
RVTGuideAPIHandler = None
fallback_rvt_guide_chat = None

try:
    from library.rvt_guide import RVTGuideAPIHandler
    from library.rvt_guide.fallback_handlers import fallback_rvt_guide_chat
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


# ============= Chat API 端點 =============

@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def dify_chat_with_file(request):
    """
    Dify Chat API with File Support - 使用 AI OCR Library 實現
    
    🔄 重構後：直接使用 library/ai_ocr/api_handlers.py 處理
    """
    try:
        if AI_OCR_LIBRARY_AVAILABLE and AIOCRAPIHandler:
            # 使用 AI OCR library 中的 API 處理器
            return AIOCRAPIHandler.handle_dify_chat_with_file_api(request)
        else:
            # 使用 library 中的備用實現
            logger.warning("AI OCR Library 不可用，使用 library 備用實現")
            return fallback_dify_chat_with_file(request)
            
    except Exception as e:
        logger.error(f"Dify chat with file API error: {str(e)}")
        return Response({
            'success': False,
            'error': f'服務器錯誤: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])  # ✅ 修復：允許訪客使用（與其他 Assistant 一致）
def dify_chat(request):
    """
    Dify Chat API - 使用 Protocol Known Issue 配置（用於 Protocol RAG）
    
    🔄 重構後：直接使用 library/dify_integration/protocol_chat_handler.py 處理
    ✅ 權限修復：允許訪客和認證用戶使用 Protocol RAG
    """
    try:
        if dify_protocol_chat_api:
            # 使用 library 中的 Protocol Chat 實現
            return dify_protocol_chat_api(request)
        else:
            # 使用 library 中的備用實現
            if fallback_protocol_chat_api:
                return fallback_protocol_chat_api(request)
            else:
                # 最終備用方案：完全不可用時
                logger.error("所有 Protocol Chat 服務都不可用")
                return Response({
                    'success': False,
                    'error': 'Protocol Chat 服務暫時完全不可用，請稍後再試或聯絡管理員',
                    'service_status': 'completely_unavailable'
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
    except Exception as e:
        logger.error(f"Dify protocol chat API error: {str(e)}")
        return Response({
            'success': False,
            'error': f'服務器錯誤: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def dify_ocr_chat(request):
    """
    Dify OCR Chat API - 使用 AI OCR Library 統一實現
    
    🔄 重構後：直接使用 library 中的便利函數
    """
    if dify_ocr_chat_api:
        # 使用 library 中的統一實現
        return dify_ocr_chat_api(request)
    else:
        # 最終備用方案
        logger.error("AI OCR Library 完全不可用")
        return Response({
            'success': False,
            'error': 'AI OCR 聊天服務暫時不可用，請稍後再試或聯絡管理員'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def rvt_guide_chat(request):
    """
    RVT Guide Chat API - 使用 library 統一實現
    """
    try:
        if RVT_GUIDE_LIBRARY_AVAILABLE and RVTGuideAPIHandler:
            return RVTGuideAPIHandler.handle_chat_api(request)
        elif fallback_rvt_guide_chat:
            # 使用 library 中的備用實現
            return fallback_rvt_guide_chat(request)
        else:
            # library 完全不可用時的最終錯誤處理
            logger.error("RVT Guide library 完全不可用")
            return Response({
                'success': False,
                'error': 'RVT Guide service temporarily unavailable, please contact administrator'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        logger.error(f"RVT Guide chat error: {str(e)}")
        return Response({
            'success': False,
            'error': f'RVT Guide 服務器錯誤: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])  # 暫時改為 AllowAny 測試 403 問題
def protocol_guide_chat(request):
    """Protocol Guide 聊天 API"""
    if PROTOCOL_GUIDE_LIBRARY_AVAILABLE and ProtocolGuideAPIHandler:
        return ProtocolGuideAPIHandler.handle_chat_api(request)
    else:
        return Response({
            'error': 'Protocol Guide Library 未安裝，聊天功能不可用'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


# ============= Chat Analytics API =============

@api_view(['GET'])
@permission_classes([AllowAny])
def chat_usage_statistics(request):
    """
    獲取聊天使用統計數據 - 使用 Chat Analytics Library 統一實現
    
    🔄 重構後：直接使用 library/chat_analytics/ 處理
    """
    try:
        if CHAT_ANALYTICS_LIBRARY_AVAILABLE and handle_chat_usage_statistics_api:
            # 使用 Chat Analytics library 中的統一 API 處理器
            return handle_chat_usage_statistics_api(request)
        else:
            # 使用備用實現
            logger.warning("Chat Analytics Library 不可用，使用備用實現")
            try:
                from library.chat_analytics.fallback_handlers import fallback_chat_usage_statistics_api
                return fallback_chat_usage_statistics_api(request)
            except ImportError:
                # 最終備用方案
                logger.error("Chat Analytics Library 完全不可用")
                return Response({
                    'success': False,
                    'error': 'Chat analytics service temporarily unavailable'
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
                
    except Exception as e:
        logger.error(f"Chat usage statistics error: {str(e)}")
        return Response({
            'success': False,
            'error': f'統計數據獲取失敗: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def record_chat_usage(request):
    """
    記錄聊天使用情況 - 使用 Chat Analytics Library 統一實現
    
    🔄 重構後：直接使用 library/chat_analytics/ 處理
    """
    try:
        if CHAT_ANALYTICS_LIBRARY_AVAILABLE and handle_record_chat_usage_api:
            # 使用 Chat Analytics library 中的統一 API 處理器
            return handle_record_chat_usage_api(request)
        else:
            # 使用備用實現
            logger.warning("Chat Analytics Library 不可用，使用備用實現")
            try:
                from library.chat_analytics.fallback_handlers import fallback_record_chat_usage_api
                return fallback_record_chat_usage_api(request)
            except ImportError:
                # 最終備用方案
                logger.error("Chat Analytics Library 完全不可用")
                return Response({
                    'success': False,
                    'error': 'Chat analytics service temporarily unavailable'
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
                
    except Exception as e:
        logger.error(f"Record chat usage error: {str(e)}")
        return Response({
            'success': False,
            'error': f'記錄使用情況失敗: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
