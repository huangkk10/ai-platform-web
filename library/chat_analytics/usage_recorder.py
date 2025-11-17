"""
Chat Usage Recorder - 聊天使用記錄處理器
=====================================

處理聊天使用記錄相關的邏輯：
- 聊天類型驗證
- 客戶端信息提取
- 使用記錄創建
- 記錄結果處理
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# 有效的聊天類型
VALID_CHAT_TYPES = ['know_issue_chat', 'log_analyze_chat', 'rvt_assistant_chat', 'protocol_assistant_chat']


class ChatUsageRecorder:
    """聊天使用記錄處理器 - 處理聊天使用記錄"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.valid_types = VALID_CHAT_TYPES
    
    def validate_chat_type(self, chat_type: str) -> bool:
        """
        驗證聊天類型
        
        Args:
            chat_type: 聊天類型
            
        Returns:
            bool: 是否有效
        """
        is_valid = chat_type in self.valid_types
        if not is_valid:
            self.logger.warning(f"無效的聊天類型: {chat_type}")
        return is_valid
    
    def extract_client_info(self, request) -> Dict[str, str]:
        """
        提取客戶端信息
        
        Args:
            request: HTTP 請求對象
            
        Returns:
            Dict[str, str]: 客戶端信息
        """
        try:
            # 獲取 IP 地址
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0].strip()
            else:
                ip_address = request.META.get('REMOTE_ADDR', 'unknown')
            
            # 獲取 User Agent
            user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')
            
            client_info = {
                'ip_address': ip_address,
                'user_agent': user_agent
            }
            
            self.logger.debug(f"客戶端信息: IP={ip_address}, UA={user_agent[:50]}...")
            return client_info
            
        except Exception as e:
            self.logger.error(f"客戶端信息提取失敗: {e}")
            return {
                'ip_address': 'unknown',
                'user_agent': 'unknown'
            }
    
    def create_usage_record(self, request_data: Dict[str, Any], client_info: Dict[str, str], user=None) -> Optional[Any]:
        """
        創建使用記錄
        
        Args:
            request_data: 請求數據
            client_info: 客戶端信息
            user: 用戶對象
            
        Returns:
            Usage record 實例或 None
        """
        try:
            # 動態導入避免循環依賴
            from api.models import ChatUsage
            
            usage_record = ChatUsage.objects.create(
                user=user if user and user.is_authenticated else None,
                session_id=request_data.get('session_id', ''),
                chat_type=request_data.get('chat_type'),
                message_count=request_data.get('message_count', 1),
                has_file_upload=request_data.get('has_file_upload', False),
                response_time=request_data.get('response_time'),
                ip_address=client_info['ip_address'],
                user_agent=client_info['user_agent']
            )
            
            self.logger.info(f"聊天使用記錄創建成功: ID={usage_record.id}, 類型={request_data.get('chat_type')}")
            return usage_record
            
        except ImportError:
            self.logger.error("ChatUsage model 不可用")
            return None
        except Exception as e:
            self.logger.error(f"使用記錄創建失敗: {e}")
            return None
    
    def record_chat_usage(self, request_data: Dict[str, Any], client_info: Dict[str, str], user=None) -> Dict[str, Any]:
        """
        記錄聊天使用
        
        Args:
            request_data: 請求數據
            client_info: 客戶端信息
            user: 用戶對象
            
        Returns:
            Dict[str, Any]: 記錄結果
        """
        try:
            chat_type = request_data.get('chat_type')
            
            # 驗證聊天類型
            if not self.validate_chat_type(chat_type):
                return {
                    'success': False,
                    'error': '無效的聊天類型',
                    'valid_types': self.valid_types
                }
            
            # 創建使用記錄
            usage_record = self.create_usage_record(request_data, client_info, user)
            
            if usage_record:
                return {
                    'success': True,
                    'record_id': usage_record.id,
                    'chat_type': chat_type
                }
            else:
                return {
                    'success': False,
                    'error': '記錄創建失敗'
                }
                
        except Exception as e:
            self.logger.error(f"聊天使用記錄處理失敗: {e}")
            return {
                'success': False,
                'error': f'記錄處理失敗: {str(e)}'
            }