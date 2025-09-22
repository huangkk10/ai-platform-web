from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class UserProfile(models.Model):
    """使用者個人檔案擴展"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


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
        ('rvt_log_analyze_chat', 'RVT Assistant'),
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
    test_datetime = models.DateTimeField(verbose_name="測試時間", help_text="進行測試的具體時間")
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
        ordering = ['-test_datetime', '-created_at']
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
        return f"{class_info}[{self.project_name}] {self.device_model} - {self.benchmark_score}分 ({self.test_datetime.strftime('%Y-%m-%d')})"
    
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
    
    MAIN_CATEGORY_CHOICES = [
        ('system_architecture', '系統架構'),
        ('environment_setup', '環境準備'),
        ('configuration_management', '配置管理'),
        ('test_case_management', '測項管理'),
        ('operation_flow', '操作流程'),
        ('troubleshooting', '故障排除'),
        ('contact_support', '聯絡支援'),
    ]
    
    SUB_CATEGORY_CHOICES = [
        # 系統架構子分類
        ('jenkins_ansible_concept', 'Jenkins和Ansible概念'),
        ('system_workflow', '系統工作流程'),
        
        # 環境準備子分類
        ('network_requirements', '網路需求'),
        ('hardware_requirements', '硬體設備'),
        ('system_installation', '系統軟體安裝'),
        ('bios_settings', 'BIOS設定'),
        
        # 配置管理子分類
        ('nas_directory', 'NAS目錄結構'),
        ('machine_configuration', '機器設定格式'),
        ('group_variables', '群組變數設定'),
        ('required_parameters', '必要參數列表'),
        
        # 測項管理子分類
        ('test_parameters', '測項參數說明'),
        ('test_modes', '測試模式'),
        ('test_examples', '測試範例'),
        
        # 操作流程子分類
        ('jenkins_stages', 'Jenkins階段'),
        ('jenkins_operations', 'Jenkins操作'),
        ('uart_control', 'UART控制'),
        ('mdt_operations', 'MDT相關操作'),
        ('ansible_parameters', 'Ansible參數'),
        
        # 故障排除子分類
        ('jenkins_failures', 'Jenkins失敗'),
        ('ansible_errors', 'Ansible錯誤'),
        ('mdt_failures', 'MDT部署失敗'),
        ('script_failures', '腳本執行失敗'),
        ('log_analysis', '日誌分析'),
        
        # 聯絡支援子分類
        ('team_contacts', '團隊聯絡'),
        ('support_procedures', '支援流程'),
    ]
    
    # 基本識別欄位
    title = models.CharField(max_length=300, verbose_name="文檔標題", help_text="文檔的顯示標題")
    version = models.CharField(max_length=50, default="1.0", verbose_name="版本號", help_text="文檔版本")
    
    # 分類欄位
    main_category = models.CharField(
        max_length=50, 
        choices=MAIN_CATEGORY_CHOICES, 
        verbose_name="主分類",
        help_text="文檔所屬的主要分類"
    )
    sub_category = models.CharField(
        max_length=50, 
        choices=SUB_CATEGORY_CHOICES, 
        verbose_name="子分類",
        help_text="文檔所屬的子分類"
    )
    
    # 內容欄位
    content = models.TextField(verbose_name="文檔內容", help_text="文檔的主要內容")
    
    # 使用情境欄位
    question_type = models.CharField(
        max_length=50,
        choices=[
            ('operation_guide', '操作指南'),
            ('parameter_explanation', '參數說明'),
            ('troubleshooting', '故障排除'),
            ('concept_explanation', '概念說明'),
        ],
        default='operation_guide',
        verbose_name="問題類型",
        help_text="這個文檔主要回答什麼類型的問題"
    )
    
    target_user = models.CharField(
        max_length=50,
        choices=[
            ('beginner', '初學者'),
            ('advanced', '進階使用者'),
            ('admin', '系統管理員'),
            ('all', '所有用戶'),
        ],
        default='all',
        verbose_name="目標使用者",
        help_text="這個文檔的目標使用者群體"
    )
    
    # 狀態管理
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', '草稿'),
            ('published', '已發布'),
            ('archived', '已歸檔'),
        ],
        default='published',
        verbose_name="狀態"
    )
    
    # 時間戳記
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")
    
    class Meta:
        ordering = ['main_category', 'sub_category', 'title']
        verbose_name = "RVT使用指南"
        verbose_name_plural = "RVT使用指南"
        db_table = 'rvt_guide'
        indexes = [
            models.Index(fields=['main_category', 'sub_category']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"[{self.get_main_category_display()}] {self.title}"
    
    def get_full_category_name(self):
        """獲取完整的分類名稱"""
        main_name = self.get_main_category_display()
        sub_name = self.get_sub_category_display()
        return f"{main_name} > {sub_name}"
    
    def get_search_content(self):
        """獲取用於搜索的完整內容"""
        search_text = f"{self.title} {self.content}"
        return search_text
