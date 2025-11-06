from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Project, Task, KnowIssue, TestClass, OCRTestClass, OCRStorageBenchmark, RVTGuide, ProtocolGuide, ContentImage

# 導入通用序列化器（適用於所有知識庫）
from library.common.serializers import ContentImageSerializer

# 導入模組化的 RVT Guide 序列化器
from library.rvt_guide.serializers import (
    RVTGuideSerializer,
    RVTGuideListSerializer,
    RVTGuideWithImagesSerializer
)


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined', 
                 'is_staff', 'is_superuser', 'is_active', 'password']
        read_only_fields = ['id', 'date_joined']
        extra_kwargs = {
            'password': {'write_only': True, 'required': False}
        }
    
    def create(self, validated_data):
        """創建用戶時處理密碼加密"""
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        
        if password:
            user.set_password(password)
            user.save()
        
        return user
    
    def update(self, instance, validated_data):
        """更新用戶時處理密碼加密"""
        password = validated_data.pop('password', None)
        
        # 更新其他欄位
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # 如果提供了新密碼，則更新密碼
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    permissions_summary = serializers.CharField(source='get_permissions_summary', read_only=True)
    has_any_web_permission = serializers.BooleanField(source='has_any_web_permission', read_only=True)
    has_any_kb_permission = serializers.BooleanField(source='has_any_kb_permission', read_only=True)
    can_manage_permissions = serializers.BooleanField(source='can_manage_permissions', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'user', 'avatar', 'bio', 'location', 'birth_date', 
            # 權限相關欄位
            'web_protocol_rag', 'web_ai_ocr', 'web_rvt_assistant', 'web_protocol_assistant',
            'kb_protocol_rag', 'kb_ai_ocr', 'kb_rvt_assistant', 'kb_protocol_assistant',
            'is_super_admin',
            # 計算欄位
            'permissions_summary', 'has_any_web_permission', 
            'has_any_kb_permission', 'can_manage_permissions',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'permissions_summary', 
                           'has_any_web_permission', 'has_any_kb_permission', 
                           'can_manage_permissions']


class UserPermissionSerializer(serializers.ModelSerializer):
    """專用於權限管理的序列化器 - 只包含權限相關欄位"""
    user = UserSerializer(read_only=True)
    permissions_summary = serializers.CharField(source='get_permissions_summary', read_only=True)
    
    # 從 User model 獲取 is_staff 和 is_superuser
    is_staff = serializers.BooleanField(source='user.is_staff', read_only=True)
    is_superuser = serializers.BooleanField(source='user.is_superuser', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'user', 
            # 權限欄位
            'web_protocol_rag', 'web_ai_ocr', 'web_rvt_assistant', 'web_protocol_assistant',
            'kb_protocol_rag', 'kb_ai_ocr', 'kb_rvt_assistant', 'kb_protocol_assistant',
            'is_super_admin',
            # 系統管理權限（從 User model）
            'is_staff', 'is_superuser',
            # 計算欄位
            'permissions_summary'
        ]
        read_only_fields = ['permissions_summary', 'is_staff', 'is_superuser']


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
    class_identifier = serializers.CharField(source='get_class_identifier', read_only=True)
    test_class_name = serializers.SerializerMethodField()
    
    class Meta:
        model = OCRStorageBenchmark
        fields = [
            'id', 'project_name', 'benchmark_score', 'average_bandwidth',
            'device_model', 'firmware_version', 'test_datetime', 'benchmark_version', 'mark_version_3d',
            'ocr_confidence', 'ocr_processing_time',
            'ocr_raw_text', 'ai_structured_data',
            'test_class', 'class_sequence_id', 'test_class_name', 'class_identifier',  # 新增欄位
            'uploaded_by', 'uploaded_by_name', 'created_at', 'updated_at',
            # 計算欄位
            'performance_grade', 'summary', 'ai_data_summary'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'uploaded_by_name',
            'performance_grade', 'summary', 'ai_data_summary', 'class_identifier',
            'class_sequence_id'  # 自動生成，不可編輯
        ]
    
    def get_uploaded_by_name(self, obj):
        """獲取上傳者的友好名稱"""
        if obj.uploaded_by:
            full_name = f"{obj.uploaded_by.first_name} {obj.uploaded_by.last_name}".strip()
            return full_name if full_name else obj.uploaded_by.username
        return None
    
    def get_test_class_name(self, obj):
        """獲取測試類別名稱"""
        return obj.test_class.name if obj.test_class else None


class OCRStorageBenchmarkListSerializer(serializers.ModelSerializer):
    """AI OCR 存儲基準測試列表序列化器 - 不包含圖像資料以提升效能"""
    uploaded_by_name = serializers.SerializerMethodField()
    performance_grade = serializers.CharField(source='get_performance_grade', read_only=True)
    summary = serializers.CharField(source='get_summary', read_only=True)
    ai_data_summary = serializers.CharField(source='get_ai_data_summary', read_only=True)
    class_identifier = serializers.CharField(source='get_class_identifier', read_only=True)
    test_class_name = serializers.SerializerMethodField()
    
    class Meta:
        model = OCRStorageBenchmark
        fields = [
            'id', 'project_name', 'benchmark_score', 'average_bandwidth',
            'device_model', 'firmware_version', 'test_datetime', 'benchmark_version', 'mark_version_3d',
            'ocr_confidence', 'uploaded_by_name',
            'test_class', 'class_sequence_id', 'test_class_name', 'class_identifier',  # 新增欄位
            'created_at', 'updated_at',
            # 計算欄位
            'performance_grade', 'summary', 'ai_data_summary'
        ]
    
    def get_uploaded_by_name(self, obj):
        """獲取上傳者的友好名稱"""
        if obj.uploaded_by:
            full_name = f"{obj.uploaded_by.first_name} {obj.uploaded_by.last_name}".strip()
            return full_name if full_name else obj.uploaded_by.username
        return None
    
    def get_test_class_name(self, obj):
        """獲取測試類別名稱"""
        return obj.test_class.name if obj.test_class else None


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


# ============================================================================
# RVT Guide 序列化器已移至模組化結構
# ============================================================================
# 
# 原本在此文件中定義的序列化器已移至：
#   - RVTGuideSerializer           → library/rvt_guide/serializers/base.py
#   - RVTGuideListSerializer       → library/rvt_guide/serializers/list.py
#   - ContentImageSerializer       → library/rvt_guide/serializers/with_images.py
#   - RVTGuideWithImagesSerializer → library/rvt_guide/serializers/with_images.py
#
# 所有序列化器已在檔案開頭導入，保持向後兼容性
# 現有程式碼無需修改，可直接使用這些序列化器
#
# ============================================================================


# ============================================================================
# Protocol Guide 序列化器
# ============================================================================

class ProtocolGuideSerializer(serializers.ModelSerializer):
    """Protocol Guide 完整序列化器 - 簡化版（與 RVTGuideSerializer 結構一致）"""
    
    class Meta:
        model = ProtocolGuide
        fields = [
            'id', 'title',
            'content',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at'
        ]


class ProtocolGuideListSerializer(serializers.ModelSerializer):
    """Protocol Guide 列表序列化器 - 輕量級，用於列表視圖"""
    
    class Meta:
        model = ProtocolGuide
        fields = [
            'id', 'title',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProtocolGuideWithImagesSerializer(serializers.ModelSerializer):
    """Protocol Guide 帶圖片序列化器 - 包含關聯的圖片資訊"""
    images = ContentImageSerializer(source='get_active_images', many=True, read_only=True)
    image_count = serializers.IntegerField(source='get_image_count', read_only=True)
    has_images = serializers.BooleanField(source='has_images', read_only=True)
    primary_image = ContentImageSerializer(source='get_primary_image', read_only=True)
    
    class Meta:
        model = ProtocolGuide
        fields = [
            'id', 'title',
            'content',
            'created_at', 'updated_at',
            # 圖片相關欄位
            'images', 'image_count', 'has_images', 'primary_image'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 
                           'images', 'image_count', 'has_images', 'primary_image']


class SearchThresholdSettingSerializer(serializers.ModelSerializer):
    """搜尋 Threshold 設定序列化器"""
    
    # 唯讀欄位：顯示計算後的所有 threshold 值
    calculated_thresholds = serializers.SerializerMethodField()
    assistant_type_display = serializers.CharField(source='get_assistant_type_display', read_only=True)
    updated_by_username = serializers.CharField(source='updated_by.username', read_only=True, allow_null=True)
    
    class Meta:
        from .models import SearchThresholdSetting
        model = SearchThresholdSetting
        fields = [
            'id',
            'assistant_type',
            'assistant_type_display',
            'master_threshold',
            'title_weight',  # 新增：標題權重
            'content_weight',  # 新增：內容權重
            'calculated_thresholds',  # 計算後的所有 threshold
            'description',
            'is_active',
            'created_at',
            'updated_at',
            'updated_by',
            'updated_by_username',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'updated_by',
            'calculated_thresholds',
            'assistant_type_display',
            'updated_by_username',
        ]
    
    def get_calculated_thresholds(self, obj):
        """獲取計算後的所有 threshold 值"""
        return obj.get_calculated_thresholds()
    
    def validate_master_threshold(self, value):
        """驗證 master_threshold 範圍"""
        if value < 0 or value > 1:
            raise serializers.ValidationError("Threshold 必須在 0.00 到 1.00 之間")
        return value
    
    def validate_title_weight(self, value):
        """驗證標題權重範圍"""
        if value < 0 or value > 100:
            raise serializers.ValidationError("標題權重必須在 0 到 100 之間")
        return value
    
    def validate_content_weight(self, value):
        """驗證內容權重範圍"""
        if value < 0 or value > 100:
            raise serializers.ValidationError("內容權重必須在 0 到 100 之間")
        return value
    
    def validate(self, attrs):
        """驗證權重總和"""
        title_weight = attrs.get('title_weight', getattr(self.instance, 'title_weight', 60) if self.instance else 60)
        content_weight = attrs.get('content_weight', getattr(self.instance, 'content_weight', 40) if self.instance else 40)
        
        if title_weight + content_weight != 100:
            raise serializers.ValidationError({
                'non_field_errors': ['標題權重與內容權重的總和必須為 100%']
            })
        
        return attrs
    
    def update(self, instance, validated_data):
        """更新時自動設定 updated_by"""
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            validated_data['updated_by'] = request.user
        return super().update(instance, validated_data)
