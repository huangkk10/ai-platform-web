"""
Auth Library 備用處理器 - Fallback Handlers

提供當主要的 Auth Library 服務不可用時的備用實現。
這些備用實現確保系統在 library 出現問題時仍能基本運作。

Author: AI Platform Team  
Created: 2024-10-08
"""

import logging
from typing import Dict, Any, Optional
from django.contrib.auth.models import User
from django.db import models
from rest_framework import status
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class UserProfileFallbackHandler:
    """用戶檔案備用處理器"""
    
    @staticmethod
    def get_fallback_queryset(user: User):
        """
        備用查詢集獲取邏輯
        
        Args:
            user: 當前用戶
            
        Returns:
            QuerySet: UserProfile 查詢集
        """
        try:
            # 動態導入避免循環引用
            from api.models import UserProfile
            
            # 超級管理員檢查
            if user.is_superuser or (hasattr(user, 'userprofile') and user.userprofile.is_super_admin):
                return UserProfile.objects.all()
            
            # 普通用戶只能看到自己的
            return UserProfile.objects.filter(user=user)
            
        except Exception as e:
            logger.error(f"備用查詢集獲取失敗: {str(e)}")
            # 最終備用：只返回用戶自己的檔案
            from api.models import UserProfile
            return UserProfile.objects.filter(user=user)
    
    @staticmethod
    def get_fallback_serializer_class(action: str):
        """
        備用序列化器類選擇
        
        Args:
            action: ViewSet 操作名稱
            
        Returns:
            序列化器類
        """
        try:
            # 動態導入避免循環引用
            from api.serializers import UserProfileSerializer, UserPermissionSerializer
            
            if action in ['manage_permissions', 'bulk_update_permissions']:
                return UserPermissionSerializer
            return UserProfileSerializer
            
        except ImportError as e:
            logger.error(f"序列化器導入失敗: {str(e)}")
            return None
    
    @staticmethod
    def check_super_admin_permission_fallback(user: User) -> tuple[bool, Optional[Response]]:
        """
        備用超級管理員權限檢查
        
        Args:
            user: 當前用戶
            
        Returns:
            tuple[bool, Optional[Response]]: (是否有權限, 錯誤響應或None)
        """
        try:
            is_super = user.is_superuser or (hasattr(user, 'userprofile') and user.userprofile.is_super_admin)
            
            if not is_super:
                return False, Response(
                    {'error': '權限不足，僅超級管理員可以執行此操作'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            return True, None
            
        except Exception as e:
            logger.error(f"備用權限檢查失敗: {str(e)}")
            return False, Response(
                {'error': f'權限檢查失敗: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @staticmethod
    def handle_get_my_profile_fallback(user: User) -> Response:
        """
        備用獲取個人檔案處理
        
        Args:
            user: 當前用戶
            
        Returns:
            Response: API 響應
        """
        try:
            # 動態導入避免循環引用
            from api.models import UserProfile
            from api.serializers import UserProfileSerializer
            
            profile = UserProfile.objects.get(user=user)
            serializer = UserProfileSerializer(profile)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"備用獲取個人檔案失敗: {str(e)}")
            return Response(
                {'error': 'Profile not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @staticmethod
    def handle_list_permissions_fallback(user: User) -> Response:
        """
        備用列出用戶權限處理
        
        Args:
            user: 當前用戶
            
        Returns:
            Response: API 響應
        """
        try:
            # 檢查權限
            has_permission, error_response = UserProfileFallbackHandler.check_super_admin_permission_fallback(user)
            if not has_permission:
                return error_response
            
            # 動態導入避免循環引用
            from api.models import UserProfile
            from api.serializers import UserPermissionSerializer
            
            profiles = UserProfile.objects.all().select_related('user').order_by('user__username')
            serializer = UserPermissionSerializer(profiles, many=True)
            
            return Response({
                'success': True,
                'data': serializer.data,
                'count': len(serializer.data)
            })
            
        except Exception as e:
            logger.error(f"備用列出權限失敗: {str(e)}")
            return Response(
                {'error': f'獲取用戶權限列表失敗: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @staticmethod
    def handle_manage_permissions_fallback(user: User, target_user_id: int, update_data: Dict) -> Response:
        """
        備用管理用戶權限處理
        
        Args:
            user: 當前用戶
            target_user_id: 目標用戶ID
            update_data: 更新數據
            
        Returns:
            Response: API 響應
        """
        try:
            # 檢查權限
            has_permission, error_response = UserProfileFallbackHandler.check_super_admin_permission_fallback(user)
            if not has_permission:
                return error_response
            
            # 動態導入避免循環引用
            from api.models import UserProfile
            from api.serializers import UserPermissionSerializer
            
            # 獲取目標用戶檔案
            try:
                profile = UserProfile.objects.get(user_id=target_user_id)
            except UserProfile.DoesNotExist:
                return Response(
                    {'error': '用戶檔案不存在'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # 檢查是否可以修改超級管理員
            if (hasattr(profile, 'is_super_admin') and 
                profile.is_super_admin and 
                not user.is_superuser):
                return Response(
                    {'error': '只有 Django 超級用戶可以修改超級管理員的權限'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # 執行更新
            serializer = UserPermissionSerializer(profile, data=update_data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'success': True,
                    'message': f'用戶 {profile.user.username} 的權限已更新',
                    'data': serializer.data
                })
            else:
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"備用管理權限失敗: {str(e)}")
            return Response(
                {'error': f'管理用戶權限失敗: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @staticmethod
    def handle_bulk_permissions_fallback(user: User, request_data: Dict) -> Response:
        """
        備用批量更新用戶權限處理
        
        Args:
            user: 當前用戶
            request_data: 請求數據
            
        Returns:
            Response: API 響應
        """
        try:
            # 檢查權限
            has_permission, error_response = UserProfileFallbackHandler.check_super_admin_permission_fallback(user)
            if not has_permission:
                return error_response
            
            updates = request_data.get('updates', [])
            if not updates:
                return Response(
                    {'error': '請提供要更新的用戶權限資料'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 動態導入避免循環引用
            from api.models import UserProfile
            from api.serializers import UserPermissionSerializer
            
            updated_count = 0
            errors = []
            
            for update in updates:
                profile_id = update.get('profile_id')
                if not profile_id:
                    errors.append({'error': '缺少 profile_id'})
                    continue
                    
                try:
                    profile = UserProfile.objects.get(pk=profile_id)
                    
                    # 檢查超級管理員權限
                    if (hasattr(profile, 'is_super_admin') and 
                        profile.is_super_admin and 
                        not user.is_superuser):
                        errors.append({
                            'profile_id': profile_id,
                            'error': '只有 Django 超級用戶可以修改超級管理員的權限'
                        })
                        continue
                    
                    # 執行更新
                    serializer = UserPermissionSerializer(profile, data=update, partial=True)
                    if serializer.is_valid():
                        serializer.save()
                        updated_count += 1
                    else:
                        errors.append({
                            'profile_id': profile_id,
                            'errors': serializer.errors
                        })
                        
                except UserProfile.DoesNotExist:
                    errors.append({
                        'profile_id': profile_id,
                        'error': '用戶檔案不存在'
                    })
                except Exception as e:
                    errors.append({
                        'profile_id': profile_id,
                        'error': f'處理失敗: {str(e)}'
                    })
            
            return Response({
                'success': True,
                'message': f'已成功更新 {updated_count} 個用戶的權限',
                'updated_count': updated_count,
                'errors': errors
            })
            
        except Exception as e:
            logger.error(f"備用批量更新權限失敗: {str(e)}")
            return Response(
                {'error': f'批量更新用戶權限失敗: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @staticmethod
    def handle_get_my_permissions_fallback(user: User) -> Response:
        """
        備用獲取我的權限處理
        
        Args:
            user: 當前用戶
            
        Returns:
            Response: API 響應
        """
        try:
            # 動態導入避免循環引用
            from api.models import UserProfile
            from api.serializers import UserPermissionSerializer
            
            profile = UserProfile.objects.get(user=user)
            serializer = UserPermissionSerializer(profile)
            return Response({
                'success': True,
                'data': serializer.data
            })
            
        except Exception as e:
            logger.error(f"備用獲取我的權限失敗: {str(e)}")
            return Response(
                {'error': '用戶檔案不存在'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class UserProfileViewSetFallbackManager:
    """UserProfile ViewSet 備用管理器"""
    
    def __init__(self):
        """初始化備用管理器"""
        self.handler = UserProfileFallbackHandler()
    
    def get_queryset_fallback(self, user: User):
        """獲取備用查詢集"""
        return self.handler.get_fallback_queryset(user)
    
    def get_serializer_class_fallback(self, action: str):
        """獲取備用序列化器類"""
        return self.handler.get_fallback_serializer_class(action)
    
    def handle_action_fallback(self, action: str, user: User, **kwargs) -> Response:
        """
        統一處理 ViewSet 操作的備用實現
        
        Args:
            action: 操作名稱
            user: 當前用戶
            **kwargs: 操作參數
            
        Returns:
            Response: API 響應
        """
        try:
            if action == 'get_my_profile':
                return self.handler.handle_get_my_profile_fallback(user)
            
            elif action == 'list_permissions':
                return self.handler.handle_list_permissions_fallback(user)
            
            elif action == 'manage_permissions':
                target_user_id = kwargs.get('target_user_id')
                update_data = kwargs.get('update_data', {})
                return self.handler.handle_manage_permissions_fallback(user, target_user_id, update_data)
            
            elif action == 'bulk_permissions':
                request_data = kwargs.get('request_data', {})
                return self.handler.handle_bulk_permissions_fallback(user, request_data)
            
            elif action == 'get_my_permissions':
                return self.handler.handle_get_my_permissions_fallback(user)
            
            else:
                logger.error(f"不支援的備用操作: {action}")
                return Response(
                    {'error': f'不支援的操作: {action}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.error(f"備用操作處理失敗 - 操作: {action}, 錯誤: {str(e)}")
            return Response(
                {'error': f'操作失敗: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# 便利函數
def create_user_profile_fallback_manager() -> UserProfileViewSetFallbackManager:
    """
    創建用戶檔案備用管理器
    
    Returns:
        UserProfileViewSetFallbackManager: 備用管理器實例
    """
    return UserProfileViewSetFallbackManager()


def handle_user_profile_fallback(action: str, user: User, **kwargs) -> Response:
    """
    統一處理用戶檔案備用操作
    
    Args:
        action: 操作名稱
        user: 當前用戶
        **kwargs: 操作參數
        
    Returns:
        Response: API 響應
    """
    manager = create_user_profile_fallback_manager()
    return manager.handle_action_fallback(action, user, **kwargs)


def get_user_profile_queryset_fallback(user: User):
    """
    便利函數：獲取用戶檔案備用查詢集
    
    Args:
        user: Django User 對象
        
    Returns:
        QuerySet: UserProfile 查詢集
    """
    return UserProfileFallbackHandler.get_fallback_queryset(user)


def get_user_profile_serializer_fallback(action: str):
    """
    便利函數：獲取用戶檔案備用序列化器
    
    Args:
        action: ViewSet 操作名稱
        
    Returns:
        序列化器類
    """
    return UserProfileFallbackHandler.get_fallback_serializer_class(action)