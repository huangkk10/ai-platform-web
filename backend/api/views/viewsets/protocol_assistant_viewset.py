"""
Protocol Assistant ViewSet
提供 Protocol Assistant 聊天功能的 API 端點
使用 Protocol Guide API Handler 作為基礎
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
import logging

logger = logging.getLogger(__name__)

# 嘗試導入 Protocol Guide Library
try:
    from library.protocol_guide import (
        PROTOCOL_GUIDE_LIBRARY_AVAILABLE,
        ProtocolGuideAPIHandler
    )
except ImportError:
    PROTOCOL_GUIDE_LIBRARY_AVAILABLE = False
    ProtocolGuideAPIHandler = None
    logger.warning("Protocol Guide Library not available")


class ProtocolAssistantViewSet(viewsets.ViewSet):
    """
    Protocol Assistant ViewSet
    
    提供與 Protocol Assistant 聊天的 API 端點，整合 Dify Protocol Guide 應用
    內部使用 ProtocolGuideAPIHandler 處理所有邏輯
    """
    permission_classes = [AllowAny]  # 允許未登入用戶使用

    @action(detail=False, methods=['post'])
    def chat(self, request):
        """
        Protocol Assistant 聊天端點
        
        Request Body:
            - query: 用戶問題
            - conversation_id: 對話 ID（可選）
            - user_id: 用戶 ID（可選，默認使用當前用戶）
        
        Response:
            - success: 是否成功
            - answer: AI 回答
            - conversation_id: 對話 ID
            - message_id: 訊息 ID
            - error: 錯誤訊息（如果有）
        """
        # 🔍 DEBUG: 記錄請求詳細信息
        logger.info(f"📥 Protocol Assistant chat request:")
        logger.info(f"  - User: {request.user}")
        logger.info(f"  - Authenticated: {request.user.is_authenticated}")
        logger.info(f"  - Request data: {request.data}")
        
        try:
            if PROTOCOL_GUIDE_LIBRARY_AVAILABLE and ProtocolGuideAPIHandler:
                # 使用 Protocol Guide API Handler 處理聊天請求
                return ProtocolGuideAPIHandler.handle_chat_api(request)
            else:
                logger.error("Protocol Guide Library not available")
                return Response({
                    'success': False,
                    'error': 'Protocol Assistant 服務暫時不可用，請聯繫管理員'
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
                
        except Exception as e:
            logger.exception(f"Protocol Assistant 處理請求時發生錯誤: {str(e)}")
            return Response({
                'success': False,
                'error': f'處理請求時發生錯誤: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def config(self, request):
        """
        獲取 Protocol Assistant 配置資訊
        
        Response:
            - app_name: 應用名稱
            - description: 應用描述
            - features: 功能列表
            - workspace: 工作室名稱
        """
        try:
            if PROTOCOL_GUIDE_LIBRARY_AVAILABLE and ProtocolGuideAPIHandler:
                # 使用 Protocol Guide API Handler 處理配置請求
                return ProtocolGuideAPIHandler.handle_config_api(request)
            else:
                logger.error("Protocol Guide Library not available")
                return Response({
                    'success': False,
                    'error': 'Protocol Assistant 服務暫時不可用'
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
                
        except Exception as e:
            logger.exception(f"獲取 Protocol Assistant 配置時發生錯誤: {str(e)}")
            return Response({
                'success': False,
                'error': f'獲取配置時發生錯誤: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def feedback(self, request):
        """
        提交用戶反饋
        
        Request Body:
            - message_id: 訊息 ID
            - rating: 評分（like/dislike）
        
        Response:
            - success: 是否成功
            - error: 錯誤訊息（如果有）
        """
        try:
            message_id = request.data.get('message_id')
            rating = request.data.get('rating')

            if not message_id or not rating:
                return Response({
                    'success': False,
                    'error': '缺少必要參數'
                }, status=status.HTTP_400_BAD_REQUEST)

            if not PROTOCOL_GUIDE_LIBRARY_AVAILABLE or not ProtocolGuideAPIHandler:
                return Response({
                    'success': False,
                    'error': 'Protocol Assistant 服務暫時不可用'
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

            # 使用 Protocol Guide 的配置來發送反饋
            from library.config.dify_config_manager import get_protocol_guide_config
            from library.dify_integration.request_manager import DifyRequestManager
            
            config = get_protocol_guide_config()
            request_manager = DifyRequestManager(
                api_url=config.api_url,
                api_key=config.api_key
            )

            # 發送反饋
            result = request_manager.send_feedback(
                message_id=message_id,
                rating=rating,
                user_id=str(request.user.id)
            )

            if result['success']:
                logger.info(f"Protocol Assistant 反饋提交成功: message_id={message_id}, rating={rating}")
                return Response({
                    'success': True
                }, status=status.HTTP_200_OK)
            else:
                logger.error(f"Protocol Assistant 反饋提交失敗: {result.get('error')}")
                return Response({
                    'success': False,
                    'error': result.get('error', '提交反饋失敗')
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.exception(f"提交 Protocol Assistant 反饋時發生錯誤: {str(e)}")
            return Response({
                'success': False,
                'error': f'提交反饋時發生錯誤: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

