"""
對話管理 Library

提供完整的對話記錄、管理和查詢功能，支援用戶和訪客。

主要功能：
- 對話會話管理
- 訊息記錄和查詢
- 用戶和訪客識別
- 統計分析功能

Author: AI Platform Team
Created: 2024-10-08
"""

# 檢查依賴和可用性
CONVERSATION_MANAGEMENT_AVAILABLE = False

try:
    # 檢查 Django 模型是否可用
    from api.models import ConversationSession, ChatMessage
    
    # 導入核心功能
    from .conversation_recorder import ConversationRecorder
    from .conversation_manager import ConversationManager
    from .guest_identifier import GuestIdentifier
    from .statistics import ConversationStatistics
    from .api_handlers import ConversationAPIHandler
    
    CONVERSATION_MANAGEMENT_AVAILABLE = True
    
    # 便利函數
    from .convenience_functions import (
        record_user_message,
        record_assistant_message,
        get_conversation_history,
        create_conversation_session,
        get_or_create_session,
        record_complete_exchange
    )
    
except ImportError as e:
    # 如果依賴不可用，提供備用實現
    print(f"Conversation Management Library 部分功能不可用: {str(e)}")
    
    # 提供最小化的備用實現
    class ConversationRecorder:
        @staticmethod
        def record_message(*args, **kwargs):
            return {"success": False, "error": "Library not available"}
    
    class ConversationManager:
        @staticmethod
        def get_user_conversations(*args, **kwargs):
            return []

# 版本資訊
__version__ = "1.0.0"
__all__ = [
    'CONVERSATION_MANAGEMENT_AVAILABLE',
    'ConversationRecorder',
    'ConversationManager', 
    'GuestIdentifier',
    'ConversationStatistics',
    'ConversationAPIHandler',
    'record_user_message',
    'record_assistant_message',
    'get_conversation_history',
    'create_conversation_session',
    'get_or_create_session',
    'record_complete_exchange'
]