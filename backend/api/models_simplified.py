# 簡化版 OCR 存儲基準測試模型
from django.db import models
from django.contrib.auth.models import User

class OCRStorageBenchmarkSimple(models.Model):
    """AI OCR 存儲基準測試資料模型 - 簡化版"""
    
    # === 核心測試資料 (對應附件內容) ===
    benchmark_score = models.IntegerField(verbose_name="測試得分", help_text="例如: 6883")
    average_bandwidth = models.CharField(max_length=50, verbose_name="平均帶寬", help_text="例如: 1174.89 MB/s")
    device_model = models.CharField(max_length=200, verbose_name="裝置型號", help_text="例如: KINGSTON SFYR2S1TO")
    firmware_version = models.CharField(max_length=100, verbose_name="韌體版本", help_text="例如: SGW0904A")
    test_datetime = models.DateTimeField(verbose_name="測試時間", help_text="例如: 2025-09-06 16:13")
    benchmark_version = models.CharField(max_length=50, verbose_name="3DMark版本", help_text="例如: 2.28.8228 (測試專用版)")
    
    # === OCR 相關欄位 ===
    # 原始圖像存儲
    original_image_data = models.BinaryField(blank=True, null=True, verbose_name="原始圖像", help_text="OCR 來源圖像")
    original_image_filename = models.CharField(max_length=255, blank=True, verbose_name="圖像檔名")
    
    # OCR 提取的原始文本
    ocr_raw_text = models.TextField(blank=True, verbose_name="OCR文本", help_text="OCR 識別出的原始文本")
    
    # AI 處理後的結構化資料
    ai_structured_data = models.JSONField(blank=True, null=True, verbose_name="結構化資料", help_text="AI 處理後的 JSON 資料")
    
    # === 基本管理欄位 ===
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="上傳者")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")
    
    class Meta:
        ordering = ['-test_datetime', '-created_at']
        verbose_name = "OCR 存儲測試"
        verbose_name_plural = "OCR 存儲測試"
        db_table = 'ocr_storage_simple'
    
    def __str__(self):
        return f"[{self.device_model}] {self.benchmark_score}分 ({self.test_datetime.strftime('%Y-%m-%d')})"
    
    def get_summary(self):
        """獲取摘要"""
        return f"裝置: {self.device_model} | 分數: {self.benchmark_score} | 帶寬: {self.average_bandwidth}"