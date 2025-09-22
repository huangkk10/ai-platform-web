from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Project, Task, Employee, DifyEmployee, KnowIssue, TestClass, OCRTestClass, OCRStorageBenchmark, RVTGuide


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
    updated_by_name = serializers.SerializerMethodField()
    test_class_name = serializers.CharField(source='test_class.name', read_only=True)
    summary = serializers.CharField(source='get_summary', read_only=True)
    image_urls = serializers.SerializerMethodField()
    image_count = serializers.SerializerMethodField()
    image_list = serializers.SerializerMethodField()
    
    class Meta:
        model = KnowIssue
        fields = [
            'id', 'issue_id', 'test_version', 'jira_number', 'updated_by', 
            'updated_by_name', 'project', 'test_class', 'test_class_name',
            'class_sequence_id', 'script', 'issue_type', 'status', 
            'error_message', 'supplement', 'summary', 'created_at', 'updated_at',
            # 二進制圖片欄位 (不直接暴露 data 欄位到 API)
            'image1_filename', 'image1_content_type',
            'image2_filename', 'image2_content_type',
            'image3_filename', 'image3_content_type',
            'image4_filename', 'image4_content_type',
            'image5_filename', 'image5_content_type',
            # 計算欄位
            'image_urls', 'image_count', 'image_list'
        ]
        read_only_fields = ['id', 'issue_id', 'class_sequence_id', 'created_at', 'updated_at', 
                           'updated_by_name', 'test_class_name', 'summary', 'image_urls', 
                           'image_count', 'image_list']
    
    def get_updated_by_name(self, obj):
        """獲取修改者的友好名稱"""
        if obj.updated_by:
            # 優先使用 first_name + last_name，如果沒有則使用 username
            full_name = f"{obj.updated_by.first_name} {obj.updated_by.last_name}".strip()
            return full_name if full_name else obj.updated_by.username
        return None
    
    def get_image_urls(self, obj):
        """獲取所有圖片的URL列表"""
        return obj.get_image_urls()
    
    def get_image_count(self, obj):
        """獲取圖片數量"""
        return obj.get_image_count()
    
    def get_image_list(self, obj):
        """獲取圖片詳細資訊列表"""
        return obj.get_image_list()


class OCRStorageBenchmarkSerializer(serializers.ModelSerializer):
    """AI OCR 存儲基準測試序列化器"""
    uploaded_by_name = serializers.SerializerMethodField()
    performance_grade = serializers.CharField(source='get_performance_grade', read_only=True)
    summary = serializers.CharField(source='get_summary', read_only=True)
    ai_data_summary = serializers.CharField(source='get_ai_data_summary', read_only=True)
    
    class Meta:
        model = OCRStorageBenchmark
        fields = [
            'id', 'project_name', 'benchmark_score', 'average_bandwidth',
            'device_model', 'firmware_version', 'test_datetime', 'benchmark_version', 'mark_version_3d',
            'ocr_confidence', 'ocr_processing_time',
            'ocr_raw_text', 'ai_structured_data',
            'uploaded_by', 'uploaded_by_name', 'created_at', 'updated_at',
            # 計算欄位
            'performance_grade', 'summary', 'ai_data_summary'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'uploaded_by_name',
            'performance_grade', 'summary', 'ai_data_summary'
        ]
    
    def get_uploaded_by_name(self, obj):
        """獲取上傳者的友好名稱"""
        if obj.uploaded_by:
            full_name = f"{obj.uploaded_by.first_name} {obj.uploaded_by.last_name}".strip()
            return full_name if full_name else obj.uploaded_by.username
        return None


class OCRStorageBenchmarkListSerializer(serializers.ModelSerializer):
    """AI OCR 存儲基準測試列表序列化器 - 不包含圖像資料以提升效能"""
    uploaded_by_name = serializers.SerializerMethodField()
    performance_grade = serializers.CharField(source='get_performance_grade', read_only=True)
    summary = serializers.CharField(source='get_summary', read_only=True)
    ai_data_summary = serializers.CharField(source='get_ai_data_summary', read_only=True)
    
    class Meta:
        model = OCRStorageBenchmark
        fields = [
            'id', 'project_name', 'benchmark_score', 'average_bandwidth',
            'device_model', 'firmware_version', 'test_datetime', 'benchmark_version', 'mark_version_3d',
            'ocr_confidence', 'uploaded_by_name',
            'created_at', 'updated_at',
            # 計算欄位
            'performance_grade', 'summary', 'ai_data_summary'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'uploaded_by_name',
            'performance_grade', 'summary', 'ai_data_summary'
        ]
    
    def get_uploaded_by_name(self, obj):
        """獲取上傳者的友好名稱"""
        if obj.uploaded_by:
            full_name = f"{obj.uploaded_by.first_name} {obj.uploaded_by.last_name}".strip()
            return full_name if full_name else obj.uploaded_by.username
        return None


class TestClassSerializer(serializers.ModelSerializer):
    """測試類別序列化器 - Admin 專用"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = TestClass
        fields = [
            'id', 'name', 'description', 'is_active', 
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_by_name', 'created_at', 'updated_at']


class OCRTestClassSerializer(serializers.ModelSerializer):
    """OCR測試類別序列化器 - Admin 專用"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = OCRTestClass
        fields = [
            'id', 'name', 'description', 'is_active', 
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_by_name', 'created_at', 'updated_at']


class RVTGuideSerializer(serializers.ModelSerializer):
    """RVT Guide 完整序列化器"""
    main_category_display = serializers.CharField(source='get_main_category_display', read_only=True)
    sub_category_display = serializers.CharField(source='get_sub_category_display', read_only=True)
    question_type_display = serializers.CharField(source='get_question_type_display', read_only=True)
    target_user_display = serializers.CharField(source='get_target_user_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    full_category_name = serializers.SerializerMethodField()
    
    class Meta:
        model = RVTGuide
        fields = [
            'id', 'title', 'version',
            'main_category', 'main_category_display',
            'sub_category', 'sub_category_display',
            'content',
            'question_type', 'question_type_display',
            'target_user', 'target_user_display',
            'status', 'status_display',
            'full_category_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'main_category_display',
            'sub_category_display', 'question_type_display', 
            'target_user_display', 'status_display',
            'full_category_name'
        ]
    
    def get_full_category_name(self, obj):
        """獲取完整分類名稱"""
        return obj.get_full_category_name()


class RVTGuideListSerializer(serializers.ModelSerializer):
    """RVT Guide 列表序列化器 - 用於列表視圖，包含較少字段以提升性能"""
    main_category_display = serializers.CharField(source='get_main_category_display', read_only=True)
    sub_category_display = serializers.CharField(source='get_sub_category_display', read_only=True)
    question_type_display = serializers.CharField(source='get_question_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    target_user_display = serializers.CharField(source='get_target_user_display', read_only=True)
    
    full_category_name = serializers.SerializerMethodField()
    
    class Meta:
        model = RVTGuide
        fields = [
            'id', 'title', 'version',
            'main_category', 'main_category_display', 
            'sub_category_display',
            'question_type', 'question_type_display',
            'target_user_display', 'status', 'status_display',
            'full_category_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'main_category_display',
            'sub_category_display', 'question_type_display', 
            'target_user_display', 'status_display',
            'full_category_name'
        ]
    
    def get_full_category_name(self, obj):
        """獲取完整分類名稱"""
        return obj.get_full_category_name()
