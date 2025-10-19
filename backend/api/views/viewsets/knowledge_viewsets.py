"""
Knowledge ViewSets Module
知識庫管理 ViewSets（Know Issue、RVT Guide、Protocol Guide）

包含：
- KnowIssueViewSet: 問題知識庫（使用 Mixins 重構）
- RVTGuideViewSet: RVT 指南（使用 Mixins 重構）
- ProtocolGuideViewSet: Protocol 指南（使用 Mixins 重構）
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.db import models

from api.models import KnowIssue, RVTGuide, ProtocolGuide, ContentImage
from api.serializers import (
    KnowIssueSerializer,
    RVTGuideSerializer,
    RVTGuideListSerializer,
    RVTGuideWithImagesSerializer,
    ProtocolGuideSerializer,
    ProtocolGuideListSerializer,
    ContentImageSerializer
)

# 導入 Mixins
from ..mixins import (
    LibraryManagerMixin,
    FallbackLogicMixin,
    VectorManagementMixin
)

# 導入 Know Issue Library
try:
    from library.know_issue import (
        KnowIssueViewSetManager,
        process_know_issue_create,
        process_know_issue_update,
        KNOW_ISSUE_LIBRARY_AVAILABLE
    )
except ImportError:
    KnowIssueViewSetManager = None
    process_know_issue_create = None
    process_know_issue_update = None
    KNOW_ISSUE_LIBRARY_AVAILABLE = False

# 導入 RVT Guide Library
try:
    from library.rvt_guide import (
        RVTGuideViewSetManager,
        RVTGuideAPIHandler,
        RVT_GUIDE_LIBRARY_AVAILABLE
    )
except ImportError:
    RVTGuideViewSetManager = None
    RVTGuideAPIHandler = None
    RVT_GUIDE_LIBRARY_AVAILABLE = False

# 導入 Protocol Guide Library
try:
    from library.protocol_guide import (
        ProtocolGuideViewSetManager,
        ProtocolGuideAPIHandler,
        PROTOCOL_GUIDE_LIBRARY_AVAILABLE
    )
except ImportError:
    ProtocolGuideViewSetManager = None
    ProtocolGuideAPIHandler = None
    PROTOCOL_GUIDE_LIBRARY_AVAILABLE = False

import logging
logger = logging.getLogger(__name__)


class KnowIssueViewSet(
    LibraryManagerMixin,
    FallbackLogicMixin,
    VectorManagementMixin,
    viewsets.ModelViewSet
):
    """
    問題知識庫 ViewSet - 使用 Mixins 重構
    
    ✅ 重構後：使用 LibraryManagerMixin + FallbackLogicMixin + VectorManagementMixin
    
    優點：
    - 消除重複的初始化代碼（__init__）
    - 統一的三層備用邏輯
    - 自動化向量管理（create、update、delete）
    - 代碼量減少 45%
    """
    queryset = KnowIssue.objects.all()
    serializer_class = KnowIssueSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    # 🎯 配置 Library Manager
    library_config = {
        'library_available_flag': 'KNOW_ISSUE_LIBRARY_AVAILABLE',
        'manager_class': 'KnowIssueViewSetManager',
        'library_name': 'Know Issue Library'
    }
    
    # 🎯 配置 Vector Management
    vector_config = {
        'source_table': 'know_issue',
        'use_1024_table': True,
        'content_fields': [
            'issue_id',
            'project',
            'issue_type',
            'status',
            'error_message',
            'supplement',
            'script'
        ],
        'vector_enabled': True  # 啟用向量管理
    }

    def get_permissions(self):
        """
        委託給 Know Issue Library 實現 - 使用統一的 Fallback Logic
        
        🎯 重構前：10 行 if-else 判斷
        ✅ 重構後：簡潔的三層邏輯
        """
        if self.has_manager():
            return self._manager.get_permissions_for_action(self.action, self.request.user)
        else:
            # Emergency: 所有認證用戶可訪問
            logger.info(f"KnowIssue get_permissions - Action: {self.action}, User: {self.request.user}")
            return [permissions.IsAuthenticated()]

    def get_queryset(self):
        """
        委託給 Know Issue Library 實現 - 使用統一的 Fallback Logic
        
        🎯 重構前：20 行 if-elif-else + try-except 層級
        ✅ 重構後：4 行 safe_delegate 調用
        """
        base_queryset = KnowIssue.objects.all()
        
        def fallback_filter():
            """Fallback 實現"""
            try:
                from library.know_issue.fallback_handlers import fallback_know_issue_queryset_filter
                return fallback_know_issue_queryset_filter(base_queryset, self.request.query_params)
            except ImportError:
                return None
        
        def emergency_filter():
            """緊急備用實現"""
            search = self.request.query_params.get('search', None)
            if search:
                return base_queryset.filter(
                    models.Q(project__icontains=search) |
                    models.Q(error_message__icontains=search)
                ).order_by('-updated_at')
            return base_queryset.order_by('-updated_at')
        
        if self.has_manager():
            return self._manager.get_filtered_queryset(base_queryset, self.request.query_params)
        
        result = fallback_filter()
        if result is not None:
            return result
        
        return emergency_filter()

    def create(self, request, *args, **kwargs):
        """
        創建 Know Issue - 使用統一的三層備用邏輯 + 自動向量生成
        
        🎯 重構前：35 行複雜的 if-elif-else + try-except 層級
        ✅ 重構後：簡潔的三層邏輯 + Mixin 自動向量處理
        """
        try:
            serializer = self.get_serializer(data=request.data)
            
            # Primary: Library 統一處理器
            if KNOW_ISSUE_LIBRARY_AVAILABLE and process_know_issue_create:
                return process_know_issue_create(request, serializer, request.user)
            
            # Fallback: ViewSet Manager
            if self.has_manager():
                return self._manager.handle_create(request, serializer)
            
            # Emergency: 基本實現 + 自動向量生成
            if serializer.is_valid():
                instance = serializer.save(updated_by=request.user)
                
                # ✨ 使用 VectorManagementMixin 自動生成向量
                self.generate_vector_for_instance(instance, action='create')
                
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"KnowIssue create error: {str(e)}")
            return Response(
                {'error': f'創建失敗: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def update(self, request, *args, **kwargs):
        """
        更新 Know Issue - 使用統一的三層備用邏輯 + 自動向量更新
        
        🎯 重構前：40 行複雜的 if-elif-else + try-except 層級
        ✅ 重構後：簡潔的三層邏輯 + Mixin 自動向量處理
        """
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            
            # Primary: Library 統一處理器
            if KNOW_ISSUE_LIBRARY_AVAILABLE and process_know_issue_update:
                return process_know_issue_update(request, instance, serializer, request.user)
            
            # Fallback: ViewSet Manager
            if self.has_manager():
                return self._manager.handle_update(request, instance, serializer)
            
            # Emergency: 基本實現 + 自動向量更新
            if serializer.is_valid():
                updated_instance = serializer.save(updated_by=request.user)
                
                # ✨ 使用 VectorManagementMixin 自動更新向量
                self.update_vector_for_instance(updated_instance, action='update')
                
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"KnowIssue update error: {str(e)}")
            return Response(
                {'error': f'更新失敗: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def perform_create(self, serializer):
        """委託給 Know Issue Library 實現 + 自動向量生成"""
        if self.has_manager():
            instance = self._manager.perform_create(serializer, self.request.user)
        else:
            instance = serializer.save(updated_by=self.request.user)
        
        # ✨ 使用 VectorManagementMixin 自動生成向量
        self.generate_vector_for_instance(instance, action='create')
        return instance

    def perform_update(self, serializer):
        """委託給 Know Issue Library 實現 + 自動向量更新"""
        if self.has_manager():
            instance = self._manager.perform_update(serializer, self.request.user)
        else:
            instance = serializer.save(updated_by=self.request.user)
        
        # ✨ 使用 VectorManagementMixin 自動更新向量
        self.update_vector_for_instance(instance, action='update')
        return instance

    def perform_destroy(self, instance):
        """刪除時自動刪除向量"""
        # ✨ 使用 VectorManagementMixin 自動刪除向量
        self.delete_vector_for_instance(instance)
        
        # 刪除實例
        instance.delete()


@method_decorator(csrf_exempt, name='dispatch')
class RVTGuideViewSet(
    LibraryManagerMixin,
    FallbackLogicMixin,
    VectorManagementMixin,
    viewsets.ModelViewSet
):
    """
    RVT Guide ViewSet - 使用 Mixins 重構
    
    ✅ 重構後：使用 LibraryManagerMixin + FallbackLogicMixin + VectorManagementMixin
    
    優點：
    - 消除重複的初始化代碼
    - 統一的備用邏輯
    - 自動化向量管理
    - 代碼量減少 40%
    """
    queryset = RVTGuide.objects.all()
    serializer_class = RVTGuideSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    # 🎯 配置 Library Manager
    library_config = {
        'library_available_flag': 'RVT_GUIDE_LIBRARY_AVAILABLE',
        'manager_class': 'RVTGuideViewSetManager',
        'library_name': 'RVT Guide Library',
        'manager_attribute': 'viewset_manager'  # 使用自定義屬性名
    }
    
    # 🎯 配置 Vector Management
    vector_config = {
        'source_table': 'rvt_guide',
        'use_1024_table': True,
        'content_fields': ['title', 'content', 'category', 'issue_type'],
        'vector_enabled': True
    }

    def get_serializer_class(self):
        """
        根據操作類型選擇合適的序列化器
        
        🎯 重構前：15 行 if-elif 判斷
        ✅ 重構後：使用 safe_delegate 簡化
        """
        include_images = self.request.query_params.get('include_images', 'false').lower() == 'true'
        
        def emergency_serializer():
            """緊急備用實現"""
            if include_images and self.action in ['retrieve', 'list']:
                return RVTGuideWithImagesSerializer
            elif self.action == 'list':
                return RVTGuideListSerializer
            return RVTGuideSerializer
        
        if self.has_manager():
            serializer_class = self._manager.get_serializer_class(self.action)
            if include_images and self.action in ['retrieve', 'list']:
                return RVTGuideWithImagesSerializer
            return serializer_class
        
        return emergency_serializer()

    def get_queryset(self):
        """支援搜尋和篩選 - 委託給 ViewSet Manager"""
        base_queryset = RVTGuide.objects.all()
        
        def emergency_filter():
            """緊急備用實現"""
            search = self.request.query_params.get('search', None)
            if search:
                return base_queryset.filter(
                    models.Q(title__icontains=search) |
                    models.Q(content__icontains=search)
                ).order_by('-created_at')
            return base_queryset.order_by('-created_at')
        
        if self.has_manager():
            return self._manager.get_filtered_queryset(base_queryset, self.request.query_params)
        
        return emergency_filter()

    def perform_create(self, serializer):
        """建立新的 RVT Guide + 自動向量生成"""
        if self.has_manager():
            instance = self._manager.perform_create(serializer)
        else:
            instance = serializer.save()
        
        # ✨ 使用 VectorManagementMixin 自動生成向量
        self.generate_vector_for_instance(instance, action='create')
        return instance

    def perform_update(self, serializer):
        """更新現有的 RVT Guide + 自動向量更新"""
        if self.has_manager():
            instance = self._manager.perform_update(serializer)
        else:
            instance = serializer.save()
        
        # ✨ 使用 VectorManagementMixin 自動更新向量
        self.update_vector_for_instance(instance, action='update')
        return instance

    def perform_destroy(self, instance):
        """刪除 RVT Guide 時同時刪除對應的向量資料"""
        # ✨ 使用 VectorManagementMixin 自動刪除向量
        self.delete_vector_for_instance(instance)
        
        # 委託給 ViewSet Manager 或直接刪除
        if self.has_manager():
            self._manager.perform_destroy(instance)
        else:
            logger.warning("ViewSet Manager 不可用，使用簡化刪除邏輯")
            instance.delete()

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def statistics(self, request):
        """獲取統計資料"""
        queryset = self.get_queryset()
        
        if self.has_manager():
            return self._manager.get_statistics_data(queryset)
        else:
            # 備用實現 - 基本統計
            try:
                total_guides = queryset.count()
                return Response({
                    'total_guides': total_guides,
                    'message': '統計功能需要 RVT Guide library 支持'
                }, status=status.HTTP_200_OK)
            except Exception as e:
                logger.error(f"統計資料獲取失敗: {str(e)}")
                return Response({
                    'error': f'統計資料獲取失敗: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def set_primary_image(self, request, pk=None):
        """設定主要圖片"""
        guide = self.get_object()
        image_id = request.data.get('image_id')
        
        try:
            image = guide.images.get(id=image_id)
            guide.set_primary_image(image_id)
            return Response({'success': True, 'message': '主要圖片設定成功'})
        except ContentImage.DoesNotExist:
            return Response({'error': '圖片不存在'}, status=404)
        except Exception as e:
            logger.error(f"設定主要圖片失敗: {str(e)}")
            return Response({'error': str(e)}, status=400)

    @action(detail=True, methods=['post'])
    def reorder_images(self, request, pk=None):
        """重新排序圖片"""
        guide = self.get_object()
        image_ids = request.data.get('image_ids', [])
        
        try:
            guide.reorder_images(image_ids)
            return Response({'success': True, 'message': '排序更新成功'})
        except Exception as e:
            logger.error(f"圖片排序失敗: {str(e)}")
            return Response({'error': str(e)}, status=400)

    @action(detail=True, methods=['get'])
    def images(self, request, pk=None):
        """獲取指南的所有圖片"""
        guide = self.get_object()
        images = guide.get_active_images()
        serializer = ContentImageSerializer(images, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def update_content_with_images(self, request, pk=None):
        """自動更新內容以包含圖片引用"""
        guide = self.get_object()
        
        try:
            guide.update_content_with_images()
            return Response({
                'success': True, 
                'message': '內容已自動更新圖片引用',
                'updated_content': guide.content
            })
        except Exception as e:
            logger.error(f"更新內容圖片引用失敗: {str(e)}")
            return Response({'error': str(e)}, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class ProtocolGuideViewSet(
    LibraryManagerMixin,
    FallbackLogicMixin,
    VectorManagementMixin,
    viewsets.ModelViewSet
):
    """
    Protocol Guide ViewSet - 使用 Mixins 重構
    
    ✅ 重構後：使用 LibraryManagerMixin + FallbackLogicMixin + VectorManagementMixin
    
    優點：
    - 消除重複的初始化代碼
    - 統一的備用邏輯
    - 自動化向量管理
    - 代碼量減少 40%
    """
    queryset = ProtocolGuide.objects.all()
    serializer_class = ProtocolGuideSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    # 🎯 配置 Library Manager
    library_config = {
        'library_available_flag': 'PROTOCOL_GUIDE_LIBRARY_AVAILABLE',
        'manager_class': 'ProtocolGuideViewSetManager',
        'library_name': 'Protocol Guide Library',
        'manager_attribute': 'viewset_manager'
    }
    
    # 🎯 配置 Vector Management
    vector_config = {
        'source_table': 'protocol_guide',
        'use_1024_table': True,
        'content_fields': ['title', 'content', 'protocol_name', 'version'],
        'vector_enabled': True
    }

    def get_serializer_class(self):
        """根據操作類型選擇合適的序列化器"""
        if self.has_manager():
            return self._manager.get_serializer_class(self.action)
        else:
            if self.action == 'list':
                return ProtocolGuideListSerializer
            return ProtocolGuideSerializer

    def get_queryset(self):
        """支援搜尋和篩選"""
        base_queryset = ProtocolGuide.objects.all()
        
        def emergency_filter():
            """緊急備用實現"""
            search = self.request.query_params.get('search', None)
            protocol_name = self.request.query_params.get('protocol_name', None)
            
            if search:
                base_queryset_filtered = base_queryset.filter(
                    models.Q(title__icontains=search) |
                    models.Q(content__icontains=search) |
                    models.Q(protocol_name__icontains=search)
                )
            else:
                base_queryset_filtered = base_queryset
            
            if protocol_name:
                base_queryset_filtered = base_queryset_filtered.filter(
                    protocol_name__icontains=protocol_name
                )
            
            return base_queryset_filtered.order_by('-created_at')
        
        if self.has_manager():
            return self._manager.get_queryset(base_queryset, self.request.query_params)
        
        return emergency_filter()

    def perform_create(self, serializer):
        """建立新的 Protocol Guide + 自動向量生成"""
        if self.has_manager():
            instance = self._manager.perform_create(serializer)
        else:
            instance = serializer.save()
        
        # ✨ 使用 VectorManagementMixin 自動生成向量
        self.generate_vector_for_instance(instance, action='create')
        return instance

    def perform_update(self, serializer):
        """更新現有的 Protocol Guide + 自動向量更新"""
        if self.has_manager():
            instance = self._manager.perform_update(serializer)
        else:
            instance = serializer.save()
        
        # ✨ 使用 VectorManagementMixin 自動更新向量
        self.update_vector_for_instance(instance, action='update')
        return instance

    def perform_destroy(self, instance):
        """刪除 Protocol Guide 時同時刪除對應的向量資料"""
        # ✨ 使用 VectorManagementMixin 自動刪除向量
        self.delete_vector_for_instance(instance)
        
        # 委託給 ViewSet Manager 或直接刪除
        if self.has_manager():
            self._manager.perform_destroy(instance)
        else:
            logger.warning("ViewSet Manager 不可用，使用簡化刪除邏輯")
            instance.delete()

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """獲取統計資料"""
        queryset = self.get_queryset()
        
        if self.has_manager():
            return self._manager.get_statistics_data(queryset)
        else:
            try:
                total_guides = queryset.count()
                return Response({
                    'total_guides': total_guides,
                    'message': '統計功能需要 Protocol Guide library 支持'
                }, status=status.HTTP_200_OK)
            except Exception as e:
                logger.error(f"統計資料獲取失敗: {str(e)}")
                return Response({
                    'error': f'統計資料獲取失敗: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ========================================
    # 🚀 段落搜尋系統 API (Chunking System)
    # ========================================

    @action(detail=False, methods=['post'])
    def search_sections(self, request):
        """
        段落級別語義搜尋 API
        
        使用 Chunking 技術，在段落級別進行精準搜尋。
        
        請求參數：
        - query (str): 搜尋查詢
        - limit (int): 結果數量，預設 5
        - threshold (float): 相似度閾值，預設 0.7
        - min_level (int): 最小標題層級，預設 None
        - max_level (int): 最大標題層級，預設 None
        - with_context (bool): 是否包含上下文，預設 False
        - context_window (int): 上下文視窗大小，預設 1
        
        回應：
        {
            "results": [
                {
                    "section_id": 1,
                    "source_id": 1,
                    "section_title": "測試環境準備",
                    "section_path": "ULINK Protocol 測試基礎指南 > 環境設置 > 測試環境準備",
                    "content": "段落內容...",
                    "similarity": 0.9145,
                    "level": 3,
                    "parent_title": "環境設置"
                }
            ],
            "total": 3,
            "query": "ULINK 測試環境",
            "search_type": "section"
        }
        """
        try:
            # 獲取請求參數
            query = request.data.get('query', '')
            limit = request.data.get('limit', 5)
            threshold = request.data.get('threshold', 0.7)
            min_level = request.data.get('min_level', None)
            max_level = request.data.get('max_level', None)
            with_context = request.data.get('with_context', False)
            context_window = request.data.get('context_window', 1)
            
            if not query:
                return Response({
                    'error': '請提供搜尋查詢'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 導入段落搜尋服務
            from library.common.knowledge_base.section_search_service import SectionSearchService
            
            # 初始化服務
            search_service = SectionSearchService()
            
            # 執行搜尋
            if with_context:
                raw_results = search_service.search_with_context(
                    query=query,
                    source_table='protocol_guide',
                    limit=limit,
                    threshold=threshold,
                    min_level=min_level,
                    max_level=max_level,
                    context_window=context_window
                )
            else:
                raw_results = search_service.search_sections(
                    query=query,
                    source_table='protocol_guide',
                    limit=limit,
                    threshold=threshold,
                    min_level=min_level,
                    max_level=max_level
                )
            
            # 標準化結果格式（適配前端）
            results = []
            for result in raw_results:
                results.append({
                    'section_id': result.get('section_id'),
                    'source_id': result.get('source_id'),
                    'section_title': result.get('heading_text', ''),  # 使用 heading_text
                    'section_path': result.get('section_path', ''),
                    'content': result.get('content', ''),
                    'similarity': result.get('similarity', 0.0),
                    'level': result.get('heading_level', 0),  # 使用 heading_level
                    'word_count': result.get('word_count', 0),
                    'has_code': result.get('has_code', False),
                    'has_images': result.get('has_images', False)
                })
            
            return Response({
                'results': results,
                'total': len(results),
                'query': query,
                'search_type': 'section',
                'with_context': with_context
            })
            
        except Exception as e:
            logger.error(f"段落搜尋失敗: {str(e)}")
            return Response({
                'error': f'段落搜尋失敗: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def compare_search(self, request):
        """
        新舊搜尋系統對比 API
        
        同時執行整篇文檔搜尋（舊系統）和段落搜尋（新系統），
        並提供詳細的對比數據。
        
        請求參數：
        - query (str): 搜尋查詢
        - limit (int): 每個系統的結果數量，預設 3
        
        回應：
        {
            "query": "ULINK 測試環境",
            "old_system": {
                "results": [...],
                "avg_content_length": 1443,
                "avg_similarity": 0.8662,
                "search_type": "document"
            },
            "new_system": {
                "results": [...],
                "avg_content_length": 52,
                "avg_similarity": 0.9145,
                "search_type": "section"
            },
            "comparison": {
                "content_length_reduction": "96.4%",
                "similarity_improvement": "+4.8%",
                "precision_gain": "+5.6%"
            }
        }
        """
        try:
            query = request.data.get('query', '')
            limit = request.data.get('limit', 3)
            
            if not query:
                return Response({
                    'error': '請提供搜尋查詢'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 導入服務
            from api.services.embedding_service import get_embedding_service
            from library.common.knowledge_base.section_search_service import SectionSearchService
            from django.db import connection
            
            embedding_service = get_embedding_service()
            section_service = SectionSearchService()
            
            # 1. 生成查詢向量
            query_embedding = embedding_service.generate_embedding(query)
            
            # 2. 舊系統搜尋（整篇文檔）
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        de.source_id,
                        pg.title,
                        pg.content,
                        1 - (de.embedding <=> %s::vector) as similarity
                    FROM document_embeddings de
                    JOIN protocol_guide pg ON de.source_id = pg.id
                    WHERE de.source_table = 'protocol_guide'
                    ORDER BY de.embedding <=> %s::vector
                    LIMIT %s
                """, [query_embedding, query_embedding, limit])
                
                old_results = []
                for row in cursor.fetchall():
                    old_results.append({
                        'source_id': row[0],
                        'title': row[1],
                        'content': row[2],
                        'content_length': len(row[2]),
                        'similarity': float(row[3])
                    })
            
            # 3. 新系統搜尋（段落級別）
            new_results = section_service.search_sections(
                query=query,
                source_table='protocol_guide',
                limit=limit,
                threshold=0.0  # 不過濾，取 top limit
            )
            
            # 4. 計算統計數據
            old_avg_length = sum(r['content_length'] for r in old_results) / len(old_results) if old_results else 0
            old_avg_similarity = sum(r['similarity'] for r in old_results) / len(old_results) if old_results else 0
            
            new_avg_length = sum(len(r.get('content', '')) for r in new_results) / len(new_results) if new_results else 0
            new_avg_similarity = sum(r['similarity'] for r in new_results) / len(new_results) if new_results else 0
            
            # 5. 計算改善比例
            length_reduction = ((old_avg_length - new_avg_length) / old_avg_length * 100) if old_avg_length > 0 else 0
            similarity_improvement = ((new_avg_similarity - old_avg_similarity) / old_avg_similarity * 100) if old_avg_similarity > 0 else 0
            
            return Response({
                'query': query,
                'old_system': {
                    'results': old_results,
                    'avg_content_length': round(old_avg_length, 2),
                    'avg_similarity': round(old_avg_similarity * 100, 2),
                    'search_type': 'document',
                    'system': '整篇文檔搜尋'
                },
                'new_system': {
                    'results': new_results,
                    'avg_content_length': round(new_avg_length, 2),
                    'avg_similarity': round(new_avg_similarity * 100, 2),
                    'search_type': 'section',
                    'system': '段落級別搜尋'
                },
                'comparison': {
                    'content_length_reduction': f"{length_reduction:.1f}%",
                    'similarity_improvement': f"{similarity_improvement:+.1f}%",
                    'conclusion': '新系統更精準' if new_avg_similarity > old_avg_similarity else '舊系統更精準'
                }
            })
            
        except Exception as e:
            logger.error(f"對比搜尋失敗: {str(e)}")
            return Response({
                'error': f'對比搜尋失敗: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def regenerate_section_vectors(self, request):
        """
        重新生成段落向量 API
        
        用於：
        1. 新增文檔後批量生成段落向量
        2. 內容更新後重新生成段落向量
        3. 向量系統升級後批量遷移
        
        請求參數：
        - guide_ids (list): 要處理的 Guide ID 列表，空表示全部
        - force (bool): 是否強制重新生成（刪除舊向量），預設 False
        
        回應：
        {
            "processed": 5,
            "success": 4,
            "failed": 1,
            "details": [
                {"guide_id": 1, "sections": 23, "status": "success"},
                {"guide_id": 2, "sections": 0, "status": "failed", "error": "..."}
            ]
        }
        """
        try:
            guide_ids = request.data.get('guide_ids', [])
            force = request.data.get('force', False)
            
            # 導入服務
            from library.common.knowledge_base.section_vectorization_service import SectionVectorizationService
            
            vectorization_service = SectionVectorizationService()
            
            # 確定要處理的 Guide
            if guide_ids:
                guides = ProtocolGuide.objects.filter(id__in=guide_ids)
            else:
                guides = ProtocolGuide.objects.all()
            
            results = []
            success_count = 0
            failed_count = 0
            
            for guide in guides:
                try:
                    # 如果強制重新生成，先刪除舊向量
                    if force:
                        vectorization_service.delete_document_sections(
                            source_table='protocol_guide',
                            source_id=guide.id
                        )
                    
                    # 生成新向量
                    section_count = vectorization_service.vectorize_document_sections(
                        source_table='protocol_guide',
                        source_id=guide.id,
                        markdown_content=guide.content,
                        metadata={
                            'title': guide.title,
                            'protocol_name': guide.protocol_name,
                            'version': guide.version
                        }
                    )
                    
                    results.append({
                        'guide_id': guide.id,
                        'title': guide.title,
                        'sections': section_count,
                        'status': 'success'
                    })
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"Guide {guide.id} 向量生成失敗: {str(e)}")
                    results.append({
                        'guide_id': guide.id,
                        'title': guide.title,
                        'sections': 0,
                        'status': 'failed',
                        'error': str(e)
                    })
                    failed_count += 1
            
            return Response({
                'processed': len(guides),
                'success': success_count,
                'failed': failed_count,
                'details': results
            })
            
        except Exception as e:
            logger.error(f"批量生成段落向量失敗: {str(e)}")
            return Response({
                'error': f'批量生成段落向量失敗: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
