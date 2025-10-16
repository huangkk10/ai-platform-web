"""
RVT Guide 列表序列化器

提供輕量級的序列化功能，只包含列表視圖所需的必要欄位
優化列表查詢性能
"""

from rest_framework import serializers


class RVTGuideListSerializer(serializers.ModelSerializer):
    """
    RVT Guide 列表序列化器
    
    用於列表視圖（list），只包含必要欄位以提升性能
    不包含大型欄位（如 content）
    """
    
    class Meta:
        # 延遲導入避免循環依賴
        from api.models import RVTGuide
        model = RVTGuide
        fields = [
            'id', 'title',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at'
        ]
