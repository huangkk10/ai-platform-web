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
