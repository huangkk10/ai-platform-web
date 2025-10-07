"""
對話管理器 - Conversation Manager

提供對話會話的管理功能，包括建立、查詢、更新等操作。

Author: AI Platform Team  
Created: 2024-10-08
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from django.http import HttpRequest
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist

from .guest_identifier import GuestIdentifier, get_request_identifier

logger = logging.getLogger(__name__)

# 延遲導入避免循環依賴
def get_models():
    """延遲導入 Django 模型"""
    try:
        from api.models import ConversationSession, ChatMessage
        return ConversationSession, ChatMessage
    except ImportError:
        return None, None


class ConversationManager:
    """對話管理器類"""
    
    @staticmethod
    def create_session(
        request: HttpRequest,
        session_id: str,
        chat_type: str = 'rvt_assistant_chat',
        title: str = "",
        auto_delete_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        建立新的對話會話
        
        Args:
            request: Django HttpRequest 物件
            session_id: 會話ID（通常是 Dify conversation_id）
            chat_type: 聊天類型
            title: 對話標題
            auto_delete_days: 自動刪除天數（僅限訪客）
            
        Returns:
            dict: 建立結果，包含 ConversationSession 實例
        """
        ConversationSession, ChatMessage = get_models()
        if not ConversationSession:
            return {"success": False, "error": "Models not available"}
        
        try:
            # 獲取用戶/訪客標識
            identifier_info = get_request_identifier(request)
            user = identifier_info['user']
            guest_id = identifier_info['guest_id']
            is_guest = identifier_info['is_guest']
            
            # 檢查會話是否已存在
            existing_session = ConversationSession.objects.filter(session_id=session_id).first()
            if existing_session:
                return {
                    "success": True,
                    "session": existing_session,
                    "created": False,
                    "message": "Session already exists"
                }
            
            # 建立自動刪除時間（僅限訪客）
            auto_delete_at = None
            if is_guest and auto_delete_days:
                auto_delete_at = timezone.now() + timedelta(days=auto_delete_days)
            
            # 生成預設標題
            if not title:
                if is_guest:
                    title = f"訪客對話 - {timezone.now().strftime('%m/%d %H:%M')}"
                else:
                    title = f"{user.username} 的對話 - {timezone.now().strftime('%m/%d %H:%M')}"
            
            # 建立會話
            with transaction.atomic():
                session = ConversationSession.objects.create(
                    session_id=session_id,
                    user=user,
                    guest_identifier=guest_id,
                    is_guest_session=is_guest,
                    chat_type=chat_type,
                    title=title,
                    auto_delete_at=auto_delete_at
                )
                
                logger.info(f"Created conversation session: {session_id} for {'guest' if is_guest else user.username}")
                
                return {
                    "success": True,
                    "session": session,
                    "created": True,
                    "is_guest": is_guest
                }
                
        except Exception as e:
            logger.error(f"Failed to create conversation session: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to create session: {str(e)}"
            }
    
    @staticmethod
    def get_or_create_session(
        request: HttpRequest,
        session_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        獲取或建立對話會話
        
        Args:
            request: Django HttpRequest 物件
            session_id: 會話ID
            **kwargs: 建立會話時的額外參數
            
        Returns:
            dict: 會話實例和建立狀態
        """
        ConversationSession, ChatMessage = get_models()
        if not ConversationSession:
            return {"success": False, "error": "Models not available"}
        
        try:
            # 先嘗試獲取現有會話
            session = ConversationSession.objects.filter(session_id=session_id).first()
            
            if session:
                return {
                    "success": True,
                    "session": session,
                    "created": False
                }
            
            # 不存在則建立新會話
            return ConversationManager.create_session(
                request=request,
                session_id=session_id,
                **kwargs
            )
            
        except Exception as e:
            logger.error(f"Failed to get or create session: {str(e)}")
            return {
                "success": False,
                "error": f"Get or create failed: {str(e)}"
            }
    
    @staticmethod
    def get_user_conversations(
        request: HttpRequest,
        page: int = 1,
        page_size: int = 20,
        chat_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        獲取用戶的對話列表
        
        Args:
            request: Django HttpRequest 物件
            page: 頁碼
            page_size: 每頁大小
            chat_type: 聊天類型篩選
            
        Returns:
            dict: 對話列表和分頁資訊
        """
        ConversationSession, ChatMessage = get_models()
        if not ConversationSession:
            return {"success": False, "error": "Models not available"}
        
        try:
            # 獲取用戶/訪客標識
            identifier_info = get_request_identifier(request)
            user = identifier_info['user']
            guest_id = identifier_info['guest_id']
            is_guest = identifier_info['is_guest']
            
            # 構建查詢
            if is_guest:
                # 訪客查詢
                queryset = ConversationSession.objects.filter(
                    guest_identifier=guest_id,
                    is_guest_session=True
                )
            else:
                # 登入用戶查詢
                queryset = ConversationSession.objects.filter(
                    user=user,
                    is_guest_session=False
                )
            
            # 篩選聊天類型
            if chat_type:
                queryset = queryset.filter(chat_type=chat_type)
            
            # 排序
            queryset = queryset.order_by('-last_message_at', '-created_at')
            
            # 分頁
            total_count = queryset.count()
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            conversations = list(queryset[start_idx:end_idx])
            
            # 計算分頁資訊
            total_pages = (total_count + page_size - 1) // page_size
            has_next = page < total_pages
            has_prev = page > 1
            
            return {
                "success": True,
                "conversations": conversations,
                "pagination": {
                    "current_page": page,
                    "page_size": page_size,
                    "total_count": total_count,
                    "total_pages": total_pages,
                    "has_next": has_next,
                    "has_prev": has_prev
                },
                "user_info": {
                    "is_guest": is_guest,
                    "identifier": identifier_info['identifier']
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get user conversations: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to get conversations: {str(e)}"
            }
    
    @staticmethod
    def get_conversation_messages(
        conversation_id: int,
        request: HttpRequest = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """
        獲取對話的訊息列表
        
        Args:
            conversation_id: 對話會話ID
            request: Django HttpRequest 物件（用於權限檢查）
            page: 頁碼
            page_size: 每頁大小
            
        Returns:
            dict: 訊息列表和分頁資訊
        """
        ConversationSession, ChatMessage = get_models()
        if not ConversationSession or not ChatMessage:
            return {"success": False, "error": "Models not available"}
        
        try:
            # 獲取對話會話
            session = ConversationSession.objects.get(id=conversation_id)
            
            # 權限檢查（如果提供了 request）
            if request:
                identifier_info = get_request_identifier(request)
                user = identifier_info['user']
                guest_id = identifier_info['guest_id']
                is_guest = identifier_info['is_guest']
                
                # 檢查訪問權限
                if is_guest:
                    if session.guest_identifier != guest_id:
                        return {"success": False, "error": "Access denied"}
                else:
                    if session.user != user:
                        return {"success": False, "error": "Access denied"}
            
            # 獲取訊息
            queryset = ChatMessage.objects.filter(conversation=session).order_by('sequence_number')
            
            # 分頁
            total_count = queryset.count()
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            messages = list(queryset[start_idx:end_idx])
            
            # 分頁資訊
            total_pages = (total_count + page_size - 1) // page_size
            
            return {
                "success": True,
                "session": session,
                "messages": messages,
                "pagination": {
                    "current_page": page,
                    "page_size": page_size,
                    "total_count": total_count,
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_prev": page > 1
                }
            }
            
        except ConversationSession.DoesNotExist:
            return {"success": False, "error": "Conversation not found"}
        except Exception as e:
            logger.error(f"Failed to get conversation messages: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to get messages: {str(e)}"
            }
    
    @staticmethod
    def update_session_title(
        session_id: str,
        new_title: str,
        request: HttpRequest = None
    ) -> Dict[str, Any]:
        """
        更新對話會話標題
        
        Args:
            session_id: 會話ID
            new_title: 新標題
            request: Django HttpRequest 物件（用於權限檢查）
            
        Returns:
            dict: 更新結果
        """
        ConversationSession, ChatMessage = get_models()
        if not ConversationSession:
            return {"success": False, "error": "Models not available"}
        
        try:
            session = ConversationSession.objects.get(session_id=session_id)
            
            # 權限檢查
            if request:
                identifier_info = get_request_identifier(request)
                user = identifier_info['user']
                guest_id = identifier_info['guest_id']
                is_guest = identifier_info['is_guest']
                
                if is_guest:
                    if session.guest_identifier != guest_id:
                        return {"success": False, "error": "Access denied"}
                else:
                    if session.user != user:
                        return {"success": False, "error": "Access denied"}
            
            # 更新標題
            session.title = new_title
            session.save(update_fields=['title', 'updated_at'])
            
            return {
                "success": True,
                "message": "Title updated successfully",
                "session": session
            }
            
        except ConversationSession.DoesNotExist:
            return {"success": False, "error": "Session not found"}
        except Exception as e:
            logger.error(f"Failed to update session title: {str(e)}")
            return {
                "success": False,
                "error": f"Update failed: {str(e)}"
            }
    
    @staticmethod
    def cleanup_expired_guest_sessions() -> Dict[str, Any]:
        """
        清理過期的訪客會話
        
        Returns:
            dict: 清理結果
        """
        ConversationSession, ChatMessage = get_models()
        if not ConversationSession:
            return {"success": False, "error": "Models not available"}
        
        try:
            now = timezone.now()
            
            # 查找過期的訪客會話
            expired_sessions = ConversationSession.objects.filter(
                is_guest_session=True,
                auto_delete_at__lte=now
            )
            
            deleted_count = expired_sessions.count()
            if deleted_count > 0:
                # 刪除過期會話（會連同訊息一起刪除，因為有 CASCADE）
                expired_sessions.delete()
                logger.info(f"Cleaned up {deleted_count} expired guest sessions")
            
            return {
                "success": True,
                "deleted_count": deleted_count,
                "message": f"Cleaned up {deleted_count} expired sessions"
            }
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {str(e)}")
            return {
                "success": False,
                "error": f"Cleanup failed: {str(e)}"
            }