"""
Django REST Framework 認證 API 處理器 - DRF Auth Handler

提供完整的 DRF API 認證處理，包含登入、註冊、登出、密碼更改等功能。
這個模組將所有 API 邏輯統一處理，大幅簡化 views.py 中的代碼。

Author: AI Platform Team
Created: 2024-10-07
"""

import json
import logging
from typing import Dict, Any
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from rest_framework.response import Response
from rest_framework import status

from .authentication_service import AuthenticationService
from .user_profile_service import UserProfileService
from .validation_service import ValidationService
from .response_formatter import AuthResponseFormatter
from .login_handler import LoginHandler

logger = logging.getLogger(__name__)


class DRFAuthHandler:
    """
    Django REST Framework 認證處理器
    
    統一處理所有認證相關的 API，包括：
    - 用戶登入 (handle_login_api)
    - 用戶註冊 (handle_register_api)  
    - 用戶登出 (handle_logout_api)
    - 密碼更改 (handle_change_password_api)
    - 用戶資訊 (handle_user_info_api)
    
    特點:
    - 完整的錯誤處理
    - 統一的響應格式
    - 向後兼容性
    - 自動備用機制
    """
    
    @staticmethod
    def handle_login_api(request) -> Response:
        """
        處理完整的 DRF 登入 API
        
        Args:
            request: Django HttpRequest 物件
            
        Returns:
            Response: DRF Response 物件
        """
        try:
            # 解析請求數據
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return Response({
                    'success': False,
                    'message': '無效的 JSON 格式'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            username = data.get('username', '')
            password = data.get('password', '')
            
            # 檢查 AUTH_LIBRARY_AVAILABLE 狀態
            try:
                # 嘗試使用完整的 library 功能
                login_response = LoginHandler.handle_login(request, username, password)
                
                # 將 JsonResponse 轉換為 DRF Response
                response_data = json.loads(login_response.content.decode('utf-8'))
                return Response(response_data, status=login_response.status_code)
                
            except Exception as library_error:
                logger.warning(f"Library 認證失敗，使用備用實現: {str(library_error)}")
                # 使用備用實現
                return DRFAuthHandler._fallback_login(request, username, password)
            
        except Exception as e:
            logger.error(f"Login API error: {str(e)}")
            return Response({
                'success': False,
                'message': '伺服器錯誤'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @staticmethod
    def _fallback_login(request, username: str, password: str) -> Response:
        """備用登入實現"""
        try:
            # 基本驗證
            if not username or not password:
                return Response({
                    'success': False,
                    'message': '用戶名和密碼不能為空'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Django 認證
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                if user.is_active:
                    login(request, user)
                    
                    # 獲取用戶資料
                    try:
                        # 動態導入避免循環依賴
                        from api.models import UserProfile
                        profile = UserProfile.objects.get(user=user)
                        bio = profile.bio
                    except:
                        bio = ''
                    
                    return Response({
                        'success': True,
                        'message': '登入成功',
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
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'success': False,
                        'message': '該帳號已被停用'
                    }, status=status.HTTP_401_UNAUTHORIZED)
            else:
                return Response({
                    'success': False,
                    'message': '用戶名或密碼錯誤'
                }, status=status.HTTP_401_UNAUTHORIZED)
                
        except Exception as e:
            logger.error(f"Fallback login error: {str(e)}")
            return Response({
                'success': False,
                'message': '伺服器錯誤'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @staticmethod
    def handle_register_api(request) -> Response:
        """
        處理完整的 DRF 註冊 API
        
        Args:
            request: Django HttpRequest 物件
            
        Returns:
            Response: DRF Response 物件
        """
        try:
            # 解析請求數據
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return Response({
                    'success': False,
                    'message': '無效的 JSON 格式'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            username = data.get('username', '').strip()
            password = data.get('password', '')
            email = data.get('email', '').strip()
            first_name = data.get('first_name', '').strip()
            last_name = data.get('last_name', '').strip()
            # 🆕 獲取申請資訊
            application_department = data.get('application_department', '').strip()
            application_reason = data.get('application_reason', '').strip()
            
            try:
                # 使用 library 服務
                # 1. 數據驗證
                validation_result, errors = ValidationService.validate_registration_data({
                    'username': username,
                    'password': password,
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name
                })
                
                if not validation_result:
                    return Response({
                        'success': False,
                        'errors': errors
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # 🆕 驗證申請資訊
                if not application_department or not application_reason:
                    return Response({
                        'success': False,
                        'message': '請填寫申請部門和申請理由'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # 2. 檢查重複
                if User.objects.filter(username=username).exists():
                    return Response({
                        'success': False,
                        'message': '用戶名已存在'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                if User.objects.filter(email=email).exists():
                    return Response({
                        'success': False,
                        'message': 'Email 已被註冊'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # 🆕 3. 創建用戶（預設為未啟用，等待審核）
                user = User.objects.create_user(
                    username=username,
                    password=password,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    is_active=False  # ✅ 預設為未啟用
                )
                
                # 🆕 4. 創建用戶檔案並設置審核狀態
                UserProfileService.create_or_update_user_profile(
                    user=user,
                    profile_data={
                        'bio': f'歡迎 {first_name or username} 加入！',
                        'account_status': 'pending',  # ✅ 待審核
                        'application_department': application_department,
                        'application_reason': application_reason
                    }
                )
                
                logger.info(f"New user registered: {username} ({email}) - 待審核")
                
                return Response({
                    'success': True,
                    'message': '註冊申請已提交，請等待管理員審核。審核通過後會收到通知。',
                    'status': 'pending',
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'date_joined': user.date_joined.isoformat()
                    }
                }, status=status.HTTP_201_CREATED)
                
            except Exception as library_error:
                logger.warning(f"Library 註冊失敗，使用備用實現: {str(library_error)}")
                # 使用備用實現
                return DRFAuthHandler._fallback_register(
                    username, password, email, first_name, last_name
                )
                
        except Exception as e:
            logger.error(f"Register API error: {str(e)}")
            return Response({
                'success': False,
                'message': f'註冊失敗: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @staticmethod
    def _fallback_register(username: str, password: str, email: str, 
                          first_name: str, last_name: str) -> Response:
        """備用註冊實現"""
        try:
            # 基本驗證
            if not username:
                return Response({
                    'success': False,
                    'message': '用戶名不能為空'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            if not password:
                return Response({
                    'success': False,
                    'message': '密碼不能為空'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            if not email:
                return Response({
                    'success': False,
                    'message': 'Email 不能為空'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 檢查重複
            if User.objects.filter(username=username).exists():
                return Response({
                    'success': False,
                    'message': '用戶名已存在'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if User.objects.filter(email=email).exists():
                return Response({
                    'success': False,
                    'message': 'Email 已被註冊'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 創建新用戶
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email,
                first_name=first_name,
                last_name=last_name
            )
            
            # 創建用戶檔案
            try:
                from api.models import UserProfile
                UserProfile.objects.create(
                    user=user,
                    bio=f'歡迎 {first_name or username} 加入！'
                )
            except:
                pass  # 如果創建失敗，不影響註冊
            
            logger.info(f"New user registered (fallback): {username} ({email})")
            
            return Response({
                'success': True,
                'message': '註冊成功！請使用新帳號登入',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'date_joined': user.date_joined.isoformat()
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Fallback register error: {str(e)}")
            return Response({
                'success': False,
                'message': f'註冊失敗: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @staticmethod
    def handle_logout_api(request) -> Response:
        """
        處理完整的 DRF 登出 API
        
        Args:
            request: Django HttpRequest 物件
            
        Returns:
            Response: DRF Response 物件
        """
        try:
            try:
                # 使用 library 服務
                logout_result = AuthenticationService.logout_user(
                    request, 
                    force_clear_all_sessions=True
                )
                
                return Response({
                    'success': True,
                    'message': logout_result['message'],
                    'username': logout_result.get('username')
                }, status=status.HTTP_200_OK)
                
            except Exception as library_error:
                logger.warning(f"Library 登出失敗，使用備用實現: {str(library_error)}")
                # 使用備用實現
                return DRFAuthHandler._fallback_logout(request)
                
        except Exception as e:
            logger.error(f"Logout API error: {str(e)}")
            # 即使出錯也強制清除狀態
            try:
                logout(request)
                if hasattr(request, 'session'):
                    request.session.flush()
            except:
                pass
            
            return Response({
                'success': True,
                'message': '已強制清除登入狀態'
            }, status=status.HTTP_200_OK)
    
    @staticmethod
    def _fallback_logout(request) -> Response:
        """備用登出實現"""
        try:
            username = None
            
            # 獲取用戶名
            if hasattr(request, 'user') and request.user.is_authenticated:
                username = request.user.username
            
            # 清除 session
            if hasattr(request, 'session'):
                request.session.flush()
            
            # Django logout
            logout(request)
            
            # 清除相關 session
            if username:
                try:
                    user_sessions = Session.objects.filter(
                        session_data__contains=username
                    )
                    user_sessions.delete()
                except:
                    pass
            
            return Response({
                'success': True,
                'message': f'用戶 {username or "用戶"} 已成功登出並清除所有 session'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Fallback logout error: {str(e)}")
            return Response({
                'success': True,  # 即使出錯也返回成功
                'message': '已強制清除登入狀態'
            }, status=status.HTTP_200_OK)
    
    @staticmethod
    def handle_change_password_api(request) -> Response:
        """
        處理完整的 DRF 密碼更改 API
        
        Args:
            request: Django HttpRequest 物件
            
        Returns:
            Response: DRF Response 物件
        """
        try:
            # 檢查用戶認證
            if not request.user.is_authenticated:
                return Response({
                    'error': '需要登入才能更改密碼'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # 解析請求數據
            data = request.data
            old_password = data.get('old_password', '')
            new_password = data.get('new_password', '')
            
            try:
                # 使用 library 服務
                # 1. 數據驗證
                validation_result, errors = ValidationService.validate_password_change_data({
                    'old_password': old_password,
                    'new_password': new_password
                })
                
                if not validation_result:
                    return Response(errors, status=status.HTTP_400_BAD_REQUEST)
                
                # 2. 更改密碼
                change_result = AuthenticationService.change_user_password(
                    user=request.user,
                    old_password=old_password,
                    new_password=new_password
                )
                
                if change_result['success']:
                    return Response({
                        'success': True,
                        'message': change_result['message']
                    }, status=status.HTTP_200_OK)
                else:
                    error_code = change_result.get('error_code')
                    if error_code == 'INVALID_OLD_PASSWORD':
                        return Response({
                            'old_password': [change_result['message']]
                        }, status=status.HTTP_400_BAD_REQUEST)
                    elif error_code == 'SAME_PASSWORD':
                        return Response({
                            'new_password': [change_result['message']]
                        }, status=status.HTTP_400_BAD_REQUEST)
                    else:
                        return Response({
                            'error': change_result['message']
                        }, status=status.HTTP_400_BAD_REQUEST)
                        
            except Exception as library_error:
                logger.warning(f"Library 密碼更改失敗，使用備用實現: {str(library_error)}")
                # 使用備用實現
                return DRFAuthHandler._fallback_change_password(
                    request.user, old_password, new_password
                )
                
        except Exception as e:
            logger.error(f"Change password API error: {str(e)}")
            return Response({
                'error': '伺服器錯誤，請稍後再試'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @staticmethod
    def _fallback_change_password(user, old_password: str, new_password: str) -> Response:
        """備用密碼更改實現"""
        try:
            # 基本驗證
            if not old_password:
                return Response({
                    'old_password': ['目前密碼不能為空']
                }, status=status.HTTP_400_BAD_REQUEST)
                
            if not new_password:
                return Response({
                    'new_password': ['新密碼不能為空']
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 驗證目前密碼
            if not user.check_password(old_password):
                return Response({
                    'old_password': ['目前密碼不正確']
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 檢查新密碼
            if user.check_password(new_password):
                return Response({
                    'new_password': ['新密碼不能與目前密碼相同']
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 更改密碼
            user.set_password(new_password)
            user.save()
            
            logger.info(f"Password changed successfully (fallback): {user.username}")
            
            return Response({
                'success': True,
                'message': '密碼更改成功'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Fallback change password error: {str(e)}")
            return Response({
                'error': '伺服器錯誤，請稍後再試'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @staticmethod
    def handle_user_info_api(request) -> Response:
        """
        處理完整的 DRF 用戶資訊 API
        
        Args:
            request: Django HttpRequest 物件
            
        Returns:
            Response: DRF Response 物件
        """
        try:
            if request.user.is_authenticated:
                user = request.user
                
                # 獲取用戶資料
                try:
                    from api.models import UserProfile
                    profile = UserProfile.objects.get(user=user)
                    bio = profile.bio
                except:
                    bio = ''

                return Response({
                    'success': True,
                    'authenticated': True,
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
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': True,
                    'authenticated': False,
                    'message': '用戶未登入'
                }, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"User info API error: {str(e)}")
            return Response({
                'success': False,
                'message': '獲取用戶資訊失敗'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# 便利函數 - 向後兼容性
def handle_login_api(request):
    """便利函數：處理登入 API"""
    return DRFAuthHandler.handle_login_api(request)


def handle_register_api(request):
    """便利函數：處理註冊 API"""
    return DRFAuthHandler.handle_register_api(request)


def handle_logout_api(request):
    """便利函數：處理登出 API"""
    return DRFAuthHandler.handle_logout_api(request)


def handle_change_password_api(request):
    """便利函數：處理密碼更改 API"""
    return DRFAuthHandler.handle_change_password_api(request)


def handle_user_info_api(request):
    """便利函數：處理用戶資訊 API"""
    return DRFAuthHandler.handle_user_info_api(request)