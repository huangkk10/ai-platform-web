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
    用戶登入 API - 帶審核狀態檢查
    
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
        # 🆕 Fallback 實現：帶審核狀態檢查的登入
        from rest_framework.response import Response
        from rest_framework import status as http_status
        from django.contrib.auth import authenticate, login
        from django.contrib.auth.models import User
        from api.models import UserProfile
        from rest_framework.authtoken.models import Token
        
        try:
            username = request.data.get('username', '').strip()
            password = request.data.get('password', '').strip()
            
            if not username or not password:
                return Response({
                    'success': False,
                    'error': '請提供用戶名和密碼'
                }, status=http_status.HTTP_400_BAD_REQUEST)
            
            # 驗證用戶憑證
            user = authenticate(username=username, password=password)
            
            if user is None:
                return Response({
                    'success': False,
                    'error': '用戶名或密碼錯誤'
                }, status=http_status.HTTP_400_BAD_REQUEST)
            
            # 🆕 檢查帳號審核狀態
            try:
                profile = user.userprofile
                
                if profile.account_status == 'pending':
                    return Response({
                        'success': False,
                        'error': '您的帳號尚未通過審核，請耐心等待管理員審核通知',
                        'status': 'pending'
                    }, status=http_status.HTTP_403_FORBIDDEN)
                
                elif profile.account_status == 'rejected':
                    rejection_reason = profile.rejection_reason or '未提供原因'
                    return Response({
                        'success': False,
                        'error': f'您的帳號申請已被拒絕。原因：{rejection_reason}',
                        'status': 'rejected',
                        'rejection_reason': rejection_reason
                    }, status=http_status.HTTP_403_FORBIDDEN)
                
                elif profile.account_status == 'suspended':
                    return Response({
                        'success': False,
                        'error': '您的帳號已被停用，請聯絡系統管理員',
                        'status': 'suspended'
                    }, status=http_status.HTTP_403_FORBIDDEN)
            
            except UserProfile.DoesNotExist:
                # 向後相容：舊用戶沒有 profile，自動創建並設為已批准
                profile = UserProfile.objects.create(
                    user=user,
                    account_status='approved'
                )
                logger.info(f"為現有用戶 {username} 自動創建 UserProfile")
            
            # 檢查用戶是否啟用
            if not user.is_active:
                return Response({
                    'success': False,
                    'error': '帳號尚未啟用'
                }, status=http_status.HTTP_403_FORBIDDEN)
            
            # SuperUser 豁免審核檢查（確保管理員始終能登入）
            if user.is_superuser:
                if profile.account_status != 'approved':
                    profile.account_status = 'approved'
                    profile.save()
            
            # 登入用戶
            login(request, user)
            
            # 獲取或創建 Token
            token, _ = Token.objects.get_or_create(user=user)
            
            # 準備回應數據
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'account_status': profile.account_status  # 🆕 包含審核狀態
            }
            
            logger.info(f"用戶登入成功: {username}")
            
            return Response({
                'success': True,
                'message': '登入成功',
                'data': {
                    'user': user_data,
                    'token': token.key
                }
            })
            
        except Exception as e:
            logger.error(f"登入失敗: {str(e)}")
            return Response({
                'success': False,
                'error': f'登入失敗: {str(e)}'
            }, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([])
def user_register(request):
    """
    用戶註冊 API - 帶審核機制
    
    Request Body:
        {
            "username": "string",
            "password": "string",
            "email": "string",
            "first_name": "string",
            "last_name": "string",
            "application_department": "string",  # 🆕 申請部門
            "application_reason": "string"       # 🆕 申請理由
        }
    
    Response:
        {
            "success": true,
            "message": "註冊申請已提交，請等待管理員審核",
            "status": "pending",
            "data": {
                "username": "string",
                "email": "string"
            }
        }
    """
    if AUTH_LIBRARY_AVAILABLE and DRFAuthHandler:
        return DRFAuthHandler.handle_register_api(request)
    else:
        # 🆕 Fallback 實現：帶審核機制的註冊
        from rest_framework.response import Response
        from rest_framework import status as http_status
        from django.contrib.auth.models import User
        from api.models import UserProfile
        
        try:
            data = request.data
            username = data.get('username', '').strip()
            password = data.get('password', '').strip()
            email = data.get('email', '').strip()
            first_name = data.get('first_name', '').strip()
            last_name = data.get('last_name', '').strip()
            application_department = data.get('application_department', '').strip()
            application_reason = data.get('application_reason', '').strip()
            
            # 驗證必填欄位
            if not username or not password or not email:
                return Response({
                    'success': False,
                    'error': '用戶名、密碼和 Email 為必填項'
                }, status=http_status.HTTP_400_BAD_REQUEST)
            
            # 🆕 驗證申請資訊
            if not application_department or not application_reason:
                return Response({
                    'success': False,
                    'error': '請填寫申請部門和申請理由'
                }, status=http_status.HTTP_400_BAD_REQUEST)
            
            # 檢查用戶名是否已存在
            if User.objects.filter(username=username).exists():
                return Response({
                    'success': False,
                    'error': '用戶名已存在'
                }, status=http_status.HTTP_400_BAD_REQUEST)
            
            # 檢查 email 是否已存在
            if User.objects.filter(email=email).exists():
                return Response({
                    'success': False,
                    'error': 'Email 已被使用'
                }, status=http_status.HTTP_400_BAD_REQUEST)
            
            # 🆕 創建用戶（預設為未啟用，等待審核）
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_active=False  # ✅ 預設為未啟用
            )
            
            # 🆕 創建 UserProfile 並設置審核狀態
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.account_status = 'pending'  # 待審核
            profile.application_department = application_department
            profile.application_reason = application_reason
            profile.save()
            
            logger.info(f"新用戶註冊申請: {username} ({email}) - 待審核")
            
            return Response({
                'success': True,
                'message': '註冊申請已提交，請等待管理員審核。審核通過後會收到通知。',
                'status': 'pending',
                'data': {
                    'username': username,
                    'email': email
                }
            }, status=http_status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"註冊失敗: {str(e)}")
            return Response({
                'success': False,
                'error': f'註冊失敗: {str(e)}'
            }, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)


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
