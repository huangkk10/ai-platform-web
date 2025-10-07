"""
訪客識別器 - Guest Identifier

提供訪客用戶的唯一標識生成和管理功能。

Author: AI Platform Team  
Created: 2024-10-08
"""

import hashlib
import logging
import time
from typing import Optional
from django.http import HttpRequest

logger = logging.getLogger(__name__)


class GuestIdentifier:
    """訪客識別器類"""
    
    @staticmethod
    def generate_guest_id(request: HttpRequest) -> str:
        """
        為訪客生成唯一標識符
        
        Args:
            request: Django HttpRequest 物件
            
        Returns:
            str: 訪客唯一標識符
        """
        try:
            # 方法 1: 使用 Session Key （優先）
            if hasattr(request, 'session') and request.session.session_key:
                return f"guest_session_{request.session.session_key}"
            
            # 方法 2: 使用 IP + User Agent 雜湊
            ip_address = GuestIdentifier._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:200]  # 限制長度
            
            # 建立雜湊
            hash_string = f"{ip_address}_{user_agent}"
            hash_object = hashlib.md5(hash_string.encode('utf-8'))
            hash_hex = hash_object.hexdigest()[:16]  # 取前16位
            
            guest_id = f"guest_{hash_hex}"
            
            logger.debug(f"Generated guest ID: {guest_id}")
            return guest_id
            
        except Exception as e:
            logger.error(f"Failed to generate guest ID: {str(e)}")
            # 備用方案：使用時間戳
            import time
            timestamp = str(int(time.time() * 1000))[-8:]  # 取後8位毫秒時間戳
            return f"guest_fallback_{timestamp}"
    
    @staticmethod
    def _get_client_ip(request: HttpRequest) -> str:
        """
        獲取客戶端真實 IP 地址
        
        Args:
            request: Django HttpRequest 物件
            
        Returns:
            str: 客戶端 IP 地址
        """
        # 檢查代理服務器頭部
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
            return ip
        
        # 檢查其他代理頭部
        x_real_ip = request.META.get('HTTP_X_REAL_IP')
        if x_real_ip:
            return x_real_ip.strip()
        
        # 預設使用 REMOTE_ADDR
        return request.META.get('REMOTE_ADDR', '127.0.0.1')
    
    @staticmethod
    def is_guest_request(request: HttpRequest) -> bool:
        """
        判斷請求是否來自訪客
        
        Args:
            request: Django HttpRequest 物件
            
        Returns:
            bool: 是否為訪客請求
        """
        return not (hasattr(request, 'user') and request.user.is_authenticated)
    
    @staticmethod
    def get_user_or_guest_id(request: HttpRequest) -> tuple:
        """
        獲取用戶ID或訪客標識
        
        Args:
            request: Django HttpRequest 物件
            
        Returns:
            tuple: (user_obj_or_none, guest_id_or_none, is_guest)
        """
        try:
            if hasattr(request, 'user') and request.user.is_authenticated:
                # 已登入用戶
                return request.user, None, False
            else:
                # 訪客用戶
                guest_id = GuestIdentifier.generate_guest_id(request)
                return None, guest_id, True
                
        except Exception as e:
            logger.error(f"Error in get_user_or_guest_id: {str(e)}")
            # 備用方案
            guest_id = f"guest_error_{int(time.time())}"
            return None, guest_id, True
    
    @staticmethod
    def validate_guest_id(guest_id: str) -> bool:
        """
        驗證訪客ID格式是否正確
        
        Args:
            guest_id: 訪客ID字符串
            
        Returns:
            bool: 是否為有效的訪客ID
        """
        if not guest_id or not isinstance(guest_id, str):
            return False
        
        # 檢查是否符合預期格式
        valid_prefixes = ['guest_session_', 'guest_', 'guest_fallback_', 'guest_error_']
        
        return any(guest_id.startswith(prefix) for prefix in valid_prefixes)


# 便利函數
def get_request_identifier(request: HttpRequest) -> dict:
    """
    獲取請求的完整標識資訊
    
    Args:
        request: Django HttpRequest 物件
        
    Returns:
        dict: 包含用戶/訪客標識資訊的字典
    """
    user, guest_id, is_guest = GuestIdentifier.get_user_or_guest_id(request)
    
    return {
        'user': user,
        'guest_id': guest_id, 
        'is_guest': is_guest,
        'identifier': guest_id if is_guest else f"user_{user.id}",
        'display_name': guest_id if is_guest else user.username,
        'ip_address': GuestIdentifier._get_client_ip(request),
        'user_agent': request.META.get('HTTP_USER_AGENT', '')[:200]
    }