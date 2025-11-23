from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    UserProfile, Project, Task, KnowIssue, TestClass, OCRTestClass, 
    OCRStorageBenchmark, RVTGuide, ProtocolGuide, ContentImage,
    SearchAlgorithmVersion, BenchmarkMetric, BenchmarkTestCase,
    BenchmarkTestRun, BenchmarkTestResult
)

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
            'title_weight',  # 舊欄位：標題權重（向後相容）
            'content_weight',  # 舊欄位：內容權重（向後相容）
            
            # 🆕 第一階段配置
            'stage1_threshold',
            'stage1_title_weight',
            'stage1_content_weight',
            
            # 🆕 第二階段配置
            'stage2_threshold',
            'stage2_title_weight',
            'stage2_content_weight',
            
            # 🆕 配置策略
            'use_unified_weights',
            
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
    
    # === 🆕 第一階段驗證 ===
    def validate_stage1_threshold(self, value):
        """驗證第一階段 threshold 範圍"""
        if value < 0 or value > 1:
            raise serializers.ValidationError("第一階段 Threshold 必須在 0.00 到 1.00 之間")
        return value
    
    def validate_stage1_title_weight(self, value):
        """驗證第一階段標題權重範圍"""
        if value < 0 or value > 100:
            raise serializers.ValidationError("第一階段標題權重必須在 0 到 100 之間")
        return value
    
    def validate_stage1_content_weight(self, value):
        """驗證第一階段內容權重範圍"""
        if value < 0 or value > 100:
            raise serializers.ValidationError("第一階段內容權重必須在 0 到 100 之間")
        return value
    
    # === 🆕 第二階段驗證 ===
    def validate_stage2_threshold(self, value):
        """驗證第二階段 threshold 範圍"""
        if value < 0 or value > 1:
            raise serializers.ValidationError("第二階段 Threshold 必須在 0.00 到 1.00 之間")
        return value
    
    def validate_stage2_title_weight(self, value):
        """驗證第二階段標題權重範圍"""
        if value < 0 or value > 100:
            raise serializers.ValidationError("第二階段標題權重必須在 0 到 100 之間")
        return value
    
    def validate_stage2_content_weight(self, value):
        """驗證第二階段內容權重範圍"""
        if value < 0 or value > 100:
            raise serializers.ValidationError("第二階段內容權重必須在 0 到 100 之間")
        return value
    
    def validate(self, attrs):
        """驗證權重總和（支援兩階段配置）"""
        # === 舊欄位驗證（向後相容） ===
        title_weight = attrs.get('title_weight', getattr(self.instance, 'title_weight', 60) if self.instance else 60)
        content_weight = attrs.get('content_weight', getattr(self.instance, 'content_weight', 40) if self.instance else 40)
        
        if title_weight + content_weight != 100:
            raise serializers.ValidationError({
                'non_field_errors': ['標題權重與內容權重的總和必須為 100%']
            })
        
        # === 🆕 第一階段權重驗證 ===
        stage1_title = attrs.get('stage1_title_weight', 
                                 getattr(self.instance, 'stage1_title_weight', 60) if self.instance else 60)
        stage1_content = attrs.get('stage1_content_weight',
                                   getattr(self.instance, 'stage1_content_weight', 40) if self.instance else 40)
        
        if stage1_title + stage1_content != 100:
            raise serializers.ValidationError({
                'non_field_errors': ['第一階段：標題權重與內容權重的總和必須為 100%']
            })
        
        # === 🆕 第二階段權重驗證 ===
        # 只有在不使用統一配置時才驗證第二階段
        use_unified = attrs.get('use_unified_weights',
                               getattr(self.instance, 'use_unified_weights', True) if self.instance else True)
        
        if not use_unified:
            stage2_title = attrs.get('stage2_title_weight',
                                    getattr(self.instance, 'stage2_title_weight', 50) if self.instance else 50)
            stage2_content = attrs.get('stage2_content_weight',
                                      getattr(self.instance, 'stage2_content_weight', 50) if self.instance else 50)
            
            if stage2_title + stage2_content != 100:
                raise serializers.ValidationError({
                    'non_field_errors': ['第二階段：標題權重與內容權重的總和必須為 100%']
                })
        
        return attrs
    
    def update(self, instance, validated_data):
        """更新時自動設定 updated_by"""
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            validated_data['updated_by'] = request.user
        return super().update(instance, validated_data)


# ========================================
# 搜尋演算法跑分系統 Serializers
# ========================================

class SearchAlgorithmVersionSerializer(serializers.ModelSerializer):
    """搜尋演算法版本 Serializer"""
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    test_runs_count = serializers.SerializerMethodField()
    
    class Meta:
        model = SearchAlgorithmVersion
        fields = [
            'id', 'version_name', 'version_code', 'description', 'algorithm_type',
            'parameters', 'is_active', 'is_baseline', 'created_at', 'created_by',
            'created_by_username', 'avg_precision', 'avg_recall', 'avg_response_time',
            'total_tests', 'test_runs_count'
        ]
        read_only_fields = ['created_at', 'created_by', 'test_runs_count']
    
    def get_test_runs_count(self, obj):
        """獲取測試執行次數"""
        return obj.test_runs.count()
    
    def create(self, validated_data):
        """創建時自動設定 created_by"""
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            validated_data['created_by'] = request.user
        return super().create(validated_data)


class BenchmarkMetricSerializer(serializers.ModelSerializer):
    """評分維度 Serializer"""
    
    class Meta:
        model = BenchmarkMetric
        fields = [
            'id', 'metric_name', 'metric_key', 'description', 'metric_type',
            'calculation_method', 'max_score', 'min_score', 'weight',
            'is_active', 'display_order', 'created_at'
        ]
        read_only_fields = ['created_at']


class BenchmarkTestCaseSerializer(serializers.ModelSerializer):
    """測試案例 Serializer"""
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    results_count = serializers.SerializerMethodField()
    
    class Meta:
        model = BenchmarkTestCase
        fields = [
            'id', 'question', 'question_type', 'difficulty_level',
            'expected_document_ids', 'expected_keywords', 'expected_answer_summary',
            'min_required_matches', 'acceptable_document_ids', 'category', 'tags',
            'source', 'is_active', 'is_validated', 'total_runs', 'avg_score',
            'created_at', 'updated_at', 'created_by', 'created_by_username',
            'results_count'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'results_count']
    
    def get_results_count(self, obj):
        """獲取測試結果數量"""
        return obj.results.count()
    
    def create(self, validated_data):
        """創建時自動設定 created_by"""
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            validated_data['created_by'] = request.user
        return super().create(validated_data)


class BenchmarkTestRunSerializer(serializers.ModelSerializer):
    """測試執行記錄 Serializer"""
    version = serializers.SerializerMethodField()  # 返回完整版本物件
    triggered_by_username = serializers.CharField(source='triggered_by.username', read_only=True)
    results_count = serializers.SerializerMethodField()
    passed_count = serializers.SerializerMethodField()
    failed_count = serializers.SerializerMethodField()
    pass_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = BenchmarkTestRun
        fields = [
            'id', 'version', 'run_name', 'run_type',
            'total_test_cases', 'completed_test_cases', 'status', 'overall_score',
            'avg_precision', 'avg_recall', 'avg_f1_score', 'avg_response_time',
            'started_at', 'completed_at', 'duration_seconds', 'triggered_by',
            'triggered_by_username', 'environment', 'git_commit_hash', 'notes',
            'created_at', 'results_count', 'passed_count', 'failed_count', 'pass_rate'
        ]
        read_only_fields = [
            'created_at', 'results_count', 'passed_count', 'failed_count', 'pass_rate'
        ]
    
    def get_version(self, obj):
        """返回完整的版本資訊"""
        if obj.version:
            return {
                'id': obj.version.id,
                'version_name': obj.version.version_name,
                'version_code': obj.version.version_code,
                'description': obj.version.description,
                'is_baseline': obj.version.is_baseline,
            }
        return None
    
    def create(self, validated_data):
        """創建測試執行時處理 version 欄位"""
        # version 在創建時應該從 context 或 initial_data 中獲取
        version_id = self.initial_data.get('version') or self.initial_data.get('version_id')
        if version_id:
            from api.models import SearchAlgorithmVersion
            validated_data['version'] = SearchAlgorithmVersion.objects.get(id=version_id)
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """更新測試執行時處理 version 欄位"""
        # version 在更新時不應該被修改，但如果有提供則處理
        version_id = self.initial_data.get('version') or self.initial_data.get('version_id')
        if version_id:
            from api.models import SearchAlgorithmVersion
            validated_data['version'] = SearchAlgorithmVersion.objects.get(id=version_id)
        return super().update(instance, validated_data)
    
    def get_results_count(self, obj):
        """獲取測試結果數量"""
        return obj.results.count()
    
    def get_passed_count(self, obj):
        """獲取通過的測試數量"""
        return obj.results.filter(is_passed=True).count()
    
    def get_failed_count(self, obj):
        """獲取失敗的測試數量"""
        return obj.results.filter(is_passed=False).count()
    
    def get_pass_rate(self, obj):
        """計算通過率（返回 0-1 的比例值，前端會 × 100 顯示為百分比）"""
        total = obj.results.count()
        if total == 0:
            return 0
        passed = obj.results.filter(is_passed=True).count()
        return round(passed / total, 4)  # 返回比例值（如 0.9818）而非百分比


class BenchmarkTestResultSerializer(serializers.ModelSerializer):
    """測試結果詳細 Serializer"""
    test_run_name = serializers.CharField(source='test_run.run_name', read_only=True)
    test_case_question = serializers.CharField(source='test_case.question', read_only=True)
    test_case_difficulty = serializers.CharField(source='test_case.difficulty_level', read_only=True)
    
    class Meta:
        model = BenchmarkTestResult
        fields = [
            'id', 'test_run', 'test_run_name', 'test_case', 'test_case_question',
            'test_case_difficulty', 'search_query', 'returned_document_ids',
            'returned_document_scores', 'precision_score', 'recall_score',
            'f1_score', 'ndcg_score', 'response_time', 'true_positives',
            'false_positives', 'false_negatives', 'is_passed', 'pass_reason',
            'detailed_results', 'created_at'
        ]
        read_only_fields = ['created_at']

