from django.db import models
from django.contrib.auth.models import User


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


class Employee(models.Model):
    """員工模型 - 用於 Dify 知識庫查詢演示"""
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
        verbose_name = "員工"
        verbose_name_plural = "員工"

    def __str__(self):
        return f"{self.name} - {self.position}"
    
    def get_full_info(self):
        """獲取完整的員工資訊文本"""
        info = f"姓名: {self.name}\n"
        info += f"部門: {self.department}\n"
        info += f"職位: {self.position}\n"
        info += f"Email: {self.email}\n"
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