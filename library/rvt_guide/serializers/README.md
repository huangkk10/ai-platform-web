# RVT Guide Serializers 模組化說明

## 📦 目錄結構

```
library/rvt_guide/serializers/
├── __init__.py           # 統一導出介面
├── base.py              # 基礎序列化器
├── list.py              # 列表序列化器
└── with_images.py       # 圖片相關序列化器
```

## 📋 序列化器說明

### 1. RVTGuideSerializer (base.py)
**用途：** 完整的 RVT Guide 序列化器
**包含欄位：** id, title, content, created_at, updated_at
**使用場景：**
- 詳細視圖（retrieve）
- 創建操作（create）
- 更新操作（update）

### 2. RVTGuideListSerializer (list.py)
**用途：** 輕量級列表序列化器
**包含欄位：** id, title, created_at, updated_at
**使用場景：**
- 列表視圖（list）
- 需要提升性能的場景
- 不需要顯示完整內容的地方

### 3. ContentImageSerializer (來自 common)
**位置：** `library.common.serializers.image`
**用途：** 通用內容圖片序列化器（從 common 模組導入）
**特點：** 可重用於所有知識庫的圖片管理
**包含欄位：**
- 基本資訊：id, title, description, filename
- 檔案資訊：content_type_mime, file_size, width, height
- 顯示資訊：display_order, is_primary, is_active
- 計算欄位：data_url, size_display, dimensions_display

**注意：** 此序列化器現在位於 `library.common.serializers`，可供所有知識庫重用

### 4. RVTGuideWithImagesSerializer (with_images.py)
**用途：** 包含完整圖片資訊的 RVT Guide 序列化器
**包含欄位：**
- RVT Guide 基本欄位
- images：所有圖片（包括未啟用）
- active_images：啟用的圖片
- primary_image：主要圖片
- image_count：圖片數量
- has_images：是否有圖片

## 🔧 使用方式

### 方式 1：從 library 直接導入（推薦）
```python
from library.rvt_guide.serializers import (
    RVTGuideSerializer,
    RVTGuideListSerializer,
    ContentImageSerializer,
    RVTGuideWithImagesSerializer
)
```

### 方式 2：從 api.serializers 導入（向後兼容）
```python
from api.serializers import (
    RVTGuideSerializer,
    RVTGuideListSerializer,
    ContentImageSerializer,
    RVTGuideWithImagesSerializer
)
```

### 方式 3：使用輔助函數
```python
from library.rvt_guide.serializers import get_serializer_class

# 獲取基礎序列化器
BaseSerializer = get_serializer_class('base')

# 獲取列表序列化器
ListSerializer = get_serializer_class('list')

# 獲取圖片序列化器
WithImagesSerializer = get_serializer_class('with_images')
```

## 🎯 在 ViewSet 中使用

```python
from rest_framework import viewsets
from library.rvt_guide.serializers import (
    RVTGuideSerializer,
    RVTGuideListSerializer,
    RVTGuideWithImagesSerializer
)

class RVTGuideViewSet(viewsets.ModelViewSet):
    queryset = RVTGuide.objects.all()
    
    def get_serializer_class(self):
        """根據操作類型選擇序列化器"""
        if self.action == 'list':
            return RVTGuideListSerializer
        elif self.request.query_params.get('include_images'):
            return RVTGuideWithImagesSerializer
        return RVTGuideSerializer
```

## 🔄 重用於其他知識庫

這個模組化結構可以輕鬆複製到其他知識庫：

```python
# 為 Protocol Assistant 創建類似結構
library/protocol_assistant/serializers/
├── __init__.py
├── base.py              # ProtocolGuideSerializer
├── list.py              # ProtocolGuideListSerializer
└── with_images.py       # ProtocolGuideWithImagesSerializer

# 大部分程式碼可以直接複製，只需修改：
# 1. Model 引用（RVTGuide → ProtocolGuide）
# 2. 類別名稱
# 3. 特定欄位（如果有差異）
```

## ✅ 優點

1. **關注點分離**：每個序列化器有自己的文件
2. **易於維護**：清晰的模組結構，容易找到和修改
3. **可重用性**：可以輕鬆複製到其他知識庫
4. **向後兼容**：現有代碼無需修改
5. **擴展性強**：新增序列化器只需新增文件
6. **文檔清晰**：每個文件都有明確的用途說明

## 📝 添加新序列化器

如果需要添加新的序列化器（例如統計序列化器）：

1. 創建新文件：`library/rvt_guide/serializers/statistics.py`
2. 定義序列化器類
3. 在 `__init__.py` 中導入並添加到 `__all__`
4. 更新 `SERIALIZER_MAP` 字典（如果需要）

```python
# statistics.py
class RVTGuideStatisticsSerializer(serializers.ModelSerializer):
    total_guides = serializers.IntegerField()
    # ... 其他統計欄位

# __init__.py
from .statistics import RVTGuideStatisticsSerializer

__all__ = [
    # ... 現有序列化器
    'RVTGuideStatisticsSerializer',
]
```

## 🚀 遷移檢查清單

- [x] 創建 serializers/ 目錄結構
- [x] 移動 RVTGuideSerializer 到 base.py
- [x] 移動 RVTGuideListSerializer 到 list.py
- [x] 移動圖片相關序列化器到 with_images.py
- [x] 創建統一的 __init__.py
- [x] 更新 api/serializers.py 導入
- [x] 添加向後兼容性註釋
- [x] 更新 views.py 註釋
- [ ] 測試所有 API 端點
- [ ] 更新相關文檔

## 📊 影響範圍

| 文件 | 修改內容 | 狀態 |
|------|---------|------|
| `library/rvt_guide/serializers/base.py` | 新增 | ✅ |
| `library/rvt_guide/serializers/list.py` | 新增 | ✅ |
| `library/rvt_guide/serializers/with_images.py` | 新增 | ✅ |
| `library/rvt_guide/serializers/__init__.py` | 新增 | ✅ |
| `backend/api/serializers.py` | 移除定義，改為導入 | ✅ |
| `backend/api/views.py` | 添加註釋說明 | ✅ |

---

**最後更新：** 2025-10-16  
**版本：** v1.0  
**負責人：** AI Platform Team
