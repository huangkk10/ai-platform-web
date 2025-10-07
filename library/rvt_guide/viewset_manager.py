"""
RVT Guide ViewSet 管理器

統一管理 RVTGuideViewSet 的所有功能：
- CRUD 操作邏輯
- 查詢和篩選邏輯
- 統計資料邏輯
- 向量生成邏輯

減少 views.py 中 ViewSet 相關程式碼
"""

import logging
from django.db import models
from django.db.models import Count
from rest_framework import status
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class RVTGuideViewSetManager:
    """RVT Guide ViewSet 管理器 - 統一處理 ViewSet 相關邏輯"""
    
    def __init__(self):
        self.logger = logger
        
    def get_serializer_class(self, action):
        """
        根據操作類型選擇合適的序列化器
        """
        from backend.api.serializers import RVTGuideSerializer, RVTGuideListSerializer
        
        if action == 'list':
            # 列表視圖使用輕量級序列化器以提升性能
            return RVTGuideListSerializer
        return RVTGuideSerializer
    
    def perform_create(self, serializer):
        """
        建立新的 RVT Guide
        """
        instance = serializer.save()
        # 自動生成向量
        self.generate_vector_for_guide(instance, action='create')
        return instance
    
    def perform_update(self, serializer):
        """
        更新現有的 RVT Guide
        """
        instance = serializer.save()
        # 自動生成向量
        self.generate_vector_for_guide(instance, action='update')
        return instance
    
    def generate_vector_for_guide(self, instance, action='create'):
        """
        為 RVT Guide 生成向量資料
        
        Args:
            instance: RVTGuide 實例
            action: 操作類型 ('create' 或 'update')
        """
        try:
            # 使用統一的向量服務
            from .vector_service import RVTGuideVectorService
            vector_service = RVTGuideVectorService()
            
            success = vector_service.generate_and_store_vector(instance, action)
            
            if success:
                self.logger.info(f"✅ 成功為 RVT Guide 生成向量 ({action}): ID {instance.id} - {instance.title}")
            else:
                self.logger.error(f"❌ RVT Guide 向量生成失敗 ({action}): ID {instance.id} - {instance.title}")
                
        except Exception as e:
            self.logger.error(f"❌ RVT Guide 向量生成異常 ({action}): ID {instance.id} - {str(e)}")
    
    def get_filtered_queryset(self, queryset, query_params):
        """
        根據查詢參數過濾資料
        
        Args:
            queryset: 原始查詢集
            query_params: 查詢參數字典
            
        Returns:
            過濾後的查詢集
        """
        # 標題搜尋
        title = query_params.get('title', None)
        if title:
            queryset = queryset.filter(title__icontains=title)
        
        # 子分類篩選
        sub_category = query_params.get('sub_category', None)
        if sub_category:
            queryset = queryset.filter(sub_category=sub_category)
        
        # 狀態篩選
        status_filter = query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # 關鍵字搜尋
        keywords = query_params.get('keywords', None)
        if keywords:
            queryset = queryset.filter(keywords__icontains=keywords)
        
        # 一般關鍵字搜尋
        search = query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                models.Q(title__icontains=search) |
                models.Q(content__icontains=search) |
                models.Q(keywords__icontains=search) |
                models.Q(document_name__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    def get_statistics_data(self, queryset):
        """
        獲取統計資料
        
        Args:
            queryset: 查詢集
            
        Returns:
            Response: 統計資料響應
        """
        try:
            from backend.api.serializers import RVTGuideListSerializer
            
            # 基本統計
            total_guides = queryset.count()
            published_guides = queryset.filter(status='published').count()
            
            # 按子分類統計
            sub_category_stats = queryset.values('sub_category').annotate(count=Count('id'))
            
            # 按狀態統計
            status_stats = queryset.values('status').annotate(count=Count('id'))
            
            # 最新文檔 (前5名)
            recent_guides = queryset.order_by('-updated_at')[:5]
            recent_guides_data = RVTGuideListSerializer(recent_guides, many=True).data
            
            return Response({
                'total_guides': total_guides,
                'published_guides': published_guides,
                'publish_rate': round(published_guides / total_guides * 100, 2) if total_guides > 0 else 0,
                'sub_category_distribution': list(sub_category_stats),
                'status_distribution': list(status_stats),
                'recent_guides': recent_guides_data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            self.logger.error(f"統計資料獲取失敗: {str(e)}")
            return Response({
                'error': f'統計資料獲取失敗: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def handle_bulk_operations(self, queryset, operation, data=None):
        """
        處理批量操作
        
        Args:
            queryset: 查詢集
            operation: 操作類型 ('delete', 'update_status', etc.)
            data: 操作相關數據
            
        Returns:
            Response: 操作結果響應
        """
        try:
            if operation == 'delete':
                count = queryset.count()
                queryset.delete()
                return Response({
                    'success': True,
                    'message': f'成功刪除 {count} 個 RVT Guide',
                    'deleted_count': count
                }, status=status.HTTP_200_OK)
            
            elif operation == 'update_status':
                new_status = data.get('status') if data else None
                if not new_status:
                    return Response({
                        'error': 'Status is required for bulk status update'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                count = queryset.update(status=new_status)
                return Response({
                    'success': True,
                    'message': f'成功更新 {count} 個 RVT Guide 的狀態為 {new_status}',
                    'updated_count': count
                }, status=status.HTTP_200_OK)
            
            else:
                return Response({
                    'error': f'Unsupported bulk operation: {operation}'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            self.logger.error(f"批量操作失敗 ({operation}): {str(e)}")
            return Response({
                'error': f'批量操作失敗: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)