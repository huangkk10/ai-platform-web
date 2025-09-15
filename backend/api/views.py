from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
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
from .models import UserProfile, Project, Task, Employee, DifyEmployee, KnowIssue, TestClass
from .serializers import UserSerializer, UserProfileSerializer, ProjectSerializer, TaskSerializer, EmployeeSerializer, DifyEmployeeSerializer, DifyEmployeeListSerializer, KnowIssueSerializer, TestClassSerializer

logger = logging.getLogger(__name__)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """使用者 ViewSet (只讀)"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


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


def search_know_issue_knowledge(query_text, limit=5):
    """
    在 PostgreSQL 中搜索 Know Issue 知識庫
    """
    try:
        with connection.cursor() as cursor:
            sql = """
            SELECT 
                ki.id,
                ki.issue_id,
                ki.test_version,
                ki.jira_number,
                ki.project,
                ki.test_class_id,
                tc.name as test_class_name,
                ki.script,
                ki.issue_type,
                ki.status,
                ki.error_message,
                ki.supplement,
                ki.created_at,
                CASE 
                    WHEN ki.issue_id ILIKE %s THEN 1.0
                    WHEN ki.project ILIKE %s THEN 0.9
                    WHEN tc.name ILIKE %s THEN 0.8
                    WHEN ki.error_message ILIKE %s THEN 0.7
                    WHEN ki.supplement ILIKE %s THEN 0.6
                    WHEN ki.script ILIKE %s THEN 0.5
                    ELSE 0.3
                END as score
            FROM know_issue ki
            LEFT JOIN test_class tc ON ki.test_class_id = tc.id
            WHERE 
                ki.issue_id ILIKE %s OR 
                ki.project ILIKE %s OR 
                tc.name ILIKE %s OR 
                ki.error_message ILIKE %s OR 
                ki.supplement ILIKE %s OR 
                ki.script ILIKE %s
            ORDER BY score DESC, ki.created_at DESC
            LIMIT %s
            """
            
            search_pattern = f'%{query_text}%'
            cursor.execute(sql, [
                search_pattern, search_pattern, search_pattern, 
                search_pattern, search_pattern, search_pattern,
                search_pattern, search_pattern, search_pattern,
                search_pattern, search_pattern, search_pattern,
                limit
            ])
            
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            results = []
            for row in rows:
                issue_data = dict(zip(columns, row))
                
                # 格式化為知識片段
                content = f"問題編號: {issue_data['issue_id']}\n"
                content += f"專案: {issue_data['project']}\n"
                content += f"測試版本: {issue_data['test_version']}\n"
                if issue_data['test_class_name']:
                    content += f"測試類別: {issue_data['test_class_name']}\n"
                if issue_data['jira_number']:
                    content += f"JIRA編號: {issue_data['jira_number']}\n"
                content += f"問題類型: {issue_data['issue_type']}\n"
                content += f"狀態: {issue_data['status']}\n"
                if issue_data['error_message']:
                    content += f"錯誤訊息: {issue_data['error_message']}\n"
                if issue_data['supplement']:
                    content += f"補充說明: {issue_data['supplement']}\n"
                if issue_data['script']:
                    content += f"相關腳本: {issue_data['script']}\n"
                content += f"建立時間: {issue_data['created_at']}"
                
                results.append({
                    'id': str(issue_data['id']),
                    'title': f"{issue_data['issue_id']} - {issue_data['project']}",
                    'content': content,
                    'score': float(issue_data['score']),
                    'metadata': {
                        'source': 'know_issue_database',
                        'issue_id': issue_data['issue_id'],
                        'project': issue_data['project'],
                        'test_version': issue_data['test_version'],
                        'issue_type': issue_data['issue_type'],
                        'status': issue_data['status']
                    }
                })
            
            return results
            
    except Exception as e:
        logger.error(f"Know Issue database search error: {str(e)}")
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
        
        print(f"[DEBUG] Dify request - Query: '{query}', top_k: {top_k}, score_threshold: {score_threshold}")
        logger.info(f"Dify knowledge search - Knowledge ID: {knowledge_id}, Query: '{query}', top_k: {top_k}, score_threshold: {score_threshold}")
        
        if not query:
            logger.warning("Query parameter is missing")
            return Response({
                'error_code': 2001,
                'error_msg': 'Query parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 搜索 PostgreSQL 知識
        logger.info(f"Searching for query: '{query}' with limit: {top_k}")
        
        # 根據 knowledge_id 決定搜索哪個知識庫
        if knowledge_id in ['know_issue_db', 'know_issue', 'know-issue']:
            search_results = search_know_issue_knowledge(query, limit=top_k)
            logger.info(f"Know Issue search results count: {len(search_results)}")
        else:
            # 默認搜索員工知識庫
            search_results = search_postgres_knowledge(query, limit=top_k)
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
            
        if len(password) < 6:
            return Response({
                'success': False,
                'message': '密碼長度至少需要 6 個字符'
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