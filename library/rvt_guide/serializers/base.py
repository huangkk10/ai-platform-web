"""
RVT Guide 基礎序列化器

提供 RVT Guide 的完整序列化功能
包含所有欄位，用於詳細視圖和創建/更新操作
"""

from rest_framework import serializers


class RVTGuideSerializer(serializers.ModelSerializer):
    """
    RVT Guide 完整序列化器
    
    用於：
    - 詳細視圖（retrieve）
    - 創建操作（create）
    - 更新操作（update）
    
    包含所有基本欄位
    """
    
    class Meta:
        # 延遲導入避免循環依賴
        from api.models import RVTGuide
        model = RVTGuide
        fields = [
            'id', 'title',
            'content',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at'
        ]
