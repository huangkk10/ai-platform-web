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
from .models import UserProfile, Project, Task, Employee, DifyEmployee, KnowIssue, TestClass
from .serializers import UserSerializer, UserProfileSerializer, ProjectSerializer, TaskSerializer, EmployeeSerializer, DifyEmployeeSerializer, DifyEmployeeListSerializer, KnowIssueSerializer, TestClassSerializer

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
    from library.config.dify_app_configs import create_protocol_chat_client, get_protocol_known_issue_config
except ImportError:
    # 如果 library 路徑有問題，提供備用配置
    create_protocol_chat_client = None
    get_protocol_known_issue_config = None

logger = logging.getLogger(__name__)


def preprocess_chinese_query(query):
    """
    預處理中文查詢，提取關鍵字並優化搜索效果
    支援向量搜索和關鍵字搜索的雙重優化
    """
    logger.debug(f"預處理原始查詢: '{query}'")
    
    # 移除問號和其他標點符號
    processed = query.replace('？', '').replace('?', '').replace('。', '').replace('，', ' ').replace(',', ' ')
    
    # 擴展關鍵字映射 - 更全面的映射
    keyword_expansions = {
        # Jenkins 相關
        'Jenkins有階段': 'Jenkins 測試階段',
        'Jenkins階段': 'Jenkins 測試階段',
        'Jenkins有幾個階段': 'Jenkins 測試階段',
        'Jenkins有哪些階段': 'Jenkins 測試階段',
        'Jenkins測試階段': 'Jenkins 測試階段',
        'Jenkins流程': 'Jenkins 測試階段',
        'Jenkins步驟': 'Jenkins 測試階段',
        
        # RVT 相關
        'RVT是什麼': 'RVT 系統架構',
        'RVT系統': 'RVT 系統架構',
        'RVT操作流程': 'RVT Jenkins Ansible',
        'RVT流程': 'RVT Jenkins Ansible',
        '什麼是RVT': 'RVT 系統架構',
        'RVT概念': 'RVT 系統架構',
        
        # Ansible 相關
        'Ansible設定': 'Ansible 配置',
        'Ansible如何設定': 'Ansible 配置',
        'Ansible配置': 'Ansible 配置',
        'Ansible參數': 'Ansible 參數',
        
        # 其他概念
        '環境準備': '先決條件 環境準備',
        '故障排除': 'Jenkins 失敗 故障排除',
        '配置管理': 'Ansible 配置',
        'MDT配置': 'MDT 環境準備',
        'UART設定': 'UART 配置',
    }
    
    # 移除問句詞並標準化
    normalized_query = processed.replace(' ', '').lower()
    
    # 先檢查是否有直接映射
    for pattern, replacement in keyword_expansions.items():
        if pattern.replace(' ', '').lower() in normalized_query:
            logger.info(f"Keyword expansion: '{query}' -> '{replacement}'")
            return replacement
    
    # 常見的問句詞彙移除
    stop_words = ['有哪些', '是什麼', '如何', '怎麼', '什麼', '幾個', '多少', '怎樣', '有什麼', '有', '是']
    
    # 移除常見問句詞彙
    for stop_word in stop_words:
        processed = processed.replace(stop_word, ' ')
    
    # 移除多餘空格
    processed = ' '.join(processed.split())
    
    # 技術關鍵字提取和增強
    tech_keywords = {
        'jenkins': 'Jenkins',
        'ansible': 'Ansible', 
        'rvt': 'RVT',
        'uart': 'UART',
        'mdt': 'MDT',
        'poll': 'Poll 輪詢',
        'deploy': 'Deploy 部署',
        'ffu': 'FFU 韌體更新',
        'setup': 'SETUP 測試平台',
        'initcard': 'InitCard 開卡',
        'bios': 'BIOS iPXE',
        'nas': 'NAS 配置',
        '階段': '測試階段',
        '流程': '操作流程',
        '參數': '參數設定',
        '配置': '配置設定',
        '故障': '故障排除',
        '環境': '環境準備',
        '先決條件': '先決條件 環境準備'
    }
    
    # 增強關鍵字匹配
    enhanced_keywords = []
    query_lower = query.lower()
    
    for key, enhanced in tech_keywords.items():
        if key in query_lower:
            enhanced_keywords.append(enhanced)
    
    if enhanced_keywords:
        result = ' '.join(enhanced_keywords)
        logger.info(f"Tech keyword enhancement: '{query}' -> '{result}'")
        return result
    
    # 如果處理後的查詢太短，使用原查詢的關鍵部分
    if len(processed.strip()) < 3:
        # 提取核心技術詞彙
        core_terms = []
        for term in ['Jenkins', 'Ansible', 'RVT', 'UART', 'MDT']:
            if term.lower() in query.lower():
                core_terms.append(term)
        
        if core_terms:
            return ' '.join(core_terms)
        return query
    
    return processed.strip() if processed.strip() else query


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
                ki.updated_at,
                ki.updated_by_id,
                u.username as updated_by_name,
                u.first_name as updated_by_first_name,
                u.last_name as updated_by_last_name,
                CASE 
                    WHEN ki.issue_id ILIKE %s THEN 1.0
                    WHEN ki.project ILIKE %s THEN 0.9
                    WHEN tc.name ILIKE %s THEN 0.8
                    WHEN u.username ILIKE %s THEN 0.8
                    WHEN u.first_name ILIKE %s THEN 0.8
                    WHEN u.last_name ILIKE %s THEN 0.8
                    WHEN ki.error_message ILIKE %s THEN 0.7
                    WHEN ki.supplement ILIKE %s THEN 0.6
                    WHEN ki.script ILIKE %s THEN 0.5
                    ELSE 0.3
                END as score
            FROM know_issue ki
            LEFT JOIN test_class tc ON ki.test_class_id = tc.id
            LEFT JOIN auth_user u ON ki.updated_by_id = u.id
            WHERE 
                ki.issue_id ILIKE %s OR 
                ki.project ILIKE %s OR 
                tc.name ILIKE %s OR 
                u.username ILIKE %s OR 
                u.first_name ILIKE %s OR 
                u.last_name ILIKE %s OR 
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
                
                # 添加更改人員資訊
                if issue_data['updated_by_name']:
                    updated_by_display = issue_data['updated_by_name']
                    if issue_data['updated_by_first_name'] or issue_data['updated_by_last_name']:
                        full_name = f"{issue_data['updated_by_first_name'] or ''} {issue_data['updated_by_last_name'] or ''}".strip()
                        if full_name:
                            updated_by_display = f"{full_name} ({issue_data['updated_by_name']})"
                    content += f"更新人員: {updated_by_display}\n"
                
                content += f"建立時間: {issue_data['created_at']}\n"
                content += f"更新時間: {issue_data['updated_at']}"
                
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
                        'status': issue_data['status'],
                        'updated_by_id': issue_data['updated_by_id'],
                        'updated_by_name': issue_data['updated_by_name'],
                        'updated_at': str(issue_data['updated_at']) if issue_data['updated_at'] else None
                    }
                })
            
            return results
            
    except Exception as e:
        logger.error(f"Know Issue database search error: {str(e)}")
        return []


def search_rvt_guide_knowledge(query_text, limit=5):
    """
    在 PostgreSQL 中搜索 RVT Guide 知識庫
    """
    try:
        with connection.cursor() as cursor:
            sql = """
            SELECT 
                id,
                document_name,
                title,
                version,
                main_category,
                sub_category,
                content,
                keywords,
                question_type,
                target_user,
                status,
                created_at,
                updated_at,
                CASE 
                    WHEN title ILIKE %s THEN 1.0
                    WHEN keywords ILIKE %s THEN 0.9
                    WHEN content ILIKE %s THEN 0.8
                    WHEN document_name ILIKE %s THEN 0.6
                    ELSE 0.5
                END as score
            FROM rvt_guide
            WHERE 
                status = 'published' AND (
                    title ILIKE %s OR 
                    keywords ILIKE %s OR 
                    content ILIKE %s OR 
                    document_name ILIKE %s
                )
            ORDER BY score DESC, created_at DESC
            LIMIT %s
            """
            
            search_pattern = f'%{query_text}%'
            cursor.execute(sql, [
                search_pattern, search_pattern, search_pattern, search_pattern,
                search_pattern, search_pattern, search_pattern, search_pattern,
                limit
            ])
            
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            results = []
            for row in rows:
                guide_data = dict(zip(columns, row))
                
                # 格式化為知識片段
                content = f"# {guide_data['title']}\n\n"
                content += f"**分類**: {guide_data['main_category']} > {guide_data['sub_category']}\n\n"
                content += f"**內容**:\n{guide_data['content']}"
                
                # 獲取關鍵字列表
                keywords_list = []
                if guide_data['keywords']:
                    keywords_list = [k.strip() for k in guide_data['keywords'].split(',')]
                
                results.append({
                    'id': str(guide_data['id']),
                    'title': guide_data['title'],
                    'content': content,
                    'score': float(guide_data['score']),
                    'metadata': {
                        'source': 'rvt_guide_database',
                        'document_name': guide_data['document_name'],
                        'version': guide_data['version'],
                        'main_category': guide_data['main_category'],
                        'sub_category': guide_data['sub_category'],
                        'question_type': guide_data['question_type'],
                        'target_user': guide_data['target_user'],
                        'keywords': keywords_list,
                        'created_at': str(guide_data['created_at']) if guide_data['created_at'] else None,
                        'updated_at': str(guide_data['updated_at']) if guide_data['updated_at'] else None
                    }
                })
            
            logger.info(f"RVT Guide search found {len(results)} results for query: '{query_text}'")
            return results
            
    except Exception as e:
        logger.error(f"RVT Guide database search error: {str(e)}")
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
        
        # 暫時註釋預處理功能，直接使用原始查詢測試向量搜索效果
        # processed_query = preprocess_chinese_query(query)
        processed_query = query  # 直接使用原始查詢
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
    """
    try:
        import time
        import os
        import tempfile
        import requests
        from library.dify_integration import create_report_analyzer_client
        from library.config.dify_app_configs import get_report_analyzer_3_config
        from library.data_processing.file_utils import (
            get_file_info, 
            validate_file_for_upload, 
            get_default_analysis_query
        )
        
        message = request.data.get('message', '').strip()
        conversation_id = request.data.get('conversation_id', '')
        uploaded_file = request.FILES.get('file')
        
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
                config = get_report_analyzer_3_config()
                client = create_report_analyzer_client(
                    config['api_url'],
                    config['api_key'],
                    config['base_url']
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
                
                # 7. 清理臨時文件
                os.remove(temp_file_path)
                os.rmdir(temp_dir)
                
                # 8. 返回結果
                if result['success']:
                    logger.info(f"File analysis success for user {request.user.username}: {uploaded_file.name}")
                    
                    return Response({
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
                    }, status=status.HTTP_200_OK)
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
    Dify Chat API - 使用 PROTOCOL_KNOWN_ISSUE_SYSTEM 配置
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
        
        # 使用 library/config 模組的配置
        try:
            from library.config.dify_app_configs import get_protocol_known_issue_config
            dify_config = get_protocol_known_issue_config()
        except Exception as config_error:
            logger.error(f"Failed to load Dify config: {config_error}")
            return Response({
                'success': False,
                'error': f'配置載入失敗: {str(config_error)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # 檢查必要配置
        api_url = dify_config.get('api_url')
        api_key = dify_config.get('api_key')
        
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
    獲取 Dify 配置資訊 - 用於前端顯示
    """
    try:
        if get_protocol_known_issue_config is None:
            return Response({
                'success': False,
                'error': 'Dify 配置模組載入失敗'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # 獲取配置
        config = get_protocol_known_issue_config()
        
        # 只返回安全的配置資訊
        safe_config = {
            'app_name': config.get('app_name', 'Unknown App'),
            'workspace': config.get('workspace', 'Unknown Workspace'),
            'description': config.get('description', ''),
            'features': config.get('features', []),
            'api_url': config.get('api_url', ''),
            'base_url': config.get('base_url', ''),
            'timeout': config.get('timeout', 60),
            'response_mode': config.get('response_mode', 'blocking'),
            # 不返回完整的 API Key，只返回前幾位用於驗證
            'api_key_prefix': config.get('api_key', '')[:10] + '...' if config.get('api_key') else ''
        }
        
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
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
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
            'rvt_log_analyze_chat': 'RVT Assistant'
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
            current_date = start_date + timedelta(days=i)
            next_date = current_date + timedelta(days=1)
            
            day_usage = base_queryset.filter(
                created_at__gte=current_date,
                created_at__lt=next_date
            )
            
            # 各類型當日使用次數
            know_issue_count = day_usage.filter(chat_type='know_issue_chat').count()
            log_analyze_count = day_usage.filter(chat_type='log_analyze_chat').count()
            rvt_log_count = day_usage.filter(chat_type='rvt_log_analyze_chat').count()
            total_count = day_usage.count()
            
            daily_stats.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'total': total_count,
                'know_issue_chat': know_issue_count,
                'log_analyze_chat': log_analyze_count,
                'rvt_log_analyze_chat': rvt_log_count
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
        valid_types = ['know_issue_chat', 'log_analyze_chat', 'rvt_log_analyze_chat', 'rvt_assistant_chat']
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
        
        # 使用 RVT_GUIDE 配置
        try:
            from library.config.dify_app_configs import get_rvt_guide_config
            rvt_config = get_rvt_guide_config()
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
        
        # 發送請求到 Dify RVT Guide
        try:
            response = requests.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=rvt_config.get('timeout', 60)  # 使用配置中的超時時間
            )
        except requests.exceptions.Timeout:
            return Response({
                'success': False,
                'error': 'RVT Guide 分析超時，請稍後再試或簡化問題描述'
            }, status=status.HTTP_408_REQUEST_TIMEOUT)
        except requests.exceptions.ConnectionError:
            return Response({
                'success': False,
                'error': 'RVT Guide 連接失敗，請檢查網路連接'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as req_error:
            return Response({
                'success': False,
                'error': f'RVT Guide API 請求錯誤: {str(req_error)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            # 記錄成功的聊天
            logger.info(f"RVT Guide chat success for user {request.user.username if request.user.is_authenticated else 'guest'}: response_time={elapsed:.2f}s")
            
            return Response({
                'success': True,
                'answer': result.get('answer', ''),
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
                try:
                    response_data = response.json()
                    if 'Conversation Not Exists' in response_data.get('message', ''):
                        logger.warning(f"RVT Guide conversation {conversation_id} not exists, retrying without conversation_id")
                        
                        # 重新發送請求，不帶 conversation_id
                        retry_payload = {
                            'inputs': {},
                            'query': message,
                            'response_mode': 'blocking',
                            'user': f"rvt_user_{request.user.id if request.user.is_authenticated else 'guest'}"
                        }
                        
                        retry_response = requests.post(
                            api_url,
                            headers=headers,
                            json=retry_payload,
                            timeout=rvt_config.get('timeout', 60)
                        )
                        
                        if retry_response.status_code == 200:
                            retry_result = retry_response.json()
                            logger.info(f"RVT Guide chat retry success")
                            
                            return Response({
                                'success': True,
                                'answer': retry_result.get('answer', ''),
                                'conversation_id': retry_result.get('conversation_id', ''),
                                'message_id': retry_result.get('message_id', ''),
                                'response_time': elapsed,
                                'metadata': retry_result.get('metadata', {}),
                                'usage': retry_result.get('usage', {}),
                                'warning': '原對話已過期，已開始新對話',
                                'workspace': rvt_config.get('workspace', 'RVT_Guide'),
                                'app_name': rvt_config.get('app_name', 'RVT Guide')
                            }, status=status.HTTP_200_OK)
                        
                except Exception as retry_error:
                    logger.error(f"RVT Guide retry request failed: {str(retry_error)}")
            
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
        from library.config.dify_app_configs import get_rvt_guide_config
        config = get_rvt_guide_config()
        
        # 返回安全的配置信息（不包含 API key）
        safe_config = {
            'app_name': config.get('app_name', 'RVT Guide'),
            'workspace': config.get('workspace', 'RVT_Guide'),
            'description': config.get('description', 'RVT 相關指導和協助'),
            'features': config.get('features', ['RVT 指導', '技術支援', 'RVT 流程管理']),
            'timeout': config.get('timeout', 60),
            'response_mode': config.get('response_mode', 'blocking')
        }
        
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