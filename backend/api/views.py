from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.db import models, connection
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json
import logging
from .models import UserProfile, Project, Task
from .serializers import UserSerializer, UserProfileSerializer, ProjectSerializer, TaskSerializer

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


def search_postgres_knowledge(query_text, limit=5):
    """
    在 PostgreSQL 中搜索員工知識
    使用全文搜索查詢員工資料
    """
    try:
        with connection.cursor() as cursor:
            # 使用全文搜索查詢員工資料 (假設有 name, department, skills 欄位)
            sql = """
            SELECT 
                id,
                name,
                department,
                skills,
                email,
                position,
                CASE 
                    WHEN name ILIKE %s THEN 1.0
                    WHEN department ILIKE %s THEN 0.8
                    WHEN skills ILIKE %s THEN 0.9
                    WHEN position ILIKE %s THEN 0.7
                    ELSE 0.5
                END as score
            FROM api_employee
            WHERE 
                name ILIKE %s OR 
                department ILIKE %s OR 
                skills ILIKE %s OR 
                position ILIKE %s
            ORDER BY score DESC, name ASC
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
                employee_data = dict(zip(columns, row))
                # 格式化為知識片段
                content = f"員工姓名: {employee_data['name']}\n"
                content += f"部門: {employee_data['department']}\n"
                content += f"職位: {employee_data['position']}\n"
                content += f"技能: {employee_data['skills']}\n"
                content += f"Email: {employee_data['email']}"
                
                results.append({
                    'id': str(employee_data['id']),
                    'title': f"{employee_data['name']} - {employee_data['position']}",
                    'content': content,
                    'score': float(employee_data['score']),
                    'metadata': {
                        'department': employee_data['department'],
                        'position': employee_data['position'],
                        'source': 'employee_database'
                    }
                })
            
            return results
            
    except Exception as e:
        logger.error(f"Database search error: {str(e)}")
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
        search_results = search_postgres_knowledge(query, limit=top_k)
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