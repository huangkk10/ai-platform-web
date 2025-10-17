"""
用戶認證相關 Views
========================================

包含所有用戶認證相關的 API 端點：
- 用戶登入 (user_login_api)
- 用戶註冊 (user_register)
- 用戶登出 (user_logout)
- 更改密碼 (change_password)
- 獲取用戶資訊 (user_info)

重構自 legacy_views.py
Created: 2025-10-17
"""

import logging
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)

# 導入認證服務 library
try:
    from library.auth import DRFAuthHandler
    AUTH_LIBRARY_AVAILABLE = True
except ImportError as e:
    logger.error(f"無法導入 Auth Library: {e}")
    AUTH_LIBRARY_AVAILABLE = False
    DRFAuthHandler = None


# ============= 用戶認證 API =============

@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([])
def user_login_api(request):
    """
    用戶登入 API - 統一使用 DRFAuthHandler 實現
    
    優化版本：移除 class-based view，統一使用 function-based view
    
    Request Body:
        {
            "username": "string",
            "password": "string"
        }
    
    Response:
        {
            "success": true,
            "message": "登入成功",
            "data": {
                "user": {...},
                "token": "...",
                "permissions": [...]
            }
        }
    """
    if AUTH_LIBRARY_AVAILABLE and DRFAuthHandler:
        return DRFAuthHandler.handle_login_api(request)
    else:
        from rest_framework.response import Response
        from rest_framework import status
        return Response({
            'success': False,
            'message': '認證服務不可用'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([])
def user_register(request):
    """
    用戶註冊 API - 完全使用 library/auth/DRFAuthHandler 實現
    
    Request Body:
        {
            "username": "string",
            "password": "string",
            "email": "string",
            "first_name": "string",
            "last_name": "string"
        }
    
    Response:
        {
            "success": true,
            "message": "註冊成功",
            "data": {
                "user": {...}
            }
        }
    """
    if AUTH_LIBRARY_AVAILABLE and DRFAuthHandler:
        return DRFAuthHandler.handle_register_api(request)
    else:
        from rest_framework.response import Response
        from rest_framework import status
        return Response({
            'success': False,
            'message': '註冊服務不可用'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([])
def user_logout(request):
    """
    用戶登出 API - 完全使用 library/auth/DRFAuthHandler 實現
    
    Response:
        {
            "success": true,
            "message": "登出成功"
        }
    """
    if AUTH_LIBRARY_AVAILABLE and DRFAuthHandler:
        return DRFAuthHandler.handle_logout_api(request)
    else:
        from rest_framework.response import Response
        from rest_framework import status
        return Response({
            'success': False,
            'message': '登出服務不可用'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    更改密碼 API - 完全使用 library/auth/DRFAuthHandler 實現
    
    Request Body:
        {
            "old_password": "string",
            "new_password": "string"
        }
    
    Response:
        {
            "success": true,
            "message": "密碼更改成功"
        }
    """
    if AUTH_LIBRARY_AVAILABLE and DRFAuthHandler:
        return DRFAuthHandler.handle_change_password_api(request)
    else:
        from rest_framework.response import Response
        from rest_framework import status
        return Response({
            'success': False,
            'message': '密碼更改服務不可用'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(['GET'])
@permission_classes([])
def user_info(request):
    """
    獲取當前用戶資訊 API - 完全使用 library/auth/DRFAuthHandler 實現
    
    Response:
        {
            "success": true,
            "data": {
                "user": {
                    "id": 1,
                    "username": "string",
                    "email": "string",
                    "first_name": "string",
                    "last_name": "string"
                },
                "permissions": [...]
            }
        }
    """
    if AUTH_LIBRARY_AVAILABLE and DRFAuthHandler:
        return DRFAuthHandler.handle_user_info_api(request)
    else:
        from rest_framework.response import Response
        from rest_framework import status
        return Response({
            'success': False,
            'message': '用戶資訊服務不可用'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
