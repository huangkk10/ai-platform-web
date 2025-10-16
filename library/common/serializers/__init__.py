"""
通用序列化器模組

提供可重用的序列化器組件，適用於所有知識庫系統

包含：
- ContentImageSerializer: 通用圖片序列化器
- 未來可擴展更多通用序列化器（例如：BaseKnowledgeSerializer）

使用範例：
    from library.common.serializers import ContentImageSerializer
    
    # 在 RVT Guide 中使用
    from library.common.serializers import ContentImageSerializer
    
    class RVTGuideWithImagesSerializer(serializers.ModelSerializer):
        images = ContentImageSerializer(many=True, read_only=True)
        ...
    
    # 在 Protocol Assistant 中使用（完全相同）
    from library.common.serializers import ContentImageSerializer
    
    class ProtocolGuideWithImagesSerializer(serializers.ModelSerializer):
        images = ContentImageSerializer(many=True, read_only=True)
        ...
"""

# 通用圖片序列化器
from .image import ContentImageSerializer


# 統一導出
__all__ = [
    'ContentImageSerializer',
]


# 未來可擴展的序列化器映射
COMMON_SERIALIZER_MAP = {
    'image': ContentImageSerializer,
    # 'base_knowledge': BaseKnowledgeSerializer,  # 未來可添加
    # 'base_list': BaseKnowledgeListSerializer,   # 未來可添加
}


def get_common_serializer(serializer_type='image'):
    """
    獲取通用序列化器類
    
    Args:
        serializer_type: 序列化器類型
            - 'image': 圖片序列化器（預設）
    
    Returns:
        對應的序列化器類
    
    Raises:
        ValueError: 如果提供的類型不存在
    """
    if serializer_type not in COMMON_SERIALIZER_MAP:
        raise ValueError(
            f"Unknown serializer type: {serializer_type}. "
            f"Valid types: {', '.join(COMMON_SERIALIZER_MAP.keys())}"
        )
    return COMMON_SERIALIZER_MAP[serializer_type]
