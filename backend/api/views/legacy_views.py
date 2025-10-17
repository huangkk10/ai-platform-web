from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db import models, connection
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.sessions.models import Session
from django.views import View
from django.http import JsonResponse
import json
import logging
import sys
import os
import time
from api.models import UserProfile, Project, Task, KnowIssue, TestClass, OCRTestClass, OCRStorageBenchmark, RVTGuide, ProtocolGuide, ContentImage
# RVT Guide 序列化器已模組化至 library/rvt_guide/serializers/
# 但通過 api/serializers.py 保持向後兼容，因此此處導入方式無需修改
from api.serializers import UserSerializer, UserProfileSerializer, UserPermissionSerializer, ProjectSerializer, TaskSerializer, KnowIssueSerializer, TestClassSerializer, OCRTestClassSerializer, OCRStorageBenchmarkSerializer, OCRStorageBenchmarkListSerializer, RVTGuideSerializer, RVTGuideListSerializer, ProtocolGuideSerializer, ProtocolGuideListSerializer, ContentImageSerializer, RVTGuideWithImagesSerializer
from rest_framework.exceptions import ValidationError

# 導入向量搜索服務
try:
    from api.services.embedding_service import search_rvt_guide_with_vectors, get_embedding_service
    VECTOR_SEARCH_AVAILABLE = True
except ImportError as e:
    VECTOR_SEARCH_AVAILABLE = False
    print(f"向量搜索服務不可用: {e}")  # 暫時使用 print，logger 會在後面定義

# 添加 library 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

# 導入 Dify 配置管理
try:
    from library.config.dify_config_manager import get_protocol_known_issue_config, get_report_analyzer_config
    from library.dify_integration import make_dify_request, process_dify_answer, dify_protocol_chat_api, fallback_protocol_chat_api
    # 🆕 導入資料庫搜索服務
    from library.data_processing.database_search import (
        DatabaseSearchService,
        search_know_issue_knowledge,
        search_rvt_guide_knowledge,
        search_ocr_storage_benchmark,
        search_postgres_knowledge
    )
    # 🆕 導入系統監控服務
    from library.system_monitoring import (
        HealthChecker, create_health_checker,
        AdminSystemMonitor, create_admin_monitor,
        get_minimal_fallback_status_dict,
        get_basic_fallback_status_dict
    )
    # 🆕 導入 AI OCR library
    from library.ai_ocr import (
        AIOCRAPIHandler,
        OCRTestClassViewSetManager,
        OCRStorageBenchmarkViewSetManager,
        AIOCRChatService,
        AIOCRSearchService,
        AI_OCR_LIBRARY_AVAILABLE,
        create_ai_ocr_api_handler,
        search_ocr_storage_benchmark_unified,
        fallback_dify_ocr_storage_benchmark_search,
        handle_upload_image_fallback,
        dify_ocr_chat_api,
        fallback_dify_chat_with_file,
        # 🆕 導入 OCR 處理器
        OCRProcessor,
        process_ocr_record,
        create_ocr_processor,
        fallback_process_ocr_record,
        # 🆕 導入查詢管理器
        OCRStorageBenchmarkQueryManager,
        create_ocr_queryset_manager,
        fallback_ocr_storage_benchmark_queryset_filter,
        # 🆕 導入最終備用 OCR 處理函數
        final_fallback_process_ocr,
        emergency_fallback_process_ocr
    )
    # 🆕 導入 AI Utils library (API 重試機制)
    from library.ai_utils import (
        retry_api_request,
        APIRetryHandler,
        APIRetryConfig,
        create_retry_handler,
        retryable_api,
        DEFAULT_CONFIG,
        AGGRESSIVE_CONFIG,
        CONSERVATIVE_CONFIG
    )
    # 🆕 導入認證服務 library
    from library.auth import (
        AuthenticationService,
        UserProfileService,
        ValidationService,
        AuthResponseFormatter,
        LoginHandler,
        DRFAuthHandler,
        # 🆕 導入權限管理和 ViewSet 管理器
        PermissionService,
        UserPermissionManager,
        UserProfileViewSetManager,
        UserProfileAPIHandler,
        get_user_profile_queryset,
        create_user_profile_viewset_manager,
        # 🆕 導入備用處理器
        UserProfileFallbackHandler,
        UserProfileViewSetFallbackManager,
        create_user_profile_fallback_manager,
        handle_user_profile_fallback,
        get_user_profile_queryset_fallback,
        get_user_profile_serializer_fallback
    )
    # 🆕 導入 RVT Guide library
    from library.rvt_guide import (
        RVTGuideAPIHandler,
        RVTGuideViewSetManager,
        RVTGuideSearchService,
        RVTGuideVectorService,
        fallback_dify_rvt_guide_search,
        fallback_rvt_guide_chat,
        fallback_rvt_guide_config
    )
    # 🆕 導入 Know Issue library
    from library.know_issue import (
        KnowIssueViewSetManager,
        KnowIssueAPIHandler,
        KnowIssueProcessor,
        process_know_issue_create,
        process_know_issue_update,
        handle_dify_know_issue_search_api,
        create_know_issue_viewset_manager,
        create_know_issue_api_handler,
        KNOW_ISSUE_LIBRARY_AVAILABLE
    )
    # 🆕 導入 Dify Knowledge library
    from library.dify_knowledge import (
        DifyKnowledgeSearchHandler,
        DifyKnowledgeAPIProcessor,
        DifyKnowledgeManager,
        handle_dify_knowledge_search_api,
        process_dify_knowledge_request,
        create_dify_knowledge_search_handler,
        DIFY_KNOWLEDGE_LIBRARY_AVAILABLE
    )
    # 🆕 導入 Chat Analytics library
    from library.chat_analytics import (
        ChatUsageStatisticsHandler,
        ChatUsageRecorder,
        ChatAnalyticsAPIHandler,
        handle_chat_usage_statistics_api,
        handle_record_chat_usage_api,
        create_chat_statistics_handler,
        create_chat_usage_recorder,
        CHAT_ANALYTICS_LIBRARY_AVAILABLE
    )
    # 🆕 導入 RVT Analytics library
    from library.rvt_analytics import (
        MessageFeedbackHandler,
        QuestionClassifier,
        SatisfactionAnalyzer,
        StatisticsManager,
        RVTAnalyticsAPIHandler,
        record_message_feedback,
        classify_question,
        analyze_user_satisfaction,
        get_rvt_analytics_stats,
        handle_feedback_api,
        handle_analytics_api,
        RVT_ANALYTICS_AVAILABLE,
        MESSAGE_FEEDBACK_AVAILABLE,
        QUESTION_CLASSIFIER_AVAILABLE,
        SATISFACTION_ANALYZER_AVAILABLE,
        STATISTICS_MANAGER_AVAILABLE,
        API_HANDLERS_AVAILABLE
    )
    # 🆕 導入聊天向量化和聚類服務
    try:
        from library.rvt_analytics.chat_vector_service import (
            get_chat_vector_service,
            generate_message_vector,
            search_similar_chat_messages
        )
        from library.rvt_analytics.chat_clustering_service import (
            get_clustering_service,
            perform_auto_clustering,
            get_cluster_categories
        )
        CHAT_VECTOR_SERVICES_AVAILABLE = True
    except ImportError as e:
        print(f"聊天向量化服務不可用: {e}")
        CHAT_VECTOR_SERVICES_AVAILABLE = False
    # 🆕 導入 Task Management library
    from library.task_management import (
        TaskViewSetManager,
        TaskQueryManager,
        TaskAssignmentHandler,
        TaskStatusManager,
        create_task_viewset_manager,
        create_task_query_manager,
        get_user_related_tasks,
        handle_task_assignment,
        handle_status_change,
        TASK_MANAGEMENT_LIBRARY_AVAILABLE
    )
    AUTH_LIBRARY_AVAILABLE = True
    RVT_GUIDE_LIBRARY_AVAILABLE = True
    KNOW_ISSUE_LIBRARY_AVAILABLE = True
    DIFY_KNOWLEDGE_LIBRARY_AVAILABLE = True
    CHAT_ANALYTICS_LIBRARY_AVAILABLE = True
except ImportError:
    # 如果 library 路徑有問題，提供備用配置
    get_protocol_known_issue_config = None
    get_report_analyzer_config = None
    make_dify_request = None
    process_dify_answer = None
    dify_protocol_chat_api = None
    fallback_protocol_chat_api = None
    # 備用搜索函數 (保持原有邏輯)
    DatabaseSearchService = None
    search_know_issue_knowledge = None
    search_rvt_guide_knowledge = None
    search_ocr_storage_benchmark = None
    search_postgres_knowledge = None
    # 備用系統監控服務
    HealthChecker = None
    create_health_checker = None
    AdminSystemMonitor = None
    create_admin_monitor = None
    get_minimal_fallback_status_dict = None
    get_basic_fallback_status_dict = None
    # 備用認證服務
    AuthenticationService = None
    UserProfileService = None
    ValidationService = None
    AuthResponseFormatter = None
    LoginHandler = None
    DRFAuthHandler = None
    # 🆕 備用權限管理和 ViewSet 管理器
    PermissionService = None
    UserPermissionManager = None
    UserProfileViewSetManager = None
    UserProfileAPIHandler = None
    get_user_profile_queryset = None
    create_user_profile_viewset_manager = None
    # 🆕 備用處理器
    UserProfileFallbackHandler = None
    UserProfileViewSetFallbackManager = None
    create_user_profile_fallback_manager = None
    handle_user_profile_fallback = None
    get_user_profile_queryset_fallback = None
    get_user_profile_serializer_fallback = None
    # 備用 RVT Guide 服務
    RVTGuideAPIHandler = None
    RVTGuideViewSetManager = None
    RVTGuideSearchService = None
    RVTGuideVectorService = None
    # 🆕 備用 Know Issue 服務
    KnowIssueViewSetManager = None
    KnowIssueAPIHandler = None
    KnowIssueProcessor = None
    process_know_issue_create = None
    process_know_issue_update = None
    handle_dify_know_issue_search_api = None
    create_know_issue_viewset_manager = None
    create_know_issue_api_handler = None
    KNOW_ISSUE_LIBRARY_AVAILABLE = False
    # 🆕 備用 Dify Knowledge 服務
    DifyKnowledgeSearchHandler = None
    DifyKnowledgeAPIProcessor = None
    DifyKnowledgeManager = None
    handle_dify_knowledge_search_api = None
    process_dify_knowledge_request = None
    create_dify_knowledge_search_handler = None
    DIFY_KNOWLEDGE_LIBRARY_AVAILABLE = False
    # 🆕 備用 Chat Analytics 服務
    ChatUsageStatisticsHandler = None
    ChatUsageRecorder = None
    ChatAnalyticsAPIHandler = None
    handle_chat_usage_statistics_api = None
    handle_record_chat_usage_api = None
    create_chat_statistics_handler = None
    create_chat_usage_recorder = None
    CHAT_ANALYTICS_LIBRARY_AVAILABLE = False
    # 🆕 備用 RVT Analytics 服務
    MessageFeedbackHandler = None
    QuestionClassifier = None
    SatisfactionAnalyzer = None
    StatisticsManager = None
    RVTAnalyticsAPIHandler = None
    record_message_feedback = None
    classify_question = None
    analyze_user_satisfaction = None
    get_rvt_analytics_stats = None
    handle_feedback_api = None
    handle_analytics_api = None
    RVT_ANALYTICS_AVAILABLE = False
    MESSAGE_FEEDBACK_AVAILABLE = False
    QUESTION_CLASSIFIER_AVAILABLE = False
    SATISFACTION_ANALYZER_AVAILABLE = False
    STATISTICS_MANAGER_AVAILABLE = False
    API_HANDLERS_AVAILABLE = False
    # 🆕 備用 Task Management 服務
    TaskViewSetManager = None
    TaskQueryManager = None
    TaskAssignmentHandler = None
    TaskStatusManager = None
    create_task_viewset_manager = None
    create_task_query_manager = None
    get_user_related_tasks = None
    handle_task_assignment = None
    handle_status_change = None
    TASK_MANAGEMENT_LIBRARY_AVAILABLE = False
    # 🆕 備用 AI OCR 服務
    AIOCRAPIHandler = None
    OCRTestClassViewSetManager = None
    OCRStorageBenchmarkViewSetManager = None
    AIOCRChatService = None
    AIOCRSearchService = None
    create_ai_ocr_api_handler = None
    search_ocr_storage_benchmark_unified = None
    fallback_dify_ocr_storage_benchmark_search = None
    handle_upload_image_fallback = None
    dify_ocr_chat_api = None
    # 🆕 備用 OCR 處理器
    OCRProcessor = None
    process_ocr_record = None
    create_ocr_processor = None
    fallback_process_ocr_record = None
    # 🆕 備用查詢管理器
    OCRStorageBenchmarkQueryManager = None
    create_ocr_queryset_manager = None
    fallback_ocr_storage_benchmark_queryset_filter = None
    # 🆕 備用最終 OCR 處理函數
    final_fallback_process_ocr = None
    emergency_fallback_process_ocr = None
    AI_OCR_LIBRARY_AVAILABLE = False
    # 🆕 備用 AI Utils 服務 (API 重試機制)
    retry_api_request = None
    APIRetryHandler = None
    APIRetryConfig = None
    create_retry_handler = None
    retryable_api = None
    DEFAULT_CONFIG = None
    AGGRESSIVE_CONFIG = None
    CONSERVATIVE_CONFIG = None
    # 備用函數設定為 None，將使用本地備用實現
    fallback_dify_rvt_guide_search = None
    fallback_rvt_guide_chat = None
    fallback_rvt_guide_config = None
    AUTH_LIBRARY_AVAILABLE = False
    RVT_GUIDE_LIBRARY_AVAILABLE = False
    KNOW_ISSUE_LIBRARY_AVAILABLE = False

logger = logging.getLogger(__name__)


# ============= 🎯 已重構：RVT Guide 實現已移到 library =============
# 所有 RVT Guide 相關功能現在都使用 library/rvt_guide/ 模組
# - 主要實現：library/rvt_guide/api_handlers.py
# - 備用實現：library/rvt_guide/fallback_handlers.py
# 無需本地備用函數，library 已提供完整的多層備用機制


# ============= 🎯 已重構：API 重試機制已移到 library =============
# retry_api_request 函數已重構到 library/ai_utils/api_retry.py
# - 提供更完整的重試策略（固定、線性、指數、斐波那契）
# - 智能錯誤分類和重試判斷
# - 裝飾器支援和預定義配置
# - 詳細的日誌記錄和監控
# 
# 🔄 重構後使用方式：
# from library.ai_utils import retry_api_request, retryable_api, APIRetryConfig
#
# # 方式1：直接調用
# result = retry_api_request(my_function, max_retries=3, retry_delay=1.0)
#
# # 方式2：使用裝飾器  
# @retryable_api(config)
# def my_api_function():
#     pass
#
# # 方式3：使用預定義配置
# from library.ai_utils import AGGRESSIVE_CONFIG, create_retry_handler
# handler = create_retry_handler(AGGRESSIVE_CONFIG)
# result = handler.retry_request(my_function)

# 🔄 向後兼容：保留原函數簽名，實際調用 library 實現
# retry_api_request 函數現在從 library.ai_utils 導入，無需本地實現


@method_decorator(csrf_exempt, name='dispatch')
class UserViewSet(viewsets.ModelViewSet):
    """使用者 ViewSet - 完整 CRUD，僅管理員可修改"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """根據動作決定權限"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            # 只有管理員可以進行寫操作
            return [permissions.IsAuthenticated(), permissions.IsAdminUser()]
        # 讀取操作只需要登入
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        """根據用戶權限返回不同的查詢集"""
        if self.request.user.is_staff:
            # 管理員可以看到所有用戶
            return User.objects.all()
        else:
            # 一般用戶只能看到自己
            return User.objects.filter(id=self.request.user.id)
    
    def perform_create(self, serializer):
        """創建用戶時的額外處理"""
        user = serializer.save()
        # 為新用戶創建 UserProfile
        UserProfile.objects.get_or_create(
            user=user,
            defaults={'bio': f'歡迎 {user.username} 加入！'}
        )
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def change_password(self, request, pk=None):
        """管理員重設用戶密碼"""
        user = self.get_object()
        new_password = request.data.get('new_password')
        
        if not new_password:
            return Response(
                {'error': 'new_password is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(new_password)
        user.save()
        
        return Response({'message': f'Password changed for user {user.username}'})


@method_decorator(csrf_exempt, name='dispatch')
class UserProfileViewSet(viewsets.ModelViewSet):
    """
    使用者個人檔案 ViewSet - 使用 library/auth 統一實現
    
    🔄 重構後：主要邏輯委託給 library/auth，備用實現也統一由 library 管理
    """
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 初始化 ViewSet 管理器和備用管理器
        if AUTH_LIBRARY_AVAILABLE and UserProfileViewSetManager:
            self._manager = create_user_profile_viewset_manager()
            self._fallback_manager = create_user_profile_fallback_manager()
        else:
            self._manager = None
            self._fallback_manager = None
            logger.warning("Auth Library 完全不可用，UserProfileViewSet 使用緊急備用實現")

    def get_queryset(self):
        """委託給 Auth Library 實現 - 包含統一的備用機制"""
        if self._manager:
            return self._manager.get_queryset_for_user(self.request.user)
        elif self._fallback_manager:
            # 使用 library 中的備用實現
            return self._fallback_manager.get_queryset_fallback(self.request.user)
        else:
            # 緊急備用實現（library 完全不可用時）
            logger.warning("使用緊急備用查詢集實現")
            user = self.request.user
            if user.is_superuser:
                return UserProfile.objects.all()
            return UserProfile.objects.filter(user=user)

    def get_serializer_class(self):
        """委託給 Auth Library 實現 - 包含統一的備用機制"""
        if self._manager:
            serializer_class = self._manager.get_serializer_class_for_action(self.action)
            if serializer_class:
                return serializer_class
        elif self._fallback_manager:
            # 使用 library 中的備用實現
            serializer_class = self._fallback_manager.get_serializer_class_fallback(self.action)
            if serializer_class:
                return serializer_class
        
        # 緊急備用實現
        logger.warning("使用緊急備用序列化器實現")
        if self.action in ['manage_permissions', 'bulk_update_permissions']:
            return UserPermissionSerializer
        return UserProfileSerializer

    @action(detail=False, methods=['get'], url_path='me')
    def get_my_profile(self, request):
        """獲取當前使用者的個人檔案 - 統一使用 library 備用處理器"""
        if self._manager:
            return self._manager.handle_get_my_profile(request.user)
        elif self._fallback_manager:
            return self._fallback_manager.handle_action_fallback('get_my_profile', request.user)
        else:
            # 緊急備用實現
            logger.warning("使用緊急備用 get_my_profile 實現")
            try:
                profile = UserProfile.objects.get(user=request.user)
                serializer = self.get_serializer(profile)
                return Response(serializer.data)
            except UserProfile.DoesNotExist:
                return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'], url_path='permissions', 
            permission_classes=[permissions.IsAuthenticated])
    def list_user_permissions(self, request):
        """獲取所有用戶的權限列表 - 統一使用 library 備用處理器"""
        if self._manager:
            return self._manager.handle_list_user_permissions(request.user)
        elif self._fallback_manager:
            return self._fallback_manager.handle_action_fallback('list_permissions', request.user)
        else:
            # 緊急備用實現
            logger.warning("使用緊急備用 list_permissions 實現")
            if not request.user.is_superuser:
                return Response({'error': '權限不足'}, status=status.HTTP_403_FORBIDDEN)
            
            profiles = UserProfile.objects.all().select_related('user').order_by('user__username')
            serializer = UserPermissionSerializer(profiles, many=True)
            return Response({'success': True, 'data': serializer.data, 'count': len(serializer.data)})

    @action(detail=True, methods=['patch'], url_path='permissions')
    def manage_permissions(self, request, pk=None):
        """管理指定用戶的權限 - 統一使用 library 備用處理器"""
        if self._manager:
            return self._manager.handle_manage_permissions(request.user, pk, request.data)
        elif self._fallback_manager:
            return self._fallback_manager.handle_action_fallback(
                'manage_permissions', 
                request.user, 
                target_user_id=pk, 
                update_data=request.data
            )
        else:
            # 緊急備用實現
            logger.warning("使用緊急備用 manage_permissions 實現")
            return Response({'error': '權限管理服務暫時不可用'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    @action(detail=False, methods=['post'], url_path='bulk-permissions')
    def bulk_update_permissions(self, request):
        """批量更新用戶權限 - 統一使用 library 備用處理器"""
        if self._manager:
            return self._manager.handle_bulk_update_permissions(request.user, request.data)
        elif self._fallback_manager:
            return self._fallback_manager.handle_action_fallback(
                'bulk_permissions', 
                request.user, 
                request_data=request.data
            )
        else:
            # 緊急備用實現
            logger.warning("使用緊急備用 bulk_permissions 實現")
            return Response({'error': '批量權限管理服務暫時不可用'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    @action(detail=False, methods=['get'], url_path='my-permissions')
    def get_my_permissions(self, request):
        """獲取當前用戶的權限資訊 - 統一使用 library 備用處理器"""
        if self._manager:
            return self._manager.handle_get_my_permissions(request.user)
        elif self._fallback_manager:
            return self._fallback_manager.handle_action_fallback('get_my_permissions', request.user)
        else:
            # 緊急備用實現
            logger.warning("使用緊急備用 get_my_permissions 實現")
            try:
                profile = UserProfile.objects.get(user=request.user)
                serializer = UserPermissionSerializer(profile)
                return Response({'success': True, 'data': serializer.data})
            except UserProfile.DoesNotExist:
                return Response({'error': '用戶檔案不存在'}, status=status.HTTP_404_NOT_FOUND)


@method_decorator(csrf_exempt, name='dispatch')
class ProjectViewSet(viewsets.ModelViewSet):
    """專案 ViewSet"""
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # 只返回使用者擁有或參與的專案
        user = self.request.user
        return Project.objects.filter(
            models.Q(owner=user) | models.Q(members=user)
        ).distinct()

    def perform_create(self, serializer):
        # 設定當前使用者為專案擁有者
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=['post'], url_path='add-member')
    def add_member(self, request, pk=None):
        """新增專案成員"""
        project = self.get_object()
        user_id = request.data.get('user_id')
        
        try:
            user = User.objects.get(id=user_id)
            project.members.add(user)
            return Response({'message': f'User {user.username} added to project'})
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'], url_path='remove-member')
    def remove_member(self, request, pk=None):
        """移除專案成員"""
        project = self.get_object()
        user_id = request.data.get('user_id')
        
        try:
            user = User.objects.get(id=user_id)
            project.members.remove(user)
            return Response({'message': f'User {user.username} removed from project'})
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )


@method_decorator(csrf_exempt, name='dispatch')
class TaskViewSet(viewsets.ModelViewSet):
    """
    任務 ViewSet - 使用 Task Management Library 統一實現
    
    🔄 重構後：主要邏輯委託給 library/task_management/
    """
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 初始化 Task Management ViewSet Manager
        if TASK_MANAGEMENT_LIBRARY_AVAILABLE and TaskViewSetManager:
            self._manager = create_task_viewset_manager()
        else:
            self._manager = None
            logger.warning("Task Management Library 不可用，TaskViewSet 使用備用實現")

    def get_queryset(self):
        """委託給 Task Management Library 實現"""
        if self._manager:
            return self._manager.get_user_tasks(self.request.user, self.request.query_params)
        else:
            # 備用實現
            logger.warning("使用備用任務查詢實現")
            try:
                if TASK_MANAGEMENT_LIBRARY_AVAILABLE:
                    from library.task_management import fallback_task_query
                    result = fallback_task_query(self.request.user, self.request.query_params)
                    if result is not None:
                        return result
                
                # 最終備用方案
                user = self.request.user
                return Task.objects.filter(
                    models.Q(assignee=user) | 
                    models.Q(creator=user) | 
                    models.Q(project__owner=user) |
                    models.Q(project__members=user)
                ).distinct().order_by('-created_at')
                
            except Exception as e:
                logger.error(f"任務查詢備用實現失敗: {str(e)}")
                return Task.objects.filter(assignee=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        """委託給 Task Management Library 實現"""
        if self._manager:
            return self._manager.perform_create(serializer, self.request.user)
        else:
            # 備用實現
            serializer.save(creator=self.request.user)

    @action(detail=True, methods=['post'], url_path='assign')
    def assign_task(self, request, pk=None):
        """
        指派任務給使用者 - 🔄 重構後使用 Task Management Library 統一實現
        """
        try:
            task = self.get_object()
            user_id = request.data.get('user_id')
            
            if not user_id:
                return Response({
                    'error': 'user_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if self._manager:
                # 使用 Task Management library 中的指派處理器
                return self._manager.handle_task_assignment(task, user_id, self.request.user)
            else:
                # 使用 library 中的備用實現
                logger.warning("ViewSet Manager 不可用，使用 library 指派備用實現")
                try:
                    user = User.objects.get(id=user_id)
                    if TASK_MANAGEMENT_LIBRARY_AVAILABLE:
                        from library.task_management import fallback_task_assignment
                        return fallback_task_assignment(task, user, self.request.user)
                    else:
                        # 最終備用方案
                        task.assignee = user
                        task.save()
                        return Response({
                            'message': f'Task assigned to {user.username}',
                            'emergency_fallback': True
                        })
                except User.DoesNotExist:
                    return Response(
                        {'error': 'User not found'}, 
                        status=status.HTTP_404_NOT_FOUND
                    )
        except Exception as e:
            logger.error(f"任務指派失敗: {str(e)}")
            return Response(
                {'error': f'任務指派失敗: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], url_path='change-status')
    def change_status(self, request, pk=None):
        """
        變更任務狀態 - 🔄 重構後使用 Task Management Library 統一實現
        """
        try:
            task = self.get_object()
            new_status = request.data.get('status')
            
            if not new_status:
                return Response({
                    'error': 'status is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if self._manager:
                # 使用 Task Management library 中的狀態管理器
                return self._manager.handle_status_change(task, new_status, self.request.user)
            else:
                # 使用 library 中的備用實現
                logger.warning("ViewSet Manager 不可用，使用 library 狀態備用實現")
                try:
                    if TASK_MANAGEMENT_LIBRARY_AVAILABLE:
                        from library.task_management import fallback_status_change
                        return fallback_status_change(task, new_status, self.request.user)
                    else:
                        # 最終備用方案
                        if new_status in dict(Task.STATUS_CHOICES):
                            old_status = task.status
                            task.status = new_status
                            task.save()
                            return Response({
                                'message': f'Task status changed from {old_status} to {new_status}',
                                'emergency_fallback': True
                            })
                        else:
                            return Response(
                                {'error': 'Invalid status'}, 
                                status=status.HTTP_400_BAD_REQUEST
                            )
                except Exception as e:
                    logger.error(f"狀態變更備用實現失敗: {str(e)}")
                    return Response(
                        {'error': f'狀態變更失敗: {str(e)}'}, 
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
        except Exception as e:
            logger.error(f"任務狀態變更失敗: {str(e)}")
            return Response(
                {'error': f'任務狀態變更失敗: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def statistics(self, request):
        """
        獲取任務統計資料 - 🆕 新增功能，使用 Task Management Library
        """
        try:
            if self._manager:
                statistics = self._manager.get_task_statistics(self.request.user)
                return Response({
                    'success': True,
                    'data': statistics
                }, status=status.HTTP_200_OK)
            else:
                # 使用備用實現
                try:
                    if TASK_MANAGEMENT_LIBRARY_AVAILABLE:
                        from library.task_management import fallback_task_statistics
                        statistics = fallback_task_statistics(self.request.user)
                        return Response({
                            'success': True,
                            'data': statistics
                        }, status=status.HTTP_200_OK)
                    else:
                        # 最終備用方案
                        user_tasks = self.get_queryset()
                        return Response({
                            'success': True,
                            'data': {
                                'total_tasks': user_tasks.count(),
                                'emergency_fallback': True
                            }
                        }, status=status.HTTP_200_OK)
                except Exception as e:
                    logger.error(f"統計備用實現失敗: {str(e)}")
                    return Response({
                        'success': False,
                        'error': str(e)
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"任務統計獲取失敗: {str(e)}")
            return Response({
                'success': False,
                'error': f'統計資料獲取失敗: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def available_transitions(self, request, pk=None):
        """
        獲取任務可用的狀態轉換 - 🆕 新增功能
        """
        try:
            task = self.get_object()
            
            if self._manager:
                transitions = self._manager.get_available_status_transitions(task)
            else:
                # 備用實現：返回所有可用狀態
                transitions = [choice[0] for choice in Task.STATUS_CHOICES if choice[0] != task.status]
            
            return Response({
                'success': True,
                'current_status': task.status,
                'available_transitions': transitions
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"獲取可用轉換失敗: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)







# ============= 🚨 重要：Dify 知識庫 API 已重構 =============
# Dify 外部知識庫相關的 API 已移動到 views/dify_knowledge_views.py
# 搜索函數和 API 端點現在使用依賴注入模式，避免循環依賴
# 
# 如需使用 Dify API，請導入：
# from .dify_knowledge_views import (
#     dify_knowledge_search,
#     dify_know_issue_search,
#     dify_ocr_storage_benchmark_search,
#     dify_rvt_guide_search,
#     dify_protocol_guide_search,
# )


@method_decorator(csrf_exempt, name='dispatch')
class KnowIssueViewSet(viewsets.ModelViewSet):
    """
    問題知識庫 ViewSet - 使用 Know Issue Library 實現
    
    🔄 重構後：主要邏輯委託給 library/know_issue/
    """
    queryset = KnowIssue.objects.all()
    serializer_class = KnowIssueSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 初始化 Know Issue ViewSet Manager
        if KNOW_ISSUE_LIBRARY_AVAILABLE and KnowIssueViewSetManager:
            self._manager = KnowIssueViewSetManager()
        else:
            self._manager = None
            logger.warning("Know Issue Library 不可用，KnowIssueViewSet 使用備用實現")
    
    def get_permissions(self):
        """委託給 Know Issue Library 實現"""
        if self._manager:
            return self._manager.get_permissions_for_action(self.action, self.request.user)
        else:
            # 備用實現
            logger.info(f"KnowIssue get_permissions - Action: {self.action}")
            logger.info(f"KnowIssue get_permissions - User: {self.request.user}")
            logger.info(f"KnowIssue get_permissions - Is authenticated: {self.request.user.is_authenticated}")
            
            # 允許所有登入用戶訪問
            return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        """委託給 Know Issue Library 實現"""
        base_queryset = KnowIssue.objects.all()
        
        if self._manager:
            return self._manager.get_filtered_queryset(base_queryset, self.request.query_params)
        else:
            # 備用實現 - 簡化過濾
            try:
                from library.know_issue.fallback_handlers import fallback_know_issue_queryset_filter
                return fallback_know_issue_queryset_filter(base_queryset, self.request.query_params)
            except ImportError:
                # 最終備用實現
                search = self.request.query_params.get('search', None)
                if search:
                    base_queryset = base_queryset.filter(
                        models.Q(project__icontains=search) |
                        models.Q(error_message__icontains=search)
                    )
                return base_queryset.order_by('-updated_at')
    
    def create(self, request, *args, **kwargs):
        """
        創建 Know Issue - 使用 Know Issue Library 統一實現
        
        🔄 重構後：直接使用 library/know_issue/ 處理
        """
        try:
            serializer = self.get_serializer(data=request.data)
            
            if KNOW_ISSUE_LIBRARY_AVAILABLE and process_know_issue_create:
                # 使用 Know Issue library 中的統一處理器
                return process_know_issue_create(request, serializer, request.user)
            elif self._manager:
                # 使用 ViewSet 管理器中的處理方法
                return self._manager.handle_create(request, serializer)
            else:
                # 使用備用實現
                try:
                    from library.know_issue.fallback_handlers import fallback_know_issue_create
                    return fallback_know_issue_create(request, serializer)
                except ImportError:
                    # 最終備用方案
                    logger.warning("Know Issue Library 完全不可用，使用最終備用實現")
                    if serializer.is_valid():
                        instance = serializer.save(updated_by=request.user)
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
        更新 Know Issue - 使用 Know Issue Library 統一實現
        
        🔄 重構後：直接使用 library/know_issue/ 處理
        """
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            
            if KNOW_ISSUE_LIBRARY_AVAILABLE and process_know_issue_update:
                # 使用 Know Issue library 中的統一處理器
                return process_know_issue_update(request, instance, serializer, request.user)
            elif self._manager:
                # 使用 ViewSet 管理器中的處理方法
                return self._manager.handle_update(request, instance, serializer)
            else:
                # 使用備用實現
                try:
                    from library.know_issue.fallback_handlers import fallback_know_issue_update
                    return fallback_know_issue_update(request, instance, serializer)
                except ImportError:
                    # 最終備用方案
                    logger.warning("Know Issue Library 完全不可用，使用最終備用實現")
                    if serializer.is_valid():
                        updated_instance = serializer.save(updated_by=request.user)
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
        """委託給 Know Issue Library 實現"""
        if self._manager:
            return self._manager.perform_create(serializer, self.request.user)
        else:
            # 備用實現
            serializer.save(updated_by=self.request.user)
    
    def perform_update(self, serializer):
        """委託給 Know Issue Library 實現"""
        if self._manager:
            return self._manager.perform_update(serializer, self.request.user)
        else:
            # 備用實現
            serializer.save(updated_by=self.request.user)
    
    def _generate_vector_for_know_issue(self, instance, action='create'):
        """
        為 Know Issue 生成向量資料
        
        Args:
            instance: KnowIssue 實例
            action: 操作類型 ('create' 或 'update')
        """
        try:
            # 動態導入 embedding_service 避免循環導入
            from .services.embedding_service import get_embedding_service
            
            # 格式化內容用於向量化
            content = f"Issue ID: {instance.issue_id}\n"
            content += f"專案: {instance.project}\n"
            content += f"問題類型: {instance.issue_type}\n"
            content += f"狀態: {instance.status}\n"
            content += f"錯誤訊息: {instance.error_message}\n"
            if instance.supplement:
                content += f"補充說明: {instance.supplement}\n"
            if instance.script:
                content += f"相關腳本: {instance.script}\n"
            
            # 獲取 embedding 服務
            service = get_embedding_service()  # 使用 1024 維模型
            
            # 生成並儲存向量
            success = service.store_document_embedding(
                source_table='know_issue',
                source_id=instance.id,
                content=content,
                use_1024_table=True  # 使用 1024 維表格
            )
            
            if success:
                logger.info(f"✅ 成功為 Know Issue 生成向量 ({action}): ID {instance.id} - {instance.issue_id}")
            else:
                logger.error(f"❌ Know Issue 向量生成失敗 ({action}): ID {instance.id} - {instance.issue_id}")
                
        except Exception as e:
            logger.error(f"❌ Know Issue 向量生成異常 ({action}): ID {instance.id} - {str(e)}")


@method_decorator(csrf_exempt, name='dispatch')
class TestClassViewSet(viewsets.ModelViewSet):
    """測試類別 ViewSet - 讀取開放給所有用戶，但只有 admin 可以修改"""
    queryset = TestClass.objects.all()
    serializer_class = TestClassSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """
        讀取操作(list, retrieve)開放給所有認證用戶
        修改操作(create, update, partial_update, destroy)只允許管理員
        """
        if self.action in ['list', 'retrieve']:
            # 讀取操作：所有認證用戶都可以訪問
            return [permissions.IsAuthenticated()]
        else:
            # 修改操作：只有管理員可以訪問
            if not (self.request.user.is_staff or self.request.user.is_superuser):
                self.permission_denied(
                    self.request,
                    message='只有管理員才能管理測試類別'
                )
            return [permissions.IsAuthenticated()]
    
    def perform_create(self, serializer):
        """建立時設定建立者為當前用戶"""
        serializer.save(created_by=self.request.user)
    
    def get_queryset(self):
        """支援搜尋和篩選"""
        queryset = TestClass.objects.all()
        
        # 搜尋功能
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        # 狀態篩選
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            if is_active.lower() in ['true', '1']:
                queryset = queryset.filter(is_active=True)
            elif is_active.lower() in ['false', '0']:
                queryset = queryset.filter(is_active=False)
        
        return queryset.order_by('-created_at')


@method_decorator(csrf_exempt, name='dispatch')
class OCRTestClassViewSet(viewsets.ModelViewSet):
    """
    OCR測試類別 ViewSet - 使用 AI OCR Library 實現
    
    🔄 重構後：主要邏輯委託給 library/ai_ocr/viewset_manager.py
    """
    queryset = OCRTestClass.objects.all()
    serializer_class = OCRTestClassSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 初始化 AI OCR ViewSet Manager
        if AI_OCR_LIBRARY_AVAILABLE and OCRTestClassViewSetManager:
            self._manager = OCRTestClassViewSetManager()
        else:
            self._manager = None
            logger.warning("AI OCR Library 不可用，OCRTestClassViewSet 使用備用實現")
    
    def get_permissions(self):
        """委託給 AI OCR Library 實現"""
        if self._manager:
            return self._manager.get_permissions(self)
        else:
            # 備用實現
            if self.action in ['list', 'retrieve']:
                return [permissions.IsAuthenticated()]
            else:
                if not (self.request.user.is_staff or self.request.user.is_superuser):
                    self.permission_denied(self.request, message='只有管理員才能管理OCR測試類別')
                return [permissions.IsAuthenticated()]
    
    def perform_create(self, serializer):
        """委託給 AI OCR Library 實現"""
        if self._manager:
            return self._manager.perform_create(self, serializer)
        else:
            # 備用實現
            serializer.save(created_by=self.request.user)
    
    def get_queryset(self):
        """委託給 AI OCR Library 實現"""
        if self._manager:
            return self._manager.get_queryset(self)
        else:
            # 備用實現
            queryset = OCRTestClass.objects.all()
            search = self.request.query_params.get('search', None)
            if search:
                queryset = queryset.filter(name__icontains=search)
            
            is_active = self.request.query_params.get('is_active', None)
            if is_active is not None:
                if is_active.lower() in ['true', '1']:
                    queryset = queryset.filter(is_active=True)
                elif is_active.lower() in ['false', '0']:
                    queryset = queryset.filter(is_active=False)
            
            return queryset.order_by('-created_at')


@method_decorator(csrf_exempt, name='dispatch')
class OCRStorageBenchmarkViewSet(viewsets.ModelViewSet):
    """
    AI OCR 存儲基準測試 ViewSet - 使用 AI OCR Library 實現
    
    🔄 重構後：複雜方法委託給 library/ai_ocr/viewset_manager.py
    """
    queryset = OCRStorageBenchmark.objects.all()
    serializer_class = OCRStorageBenchmarkSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 初始化 AI OCR ViewSet Manager
        if AI_OCR_LIBRARY_AVAILABLE and OCRStorageBenchmarkViewSetManager:
            self._manager = OCRStorageBenchmarkViewSetManager()
        else:
            self._manager = None
            logger.warning("AI OCR Library 不可用，OCRStorageBenchmarkViewSet 使用備用實現")
    
    def get_serializer_class(self):
        """委託給 AI OCR Library 實現"""
        if self._manager:
            return self._manager.get_serializer_class(self)
        else:
            # 備用實現
            if self.action == 'list':
                return OCRStorageBenchmarkListSerializer
            return OCRStorageBenchmarkSerializer
    
    def perform_create(self, serializer):
        """委託給 AI OCR Library 實現"""
        if self._manager:
            return self._manager.perform_create(self, serializer)
        else:
            # 備用實現
            serializer.save(uploaded_by=self.request.user)
    
    def get_queryset(self):
        """委託給 AI OCR Library 實現"""
        # 🔄 重構後：統一使用 AI OCR Library 中的查詢管理邏輯
        base_queryset = OCRStorageBenchmark.objects.select_related('test_class', 'uploaded_by').all()
        
        if self._manager:
            # 優先使用 ViewSet Manager 中的查詢邏輯（已整合查詢管理器）
            return self._manager.get_filtered_queryset(base_queryset, self.request.query_params)
        else:
            # 🚨 備用實現：直接使用 library 中的查詢管理器
            try:
                if AI_OCR_LIBRARY_AVAILABLE:
                    from library.ai_ocr import (
                        create_ocr_queryset_manager,
                        fallback_ocr_storage_benchmark_queryset_filter
                    )
                    
                    # 嘗試創建查詢管理器
                    query_manager = create_ocr_queryset_manager()
                    if query_manager:
                        return query_manager.get_filtered_queryset(base_queryset, self.request.query_params)
                    else:
                        # 使用備用函數
                        return fallback_ocr_storage_benchmark_queryset_filter(
                            base_queryset, self.request.query_params
                        )
                else:
                    # AI OCR Library 完全不可用時的最終備用
                    logger.warning("AI OCR Library 完全不可用，使用最基本查詢邏輯")
                    search = self.request.query_params.get('search', None)
                    if search:
                        base_queryset = base_queryset.filter(
                            models.Q(project_name__icontains=search) |
                            models.Q(device_model__icontains=search)
                        )
                    return base_queryset.order_by('-test_datetime', '-created_at')
                    
            except Exception as e:
                logger.error(f"使用 library 查詢管理器失敗: {str(e)}")
                # 最終備用方案
                search = self.request.query_params.get('search', None)
                if search:
                    base_queryset = base_queryset.filter(
                        models.Q(project_name__icontains=search) |
                        models.Q(device_model__icontains=search)
                    )
                return base_queryset.order_by('-test_datetime', '-created_at')
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def upload_image(self, request, pk=None):
        """上傳原始圖像 - 委託給 AI OCR Library 實現"""
        if self._manager:
            return self._manager.upload_image(self, request, pk)
        else:
            # 使用 library 中的備用實現
            try:
                ocr_record = self.get_object()
                uploaded_file = request.FILES.get('image')
                
                if handle_upload_image_fallback:
                    # 使用 AI OCR library 中的備用實現
                    return handle_upload_image_fallback(ocr_record, uploaded_file)
                else:
                    # 最終備用方案
                    logger.error("AI OCR Library 完全不可用，無法上傳圖像")
                    return Response({
                        'error': 'AI OCR 圖像上傳服務暫時不可用，請稍後再試或聯絡管理員'
                    }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
                    
            except Exception as e:
                logger.error(f"圖像上傳失敗: {str(e)}")
                return Response({
                    'error': f'圖像上傳失敗: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # 🚨 verify_record 方法已移除
    # 原因：OCRStorageBenchmark 模型中沒有 verified_by, verification_notes, is_verified 字段
    # 這些字段在運行 0021 遷移時已被移除，但方法未同步更新
    # 如需驗證功能，請先在模型中重新添加相關字段
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def process_ocr(self, request, pk=None):
        """
        處理 OCR 識別 - 使用 AI OCR Library 統一實現
        
        🔄 重構後：直接使用 library/ai_ocr/ocr_processor.py 處理
        """
        try:
            ocr_record = self.get_object()
            
            if AI_OCR_LIBRARY_AVAILABLE and process_ocr_record:
                # 使用 AI OCR library 中的統一處理器
                return process_ocr_record(ocr_record)
            elif self._manager:
                # 使用 ViewSet 管理器中的處理方法
                return self._manager.handle_process_ocr(ocr_record)
            else:
                # 🔄 重構後：使用 library 中的最終備用實現
                logger.warning("AI OCR Library 和管理器都不可用，使用 library 最終備用實現")
                if final_fallback_process_ocr:
                    # 使用 AI OCR library 中的最終備用處理
                    return final_fallback_process_ocr(ocr_record)
                elif emergency_fallback_process_ocr:
                    # 使用緊急備用處理
                    return emergency_fallback_process_ocr(ocr_record)
                else:
                    # 🚨 最終錯誤：所有 library 備用函數都不可用
                    logger.error("所有 library 最終備用函數都不可用，OCR 處理功能完全無法使用")
                    return Response({
                        'error': 'OCR 處理服務完全不可用，請檢查系統配置或聯絡管理員',
                        'error_code': 'OCR_SERVICE_UNAVAILABLE',
                        'note': '所有備用處理方式都已失效，系統需要維護'
                    }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
                
        except Exception as e:
            logger.error(f"OCR 處理失敗: {str(e)}")
            return Response({
                'error': f'OCR 處理失敗: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # 🆕 _emergency_local_fallback_process_ocr 方法已移除
    # 原因：此功能已在 library/ai_ocr/fallback_handlers.py 中實現
    # 現在使用：final_fallback_process_ocr 和 emergency_fallback_process_ocr 函數
    # 這些函數提供更完整的錯誤處理和日誌記錄
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def statistics(self, request):
        """
        獲取統計資料 - 🆕 重構後使用 AI OCR Library 統一實現
        """
        try:
            queryset = self.get_queryset()
            
            if self._manager:
                # 使用 ViewSet Manager 中的統計功能（已整合統計管理器）
                return self._manager.get_statistics_data(queryset)
            else:
                # 使用 library 中的備用統計實現
                logger.warning("ViewSet Manager 不可用，使用 library 統計備用實現")
                try:
                    if AI_OCR_LIBRARY_AVAILABLE:
                        from library.ai_ocr import handle_ocr_storage_benchmark_statistics
                        return handle_ocr_storage_benchmark_statistics(queryset)
                    else:
                        # AI OCR Library 完全不可用時的最終備用
                        logger.error("AI OCR Library 完全不可用，使用最基本統計")
                        return self._emergency_basic_statistics(queryset)
                except ImportError as e:
                    logger.error(f"AI OCR Library 統計功能導入失敗: {e}")
                    return self._emergency_basic_statistics(queryset)
                    
        except Exception as e:
            logger.error(f"統計資料獲取失敗: {str(e)}")
            return Response({
                'success': False,
                'error': f'統計資料獲取失敗: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _emergency_basic_statistics(self, queryset):
        """緊急基本統計實現（在所有 library 都不可用時使用）"""
        try:
            total_records = queryset.count()
            if total_records == 0:
                return Response({
                    'success': True,
                    'total_records': 0,
                    'message': '沒有找到任何記錄',
                    'emergency_fallback': True
                }, status=status.HTTP_200_OK)
            
            return Response({
                'success': True,
                'total_records': total_records,
                'message': '使用緊急基本統計實現，功能受限',
                'emergency_fallback': True
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"緊急基本統計也失敗: {str(e)}")
            return Response({
                'success': False,
                'error': f'統計功能完全不可用: {str(e)}',
                'emergency_fallback': True
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# === 用戶認證 API ===

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([])
def user_login_api(request):
    """
    用戶登入 API - 統一使用 DRFAuthHandler 實現
    優化版本：移除 class-based view，統一使用 function-based view
    """
    return DRFAuthHandler.handle_login_api(request)


# 🚫 已棄用：UserLoginView class 已重構為 function-based view
# 理由：統一 API 風格，簡化維護，更好的 DRF 整合


# user_login function 已移除 - 改為使用優化後的 UserLoginView


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([])
def user_register(request):
    """
    用戶註冊 API - 完全使用 library/auth/DRFAuthHandler 實現
    """
    return DRFAuthHandler.handle_register_api(request)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([])
def user_logout(request):
    """
    用戶登出 API - 完全使用 library/auth/DRFAuthHandler 實現
    """
    return DRFAuthHandler.handle_logout_api(request)


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    更改密碼 API - 完全使用 library/auth/DRFAuthHandler 實現
    """
    return DRFAuthHandler.handle_change_password_api(request)


@api_view(['GET'])
@permission_classes([])
def user_info(request):
    """
    獲取當前用戶資訊 API - 完全使用 library/auth/DRFAuthHandler 實現
    """
    return DRFAuthHandler.handle_user_info_api(request)


@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def dify_chat_with_file(request):
    """
    Dify Chat API with File Support - 使用 AI OCR Library 實現
    
    🔄 重構後：直接使用 library/ai_ocr/api_handlers.py 處理
    """
    try:
        if AI_OCR_LIBRARY_AVAILABLE and AIOCRAPIHandler:
            # 使用 AI OCR library 中的 API 處理器
            return AIOCRAPIHandler.handle_dify_chat_with_file_api(request)
        else:
            # 使用 library 中的備用實現
            logger.warning("AI OCR Library 不可用，使用 library 備用實現")
            return fallback_dify_chat_with_file(request)
            
    except Exception as e:
        logger.error(f"Dify chat with file API error: {str(e)}")
        return Response({
            'success': False,
            'error': f'服務器錯誤: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])  # 修復：要求認證
def dify_chat(request):
    """
    Dify Chat API - 使用 Protocol Known Issue 配置（用於 Protocol RAG）
    
    🔄 重構後：直接使用 library/dify_integration/protocol_chat_handler.py 處理
    🔒 權限修復：要求用戶認證後才能使用 Protocol RAG
    """
    try:
        if dify_protocol_chat_api:
            # 使用 library 中的 Protocol Chat 實現
            return dify_protocol_chat_api(request)
        else:
            # 使用 library 中的備用實現
            if fallback_protocol_chat_api:
                return fallback_protocol_chat_api(request)
            else:
                # 最終備用方案：完全不可用時
                logger.error("所有 Protocol Chat 服務都不可用")
                return Response({
                    'success': False,
                    'error': 'Protocol Chat 服務暫時完全不可用，請稍後再試或聯絡管理員',
                    'service_status': 'completely_unavailable'
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
    except Exception as e:
        logger.error(f"Dify protocol chat API error: {str(e)}")
        return Response({
            'success': False,
            'error': f'服務器錯誤: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def dify_config_info(request):
    """
    獲取 Dify 配置資訊 - 用於前端顯示（使用 Protocol Known Issue 配置）
    """
    try:
        # 使用 Protocol Known Issue 配置
        config = get_protocol_known_issue_config()
        
        # 只返回安全的配置資訊
        safe_config = config.get_safe_config()
        
        return Response({
            'success': True,
            'config': safe_config
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Get Dify config error: {str(e)}")
        return Response({
            'success': False,
            'error': f'獲取配置失敗: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def dify_ocr_chat(request):
    """
    Dify OCR Chat API - 使用 AI OCR Library 統一實現
    
    🔄 重構後：直接使用 library 中的便利函數
    """
    if dify_ocr_chat_api:
        # 使用 library 中的統一實現
        return dify_ocr_chat_api(request)
    else:
        # 最終備用方案
        logger.error("AI OCR Library 完全不可用")
        return Response({
            'success': False,
            'error': 'AI OCR 聊天服務暫時不可用，請稍後再試或聯絡管理員'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(['GET'])
@permission_classes([AllowAny])
def chat_usage_statistics(request):
    """
    獲取聊天使用統計數據 - 使用 Chat Analytics Library 統一實現
    
    🔄 重構後：直接使用 library/chat_analytics/ 處理
    """
    try:
        if CHAT_ANALYTICS_LIBRARY_AVAILABLE and handle_chat_usage_statistics_api:
            # 使用 Chat Analytics library 中的統一 API 處理器
            return handle_chat_usage_statistics_api(request)
        else:
            # 使用備用實現
            logger.warning("Chat Analytics Library 不可用，使用備用實現")
            try:
                from library.chat_analytics.fallback_handlers import fallback_chat_usage_statistics_api
                return fallback_chat_usage_statistics_api(request)
            except ImportError:
                # 最終備用方案
                logger.error("Chat Analytics Library 完全不可用")
                return Response({
                    'success': False,
                    'error': 'Chat analytics service temporarily unavailable'
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
                
    except Exception as e:
        logger.error(f"Chat usage statistics error: {str(e)}")
        return Response({
            'success': False,
            'error': f'統計數據獲取失敗: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def record_chat_usage(request):
    """
    記錄聊天使用情況 - 使用 Chat Analytics Library 統一實現
    
    🔄 重構後：直接使用 library/chat_analytics/ 處理
    """
    try:
        if CHAT_ANALYTICS_LIBRARY_AVAILABLE and handle_record_chat_usage_api:
            # 使用 Chat Analytics library 中的統一 API 處理器
            return handle_record_chat_usage_api(request)
        else:
            # 使用備用實現
            logger.warning("Chat Analytics Library 不可用，使用備用實現")
            try:
                from library.chat_analytics.fallback_handlers import fallback_record_chat_usage_api
                return fallback_record_chat_usage_api(request)
            except ImportError:
                # 最終備用方案
                logger.error("Chat Analytics Library 完全不可用")
                return Response({
                    'success': False,
                    'error': 'Chat analytics service temporarily unavailable'
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
                
    except Exception as e:
        logger.error(f"Record chat usage error: {str(e)}")
        return Response({
            'success': False,
            'error': f'記錄使用情況失敗: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def rvt_guide_chat(request):
    """
    RVT Guide Chat API - 使用 library 統一實現
    """
    try:
        if RVT_GUIDE_LIBRARY_AVAILABLE and RVTGuideAPIHandler:
            return RVTGuideAPIHandler.handle_chat_api(request)
        elif fallback_rvt_guide_chat:
            # 使用 library 中的備用實現
            return fallback_rvt_guide_chat(request)
        else:
            # library 完全不可用時的最終錯誤處理
            logger.error("RVT Guide library 完全不可用")
            return Response({
                'success': False,
                'error': 'RVT Guide service temporarily unavailable, please contact administrator'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        logger.error(f"RVT Guide chat error: {str(e)}")
        return Response({
            'success': False,
            'error': f'RVT Guide 服務器錯誤: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def rvt_guide_config(request):
    """
    獲取 RVT Guide 配置信息 - 使用 library 統一實現
    """
    try:
        if RVT_GUIDE_LIBRARY_AVAILABLE and RVTGuideAPIHandler:
            return RVTGuideAPIHandler.handle_config_api(request)
        elif fallback_rvt_guide_config:
            # 使用 library 中的備用實現
            return fallback_rvt_guide_config(request)
        else:
            # library 完全不可用時的最終錯誤處理
            logger.error("RVT Guide library 完全不可用")
            return Response({
                'success': False,
                'error': 'RVT Guide configuration service temporarily unavailable'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        logger.error(f"Get RVT Guide config error: {str(e)}")
        return Response({
            'success': False,
            'error': f'獲取 RVT Guide 配置失敗: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class RVTGuideViewSet(viewsets.ModelViewSet):
    """RVT Guide ViewSet - 使用 library 統一管理"""
    queryset = RVTGuide.objects.all()
    serializer_class = RVTGuideSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.viewset_manager = None
        if RVT_GUIDE_LIBRARY_AVAILABLE and RVTGuideViewSetManager:
            self.viewset_manager = RVTGuideViewSetManager()
    
    def get_serializer_class(self):
        """根據操作類型選擇合適的序列化器"""
        if self.viewset_manager:
            return self.viewset_manager.get_serializer_class(self.action)
        else:
            # 備用實現
            if self.action == 'list':
                return RVTGuideListSerializer
            return RVTGuideSerializer
    
    def perform_create(self, serializer):
        """建立新的 RVT Guide"""
        if self.viewset_manager:
            return self.viewset_manager.perform_create(serializer)
        else:
            # 備用實現
            return serializer.save()
    
    def perform_update(self, serializer):
        """更新現有的 RVT Guide"""
        if self.viewset_manager:
            return self.viewset_manager.perform_update(serializer)
        else:
            # 備用實現
            return serializer.save()
    
    def perform_destroy(self, instance):
        """刪除 RVT Guide 時同時刪除對應的向量資料 - 委託給 ViewSet Manager"""
        if self.viewset_manager:
            return self.viewset_manager.perform_destroy(instance)
        else:
            # 備用實現：直接刪除（沒有向量處理）
            logger.warning("ViewSet Manager 不可用，使用簡化刪除邏輯")
            instance.delete()
    
    def get_queryset(self):
        """支援搜尋和篩選 - 委託給 ViewSet Manager"""
        base_queryset = RVTGuide.objects.all()
        
        if self.viewset_manager:
            return self.viewset_manager.get_queryset(base_queryset, self.request.query_params)
        else:
            # 備用實現 - 簡化的篩選
            search = self.request.query_params.get('search', None)
            if search:
                base_queryset = base_queryset.filter(
                    models.Q(title__icontains=search) |
                    models.Q(content__icontains=search)
                )
            return base_queryset.order_by('-created_at')
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def statistics(self, request):
        """獲取統計資料"""
        queryset = self.get_queryset()
        
        if self.viewset_manager:
            return self.viewset_manager.get_statistics_data(queryset)
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
            # 先檢查圖片是否存在且屬於該 guide
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
    
    def get_serializer_class(self):
        """根據操作類型選擇合適的序列化器"""
        # 檢查是否需要包含圖片資料
        include_images = self.request.query_params.get('include_images', 'false').lower() == 'true'
        
        if self.viewset_manager:
            serializer_class = self.viewset_manager.get_serializer_class(self.action)
            # 如果需要圖片且是詳細檢視，使用帶圖片的序列化器
            if include_images and self.action in ['retrieve', 'list']:
                return RVTGuideWithImagesSerializer
            return serializer_class
        else:
            # 備用實現
            if include_images and self.action in ['retrieve', 'list']:
                return RVTGuideWithImagesSerializer
            elif self.action == 'list':
                return RVTGuideListSerializer
            return RVTGuideSerializer


# ============= Protocol Guide 相關 API =============

# 檢查 Protocol Guide Library 是否可用
PROTOCOL_GUIDE_LIBRARY_AVAILABLE = False
ProtocolGuideViewSetManager = None
ProtocolGuideAPIHandler = None

try:
    from library.protocol_guide import (
        ProtocolGuideViewSetManager,
        ProtocolGuideAPIHandler
    )
    PROTOCOL_GUIDE_LIBRARY_AVAILABLE = True
    logger.info("✅ Protocol Guide Library 載入成功")
except ImportError as e:
    logger.warning(f"⚠️  Protocol Guide Library 無法載入: {str(e)}")
    logger.warning("將使用備用實現（功能受限）")


@method_decorator(csrf_exempt, name='dispatch')
class ProtocolGuideViewSet(viewsets.ModelViewSet):
    """Protocol Guide ViewSet - 使用 library 統一管理"""
    queryset = ProtocolGuide.objects.all()
    serializer_class = ProtocolGuideSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.viewset_manager = None
        if PROTOCOL_GUIDE_LIBRARY_AVAILABLE and ProtocolGuideViewSetManager:
            self.viewset_manager = ProtocolGuideViewSetManager()
    
    def get_serializer_class(self):
        """根據操作類型選擇合適的序列化器"""
        if self.viewset_manager:
            return self.viewset_manager.get_serializer_class(self.action)
        else:
            if self.action == 'list':
                return ProtocolGuideListSerializer
            return ProtocolGuideSerializer
    
    def perform_create(self, serializer):
        """建立新的 Protocol Guide"""
        if self.viewset_manager:
            return self.viewset_manager.perform_create(serializer)
        else:
            return serializer.save()
    
    def perform_update(self, serializer):
        """更新現有的 Protocol Guide"""
        if self.viewset_manager:
            return self.viewset_manager.perform_update(serializer)
        else:
            return serializer.save()
    
    def perform_destroy(self, instance):
        """刪除 Protocol Guide 時同時刪除對應的向量資料"""
        if self.viewset_manager:
            return self.viewset_manager.perform_destroy(instance)
        else:
            logger.warning("ViewSet Manager 不可用，使用簡化刪除邏輯")
            instance.delete()
    
    def get_queryset(self):
        """支援搜尋和篩選"""
        base_queryset = ProtocolGuide.objects.all()
        
        if self.viewset_manager:
            return self.viewset_manager.get_queryset(base_queryset, self.request.query_params)
        else:
            # 備用實現 - 簡化的篩選
            search = self.request.query_params.get('search', None)
            protocol_name = self.request.query_params.get('protocol_name', None)
            
            if search:
                base_queryset = base_queryset.filter(
                    models.Q(title__icontains=search) |
                    models.Q(content__icontains=search) |
                    models.Q(protocol_name__icontains=search)
                )
            
            if protocol_name:
                base_queryset = base_queryset.filter(protocol_name__icontains=protocol_name)
            
            return base_queryset.order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """獲取統計資料"""
        queryset = self.get_queryset()
        
        if self.viewset_manager:
            return self.viewset_manager.get_statistics_data(queryset)
        else:
            try:
                total_guides = queryset.count()
                protocol_stats = queryset.values('protocol_name').annotate(
                    count=Count('id')
                ).order_by('-count')
                
                return Response({
                    'total_guides': total_guides,
                    'protocol_distribution': list(protocol_stats),
                    'message': '完整統計功能需要 Protocol Guide library 支持'
                }, status=status.HTTP_200_OK)
            except Exception as e:
                logger.error(f"統計資料獲取失敗: {str(e)}")
                return Response({
                    'error': f'統計資料獲取失敗: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# dify_protocol_guide_search 已移至 views/dify_knowledge_views.py


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def protocol_guide_chat(request):
    """Protocol Guide 聊天 API"""
    if PROTOCOL_GUIDE_LIBRARY_AVAILABLE and ProtocolGuideAPIHandler:
        return ProtocolGuideAPIHandler.handle_chat_api(request)
    else:
        return Response({
            'error': 'Protocol Guide Library 未安裝，聊天功能不可用'
        }, status=503)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def protocol_guide_config(request):
    """Protocol Guide 配置 API"""
    if PROTOCOL_GUIDE_LIBRARY_AVAILABLE and ProtocolGuideAPIHandler:
        return ProtocolGuideAPIHandler.handle_config_api(request)
    else:
        return Response({
            'name': 'Protocol Guide System',
            'description': 'Protocol 測試指南系統',
            'version': '1.0.0',
            'features': ['search', 'basic_crud'],
            'library_available': False
        })


# ============= 系統狀態監控 API =============


@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def system_logs(request):
    """
    系統日誌 API - 獲取最近的系統日誌
    """
    try:
        from django.utils import timezone
        import logging
        
        log_type = request.query_params.get('type', 'django')
        lines = int(request.query_params.get('lines', 50))
        
        if log_type == 'django':
            # 獲取 Django 日誌（這裡簡化處理）
            logger_instance = logging.getLogger('django')
            
            # 返回模擬的日誌數據
            logs = [
                f"[{timezone.now().strftime('%Y-%m-%d %H:%M:%S')}] INFO: Django server is running",
                f"[{timezone.now().strftime('%Y-%m-%d %H:%M:%S')}] INFO: Database connection healthy",
                f"[{timezone.now().strftime('%Y-%m-%d %H:%M:%S')}] INFO: API endpoints responding normally"
            ]
        else:
            logs = ["Log type not supported"]
        
        return Response({
            'logs': logs,
            'type': log_type,
            'lines': len(logs),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"系統日誌獲取失敗: {str(e)}")
        return Response({
            'error': f'系統日誌獲取失敗: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============= 簡化版系統狀態監控 API =============

@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def simple_system_status(request):
    """
    簡化版系統狀態監控 API - 使用 library/system_monitoring 模組
    """
    try:
        from django.db import connection
        
        # 使用 library 中的管理員監控器
        if AdminSystemMonitor and create_admin_monitor:
            logger.info("使用 AdminSystemMonitor 進行系統狀態檢查")
            admin_monitor = create_admin_monitor()
            status_dict = admin_monitor.get_simple_status_dict(connection)
            logger.info(f"AdminSystemMonitor 回傳狀態: {status_dict.get('status')}")
            return Response(status_dict, status=status.HTTP_200_OK)
        
        # 如果 library 不可用，使用 library 中的備用實現
        else:
            logger.warning("AdminSystemMonitor library 不可用，使用 library 備用實現")
            
            if get_minimal_fallback_status_dict:
                # 使用 library 中的備用實現
                status_dict = get_minimal_fallback_status_dict(connection)
                return Response(status_dict, status=status.HTTP_200_OK)
            else:
                # 最後的備用方案 - 使用 library 中的緊急備用
                from library.system_monitoring.fallback_monitor import get_minimal_fallback_status_dict
                emergency_status = get_minimal_fallback_status_dict(connection)
                return Response(emergency_status, status=status.HTTP_200_OK)
            
    except Exception as e:
        logger.error(f"Simple system status error: {str(e)}")
        try:
            from django.utils import timezone
            timestamp = timezone.now().isoformat()
        except:
            timestamp = None
        return Response({
            'error': f'系統狀態獲取失敗: {str(e)}',
            'status': 'error',
            'timestamp': timestamp
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)








# ============= 基本系統狀態 API（所有用戶可訪問）=============

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def basic_system_status(request):
    """
    基本系統狀態 API - 所有登入用戶可訪問
    提供基本的系統運行狀態，不包含敏感信息
    
    使用 library/system_monitoring 模組提供的功能
    """
    try:
        # 如果 library 可用，使用新的健康檢查器
        if HealthChecker and create_health_checker:
            from django.db import connection
            
            # 使用新的健康檢查器
            health_checker = create_health_checker()
            health_result = health_checker.perform_basic_health_check(connection)
            
            # 轉換為 API 回應格式
            response_data = health_result.to_dict()
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        else:
            # 備用實現（如果 library 不可用）
            logger.warning("HealthChecker library 不可用，使用 library 備用實現")
            
            from django.db import connection
            
            if get_basic_fallback_status_dict:
                # 使用 library 中的備用實現
                status_dict = get_basic_fallback_status_dict(connection)
                return Response(status_dict, status=status.HTTP_200_OK)
            else:
                # 最後的備用方案 - 使用 library 中的緊急備用
                from library.system_monitoring.fallback_monitor import get_basic_fallback_status_dict
                emergency_status = get_basic_fallback_status_dict(connection)
                return Response(emergency_status, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Basic system status error: {str(e)}")
        return Response({
            'error': f'獲取基本系統狀態失敗: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============= 對話管理 API 端點 =============

@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])  # 支援訪客
def conversation_list(request):
    """
    對話列表 API - 使用 Conversation Management Library
    GET /api/conversations/
    
    支援查詢參數:
    - page: 頁碼 (預設 1)
    - page_size: 每頁大小 (預設 20, 最大 100)
    - chat_type: 聊天類型篩選 (可選)
    """
    try:
        from library.conversation_management import (
            CONVERSATION_MANAGEMENT_AVAILABLE,
            ConversationAPIHandler
        )
        
        if CONVERSATION_MANAGEMENT_AVAILABLE:
            return ConversationAPIHandler.handle_conversation_list_api(request)
        else:
            return Response({
                'success': False,
                'error': 'Conversation Management Library not available'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
    except Exception as e:
        logger.error(f"Conversation list API error: {str(e)}")
        return Response({
            'success': False,
            'error': f'對話列表獲取失敗: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])  # 支援訪客
def conversation_detail(request, conversation_id):
    """
    對話詳情 API - 使用 Conversation Management Library
    GET /api/conversations/{id}/
    
    支援查詢參數:
    - page: 頁碼 (預設 1)
    - page_size: 每頁大小 (預設 50, 最大 100)
    """
    try:
        from library.conversation_management import (
            CONVERSATION_MANAGEMENT_AVAILABLE,
            ConversationAPIHandler
        )
        
        if CONVERSATION_MANAGEMENT_AVAILABLE:
            return ConversationAPIHandler.handle_conversation_detail_api(request, conversation_id)
        else:
            return Response({
                'success': False,
                'error': 'Conversation Management Library not available'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
    except Exception as e:
        logger.error(f"Conversation detail API error: {str(e)}")
        return Response({
            'success': False,
            'error': f'對話詳情獲取失敗: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])  # 支援訪客
def record_conversation(request):
    """
    記錄對話 API - 使用 Conversation Management Library
    POST /api/conversations/record/
    
    預期 payload:
    {
        "session_id": "dify_conv_12345",
        "user_message": "用戶問題",
        "assistant_message": "AI回覆",
        "response_time": 2.3,
        "token_usage": {"total_tokens": 150},
        "metadata": {}
    }
    """
    try:
        from library.conversation_management import (
            CONVERSATION_MANAGEMENT_AVAILABLE,
            ConversationAPIHandler
        )
        
        if CONVERSATION_MANAGEMENT_AVAILABLE:
            return ConversationAPIHandler.handle_record_conversation_api(request)
        else:
            return Response({
                'success': False,
                'error': 'Conversation Management Library not available'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
    except Exception as e:
        logger.error(f"Record conversation API error: {str(e)}")
        return Response({
            'success': False,
            'error': f'對話記錄失敗: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['PATCH'])
@permission_classes([AllowAny])  # 支援訪客
def update_conversation_session(request, session_id):
    """
    更新會話 API - 使用 Conversation Management Library
    PATCH /api/conversations/sessions/{session_id}/
    
    預期 payload:
    {
        "title": "新標題"
    }
    """
    try:
        from library.conversation_management import (
            CONVERSATION_MANAGEMENT_AVAILABLE,
            ConversationAPIHandler
        )
        
        if CONVERSATION_MANAGEMENT_AVAILABLE:
            return ConversationAPIHandler.handle_update_session_api(request, session_id)
        else:
            return Response({
                'success': False,
                'error': 'Conversation Management Library not available'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
    except Exception as e:
        logger.error(f"Update conversation session API error: {str(e)}")
        return Response({
            'success': False,
            'error': f'會話更新失敗: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])  # 支援訪客
def conversation_stats(request):
    """
    對話統計 API - 使用 Conversation Management Library
    GET /api/conversations/stats/
    """
    try:
        from library.conversation_management import (
            CONVERSATION_MANAGEMENT_AVAILABLE,
            ConversationAPIHandler
        )
        
        if CONVERSATION_MANAGEMENT_AVAILABLE:
            return ConversationAPIHandler.handle_conversation_stats_api(request)
        else:
            return Response({
                'success': False,
                'error': 'Conversation Management Library not available'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
    except Exception as e:
        logger.error(f"Conversation stats API error: {str(e)}")
        return Response({
            'success': False,
            'error': f'對話統計獲取失敗: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============= RVT Analytics API 端點 =============

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])  # 支援訪客使用反饋功能
def rvt_analytics_feedback(request):
    """
    RVT Assistant 消息反饋 API - 使用 RVT Analytics Library
    POST /api/rvt-analytics/feedback/
    
    預期 payload:
    {
        "message_id": "uuid-string",
        "is_helpful": true/false
    }
    """
    try:
        if RVT_ANALYTICS_AVAILABLE and handle_feedback_api:
            return handle_feedback_api(request)
        else:
            # 使用備用實現
            logger.warning("RVT Analytics Library 不可用，使用備用反饋處理")
            try:
                import json
                data = json.loads(request.body)
                message_id = data.get('message_id')
                is_helpful = data.get('is_helpful')
                
                if not message_id or is_helpful is None:
                    return JsonResponse({
                        'success': False,
                        'error': 'message_id and is_helpful are required'
                    }, status=400)
                
                # 簡化的備用處理 - 直接更新數據庫
                from api.models import ChatMessage
                try:
                    message = ChatMessage.objects.get(message_id=message_id)
                    message.is_helpful = is_helpful
                    message.save(update_fields=['is_helpful', 'updated_at'])
                    
                    return JsonResponse({
                        'success': True,
                        'message': '反饋已記錄',
                        'fallback': True,
                        'data': {
                            'message_id': message_id,
                            'is_helpful': is_helpful
                        }
                    }, status=200)
                    
                except ChatMessage.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': '消息不存在'
                    }, status=404)
                    
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'備用反饋處理失敗: {str(e)}'
                }, status=500)
            
    except Exception as e:
        logger.error(f"RVT Analytics feedback API error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'反饋處理失敗: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def rvt_analytics_overview(request):
    """
    RVT Analytics 概覽 API - 使用 RVT Analytics Library
    GET /api/rvt-analytics/overview/
    
    Query parameters:
    - days: 統計天數 (default: 30)
    - user_id: 特定用戶ID (admin only)
    """
    try:
        if RVT_ANALYTICS_AVAILABLE and RVTAnalyticsAPIHandler:
            return RVTAnalyticsAPIHandler.handle_analytics_overview_api(request)
        else:
            # 備用實現
            logger.warning("RVT Analytics Library 不可用，使用備用概覽實現")
            try:
                days = int(request.GET.get('days', 30))
                user_id = request.GET.get('user_id')
                
                # 權限檢查
                if user_id and not request.user.is_staff:
                    return JsonResponse({
                        'success': False,
                        'error': '無權限查看其他用戶數據'
                    }, status=403)
                
                # 簡化的統計
                from django.utils import timezone
                from datetime import timedelta
                from api.models import ConversationSession, ChatMessage
                
                start_date = timezone.now() - timedelta(days=days)
                
                # 基本統計
                total_conversations = ConversationSession.objects.filter(
                    created_at__gte=start_date
                ).count()
                
                total_messages = ChatMessage.objects.filter(
                    created_at__gte=start_date,
                    role='assistant'
                ).count()
                
                helpful_count = ChatMessage.objects.filter(
                    created_at__gte=start_date,
                    role='assistant',
                    is_helpful=True
                ).count()
                
                return JsonResponse({
                    'success': True,
                    'fallback': True,
                    'data': {
                        'period': f'{days} 天',
                        'overview': {
                            'total_conversations': total_conversations,
                            'total_messages': total_messages,
                            'helpful_messages': helpful_count
                        }
                    }
                }, status=200)
                
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'備用概覽處理失敗: {str(e)}'
                }, status=500)
            
    except Exception as e:
        logger.error(f"RVT Analytics overview API error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'概覽獲取失敗: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])  # 需要管理員權限，但先設為登入即可
def rvt_analytics_questions(request):
    """
    RVT Analytics 問題分析 API - 使用 RVT Analytics Library
    GET /api/rvt-analytics/questions/
    
    Query parameters:
    - days: 統計天數 (default: 7)
    - category: 問題分類過濾
    """
    try:
        if RVT_ANALYTICS_AVAILABLE and RVTAnalyticsAPIHandler:
            return RVTAnalyticsAPIHandler.handle_question_analysis_api(request)
        else:
            # 備用實現
            logger.warning("RVT Analytics Library 不可用，使用備用問題分析實現")
            try:
                days = int(request.GET.get('days', 7))
                
                # 簡化的問題分析
                from django.utils import timezone
                from datetime import timedelta
                from api.models import ChatMessage
                from collections import Counter
                
                start_date = timezone.now() - timedelta(days=days)
                
                user_messages = ChatMessage.objects.filter(
                    role='user',
                    created_at__gte=start_date
                ).values_list('content', flat=True)
                
                # 簡單的關鍵字統計
                keywords = []
                for message in user_messages:
                    words = message.lower().split()
                    keywords.extend([w for w in words if len(w) > 3])
                
                keyword_counts = Counter(keywords).most_common(10)
                
                return JsonResponse({
                    'success': True,
                    'fallback': True,
                    'data': {
                        'total_questions': len(user_messages),
                        'top_keywords': keyword_counts,
                        'period': f'{days} 天'
                    }
                }, status=200)
                
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'備用問題分析失敗: {str(e)}'
                }, status=500)
            
    except Exception as e:
        logger.error(f"RVT Analytics questions API error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'問題分析失敗: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])  # 需要管理員權限，但先設為登入即可
def rvt_analytics_satisfaction(request):
    """
    RVT Analytics 滿意度分析 API - 使用 RVT Analytics Library
    GET /api/rvt-analytics/satisfaction/
    
    Query parameters:
    - days: 統計天數 (default: 30)
    - detail: 是否包含詳細分析 (true/false)
    """
    try:
        if RVT_ANALYTICS_AVAILABLE and RVTAnalyticsAPIHandler:
            return RVTAnalyticsAPIHandler.handle_satisfaction_analysis_api(request)
        else:
            # 備用實現
            logger.warning("RVT Analytics Library 不可用，使用備用滿意度分析實現")
            try:
                days = int(request.GET.get('days', 30))
                
                # 簡化的滿意度分析
                from django.utils import timezone
                from datetime import timedelta
                from api.models import ChatMessage
                
                start_date = timezone.now() - timedelta(days=days)
                
                assistant_messages = ChatMessage.objects.filter(
                    role='assistant',
                    created_at__gte=start_date
                )
                
                total_messages = assistant_messages.count()
                helpful_messages = assistant_messages.filter(is_helpful=True).count()
                unhelpful_messages = assistant_messages.filter(is_helpful=False).count()
                
                satisfaction_rate = None
                if helpful_messages + unhelpful_messages > 0:
                    satisfaction_rate = helpful_messages / (helpful_messages + unhelpful_messages)
                
                return JsonResponse({
                    'success': True,
                    'fallback': True,
                    'data': {
                        'basic_stats': {
                            'total_messages': total_messages,
                            'helpful_count': helpful_messages,
                            'unhelpful_count': unhelpful_messages,
                            'satisfaction_rate': round(satisfaction_rate, 3) if satisfaction_rate else None
                        },
                        'analysis_period': f'{days} 天'
                    }
                }, status=200)
                
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'備用滿意度分析失敗: {str(e)}'
                }, status=500)
            
    except Exception as e:
        logger.error(f"RVT Analytics satisfaction API error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'滿意度分析失敗: {str(e)}'
        }, status=500)

# ==========================================
# 聊天向量化和聚類分析 API
# ==========================================

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat_vector_search(request):
    """
    聊天消息向量相似度搜索 API
    """
    try:
        if not CHAT_VECTOR_SERVICES_AVAILABLE:
            return JsonResponse({
                'success': False,
                'error': '聊天向量化服務不可用'
            }, status=503)
        
        data = json.loads(request.body)
        query = data.get('query', '').strip()
        limit = min(int(data.get('limit', 10)), 50)  # 最大限制50
        threshold = float(data.get('threshold', 0.7))
        
        if not query:
            return JsonResponse({
                'success': False,
                'error': '查詢文本不能為空'
            }, status=400)
        
        # 執行向量搜索
        results = search_similar_chat_messages(query, limit, threshold)
        
        return JsonResponse({
            'success': True,
            'data': {
                'query': query,
                'results': results,
                'total_found': len(results),
                'search_params': {
                    'limit': limit,
                    'threshold': threshold
                }
            }
        }, status=200)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': '無效的 JSON 數據'
        }, status=400)
    except Exception as e:
        logger.error(f"Chat vector search API error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'向量搜索失敗: {str(e)}'
        }, status=500)

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat_clustering_analysis(request):
    """
    聊天消息聚類分析 API
    """
    try:
        if not CHAT_VECTOR_SERVICES_AVAILABLE:
            return JsonResponse({
                'success': False,
                'error': '聊天聚類服務不可用'
            }, status=503)
        
        data = json.loads(request.body)
        algorithm = data.get('algorithm', 'kmeans').lower()
        
        if algorithm not in ['kmeans', 'dbscan']:
            return JsonResponse({
                'success': False,
                'error': f'不支援的聚類算法: {algorithm}'
            }, status=400)
        
        # 執行聚類分析
        results = perform_auto_clustering(algorithm)
        
        if 'error' in results:
            return JsonResponse({
                'success': False,
                'error': results['error']
            }, status=500)
        
        return JsonResponse({
            'success': True,
            'data': results
        }, status=200)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': '無效的 JSON 數據'
        }, status=400)
    except Exception as e:
        logger.error(f"Chat clustering analysis API error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'聚類分析失敗: {str(e)}'
        }, status=500)

@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chat_clustering_stats(request):
    """
    獲取聊天聚類統計 API
    """
    try:
        if not CHAT_VECTOR_SERVICES_AVAILABLE:
            return JsonResponse({
                'success': False,
                'error': '聊天聚類服務不可用'
            }, status=503)
        
        # 獲取聚類統計
        cluster_categories = get_cluster_categories()
        
        # 獲取向量服務統計
        vector_service = get_chat_vector_service()
        embedding_stats = vector_service.get_embedding_stats()
        
        return JsonResponse({
            'success': True,
            'data': {
                'cluster_categories': cluster_categories,
                'embedding_stats': embedding_stats
            }
        }, status=200)
        
    except Exception as e:
        logger.error(f"Chat clustering stats API error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'獲取聚類統計失敗: {str(e)}'
        }, status=500)

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def vectorize_chat_message(request):
    """
    對單個聊天消息進行向量化 API
    """
    try:
        if not CHAT_VECTOR_SERVICES_AVAILABLE:
            return JsonResponse({
                'success': False,
                'error': '聊天向量化服務不可用'
            }, status=503)
        
        data = json.loads(request.body)
        chat_message_id = data.get('chat_message_id')
        content = data.get('content', '').strip()
        conversation_id = data.get('conversation_id')
        
        if not chat_message_id:
            return JsonResponse({
                'success': False,
                'error': 'chat_message_id 是必需的'
            }, status=400)
        
        if not content:
            return JsonResponse({
                'success': False,
                'error': '消息內容不能為空'
            }, status=400)
        
        # 生成向量
        success = generate_message_vector(chat_message_id, content, conversation_id)
        
        if success:
            # 嘗試分類
            from library.rvt_analytics.question_classifier import classify_question
            classification = classify_question(
                content, 
                chat_message_id=chat_message_id, 
                use_vector_classification=True
            )
            
            return JsonResponse({
                'success': True,
                'data': {
                    'chat_message_id': chat_message_id,
                    'vectorized': True,
                    'classification': classification
                }
            }, status=200)
        else:
            return JsonResponse({
                'success': False,
                'error': '向量化處理失敗'
            }, status=500)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': '無效的 JSON 數據'
        }, status=400)
    except Exception as e:
        logger.error(f"Vectorize chat message API error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'向量化失敗: {str(e)}'
        }, status=500)

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def intelligent_question_classify(request):
    """
    智能問題分類 API（整合向量聚類）
    """
    try:
        data = json.loads(request.body)
        question_text = data.get('question', '').strip()
        chat_message_id = data.get('chat_message_id')
        use_vector_classification = data.get('use_vector_classification', True)
        use_ai_classification = data.get('use_ai_classification', False)
        
        if not question_text:
            return JsonResponse({
                'success': False,
                'error': '問題文本不能為空'
            }, status=400)
        
        # 執行智能分類
        from library.rvt_analytics.question_classifier import classify_question
        
        classification_result = classify_question(
            question_text=question_text,
            chat_message_id=chat_message_id,
            use_vector_classification=use_vector_classification,
            use_ai_classification=use_ai_classification
        )
        
        # 如果啟用向量分類，也提供相似問題
        similar_questions = []
        if use_vector_classification and CHAT_VECTOR_SERVICES_AVAILABLE:
            similar_questions = search_similar_chat_messages(
                question_text, 
                limit=5, 
                threshold=0.6
            )
        
        return JsonResponse({
            'success': True,
            'data': {
                'question': question_text,
                'classification': classification_result,
                'similar_questions': similar_questions,
                'services_available': {
                    'vector_classification': CHAT_VECTOR_SERVICES_AVAILABLE,
                    'traditional_rules': True,
                    'ai_classification': use_ai_classification
                }
            }
        }, status=200)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': '無效的 JSON 數據'
        }, status=400)
    except Exception as e:
        logger.error(f"Intelligent question classify API error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'智能分類失敗: {str(e)}'
        }, status=500)


# ============= ContentImage 圖片管理 API =============

@method_decorator(csrf_exempt, name='dispatch')
class ContentImageViewSet(viewsets.ModelViewSet):
    """通用內容圖片管理 ViewSet"""
    queryset = ContentImage.objects.all()
    serializer_class = ContentImageSerializer
    permission_classes = [permissions.AllowAny]  # 🔧 改為允許所有用戶言取圖片
    
    def get_queryset(self):
        """根據查詢參數過濾圖片"""
        queryset = super().get_queryset()
        content_type = self.request.query_params.get('content_type')
        content_id = self.request.query_params.get('content_id')
        filename = self.request.query_params.get('filename')
        
            # 🔧 改善檔名搜索邏輯 - 支持更靈活的匹配
        if filename:
            from django.db.models import Q
            
            # 1. 精確匹配
            exact_match = Q(filename=filename)
            
            # 2. 包含匹配
            contains_match = Q(filename__icontains=filename)
            
            # 3. 如果查詢的是數字串，可能是檔名的一部分，搜索包含該數字串的所有檔案
            clean_filename = filename.replace('.png', '').replace('.jpg', '').replace('.jpeg', '').replace('.gif', '').replace('.bmp', '').replace('.webp', '')
            if clean_filename.isdigit() and len(clean_filename) > 5:  # 長數字串
                number_match = Q(filename__icontains=clean_filename)
            else:
                number_match = Q(pk=-1)
            
            # 4. 如果查詢的是 jenkins 相關，搜索包含 jenkins 的
            if 'jenkins' in filename.lower():
                jenkins_match = Q(filename__icontains='jenkins')
            else:
                jenkins_match = Q(pk=-1)
            
            # 5. 如果查詢的是 kisspng 相關，搜索包含相似關鍵詞的
            if 'kisspng' in filename.lower() or 'jenkins' in filename.lower():
                kisspng_match = Q(filename__istartswith='kisspng-') & Q(filename__icontains='jenkins')
            else:
                kisspng_match = Q(pk=-1)
            
            # 6. 反向匹配：檔名較長，查詢較短時，檢查資料庫中的檔名是否包含查詢字串
            reverse_match = Q(pk=-1)  # 預設空條件
            for field in ['filename']:
                # 只對有意義的長度進行反向匹配
                if len(filename) > 10:
                    reverse_match = reverse_match | Q(**{f'{field}__icontains': filename})
            
            # 組合所有條件（OR 關係）
            queryset = queryset.filter(exact_match | contains_match | number_match | jenkins_match | kisspng_match | reverse_match)
        
        if content_type and content_id:
            if content_type == 'rvt-guide':
                queryset = queryset.filter(rvt_guide_id=content_id)
            else:
                # 使用通用的 content_type 和 object_id 過濾
                from django.contrib.contenttypes.models import ContentType
                try:
                    ct = ContentType.objects.get(model=content_type.replace('-', ''))
                    queryset = queryset.filter(content_type=ct, object_id=content_id)
                except ContentType.DoesNotExist:
                    queryset = queryset.none()
        
        return queryset.filter(is_active=True).order_by('display_order')
    
    def perform_create(self, serializer):
        """處理圖片上傳"""
        uploaded_file = self.request.FILES.get('image')
        content_type = self.request.data.get('content_type')
        content_id = self.request.data.get('content_id')
        title = self.request.data.get('title', '')
        description = self.request.data.get('description', '')
        
        if not uploaded_file:
            raise ValidationError("請提供圖片檔案")
        
        if not content_type or not content_id:
            raise ValidationError("請提供內容類型和內容 ID")
        
        # 檔案驗證
        self._validate_image_file(uploaded_file)
        
        # 根據內容類型獲取對象
        content_object = self._get_content_object(content_type, content_id)
        
        # 創建圖片記錄
        try:
            image = ContentImage.create_from_upload(
                content_object=content_object,
                uploaded_file=uploaded_file,
                title=title,
                description=description
            )
            
            # 更新關聯的向量資料（如果是 RVT Guide）
            if content_type == 'rvt-guide':
                self._update_guide_vectors(content_object)
            
            serializer.instance = image
            
        except Exception as e:
            logger.error(f"圖片創建失敗: {str(e)}")
            raise ValidationError(f"圖片上傳失敗: {str(e)}")
    
    def _validate_image_file(self, file):
        """驗證圖片檔案"""
        max_size = 2 * 1024 * 1024  # 2MB
        allowed_types = ['image/jpeg', 'image/png', 'image/gif']
        
        if file.size > max_size:
            raise ValidationError(f"檔案大小不能超過 {max_size // (1024*1024)}MB")
        
        if file.content_type not in allowed_types:
            raise ValidationError(f"不支援的檔案類型: {file.content_type}")
    
    def _get_content_object(self, content_type, content_id):
        """根據內容類型獲取對象"""
        if content_type == 'rvt-guide':
            try:
                return RVTGuide.objects.get(id=content_id)
            except RVTGuide.DoesNotExist:
                raise ValidationError("指定的 RVT Guide 不存在")
        elif content_type == 'know-issue':
            try:
                return KnowIssue.objects.get(id=content_id)
            except KnowIssue.DoesNotExist:
                raise ValidationError("指定的 Know Issue 不存在")
        else:
            raise ValidationError(f"不支援的內容類型: {content_type}")
    
    def _update_guide_vectors(self, rvt_guide):
        """更新 RVT Guide 的向量資料"""
        try:
            from library.rvt_guide.vector_service import RVTGuideVectorService
            vector_service = RVTGuideVectorService()
            vector_service.generate_and_store_vector(rvt_guide, action='update')
        except Exception as e:
            logger.warning(f"向量更新失敗: {str(e)}")
    
    @action(detail=False, methods=['post'], url_path='batch-upload')
    def batch_upload(self, request):
        """批量上傳圖片"""
        content_type = request.data.get('content_type')
        content_id = request.data.get('content_id')
        uploaded_files = request.FILES.getlist('images')
        
        if not uploaded_files:
            return Response({'error': '請提供至少一張圖片'}, status=400)
        
        if not content_type or not content_id:
            return Response({'error': '請提供內容類型和內容 ID'}, status=400)
        
        try:
            content_object = self._get_content_object(content_type, content_id)
        except ValidationError as e:
            return Response({'error': str(e)}, status=404)
        
        created_images = []
        errors = []
        
        for uploaded_file in uploaded_files:
            try:
                self._validate_image_file(uploaded_file)
                image = ContentImage.create_from_upload(
                    content_object=content_object,
                    uploaded_file=uploaded_file
                )
                created_images.append(ContentImageSerializer(image).data)
            except Exception as e:
                errors.append(f"{uploaded_file.name}: {str(e)}")
        
        # 更新向量資料
        if created_images and content_type == 'rvt-guide':
            self._update_guide_vectors(content_object)
        
        return Response({
            'success': len(created_images),
            'errors': errors,
            'created_images': created_images
        })
    
    @action(detail=True, methods=['post'])
    def set_primary(self, request, pk=None):
        """設定為主要圖片"""
        image = self.get_object()
        
        # 清除同內容的其他主要圖片
        if image.rvt_guide:
            ContentImage.objects.filter(rvt_guide=image.rvt_guide, is_primary=True).update(is_primary=False)
        else:
            ContentImage.objects.filter(
                content_type=image.content_type, 
                object_id=image.object_id, 
                is_primary=True
            ).update(is_primary=False)
        
        # 設定當前圖片為主要圖片
        image.is_primary = True
        image.save()
        
        return Response({'success': True, 'message': '主要圖片設定成功'})
    
    @action(detail=False, methods=['post'])
    def reorder(self, request):
        """重新排序圖片"""
        image_ids = request.data.get('image_ids', [])
        content_type = request.data.get('content_type')
        content_id = request.data.get('content_id')
        
        if not image_ids:
            return Response({'error': '請提供圖片 ID 列表'}, status=400)
        
        try:
            for index, image_id in enumerate(image_ids, 1):
                ContentImage.objects.filter(id=image_id).update(display_order=index)
            
            return Response({'success': True, 'message': '排序更新成功'})
        except Exception as e:
            return Response({'error': str(e)}, status=400)


# 為 RVTGuideViewSet 添加圖片相關的 actions
# 這些方法可以添加到現有的 RVTGuideViewSet 中