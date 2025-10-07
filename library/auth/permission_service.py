"""
權限管理服務 - Permission Management Service

提供用戶權限檢查、管理和批量更新功能。

Author: AI Platform Team  
Created: 2024-10-08
"""

import logging
from typing import Dict, List, Optional, Tuple
from django.contrib.auth.models import User
from django.http import HttpRequest
from rest_framework import status
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class PermissionService:
    """權限管理服務類"""
    
    @staticmethod
    def is_super_admin(user: User) -> bool:
        """
        檢查用戶是否為超級管理員
        
        Args:
            user: Django User 對象
            
        Returns:
            bool: 是否為超級管理員
        """
        try:
            return (
                user.is_superuser or 
                (hasattr(user, 'userprofile') and user.userprofile.is_super_admin)
            )
        except Exception as e:
            logger.error(f"檢查超級管理員狀態失敗: {str(e)}")
            return False
    
    @staticmethod
    def check_super_admin_permission(user: User) -> Tuple[bool, Optional[Response]]:
        """
        檢查超級管理員權限，如果失敗返回錯誤響應
        
        Args:
            user: Django User 對象
            
        Returns:
            Tuple[bool, Optional[Response]]: (是否有權限, 錯誤響應或None)
        """
        if not PermissionService.is_super_admin(user):
            return False, Response(
                {'error': '權限不足，僅超級管理員可以執行此操作'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return True, None
    
    @staticmethod
    def get_user_profile_queryset(user: User):
        """
        根據用戶權限獲取相應的 UserProfile 查詢集
        
        Args:
            user: Django User 對象
            
        Returns:
            QuerySet: UserProfile 查詢集
        """
        try:
            # 動態導入避免循環引用
            from api.models import UserProfile
            
            # 超級管理員可以看到所有用戶的個人檔案
            if PermissionService.is_super_admin(user):
                return UserProfile.objects.all()
            
            # 普通用戶只能看到自己的個人檔案
            return UserProfile.objects.filter(user=user)
            
        except Exception as e:
            logger.error(f"獲取 UserProfile 查詢集失敗: {str(e)}")
            # 動態導入避免循環引用
            from api.models import UserProfile
            return UserProfile.objects.filter(user=user)  # 備用：只返回自己的
    
    @staticmethod
    def get_user_profile_by_user_id(user_id: int):
        """
        根據 User ID 獲取 UserProfile
        
        Args:
            user_id: User ID
            
        Returns:
            UserProfile 實例或 None
        """
        try:
            # 動態導入避免循環引用
            from api.models import UserProfile
            return UserProfile.objects.get(user_id=user_id)
        except Exception:
            return None
    
    @staticmethod
    def can_modify_user_profile(current_user: User, target_profile) -> Tuple[bool, Optional[str]]:
        """
        檢查是否可以修改目標用戶的權限
        
        Args:
            current_user: 當前執行操作的用戶
            target_profile: 要修改的目標用戶檔案
            
        Returns:
            Tuple[bool, Optional[str]]: (是否可以修改, 錯誤信息或None)
        """
        try:
            # 防止非 Django superuser 修改其他超級管理員的權限
            if (hasattr(target_profile, 'is_super_admin') and 
                target_profile.is_super_admin and 
                not current_user.is_superuser):
                return False, '只有 Django 超級用戶可以修改超級管理員的權限'
            
            return True, None
            
        except Exception as e:
            logger.error(f"檢查修改權限失敗: {str(e)}")
            return False, f'權限檢查失敗: {str(e)}'


class UserPermissionManager:
    """用戶權限管理器"""
    
    @staticmethod
    def list_all_user_permissions(current_user: User) -> Response:
        """
        獲取所有用戶的權限列表
        
        Args:
            current_user: 當前用戶
            
        Returns:
            Response: API 響應
        """
        try:
            # 檢查超級管理員權限
            has_permission, error_response = PermissionService.check_super_admin_permission(current_user)
            if not has_permission:
                return error_response
            
            # 動態導入避免循環引用
            from api.models import UserProfile
            from api.serializers import UserPermissionSerializer
            
            # 獲取所有用戶檔案
            profiles = UserProfile.objects.all().select_related('user').order_by('user__username')
            serializer = UserPermissionSerializer(profiles, many=True)
            
            return Response({
                'success': True,
                'data': serializer.data,
                'count': len(serializer.data)
            })
            
        except Exception as e:
            logger.error(f"獲取用戶權限列表失敗: {str(e)}")
            return Response(
                {'error': f'獲取用戶權限列表失敗: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @staticmethod
    def manage_user_permission(current_user: User, user_id: int, update_data: Dict) -> Response:
        """
        管理指定用戶的權限
        
        Args:
            current_user: 當前用戶
            user_id: 目標用戶ID
            update_data: 更新數據
            
        Returns:
            Response: API 響應
        """
        try:
            # 檢查超級管理員權限
            has_permission, error_response = PermissionService.check_super_admin_permission(current_user)
            if not has_permission:
                return error_response
            
            # 獲取目標用戶檔案
            profile = PermissionService.get_user_profile_by_user_id(user_id)
            if not profile:
                return Response(
                    {'error': '用戶檔案不存在'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # 檢查是否可以修改
            can_modify, error_msg = PermissionService.can_modify_user_profile(current_user, profile)
            if not can_modify:
                return Response(
                    {'error': error_msg}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # 動態導入避免循環引用
            from api.serializers import UserPermissionSerializer
            
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
            logger.error(f"管理用戶權限失敗: {str(e)}")
            return Response(
                {'error': f'管理用戶權限失敗: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @staticmethod
    def bulk_update_permissions(current_user: User, updates: List[Dict]) -> Response:
        """
        批量更新用戶權限
        
        Args:
            current_user: 當前用戶
            updates: 更新數據列表
            
        Returns:
            Response: API 響應
        """
        try:
            # 檢查超級管理員權限
            has_permission, error_response = PermissionService.check_super_admin_permission(current_user)
            if not has_permission:
                return error_response
            
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
                    
                    # 檢查是否可以修改
                    can_modify, error_msg = PermissionService.can_modify_user_profile(current_user, profile)
                    if not can_modify:
                        errors.append({
                            'profile_id': profile_id,
                            'error': error_msg
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
            logger.error(f"批量更新用戶權限失敗: {str(e)}")
            return Response(
                {'error': f'批量更新用戶權限失敗: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @staticmethod
    def get_my_permissions(user: User) -> Response:
        """
        獲取當前用戶的權限資訊
        
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
            logger.error(f"獲取當前用戶權限失敗: {str(e)}")
            return Response(
                {'error': '用戶檔案不存在'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class UserProfileQueryHelper:
    """用戶檔案查詢助手"""
    
    @staticmethod
    def get_my_profile(user: User) -> Response:
        """
        獲取當前用戶的個人檔案
        
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
            logger.error(f"獲取個人檔案失敗: {str(e)}")
            return Response(
                {'error': 'Profile not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )


# 便利函數
def check_super_admin(user: User) -> bool:
    """
    便利函數：檢查用戶是否為超級管理員
    
    Args:
        user: Django User 對象
        
    Returns:
        bool: 是否為超級管理員
    """
    return PermissionService.is_super_admin(user)


def get_user_profile_queryset(user: User):
    """
    便利函數：獲取用戶檔案查詢集
    
    Args:
        user: Django User 對象
        
    Returns:
        QuerySet: UserProfile 查詢集
    """
    return PermissionService.get_user_profile_queryset(user)


def manage_user_permissions(current_user: User, user_id: int, update_data: Dict) -> Response:
    """
    便利函數：管理用戶權限
    
    Args:
        current_user: 當前用戶
        user_id: 目標用戶ID
        update_data: 更新數據
        
    Returns:
        Response: API 響應
    """
    return UserPermissionManager.manage_user_permission(current_user, user_id, update_data)


def bulk_update_user_permissions(current_user: User, updates: List[Dict]) -> Response:
    """
    便利函數：批量更新用戶權限
    
    Args:
        current_user: 當前用戶
        updates: 更新數據列表
        
    Returns:
        Response: API 響應
    """
    return UserPermissionManager.bulk_update_permissions(current_user, updates)