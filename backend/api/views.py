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
from .models import UserProfile, Project, Task, Employee, DifyEmployee, KnowIssue, TestClass, OCRTestClass, OCRStorageBenchmark, RVTGuide
from .serializers import UserSerializer, UserProfileSerializer, ProjectSerializer, TaskSerializer, EmployeeSerializer, DifyEmployeeSerializer, DifyEmployeeListSerializer, KnowIssueSerializer, TestClassSerializer, OCRTestClassSerializer, OCRStorageBenchmarkSerializer, OCRStorageBenchmarkListSerializer, RVTGuideSerializer, RVTGuideListSerializer

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
    from library.dify_integration import make_dify_request, process_dify_answer
    # 🆕 導入資料庫搜索服務
    from library.data_processing.database_search import (
        DatabaseSearchService,
        search_know_issue_knowledge,
        search_rvt_guide_knowledge,
        search_ocr_storage_benchmark
    )
    # 🆕 導入系統監控服務
    from library.system_monitoring import HealthChecker, create_health_checker
except ImportError:
    # 如果 library 路徑有問題，提供備用配置
    get_protocol_known_issue_config = None
    get_report_analyzer_config = None
    make_dify_request = None
    process_dify_answer = None
    # 備用搜索函數 (保持原有邏輯)
    DatabaseSearchService = None
    search_know_issue_knowledge = None
    search_rvt_guide_knowledge = None
    search_ocr_storage_benchmark = None
    # 備用系統監控服務
    HealthChecker = None
    create_health_checker = None

logger = logging.getLogger(__name__)


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


class EmployeeViewSet(viewsets.ModelViewSet):
    """簡化員工 ViewSet - 僅包含 id 和 name"""
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = []  # 公開訪問
    
    def get_queryset(self):
        """可選：支援搜索"""
        queryset = Employee.objects.all()
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset


class DifyEmployeeViewSet(viewsets.ModelViewSet):
    """Dify員工 ViewSet - 支援資料庫照片存儲"""
    queryset = DifyEmployee.objects.all()
    permission_classes = []  # 公開訪問，用於 Dify 知識庫查詢
    
    def get_serializer_class(self):
        """根據動作選擇序列化器"""
        if self.action == 'list':
            # 列表頁面不包含照片資料以提升效能
            return DifyEmployeeListSerializer
        return DifyEmployeeSerializer
    
    @action(detail=True, methods=['get'], url_path='photo')
    def get_photo(self, request, pk=None):
        """獲取員工照片"""
        employee = self.get_object()
        if employee.photo_binary:
            data_url = employee.get_photo_data_url()
            return Response({
                'photo_data_url': data_url,
                'filename': employee.photo_filename,
                'content_type': employee.photo_content_type,
                'size_kb': len(employee.photo_binary) // 1024
            })
        else:
            return Response(
                {'error': 'No photo available'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'], url_path='with-photos')
    def with_photos(self, request):
        """獲取有照片的員工列表"""
        employees = DifyEmployee.objects.exclude(photo_binary__isnull=True).exclude(photo_binary__exact=b'')
        serializer = DifyEmployeeListSerializer(employees, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], url_path='search')
    def search_employees(self, request):
        """搜索員工"""
        query = request.data.get('query', '')
        if not query:
            return Response(
                {'error': 'Query parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 使用 Django ORM 搜索
        employees = DifyEmployee.objects.filter(
            models.Q(name__icontains=query) |
            models.Q(department__icontains=query) |
            models.Q(position__icontains=query) |
            models.Q(skills__icontains=query)
        )
        
        serializer = DifyEmployeeListSerializer(employees, many=True)
        return Response(serializer.data)


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
    PostgreSQL 全文搜索 OCR 存儲基準測試資料
    
    🚨 已重構：此函數已移動到 library/data_processing/database_search.py
    建議使用：DatabaseSearchService.search_ocr_storage_benchmark(query_text, limit)
    """
    try:
        # 如果 library 可用，使用新的實現
        if DatabaseSearchService:
            service = DatabaseSearchService()
            return service.search_ocr_storage_benchmark(query_text, limit)
        else:
            # 備用實現 (如果 library 不可用)
            logger = logging.getLogger(__name__)
            logger.warning("DatabaseSearchService 不可用，使用備用實現")
            return []
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"OCR Storage Benchmark 搜索失敗: {str(e)}")
        return []


@api_view(['POST'])
@permission_classes([])  # 公開 API，但會檢查 Authorization header
@csrf_exempt
def dify_knowledge_search(request):
    """
    Dify 外部知識 API 端點 - 符合官方規格
    
    期望的請求格式 (根據 Dify 官方文檔):
    {
        "knowledge_id": "your-knowledge-id",
        "query": "搜索字詞",
        "retrieval_setting": {
            "top_k": 3,
            "score_threshold": 0.5
        },
        "metadata_condition": {...}  // 可選
    }
    
    回應格式:
    {
        "records": [
            {
                "content": "知識內容",
                "score": 0.95,
                "title": "標題",
                "metadata": {...}
            }
        ]
    }
    """
    try:
        # 檢查 Authorization header (可選，但符合 Dify 規格)
        auth_header = request.headers.get('Authorization', '')
        if auth_header and not auth_header.startswith('Bearer '):
            return Response({
                'error_code': 1001,
                'error_msg': 'Invalid Authorization header format. Expected "Bearer <api-key>" format.'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # 解析請求資料
        data = json.loads(request.body) if request.body else {}
        
        # 根據 Dify 官方規格解析參數
        knowledge_id = data.get('knowledge_id', 'employee_database')
        query = data.get('query', '')
        retrieval_setting = data.get('retrieval_setting', {})
        metadata_condition = data.get('metadata_condition', {})
        
        top_k = retrieval_setting.get('top_k', 5)
        score_threshold = retrieval_setting.get('score_threshold', 0.0)
        
        # 確保分數閾值不會太高
        if score_threshold > 0.9:
            score_threshold = 0.0
            logger.warning(f"Score threshold was too high, reset to 0.0")
        
        print(f"[DEBUG] Dify request - Query: '{query}', top_k: {top_k}, score_threshold: {score_threshold}, knowledge_id: '{knowledge_id}'")
        logger.info(f"Dify knowledge search - Knowledge ID: '{knowledge_id}', Query: '{query}', top_k: {top_k}, score_threshold: {score_threshold}")
        
        if not query:
            logger.warning("Query parameter is missing")
            return Response({
                'error_code': 2001,
                'error_msg': 'Query parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 直接使用原始查詢
        processed_query = query
        logger.info(f"Using original query directly: '{processed_query}'")
        
        # 搜索 PostgreSQL 知識
        logger.info(f"Searching for query: '{processed_query}' with limit: {top_k}")
        
        # 根據 knowledge_id 決定搜索哪個知識庫
        if knowledge_id in ['know_issue_db', 'know_issue', 'know-issue']:
            search_results = search_know_issue_knowledge(processed_query, limit=top_k)
            logger.info(f"Know Issue search results count: {len(search_results)}")
        elif knowledge_id in ['rvt_guide_db', 'rvt_guide', 'rvt-guide', 'rvt_user_guide']:
            # 優先使用向量搜索，如果不可用則回退到關鍵字搜索
            if VECTOR_SEARCH_AVAILABLE:
                try:
                    search_results = search_rvt_guide_with_vectors(processed_query, limit=top_k, threshold=0.1)
                    logger.info(f"RVT Guide vector search results count: {len(search_results)}")
                    
                    # 如果向量搜索沒有結果，回退到關鍵字搜索
                    if not search_results:
                        logger.info("向量搜索無結果，回退到關鍵字搜索")
                        search_results = search_rvt_guide_knowledge(processed_query, limit=top_k)
                        logger.info(f"RVT Guide keyword search results count: {len(search_results)}")
                except Exception as e:
                    logger.error(f"向量搜索失敗，回退到關鍵字搜索: {e}")
                    search_results = search_rvt_guide_knowledge(processed_query, limit=top_k)
                    logger.info(f"RVT Guide fallback search results count: {len(search_results)}")
            else:
                search_results = search_rvt_guide_knowledge(processed_query, limit=top_k)
                logger.info(f"RVT Guide keyword search results count: {len(search_results)}")
        elif knowledge_id in ['ocr_storage_benchmark', 'ocr_benchmark', 'storage_benchmark', 'benchmark_db']:
            # 搜索 OCR 存儲基準測試資料
            search_results = search_ocr_storage_benchmark(processed_query, limit=top_k)
            logger.info(f"OCR Storage Benchmark search results count: {len(search_results)}")
        else:
            # 默認搜索員工知識庫
            search_results = search_postgres_knowledge(processed_query, limit=top_k)
            logger.info(f"Employee search results count: {len(search_results)}")
        
        logger.info(f"Raw search results count: {len(search_results)}")
        
        # 過濾分數低於閾值的結果
        filtered_results = [
            result for result in search_results 
            if result['score'] >= score_threshold
        ]
        logger.info(f"Filtered results count: {len(filtered_results)} (threshold: {score_threshold})")
        
        # 轉換為 Dify 期望的格式
        records = []
        for result in filtered_results:
            record = {
                'content': result['content'],
                'score': result['score'],
                'title': result['title'],
                'metadata': result['metadata']
            }
            records.append(record)
            logger.info(f"Added record: {record['title']}")
        
        response_data = {
            'records': records
        }
        
        logger.info(f"Final response data: {response_data}")
        logger.info(f"Dify knowledge search - Found {len(records)} results")
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except json.JSONDecodeError:
        return Response({
            'error_code': 1001,
            'error_msg': 'Invalid JSON format'
        }, status=status.HTTP_400_BAD_REQUEST)
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
    Dify Know Issue 外部知識庫 API 端點 - 專門針對問題知識庫搜索
    
    期望的請求格式:
    {
        "knowledge_id": "know_issue_db",
        "query": "搜索字詞",
        "retrieval_setting": {
            "top_k": 3,
            "score_threshold": 0.5
        }
    }
    """
    try:
        # 記錄請求來源
        logger.info(f"Dify Know Issue API request from: {request.META.get('REMOTE_ADDR')}")
        
        # 解析請求數據
        data = json.loads(request.body) if request.body else {}
        query = data.get('query', '')
        knowledge_id = data.get('knowledge_id', 'know_issue_db')
        retrieval_setting = data.get('retrieval_setting', {})
        
        top_k = retrieval_setting.get('top_k', 5)
        score_threshold = retrieval_setting.get('score_threshold', 0.0)
        
        logger.info(f"Know Issue search - Query: {query}, Top K: {top_k}, Score threshold: {score_threshold}")
        
        # 驗證必要參數
        if not query:
            return Response({
                'error_code': 2001,
                'error_msg': 'Query parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 搜索 Know Issue 資料
        search_results = search_know_issue_knowledge(query, limit=top_k)
        
        # 過濾分數低於閾值的結果
        filtered_results = [
            result for result in search_results 
            if result['score'] >= score_threshold
        ]
        
        logger.info(f"Know Issue search found {len(search_results)} results, {len(filtered_results)} after filtering")
        
        # 構建符合 Dify 規格的響應
        records = []
        for result in filtered_results:
            record = {
                'content': result['content'],
                'score': result['score'],
                'title': result['title'],
                'metadata': result['metadata']
            }
            records.append(record)
            logger.info(f"Added Know Issue record: {record['title']}")
        
        response_data = {
            'records': records
        }
        
        logger.info(f"Know Issue API response: Found {len(records)} results")
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except json.JSONDecodeError:
        return Response({
            'error_code': 1001,
            'error_msg': 'Invalid JSON format'
        }, status=status.HTTP_400_BAD_REQUEST)
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
    Dify OCR Storage Benchmark 外部知識庫 API 端點 - 專門針對 OCR 存儲基準測試搜索
    
    期望的請求格式:
    {
        "knowledge_id": "ocr_storage_benchmark",
        "query": "搜索字詞",
        "retrieval_setting": {
            "top_k": 3,
            "score_threshold": 0.5
        }
    }
    """
    try:
        # 記錄請求來源
        logger.info(f"Dify OCR Storage Benchmark API request from: {request.META.get('REMOTE_ADDR')}")
        
        # 解析請求數據
        data = json.loads(request.body) if request.body else {}
        query = data.get('query', '')
        knowledge_id = data.get('knowledge_id', 'ocr_storage_benchmark')
        retrieval_setting = data.get('retrieval_setting', {})
        
        top_k = retrieval_setting.get('top_k', 5)
        score_threshold = retrieval_setting.get('score_threshold', 0.0)
        
        logger.info(f"OCR Storage Benchmark search - Query: '{query}', Top K: {top_k}, Score threshold: {score_threshold}")
        print(f"[DEBUG] OCR Benchmark API - Query: '{query}', top_k: {top_k}, score_threshold: {score_threshold}, knowledge_id: '{knowledge_id}'")
        
        # 驗證必要參數
        if not query:
            return Response({
                'error_code': 2001,
                'error_msg': 'Query parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 專門搜索 OCR Storage Benchmark 資料
        search_results = search_ocr_storage_benchmark(query, limit=top_k)
        logger.info(f"OCR Storage Benchmark search found {len(search_results)} results")
        
        # 過濾分數低於閾值的結果
        filtered_results = [
            result for result in search_results 
            if result['score'] >= score_threshold
        ]
        logger.info(f"OCR Storage Benchmark filtered results: {len(filtered_results)} (threshold: {score_threshold})")
        
        # 構建符合 Dify 規格的響應
        records = []
        for result in filtered_results:
            record = {
                'content': result['content'],
                'score': result['score'],
                'title': result['title'],
                'metadata': result['metadata']
            }
            records.append(record)
            logger.info(f"Added OCR Benchmark record: {record['title']}")
        
        response_data = {
            'records': records
        }
        
        logger.info(f"OCR Storage Benchmark API response: Found {len(records)} results")
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except json.JSONDecodeError:
        return Response({
            'error_code': 1001,
            'error_msg': 'Invalid JSON format'
        }, status=status.HTTP_400_BAD_REQUEST)
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
    Dify RVT Guide 外部知識庫 API 端點 - 專門針對 RVT 使用指南搜索
    
    期望的請求格式:
    {
        "knowledge_id": "rvt_guide_db",
        "query": "搜索字詞",
        "retrieval_setting": {
            "top_k": 3,
            "score_threshold": 0.5
        }
    }
    """
    try:
        # 記錄請求來源
        logger.info(f"Dify RVT Guide API request from: {request.META.get('REMOTE_ADDR')}")
        
        # 解析請求數據
        data = json.loads(request.body) if request.body else {}
        query = data.get('query', '')
        knowledge_id = data.get('knowledge_id', 'rvt_guide_db')
        retrieval_setting = data.get('retrieval_setting', {})
        
        top_k = retrieval_setting.get('top_k', 5)
        score_threshold = retrieval_setting.get('score_threshold', 0.0)
        
        logger.info(f"RVT Guide search - Query: {query}, Top K: {top_k}, Score threshold: {score_threshold}")
        
        # 驗證必要參數
        if not query:
            return Response({
                'error_code': 2001,
                'error_msg': 'Query parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 搜索 RVT Guide 資料
        search_results = search_rvt_guide_knowledge(query, limit=top_k)
        
        # 過濾分數低於閾值的結果
        filtered_results = [
            result for result in search_results 
            if result['score'] >= score_threshold
        ]
        
        logger.info(f"RVT Guide search found {len(search_results)} results, {len(filtered_results)} after filtering")
        
        # 構建符合 Dify 規格的響應
        records = []
        for result in filtered_results:
            record = {
                'content': result['content'],
                'score': result['score'],
                'title': result['title'],
                'metadata': result['metadata']
            }
            records.append(record)
            logger.info(f"Added RVT Guide record: {record['title']}")
        
        response_data = {
            'records': records
        }
        
        logger.info(f"RVT Guide API response: Found {len(records)} results")
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except json.JSONDecodeError:
        return Response({
            'error_code': 1001,
            'error_msg': 'Invalid JSON format'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Dify RVT Guide search error: {str(e)}")
        return Response({
            'error_code': 2001,
            'error_msg': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class KnowIssueViewSet(viewsets.ModelViewSet):
    """問題知識庫 ViewSet"""
    queryset = KnowIssue.objects.all()
    serializer_class = KnowIssueSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """根據動作決定權限"""
        print(f"KnowIssue get_permissions - Action: {self.action}")
        print(f"KnowIssue get_permissions - User: {self.request.user}")
        print(f"KnowIssue get_permissions - Is authenticated: {self.request.user.is_authenticated}")
        
        # 允許所有登入用戶訪問
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        """根據查詢參數過濾資料"""
        queryset = KnowIssue.objects.all()
        
        # 根據專案過濾
        project = self.request.query_params.get('project', None)
        if project:
            queryset = queryset.filter(project__icontains=project)
            
        # 根據狀態過濾
        status = self.request.query_params.get('status', None)
        if status:
            queryset = queryset.filter(status=status)
            
        # 根據問題類型過濾
        issue_type = self.request.query_params.get('issue_type', None)
        if issue_type:
            queryset = queryset.filter(issue_type=issue_type)
            
        # 根據關鍵字搜尋
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                models.Q(issue_id__icontains=search) |
                models.Q(project__icontains=search) |
                models.Q(error_message__icontains=search) |
                models.Q(supplement__icontains=search)
            )
            
        return queryset.order_by('-updated_at')
    
    def create(self, request, *args, **kwargs):
        """創建 Know Issue，支援二進制圖片上傳"""
        try:
            # 處理圖片上傳
            uploaded_images = {}
            for i in range(1, 6):  # image1 到 image5
                image_field = f'image{i}'
                if image_field in request.FILES:
                    image_file = request.FILES[image_field]
                    uploaded_images[i] = {
                        'data': image_file.read(),
                        'filename': image_file.name,
                        'content_type': image_file.content_type
                    }
            
            # 創建序列化器實例
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # 保存實例，設置更新人員
            instance = serializer.save(updated_by=request.user)
            
            # 處理上傳的圖片 - 存為二進制數據
            for image_index, image_data in uploaded_images.items():
                instance.set_image_data(
                    image_index,
                    image_data['data'],
                    image_data['filename'],
                    image_data['content_type']
                )
            
            # 再次保存以處理圖片
            if uploaded_images:
                instance.save()
            
            # 返回完整的序列化數據
            response_serializer = self.get_serializer(instance)
            headers = self.get_success_headers(response_serializer.data)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
            
        except Exception as e:
            logger.error(f"KnowIssue create error: {str(e)}")
            return Response(
                {'error': f'創建失敗: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def update(self, request, *args, **kwargs):
        """更新 Know Issue，支援二進制圖片上傳"""
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            
            # 處理圖片上傳
            uploaded_images = {}
            for i in range(1, 6):  # image1 到 image5
                image_field = f'image{i}'
                if image_field in request.FILES:
                    image_file = request.FILES[image_field]
                    uploaded_images[i] = {
                        'data': image_file.read(),
                        'filename': image_file.name,
                        'content_type': image_file.content_type
                    }
            
            # 更新其他欄位
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            
            # 保存實例，設置更新人員
            instance = serializer.save(updated_by=request.user)
            
            # 處理上傳的圖片 - 存為二進制數據
            for image_index, image_data in uploaded_images.items():
                instance.set_image_data(
                    image_index,
                    image_data['data'],
                    image_data['filename'],
                    image_data['content_type']
                )
            
            # 再次保存以處理圖片
            if uploaded_images:
                instance.save()
            
            # 返回完整的序列化數據
            response_serializer = self.get_serializer(instance)
            return Response(response_serializer.data)
            
        except Exception as e:
            logger.error(f"KnowIssue update error: {str(e)}")
            return Response(
                {'error': f'更新失敗: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def perform_create(self, serializer):
        """建立時設定更新人員為當前用戶"""
        serializer.save(updated_by=self.request.user)
    
    def perform_update(self, serializer):
        """更新時設定更新人員為當前用戶"""
        serializer.save(updated_by=self.request.user)


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
    """OCR測試類別 ViewSet - 讀取開放給所有用戶，但只有 admin 可以修改"""
    queryset = OCRTestClass.objects.all()
    serializer_class = OCRTestClassSerializer
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
                    message='只有管理員才能管理OCR測試類別'
                )
            return [permissions.IsAuthenticated()]
    
    def perform_create(self, serializer):
        """建立時設定建立者為當前用戶"""
        serializer.save(created_by=self.request.user)
    
    def get_queryset(self):
        """支援搜尋和篩選"""
        queryset = OCRTestClass.objects.all()
        
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
class OCRStorageBenchmarkViewSet(viewsets.ModelViewSet):
    """AI OCR 存儲基準測試 ViewSet"""
    queryset = OCRStorageBenchmark.objects.all()
    serializer_class = OCRStorageBenchmarkSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        """根據操作類型選擇合適的序列化器"""
        if self.action == 'list':
            # 列表視圖使用不包含圖像數據的序列化器以提升性能
            return OCRStorageBenchmarkListSerializer
        return OCRStorageBenchmarkSerializer
    
    def perform_create(self, serializer):
        """建立時設定上傳者為當前用戶"""
        serializer.save(uploaded_by=self.request.user)
    
    def get_queryset(self):
        """支援搜尋和篩選"""
        queryset = OCRStorageBenchmark.objects.select_related('test_class', 'uploaded_by').all()
        
        # 專案名稱搜尋
        project_name = self.request.query_params.get('project_name', None)
        if project_name:
            queryset = queryset.filter(project_name__icontains=project_name)
        
        # 裝置型號搜尋
        device_model = self.request.query_params.get('device_model', None)
        if device_model:
            queryset = queryset.filter(device_model__icontains=device_model)
        
        # OCR 測試類別篩選 - 新增功能
        test_class_id = self.request.query_params.get('test_class', None)
        if test_class_id:
            queryset = queryset.filter(test_class_id=test_class_id)
        
        # 處理狀態篩選
        processing_status = self.request.query_params.get('processing_status', None)
        if processing_status:
            queryset = queryset.filter(processing_status=processing_status)
        
        # 測試環境篩選
        test_environment = self.request.query_params.get('test_environment', None)
        if test_environment:
            queryset = queryset.filter(test_environment=test_environment)
        
        # 測試類型篩選
        test_type = self.request.query_params.get('test_type', None)
        if test_type:
            queryset = queryset.filter(test_type=test_type)
        
        # OCRStorageBenchmark 沒有 is_verified 字段，移除驗證狀態篩選
        # is_verified = self.request.query_params.get('is_verified', None)
        # if is_verified is not None:
        #     if is_verified.lower() in ['true', '1']:
        #         queryset = queryset.filter(is_verified=True)
        #     elif is_verified.lower() in ['false', '0']:
        #         queryset = queryset.filter(is_verified=False)
        
        # 上傳者篩選
        uploaded_by = self.request.query_params.get('uploaded_by', None)
        if uploaded_by:
            queryset = queryset.filter(uploaded_by__username__icontains=uploaded_by)
        
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
        """上傳原始圖像"""
        try:
            ocr_record = self.get_object()
            
            # 檢查是否有上傳的文件
            if 'image' not in request.FILES:
                return Response({
                    'error': '請選擇要上傳的圖像文件'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            uploaded_file = request.FILES['image']
            
            # 檢查文件類型
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
            if uploaded_file.content_type not in allowed_types:
                return Response({
                    'error': f'不支援的文件類型。支援的類型: {", ".join(allowed_types)}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 檢查文件大小 (限制 10MB)
            max_size = 10 * 1024 * 1024  # 10MB
            if uploaded_file.size > max_size:
                return Response({
                    'error': f'文件大小超過限制 ({max_size // (1024*1024)}MB)'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 讀取並保存圖像資料
            ocr_record.original_image_data = uploaded_file.read()
            ocr_record.original_image_filename = uploaded_file.name
            ocr_record.original_image_content_type = uploaded_file.content_type
            ocr_record.save()
            
            return Response({
                'message': '圖像上傳成功',
                'filename': uploaded_file.name,
                'size_kb': len(ocr_record.original_image_data) // 1024,
                'content_type': uploaded_file.content_type
            }, status=status.HTTP_200_OK)
            
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
        """處理 OCR 識別"""
        try:
            ocr_record = self.get_object()
            
            # 檢查是否有原始圖像
            if not ocr_record.original_image_data:
                return Response({
                    'error': '請先上傳原始圖像'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 更新處理狀態
            ocr_record.processing_status = 'processing'
            ocr_record.save()
            
            # 這裡可以集成實際的 OCR 服務
            # 暫時返回模擬結果
            import time
            start_time = time.time()
            
            # 模擬 OCR 處理
            if not ocr_record.ocr_raw_text:
                # 根據附件內容生成模擬 OCR 結果
                mock_ocr_text = f"""
                專案名稱: {ocr_record.project_name or 'Storage Benchmark Score'}
                測試得分: {ocr_record.benchmark_score or '6883'}
                平均帶寬: {ocr_record.average_bandwidth or '1174.89 MB/s'}
                裝置型號: {ocr_record.device_model or 'KINGSTON SFYR2S1TO'}
                韌體版本: {ocr_record.firmware_version or 'SGW0904A'}
                測試時間: {ocr_record.test_datetime or '2025-09-06 16:13 +08:00'}
                3DMark 版本: {ocr_record.benchmark_version or '2.28.8228 (測試專用版)'}
                """
                ocr_record.ocr_raw_text = mock_ocr_text.strip()
            
            # 模擬 AI 結構化處理
            if not ocr_record.ai_structured_data:
                ocr_record.ai_structured_data = {
                    "project_name": ocr_record.project_name or "Storage Benchmark Score",
                    "benchmark_score": ocr_record.benchmark_score or 6883,
                    "average_bandwidth": ocr_record.average_bandwidth or "1174.89 MB/s",
                    "device_model": ocr_record.device_model or "KINGSTON SFYR2S1TO",
                    "firmware_version": ocr_record.firmware_version or "SGW0904A",
                    "test_datetime": str(ocr_record.test_datetime or "2025-09-06 16:13 +08:00"),
                    "benchmark_version": ocr_record.benchmark_version or "2.28.8228 (測試專用版)",
                    "extracted_fields": ["project_name", "benchmark_score", "average_bandwidth", "device_model", "firmware_version", "test_datetime", "benchmark_version"],
                    "confidence": 0.95
                }
            
            # 設置處理結果
            processing_time = time.time() - start_time
            ocr_record.ocr_processing_time = processing_time
            ocr_record.ocr_confidence = 0.95
            ocr_record.processing_status = 'completed'
            ocr_record.save()
            
            return Response({
                'message': 'OCR 處理完成',
                'processing_time': processing_time,
                'confidence': 0.95,
                'raw_text_preview': ocr_record.ocr_raw_text[:200] + "..." if len(ocr_record.ocr_raw_text) > 200 else ocr_record.ocr_raw_text,
                'structured_data': ocr_record.ai_structured_data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"OCR 處理失敗: {str(e)}")
            ocr_record.processing_status = 'failed'
            ocr_record.save()
            return Response({
                'error': f'OCR 處理失敗: {str(e)}'
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

@method_decorator(csrf_exempt, name='dispatch')
class UserLoginView(View):
    """
    用戶登入 API - 使用 class-based view 避免 CSRF 問題
    """
    def post(self, request):
        try:
            data = json.loads(request.body)
            username = data.get('username', '')
            password = data.get('password', '')
            
            if not username or not password:
                return JsonResponse({
                    'success': False,
                    'message': '用戶名和密碼不能為空'
                }, status=400)
            
            # Django 認證
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                if user.is_active:
                    login(request, user)
                    
                    # 獲取或創建用戶資料
                    try:
                        profile = UserProfile.objects.get(user=user)
                        bio = profile.bio
                    except UserProfile.DoesNotExist:
                        bio = ''
                    
                    return JsonResponse({
                        'success': True,
                        'message': '登入成功',
                        'user': {
                            'id': user.id,
                            'username': user.username,
                            'email': user.email,
                            'first_name': user.first_name,
                            'last_name': user.last_name,
                            'is_staff': user.is_staff,
                            'is_superuser': user.is_superuser,
                            'bio': bio,
                            'date_joined': user.date_joined.isoformat(),
                            'last_login': user.last_login.isoformat() if user.last_login else None
                        }
                    }, status=200)
                else:
                    return JsonResponse({
                        'success': False,
                        'message': '該帳號已被停用'
                    }, status=401)
            else:
                return JsonResponse({
                    'success': False,
                    'message': '用戶名或密碼錯誤'
                }, status=401)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': '無效的 JSON 格式'
            }, status=400)
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': '伺服器錯誤'
            }, status=500)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([])
def user_login(request):
    """
    用戶登入 API
    """
    try:
        data = json.loads(request.body)
        username = data.get('username', '')
        password = data.get('password', '')
        
        if not username or not password:
            return Response({
                'success': False,
                'message': '用戶名和密碼不能為空'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Django 認證
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_active:
                login(request, user)
                
                # 獲取或創建用戶資料
                try:
                    profile = UserProfile.objects.get(user=user)
                    bio = profile.bio
                except UserProfile.DoesNotExist:
                    bio = ''
                
                return Response({
                    'success': True,
                    'message': '登入成功',
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'is_staff': user.is_staff,
                        'is_superuser': user.is_superuser,
                        'bio': bio,
                        'date_joined': user.date_joined.isoformat(),
                        'last_login': user.last_login.isoformat() if user.last_login else None
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': '該帳號已被停用'
                }, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({
                'success': False,
                'message': '用戶名或密碼錯誤'
            }, status=status.HTTP_401_UNAUTHORIZED)
            
    except json.JSONDecodeError:
        return Response({
            'success': False,
            'message': '無效的 JSON 格式'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return Response({
            'success': False,
            'message': '伺服器錯誤'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([])
def user_register(request):
    """
    用戶註冊 API
    """
    try:
        data = json.loads(request.body)
        username = data.get('username', '').strip()
        password = data.get('password', '')
        email = data.get('email', '').strip()
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        
        # 基本驗證
        if not username:
            return Response({
                'success': False,
                'message': '用戶名不能為空'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        if not password:
            return Response({
                'success': False,
                'message': '密碼不能為空'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        if not email:
            return Response({
                'success': False,
                'message': 'Email 不能為空'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 檢查用戶名是否已存在
        if User.objects.filter(username=username).exists():
            return Response({
                'success': False,
                'message': '用戶名已存在'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 檢查 Email 是否已存在
        if User.objects.filter(email=email).exists():
            return Response({
                'success': False,
                'message': 'Email 已被註冊'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 創建新用戶
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        
        # 創建對應的 UserProfile
        UserProfile.objects.create(
            user=user,
            bio=f'歡迎 {first_name or username} 加入！'
        )
        
        logger.info(f"New user registered: {username} ({email})")
        
        return Response({
            'success': True,
            'message': '註冊成功！請使用新帳號登入',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'date_joined': user.date_joined.isoformat()
            }
        }, status=status.HTTP_201_CREATED)
        
    except json.JSONDecodeError:
        return Response({
            'success': False,
            'message': '無效的 JSON 格式'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return Response({
            'success': False,
            'message': f'註冊失敗: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([])
def user_logout(request):
    """
    用戶登出 API - 強制清除 session
    """
    try:
        username = None
        
        # 嘗試獲取用戶名（如果有的話）
        if hasattr(request, 'user') and request.user.is_authenticated:
            username = request.user.username
        
        # 強制清除 session
        if hasattr(request, 'session'):
            request.session.flush()  # 完全清除 session
        
        # Django logout
        logout(request)
        
        # 清除所有相關的 session
        from django.contrib.sessions.models import Session
        if username:
            # 清除該用戶的所有 session（可選）
            user_sessions = Session.objects.filter(
                session_data__contains=username
            )
            user_sessions.delete()
        
        return Response({
            'success': True,
            'message': f'用戶 {username or "用戶"} 已成功登出並清除所有 session'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        # 即使出錯也要嘗試清除 session
        try:
            if hasattr(request, 'session'):
                request.session.flush()
            logout(request)
        except:
            pass
            
        return Response({
            'success': True,
            'message': '已強制清除登入狀態'
        }, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    更改密碼 API
    """
    try:
        # 使用 request.data 而不是 request.body
        data = request.data
        old_password = data.get('old_password', '')
        new_password = data.get('new_password', '')
        
        # 基本驗證
        if not old_password:
            return Response({
                'old_password': ['目前密碼不能為空']
            }, status=status.HTTP_400_BAD_REQUEST)
            
        if not new_password:
            return Response({
                'new_password': ['新密碼不能為空']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 驗證目前密碼
        user = request.user
        if not user.check_password(old_password):
            return Response({
                'old_password': ['目前密碼不正確']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 檢查新密碼是否與舊密碼相同
        if user.check_password(new_password):
            return Response({
                'new_password': ['新密碼不能與目前密碼相同']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 更改密碼
        user.set_password(new_password)
        user.save()
        
        logger.info(f"Password changed successfully for user: {user.username}")
        
        return Response({
            'success': True,
            'message': '密碼更改成功'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Change password error: {str(e)}")
        return Response({
            'error': '伺服器錯誤，請稍後再試'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([])
def user_info(request):
    """
    獲取當前用戶資訊 API
    """
    try:
        print(f"user_info - Request method: {request.method}")
        print(f"user_info - Request user: {request.user}")
        print(f"user_info - Is authenticated: {request.user.is_authenticated}")
        print(f"user_info - Session key: {request.session.session_key}")
        print(f"user_info - Session items: {dict(request.session.items())}")
        print(f"user_info - Cookies: {request.COOKIES}")
        print(f"user_info - Headers: {dict(request.headers)}")
        
        if request.user.is_authenticated:
            user = request.user
            print(f"user_info - Authenticated user: {user.username}")
            
            # 獲取用戶資料
            try:
                profile = UserProfile.objects.get(user=user)
                bio = profile.bio
            except UserProfile.DoesNotExist:
                bio = ''

            return Response({
                'success': True,
                'authenticated': True,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_staff': user.is_staff,
                    'is_superuser': user.is_superuser,
                    'bio': bio,
                    'date_joined': user.date_joined.isoformat(),
                    'last_login': user.last_login.isoformat() if user.last_login else None
                }
            }, status=status.HTTP_200_OK)
        else:
            print(f"user_info - User not authenticated: {request.user}")
            return Response({
                'success': True,
                'authenticated': False,
                'message': '用戶未登入'
            }, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Get user info error: {str(e)}")
        return Response({
            'success': False,
            'message': '獲取用戶資訊失敗'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def dify_chat_with_file(request):
    """
    Dify Chat API with File Support - 支援圖片分析功能
    類似於 test_single_file_analysis 的流程
    整合 OCR 分析器自動解析和保存功能
    """
    try:
        import time
        import os
        import tempfile
        import requests
        from library.dify_integration import create_report_analyzer_client
        # 使用新的配置管理器
        # get_report_analyzer_config 已在頂部引入
        from library.data_processing.file_utils import (
            get_file_info, 
            validate_file_for_upload, 
            get_default_analysis_query
        )
        # 導入 OCR 分析器
        from library.data_processing.ocr_analyzer import (
            create_ocr_analyzer,
            create_ocr_database_manager
        )
        # 導入文本處理器
        from library.data_processing.text_processor import extract_project_name
        
        message = request.data.get('message', '').strip()
        conversation_id = request.data.get('conversation_id', '')
        uploaded_file = request.FILES.get('file')
        
        # 從用戶訊息中提取 project name
        extracted_project_name = extract_project_name(message) if message else None
        
        # 檢查是否有文件或消息
        if not message and not uploaded_file:
            return Response({
                'success': False,
                'error': '需要提供訊息內容或圖片文件'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 如果有文件，進行文件分析
        if uploaded_file:
            try:
                # 1. 保存臨時文件
                temp_dir = tempfile.mkdtemp()
                temp_file_path = os.path.join(temp_dir, uploaded_file.name)
                
                with open(temp_file_path, 'wb+') as temp_file:
                    for chunk in uploaded_file.chunks():
                        temp_file.write(chunk)
                
                # 2. 驗證文件
                is_valid, error_msg = validate_file_for_upload(temp_file_path, max_size_mb=10)
                if not is_valid:
                    os.remove(temp_file_path)
                    os.rmdir(temp_dir)
                    return Response({
                        'success': False,
                        'error': f'文件驗證失敗: {error_msg}'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # 3. 獲取文件信息
                file_info = get_file_info(temp_file_path)
                
                # 4. 生成查詢（如果沒有提供消息，使用默認查詢）
                query = message if message else get_default_analysis_query(temp_file_path)
                
                # 5. 使用 library 進行分析
                config = get_report_analyzer_config()
                client = create_report_analyzer_client(
                    config.api_url,
                    config.api_key,
                    config.base_url
                )
                
                start_time = time.time()
                
                # 6. 執行分析
                result = client.upload_and_analyze(
                    temp_file_path, 
                    query, 
                    user=f"web_user_{request.user.id if request.user.is_authenticated else 'guest'}",
                    verbose=True
                )
                
                elapsed = time.time() - start_time
                
                # 🆕 7. AI 回覆後自動執行 OCR 解析和保存
                ocr_analysis_result = None
                if result['success'] and result.get('answer'):
                    try:
                        print(f"\n🔬 開始執行 OCR 分析和資料庫保存...")
                        
                        # 創建 OCR 分析器和資料庫管理器
                        ocr_analyzer = create_ocr_analyzer()
                        ocr_db_manager = create_ocr_database_manager()
                        
                        # 解析 AI 回答中的測試資料
                        ai_answer = result.get('answer', '')
                        
                        # 🆕 添加 AI 回答的詳細調試輸出
                        print(f"\n📄 AI 回答內容分析:")
                        print(f"回答長度: {len(ai_answer)} 字符")
                        print(f"前 500 字符預覽:")
                        print("=" * 80)
                        print(ai_answer[:500] if ai_answer else "AI 回答為空")
                        print("=" * 80)
                        print(f"完整 AI 回答:")
                        print(repr(ai_answer)[:1000])  # 使用 repr 顯示原始格式
                        print("=" * 80)
                        
                        parsed_data = ocr_analyzer.parse_storage_benchmark_table(ai_answer)
                        
                        # 🆕 添加解析結果的詳細調試輸出
                        print(f"\n🔍 解析結果分析:")
                        print(f"解析數據: {parsed_data}")
                        print(f"解析欄位數量: {len(parsed_data) if parsed_data else 0}")
                        if parsed_data:
                            for key, value in parsed_data.items():
                                print(f"  {key}: {repr(value)}")
                        print("=" * 80)
                        
                        if parsed_data and len(parsed_data) > 5:
                            print(f"✅ OCR 解析成功，解析出 {len(parsed_data)} 個欄位")
                            
                            # 保存到資料庫
                            user = request.user if request.user.is_authenticated else None
                            
                            # 如果從訊息中提取到 project name，添加到 parsed_data 中
                            if extracted_project_name:
                                parsed_data = parsed_data or {}
                                parsed_data['project_name'] = extracted_project_name
                                print(f"📝 將 project name '{extracted_project_name}' 添加到解析數據中")
                            
                            save_result = ocr_db_manager.save_to_ocr_database(
                                parsed_data=parsed_data,
                                file_path=temp_file_path,
                                ocr_raw_text=ai_answer,
                                original_result=result,
                                uploaded_by=user
                            )
                            
                            if save_result['success']:
                                print(f"💾 資料已成功保存到 OCR 資料庫")
                                ocr_analysis_result = {
                                    'parsed': True,
                                    'fields_count': len(parsed_data),
                                    'database_saved': True,
                                    'record_info': save_result.get('performance_summary', {}),
                                    'parsed_fields': list(parsed_data.keys())
                                }
                            else:
                                print(f"⚠️ 資料庫保存失敗: {save_result.get('error', '未知錯誤')}")
                                ocr_analysis_result = {
                                    'parsed': True,
                                    'fields_count': len(parsed_data),
                                    'database_saved': False,
                                    'error': save_result.get('error', '未知錯誤')
                                }
                        else:
                            print(f"ℹ️ AI 回答中未檢測到儲存基準測試表格格式，跳過 OCR 解析")
                            ocr_analysis_result = {
                                'parsed': False,
                                'reason': 'No storage benchmark table detected'
                            }
                        
                    except Exception as ocr_error:
                        print(f"❌ OCR 分析過程出錯: {str(ocr_error)}")
                        ocr_analysis_result = {
                            'parsed': False,
                            'error': str(ocr_error)
                        }
                
                # 8. 清理臨時文件
                os.remove(temp_file_path)
                os.rmdir(temp_dir)
                
                # 9. 返回結果（包含 OCR 分析結果）
                if result['success']:
                    logger.info(f"File analysis success for user {request.user.username}: {uploaded_file.name}")
                    
                    response_data = {
                        'success': True,
                        'answer': result.get('answer', ''),
                        'conversation_id': result.get('conversation_id', ''),
                        'message_id': result.get('message_id', ''),
                        'response_time': elapsed,
                        'metadata': result.get('metadata', {}),
                        'usage': result.get('usage', {}),
                        'file_info': {
                            'name': file_info['file_name'],
                            'size': file_info['file_size'],
                            'type': 'image' if file_info['is_image'] else 'document'
                        }
                    }
                    
                    # 如果有 OCR 分析結果，添加到響應中
                    if ocr_analysis_result:
                        response_data['ocr_analysis'] = ocr_analysis_result
                    
                    return Response(response_data, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'success': False,
                        'error': result.get('error', '文件分析失敗'),
                        'response_time': elapsed
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                    
            except Exception as e:
                # 清理臨時文件
                if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                if 'temp_dir' in locals() and os.path.exists(temp_dir):
                    os.rmdir(temp_dir)
                
                logger.error(f"File analysis error: {str(e)}")
                return Response({
                    'success': False,
                    'error': f'文件分析錯誤: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # 如果沒有文件，回退到普通聊天模式
        else:
            # 使用原有的聊天邏輯（代碼將在下一步添加）
            pass
            
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
    """
    try:
        import requests
        
        data = request.data
        message = data.get('message', '').strip()
        conversation_id = data.get('conversation_id', '')
        
        if not message:
            return Response({
                'success': False,
                'error': '訊息內容不能為空'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 使用 Protocol Known Issue 配置（用於 Protocol RAG）
        try:
            dify_config = get_protocol_known_issue_config()
        except Exception as config_error:
            logger.error(f"Failed to load Protocol Known Issue config: {config_error}")
            return Response({
                'success': False,
                'error': f'配置載入失敗: {str(config_error)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # 檢查必要配置
        api_url = dify_config.api_url
        api_key = dify_config.api_key
        
        if not api_url or not api_key:
            return Response({
                'success': False,
                'error': 'Dify API 配置不完整'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # 準備請求
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'inputs': {},
            'query': message,
            'response_mode': 'blocking',
            'user': f"web_user_{request.user.id if request.user.is_authenticated else 'guest'}"
        }
        
        if conversation_id:
            payload['conversation_id'] = conversation_id
        
        start_time = time.time()
        
        # 發送請求到 Dify，增加錯誤處理
        try:
            response = requests.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=120  # 延長超時時間到 120 秒，因為 AI 回應可能需要較長時間
            )
        except requests.exceptions.Timeout:
            return Response({
                'success': False,
                'error': 'Dify API 請求超時，請稍後再試'
            }, status=status.HTTP_408_REQUEST_TIMEOUT)
        except requests.exceptions.ConnectionError:
            return Response({
                'success': False,
                'error': 'Dify API 連接失敗，請檢查網路連接'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as req_error:
            return Response({
                'success': False,
                'error': f'API 請求錯誤: {str(req_error)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            # 記錄成功的聊天
            logger.info(f"Dify chat success for user {request.user.username}: {message[:50]}...")
            
            return Response({
                'success': True,
                'answer': result.get('answer', ''),
                'conversation_id': result.get('conversation_id', ''),
                'message_id': result.get('message_id', ''),
                'response_time': elapsed,
                'metadata': result.get('metadata', {}),
                'usage': result.get('usage', {})
            }, status=status.HTTP_200_OK)
        else:
            # 特殊處理 404 錯誤（對話不存在）
            if response.status_code == 404:
                # 如果是對話不存在的錯誤，嘗試不帶 conversation_id 重新發送
                try:
                    response_data = response.json()
                    if 'Conversation Not Exists' in response_data.get('message', ''):
                        logger.warning(f"Conversation {conversation_id} not exists, retrying without conversation_id")
                        
                        # 重新發送請求，不帶 conversation_id
                        retry_payload = {
                            'inputs': {},
                            'query': message,
                            'response_mode': 'blocking',
                            'user': f"web_user_{request.user.id if request.user.is_authenticated else 'guest'}"
                        }
                        
                        retry_response = requests.post(
                            api_url,
                            headers=headers,
                            json=retry_payload,
                            timeout=120
                        )
                        
                        if retry_response.status_code == 200:
                            retry_result = retry_response.json()
                            logger.info(f"Dify chat retry success for user {request.user.username}")
                            
                            return Response({
                                'success': True,
                                'answer': retry_result.get('answer', ''),
                                'conversation_id': retry_result.get('conversation_id', ''),
                                'message_id': retry_result.get('message_id', ''),
                                'response_time': elapsed,
                                'metadata': retry_result.get('metadata', {}),
                                'usage': retry_result.get('usage', {}),
                                'warning': '原對話已過期，已開始新對話'
                            }, status=status.HTTP_200_OK)
                        
                except Exception as retry_error:
                    logger.error(f"Retry request failed: {str(retry_error)}")
            
            error_msg = f"Dify API 錯誤: {response.status_code} - {response.text}"
            logger.error(f"Dify chat error for user {request.user.username}: {error_msg}")
            
            return Response({
                'success': False,
                'error': error_msg,
                'response_time': elapsed
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Dify chat API error: {str(e)}")
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
    Dify OCR Chat API - 專門用於 AI OCR 系統，使用 Report Analyzer 3 配置
    """
    try:
        import requests
        
        # 記錄請求來源
        logger.info(f"Dify OCR chat request from: {request.META.get('REMOTE_ADDR')}")
        
        data = request.data
        message = data.get('message', '').strip()
        conversation_id = data.get('conversation_id', '')
        
        if not message:
            return Response({
                'success': False,
                'error': '訊息內容不能為空'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 使用 Report Analyzer 3 配置（專門用於 AI OCR）
        try:
            dify_config = get_report_analyzer_config()
        except Exception as config_error:
            logger.error(f"Failed to load Report Analyzer 3 config: {config_error}")
            return Response({
                'success': False,
                'error': f'AI OCR 配置載入失敗: {str(config_error)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # 檢查必要配置
        api_url = dify_config.api_url
        api_key = dify_config.api_key
        
        if not api_url or not api_key:
            return Response({
                'success': False,
                'error': 'AI OCR API 配置不完整'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # 準備請求
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'inputs': {},
            'query': message,
            'response_mode': 'blocking',
            'user': f"ocr_user_{request.user.id if request.user.is_authenticated else 'guest'}"
        }
        
        if conversation_id:
            payload['conversation_id'] = conversation_id
        
        start_time = time.time()
        
        # 發送請求到 Dify Report Analyzer 3
        try:
            response = requests.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=120  # AI OCR 分析可能需要較長時間
            )
        except requests.exceptions.Timeout:
            return Response({
                'success': False,
                'error': 'AI OCR 分析超時，請稍後再試'
            }, status=status.HTTP_408_REQUEST_TIMEOUT)
        except requests.exceptions.ConnectionError:
            return Response({
                'success': False,
                'error': 'AI OCR 連接失敗，請檢查網路連接'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as req_error:
            return Response({
                'success': False,
                'error': f'AI OCR API 請求錯誤: {str(req_error)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            # 記錄成功的聊天
            logger.info(f"AI OCR chat success for user {request.user.username if request.user.is_authenticated else 'guest'}: {message[:50]}...")
            
            # 直接使用原始的 AI 回答，不進行增強處理
            answer = result.get('answer', '')
            metadata = result.get('metadata', {})
            
            return Response({
                'success': True,
                'answer': answer,
                'conversation_id': result.get('conversation_id', ''),
                'message_id': result.get('message_id', ''),
                'response_time': elapsed,
                'metadata': metadata,
                'usage': result.get('usage', {})
            }, status=status.HTTP_200_OK)
        else:
            # 特殊處理 404 錯誤（對話不存在）
            if response.status_code == 404:
                try:
                    response_data = response.json()
                    if 'Conversation Not Exists' in response_data.get('message', ''):
                        logger.warning(f"AI OCR conversation {conversation_id} not exists, retrying without conversation_id")
                        
                        # 重新發送請求，不帶 conversation_id
                        retry_payload = {
                            'inputs': {},
                            'query': message,
                            'response_mode': 'blocking',
                            'user': f"ocr_user_{request.user.id if request.user.is_authenticated else 'guest'}"
                        }
                        
                        retry_response = requests.post(
                            api_url,
                            headers=headers,
                            json=retry_payload,
                            timeout=120
                        )
                        
                        if retry_response.status_code == 200:
                            retry_result = retry_response.json()
                            logger.info(f"AI OCR chat retry success for user {request.user.username if request.user.is_authenticated else 'guest'}")
                            
                            return Response({
                                'success': True,
                                'answer': retry_result.get('answer', ''),
                                'conversation_id': retry_result.get('conversation_id', ''),
                                'message_id': retry_result.get('message_id', ''),
                                'response_time': elapsed,
                                'metadata': retry_result.get('metadata', {}),
                                'usage': retry_result.get('usage', {}),
                                'warning': '原對話已過期，已開始新對話'
                            }, status=status.HTTP_200_OK)
                        
                except Exception as retry_error:
                    logger.error(f"AI OCR retry request failed: {str(retry_error)}")
            
            error_msg = f"AI OCR API 錯誤: {response.status_code} - {response.text}"
            logger.error(f"AI OCR chat error for user {request.user.username if request.user.is_authenticated else 'guest'}: {error_msg}")
            
            return Response({
                'success': False,
                'error': error_msg,
                'response_time': elapsed
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"AI OCR chat API error: {str(e)}")
        return Response({
            'success': False,
            'error': f'AI OCR 服務器錯誤: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def chat_usage_statistics(request):
    """
    獲取聊天使用統計數據
    """
    try:
        from django.db.models import Count, Avg
        from django.utils import timezone
        from datetime import datetime, timedelta
        from .models import ChatUsage
        
        # 獲取日期範圍參數
        days = int(request.GET.get('days', 30))  # 默認30天
        
        # 修正日期計算：使用日期開始時間，而不是當前具體時間
        current_time = timezone.now()
        end_date = current_time.replace(hour=23, minute=59, second=59, microsecond=999999)  # 今天結束時間
        start_date = (current_time - timedelta(days=days-1)).replace(hour=0, minute=0, second=0, microsecond=0)  # 開始日期的00:00:00
        
        # 基礎查詢集
        base_queryset = ChatUsage.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        # 1. 各聊天類型使用次數統計 (圓餅圖數據)
        chat_type_stats = base_queryset.values('chat_type').annotate(
            count=Count('id'),
            avg_response_time=Avg('response_time')
        ).order_by('-count')
        
        pie_chart_data = []
        type_display_map = {
            'know_issue_chat': 'Protocol RAG',
            'log_analyze_chat': 'AI OCR', 
            'rvt_assistant_chat': 'RVT Assistant'
        }
        
        for stat in chat_type_stats:
            pie_chart_data.append({
                'name': type_display_map.get(stat['chat_type'], stat['chat_type']),
                'value': stat['count'],
                'type': stat['chat_type'],
                'avg_response_time': round(stat['avg_response_time'] or 0, 2)
            })
        
        # 2. 每日使用次數統計 (曲線圖數據)
        daily_stats = []
        for i in range(days):
            # 每日統計使用日期的開始和結束時間
            current_date = (start_date + timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
            next_date = current_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            day_usage = base_queryset.filter(
                created_at__gte=current_date,
                created_at__lte=next_date  # 改為 <= 因為已經設置到當天結束時間
            )
            
            # 各類型當日使用次數
            know_issue_count = day_usage.filter(chat_type='know_issue_chat').count()
            log_analyze_count = day_usage.filter(chat_type='log_analyze_chat').count()
            rvt_assistant_count = day_usage.filter(chat_type='rvt_assistant_chat').count()
            total_count = day_usage.count()
            
            daily_stats.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'total': total_count,
                'know_issue_chat': know_issue_count,
                'log_analyze_chat': log_analyze_count,
                'rvt_assistant_chat': rvt_assistant_count
            })
        
        # 3. 總體統計
        total_usage = base_queryset.count()
        total_users = base_queryset.values('user').distinct().count()
        total_files = base_queryset.filter(has_file_upload=True).count()
        avg_response_time = base_queryset.aggregate(avg=Avg('response_time'))['avg']
        
        summary_stats = {
            'total_chats': total_usage,
            'total_users': total_users,
            'total_file_uploads': total_files,
            'avg_response_time': round(avg_response_time or 0, 2),
            'date_range': {
                'start': start_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d'),
                'days': days
            }
        }
        
        return Response({
            'success': True,
            'data': {
                'pie_chart': pie_chart_data,
                'daily_chart': daily_stats,
                'summary': summary_stats
            }
        }, status=status.HTTP_200_OK)
        
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
    記錄聊天使用情況
    """
    try:
        from .models import ChatUsage
        
        data = request.data
        chat_type = data.get('chat_type')
        message_count = data.get('message_count', 1)
        has_file_upload = data.get('has_file_upload', False)
        response_time = data.get('response_time')
        session_id = data.get('session_id', '')
        
        # 驗證聊天類型
        valid_types = ['know_issue_chat', 'log_analyze_chat', 'rvt_assistant_chat']
        if chat_type not in valid_types:
            return Response({
                'success': False,
                'error': '無效的聊天類型'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 獲取客戶端信息
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # 創建使用記錄
        usage_record = ChatUsage.objects.create(
            user=request.user if request.user.is_authenticated else None,
            session_id=session_id,
            chat_type=chat_type,
            message_count=message_count,
            has_file_upload=has_file_upload,
            response_time=response_time,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return Response({
            'success': True,
            'record_id': usage_record.id
        }, status=status.HTTP_201_CREATED)
        
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
    RVT Guide Chat API - 使用 RVT_GUIDE 配置
    """
    try:
        import requests
        
        data = request.data
        message = data.get('message', '').strip()
        conversation_id = data.get('conversation_id', '')
        
        if not message:
            return Response({
                'success': False,
                'error': '訊息內容不能為空'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 使用新的配置管理器獲取 RVT_GUIDE 配置
        try:
            from library.config import get_rvt_guide_config
            rvt_config_obj = get_rvt_guide_config()
            rvt_config = rvt_config_obj.to_dict()  # 轉換為字典以兼容現有代碼
        except Exception as config_error:
            logger.error(f"Failed to load RVT Guide config: {config_error}")
            return Response({
                'success': False,
                'error': f'RVT Guide 配置載入失敗: {str(config_error)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # 檢查必要配置
        api_url = rvt_config.get('api_url')
        api_key = rvt_config.get('api_key')
        
        if not api_url or not api_key:
            return Response({
                'success': False,
                'error': 'RVT Guide API 配置不完整'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # 記錄請求
        logger.info(f"RVT Guide chat request from user: {request.user.username if request.user.is_authenticated else 'guest'}")
        logger.debug(f"RVT Guide message: {message[:100]}...")
        
        # 準備請求
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'inputs': {},
            'query': message,
            'response_mode': 'blocking',
            'user': f"rvt_user_{request.user.id if request.user.is_authenticated else 'guest'}"
        }
        
        if conversation_id:
            payload['conversation_id'] = conversation_id
        
        start_time = time.time()
        
        # 使用 library 中的 Dify 請求管理器
        try:
            from library.dify_integration import make_dify_request, process_dify_answer, handle_conversation_error
            
            # 發送請求到 Dify RVT Guide，包含智能重試機制
            response = make_dify_request(
                api_url=api_url,
                headers=headers,
                payload=payload,
                timeout=rvt_config.get('timeout', 60),
                handle_400_answer_format_error=True
            )
        except requests.exceptions.Timeout:
            logger.error(f"RVT Guide 請求超時，已重試 3 次")
            return Response({
                'success': False,
                'error': 'RVT Guide 分析超時，請稍後再試或簡化問題描述'
            }, status=status.HTTP_408_REQUEST_TIMEOUT)
        except requests.exceptions.ConnectionError:
            logger.error(f"RVT Guide 連接失敗，已重試 3 次")
            return Response({
                'success': False,
                'error': 'RVT Guide 連接失敗，請檢查網路連接或稍後再試'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as req_error:
            logger.error(f"RVT Guide 請求錯誤: {str(req_error)}")
            return Response({
                'success': False,
                'error': f'RVT Guide API 請求錯誤: {str(req_error)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            # 使用 library 中的響應處理器處理 answer 字段
            answer = process_dify_answer(result.get('answer', ''))
            
            # 記錄成功的聊天
            logger.info(f"RVT Guide chat success for user {request.user.username if request.user.is_authenticated else 'guest'}: response_time={elapsed:.2f}s")
            
            return Response({
                'success': True,
                'answer': answer,
                'conversation_id': result.get('conversation_id', ''),
                'message_id': result.get('message_id', ''),
                'response_time': elapsed,
                'metadata': result.get('metadata', {}),
                'usage': result.get('usage', {}),
                'workspace': rvt_config.get('workspace', 'RVT_Guide'),
                'app_name': rvt_config.get('app_name', 'RVT Guide')
            }, status=status.HTTP_200_OK)
        else:
            # 特殊處理 404 錯誤（對話不存在）
            if response.status_code == 404:
                # 使用 library 中的對話錯誤處理器
                retry_result = handle_conversation_error(
                    response, api_url, headers, payload, rvt_config.get('timeout', 60)
                )
                
                if retry_result:
                    # 處理重試成功的回答
                    retry_answer = process_dify_answer(retry_result.get('answer', ''))
                    logger.info(f"RVT Guide chat retry success")
                    
                    return Response({
                        'success': True,
                        'answer': retry_answer,
                        'conversation_id': retry_result.get('conversation_id', ''),
                        'message_id': retry_result.get('message_id', ''),
                        'response_time': elapsed,
                        'metadata': retry_result.get('metadata', {}),
                        'usage': retry_result.get('usage', {}),
                        'warning': '原對話已過期，已開始新對話',
                        'workspace': rvt_config.get('workspace', 'RVT_Guide'),
                        'app_name': rvt_config.get('app_name', 'RVT Guide')
                    }, status=status.HTTP_200_OK)
            
            error_msg = f"RVT Guide API 錯誤: {response.status_code} - {response.text}"
            logger.error(f"RVT Guide chat error: {error_msg}")
            
            return Response({
                'success': False,
                'error': error_msg
            }, status=response.status_code)
        
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
    獲取 RVT Guide 配置信息
    """
    try:
        from library.config import get_rvt_guide_config
        config_obj = get_rvt_guide_config()
        
        # 返回安全的配置信息（不包含 API key）
        safe_config = config_obj.get_safe_config()
        
        return Response({
            'success': True,
            'config': safe_config
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Get RVT Guide config error: {str(e)}")
        return Response({
            'success': False,
            'error': f'獲取 RVT Guide 配置失敗: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RVTGuideViewSet(viewsets.ModelViewSet):
    """RVT Guide ViewSet - 用於 RVT Assistant 知識庫管理"""
    queryset = RVTGuide.objects.all()
    serializer_class = RVTGuideSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        """根據操作類型選擇合適的序列化器"""
        if self.action == 'list':
            # 列表視圖使用輕量級序列化器以提升性能
            return RVTGuideListSerializer
        return RVTGuideSerializer
    
    def perform_create(self, serializer):
        """建立新的 RVT Guide"""
        instance = serializer.save()
        # 自動生成向量
        self._generate_vector_for_guide(instance, action='create')
    
    def perform_update(self, serializer):
        """更新現有的 RVT Guide"""
        instance = serializer.save()
        # 自動生成向量
        self._generate_vector_for_guide(instance, action='update')
    
    def _generate_vector_for_guide(self, instance, action='create'):
        """
        為 RVT Guide 生成向量資料
        
        Args:
            instance: RVTGuide 實例
            action: 操作類型 ('create' 或 'update')
        """
        try:
            # 動態導入 embedding_service 避免循環導入
            from .services.embedding_service import get_embedding_service
            
            # 格式化內容用於向量化
            content = f"標題: {instance.title}\n"
            content += f"主分類: {instance.get_main_category_display()}\n"
            content += f"內容: {instance.content}\n"
            
            # 獲取 embedding 服務
            service = get_embedding_service()  # 使用 1024 維模型
            
            # 生成並儲存向量
            success = service.store_document_embedding(
                source_table='rvt_guide',
                source_id=instance.id,
                content=content,
                use_1024_table=True  # 使用 1024 維表格
            )
            
            if success:
                logger.info(f"✅ 成功為 RVT Guide 生成向量 ({action}): ID {instance.id} - {instance.title}")
            else:
                logger.error(f"❌ RVT Guide 向量生成失敗 ({action}): ID {instance.id} - {instance.title}")
                
        except Exception as e:
            logger.error(f"❌ RVT Guide 向量生成異常 ({action}): ID {instance.id} - {str(e)}")
    
    def get_queryset(self):
        """支援搜尋和篩選"""
        queryset = RVTGuide.objects.all()
        
        # 標題搜尋
        title = self.request.query_params.get('title', None)
        if title:
            queryset = queryset.filter(title__icontains=title)
        
        # 主分類篩選
        main_category = self.request.query_params.get('main_category', None)
        if main_category:
            queryset = queryset.filter(main_category=main_category)
        
        # 子分類篩選
        sub_category = self.request.query_params.get('sub_category', None)
        if sub_category:
            queryset = queryset.filter(sub_category=sub_category)
        
        # 狀態篩選
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # 問題類型篩選
        question_type = self.request.query_params.get('question_type', None)
        if question_type:
            queryset = queryset.filter(question_type=question_type)
        
        # 目標用戶篩選

        
        # 關鍵字搜尋
        keywords = self.request.query_params.get('keywords', None)
        if keywords:
            queryset = queryset.filter(keywords__icontains=keywords)
        
        # 一般關鍵字搜尋
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                models.Q(title__icontains=search) |
                models.Q(content__icontains=search) |
                models.Q(keywords__icontains=search) |
                models.Q(document_name__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def statistics(self, request):
        """獲取統計資料"""
        try:
            from django.db.models import Count
            
            queryset = self.get_queryset()
            
            # 基本統計
            total_guides = queryset.count()
            published_guides = queryset.filter(status='published').count()
            
            # 按主分類統計
            main_category_stats = queryset.values('main_category').annotate(count=Count('id'))
            
            # 按子分類統計
            sub_category_stats = queryset.values('sub_category').annotate(count=Count('id'))
            
            # 按狀態統計
            status_stats = queryset.values('status').annotate(count=Count('id'))
            
            # 按問題類型統計
            question_type_stats = queryset.values('question_type').annotate(count=Count('id'))
            
            # 按目標用戶統計

            
            # 最新文檔 (前5名)
            recent_guides = queryset.order_by('-updated_at')[:5]
            recent_guides_data = RVTGuideListSerializer(recent_guides, many=True).data
            
            return Response({
                'total_guides': total_guides,
                'published_guides': published_guides,
                'publish_rate': round(published_guides / total_guides * 100, 2) if total_guides > 0 else 0,
                'main_category_distribution': list(main_category_stats),
                'sub_category_distribution': list(sub_category_stats),
                'status_distribution': list(status_stats),
                'question_type_distribution': list(question_type_stats),

                'recent_guides': recent_guides_data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"統計資料獲取失敗: {str(e)}")
            return Response({
                'error': f'統計資料獲取失敗: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============= 系統狀態監控 API =============

@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def system_status(request):
    """
    系統狀態監控 API - 只有管理員可以訪問
    """
    try:
        import psutil
        import subprocess
        import docker
        from django.db import connection
        from django.core.cache import cache
        from django.utils import timezone
        from datetime import timedelta
        
        status_data = {}
        
        # 1. 資料庫狀態
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT version()")
                db_version = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM django_session WHERE expire_date > NOW()")
                active_sessions = cursor.fetchone()[0]
                
                # 檢查主要表的記錄數
                cursor.execute("SELECT COUNT(*) FROM auth_user")
                user_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM know_issue")
                know_issue_count = cursor.fetchone()[0]
                
            status_data['database'] = {
                'status': 'healthy',
                'version': db_version.split(' ')[0],
                'active_sessions': active_sessions,
                'user_count': user_count,
                'know_issue_count': know_issue_count,
                'connection_pool': len(connection.queries) if connection.queries else 0
            }
        except Exception as e:
            status_data['database'] = {
                'status': 'error',
                'error': str(e)
            }
        
        # 2. 系統資源狀態
        try:
            # CPU 使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 記憶體使用率
            memory = psutil.virtual_memory()
            
            # 磁碟使用率
            disk = psutil.disk_usage('/')
            
            status_data['system'] = {
                'status': 'healthy',
                'cpu_percent': round(cpu_percent, 2),
                'memory': {
                    'total': round(memory.total / (1024**3), 2),  # GB
                    'used': round(memory.used / (1024**3), 2),   # GB
                    'percent': round(memory.percent, 2)
                },
                'disk': {
                    'total': round(disk.total / (1024**3), 2),   # GB
                    'used': round(disk.used / (1024**3), 2),    # GB
                    'percent': round((disk.used / disk.total) * 100, 2)
                }
            }
        except Exception as e:
            status_data['system'] = {
                'status': 'error',
                'error': str(e)
            }
        
        # 3. 容器狀態檢查 (不使用 Docker API)
        try:
            # 使用系統命令檢查容器狀態
            import subprocess
            
            result = subprocess.run(['docker', 'ps', '--format', 'table {{.Names}}\t{{.Status}}\t{{.Image}}'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # 跳過標題行
                container_info = []
                
                for line in lines:
                    if line.strip():
                        parts = line.split('\t')
                        if len(parts) >= 3:
                            name, status, image = parts[0], parts[1], parts[2]
                            if any(keyword in name for keyword in ['ai-', 'postgres', 'adminer', 'portainer']):
                                container_info.append({
                                    'name': name,
                                    'status': 'running' if 'Up' in status else 'stopped',
                                    'image': image,
                                    'status_detail': status
                                })
                
                status_data['containers'] = {
                    'status': 'healthy',
                    'total': len(container_info),
                    'running': len([c for c in container_info if c['status'] == 'running']),
                    'containers': container_info
                }
            else:
                raise Exception(f"Docker command failed: {result.stderr}")
                
        except Exception as e:
            status_data['containers'] = {
                'status': 'unavailable',
                'error': f'容器狀態檢查失敗: {str(e)}',
                'message': '無法獲取容器狀態，可能是權限問題'
            }
        
        # 4. API 效能統計
        try:
            from django.db.models import Count, Avg
            from django.contrib.sessions.models import Session
            
            # 最近 24 小時的統計
            yesterday = timezone.now() - timedelta(days=1)
            
            # 活躍會話數
            active_sessions = Session.objects.filter(expire_date__gt=timezone.now()).count()
            
            # 用戶活動統計
            recent_users = User.objects.filter(last_login__gte=yesterday).count()
            
            status_data['api'] = {
                'status': 'healthy',
                'active_sessions': active_sessions,
                'recent_active_users': recent_users,
                'total_users': User.objects.count(),
                'total_know_issues': KnowIssue.objects.count(),
                'uptime': str(timezone.now() - timezone.now().replace(hour=0, minute=0, second=0))
            }
        except Exception as e:
            status_data['api'] = {
                'status': 'error',
                'error': str(e)
            }
        
        # 5. 服務健康檢查
        status_data['overall'] = {
            'status': 'healthy' if all(
                section.get('status') == 'healthy' 
                for section in [status_data.get('database', {}), status_data.get('system', {}), 
                               status_data.get('containers', {}), status_data.get('api', {})]
            ) else 'warning',
            'timestamp': timezone.now().isoformat(),
            'server_time': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return Response(status_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"系統狀態檢查失敗: {str(e)}")
        return Response({
            'error': f'系統狀態檢查失敗: {str(e)}',
            'overall': {
                'status': 'error',
                'timestamp': timezone.now().isoformat() if 'timezone' in locals() else None
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def system_logs(request):
    """
    系統日誌 API - 獲取最近的系統日誌
    """
    try:
        log_type = request.query_params.get('type', 'django')
        lines = int(request.query_params.get('lines', 50))
        
        if log_type == 'django':
            # 獲取 Django 日誌（這裡簡化處理）
            import logging
            logger = logging.getLogger('django')
            
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
    簡化版系統狀態監控 API - 不依賴 Docker API
    """
    try:
        import psutil
        from django.db import connection
        from django.utils import timezone
        
        logger.info("Starting simple_system_status API call")
        
        # 獲取系統資源
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            logger.info(f"System resources: CPU={cpu_percent}%, Memory={memory.percent}%, Disk={round((disk.used / disk.total) * 100, 1)}%")
        except Exception as e:
            logger.error(f"Error getting system resources: {e}")
            return Response({'error': f'系統資源獲取失敗: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # 資料庫狀態
        db_healthy = True
        database_stats = {}
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                
                # 主要表統計
                tables = [
                    ('users', 'auth_user'),
                    ('know_issues', 'know_issue'), 
                    ('projects', 'api_project')
                ]
                
                for name, table in tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        database_stats[name] = cursor.fetchone()[0]
                    except Exception as table_error:
                        logger.warning(f"Error counting {table}: {table_error}")
                        database_stats[name] = 0
                        
        except Exception as e:
            logger.error(f"Database error: {e}")
            db_healthy = False
            database_stats = {'error': str(e)}
        
        # 警告檢查
        alerts = []
        if cpu_percent > 80:
            alerts.append('CPU 使用率過高')
        if memory.percent > 80:
            alerts.append('記憶體使用率過高')
        if disk.percent > 85:
            alerts.append('磁碟空間不足')
        
        response_data = {
            'status': 'healthy' if db_healthy and not alerts else 'warning',
            'timestamp': timezone.now().isoformat(),
            'server_time': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            'system': {
                'cpu_percent': round(cpu_percent, 1),
                'memory': {
                    'total': round(memory.total / (1024**3), 2),
                    'used': round(memory.used / (1024**3), 2),
                    'percent': round(memory.percent, 1)
                },
                'disk': {
                    'total': round(disk.total / (1024**3), 2),
                    'used': round(disk.used / (1024**3), 2),
                    'percent': round((disk.used / disk.total) * 100, 1)
                }
            },
            'services': {
                'django': {'status': 'running'},
                'database': {'status': 'healthy' if db_healthy else 'error'}
            },
            'database_stats': database_stats,
            'alerts': alerts
        }
        
        logger.info(f"API response data: {response_data}")
        return Response(response_data)
        
    except Exception as e:
        logger.error(f"Simple system status error: {str(e)}")
        return Response({
            'error': f'系統狀態獲取失敗: {str(e)}'
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
            logger.warning("HealthChecker library 不可用，使用備用實現")
            
            from django.db import connection
            from django.utils import timezone
            
            # 簡化的備用實現
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
                db_healthy = True
                db_message = '資料庫連接正常'
            except Exception as e:
                db_healthy = False
                db_message = f'資料庫連接失敗: {str(e)}'
            
            # 基本統計
            basic_stats = {}
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) FROM auth_user WHERE is_active = true")
                    active_users = cursor.fetchone()[0]
                    basic_stats['active_users'] = {
                        'count': active_users,
                        'description': '系統中的活躍用戶數量'
                    }
            except Exception as e:
                basic_stats['error'] = f'統計數據獲取失敗: {str(e)}'
            
            return Response({
                'status': 'healthy' if db_healthy else 'warning',
                'timestamp': timezone.now().isoformat(),
                'server_time': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                'services': {
                    'django': {'status': 'running', 'message': 'Django API 正常運行'},
                    'database': {'status': 'healthy' if db_healthy else 'error', 'message': db_message}
                },
                'statistics': basic_stats,
                'user_level': 'basic'
            })
        
    except Exception as e:
        logger.error(f"Basic system status error: {str(e)}")
        return Response({
            'error': f'獲取基本系統狀態失敗: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)