"""
RVT Guide 序列化器模組

統一管理所有 RVT Guide 相關的序列化器
提供清晰的導入介面，保持向後兼容性

使用範例：
    from library.rvt_guide.serializers import (
        RVTGuideSerializer,
        RVTGuideListSerializer,
        RVTGuideWithImagesSerializer,
        ContentImageSerializer
    )
"""

# 基礎序列化器
from .base import RVTGuideSerializer

# 列表序列化器
from .list import RVTGuideListSerializer

# 通用圖片序列化器（從 common 導入並 re-export，保持向後兼容）
from library.common.serializers import ContentImageSerializer

# 圖片相關序列化器
from .with_images import RVTGuideWithImagesSerializer


# 統一導出所有序列化器
__all__ = [
    # 基礎序列化器
    'RVTGuideSerializer',
    
    # 列表序列化器
    'RVTGuideListSerializer',
    
    # 圖片相關序列化器
    'ContentImageSerializer',
    'RVTGuideWithImagesSerializer',
]


# 為了方便，也提供一個字典映射
SERIALIZER_MAP = {
    'base': RVTGuideSerializer,
    'list': RVTGuideListSerializer,
    'with_images': RVTGuideWithImagesSerializer,
    'images': ContentImageSerializer,
}


def get_serializer_class(serializer_type='base'):
    """
    根據類型獲取序列化器類
    
    Args:
        serializer_type: 序列化器類型
            - 'base': 基礎序列化器（預設）
            - 'list': 列表序列化器
            - 'with_images': 包含圖片的序列化器
            - 'images': 圖片序列化器
    
    Returns:
        對應的序列化器類
    
    Raises:
        ValueError: 如果提供的類型不存在
    """
    if serializer_type not in SERIALIZER_MAP:
        raise ValueError(
            f"Unknown serializer type: {serializer_type}. "
            f"Valid types: {', '.join(SERIALIZER_MAP.keys())}"
        )
    return SERIALIZER_MAP[serializer_type]
