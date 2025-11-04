from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone


class UserProfile(models.Model):
    """使用者個人檔案擴展"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    
    # 功能權限欄位 - Web 應用功能
    web_protocol_rag = models.BooleanField(default=False, verbose_name="Web Protocol RAG 權限", 
                                          help_text="是否可使用 Web 版本的 Protocol RAG 功能")
    web_ai_ocr = models.BooleanField(default=False, verbose_name="Web AI OCR 權限", 
                                    help_text="是否可使用 Web 版本的 AI OCR 功能")
    web_rvt_assistant = models.BooleanField(default=False, verbose_name="Web RVT Assistant 權限", 
                                           help_text="是否可使用 Web 版本的 RVT Assistant 功能")
    web_protocol_assistant = models.BooleanField(default=False, verbose_name="Web Protocol Assistant 權限", 
                                                 help_text="是否可使用 Web 版本的 Protocol Assistant 功能")
    
    # 功能權限欄位 - 知識庫功能
    kb_protocol_rag = models.BooleanField(default=False, verbose_name="知識庫 Protocol RAG 權限", 
                                         help_text="是否可使用知識庫版本的 Protocol RAG 功能")
    kb_ai_ocr = models.BooleanField(default=False, verbose_name="知識庫 AI OCR 權限", 
                                   help_text="是否可使用知識庫版本的 AI OCR 功能")
    kb_rvt_assistant = models.BooleanField(default=False, verbose_name="知識庫 RVT Assistant 權限", 
                                          help_text="是否可使用知識庫版本的 RVT Assistant 功能")
    kb_protocol_assistant = models.BooleanField(default=False, verbose_name="知識庫 Protocol Assistant 權限", 
                                               help_text="是否可使用知識庫版本的 Protocol Assistant 功能")
    
    # 管理權限欄位
    is_super_admin = models.BooleanField(default=False, verbose_name="超級管理員", 
                                        help_text="超級管理員可以管理所有用戶的權限設定")
    
    # 原有欄位
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def get_permissions_summary(self):
        """獲取權限摘要"""
        permissions = []
        if self.web_protocol_rag:
            permissions.append("Web Protocol RAG")
        if self.web_ai_ocr:
            permissions.append("Web AI OCR")
        if self.web_rvt_assistant:
            permissions.append("Web RVT Assistant")
        if self.web_protocol_assistant:
            permissions.append("Web Protocol Assistant")
        if self.kb_protocol_rag:
            permissions.append("KB Protocol RAG")
        if self.kb_ai_ocr:
            permissions.append("KB AI OCR")
        if self.kb_rvt_assistant:
            permissions.append("KB RVT Assistant")
        if self.kb_protocol_assistant:
            permissions.append("KB Protocol Assistant")
        
        if self.is_super_admin:
            permissions.append("超級管理員")
        
        return ", ".join(permissions) if permissions else "無特殊權限"
    
    def has_any_web_permission(self):
        """檢查是否擁有任何 Web 功能權限"""
        return any([self.web_protocol_rag, self.web_ai_ocr, self.web_rvt_assistant, self.web_protocol_assistant])
    
    def has_any_kb_permission(self):
        """檢查是否擁有任何知識庫功能權限"""
        return any([self.kb_protocol_rag, self.kb_ai_ocr, self.kb_rvt_assistant, self.kb_protocol_assistant])
    
    def can_manage_permissions(self):
        """檢查是否可以管理其他用戶權限"""
        return self.is_super_admin or self.user.is_superuser


class Project(models.Model):
    """專案模型"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_projects')
    members = models.ManyToManyField(User, related_name='member_projects', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class Task(models.Model):
    """任務模型"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks')
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    due_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class DifyEmployee(models.Model):
    """員工模型 - 用於 Dify 知識庫查詢演示（保留原有複雜模型）"""
    name = models.CharField(max_length=100, verbose_name="姓名")
    email = models.EmailField(unique=True, verbose_name="電子郵件")
    department = models.CharField(max_length=100, verbose_name="部門")
    position = models.CharField(max_length=100, verbose_name="職位")
    skills = models.TextField(blank=True, verbose_name="技能")
    phone = models.CharField(max_length=20, blank=True, verbose_name="電話")
    hire_date = models.DateField(verbose_name="入職日期")
    is_active = models.BooleanField(default=True, verbose_name="是否在職")
    
    # 照片直接存儲在資料庫中
    photo_binary = models.BinaryField(blank=True, null=True, verbose_name="員工照片二進位資料")
    photo_filename = models.CharField(max_length=255, blank=True, verbose_name="照片檔名")
    photo_content_type = models.CharField(max_length=100, blank=True, verbose_name="照片類型")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = "Dify員工"
        verbose_name_plural = "Dify員工"
        db_table = 'dify_employee'

    def __str__(self):
        return f"{self.name} - {self.position}"
    
    def get_full_info(self):
        """獲取完整的員工資訊文本"""
        info = f"姓名: {self.name}\n"
        info += f"部門: {self.department}\n"
        info += f"職位: {self.position}\n"
        info += f"Email: {self.email}\n"


class Employee(models.Model):
    """簡化員工模型 - 僅包含 id 和 name"""
    name = models.CharField(max_length=100, verbose_name="姓名")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = "員工"
        verbose_name_plural = "員工"
        db_table = 'employee'

    def __str__(self):
        return self.name
        if self.phone:
            info += f"電話: {self.phone}\n"
        if self.skills:
            info += f"技能: {self.skills}\n"
        info += f"入職日期: {self.hire_date}\n"
        info += f"狀態: {'在職' if self.is_active else '離職'}"
        
        # 添加照片資訊
        if self.photo_binary:
            import math
            size_kb = math.ceil(len(self.photo_binary) / 1024)
            info += f"\n照片: 已存儲在資料庫中 ({self.photo_filename}, {size_kb}KB)"
            
        return info
    
    def save_photo_to_db(self, image_path):
        """將照片檔案讀取並存入資料庫"""
        try:
            with open(image_path, 'rb') as f:
                self.photo_binary = f.read()
                self.photo_filename = image_path.split('/')[-1]
                # 根據副檔名判斷類型
                if image_path.lower().endswith('.jpg') or image_path.lower().endswith('.jpeg'):
                    self.photo_content_type = 'image/jpeg'
                elif image_path.lower().endswith('.png'):
                    self.photo_content_type = 'image/png'
                else:
                    self.photo_content_type = 'image/jpeg'  # 預設
                self.save()
                return True
        except Exception as e:
            print(f"存儲照片失敗: {e}")
            return False
    
    def get_photo_data_url(self):
        """獲取可用於 HTML 的 data URL"""
        if self.photo_binary:
            import base64
            encoded = base64.b64encode(self.photo_binary).decode('utf-8')
            return f"data:{self.photo_content_type};base64,{encoded}"
        return None
    
    def get_photo_url(self):
        """獲取照片 URL（資料庫存儲版本）"""
        if self.photo_binary:
            return f"data:image;base64,{len(self.photo_binary)} bytes stored in database"
        return None


class KnowIssue(models.Model):
    """問題知識庫模型"""
    
    # 基本資訊
    issue_id = models.CharField(max_length=50, unique=True, verbose_name="Issue ID", help_text="唯一的問題識別碼")
    test_version = models.CharField(max_length=100, verbose_name="測試版本", help_text="發現問題的測試版本")
    jira_number = models.CharField(max_length=50, blank=True, verbose_name="JIRA 號碼", help_text="相關的 JIRA 票號")
    
    # 人員與專案
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="更新人員", related_name="updated_issues")
    project = models.CharField(max_length=200, verbose_name="Project", help_text="相關專案名稱")
    
    # 分類資訊
    test_class = models.ForeignKey('TestClass', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="測試類別", help_text="問題所屬的測試類別")
    class_sequence_id = models.PositiveIntegerField(null=True, blank=True, verbose_name="類別序號", help_text="在該測試類別內的遞增ID號碼")
    
    # 技術資訊
    script = models.TextField(blank=True, verbose_name="Script", help_text="相關腳本或代碼")
    issue_type = models.CharField(max_length=50, verbose_name="Issue Type", help_text="問題類型，如 Bug, Feature Request, Improvement 等")
    status = models.CharField(max_length=50, verbose_name="修復狀態", help_text="狀態描述，如 開放中, 處理中, 已解決 等")
    
    # 問題描述
    error_message = models.TextField(verbose_name="錯誤訊息", help_text="具體的錯誤訊息內容")
    supplement = models.TextField(blank=True, verbose_name="補充", help_text="額外的補充說明或解決方案")
    
    # 圖片附件 (5張圖片支援 - 二進制存儲)
    image1_data = models.BinaryField(blank=True, null=True, verbose_name="圖片1數據", help_text="第1張附件圖片的二進制數據")
    image1_filename = models.CharField(max_length=255, blank=True, verbose_name="圖片1檔名")
    image1_content_type = models.CharField(max_length=100, blank=True, verbose_name="圖片1類型")
    
    image2_data = models.BinaryField(blank=True, null=True, verbose_name="圖片2數據", help_text="第2張附件圖片的二進制數據")
    image2_filename = models.CharField(max_length=255, blank=True, verbose_name="圖片2檔名")
    image2_content_type = models.CharField(max_length=100, blank=True, verbose_name="圖片2類型")
    
    image3_data = models.BinaryField(blank=True, null=True, verbose_name="圖片3數據", help_text="第3張附件圖片的二進制數據")
    image3_filename = models.CharField(max_length=255, blank=True, verbose_name="圖片3檔名")
    image3_content_type = models.CharField(max_length=100, blank=True, verbose_name="圖片3類型")
    
    image4_data = models.BinaryField(blank=True, null=True, verbose_name="圖片4數據", help_text="第4張附件圖片的二進制數據")
    image4_filename = models.CharField(max_length=255, blank=True, verbose_name="圖片4檔名")
    image4_content_type = models.CharField(max_length=100, blank=True, verbose_name="圖片4類型")
    
    image5_data = models.BinaryField(blank=True, null=True, verbose_name="圖片5數據", help_text="第5張附件圖片的二進制數據")
    image5_filename = models.CharField(max_length=255, blank=True, verbose_name="圖片5檔名")
    image5_content_type = models.CharField(max_length=100, blank=True, verbose_name="圖片5類型")
    
    # 時間戳記
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")
    
    class Meta:
        ordering = ['-updated_at', '-created_at']
        verbose_name = "問題知識"
        verbose_name_plural = "問題知識庫"
        db_table = 'know_issue'
    
    def __str__(self):
        return f"[{self.issue_id}] {self.project} - {self.issue_type}"
    
    def save(self, *args, **kwargs):
        """自動生成 Issue ID"""
        if not self.issue_id and self.test_class:
            # 獲取該測試類別下一個可用的 ID
            last_issue = KnowIssue.objects.filter(
                test_class=self.test_class
            ).order_by('-class_sequence_id').first()
            
            next_id = 1 if not last_issue else (last_issue.class_sequence_id or 0) + 1
            self.class_sequence_id = next_id
            
            # 生成 Issue ID 格式: {test_class_name}-{id}
            test_class_name = self.test_class.name.replace(' ', '_')
            self.issue_id = f"{test_class_name}-{next_id}"
        
        super().save(*args, **kwargs)
    
    def get_summary(self):
        """獲取問題摘要"""
        return f"Issue ID: {self.issue_id} | Project: {self.project} | Status: {self.status}"
    
    def get_image_list(self):
        """獲取所有已上傳的圖片列表（二進制版本）"""
        import base64
        images = []
        for i in range(1, 6):  # image1 到 image5
            data_field = getattr(self, f'image{i}_data')
            filename_field = getattr(self, f'image{i}_filename')
            content_type_field = getattr(self, f'image{i}_content_type')
            
            if data_field and filename_field:
                # 生成 base64 data URL
                base64_data = base64.b64encode(data_field).decode('utf-8')
                data_url = f"data:{content_type_field or 'image/jpeg'};base64,{base64_data}"
                
                images.append({
                    'field': f'image{i}',
                    'data_url': data_url,
                    'filename': filename_field,
                    'content_type': content_type_field,
                    'size_kb': len(data_field) // 1024
                })
        return images
    
    def get_image_urls(self):
        """獲取所有圖片的 data URL 列表"""
        image_list = self.get_image_list()
        return [img['data_url'] for img in image_list]
    
    def get_image_count(self):
        """獲取已上傳圖片的數量"""
        count = 0
        for i in range(1, 6):
            data_field = getattr(self, f'image{i}_data')
            if data_field:
                count += 1
        return count
    
    def set_image_data(self, image_index, file_data, filename, content_type):
        """設置圖片數據的輔助方法"""
        if 1 <= image_index <= 5:
            setattr(self, f'image{image_index}_data', file_data)
            setattr(self, f'image{image_index}_filename', filename)
            setattr(self, f'image{image_index}_content_type', content_type)
    
    def clear_image_data(self, image_index):
        """清除特定圖片數據的輔助方法"""
        if 1 <= image_index <= 5:
            setattr(self, f'image{image_index}_data', None)
            setattr(self, f'image{image_index}_filename', '')
            setattr(self, f'image{image_index}_content_type', '')


class TestClass(models.Model):
    """測試類別模型 - Admin 專用管理"""
    name = models.CharField(max_length=200, unique=True, verbose_name="類別名稱")
    description = models.TextField(blank=True, verbose_name="描述")
    is_active = models.BooleanField(default=True, verbose_name="是否啟用")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="建立者")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "測試類別"
        verbose_name_plural = "測試類別"
        db_table = 'protocol_test_class'

    def __str__(self):
        return self.name


class OCRTestClass(models.Model):
    """OCR 測試類別模型 - Admin 專用管理"""
    name = models.CharField(max_length=200, unique=True, verbose_name="OCR類別名稱")
    description = models.TextField(blank=True, verbose_name="描述")
    is_active = models.BooleanField(default=True, verbose_name="是否啟用")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="建立者")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "OCR測試類別"
        verbose_name_plural = "OCR測試類別"
        db_table = 'ocr_test_class'

    def __str__(self):
        return self.name


class ChatUsage(models.Model):
    """聊天使用記錄模型 - 用於統計分析"""
    CHAT_TYPE_CHOICES = [
        ('know_issue_chat', 'Protocol RAG'),
        ('log_analyze_chat', 'AI OCR'),
        ('rvt_assistant_chat', 'RVT Assistant'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="用戶")
    session_id = models.CharField(max_length=255, blank=True, verbose_name="會話ID")
    chat_type = models.CharField(max_length=50, choices=CHAT_TYPE_CHOICES, verbose_name="聊天類型")
    message_count = models.PositiveIntegerField(default=1, verbose_name="消息數量")
    has_file_upload = models.BooleanField(default=False, verbose_name="是否包含文件上傳")
    response_time = models.FloatField(null=True, blank=True, verbose_name="響應時間(秒)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="使用時間")
    
    # IP 和瀏覽器信息
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP地址")
    user_agent = models.TextField(blank=True, verbose_name="用戶代理")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "聊天使用記錄"
        verbose_name_plural = "聊天使用記錄"
        db_table = 'chat_usage'
        indexes = [
            models.Index(fields=['chat_type', 'created_at']),
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        user_display = self.user.username if self.user else "匿名用戶"
        return f"{user_display} - {self.get_chat_type_display()} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class OCRStorageBenchmark(models.Model):
    """AI OCR 存儲基準測試資料模型"""
    
    # 基本資訊
    project_name = models.CharField(max_length=200, verbose_name="專案名稱", help_text="測試專案的名稱")
    
    # 分類資訊 - 仿效 KnowIssue 的實作方式
    test_class = models.ForeignKey('OCRTestClass', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="OCR測試類別", help_text="基準測試所屬的OCR測試類別")
    class_sequence_id = models.PositiveIntegerField(null=True, blank=True, verbose_name="類別序號", help_text="在該OCR測試類別內的遞增ID號碼")
    
    # 測試結果
    benchmark_score = models.IntegerField(verbose_name="存儲基準分數", help_text="Storage Benchmark Score")
    average_bandwidth = models.CharField(max_length=50, verbose_name="平均帶寬", help_text="平均帶寬 (MB/s)")
    
    # 硬體資訊
    device_model = models.CharField(max_length=200, verbose_name="裝置型號", help_text="測試裝置的型號名稱")
    firmware_version = models.CharField(max_length=100, verbose_name="韌體版本", help_text="裝置韌體版本號")
    
    # 測試資訊
    test_datetime = models.DateTimeField(null=True, blank=True, verbose_name="測試時間", help_text="進行測試的具體時間")
    benchmark_version = models.CharField(max_length=50, verbose_name="基準版本", help_text="3DMark 或其他基準測試軟體版本")
    mark_version_3d = models.CharField(max_length=50, blank=True, verbose_name="3DMark版本", help_text="3DMark 軟體的具體版本號")
    

    
    # OCR 處理相關欄位
    ocr_confidence = models.FloatField(null=True, blank=True, verbose_name="OCR 信心度", help_text="OCR 識別的信心度分數 (0-1)")
    ocr_processing_time = models.FloatField(null=True, blank=True, verbose_name="OCR 處理時間 (秒)", help_text="OCR 處理所需的時間")
    

    
    # OCR 提取的原始文本
    ocr_raw_text = models.TextField(blank=True, verbose_name="OCR 原始文本", help_text="OCR 直接提取的原始文本內容")
    
    # AI 處理後的結構化資料 (JSON格式)
    ai_structured_data = models.JSONField(blank=True, null=True, verbose_name="AI 結構化資料", help_text="AI 處理後的結構化 JSON 資料")
    

    

    
    # 時間戳記
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="上傳者", related_name="uploaded_ocr_records")
    
    class Meta:
        ordering = ['-test_datetime', '-created_at']  # NULL值会排在最后
        verbose_name = "AI OCR 存儲基準測試"
        verbose_name_plural = "AI OCR 存儲基準測試"
        db_table = 'ocr_storage_benchmark'
        indexes = [
            models.Index(fields=['test_datetime', 'project_name']),
            models.Index(fields=['device_model', 'firmware_version']),
            models.Index(fields=['test_class', 'class_sequence_id']),  # 新增索引
        ]
    
    def __str__(self):
        class_info = f"[{self.get_class_identifier()}]" if self.get_class_identifier() else ""
        date_info = self.test_datetime.strftime('%Y-%m-%d') if self.test_datetime else '未知時間'
        return f"{class_info}[{self.project_name}] {self.device_model} - {self.benchmark_score}分 ({date_info})"
    
    def get_summary(self):
        """獲取測試摘要"""
        return f"專案: {self.project_name} | 裝置: {self.device_model} | 分數: {self.benchmark_score} | 平均帶寬: {self.average_bandwidth}"
    
    def get_performance_grade(self):
        """根據基準分數評估效能等級"""
        if self.benchmark_score >= 8000:
            return "優秀"
        elif self.benchmark_score >= 6000:
            return "良好"
        elif self.benchmark_score >= 4000:
            return "一般"
        elif self.benchmark_score >= 2000:
            return "待改善"
        else:
            return "需優化"
    

    
    def get_ai_data_summary(self):
        """獲取 AI 結構化資料摘要"""
        if self.ai_structured_data:
            # 從JSON中提取關鍵資訊
            data = self.ai_structured_data
            summary = []
            
            if isinstance(data, dict):
                for key, value in data.items():
                    if key.lower() in ['score', 'benchmark_score', 'storage_score']:
                        summary.append(f"分數: {value}")
                    elif key.lower() in ['bandwidth', 'average_bandwidth']:
                        summary.append(f"帶寬: {value}")
                    elif key.lower() in ['device', 'model', 'device_model']:
                        summary.append(f"裝置: {value}")
            
            return " | ".join(summary) if summary else "結構化資料已存在"
        return "無結構化資料"
    
    def save(self, *args, **kwargs):
        """自動生成類別序號 - 仿效 KnowIssue 的實作方式"""
        if not self.class_sequence_id and self.test_class:
            # 獲取該OCR測試類別下一個可用的序號
            last_benchmark = OCRStorageBenchmark.objects.filter(
                test_class=self.test_class
            ).order_by('-class_sequence_id').first()
            
            next_id = 1 if not last_benchmark else (last_benchmark.class_sequence_id or 0) + 1
            self.class_sequence_id = next_id
        
        super().save(*args, **kwargs)
    
    def get_class_identifier(self):
        """獲取類別識別碼 - 格式: {test_class_name}-{sequence_id}"""
        if self.test_class and self.class_sequence_id:
            test_class_name = self.test_class.name.replace(' ', '_')
            return f"{test_class_name}-{self.class_sequence_id}"
        return None


class RVTGuide(models.Model):
    """RVT 使用指南知識庫模型"""
    
    # 基本識別欄位
    title = models.CharField(max_length=300, verbose_name="文檔標題", help_text="文檔的顯示標題")
    
    # 內容欄位
    content = models.TextField(verbose_name="文檔內容", help_text="文檔的主要內容")
    

    

    
    # 時間戳記
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")
    
    class Meta:
        ordering = ['title']
        verbose_name = "RVT使用指南"
        verbose_name_plural = "RVT使用指南"
        db_table = 'rvt_guide'
    
    def __str__(self):
        return self.title
    
    def get_search_content(self):
        """獲取用於搜索的完整內容"""
        search_text = f"{self.title} {self.content}"
        return search_text
    
    def get_active_images(self):
        """獲取所有啟用的圖片"""
        return self.images.filter(is_active=True).order_by('display_order')
    
    def get_primary_image(self):
        """獲取主要圖片"""
        return self.images.filter(is_primary=True, is_active=True).first()
    
    def get_image_count(self):
        """獲取圖片數量"""
        return self.images.filter(is_active=True).count()
    
    def has_images(self):
        """是否有圖片"""
        return self.get_image_count() > 0
    
    def get_images_summary(self):
        """獲取圖片摘要資訊（用於向量化）"""
        images = self.get_active_images()
        if not images.exists():
            return ""
        
        summaries = []
        for img in images:
            parts = [f"圖片{img.display_order}"]
            if img.title:
                parts.append(f"標題:{img.title}")
            if img.description:
                parts.append(f"說明:{img.description}")
            parts.append(f"檔案:{img.filename}")
            summaries.append(" ".join(parts))
        
        return f"包含{len(summaries)}張圖片: " + "; ".join(summaries)
    
    def set_primary_image(self, image_id):
        """設定主要圖片"""
        # 清除現有主要圖片
        self.images.filter(is_primary=True).update(is_primary=False)
        # 設定新的主要圖片
        self.images.filter(id=image_id).update(is_primary=True)
    
    def reorder_images(self, image_ids):
        """重新排序圖片"""
        for index, image_id in enumerate(image_ids, 1):
            self.images.filter(id=image_id).update(display_order=index)
    
    def update_content_with_images(self):
        """自動更新內容以包含圖片引用"""
        images = self.get_active_images()
        
        # 移除現有的圖片區塊
        content = self.content
        
        # 尋找並移除現有的圖片區塊 (以 --- 相關圖片 --- 開始)
        import re
        content = re.sub(r'\n*---+ *相關圖片 *---+.*?(?=\n\n|\Z)', '', content, flags=re.DOTALL)
        content = content.rstrip()
        
        # 如果有圖片，添加圖片區塊
        if images.exists():
            image_section = "\n\n--- 相關圖片 ---\n"
            for img in images:
                image_info = []
                if img.is_primary:
                    image_info.append("📌 主要圖片")
                if img.title:
                    image_info.append(f"標題: {img.title}")
                if img.description:
                    image_info.append(f"說明: {img.description}")
                
                image_line = f"🖼️ {img.filename}"
                if image_info:
                    image_line += f" ({', '.join(image_info)})"
                
                image_section += f"{image_line}\n"
            
            content += image_section
        
        # 更新內容並儲存
        self.content = content
        self.save(update_fields=['content', 'updated_at'])


class ProtocolGuide(models.Model):
    """Protocol 測試指南知識庫模型 - 簡化版（與 RVTGuide 結構一致）"""
    
    # 基本識別欄位
    title = models.CharField(max_length=300, verbose_name="文檔標題", help_text="文檔的顯示標題")
    
    # 內容欄位
    content = models.TextField(verbose_name="文檔內容", help_text="文檔的主要內容")
    
    # 時間戳記
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")
    
    class Meta:
        ordering = ['title']
        verbose_name = "Protocol 測試指南"
        verbose_name_plural = "Protocol 測試指南"
        db_table = 'protocol_guide'
    
    def __str__(self):
        return self.title
    
    def get_search_content(self):
        """獲取用於搜索的完整內容"""
        search_text = f"{self.title} {self.content}"
        return search_text
    
    def get_active_images(self):
        """獲取所有啟用的圖片（使用通用內容類型）"""
        from django.contrib.contenttypes.models import ContentType
        content_type = ContentType.objects.get_for_model(self)
        return ContentImage.objects.filter(
            content_type=content_type,
            object_id=self.id,
            is_active=True
        ).order_by('display_order')
    
    def get_primary_image(self):
        """獲取主要圖片"""
        return self.get_active_images().filter(is_primary=True).first()
    
    def get_image_count(self):
        """獲取圖片數量"""
        return self.get_active_images().count()
    
    def has_images(self):
        """是否有圖片"""
        return self.get_image_count() > 0
    
    def get_images_summary(self):
        """獲取圖片摘要資訊（用於向量化和前端顯示）"""
        images = self.get_active_images()
        if not images.exists():
            return ""
        
        summaries = []
        for img in images:
            # ✅ 修復：使用前端可識別的格式 🖼️ filename
            # 同時保留說明資訊供 AI 參考
            # 優先放入能被前端解析的格式：包含 IMG:id 與實際檔名
            # 範例：🖼️ [IMG:33] kisspng-xxxx.png (說明)
            display_name = img.filename or img.title or f"image_{img.id}"
            parts = [f"🖼️ [IMG:{img.id}] {display_name}"]
            if img.description:
                parts.append(f"({img.description})")  # 附加：說明資訊
            summaries.append(" ".join(parts))
        
        return f"包含{len(summaries)}張圖片: " + "; ".join(summaries)


class ContentImage(models.Model):
    """通用內容圖片模型 - 可用於不同類型的內容"""
    
    # 通用內容類型關聯 (使用 GenericForeignKey 支援多種模型)
    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE,
        verbose_name="內容類型"
    )
    object_id = models.PositiveIntegerField(verbose_name="對象ID")
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # 為了向後兼容和查詢效能，保留直接關聯到 RVTGuide 的外鍵
    rvt_guide = models.ForeignKey(
        RVTGuide,
        on_delete=models.CASCADE,
        related_name='images',
        null=True,
        blank=True,
        verbose_name="關聯的 RVT Guide"
    )
    
    # Protocol Guide 直接關聯
    protocol_guide = models.ForeignKey(
        'ProtocolGuide',
        on_delete=models.CASCADE,
        related_name='images',
        null=True,
        blank=True,
        verbose_name="關聯的 Protocol Guide"
    )
    
    # 圖片基本資訊
    title = models.CharField(
        max_length=200, 
        blank=True, 
        null=True, 
        verbose_name="圖片標題",
        help_text="可選的圖片說明標題"
    )
    
    description = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="圖片描述",
        help_text="可選的詳細描述"
    )
    
    # 圖片檔案資訊
    filename = models.CharField(max_length=255, verbose_name="檔案名稱")
    content_type_mime = models.CharField(max_length=100, verbose_name="MIME類型")
    file_size = models.IntegerField(verbose_name="檔案大小(bytes)")
    
    # 圖片二進制資料
    image_data = models.BinaryField(verbose_name="圖片資料")
    
    # 圖片元資料
    width = models.IntegerField(null=True, blank=True, verbose_name="寬度")
    height = models.IntegerField(null=True, blank=True, verbose_name="高度")
    
    # 排序和狀態
    display_order = models.IntegerField(
        default=1, 
        verbose_name="顯示順序",
        help_text="數字越小越前面"
    )
    
    is_primary = models.BooleanField(
        default=False, 
        verbose_name="是否為主要圖片",
        help_text="用於縮圖顯示等"
    )
    
    is_active = models.BooleanField(
        default=True, 
        verbose_name="是否啟用",
        help_text="停用的圖片不會在前端顯示"
    )
    
    # 時間戳記
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="上傳時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")
    
    class Meta:
        ordering = ['display_order', 'created_at']
        verbose_name = "內容圖片"
        verbose_name_plural = "內容圖片"
        indexes = [
            models.Index(fields=['content_type', 'object_id', 'display_order']),
            models.Index(fields=['content_type', 'object_id', 'is_active']),
            models.Index(fields=['rvt_guide', 'display_order']),
            models.Index(fields=['rvt_guide', 'is_active']),
            models.Index(fields=['protocol_guide', 'display_order']),
            models.Index(fields=['protocol_guide', 'is_active']),
            models.Index(fields=['is_primary']),
        ]
    
    def __str__(self):
        if self.rvt_guide:
            return f"{self.rvt_guide.title} - {self.filename}"
        if self.protocol_guide:
            return f"{self.protocol_guide.title} - {self.filename}"
        return f"圖片 - {self.filename}"
    
    def get_data_url(self):
        """生成 data URL"""
        import base64
        if self.image_data:
            base64_data = base64.b64encode(self.image_data).decode('utf-8')
            return f"data:{self.content_type_mime};base64,{base64_data}"
        return None
    
    def get_size_display(self):
        """友好的檔案大小顯示"""
        size_kb = self.file_size // 1024
        if size_kb < 1024:
            return f"{size_kb} KB"
        else:
            size_mb = size_kb / 1024
            return f"{size_mb:.1f} MB"
    
    def get_dimensions_display(self):
        """尺寸顯示"""
        if self.width and self.height:
            return f"{self.width} × {self.height}"
        return "未知"
    
    @classmethod
    def create_from_upload(cls, content_object, uploaded_file, title=None, description=None):
        """從上傳的檔案創建圖片記錄"""
        from PIL import Image
        import io
        from django.contrib.contenttypes.models import ContentType
        
        # 讀取檔案資料
        file_data = uploaded_file.read()
        
        # 獲取圖片尺寸
        width, height = None, None
        try:
            image = Image.open(io.BytesIO(file_data))
            width, height = image.size
        except Exception:
            pass  # 如果無法讀取尺寸，保持 None
        
        # 取得下一個排序順序
        content_type = ContentType.objects.get_for_model(content_object)
        next_order = (cls.objects.filter(
            content_type=content_type, 
            object_id=content_object.pk
        ).aggregate(models.Max('display_order'))['display_order__max'] or 0) + 1
        
        # 創建記錄
        image_instance = cls.objects.create(
            content_object=content_object,
            title=title or uploaded_file.name,
            description=description,
            filename=uploaded_file.name,
            content_type_mime=uploaded_file.content_type,
            file_size=len(file_data),
            image_data=file_data,
            width=width,
            height=height,
            display_order=next_order,
            is_primary=next_order == 1  # 第一張圖片設為主要圖片
        )
        
        # 如果是 RVTGuide，同時設定 rvt_guide 外鍵以保持向後兼容
        if isinstance(content_object, RVTGuide):
            image_instance.rvt_guide = content_object
            image_instance.save()
        
        # 如果是 ProtocolGuide，設定 protocol_guide 外鍵
        if isinstance(content_object, ProtocolGuide):
            image_instance.protocol_guide = content_object
            image_instance.save()
        
        return image_instance


class ConversationSession(models.Model):
    """對話會話模型 - 記錄每個對話會話的基本資訊"""
    
    # 對話識別
    session_id = models.CharField(max_length=255, unique=True, verbose_name="會話ID")
    
    # 用戶關聯（支援訪客）
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name="用戶")
    guest_identifier = models.CharField(max_length=255, blank=True, verbose_name="訪客標識")
    is_guest_session = models.BooleanField(default=False, verbose_name="是否為訪客會話")
    
    # 對話分類
    chat_type = models.CharField(max_length=50, default='rvt_assistant_chat', verbose_name="聊天類型")
    
    # 對話資訊
    title = models.CharField(max_length=500, blank=True, verbose_name="對話標題")
    summary = models.TextField(blank=True, verbose_name="對話摘要")
    
    # 統計資訊
    message_count = models.PositiveIntegerField(default=0, verbose_name="訊息總數")
    total_tokens = models.PositiveIntegerField(default=0, verbose_name="Token總使用量")
    total_response_time = models.FloatField(default=0, verbose_name="總回應時間(秒)")
    satisfaction_score = models.FloatField(null=True, blank=True, verbose_name="滿意度分數")
    
    # 狀態管理
    is_active = models.BooleanField(default=True, verbose_name="是否活躍")
    is_archived = models.BooleanField(default=False, verbose_name="是否已歸檔")
    
    # 時間戳記
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")
    last_message_at = models.DateTimeField(null=True, blank=True, verbose_name="最後訊息時間")
    
    # 訪客資料自動清除（可選）
    auto_delete_at = models.DateTimeField(null=True, blank=True, verbose_name="自動刪除時間")
    
    class Meta:
        ordering = ['-last_message_at', '-created_at']
        verbose_name = "對話會話"
        verbose_name_plural = "對話會話"
        db_table = 'conversation_sessions'
        indexes = [
            models.Index(fields=['user', '-created_at'], name='conv_user_created_idx'),
            models.Index(fields=['session_id'], name='conv_session_id_idx'),
            models.Index(fields=['chat_type', 'is_active'], name='conv_type_active_idx'),
            models.Index(fields=['-last_message_at'], name='conv_last_msg_idx'),
            models.Index(fields=['guest_identifier'], name='conv_guest_id_idx'),
        ]
    
    def __str__(self):
        if self.user:
            user_display = self.user.username
        elif self.guest_identifier:
            user_display = f"訪客({self.guest_identifier[:8]})"
        else:
            user_display = "未知用戶"
        
        title_display = self.title or f"{self.get_chat_type_display()}"
        return f"{user_display} - {title_display}"
    
    def get_chat_type_display(self):
        """獲取聊天類型顯示名稱"""
        type_mapping = {
            'rvt_assistant_chat': 'RVT Assistant',
            'know_issue_chat': 'Protocol RAG',
            'log_analyze_chat': 'AI OCR',
        }
        return type_mapping.get(self.chat_type, self.chat_type)
    
    def update_stats(self):
        """更新統計資訊"""
        from django.db.models import Count, Sum
        from django.utils import timezone
        from django.db.models.functions import Cast
        from django.db.models import IntegerField
        
        # 基本統計
        basic_stats = self.chatmessage_set.aggregate(
            count=Count('id'),
            total_time=Sum('response_time')
        )
        
        # 分別計算 token 統計（避免 JSONB 欄位問題）
        total_tokens = 0
        try:
            messages_with_tokens = self.chatmessage_set.exclude(token_usage__isnull=True)
            for msg in messages_with_tokens:
                if msg.token_usage and isinstance(msg.token_usage, dict):
                    tokens = msg.token_usage.get('total_tokens', 0)
                    if isinstance(tokens, (int, float)):
                        total_tokens += int(tokens)
        except Exception as e:
            # 如果 token 統計失敗，記錄但不影響其他統計
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Token統計計算失敗: {str(e)}")
            total_tokens = 0
        
        self.message_count = basic_stats['count'] or 0
        self.total_tokens = total_tokens
        self.total_response_time = basic_stats['total_time'] or 0
        self.last_message_at = timezone.now()
        self.save(update_fields=['message_count', 'total_tokens', 'total_response_time', 'last_message_at'])


class ChatMessage(models.Model):
    """對話訊息模型 - 記錄每條訊息的詳細內容"""
    
    ROLE_CHOICES = [
        ('user', '用戶訊息'),
        ('assistant', 'AI回覆'),
        ('system', '系統訊息'),
    ]
    
    CONTENT_TYPE_CHOICES = [
        ('text', '純文字'),
        ('markdown', 'Markdown'),
        ('json', 'JSON'),
    ]
    
    # 對話關聯
    conversation = models.ForeignKey(ConversationSession, on_delete=models.CASCADE, verbose_name="所屬對話")
    
    # 訊息識別
    message_id = models.CharField(max_length=255, blank=True, verbose_name="訊息ID")
    
    # 訊息分類
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, verbose_name="訊息角色")
    
    # 訊息內容
    content = models.TextField(verbose_name="訊息內容")
    content_type = models.CharField(max_length=50, choices=CONTENT_TYPE_CHOICES, default='text', verbose_name="內容類型")
    
    # 順序管理
    sequence_number = models.PositiveIntegerField(verbose_name="順序號碼")
    
    # AI 相關資料（僅 assistant 訊息）
    response_time = models.FloatField(null=True, blank=True, verbose_name="回應時間(秒)")
    token_usage = models.JSONField(null=True, blank=True, verbose_name="Token使用統計")
    confidence_score = models.FloatField(null=True, blank=True, verbose_name="信心分數")
    
    # Dify 元資料
    metadata = models.JSONField(null=True, blank=True, verbose_name="元資料")
    
    # 編輯功能
    is_edited = models.BooleanField(default=False, verbose_name="是否已編輯")
    original_content = models.TextField(blank=True, verbose_name="原始內容")
    edit_history = models.JSONField(null=True, blank=True, verbose_name="編輯歷史")
    
    # 標記功能
    is_bookmarked = models.BooleanField(default=False, verbose_name="是否收藏")
    is_helpful = models.BooleanField(null=True, blank=True, verbose_name="是否有幫助")
    
    # 問題分類（僅用戶訊息）
    question_category = models.CharField(max_length=100, null=True, blank=True, verbose_name="問題分類")
    
    # 時間戳記
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")
    
    class Meta:
        ordering = ['conversation', 'sequence_number']
        verbose_name = "對話訊息"
        verbose_name_plural = "對話訊息"
        db_table = 'chat_messages'
        unique_together = [['conversation', 'sequence_number']]
        indexes = [
            models.Index(fields=['conversation', 'sequence_number'], name='msg_conv_seq_idx'),
            models.Index(fields=['role', '-created_at'], name='msg_role_created_idx'),
            models.Index(fields=['-created_at'], name='msg_created_idx'),
            models.Index(fields=['content'], name='msg_content_search_idx'),  # 全文搜索
        ]
    
    def __str__(self):
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"{self.get_role_display()} #{self.sequence_number}: {content_preview}"
    
    def save(self, *args, **kwargs):
        # 自動設定 sequence_number
        if not self.sequence_number:
            last_seq = ChatMessage.objects.filter(conversation=self.conversation).aggregate(
                models.Max('sequence_number')
            )['sequence_number__max'] or 0
            self.sequence_number = last_seq + 1
        
        super().save(*args, **kwargs)
        
        # 更新對話統計
        if self.conversation_id:
            self.conversation.update_stats()


class SearchThresholdSetting(models.Model):
    """
    搜尋 Threshold 設定管理
    
    管理不同 Assistant 的 threshold 設定。
    只儲存一個 master_threshold，其他 threshold 會根據固定公式計算：
    - 段落向量搜尋: master_threshold
    - 文檔向量搜尋: master_threshold * 0.85
    - 關鍵字補充搜尋: master_threshold * 0.5
    
    優先順序：
    1. Dify Studio 設定（最高優先，用戶當下設定）
    2. 資料庫設定（此 Model，管理員預設值）
    3. 程式碼預設值 0.7（最低優先，系統預設）
    """
    
    ASSISTANT_CHOICES = [
        ('protocol_assistant', 'Protocol Assistant'),
        ('rvt_assistant', 'RVT Assistant'),
    ]
    
    assistant_type = models.CharField(
        max_length=50,
        unique=True,
        choices=ASSISTANT_CHOICES,
        verbose_name="Assistant 類型",
        help_text="要設定 threshold 的 Assistant"
    )
    
    master_threshold = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.70,
        verbose_name="主 Threshold",
        help_text="段落向量搜尋使用的 threshold (0.00 ~ 1.00)。其他搜尋會自動計算：文檔=0.85倍、關鍵字=0.5倍"
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="說明",
        help_text="此設定的用途說明"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="啟用",
        help_text="是否啟用此設定"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="更新者",
        help_text="最後更新此設定的使用者"
    )
    
    class Meta:
        db_table = 'search_threshold_settings'
        verbose_name = "搜尋 Threshold 設定"
        verbose_name_plural = "搜尋 Threshold 設定"
        ordering = ['assistant_type']
    
    def __str__(self):
        return f"{self.get_assistant_type_display()} - Threshold: {self.master_threshold}"
    
    def get_calculated_thresholds(self):
        """
        計算所有 threshold 值
        
        Returns:
            dict: 包含所有計算後的 threshold
        """
        master = float(self.master_threshold)
        return {
            'master_threshold': master,
            'vector_section_threshold': master,  # 段落向量
            'vector_document_threshold': round(master * 0.85, 2),  # 文檔向量
            'keyword_threshold': round(master * 0.5, 2),  # 關鍵字
        }
    
    def save(self, *args, **kwargs):
        """儲存前驗證 threshold 範圍"""
        # 確保 threshold 在有效範圍內
        if self.master_threshold < 0:
            self.master_threshold = 0
        elif self.master_threshold > 1:
            self.master_threshold = 1
        
        super().save(*args, **kwargs)
