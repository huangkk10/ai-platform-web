"""
Dify Protocol Chat Fallback Handler

提供當 Protocol Chat Handler 不可用時的備用實現
簡化版本的 Protocol RAG 聊天處理
"""

import logging
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


def fallback_protocol_chat_api(request):
    """
    Protocol Chat API 備用實現 - 簡化版本
    
    當主要的 Protocol Chat Handler 不可用時使用此備用實現
    提供基本的輸入驗證和模擬響應
    
    Args:
        request: Django request 對象
        
    Returns:
        Django Response 對象
    """
    try:
        logger.warning("Dify Protocol Chat Library 不可用，使用 library 備用實現")
        
        # 解析請求數據
        data = request.data
        message = data.get('message', '').strip()
        conversation_id = data.get('conversation_id', '')
        
        # 驗證輸入
        if not message:
            return Response({
                'success': False,
                'error': '訊息內容不能為空'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 生成備用響應
        truncated_message = message[:50] + ("..." if len(message) > 50 else "")
        fallback_answer = f'已收到您的 Protocol RAG 查詢：{truncated_message}。由於 library 不可用，這是備用回應。'
        
        # 基本處理：模擬成功響應
        response_data = {
            'success': True,
            'answer': fallback_answer,
            'conversation_id': conversation_id or 'fallback_conversation',
            'message_id': 'fallback_message',
            'response_time': 0.1,
            'metadata': {
                'source': 'fallback_implementation',
                'fallback_reason': 'protocol_chat_library_unavailable',
                'original_message_length': len(message)
            },
            'usage': {},
            'warning': 'This is a fallback response. Protocol Chat service is temporarily unavailable.'
        }
        
        logger.info(f"Protocol chat fallback response generated for message: {truncated_message}")
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Protocol chat fallback error: {str(e)}")
        return Response({
            'success': False,
            'error': f'備用服務器錯誤: {str(e)}',
            'fallback': True
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def create_fallback_protocol_chat_response(message, conversation_id=None, include_metadata=True):
    """
    創建備用 Protocol Chat 響應的便利函數
    
    Args:
        message: 用戶訊息
        conversation_id: 對話 ID（可選）
        include_metadata: 是否包含詳細的 metadata
        
    Returns:
        Dict: 響應數據字典
    """
    truncated_message = message[:50] + ("..." if len(message) > 50 else "")
    
    response_data = {
        'success': True,
        'answer': f'已收到您的 Protocol RAG 查詢：{truncated_message}。由於主要服務不可用，這是備用回應。',
        'conversation_id': conversation_id or 'fallback_conversation',
        'message_id': 'fallback_message',
        'response_time': 0.1,
        'usage': {}
    }
    
    if include_metadata:
        response_data['metadata'] = {
            'source': 'fallback_implementation',
            'fallback_reason': 'protocol_chat_service_unavailable',
            'original_message_length': len(message),
            'truncated': len(message) > 50
        }
        response_data['warning'] = 'This is a fallback response. Protocol Chat service is temporarily unavailable.'
    
    return response_data


def validate_protocol_chat_input(data):
    """
    驗證 Protocol Chat 輸入數據
    
    Args:
        data: 請求數據字典
        
    Returns:
        tuple: (is_valid, error_response_or_none)
    """
    message = data.get('message', '').strip()
    
    if not message:
        error_response = Response({
            'success': False,
            'error': '訊息內容不能為空',
            'error_code': 'EMPTY_MESSAGE'
        }, status=status.HTTP_400_BAD_REQUEST)
        return False, error_response
    
    return True, None


# 便利函數：處理完整的備用 Protocol Chat 請求
def handle_fallback_protocol_chat_request(request):
    """
    處理完整的備用 Protocol Chat 請求
    包含輸入驗證、日誌記錄和錯誤處理
    
    Args:
        request: Django request 對象
        
    Returns:
        Django Response 對象
    """
    return fallback_protocol_chat_api(request)