"""
便利函數 - Convenience Functions

提供簡化的 API 函數，方便快速使用對話管理功能。

Author: AI Platform Team
Created: 2024-10-08
"""

import logging
from typing import Dict, Any, Optional
from django.http import HttpRequest

from .conversation_manager import ConversationManager
from .conversation_recorder import ConversationRecorder

logger = logging.getLogger(__name__)


def create_conversation_session(
    request: HttpRequest,
    session_id: str,
    chat_type: str = 'rvt_assistant_chat',
    title: str = "",
    auto_delete_days: Optional[int] = None
) -> Dict[str, Any]:
    """
    建立對話會話的便利函數
    
    Args:
        request: Django HttpRequest 物件
        session_id: 會話ID
        chat_type: 聊天類型
        title: 對話標題
        auto_delete_days: 自動刪除天數（僅限訪客）
        
    Returns:
        dict: 建立結果
    """
    return ConversationManager.create_session(
        request=request,
        session_id=session_id,
        chat_type=chat_type,
        title=title,
        auto_delete_days=auto_delete_days
    )


def get_or_create_session(
    request: HttpRequest,
    session_id: str,
    **kwargs
) -> Dict[str, Any]:
    """
    獲取或建立對話會話的便利函數
    
    Args:
        request: Django HttpRequest 物件
        session_id: 會話ID
        **kwargs: 其他參數
        
    Returns:
        dict: 會話實例
    """
    return ConversationManager.get_or_create_session(
        request=request,
        session_id=session_id,
        **kwargs
    )


def record_user_message(
    session_or_session_id,
    content: str,
    request: HttpRequest = None,
    **kwargs
) -> Dict[str, Any]:
    """
    記錄用戶訊息的便利函數
    
    Args:
        session_or_session_id: ConversationSession 實例或會話ID字符串
        content: 用戶訊息內容
        request: Django HttpRequest 物件（當傳入 session_id 時必需）
        **kwargs: 其他參數
        
    Returns:
        dict: 記錄結果
    """
    try:
        # 如果傳入的是字符串，則視為 session_id
        if isinstance(session_or_session_id, str):
            if not request:
                return {"success": False, "error": "Request is required when using session_id"}
            
            # 獲取會話實例
            session_result = get_or_create_session(request, session_or_session_id)
            if not session_result["success"]:
                return session_result
            
            session = session_result["session"]
        else:
            # 直接使用傳入的 session 實例
            session = session_or_session_id
        
        # 記錄訊息
        return ConversationRecorder.record_user_message(
            conversation_session=session,
            content=content,
            **kwargs
        )
        
    except Exception as e:
        logger.error(f"Failed to record user message: {str(e)}")
        return {"success": False, "error": f"Record failed: {str(e)}"}


def record_assistant_message(
    session_or_session_id,
    content: str,
    request: HttpRequest = None,
    response_time: Optional[float] = None,
    token_usage: Optional[Dict] = None,
    metadata: Optional[Dict] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    記錄AI助手回覆的便利函數
    
    Args:
        session_or_session_id: ConversationSession 實例或會話ID字符串
        content: AI回覆內容
        request: Django HttpRequest 物件（當傳入 session_id 時必需）
        response_time: 回應時間
        token_usage: Token使用統計
        metadata: 元資料
        **kwargs: 其他參數
        
    Returns:
        dict: 記錄結果
    """
    try:
        # 如果傳入的是字符串，則視為 session_id
        if isinstance(session_or_session_id, str):
            if not request:
                return {"success": False, "error": "Request is required when using session_id"}
            
            # 獲取會話實例
            session_result = get_or_create_session(request, session_or_session_id)
            if not session_result["success"]:
                return session_result
            
            session = session_result["session"]
        else:
            # 直接使用傳入的 session 實例
            session = session_or_session_id
        
        # 記錄訊息
        return ConversationRecorder.record_assistant_message(
            conversation_session=session,
            content=content,
            response_time=response_time,
            token_usage=token_usage,
            metadata=metadata,
            **kwargs
        )
        
    except Exception as e:
        logger.error(f"Failed to record assistant message: {str(e)}")
        return {"success": False, "error": f"Record failed: {str(e)}"}


def get_conversation_history(
    request: HttpRequest,
    session_id: Optional[str] = None,
    conversation_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 50
) -> Dict[str, Any]:
    """
    獲取對話歷史的便利函數
    
    Args:
        request: Django HttpRequest 物件
        session_id: 會話ID字符串
        conversation_id: 對話ID數字
        page: 頁碼
        page_size: 每頁大小
        
    Returns:
        dict: 對話歷史
    """
    try:
        if session_id:
            # 通過 session_id 獲取
            # 首先需要找到對應的 conversation_id
            try:
                from api.models import ConversationSession
                session = ConversationSession.objects.get(session_id=session_id)
                conversation_id = session.id
            except:
                return {"success": False, "error": "Session not found"}
        
        if not conversation_id:
            return {"success": False, "error": "Either session_id or conversation_id is required"}
        
        # 獲取對話訊息
        return ConversationManager.get_conversation_messages(
            conversation_id=conversation_id,
            request=request,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"Failed to get conversation history: {str(e)}")
        return {"success": False, "error": f"Get history failed: {str(e)}"}


def get_user_conversation_list(
    request: HttpRequest,
    page: int = 1,
    page_size: int = 20,
    chat_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    獲取用戶對話列表的便利函數
    
    Args:
        request: Django HttpRequest 物件
        page: 頁碼
        page_size: 每頁大小
        chat_type: 聊天類型篩選
        
    Returns:
        dict: 對話列表
    """
    return ConversationManager.get_user_conversations(
        request=request,
        page=page,
        page_size=page_size,
        chat_type=chat_type
    )


def record_complete_exchange(
    request: HttpRequest,
    session_id: str,
    user_message: str,
    assistant_message: str,
    response_time: Optional[float] = None,
    token_usage: Optional[Dict] = None,
    metadata: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    記錄完整的一問一答交互的便利函數
    
    Args:
        request: Django HttpRequest 物件
        session_id: 會話ID
        user_message: 用戶訊息
        assistant_message: AI回覆
        response_time: 回應時間
        token_usage: Token使用統計
        metadata: 元資料
        
    Returns:
        dict: 記錄結果
    """
    try:
        # 獲取或建立會話
        session_result = get_or_create_session(request, session_id)
        if not session_result["success"]:
            return session_result
        
        session = session_result["session"]
        
        # 記錄用戶訊息
        user_result = ConversationRecorder.record_user_message(
            conversation_session=session,
            content=user_message
        )
        
        if not user_result["success"]:
            return user_result
        
        # 記錄AI回覆
        # 從 metadata 中提取 dify_message_id 作為 message_id
        dify_message_id = ""
        if metadata and isinstance(metadata, dict):
            dify_message_id = metadata.get('dify_message_id', '')
        
        assistant_result = ConversationRecorder.record_assistant_message(
            conversation_session=session,
            content=assistant_message,
            response_time=response_time,
            token_usage=token_usage,
            metadata=metadata,
            message_id=dify_message_id  # 添加 message_id 參數
        )
        
        if not assistant_result["success"]:
            return assistant_result
        
        return {
            "success": True,
            "session": session,
            "user_message": user_result,
            "assistant_message": assistant_result,
            "message": "Complete exchange recorded successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to record complete exchange: {str(e)}")
        return {"success": False, "error": f"Record exchange failed: {str(e)}"}