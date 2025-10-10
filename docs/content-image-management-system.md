# 通用內容圖片管理系統

## 🎯 概述

這是一個為 AI Platform 設計的通用圖片管理系統，支援多種內容類型（RVT Guide、Know Issue 等）的圖片存儲和管理。系統採用獨立資料表設計，具有良好的擴展性和靈活性。

## 🏗️ 系統架構

### 資料庫設計

#### ContentImage 模型
```python
# backend/api/models.py
class ContentImage(models.Model):
    # 通用內容關聯（支援多種模型）
    content_type = models.ForeignKey('contenttypes.ContentType', ...)
    object_id = models.PositiveIntegerField(...)
    content_object = models.GenericForeignKey('content_type', 'object_id')
    
    # 向後兼容的直接關聯
    rvt_guide = models.ForeignKey(RVTGuide, ...)
    
    # 圖片基本資訊
    title = models.CharField(...)
    description = models.TextField(...)
    filename = models.CharField(...)
    content_type_mime = models.CharField(...)
    file_size = models.IntegerField(...)
    
    # 圖片資料
    image_data = models.BinaryField(...)
    width = models.IntegerField(...)
    height = models.IntegerField(...)
    
    # 狀態和排序
    display_order = models.IntegerField(...)
    is_primary = models.BooleanField(...)
    is_active = models.BooleanField(...)
```

### 前端組件

#### ContentImageManager 組件
- **位置**: `frontend/src/components/ContentImageManager.js`
- **樣式**: `frontend/src/components/ContentImageManager.css`
- **功能**: 圖片上傳、編輯、排序、刪除等完整管理功能

## 🚀 使用方法

### 1. 基本使用

```javascript
import ContentImageManager from '../components/ContentImageManager';

const MyPage = () => {
  const [images, setImages] = useState([]);
  
  return (
    <ContentImageManager
      contentType="rvt-guide"     // 內容類型
      contentId={123}             // 內容 ID
      images={images}             // 圖片列表
      onImagesChange={setImages}  // 圖片變更回調
      maxImages={10}              // 最大圖片數量
      maxSizeMB={2}              // 單檔最大大小
      title="相關圖片"            // 組件標題
      readonly={false}           // 是否唯讀
    />
  );
};
```

### 2. 不同內容類型的使用

```javascript
// RVT Guide
<ContentImageManager
  contentType="rvt-guide"
  contentId={guideId}
  images={images}
  onImagesChange={setImages}
/>

// Know Issue
<ContentImageManager
  contentType="know-issue"
  contentId={issueId}
  images={images}
  onImagesChange={setImages}
  maxImages={5}
  title="相關截圖"
/>

// 唯讀模式（用於檢視頁面）
<ContentImageManager
  contentType="rvt-guide"
  contentId={guideId}
  images={images}
  onImagesChange={() => {}}
  readonly={true}
/>
```

## 🎨 功能特性

### 圖片管理功能
- ✅ **圖片上傳**: 支援單張和批量上傳
- ✅ **拖拽排序**: 直觀的拖拽介面調整順序
- ✅ **主要圖片**: 設定主要圖片用於縮圖顯示
- ✅ **圖片編輯**: 修改圖片標題和描述
- ✅ **圖片預覽**: 內建圖片預覽功能
- ✅ **圖片刪除**: 安全的刪除確認機制

### 檔案驗證
- ✅ **格式限制**: 支援 JPEG、PNG、GIF
- ✅ **大小限制**: 可配置的檔案大小限制
- ✅ **數量限制**: 可配置的圖片數量限制
- ✅ **內容驗證**: MIME 類型驗證

### 使用者體驗
- ✅ **響應式設計**: 適應不同螢幕尺寸
- ✅ **載入狀態**: 明確的載入和錯誤提示
- ✅ **批量操作**: 支援批量上傳和操作
- ✅ **唯讀模式**: 支援只檢視不編輯的模式

## 📋 API 端點

### 圖片管理 API
```
GET    /api/content-images/              # 獲取圖片列表
POST   /api/content-images/              # 上傳新圖片
GET    /api/content-images/{id}/         # 獲取單張圖片
PATCH  /api/content-images/{id}/         # 更新圖片資訊
DELETE /api/content-images/{id}/         # 刪除圖片
POST   /api/content-images/batch-upload/ # 批量上傳
```

### RVT Guide 專用 API
```
POST /api/rvt-guides/{id}/set_primary_image/  # 設定主要圖片
POST /api/rvt-guides/{id}/reorder_images/     # 重新排序圖片
GET  /api/rvt-guides/{id}/images/             # 獲取指南圖片
```

## 🔧 資料庫遷移

執行以下命令來建立必要的資料表：

```bash
# 進入 Django 容器
docker exec -it ai-django bash

# 執行遷移
python manage.py migrate
```

遷移檔案位置：`backend/api/migrations/0031_add_content_image.py`

## 📊 資料表結構

### 主要索引
```sql
-- 內容類型和對象 ID 索引
CREATE INDEX content_image_ct_obj_order_idx ON content_images(content_type_id, object_id, display_order);
CREATE INDEX content_image_ct_obj_active_idx ON content_images(content_type_id, object_id, is_active);

-- RVT Guide 專用索引（向後兼容）
CREATE INDEX content_image_rvt_order_idx ON content_images(rvt_guide_id, display_order);
CREATE INDEX content_image_rvt_active_idx ON content_images(rvt_guide_id, is_active);

-- 主要圖片索引
CREATE INDEX content_image_primary_idx ON content_images(is_primary);
```

## 🤖 AI 整合支援

### 向量搜尋整合
系統已整合到 RVT Guide 的向量搜尋中，圖片資訊會被包含在向量化的內容中：

```python
# library/rvt_guide/vector_service.py
def _format_content_for_embedding(self, instance):
    content_parts = []
    # ... 其他內容 ...
    
    # 圖片摘要資訊
    if hasattr(instance, 'get_images_summary'):
        images_summary = instance.get_images_summary()
        if images_summary:
            content_parts.append(images_summary)
    
    return "\n".join(content_parts)
```

### 聊天回應中的圖片顯示
AI 聊天系統會自動檢測包含圖片的知識庫內容，並在回應中顯示相關圖片。

## 🛠️ 開發指南

### 擴展到新的內容類型

1. **確保模型相容性**:
   ```python
   # 在你的模型中添加便利方法
   class YourModel(models.Model):
       def get_active_images(self):
           return ContentImage.objects.filter(
               content_type=ContentType.objects.get_for_model(self),
               object_id=self.pk,
               is_active=True
           ).order_by('display_order')
   ```

2. **使用組件**:
   ```javascript
   <ContentImageManager
     contentType="your-content-type"
     contentId={yourId}
     images={images}
     onImagesChange={setImages}
   />
   ```

3. **添加 API 支援**: 確保後端 API 支援新的內容類型。

### 自定義樣式
可以通過覆寫 CSS 類名來自定義組件樣式：

```css
.content-image-manager .custom-style {
  /* 你的自定義樣式 */
}
```

## 🔒 安全考量

- **檔案驗證**: 嚴格的 MIME 類型和檔案大小驗證
- **權限控制**: 基於用戶權限的圖片管理
- **資料清理**: 前端使用 DOMPurify 清理不安全內容
- **CSRF 保護**: API 請求包含 CSRF 保護

## 📈 效能優化

- **按需載入**: 圖片資料僅在需要時載入
- **資料庫索引**: 針對常用查詢進行索引優化
- **分頁支援**: 大量圖片時的分頁載入
- **快取策略**: 合理的快取機制減少重複請求

## 🐛 故障排除

### 常見問題

1. **圖片上傳失敗**
   - 檢查檔案格式和大小限制
   - 確認後端 API 端點正常
   - 檢查網路連接和權限

2. **圖片無法顯示**
   - 確認 data URL 生成正確
   - 檢查瀏覽器控制台錯誤
   - 驗證圖片資料完整性

3. **拖拽排序不工作**
   - 確認不是在唯讀模式
   - 檢查 JavaScript 錯誤
   - 驗證 API 端點回應

### 除錯技巧

```javascript
// 啟用組件除錯
const ContentImageManager = ({ debug = false, ...props }) => {
  if (debug) {
    console.log('ContentImageManager props:', props);
  }
  // ...
};
```

## 📝 更新記錄

### v1.0.0 (2024-10-10)
- ✅ 建立通用 ContentImage 模型
- ✅ 實現 ContentImageManager 組件
- ✅ 整合 RVT Guide 圖片管理
- ✅ 支援拖拽排序和批量操作
- ✅ 完整的 API 和資料庫支援

## 🤝 貢獻指南

歡迎貢獻改進建議！請遵循以下步驟：

1. Fork 專案
2. 建立功能分支
3. 提交變更
4. 發起 Pull Request

## 📄 許可證

此專案屬於 AI Platform 內部系統，請遵循公司相關政策。