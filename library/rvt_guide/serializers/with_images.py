"""
RVT Guide 圖片相關序列化器

使用通用的 ContentImageSerializer（來自 library.common）
提供包含圖片的 RVT Guide 序列化功能
"""

from rest_framework import serializers
# 使用通用的圖片序列化器
from library.common.serializers import ContentImageSerializer


class RVTGuideWithImagesSerializer(serializers.ModelSerializer):
    """
    包含圖片的 RVT Guide 序列化器
    
    在基本 RVT Guide 資訊基礎上，增加圖片相關欄位
    適用於需要顯示圖片的詳細視圖
    """
    images = ContentImageSerializer(many=True, read_only=True)
    active_images = serializers.SerializerMethodField()
    primary_image = serializers.SerializerMethodField()
    image_count = serializers.SerializerMethodField()
    has_images = serializers.SerializerMethodField()
    
    class Meta:
        from api.models import RVTGuide
        model = RVTGuide
        fields = [
            'id', 'title', 'content', 'created_at', 'updated_at',
            'images', 'active_images', 'primary_image', 'image_count', 'has_images'
        ]
    
    def get_active_images(self, obj):
        """獲取所有啟用的圖片"""
        images = obj.get_active_images()
        return ContentImageSerializer(images, many=True).data
    
    def get_primary_image(self, obj):
        """獲取主要圖片"""
        primary = obj.get_primary_image()
        return ContentImageSerializer(primary).data if primary else None
    
    def get_image_count(self, obj):
        """獲取圖片數量"""
        return obj.get_image_count()
    
    def get_has_images(self, obj):
        """檢查是否有圖片"""
        return obj.has_images()
