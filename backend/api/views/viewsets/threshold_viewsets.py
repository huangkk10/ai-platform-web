"""
Threshold Settings ViewSet
==========================

提供 Threshold 設定的 CRUD API，只有管理員可以修改設定。
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
import logging

from api.models import SearchThresholdSetting
from api.serializers import SearchThresholdSettingSerializer

logger = logging.getLogger(__name__)


class SearchThresholdViewSet(viewsets.ModelViewSet):
    """
    搜尋 Threshold 設定 ViewSet
    
    功能：
    - GET /api/threshold-settings/ - 列表（所有用戶可讀）
    - GET /api/threshold-settings/{id}/ - 詳情（所有用戶可讀）
    - POST /api/threshold-settings/ - 創建（僅管理員）
    - PUT/PATCH /api/threshold-settings/{id}/ - 更新（僅管理員）
    - DELETE /api/threshold-settings/{id}/ - 刪除（僅管理員）
    - POST /api/threshold-settings/refresh-cache/ - 重新整理快取（僅管理員）
    
    權限：
    - 讀取：所有已認證用戶
    - 修改：僅管理員（is_staff=True）
    """
    
    queryset = SearchThresholdSetting.objects.all().order_by('assistant_type')
    serializer_class = SearchThresholdSettingSerializer
    
    def get_permissions(self):
        """
        動態權限控制
        - 讀取操作：所有已認證用戶
        - 修改操作：僅管理員
        """
        if self.action in ['list', 'retrieve', 'get_cache_info']:
            # 讀取操作：所有已認證用戶
            permission_classes = [permissions.IsAuthenticated]
        else:
            # 修改操作：僅管理員
            permission_classes = [permissions.IsAdminUser]
        
        return [permission() for permission in permission_classes]
    
    def get_serializer_context(self):
        """傳遞 request 到 serializer（用於自動設定 updated_by）"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def list(self, request, *args, **kwargs):
        """
        列出所有 threshold 設定
        
        回應格式：
        [
            {
                "id": 1,
                "assistant_type": "protocol_assistant",
                "assistant_type_display": "Protocol Assistant",
                "master_threshold": "0.75",
                "calculated_thresholds": {
                    "master_threshold": 0.75,
                    "vector_section_threshold": 0.75,
                    "vector_document_threshold": 0.64,
                    "keyword_threshold": 0.38
                },
                ...
            },
            ...
        ]
        """
        logger.info(f"用戶 {request.user.username} 請求 threshold 設定列表")
        return super().list(request, *args, **kwargs)
    
    def create(self, request, *args, **kwargs):
        """創建新的 threshold 設定（僅管理員）"""
        logger.info(f"管理員 {request.user.username} 創建新的 threshold 設定")
        
        # 自動設定 updated_by
        if 'updated_by' not in request.data:
            request.data['updated_by'] = request.user.id
        
        response = super().create(request, *args, **kwargs)
        
        # 創建成功後重新整理快取
        if response.status_code == status.HTTP_201_CREATED:
            self._refresh_cache()
            logger.info(f"✅ Threshold 設定創建成功，快取已重新整理")
        
        return response
    
    def update(self, request, *args, **kwargs):
        """更新 threshold 設定（僅管理員）"""
        instance = self.get_object()
        logger.info(
            f"管理員 {request.user.username} 更新 {instance.assistant_type} 的 threshold 設定"
        )
        
        response = super().update(request, *args, **kwargs)
        
        # 更新成功後重新整理快取
        if response.status_code == status.HTTP_200_OK:
            self._refresh_cache()
            logger.info(f"✅ Threshold 設定更新成功，快取已重新整理")
        
        return response
    
    def destroy(self, request, *args, **kwargs):
        """刪除 threshold 設定（僅管理員）"""
        instance = self.get_object()
        logger.info(
            f"管理員 {request.user.username} 刪除 {instance.assistant_type} 的 threshold 設定"
        )
        
        response = super().destroy(request, *args, **kwargs)
        
        # 刪除成功後重新整理快取
        if response.status_code == status.HTTP_204_NO_CONTENT:
            self._refresh_cache()
            logger.info(f"✅ Threshold 設定刪除成功，快取已重新整理")
        
        return response
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def refresh_cache(self, request):
        """
        手動重新整理 threshold 快取（僅管理員）
        
        POST /api/threshold-settings/refresh-cache/
        
        回應：
        {
            "message": "快取已重新整理",
            "cache_info": {
                "cache_size": 2,
                "cached_assistants": ["protocol_assistant", "rvt_assistant"]
            }
        }
        """
        logger.info(f"管理員 {request.user.username} 手動觸發快取重新整理")
        
        cache_info = self._refresh_cache()
        
        return Response({
            'message': '快取已重新整理',
            'cache_info': cache_info
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def get_cache_info(self, request):
        """
        獲取快取資訊（所有用戶可讀）
        
        GET /api/threshold-settings/get-cache-info/
        
        回應：
        {
            "cache_size": 2,
            "cache_age_seconds": 120,
            "is_valid": true,
            "cached_assistants": ["protocol_assistant", "rvt_assistant"],
            "ttl": 300
        }
        """
        from library.common.threshold_manager import get_threshold_manager
        
        manager = get_threshold_manager()
        cache_info = manager.get_cache_info()
        
        logger.info(f"用戶 {request.user.username} 查詢快取資訊")
        
        return Response(cache_info, status=status.HTTP_200_OK)
    
    def _refresh_cache(self):
        """重新整理 ThresholdManager 快取"""
        from library.common.threshold_manager import get_threshold_manager
        
        manager = get_threshold_manager()
        manager.refresh_cache()
        
        # 返回快取資訊
        return manager.get_cache_info()
