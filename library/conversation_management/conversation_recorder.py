"""
對話記錄器 - Conversation Recorder

負責記錄用戶和AI之間的對話訊息到資料庫。

Author: AI Platform Team
Created: 2024-10-08  
"""

import logging
from typing import Dict, Any, Optional
from django.http import HttpRequest
from django.utils import timezone
from django.db import transaction

logger = logging.getLogger(__name__)

# 延遲導入避免循環依賴
def get_models():
    """延遲導入 Django 模型"""
    try:
        from api.models import ConversationSession, ChatMessage
        return ConversationSession, ChatMessage
    except ImportError:
        return None, None


class ConversationRecorder:
    """對話記錄器類"""
    
    @staticmethod
    def record_message(
        conversation_session: Any,
        role: str,
        content: str,
        message_id: str = "",
        response_time: Optional[float] = None,
        token_usage: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
        content_type: str = "text"
    ) -> Dict[str, Any]:
        """
        記錄單條訊息
        
        Args:
            conversation_session: ConversationSession 實例
            role: 訊息角色 ('user', 'assistant', 'system')
            content: 訊息內容
            message_id: 訊息ID（可選）
            response_time: 回應時間（秒）
            token_usage: Token使用統計
            metadata: 額外元資料
            content_type: 內容類型
            
        Returns:
            dict: 記錄結果
        """
        ConversationSession, ChatMessage = get_models()
        if not ChatMessage:
            return {"success": False, "error": "Models not available"}
        
        try:
            with transaction.atomic():
                # 建立訊息記錄
                message = ChatMessage.objects.create(
                    conversation=conversation_session,
                    message_id=message_id,
                    role=role,
                    content=content,
                    content_type=content_type,
                    response_time=response_time,
                    token_usage=token_usage,
                    metadata=metadata
                )
                
                # 自動更新會話統計（透過模型的 save 方法觸發）
                logger.info(f"Message recorded: {role} message #{message.sequence_number}")
                
                return {
                    "success": True,
                    "message_id": message.id,
                    "sequence_number": message.sequence_number,
                    "conversation_id": conversation_session.id
                }
                
        except Exception as e:
            logger.error(f"Failed to record message: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to record message: {str(e)}"
            }
    
    @staticmethod
    def record_user_message(
        conversation_session: Any,
        content: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        記錄用戶訊息的便利方法
        
        Args:
            conversation_session: ConversationSession 實例
            content: 用戶訊息內容
            **kwargs: 其他可選參數
            
        Returns:
            dict: 記錄結果
        """
        return ConversationRecorder.record_message(
            conversation_session=conversation_session,
            role='user',
            content=content,
            **kwargs
        )
    
    @staticmethod
    def record_assistant_message(
        conversation_session: Any,
        content: str,
        response_time: Optional[float] = None,
        token_usage: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
        message_id: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        """
        記錄AI助手回覆的便利方法
        
        Args:
            conversation_session: ConversationSession 實例  
            content: AI回覆內容
            response_time: 回應時間
            token_usage: Token使用統計
            metadata: Dify回傳的元資料
            **kwargs: 其他可選參數
            
        Returns:
            dict: 記錄結果
        """
        return ConversationRecorder.record_message(
            conversation_session=conversation_session,
            role='assistant',
            content=content,
            message_id=message_id,
            response_time=response_time,
            token_usage=token_usage,
            metadata=metadata,
            **kwargs
        )
    
    @staticmethod
    def record_system_message(
        conversation_session: Any,
        content: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        記錄系統訊息的便利方法
        
        Args:
            conversation_session: ConversationSession 實例
            content: 系統訊息內容
            **kwargs: 其他可選參數
            
        Returns:
            dict: 記錄結果
        """
        return ConversationRecorder.record_message(
            conversation_session=conversation_session,
            role='system',
            content=content,
            **kwargs
        )
    
    @staticmethod
    def batch_record_messages(
        conversation_session: Any,
        messages: list
    ) -> Dict[str, Any]:
        """
        批量記錄多條訊息
        
        Args:
            conversation_session: ConversationSession 實例
            messages: 訊息列表，每個元素包含訊息資訊
            
        Returns:
            dict: 批量記錄結果
        """
        ConversationSession, ChatMessage = get_models()
        if not ChatMessage:
            return {"success": False, "error": "Models not available"}
        
        try:
            with transaction.atomic():
                recorded_messages = []
                
                for msg_data in messages:
                    result = ConversationRecorder.record_message(
                        conversation_session=conversation_session,
                        **msg_data
                    )
                    
                    if result["success"]:
                        recorded_messages.append(result)
                    else:
                        # 如果任何一條失敗，回滾整個事務
                        raise Exception(f"Failed to record message: {result['error']}")
                
                return {
                    "success": True,
                    "recorded_count": len(recorded_messages),
                    "messages": recorded_messages
                }
                
        except Exception as e:
            logger.error(f"Failed to batch record messages: {str(e)}")
            return {
                "success": False,
                "error": f"Batch record failed: {str(e)}"
            }
    
    @staticmethod
    def update_message_feedback(
        message_id: int,
        is_helpful: Optional[bool] = None,
        is_bookmarked: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        更新訊息的用戶反饋
        
        Args:
            message_id: 訊息ID
            is_helpful: 是否有幫助
            is_bookmarked: 是否收藏
            
        Returns:
            dict: 更新結果
        """
        ConversationSession, ChatMessage = get_models()
        if not ChatMessage:
            return {"success": False, "error": "Models not available"}
        
        try:
            message = ChatMessage.objects.get(id=message_id)
            
            update_fields = []
            if is_helpful is not None:
                message.is_helpful = is_helpful
                update_fields.append('is_helpful')
            
            if is_bookmarked is not None:
                message.is_bookmarked = is_bookmarked
                update_fields.append('is_bookmarked')
            
            if update_fields:
                update_fields.append('updated_at')
                message.save(update_fields=update_fields)
                
                return {
                    "success": True,
                    "message": "Feedback updated successfully"
                }
            else:
                return {
                    "success": False,
                    "error": "No feedback data provided"
                }
                
        except ChatMessage.DoesNotExist:
            return {
                "success": False,
                "error": "Message not found"
            }
        except Exception as e:
            logger.error(f"Failed to update message feedback: {str(e)}")
            return {
                "success": False,
                "error": f"Update failed: {str(e)}"
            }