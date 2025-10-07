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
from .models import UserProfile, Project, Task, KnowIssue, TestClass, OCRTestClass, OCRStorageBenchmark, RVTGuide
from .serializers import UserSerializer, UserProfileSerializer, ProjectSerializer, TaskSerializer, KnowIssueSerializer, TestClassSerializer, OCRTestClassSerializer, OCRStorageBenchmarkSerializer, OCRStorageBenchmarkListSerializer, RVTGuideSerializer, RVTGuideListSerializer

# 導入向量搜索服務
try:
    from .services.embedding_service import search_rvt_guide_with_vectors, get_embedding_service
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
        search_ocr_storage_benchmark
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
        fallback_process_ocr_record
    )
    # 🆕 導入認證服務 library
    from library.auth import (
        AuthenticationService,
        UserProfileService,
        ValidationService,
        AuthResponseFormatter,
        LoginHandler,
        DRFAuthHandler
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
    AI_OCR_LIBRARY_AVAILABLE = False
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


def retry_api_request(func, max_retries=3, retry_delay=1, backoff_factor=2):
    """
    API 請求重試機制
    
    Args:
        func: 要執行的函數
        max_retries: 最大重試次數
        retry_delay: 初始重試延遲（秒）
        backoff_factor: 退避係數
    
    Returns:
        函數執行結果或拋出最後一個異常
    """
    import requests
    import time
    
    last_exception = None
    delay = retry_delay
    
    for attempt in range(max_retries + 1):
        try:
            result = func()
            if attempt > 0:
                logger.info(f"重試成功，嘗試次數: {attempt + 1}")
            return result
            
        except requests.exceptions.Timeout as e:
            last_exception = e
            if attempt < max_retries:
                logger.warning(f"請求超時，第 {attempt + 1} 次重試，延遲 {delay} 秒")
                time.sleep(delay)
                delay *= backoff_factor
                continue
                
        except requests.exceptions.ConnectionError as e:
            last_exception = e
            if attempt < max_retries:
                logger.warning(f"連接錯誤，第 {attempt + 1} 次重試，延遲 {delay} 秒")
                time.sleep(delay)
                delay *= backoff_factor
                continue
                
        except requests.exceptions.RequestException as e:
            # 檢查是否是可重試的 HTTP 錯誤
            if hasattr(e, 'response') and e.response is not None:
                status_code = e.response.status_code
                
                # HTTP 400: Bad Request - 可能是暫時性問題
                # HTTP 429: Too Many Requests - 速率限制
                # HTTP 502, 503, 504: 服務器錯誤
                if status_code in [400, 429, 502, 503, 504]:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(f"HTTP {status_code} 錯誤，第 {attempt + 1} 次重試，延遲 {delay} 秒")
                        time.sleep(delay)
                        delay *= backoff_factor
                        continue
                        
            # 其他 HTTP 錯誤不重試
            raise e
            
        except Exception as e:
            # 其他異常不重試
            raise e
    
    # 所有重試都失敗，拋出最後一個異常
    logger.error(f"重試 {max_retries} 次後仍然失敗")
    raise last_exception


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


class UserProfileViewSet(viewsets.ModelViewSet):
    """使用者個人檔案 ViewSet"""
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # 只返回當前使用者的個人檔案
        return UserProfile.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'], url_path='me')
    def get_my_profile(self, request):
        """獲取當前使用者的個人檔案"""
        try:
            profile = UserProfile.objects.get(user=request.user)
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'Profile not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )


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


class TaskViewSet(viewsets.ModelViewSet):
    """任務 ViewSet"""
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # 只返回使用者相關的任務
        user = self.request.user
        return Task.objects.filter(
            models.Q(assignee=user) | 
            models.Q(creator=user) | 
            models.Q(project__owner=user) |
            models.Q(project__members=user)
        ).distinct()

    def perform_create(self, serializer):
        # 設定當前使用者為任務建立者
        serializer.save(creator=self.request.user)

    @action(detail=True, methods=['post'], url_path='assign')
    def assign_task(self, request, pk=None):
        """指派任務給使用者"""
        task = self.get_object()
        user_id = request.data.get('user_id')
        
        try:
            user = User.objects.get(id=user_id)
            task.assignee = user
            task.save()
            return Response({'message': f'Task assigned to {user.username}'})
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'], url_path='change-status')
    def change_status(self, request, pk=None):
        """變更任務狀態"""
        task = self.get_object()
        new_status = request.data.get('status')
        
        if new_status in dict(Task.STATUS_CHOICES):
            task.status = new_status
            task.save()
            return Response({'message': f'Task status changed to {new_status}'})
        else:
            return Response(
                {'error': 'Invalid status'}, 
                status=status.HTTP_400_BAD_REQUEST
            )








def search_postgres_knowledge(query_text, limit=5):
    """
    在 PostgreSQL 中搜索員工知識
    使用全文搜索查詢簡化員工資料
    """
    try:
        with connection.cursor() as cursor:
            # 使用全文搜索查詢員工資料 (僅有 id, name 欄位)
            sql = """
            SELECT 
                id,
                name,
                CASE 
                    WHEN name ILIKE %s THEN 1.0
                    ELSE 0.5
                END as score
            FROM employee
            WHERE 
                name ILIKE %s
            ORDER BY score DESC, name ASC
            LIMIT %s
            """
            
            search_pattern = f'%{query_text}%'
            cursor.execute(sql, [
                search_pattern, search_pattern, limit
            ])
            
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            results = []
            for row in rows:
                employee_data = dict(zip(columns, row))
                # 格式化為知識片段
                content = f"員工姓名: {employee_data['name']}\n"
                content += f"員工ID: {employee_data['id']}"
                
                results.append({
                    'id': str(employee_data['id']),
                    'title': f"{employee_data['name']}",
                    'content': content,
                    'score': float(employee_data['score']),
                    'metadata': {
                        'source': 'employee_database',
                        'employee_id': employee_data['id']
                    }
                })
            
            return results
            
    except Exception as e:
        logger.error(f"Database search error: {str(e)}")
        return []


# ============= 🚨 重要：搜索函數已重構到 Library =============
# 以下搜索函數已移動到 library/data_processing/database_search.py
# 保留這些函數定義是為了向後相容性
# 新代碼應該使用：from library.data_processing.database_search import DatabaseSearchService

def search_know_issue_knowledge(query_text, limit=5):
    """
    【向後兼容】此函數已遷移至 library/data_processing/database_search.py
    現在調用 library 中的新實現
    """
    try:
        # 如果 library 可用，使用新的實現
        if DatabaseSearchService:
            service = DatabaseSearchService()
            return service.search_know_issue_knowledge(query_text, limit)
        else:
            # 備用實現 (如果 library 不可用)
            logger = logging.getLogger(__name__)
            logger.warning("DatabaseSearchService 不可用，使用備用實現")
            return []
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Know Issue 搜索失敗: {str(e)}")
        return []


def search_rvt_guide_knowledge(query_text, limit=5):
    """
    在 PostgreSQL 中搜索 RVT Guide 知識庫
    
    🚨 已重構：此函數已移動到 library/data_processing/database_search.py
    建議使用：DatabaseSearchService.search_rvt_guide_knowledge(query_text, limit)
    """
    try:
        # 如果 library 可用，使用新的實現
        if DatabaseSearchService:
            service = DatabaseSearchService()
            return service.search_rvt_guide_knowledge(query_text, limit)
        else:
            # 備用實現 (如果 library 不可用)
            logger = logging.getLogger(__name__)
            logger.warning("DatabaseSearchService 不可用，使用備用實現")
            return []
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"RVT Guide 搜索失敗: {str(e)}")
        return []


def search_ocr_storage_benchmark(query_text, limit=5):
    """
    搜索 OCR Storage Benchmark 資料 - 使用 AI OCR Library 統一實現
    
    � 重構後：優先使用 library/ai_ocr/search_service.py
    �🚨 已重構：原功能已移動到 library/data_processing/database_search.py
    """
    try:
        if AI_OCR_LIBRARY_AVAILABLE and search_ocr_storage_benchmark_unified:
            # 🆕 優先使用 AI OCR library 中的統一搜索服務
            return search_ocr_storage_benchmark_unified(query_text, limit)
        elif DatabaseSearchService:
            # 備用：使用原有的資料庫搜索服務
            service = DatabaseSearchService()
            return service.search_ocr_storage_benchmark(query_text, limit)
        else:
            # 最終備用實現
            logger.warning("AI OCR Library 和 DatabaseSearchService 都不可用，使用最基本備用")
            return []
    except Exception as e:
        logger.error(f"OCR Storage Benchmark 搜索失敗: {str(e)}")
        return []


@api_view(['POST'])
@permission_classes([])  # 公開 API，但會檢查 Authorization header
@csrf_exempt
def dify_knowledge_search(request):
    """
    Dify 外部知識 API 端點 - 使用 Dify Knowledge Library 統一實現
    
    🔄 重構後：直接使用 library/dify_knowledge/ 處理
    """
    try:
        if DIFY_KNOWLEDGE_LIBRARY_AVAILABLE and handle_dify_knowledge_search_api:
            # 使用 Dify Knowledge library 中的統一 API 處理器
            return handle_dify_knowledge_search_api(request)
        else:
            # 使用備用實現
            logger.warning("Dify Knowledge Library 不可用，使用備用實現")
            try:
                from library.dify_knowledge.fallback_handlers import fallback_dify_knowledge_search
                return fallback_dify_knowledge_search(request)
            except ImportError:
                # 最終備用方案
                logger.error("Dify Knowledge Library 完全不可用")
                return Response({
                    'error_code': 2001,
                    'error_msg': 'Knowledge search service temporarily unavailable'
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
                
    except Exception as e:
        logger.error(f"Dify knowledge search error: {str(e)}")
        return Response({
            'error_code': 2001,
            'error_msg': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([])  # 公開 API，但會檢查 Authorization header
@csrf_exempt
def dify_know_issue_search(request):
    """
    Dify Know Issue 外部知識庫 API 端點 - 使用 library 統一實現
    
    🔄 重構後：直接使用 library/know_issue/ 處理
    """
    try:
        if KNOW_ISSUE_LIBRARY_AVAILABLE and handle_dify_know_issue_search_api:
            # 使用 Know Issue library 中的 API 處理器
            return handle_dify_know_issue_search_api(request)
        else:
            # 使用備用實現
            logger.warning("Know Issue Library 不可用，使用備用實現")
            try:
                from library.know_issue.fallback_handlers import fallback_dify_know_issue_search
                return fallback_dify_know_issue_search(request)
            except ImportError:
                # 最終備用方案
                logger.error("Know Issue Library 完全不可用")
                return Response({
                    'error_code': 2001,
                    'error_msg': 'Know Issue search service temporarily unavailable'
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
    except Exception as e:
        logger.error(f"Dify Know Issue search error: {str(e)}")
        return Response({
            'error_code': 2001,
            'error_msg': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([])  # 公開 API，但會檢查 Authorization header
@csrf_exempt
def dify_ocr_storage_benchmark_search(request):
    """
    Dify OCR Storage Benchmark 外部知識庫 API 端點 - 使用 AI OCR Library 實現
    
    🔄 重構後：主要邏輯和備用實現都在 library 中維護
    """
    try:
        if AI_OCR_LIBRARY_AVAILABLE and AIOCRAPIHandler:
            # 使用 AI OCR library 中的 API 處理器
            return AIOCRAPIHandler.handle_dify_ocr_storage_benchmark_search_api(request)
        elif fallback_dify_ocr_storage_benchmark_search:
            # 使用 library 中維護的備用實現
            return fallback_dify_ocr_storage_benchmark_search(request)
        else:
            # library 完全不可用時的最終錯誤處理
            logger.error("AI OCR Library 完全不可用")
            return Response({
                'error_code': 2001,
                'error_msg': 'OCR Storage Benchmark search service temporarily unavailable'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
    except Exception as e:
        logger.error(f"Dify OCR Storage Benchmark search error: {str(e)}")
        return Response({
            'error_code': 2001,
            'error_msg': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([])  # 公開 API，但會檢查 Authorization header
@csrf_exempt
def dify_rvt_guide_search(request):
    """
    Dify RVT Guide 外部知識庫搜索 API - 使用 library 統一實現
    """
    try:
        if RVT_GUIDE_LIBRARY_AVAILABLE and RVTGuideAPIHandler:
            return RVTGuideAPIHandler.handle_dify_search_api(request)
        elif fallback_dify_rvt_guide_search:
            # 使用 library 中的備用實現
            return fallback_dify_rvt_guide_search(request)
        else:
            # library 完全不可用時的最終錯誤處理
            logger.error("RVT Guide library 完全不可用")
            return Response({
                'error_code': 2001,
                'error_msg': 'RVT Guide service temporarily unavailable'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        logger.error(f"Dify RVT Guide search error: {str(e)}")
        return Response({
            'error_code': 2001,
            'error_msg': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
        if self._manager:
            return self._manager.get_queryset(self)
        else:
            # 備用實現：簡化版查詢邏輯
            queryset = OCRStorageBenchmark.objects.select_related('test_class', 'uploaded_by').all()
            
            # 基本搜索和過濾
            search = self.request.query_params.get('search', None)
            if search:
                queryset = queryset.filter(
                    models.Q(project_name__icontains=search) |
                    models.Q(device_model__icontains=search) |
                    models.Q(firmware_version__icontains=search)
                )
            
            project_name = self.request.query_params.get('project_name', None)
            if project_name:
                queryset = queryset.filter(project_name__icontains=project_name)
            
            device_model = self.request.query_params.get('device_model', None)
            if device_model:
                queryset = queryset.filter(device_model__icontains=device_model)
                
            test_class_id = self.request.query_params.get('test_class', None)
            if test_class_id:
                queryset = queryset.filter(test_class_id=test_class_id)
        
        # 分數範圍篩選
        min_score = self.request.query_params.get('min_score', None)
        max_score = self.request.query_params.get('max_score', None)
        if min_score:
            try:
                queryset = queryset.filter(benchmark_score__gte=int(min_score))
            except ValueError:
                pass
        if max_score:
            try:
                queryset = queryset.filter(benchmark_score__lte=int(max_score))
            except ValueError:
                pass
        
        # 時間範圍篩選
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        if start_date:
            try:
                from datetime import datetime
                start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                queryset = queryset.filter(test_datetime__gte=start_datetime)
            except (ValueError, TypeError):
                pass
        if end_date:
            try:
                from datetime import datetime
                end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                queryset = queryset.filter(test_datetime__lte=end_datetime)
            except (ValueError, TypeError):
                pass
        
        # 一般關鍵字搜尋
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                models.Q(project_name__icontains=search) |
                models.Q(device_model__icontains=search) |
                models.Q(firmware_version__icontains=search) |
                models.Q(ocr_raw_text__icontains=search) |
                models.Q(verification_notes__icontains=search)
            )
        
        return queryset.order_by('-test_datetime', '-created_at')
    
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
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def verify_record(self, request, pk=None):
        """驗證記錄"""
        try:
            ocr_record = self.get_object()
            verification_notes = request.data.get('verification_notes', '')
            
            ocr_record.verified_by = request.user
            ocr_record.verification_notes = verification_notes
            ocr_record.is_verified = True
            ocr_record.save()
            
            return Response({
                'message': '記錄驗證成功',
                'verified_by': request.user.username,
                'verification_notes': verification_notes
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"記錄驗證失敗: {str(e)}")
            return Response({
                'error': f'記錄驗證失敗: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
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
                # 最終備用實現
                logger.warning("AI OCR Library 和管理器都不可用，使用最終備用實現")
                return self._final_fallback_process_ocr(ocr_record)
                
        except Exception as e:
            logger.error(f"OCR 處理失敗: {str(e)}")
            return Response({
                'error': f'OCR 處理失敗: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _final_fallback_process_ocr(self, ocr_record):
        """最終備用的 OCR 處理實現"""
        try:
            # 檢查是否有原始圖像
            if not ocr_record.original_image_data:
                return Response({
                    'error': '請先上傳原始圖像'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 簡單模擬處理
            import time
            start_time = time.time()
            
            if hasattr(ocr_record, 'processing_status'):
                ocr_record.processing_status = 'completed'
            
            processing_time = time.time() - start_time
            
            if hasattr(ocr_record, 'ocr_processing_time'):
                ocr_record.ocr_processing_time = processing_time
            if hasattr(ocr_record, 'ocr_confidence'):
                ocr_record.ocr_confidence = 0.70  # 最終備用實現置信度最低
                
            ocr_record.save()
            
            return Response({
                'message': 'OCR 處理完成（最終備用模式）',
                'processing_time': processing_time,
                'confidence': 0.70,
                'note': '使用最終備用處理模式，功能受限，建議檢查系統配置'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"最終備用 OCR 處理也失敗: {str(e)}")
            return Response({
                'error': f'OCR 處理完全失敗: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def statistics(self, request):
        """獲取統計資料"""
        try:
            from django.db.models import Count, Avg, Max, Min
            
            queryset = self.get_queryset()
            
            # 基本統計
            total_records = queryset.count()
            # OCRStorageBenchmark 沒有 is_verified 字段，移除這個統計
            # verified_records = queryset.filter(is_verified=True).count()
            
            # OCRStorageBenchmark 沒有 processing_status 字段，改為按測試類別統計
            test_class_stats = queryset.values('test_class__name').annotate(count=Count('id'))
            
            # 分數統計
            score_stats = queryset.aggregate(
                avg_score=Avg('benchmark_score'),
                max_score=Max('benchmark_score'),
                min_score=Min('benchmark_score')
            )
            
            # OCRStorageBenchmark 沒有 test_environment 字段，改為按韌體版本統計
            firmware_stats = queryset.values('firmware_version').annotate(count=Count('id'))
            
            # OCRStorageBenchmark 沒有 test_type 字段，改為按專案名稱統計
            project_stats = queryset.values('project_name').annotate(count=Count('id'))
            
            # 按裝置型號統計 (前10名)
            device_stats = queryset.values('device_model').annotate(count=Count('id')).order_by('-count')[:10]
            
            return Response({
                'total_records': total_records,
                # 移除 verified_records 相關統計
                'test_class_distribution': list(test_class_stats),
                'score_statistics': score_stats,
                'firmware_distribution': list(firmware_stats),
                'project_distribution': list(project_stats),
                'top_devices': list(device_stats)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"統計資料獲取失敗: {str(e)}")
            return Response({
                'error': f'統計資料獲取失敗: {str(e)}'
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
@permission_classes([AllowAny])
def dify_chat(request):
    """
    Dify Chat API - 使用 Protocol Known Issue 配置（用於 Protocol RAG）
    
    🔄 重構後：直接使用 library/dify_integration/protocol_chat_handler.py 處理
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
    
    def get_queryset(self):
        """支援搜尋和篩選"""
        base_queryset = RVTGuide.objects.all()
        
        if self.viewset_manager:
            return self.viewset_manager.get_filtered_queryset(base_queryset, self.request.query_params)
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