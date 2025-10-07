"""
API 處理器 - API Handlers  

提供對話管理相關的 API 處理功能，包括 ViewSet 和 API 端點處理。

Author: AI Platform Team
Created: 2024-10-08
"""

import logging
from typing import Dict, Any, Optional
from django.http import HttpRequest
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated

from .conversation_manager import ConversationManager
from .conversation_recorder import ConversationRecorder
from .statistics import ConversationStatistics
from .convenience_functions import (
    get_user_conversation_list,
    get_conversation_history,
    record_complete_exchange
)

logger = logging.getLogger(__name__)


class ConversationAPIHandler:
    """對話 API 處理器類"""
    
    @staticmethod
    def handle_conversation_list_api(request: HttpRequest) -> Response:
        """
        處理對話列表 API
        GET /api/conversations/
        
        Args:
            request: Django HttpRequest 物件
            
        Returns:
            Response: DRF Response 物件
        """
        try:
            # 獲取查詢參數
            page = int(request.GET.get('page', 1))
            page_size = min(int(request.GET.get('page_size', 20)), 100)  # 限制最大 100
            chat_type = request.GET.get('chat_type', None)
            
            # 獲取對話列表
            result = get_user_conversation_list(
                request=request,
                page=page,
                page_size=page_size,
                chat_type=chat_type
            )
            
            if result["success"]:
                # 序列化會話資料
                conversations_data = []
                for session in result["conversations"]:
                    conversations_data.append({
                        "id": session.id,
                        "session_id": session.session_id,
                        "title": session.title,
                        "chat_type": session.chat_type,
                        "message_count": session.message_count,
                        "total_tokens": session.total_tokens,
                        "is_guest_session": session.is_guest_session,
                        "created_at": session.created_at.isoformat(),
                        "last_message_at": session.last_message_at.isoformat() if session.last_message_at else None,
                        "is_active": session.is_active
                    })
                
                return Response({
                    "success": True,
                    "conversations": conversations_data,
                    "pagination": result["pagination"],
                    "user_info": result["user_info"]
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "success": False,
                    "error": result["error"]
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Conversation list API error: {str(e)}")
            return Response({
                "success": False,
                "error": f"API error: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @staticmethod
    def handle_conversation_detail_api(request: HttpRequest, conversation_id: int) -> Response:
        """
        處理對話詳情 API
        GET /api/conversations/{id}/
        
        Args:
            request: Django HttpRequest 物件
            conversation_id: 對話ID
            
        Returns:
            Response: DRF Response 物件
        """
        try:
            # 獲取查詢參數
            page = int(request.GET.get('page', 1))
            page_size = min(int(request.GET.get('page_size', 50)), 100)
            
            # 獲取對話訊息
            result = get_conversation_history(
                request=request,
                conversation_id=conversation_id,
                page=page,
                page_size=page_size
            )
            
            if result["success"]:
                session = result["session"]
                
                # 序列化會話資料
                session_data = {
                    "id": session.id,
                    "session_id": session.session_id,
                    "title": session.title,
                    "summary": session.summary,
                    "chat_type": session.chat_type,
                    "message_count": session.message_count,
                    "total_tokens": session.total_tokens,
                    "total_response_time": session.total_response_time,
                    "is_guest_session": session.is_guest_session,
                    "created_at": session.created_at.isoformat(),
                    "last_message_at": session.last_message_at.isoformat() if session.last_message_at else None
                }
                
                # 序列化訊息資料
                messages_data = []
                for message in result["messages"]:
                    messages_data.append({
                        "id": message.id,
                        "message_id": message.message_id,
                        "role": message.role,
                        "content": message.content,
                        "content_type": message.content_type,
                        "sequence_number": message.sequence_number,
                        "response_time": message.response_time,
                        "token_usage": message.token_usage,
                        "metadata": message.metadata,
                        "is_bookmarked": message.is_bookmarked,
                        "is_helpful": message.is_helpful,
                        "created_at": message.created_at.isoformat()
                    })
                
                return Response({
                    "success": True,
                    "session": session_data,
                    "messages": messages_data,
                    "pagination": result["pagination"]
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "success": False,
                    "error": result["error"]
                }, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as e:
            logger.error(f"Conversation detail API error: {str(e)}")
            return Response({
                "success": False,
                "error": f"API error: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @staticmethod
    def handle_record_conversation_api(request: HttpRequest) -> Response:
        """
        處理記錄對話 API
        POST /api/conversations/record/
        
        Expected payload:
        {
            "session_id": "dify_conv_12345",
            "user_message": "用戶問題",
            "assistant_message": "AI回覆",
            "response_time": 2.3,
            "token_usage": {"total_tokens": 150},
            "metadata": {}
        }
        
        Args:
            request: Django HttpRequest 物件
            
        Returns:
            Response: DRF Response 物件
        """
        try:
            data = request.data
            
            # 必需欄位驗證
            required_fields = ['session_id', 'user_message', 'assistant_message']
            for field in required_fields:
                if field not in data:
                    return Response({
                        "success": False,
                        "error": f"Missing required field: {field}"
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # 記錄完整對話交互
            result = record_complete_exchange(
                request=request,
                session_id=data['session_id'],
                user_message=data['user_message'],
                assistant_message=data['assistant_message'],
                response_time=data.get('response_time'),
                token_usage=data.get('token_usage'),
                metadata=data.get('metadata')
            )
            
            if result["success"]:
                return Response({
                    "success": True,
                    "message": "Conversation recorded successfully",
                    "session_id": result["session"].session_id,
                    "conversation_id": result["session"].id
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    "success": False,
                    "error": result["error"]
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Record conversation API error: {str(e)}")
            return Response({
                "success": False,
                "error": f"API error: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @staticmethod
    def handle_update_session_api(request: HttpRequest, session_id: str) -> Response:
        """
        處理更新會話 API
        PATCH /api/conversations/{session_id}/
        
        Args:
            request: Django HttpRequest 物件
            session_id: 會話ID
            
        Returns:
            Response: DRF Response 物件
        """
        try:
            data = request.data
            
            # 目前只支援更新標題
            if 'title' in data:
                result = ConversationManager.update_session_title(
                    session_id=session_id,
                    new_title=data['title'],
                    request=request
                )
                
                if result["success"]:
                    return Response({
                        "success": True,
                        "message": result["message"]
                    }, status=status.HTTP_200_OK)
                else:
                    status_code = status.HTTP_404_NOT_FOUND if "not found" in result["error"].lower() else status.HTTP_400_BAD_REQUEST
                    return Response({
                        "success": False,
                        "error": result["error"]
                    }, status=status_code)
            else:
                return Response({
                    "success": False,
                    "error": "No valid fields to update"
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Update session API error: {str(e)}")
            return Response({
                "success": False,
                "error": f"API error: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @staticmethod
    def handle_conversation_stats_api(request: HttpRequest) -> Response:
        """
        處理對話統計 API
        GET /api/conversations/stats/
        
        Args:
            request: Django HttpRequest 物件
            
        Returns:
            Response: DRF Response 物件
        """
        try:
            from .guest_identifier import get_request_identifier
            
            # 獲取用戶/訪客標識
            identifier_info = get_request_identifier(request)
            user = identifier_info['user']
            guest_id = identifier_info['guest_id']
            is_guest = identifier_info['is_guest']
            
            # 獲取統計資料
            if is_guest:
                result = ConversationStatistics.get_user_stats(guest_id=guest_id)
            else:
                result = ConversationStatistics.get_user_stats(user_id=user.id)
            
            if result["success"]:
                return Response({
                    "success": True,
                    "stats": result
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "success": False,
                    "error": result["error"]
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Conversation stats API error: {str(e)}")
            return Response({
                "success": False,
                "error": f"API error: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# DRF 裝飾器風格的 API 端點

@api_view(['GET'])
@permission_classes([AllowAny])  # 支援訪客
def conversation_list_api(request):
    """對話列表 API 端點"""
    return ConversationAPIHandler.handle_conversation_list_api(request)


@api_view(['GET'])
@permission_classes([AllowAny])  # 支援訪客
def conversation_detail_api(request, conversation_id):
    """對話詳情 API 端點"""
    return ConversationAPIHandler.handle_conversation_detail_api(request, conversation_id)


@api_view(['POST'])
@permission_classes([AllowAny])  # 支援訪客
def record_conversation_api(request):
    """記錄對話 API 端點"""
    return ConversationAPIHandler.handle_record_conversation_api(request)


@api_view(['PATCH'])
@permission_classes([AllowAny])  # 支援訪客
def update_session_api(request, session_id):
    """更新會話 API 端點"""
    return ConversationAPIHandler.handle_update_session_api(request, session_id)


@api_view(['GET'])
@permission_classes([AllowAny])  # 支援訪客
def conversation_stats_api(request):
    """對話統計 API 端點"""
    return ConversationAPIHandler.handle_conversation_stats_api(request)