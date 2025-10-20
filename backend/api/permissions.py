"""
自定義權限類和裝飾器 - 用於控制用戶功能權限
"""

from functools import wraps
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from .models import UserProfile


class HasWebPermission(permissions.BasePermission):
    """
    檢查用戶是否有指定的Web功能權限
    """
    
    def __init__(self, permission_name):
        self.permission_name = permission_name
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
            
        try:
            profile = request.user.userprofile
            return getattr(profile, self.permission_name, False) or profile.is_super_admin or request.user.is_superuser
        except UserProfile.DoesNotExist:
            return False


class HasKnowledgeBasePermission(permissions.BasePermission):
    """
    檢查用戶是否有指定的知識庫功能權限
    """
    
    def __init__(self, permission_name):
        self.permission_name = permission_name
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
            
        try:
            profile = request.user.userprofile
            return getattr(profile, self.permission_name, False) or profile.is_super_admin or request.user.is_superuser
        except UserProfile.DoesNotExist:
            return False


class IsSuperAdmin(permissions.BasePermission):
    """
    檢查用戶是否為超級管理員
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
            
        try:
            profile = request.user.userprofile
            return profile.is_super_admin or request.user.is_superuser
        except UserProfile.DoesNotExist:
            return request.user.is_superuser


def require_web_permission(permission_name):
    """
    裝飾器：要求用戶擁有指定的Web功能權限
    
    使用方式:
    @require_web_permission('web_protocol_rag')
    def my_view(request):
        pass
    """
    def decorator(func):
        @wraps(func)
        @login_required
        def wrapper(request, *args, **kwargs):
            try:
                profile = request.user.userprofile
                has_permission = (
                    getattr(profile, permission_name, False) or 
                    profile.is_super_admin or 
                    request.user.is_superuser
                )
                
                if not has_permission:
                    return JsonResponse({
                        'error': f'權限不足，需要 {permission_name} 權限',
                        'required_permission': permission_name
                    }, status=403)
                
            except UserProfile.DoesNotExist:
                return JsonResponse({
                    'error': '用戶檔案不存在',
                }, status=404)
            
            return func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_kb_permission(permission_name):
    """
    裝飾器：要求用戶擁有指定的知識庫功能權限
    
    使用方式:
    @require_kb_permission('kb_protocol_rag')
    def my_view(request):
        pass
    """
    def decorator(func):
        @wraps(func)
        @login_required
        def wrapper(request, *args, **kwargs):
            try:
                profile = request.user.userprofile
                has_permission = (
                    getattr(profile, permission_name, False) or 
                    profile.is_super_admin or 
                    request.user.is_superuser
                )
                
                if not has_permission:
                    return JsonResponse({
                        'error': f'權限不足，需要 {permission_name} 權限',
                        'required_permission': permission_name
                    }, status=403)
                
            except UserProfile.DoesNotExist:
                return JsonResponse({
                    'error': '用戶檔案不存在',
                }, status=404)
            
            return func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_super_admin(func):
    """
    裝飾器：要求用戶為超級管理員
    
    使用方式:
    @require_super_admin
    def admin_view(request):
        pass
    """
    @wraps(func)
    @login_required
    def wrapper(request, *args, **kwargs):
        try:
            profile = request.user.userprofile
            is_super_admin = profile.is_super_admin or request.user.is_superuser
            
            if not is_super_admin:
                return JsonResponse({
                    'error': '權限不足，僅超級管理員可以訪問'
                }, status=403)
            
        except UserProfile.DoesNotExist:
            if not request.user.is_superuser:
                return JsonResponse({
                    'error': '用戶檔案不存在'
                }, status=404)
        
        return func(request, *args, **kwargs)
    return wrapper


def check_user_permission(user, permission_name):
    """
    檢查用戶是否擁有指定權限的工具函數
    
    Args:
        user: Django User 對象
        permission_name: 權限名稱 (如 'web_protocol_rag')
    
    Returns:
        bool: True if user has permission, False otherwise
    """
    if not user.is_authenticated:
        return False
    
    # Django 超級用戶總是有權限
    if user.is_superuser:
        return True
    
    try:
        profile = user.userprofile
        # 超級管理員總是有權限
        if profile.is_super_admin:
            return True
        # 檢查指定權限
        return getattr(profile, permission_name, False)
    except UserProfile.DoesNotExist:
        return False


def get_user_permissions(user):
    """
    獲取用戶的所有權限
    
    Args:
        user: Django User 對象
    
    Returns:
        dict: 權限字典
    """
    if not user.is_authenticated:
        return {}
    
    try:
        profile = user.userprofile
        return {
            'web_protocol_rag': profile.web_protocol_rag,
            'web_ai_ocr': profile.web_ai_ocr,
            'web_rvt_assistant': profile.web_rvt_assistant,
            'web_protocol_assistant': profile.web_protocol_assistant,
            'kb_protocol_rag': profile.kb_protocol_rag,
            'kb_ai_ocr': profile.kb_ai_ocr,
            'kb_rvt_assistant': profile.kb_rvt_assistant,
            'is_super_admin': profile.is_super_admin,
            'is_django_superuser': user.is_superuser,
        }
    except UserProfile.DoesNotExist:
        return {
            'web_protocol_rag': False,
            'web_ai_ocr': False,
            'web_rvt_assistant': False,
            'web_protocol_assistant': False,
            'kb_protocol_rag': False,
            'kb_ai_ocr': False,
            'kb_rvt_assistant': False,
            'is_super_admin': False,
            'is_django_superuser': user.is_superuser,
        }


# DRF 權限類實例 - 可以直接在 ViewSet 中使用
class WebProtocolRAGPermission(permissions.BasePermission):
    """Web Protocol RAG 權限"""
    def has_permission(self, request, view):
        return check_user_permission(request.user, 'web_protocol_rag')


class WebAIOCRPermission(permissions.BasePermission):
    """Web AI OCR 權限"""
    def has_permission(self, request, view):
        return check_user_permission(request.user, 'web_ai_ocr')


class WebRVTAssistantPermission(permissions.BasePermission):
    """知識庫 RVT Assistant 權限"""
    def has_permission(self, request, view):
        return check_user_permission(request.user, 'web_rvt_assistant')


class WebProtocolAssistantPermission(permissions.BasePermission):
    """Web Protocol Assistant 權限"""
    def has_permission(self, request, view):
        return check_user_permission(request.user, 'web_protocol_assistant')


class KBProtocolRAGPermission(permissions.BasePermission):
    """知識庫 Protocol RAG 權限"""
    def has_permission(self, request, view):
        return check_user_permission(request.user, 'kb_protocol_rag')


class KBAIOCRPermission(permissions.BasePermission):
    """知識庫 AI OCR 權限"""
    def has_permission(self, request, view):
        return check_user_permission(request.user, 'kb_ai_ocr')


class KBRVTAssistantPermission(permissions.BasePermission):
    """知識庫 RVT Assistant 權限"""
    def has_permission(self, request, view):
        return check_user_permission(request.user, 'kb_rvt_assistant')


class SuperAdminPermission(permissions.BasePermission):
    """超級管理員權限"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
            
        try:
            profile = request.user.userprofile
            return profile.is_super_admin
        except UserProfile.DoesNotExist:
            return False