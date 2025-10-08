"""
Message Feedback Handler - 處理用戶對 AI 回覆的反饋評分

此模組負責：
- 記錄用戶對消息的按讚/按踩反饋
- 更新數據庫中的 is_helpful 字段
- 提供反饋統計功能
- 與對話管理系統集成
"""

import logging
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)

class MessageFeedbackHandler:
    """消息反饋處理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def record_feedback(self, message_id, is_helpful, user=None, guest_identifier=None):
        """
        記錄用戶對消息的反饋
        
        Args:
            message_id (str): 消息ID
            is_helpful (bool): True為按讚，False為按踩
            user (User): 登入用戶（可選）
            guest_identifier (str): 訪客識別碼（可選）
            
        Returns:
            dict: 處理結果
        """
        try:
            from api.models import ChatMessage
            
            # 查找消息
            try:
                message = ChatMessage.objects.get(message_id=message_id)
            except ChatMessage.DoesNotExist:
                return {
                    'success': False,
                    'error': f'消息不存在: {message_id}'
                }
            
            # 只能對 AI 回覆進行評分
            if message.role != 'assistant':
                return {
                    'success': False,
                    'error': '只能對 AI 回覆進行評分'
                }
            
            # 更新反饋
            old_feedback = message.is_helpful
            message.is_helpful = is_helpful
            message.save(update_fields=['is_helpful', 'updated_at'])
            
            # 更新對話會話的統計數據
            self._update_session_stats(message.conversation_id)
            
            self.logger.info(
                f"消息反饋已記錄: message_id={message_id}, "
                f"is_helpful={is_helpful}, "
                f"user={user.username if user else 'guest'}, "
                f"old_feedback={old_feedback}"
            )
            
            return {
                'success': True,
                'message_id': message_id,
                'is_helpful': is_helpful,
                'previous_feedback': old_feedback,
                'updated_at': message.updated_at.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"記錄消息反饋失敗: {str(e)}")
            return {
                'success': False,
                'error': f'記錄反饋失敗: {str(e)}'
            }
    
    def _update_session_stats(self, conversation_id):
        """更新對話會話的統計數據"""
        try:
            from api.models import ConversationSession, ChatMessage
            
            session = ConversationSession.objects.get(id=conversation_id)
            messages = ChatMessage.objects.filter(
                conversation_id=conversation_id,
                role='assistant'
            )
            
            # 計算滿意度統計
            total_messages = messages.count()
            if total_messages > 0:
                helpful_messages = messages.filter(is_helpful=True).count()
                unhelpful_messages = messages.filter(is_helpful=False).count()
                
                # 計算滿意度分數（0-1之間）
                if helpful_messages + unhelpful_messages > 0:
                    satisfaction_score = helpful_messages / (helpful_messages + unhelpful_messages)
                else:
                    satisfaction_score = None
                
                # 如果 ConversationSession 有 satisfaction_score 字段，更新它
                # 這裡暫時註解，因為可能需要先添加這個字段
                # session.satisfaction_score = satisfaction_score
                # session.save(update_fields=['satisfaction_score', 'updated_at'])
                
                self.logger.debug(
                    f"會話統計已更新: conversation_id={conversation_id}, "
                    f"satisfaction_score={satisfaction_score}"
                )
                
        except Exception as e:
            self.logger.error(f"更新會話統計失敗: {str(e)}")
    
    def get_message_feedback_stats(self, conversation_id=None, user=None, days=30):
        """
        獲取消息反饋統計
        
        Args:
            conversation_id (int): 特定對話ID（可選）
            user (User): 特定用戶（可選）
            days (int): 統計天數
            
        Returns:
            dict: 統計結果
        """
        try:
            from api.models import ChatMessage, ConversationSession
            from django.utils import timezone
            from datetime import timedelta
            
            # 基礎查詢
            queryset = ChatMessage.objects.filter(role='assistant')
            
            # 時間範圍過濾
            if days:
                start_date = timezone.now() - timedelta(days=days)
                queryset = queryset.filter(created_at__gte=start_date)
            
            # 對話過濾
            if conversation_id:
                queryset = queryset.filter(conversation_id=conversation_id)
            
            # 用戶過濾
            if user:
                user_sessions = ConversationSession.objects.filter(user=user)
                queryset = queryset.filter(conversation_id__in=user_sessions.values_list('id', flat=True))
            
            # 統計計算
            total_messages = queryset.count()
            helpful_messages = queryset.filter(is_helpful=True).count()
            unhelpful_messages = queryset.filter(is_helpful=False).count()
            unrated_messages = queryset.filter(is_helpful__isnull=True).count()
            
            # 計算滿意度
            if helpful_messages + unhelpful_messages > 0:
                satisfaction_rate = helpful_messages / (helpful_messages + unhelpful_messages)
            else:
                satisfaction_rate = None
            
            return {
                'total_messages': total_messages,
                'helpful_messages': helpful_messages,
                'unhelpful_messages': unhelpful_messages,
                'unrated_messages': unrated_messages,
                'satisfaction_rate': satisfaction_rate,
                'feedback_rate': (helpful_messages + unhelpful_messages) / total_messages if total_messages > 0 else 0,
                'stats_period_days': days
            }
            
        except Exception as e:
            self.logger.error(f"獲取反饋統計失敗: {str(e)}")
            return {
                'error': f'獲取統計失敗: {str(e)}'
            }

# 便利函數
def record_message_feedback(message_id, is_helpful, user=None, guest_identifier=None):
    """記錄消息反饋的便利函數"""
    handler = MessageFeedbackHandler()
    return handler.record_feedback(message_id, is_helpful, user, guest_identifier)

def get_message_feedback_stats(conversation_id=None, user=None, days=30):
    """獲取反饋統計的便利函數"""
    handler = MessageFeedbackHandler()
    return handler.get_message_feedback_stats(conversation_id, user, days)

# API 處理器
def handle_message_feedback_api(request):
    """
    處理消息反饋 API 請求
    
    Expected payload:
    {
        "message_id": "uuid-string",
        "is_helpful": true/false
    }
    """
    try:
        if request.method != 'POST':
            return JsonResponse({
                'success': False,
                'error': 'Only POST method allowed'
            }, status=405)
        
        # 解析請求數據
        try:
            import json
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON format'
            }, status=400)
        
        message_id = data.get('message_id')
        is_helpful = data.get('is_helpful')
        
        if not message_id:
            return JsonResponse({
                'success': False,
                'error': 'message_id is required'
            }, status=400)
        
        if is_helpful is None:
            return JsonResponse({
                'success': False,
                'error': 'is_helpful is required'
            }, status=400)
        
        # 獲取用戶信息
        user = None
        guest_identifier = None
        
        if request.user.is_authenticated:
            user = request.user
        else:
            # 對於訪客，可以使用 session key 作為識別碼
            guest_identifier = request.session.session_key
        
        # 記錄反饋
        result = record_message_feedback(
            message_id=message_id,
            is_helpful=is_helpful,
            user=user,
            guest_identifier=guest_identifier
        )
        
        if result['success']:
            return JsonResponse(result, status=200)
        else:
            return JsonResponse(result, status=400)
            
    except Exception as e:
        logger.error(f"Message feedback API error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'服務器錯誤: {str(e)}'
        }, status=500)