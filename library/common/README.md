# Library Common 模組說明

## 📦 概述

`library/common/` 模組包含可在所有知識庫系統中重用的通用組件。

## 🎯 設計理念

- **DRY 原則**：避免重複程式碼
- **高可重用性**：組件設計為適用於多個知識庫
- **清晰的職責分離**：通用 vs 專用組件明確區分
- **易於擴展**：便於添加新的通用組件

## 📁 目錄結構

```
library/common/
├── __init__.py
└── serializers/
    ├── __init__.py          # 統一導出介面
    └── image.py             # ContentImageSerializer
```

## 🔧 包含的組件

### 1. ContentImageSerializer

**用途：** 通用內容圖片序列化器

**適用範圍：**
- RVT Assistant 知識庫
- Protocol Assistant 知識庫
- Network Assistant 知識庫
- 任何需要圖片管理的內容類型

**特性：**
- 完整的圖片資訊序列化
- 輔助顯示欄位（data_url, size_display, dimensions_display）
- 完全可重用，無需修改

## 📖 使用指南

### 基本使用

```python
# 方式 1：直接從 common 導入（推薦）
from library.common.serializers import ContentImageSerializer

# 方式 2：從特定知識庫導入（向後兼容）
from library.rvt_guide.serializers import ContentImageSerializer

# 方式 3：從 api.serializers 導入（向後兼容）
from api.serializers import ContentImageSerializer
```

### 在 RVT Guide 中使用

```python
from library.common.serializers import ContentImageSerializer
from rest_framework import serializers

class RVTGuideWithImagesSerializer(serializers.ModelSerializer):
    images = ContentImageSerializer(many=True, read_only=True)
    active_images = serializers.SerializerMethodField()
    
    def get_active_images(self, obj):
        images = obj.get_active_images()
        return ContentImageSerializer(images, many=True).data
```

### 在 Protocol Assistant 中使用

```python
# 完全相同的使用方式！
from library.common.serializers import ContentImageSerializer
from rest_framework import serializers

class ProtocolGuideWithImagesSerializer(serializers.ModelSerializer):
    images = ContentImageSerializer(many=True, read_only=True)
    active_images = serializers.SerializerMethodField()
    
    def get_active_images(self, obj):
        images = obj.get_active_images()
        return ContentImageSerializer(images, many=True).data
```

## 🚀 創建新知識庫時

### 步驟 1：建立知識庫目錄結構

```bash
library/protocol_assistant/
├── __init__.py
└── serializers/
    ├── __init__.py
    ├── base.py              # ProtocolGuideSerializer
    ├── list.py              # ProtocolGuideListSerializer
    └── with_images.py       # ProtocolGuideWithImagesSerializer
```

### 步驟 2：重用 ContentImageSerializer

```python
# library/protocol_assistant/serializers/with_images.py
from library.common.serializers import ContentImageSerializer  # 重用！

class ProtocolGuideWithImagesSerializer(serializers.ModelSerializer):
    images = ContentImageSerializer(many=True, read_only=True)
    # ... 其他欄位
```

### 步驟 3：導出序列化器

```python
# library/protocol_assistant/serializers/__init__.py
from library.common.serializers import ContentImageSerializer  # 導入並 re-export

from .base import ProtocolGuideSerializer
from .list import ProtocolGuideListSerializer
from .with_images import ProtocolGuideWithImagesSerializer

__all__ = [
    'ContentImageSerializer',      # 通用組件
    'ProtocolGuideSerializer',
    'ProtocolGuideListSerializer',
    'ProtocolGuideWithImagesSerializer',
]
```

## 🎁 優勢

### 1. 避免程式碼重複
```python
# ❌ 不好的做法（重複定義）
library/rvt_guide/serializers/image.py       # ContentImageSerializer
library/protocol_assistant/serializers/image.py  # ContentImageSerializer (重複!)

# ✅ 好的做法（重用）
library/common/serializers/image.py          # ContentImageSerializer
library/rvt_guide/serializers/               # 從 common 導入
library/protocol_assistant/serializers/      # 從 common 導入
```

### 2. 統一的介面
所有知識庫使用相同的圖片序列化器，確保：
- 一致的 API 響應格式
- 相同的欄位和行為
- 統一的維護點（只需修改一處）

### 3. 易於維護
```python
# 需要修改圖片序列化邏輯？
# 只需修改一個文件：
library/common/serializers/image.py

# 所有知識庫自動受益！
```

## 📊 向後兼容性

### 完全兼容
所有現有的導入方式仍然有效：

```python
# ✅ 舊代碼仍然可用
from library.rvt_guide.serializers import ContentImageSerializer

# ✅ 新代碼推薦使用
from library.common.serializers import ContentImageSerializer

# ✅ API 層也可用
from api.serializers import ContentImageSerializer
```

### 導入路徑追蹤
```
api.serializers.ContentImageSerializer
    ↓ (re-export)
library.rvt_guide.serializers.ContentImageSerializer
    ↓ (re-export)
library.common.serializers.ContentImageSerializer
    ↓ (實際定義)
library.common.serializers.image.ContentImageSerializer
```

## 🔮 未來擴展

### 可能添加的通用組件

```python
library/common/
├── serializers/
│   ├── image.py              # ✅ 已實現
│   ├── base_knowledge.py     # 📋 未來：通用知識庫基礎序列化器
│   └── base_list.py          # 📋 未來：通用列表序列化器
├── viewsets/
│   └── base_knowledge.py     # 📋 未來：通用知識庫 ViewSet
└── models/
    └── mixins.py             # 📋 未來：通用 Model Mixins
```

### 建立通用基類範例

```python
# 未來可能的 base_knowledge.py
class BaseKnowledgeSerializer(serializers.ModelSerializer):
    """所有知識庫序列化器的基類"""
    
    class Meta:
        abstract = True
        fields = ['id', 'title', 'content', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

# RVT Guide 繼承
class RVTGuideSerializer(BaseKnowledgeSerializer):
    class Meta(BaseKnowledgeSerializer.Meta):
        model = RVTGuide
        # 自動繼承 fields 和 read_only_fields

# Protocol Assistant 繼承
class ProtocolGuideSerializer(BaseKnowledgeSerializer):
    class Meta(BaseKnowledgeSerializer.Meta):
        model = ProtocolGuide
        # 自動繼承 fields 和 read_only_fields
```

## ✅ 檢查清單

創建新知識庫時，確保：

- [ ] 從 `library.common.serializers` 導入 `ContentImageSerializer`
- [ ] 在知識庫的 `__init__.py` 中 re-export `ContentImageSerializer`
- [ ] 不要重新定義 `ContentImageSerializer`
- [ ] 保持與 common 組件的一致性
- [ ] 添加適當的文檔說明

## 📝 相關文檔

- [RVT Guide Serializers 說明](../rvt_guide/serializers/README.md)
- [序列化器模組化報告](../../docs/rvt-guide-serializers-modularization-report.md)

---

**最後更新：** 2025-10-16  
**版本：** v1.0  
**狀態：** ✅ 已實施並測試  
**負責人：** AI Platform Team
