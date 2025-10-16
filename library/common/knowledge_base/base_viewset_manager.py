"""
知識庫 ViewSet 管理器基礎類別
=============================

提供所有知識庫 ViewSet 的通用 CRUD 邏輯。
"""

import logging
from abc import ABC
from django.db import models
from django.db.models import Count
from rest_framework import status
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class BaseKnowledgeBaseViewSetManager(ABC):
    """
    知識庫 ViewSet 管理器基礎類別
    
    子類需要設定的屬性：
    - model_class: Django Model 類別
    - serializer_class: 序列化器類別
    - list_serializer_class: 列表序列化器類別
    - source_table: 資料來源表名
    
    使用範例：
    ```python
    class ProtocolGuideViewSetManager(BaseKnowledgeBaseViewSetManager):
        model_class = ProtocolGuide
        serializer_class = ProtocolGuideSerializer
        list_serializer_class = ProtocolGuideListSerializer
        source_table = 'protocol_guide'
    ```
    """
    
    # 子類必須設定這些屬性
    model_class = None
    serializer_class = None
    list_serializer_class = None
    source_table = None
    
    def __init__(self):
        self.logger = logger
        self._validate_attributes()
    
    def _validate_attributes(self):
        """驗證必要屬性是否已設定"""
        if self.model_class is None:
            raise NotImplementedError(f"{self.__class__.__name__} must define 'model_class' attribute")
        if self.serializer_class is None:
            raise NotImplementedError(f"{self.__class__.__name__} must define 'serializer_class' attribute")
        if self.source_table is None:
            raise NotImplementedError(f"{self.__class__.__name__} must define 'source_table' attribute")
    
    def get_serializer_class(self, action):
        """
        根據操作類型選擇合適的序列化器
        """
        if action == 'list' and self.list_serializer_class:
            return self.list_serializer_class
        return self.serializer_class
    
    def perform_create(self, serializer):
        """
        建立新記錄
        
        子類可以覆寫此方法來添加自定義邏輯
        """
        instance = serializer.save()
        
        # 自動生成向量
        self.generate_vector_for_instance(instance, action='create')
        
        return instance
    
    def perform_update(self, serializer):
        """
        更新現有記錄
        
        子類可以覆寫此方法來添加自定義邏輯
        """
        instance = serializer.save()
        
        # 自動生成向量
        self.generate_vector_for_instance(instance, action='update')
        
        return instance
    
    def perform_destroy(self, instance):
        """
        刪除記錄時同時刪除對應的向量資料
        """
        try:
            # 刪除向量
            self.delete_vector_for_instance(instance)
        except Exception as e:
            self.logger.error(f"向量刪除失敗: {str(e)}")
        
        # 刪除主記錄
        instance.delete()
    
    def generate_vector_for_instance(self, instance, action='create'):
        """
        為記錄生成向量資料
        
        子類可以覆寫此方法來使用自定義的向量服務
        """
        try:
            vector_service = self.get_vector_service()
            success = vector_service.generate_and_store_vector(instance, action)
            
            if success:
                self.logger.info(f"✅ 向量生成成功 ({action}): ID {instance.id}")
            else:
                self.logger.error(f"❌ 向量生成失敗 ({action}): ID {instance.id}")
                
        except Exception as e:
            self.logger.error(f"❌ 向量生成異常 ({action}): ID {instance.id} - {str(e)}")
    
    def delete_vector_for_instance(self, instance):
        """
        刪除記錄的向量資料
        """
        try:
            vector_service = self.get_vector_service()
            vector_service.delete_vector(instance)
            self.logger.info(f"✅ 向量刪除成功: ID {instance.id}")
        except Exception as e:
            self.logger.warning(f"⚠️ 向量刪除失敗: ID {instance.id} - {str(e)}")
    
    def get_vector_service(self):
        """
        獲取向量服務實例
        
        子類需要實現此方法，返回對應的向量服務實例
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement 'get_vector_service' method")
    
    def get_filtered_queryset(self, queryset, query_params):
        """
        根據查詢參數過濾資料
        
        子類可以覆寫此方法來添加自定義過濾邏輯
        """
        # 標題搜尋
        title = query_params.get('title', None)
        if title and hasattr(self.model_class, 'title'):
            queryset = queryset.filter(title__icontains=title)
        
        # 一般關鍵字搜尋
        search = query_params.get('search', None)
        if search:
            q_objects = models.Q()
            
            # 動態添加搜索欄位
            if hasattr(self.model_class, 'title'):
                q_objects |= models.Q(title__icontains=search)
            if hasattr(self.model_class, 'content'):
                q_objects |= models.Q(content__icontains=search)
            
            if q_objects:
                queryset = queryset.filter(q_objects)
        
        # 排序
        return queryset.order_by('-created_at' if hasattr(self.model_class, 'created_at') else '-id')
    
    def get_statistics_data(self, queryset):
        """
        獲取統計資料
        
        子類可以覆寫此方法來提供自定義統計
        """
        try:
            # 基本統計
            total_count = queryset.count()
            
            # 狀態統計（如果有 status 欄位）
            status_stats = None
            if hasattr(self.model_class, 'status'):
                status_stats = queryset.values('status').annotate(count=Count('id'))
            
            # 最新記錄
            recent_items = queryset.order_by('-updated_at' if hasattr(self.model_class, 'updated_at') else '-id')[:5]
            recent_data = self.list_serializer_class(recent_items, many=True).data if self.list_serializer_class else []
            
            response_data = {
                'total_count': total_count,
                'recent_items': recent_data
            }
            
            if status_stats:
                response_data['status_distribution'] = list(status_stats)
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            self.logger.error(f"統計資料獲取失敗: {str(e)}")
            return Response({
                'error': f'統計資料獲取失敗: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def handle_bulk_operations(self, queryset, operation, data=None):
        """
        處理批量操作
        """
        try:
            if operation == 'delete':
                count = queryset.count()
                queryset.delete()
                return Response({
                    'success': True,
                    'message': f'成功刪除 {count} 條記錄',
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
                    'message': f'成功更新 {count} 條記錄的狀態',
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
