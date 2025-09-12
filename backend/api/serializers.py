from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Project, Task, Employee, DifyEmployee, KnowIssue


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['user', 'avatar', 'bio', 'location', 'birth_date', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class ProjectSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    members = UserSerializer(many=True, read_only=True)
    tasks_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'owner', 'members', 'tasks_count', 
                 'created_at', 'updated_at', 'is_active']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_tasks_count(self, obj):
        return obj.tasks.count()


class TaskSerializer(serializers.ModelSerializer):
    assignee = UserSerializer(read_only=True)
    creator = UserSerializer(read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    
    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'project', 'project_name', 
                 'assignee', 'creator', 'status', 'priority', 'due_date',
                 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class EmployeeSerializer(serializers.ModelSerializer):
    """簡化員工序列化器 - 僅包含 id 和 name"""
    
    class Meta:
        model = Employee
        fields = ['id', 'name', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class DifyEmployeeSerializer(serializers.ModelSerializer):
    """Dify員工序列化器 - 支援資料庫照片存儲"""
    photo_data_url = serializers.SerializerMethodField()
    photo_size_kb = serializers.SerializerMethodField()
    has_photo = serializers.SerializerMethodField()
    full_info = serializers.SerializerMethodField()
    
    class Meta:
        model = DifyEmployee
        fields = [
            'id', 'name', 'email', 'department', 'position', 'skills', 
            'phone', 'hire_date', 'is_active', 'photo_filename', 
            'photo_content_type', 'photo_data_url', 'photo_size_kb', 
            'has_photo', 'full_info', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'photo_data_url', 
                           'photo_size_kb', 'has_photo', 'full_info']
    
    def get_photo_data_url(self, obj):
        """獲取照片的 Base64 Data URL"""
        return obj.get_photo_data_url()
    
    def get_photo_size_kb(self, obj):
        """獲取照片大小（KB）"""
        if obj.photo_binary:
            import math
            return math.ceil(len(obj.photo_binary) / 1024)
        return 0
    
    def get_has_photo(self, obj):
        """是否有照片"""
        return bool(obj.photo_binary)
    
    def get_full_info(self, obj):
        """獲取完整員工資訊"""
        return obj.get_full_info()


class DifyEmployeeListSerializer(serializers.ModelSerializer):
    """Dify員工列表序列化器 - 不包含照片資料以提升效能"""
    photo_size_kb = serializers.SerializerMethodField()
    has_photo = serializers.SerializerMethodField()
    
    class Meta:
        model = DifyEmployee
        fields = [
            'id', 'name', 'email', 'department', 'position', 'skills', 
            'phone', 'hire_date', 'is_active', 'photo_filename', 
            'photo_content_type', 'photo_size_kb', 'has_photo',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'photo_size_kb', 'has_photo']
    
    def get_photo_size_kb(self, obj):
        """獲取照片大小（KB）"""
        if obj.photo_binary:
            import math
            return math.ceil(len(obj.photo_binary) / 1024)
        return 0
    
    def get_has_photo(self, obj):
        """是否有照片"""
        return bool(obj.photo_binary)

class KnowIssueSerializer(serializers.ModelSerializer):
    """問題知識庫序列化器"""
    updated_by_name = serializers.CharField(source='updated_by.name', read_only=True)
    issue_type_display = serializers.CharField(source='get_issue_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    summary = serializers.CharField(source='get_summary', read_only=True)
    
    class Meta:
        model = KnowIssue
        fields = [
            'id', 'issue_id', 'test_version', 'jira_number', 'updated_by', 
            'updated_by_name', 'project', 'script', 'issue_type', 
            'issue_type_display', 'status', 'status_display', 'error_message', 
            'supplement', 'summary', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'updated_by_name', 
                           'issue_type_display', 'status_display', 'summary']
