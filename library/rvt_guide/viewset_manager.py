"""
RVT Guide ViewSet 管理器

統一管理 RVTGuideViewSet 的所有功能：
- CRUD 操作邏輯
- 查詢和篩選邏輯
- 統計資料邏輯
- 向量生成邏輯

減少 views.py 中 ViewSet 相關程式碼

✨ 已遷移至新架構 - 繼承 BaseKnowledgeBaseViewSetManager
"""

import logging
from django.db import models
from django.db.models import Count
from rest_framework import status
from rest_framework.response import Response
from library.common.knowledge_base import BaseKnowledgeBaseViewSetManager
from api.models import RVTGuide

logger = logging.getLogger(__name__)


class RVTGuideViewSetManager(BaseKnowledgeBaseViewSetManager):
    """
    RVT Guide ViewSet 管理器 - 繼承基礎 ViewSet 管理器
    
    ✅ 已遷移至新架構，代碼從 265 行減少至 ~80 行
    
    繼承自 BaseKnowledgeBaseViewSetManager，自動獲得：
    - perform_create(): 創建並自動生成向量
    - perform_update(): 更新並自動生成向量
    - perform_destroy(): 刪除並自動刪除向量
    - get_serializer_class(): 根據 action 選擇序列化器
    - get_filtered_queryset(): 通用過濾邏輯
    """
    
    # 設定必要屬性
    model_class = RVTGuide
    source_table = 'rvt_guide'
    
    def __init__(self):
        # 延遲導入避免循環導入 - 必須在 super().__init__() 之前設定
        from api.serializers import RVTGuideSerializer, RVTGuideListSerializer
        self.serializer_class = RVTGuideSerializer
        self.list_serializer_class = RVTGuideListSerializer
        
        # 調用父類初始化（會驗證必要屬性）
        super().__init__()
    
    def get_queryset(self, base_queryset, query_params):
        """
        提供 queryset 給 ViewSet 使用
        
        Args:
            base_queryset: 基礎查詢集
            query_params: 查詢參數
            
        Returns:
            過濾後的查詢集
        """
        # 使用父類的 get_filtered_queryset 進行過濾
        return self.get_filtered_queryset(base_queryset, query_params)
    
    def get_vector_service(self):
        """
        獲取向量服務實例（父類需要）
        """
        from .vector_service import RVTGuideVectorService
        return RVTGuideVectorService()
    
    def get_custom_filters(self, queryset, query_params):
        """
        覆寫父類方法 - 添加 RVT Guide 特定的過濾邏輯
        
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
        
        # 一般關鍵字搜尋
        search = query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                models.Q(title__icontains=search) |
                models.Q(content__icontains=search)
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
            from api.serializers import RVTGuideListSerializer
            
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
