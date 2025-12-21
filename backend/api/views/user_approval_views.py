"""
用戶審核管理 Views
========================================

用於管理待審核用戶的 API 端點
Created: 2025-12-21
"""

import logging
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.utils import timezone
from api.models import UserProfile

logger = logging.getLogger(__name__)


class PendingUserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    待審核用戶管理 ViewSet
    
    功能：
    - 列出所有待審核用戶
    - 批准用戶註冊
    - 拒絕用戶註冊
    - 停用用戶帳號
    
    權限：僅管理員可訪問
    """
    permission_classes = [permissions.IsAdminUser]
    
    def get_queryset(self):
        """獲取待審核用戶列表"""
        return User.objects.filter(
            userprofile__account_status='pending'
        ).select_related('userprofile').order_by('-date_joined')
    
    def list(self, request):
        """列出所有待審核用戶"""
        users = self.get_queryset()
        
        data = []
        for user in users:
            try:
                profile = user.userprofile
                data.append({
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'date_joined': user.date_joined,
                    'account_status': profile.account_status,
                    'application_department': profile.application_department,
                    'application_reason': profile.application_reason,
                })
            except UserProfile.DoesNotExist:
                continue
        
        return Response({
            'success': True,
            'data': data,
            'count': len(data)
        })
    
    @action(detail=False, methods=['get'])
    def count(self, request):
        """獲取待審核用戶數量"""
        count = self.get_queryset().count()
        return Response({
            'success': True,
            'count': count
        })
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        批准用戶註冊
        
        將用戶狀態從 pending 改為 approved，並啟用帳號
        """
        try:
            user = User.objects.get(pk=pk)
            profile = user.userprofile
            
            if profile.account_status != 'pending':
                return Response({
                    'success': False,
                    'error': f'用戶狀態為 {profile.account_status}，無法批准'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 更新用戶狀態
            user.is_active = True
            user.save()
            
            # 更新審核資訊
            profile.account_status = 'approved'
            profile.reviewed_by = request.user
            profile.reviewed_at = timezone.now()
            profile.save()
            
            logger.info(f"管理員 {request.user.username} 批准了用戶 {user.username} 的註冊申請")
            
            return Response({
                'success': True,
                'message': f'已批准用戶 {user.username} 的註冊申請',
                'data': {
                    'username': user.username,
                    'email': user.email,
                    'account_status': 'approved'
                }
            })
            
        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': '用戶不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"批准用戶失敗: {str(e)}")
            return Response({
                'success': False,
                'error': f'批准失敗: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """
        拒絕用戶註冊
        
        Request Body:
            {
                "reason": "拒絕原因"
            }
        """
        try:
            user = User.objects.get(pk=pk)
            profile = user.userprofile
            reason = request.data.get('reason', '未提供原因').strip()
            
            if profile.account_status != 'pending':
                return Response({
                    'success': False,
                    'error': f'用戶狀態為 {profile.account_status}，無法拒絕'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not reason:
                return Response({
                    'success': False,
                    'error': '請提供拒絕原因'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 更新審核資訊
            profile.account_status = 'rejected'
            profile.reviewed_by = request.user
            profile.reviewed_at = timezone.now()
            profile.rejection_reason = reason
            profile.save()
            
            # 保持用戶為未啟用狀態
            user.is_active = False
            user.save()
            
            logger.info(f"管理員 {request.user.username} 拒絕了用戶 {user.username} 的註冊申請，原因：{reason}")
            
            return Response({
                'success': True,
                'message': f'已拒絕用戶 {user.username} 的註冊申請',
                'data': {
                    'username': user.username,
                    'email': user.email,
                    'account_status': 'rejected',
                    'rejection_reason': reason
                }
            })
            
        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': '用戶不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"拒絕用戶失敗: {str(e)}")
            return Response({
                'success': False,
                'error': f'拒絕失敗: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def suspend(self, request, pk=None):
        """
        停用用戶帳號
        
        Request Body:
            {
                "reason": "停用原因"
            }
        """
        try:
            user = User.objects.get(pk=pk)
            profile = user.userprofile
            reason = request.data.get('reason', '未提供原因').strip()
            
            # SuperUser 不能被停用
            if user.is_superuser:
                return Response({
                    'success': False,
                    'error': '無法停用超級管理員帳號'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 更新狀態
            profile.account_status = 'suspended'
            profile.reviewed_by = request.user
            profile.reviewed_at = timezone.now()
            profile.rejection_reason = reason  # 重用此欄位存儲停用原因
            profile.save()
            
            user.is_active = False
            user.save()
            
            logger.info(f"管理員 {request.user.username} 停用了用戶 {user.username}，原因：{reason}")
            
            return Response({
                'success': True,
                'message': f'已停用用戶 {user.username}',
                'data': {
                    'username': user.username,
                    'account_status': 'suspended'
                }
            })
            
        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': '用戶不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"停用用戶失敗: {str(e)}")
            return Response({
                'success': False,
                'error': f'停用失敗: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AllUsersViewSet(viewsets.ReadOnlyModelViewSet):
    """
    所有用戶管理 ViewSet（包含各種狀態）
    
    用於管理員查看所有用戶及其審核狀態
    權限：僅管理員可訪問
    """
    permission_classes = [permissions.IsAdminUser]
    queryset = User.objects.all().select_related('userprofile').order_by('-date_joined')
    
    def list(self, request):
        """列出所有用戶及其審核狀態"""
        filter_status = request.query_params.get('status', None)
        
        users = self.queryset
        if filter_status:
            users = users.filter(userprofile__account_status=filter_status)
        
        data = []
        for user in users:
            try:
                profile = user.userprofile
                data.append({
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_active': user.is_active,
                    'is_staff': user.is_staff,
                    'is_superuser': user.is_superuser,
                    'date_joined': user.date_joined,
                    'account_status': profile.account_status,
                    'application_department': profile.application_department,
                    'application_reason': profile.application_reason,
                    'reviewed_by': profile.reviewed_by.username if profile.reviewed_by else None,
                    'reviewed_at': profile.reviewed_at,
                    'rejection_reason': profile.rejection_reason,
                })
            except UserProfile.DoesNotExist:
                data.append({
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_active': user.is_active,
                    'is_staff': user.is_staff,
                    'is_superuser': user.is_superuser,
                    'date_joined': user.date_joined,
                    'account_status': 'approved',  # 舊用戶預設已批准
                    'application_department': None,
                    'application_reason': None,
                    'reviewed_by': None,
                    'reviewed_at': None,
                    'rejection_reason': None,
                })
        
        return Response({
            'success': True,
            'data': data,
            'count': len(data)
        })
