"""
登入處理器 - Login Handler

提供完整的登入流程處理，整合所有認證相關服務。
"""

import logging
from django.http import JsonResponse
from django.contrib.auth.models import User
from .authentication_service import AuthenticationService
from .validation_service import ValidationService
from .user_profile_service import UserProfileService
from .response_formatter import AuthResponseFormatter

logger = logging.getLogger(__name__)


class LoginHandler:
    """
    登入處理器 - 整合所有認證服務提供完整的登入流程
    
    Features:
    - 完整的登入驗證流程
    - 用戶資料封裝
    - 錯誤處理
    - 響應格式化
    """
    
    @staticmethod
    def handle_login(request, username: str, password: str) -> JsonResponse:
        """
        處理完整的用戶登入流程
        
        Args:
            request: Django HttpRequest 物件
            username: 用戶名
            password: 密碼
            
        Returns:
            JsonResponse: 包含登入結果的響應
        """
        try:
            # 1. 使用 ValidationService 進行數據驗證
            validation_result, errors = ValidationService.validate_login_data({
                'username': username,
                'password': password
            })
            
            if not validation_result:
                return AuthResponseFormatter.validation_error_response(errors)
            
            # 2. 使用 AuthenticationService 進行用戶認證
            auth_result = AuthenticationService.authenticate_user(username, password, request)
            
            if auth_result['success']:
                user = auth_result['user']
                
                # 3. 獲取完整的用戶資料
                user_data = LoginHandler._build_user_data(user)
                
                # 4. 構建成功響應
                return JsonResponse({
                    'success': True,
                    'message': '登入成功',
                    'user': user_data
                }, status=200)
            else:
                # 認證失敗，返回錯誤響應
                error_code = auth_result.get('error_code')
                return JsonResponse({
                    'success': False,
                    'message': auth_result['message'],
                    'error_code': error_code
                }, status=401)
            
        except Exception as e:
            logger.error(f"Login handler error: {str(e)}")
            return AuthResponseFormatter.error_response('登入過程發生錯誤', status_code=500)
    
    @staticmethod
    def _build_user_data(user: User) -> dict:
        """
        構建用戶資料字典
        
        Args:
            user: Django User 物件
            
        Returns:
            dict: 用戶資料字典
        """
        try:
            # 安全地獲取用戶檔案資料
            profile_data = UserProfileService.get_user_profile_data(user)
            bio = profile_data.get('bio', '') if profile_data else ''
        except Exception as e:
            logger.warning(f"Failed to get user profile for {user.username}: {str(e)}")
            bio = ''
        
        return {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'bio': bio,
            'date_joined': user.date_joined.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None
        }
    
    @staticmethod
    def handle_class_based_login(request, username: str, password: str) -> JsonResponse:
        """
        處理 Class-Based View 的登入流程
        
        這個方法專門用於 UserLoginView，提供與原有 _login_with_library 相同的功能
        
        Args:
            request: Django HttpRequest 物件
            username: 用戶名
            password: 密碼
            
        Returns:
            JsonResponse: 包含登入結果的響應
        """
        # 使用相同的處理邏輯
        return LoginHandler.handle_login(request, username, password)
    
    @staticmethod
    def handle_fallback_login(request, username: str, password: str) -> JsonResponse:
        """
        🔄 備用登入實現 - 僅在 Library 認證服務不可用時使用
        
        這是一個簡化版本的登入處理，當主要的認證服務無法使用時的備用方案。
        不依賴其他 library 組件，使用 Django 原生認證。
        
        Args:
            request: Django HttpRequest 物件
            username: 用戶名
            password: 密碼
            
        Returns:
            JsonResponse: 包含登入結果的響應
        """
        logger.warning("使用備用登入機制 - Library 認證服務不可用")
        
        # 基本參數驗證
        if not username or not password:
            return JsonResponse({
                'success': False,
                'message': '用戶名和密碼不能為空'
            }, status=400)
        
        try:
            # 使用 Django 原生認證
            from django.contrib.auth import authenticate, login
            user = authenticate(request, username=username, password=password)
            
            if user and user.is_active:
                login(request, user)
                
                # 簡化用戶資料處理 - 不依賴 UserProfileService
                try:
                    from api.models import UserProfile
                    profile = UserProfile.objects.get(user=user)
                    bio = profile.bio
                except:
                    # 如果 UserProfile 不存在或其他錯誤，使用空字符串
                    bio = ''
                
                return JsonResponse({
                    'success': True,
                    'message': '登入成功 (備用模式)',
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'is_staff': user.is_staff,
                        'is_superuser': user.is_superuser,
                        'bio': bio,
                        'date_joined': user.date_joined.isoformat(),
                        'last_login': user.last_login.isoformat() if user.last_login else None
                    }
                }, status=200)
            else:
                error_msg = '該帳號已被停用' if user and not user.is_active else '用戶名或密碼錯誤'
                return JsonResponse({
                    'success': False,
                    'message': error_msg
                }, status=401)
                
        except Exception as e:
            logger.error(f"備用登入過程發生錯誤: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': '登入過程發生錯誤'
            }, status=500)