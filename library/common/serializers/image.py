"""
通用圖片序列化器

提供可重用的圖片管理序列化功能
適用於所有需要圖片管理的內容類型（RVT Guide, Protocol Assistant, 等）
"""

from rest_framework import serializers


class ContentImageSerializer(serializers.ModelSerializer):
    """
    通用內容圖片序列化器
    
    可重用於任何知識庫的圖片管理功能：
    - RVT Assistant
    - Protocol Assistant
    - Network Assistant
    - 其他任何需要圖片管理的內容
    
    包含完整的圖片資訊和輔助顯示欄位
    """
    data_url = serializers.SerializerMethodField()
    size_display = serializers.SerializerMethodField()
    dimensions_display = serializers.SerializerMethodField()
    
    class Meta:
        from api.models import ContentImage
        model = ContentImage
        fields = [
            'id', 'title', 'description', 'filename', 'content_type_mime',
            'file_size', 'width', 'height', 'display_order', 'is_primary',
            'is_active', 'created_at', 'updated_at', 'data_url', 
            'size_display', 'dimensions_display'
        ]
        read_only_fields = [
            'id', 'filename', 'content_type_mime', 'file_size', 'width', 
            'height', 'created_at', 'updated_at', 'data_url',
            'size_display', 'dimensions_display'
        ]
    
    def get_data_url(self, obj):
        """獲取圖片的 data URL"""
        return obj.get_data_url()
    
    def get_size_display(self, obj):
        """獲取格式化的檔案大小顯示"""
        return obj.get_size_display()
    
    def get_dimensions_display(self, obj):
        """獲取格式化的尺寸顯示"""
        return obj.get_dimensions_display()
