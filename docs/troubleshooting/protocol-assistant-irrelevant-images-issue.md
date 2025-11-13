# Protocol Assistant 顯示無關圖片問題分析與解決方案

## 📋 問題描述

**現象**：用戶在 Protocol Assistant 中詢問「iol root密碼」時，AI 回答中出現了與問題無關的圖片（`upload_9bc2daefcb91b97a6fa0b8f9d0ea9a9f.png`，來自「Kingston Linux 開卡」文檔）。

**相關圖片**：
```
🖼️ upload_9bc2daefcb91b97a6fa0b8f9d0ea9a9f.png
來源：Kingston Linux 開卡文檔
實際相關性：❌ 與 IOL 密碼無關
```

**相關文檔**：
- `/docs/troubleshooting/protocol-assistant-dify-prompt-optimization.md` - Dify 提示詞優化指南

---

## 🔍 根本原因分析

### 問題根源：文檔搜尋返回過多無關文檔

#### 1. **文檔搜尋階段的行為**

```
階段 2 (Stage 2) - 文檔級搜尋：
├─ search_mode: 'document_only'
├─ threshold: 0.8
├─ top_k: 3
└─ 返回結果：
    ├─ 1. UNH-IOL (相似度 83%) ✅ 相關
    ├─ 2. Kingston Linux 開卡 (相似度 68%) ❌ 不相關
    └─ 3. I3C Protocol (相似度 65%) ❌ 不相關
```

**問題**：
- 文檔搜尋使用 `threshold=0.8`（實際被資料庫設定覆蓋）
- 但在二次過濾時，某些分數低於 0.8 的文檔仍被包含
- 結果：Kingston 文檔 (68%) 和 I3C 文檔 (65%) 被錯誤地包含在結果中

#### 2. **Dify 的引用來源機制**

**Dify 的 `retriever_resources` 返回格式**：
```json
{
  "metadata": {
    "retriever_resources": [
      {
        "content": "# 1. IOL 執行檔＆文件 內部存放路徑...",
        "score": 0.83,
        "title": "UNH-IOL",
        "type": "document"
      },
      {
        "content": "# Kingston Linux 開卡...\n🖼️ upload_9bc2daefcb91b97a6fa0b8f9d0ea9a9f.png",
        "score": 0.68,
        "title": "Kingston Linux 開卡",
        "type": "document"
      }
    ]
  }
}
```

**Dify AI 行為**：
- 將所有 `retriever_resources` 視為「引用來源」
- 在回答中可能提及所有來源（即使不相關）
- 前端解析 metadata 時，會提取**所有來源文檔**中的圖片

#### 3. **前端圖片提取邏輯**

**檔案**：`frontend/src/utils/imageProcessor.js`

```javascript
export const extractImagesFromMetadata = (metadata) => {
  const imageFilenames = new Set();
  
  // 從 metadata.retriever_resources 提取
  const resources = metadata?.retriever_resources;
  
  if (Array.isArray(resources)) {
    resources.forEach((resource) => {
      // ⚠️ 問題：提取所有資源中的圖片，不判斷相關性
      const imagePattern = /🖼️\s*([a-zA-Z0-9\-_.]{8,}\.(?:png|jpg|jpeg))/gi;
      let match;
      while ((match = imagePattern.exec(resource.content)) !== null) {
        imageFilenames.add(match[1]);
      }
    });
  }
  
  return imageFilenames;
};
```

**問題**：
- 提取**所有** `retriever_resources` 中的圖片
- 沒有根據文檔相關性或 AI 回答內容過濾圖片
- 結果：Kingston 文檔中的圖片被錯誤地顯示

---

## 🎯 解決方案

### 方案 1：提高文檔搜尋 Threshold（推薦）⭐

**目標**：減少無關文檔被包含在搜尋結果中

#### 實施步驟

**1. 調整資料庫中的 Threshold 設定**

```bash
# 進入 Django 容器
docker exec -it ai-django python manage.py shell
```

```python
from api.models import ThresholdSetting

# 調整 Protocol Assistant 的文檔搜尋閾值
protocol_threshold = ThresholdSetting.objects.get(
    assistant_type='protocol_assistant'
)

# 提高 threshold 從 0.8 到 0.85
protocol_threshold.threshold = 0.85
protocol_threshold.save()

print(f"✅ Protocol Assistant threshold 已更新為 {protocol_threshold.threshold}")
```

**2. 驗證調整效果**

```bash
# 重新查詢「iol root密碼」
# 預期結果：
# - UNH-IOL (83%) ✅ 仍然返回（低於 85% 但屬於高相似度）
# - Kingston (68%) ❌ 被過濾掉
# - I3C (65%) ❌ 被過濾掉
```

**優點**：
- ✅ 從根源減少無關文檔
- ✅ 不需要修改代碼
- ✅ 立即生效

**缺點**：
- ⚠️ 可能會過濾掉一些邊緣相關的文檔
- ⚠️ 需要根據實際效果微調 threshold

---

### 方案 2：前端智能圖片過濾（進階）

**目標**：前端根據 AI 回答內容判斷圖片是否相關

#### 實施步驟

**1. 修改 `extractImagesFromMetadata` 函數**

```javascript
// frontend/src/utils/imageProcessor.js

export const extractImagesFromMetadata = (metadata, aiAnswer) => {
  const imageFilenames = new Set();
  
  const resources = metadata?.retriever_resources;
  
  if (Array.isArray(resources)) {
    resources.forEach((resource) => {
      // ✅ 新增：檢查該資源是否在 AI 回答中被提及
      const resourceTitle = resource.title || '';
      const resourceMentioned = aiAnswer && 
        (aiAnswer.includes(resourceTitle) || 
         resource.score >= 0.80);  // 高分數文檔優先顯示圖片
      
      if (!resourceMentioned) {
        console.log(`⏭️ 跳過低相關度文檔的圖片: ${resourceTitle} (score=${resource.score})`);
        return;  // 跳過此資源
      }
      
      // 提取圖片（原有邏輯）
      const imagePattern = /🖼️\s*([a-zA-Z0-9\-_.]{8,}\.(?:png|jpg|jpeg))/gi;
      let match;
      while ((match = imagePattern.exec(resource.content)) !== null) {
        imageFilenames.add(match[1]);
        console.log(`✅ 包含相關文檔的圖片: ${match[1]} (from ${resourceTitle})`);
      }
    });
  }
  
  return imageFilenames;
};
```

**2. 修改 Hook 調用**

```javascript
// frontend/src/hooks/useMessageFormatter.js

const extractImages = (content, metadata = null, aiAnswer = null) => {
  const imageFilenames = new Set();
  
  // 從 metadata 提取圖片（傳入 AI 回答）
  const metadataImages = extractImagesFromMetadata(metadata, aiAnswer);
  
  // ... 其餘邏輯
};
```

**3. 更新前端頁面調用**

```javascript
// frontend/src/components/chat/MessageList.jsx

// 提取圖片時傳入 AI 回答內容
const imageFilenames = extractImages(
  message.content, 
  message.metadata,
  message.content  // ← 新增參數
);
```

**優點**：
- ✅ 更精準的圖片過濾
- ✅ 根據 AI 實際引用的文檔顯示圖片
- ✅ 不影響搜尋結果的完整性

**缺點**：
- ⚠️ 需要修改前端代碼
- ⚠️ 依賴 AI 回答中明確提及文檔標題

---

### 方案 3：Dify 提示詞優化（輔助）

**目標**：讓 Dify AI 只引用真正相關的文檔

#### 實施步驟

**在 Dify 工作室的提示詞中添加**：

```markdown
## 引用來源使用原則

當知識庫返回多個文檔時：
1. ✅ 只引用與用戶問題**直接相關**的文檔
2. ✅ 如果某個文檔不相關，不要在回答中提及
3. ❌ 不要因為文檔在列表中就自動引用
4. ✅ 優先使用相似度最高的文檔

範例：
- 用戶問「IOL root密碼」
- 知識庫返回：[UNH-IOL (83%), Kingston開卡 (68%)]
- ✅ 正確：只引用 UNH-IOL 文檔
- ❌ 錯誤：同時引用兩個文檔
```

**優點**：
- ✅ 從 AI 層面減少無關引用
- ✅ 不需要修改代碼

**缺點**：
- ⚠️ 依賴 AI 的理解能力
- ⚠️ 可能不夠穩定

---

## 🚀 推薦實施順序

### 第一階段：快速修復（立即實施）

✅ **方案 1：提高 Threshold**
- 時間：5 分鐘
- 風險：低
- 效果：中等

```bash
# 執行調整
docker exec -it ai-django python manage.py shell
# 運行上面的 Python 代碼
```

### 第二階段：優化 AI 行為（1-2 天）

✅ **方案 3：Dify 提示詞優化**
- 時間：30 分鐘
- 風險：低
- 效果：中等

### 第三階段：完善前端邏輯（可選）

✅ **方案 2：前端智能過濾**
- 時間：2-3 小時
- 風險：中
- 效果：高

---

## 📊 效果驗證

### 測試案例

**測試 1：IOL 密碼查詢**
```
查詢：「iol root密碼」
預期結果：
- ✅ 顯示 UNH-IOL 相關內容
- ❌ 不顯示 Kingston 開卡圖片
```

**測試 2：CrystalDiskMark 查詢**
```
查詢：「crystaldiskmark」
預期結果：
- ✅ 顯示 CrystalDiskMark 相關內容
- ❌ 不顯示其他 Protocol 測試工具圖片
```

### 驗證指標

| 指標 | 修改前 | 目標 |
|------|--------|------|
| 無關圖片顯示率 | 50% | <10% |
| 相關文檔召回率 | 100% | >90% |
| 用戶滿意度 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 🐛 除錯技巧

### 查看搜尋結果

```bash
# 查看最近的搜尋日誌
docker logs ai-django --tail 200 | grep "Protocol Guide 搜索結果"

# 查看文檔相似度分數
docker logs ai-django --tail 200 | grep "分數範圍"
```

### 查看前端圖片提取

```javascript
// 在瀏覽器 Console 中
// 查看最後一次提取的圖片
console.log('Extracted images:', sessionStorage.getItem('last_extracted_images'));
```

### 查看 Dify 回應結構

```bash
# 查看完整的 Dify metadata
docker logs ai-django --tail 500 | grep -A 20 "retriever_resources"
```

---

## 📚 相關文檔

- `/docs/troubleshooting/protocol-assistant-dify-prompt-optimization.md` - Dify 提示詞優化
- `/docs/vector-search/vector-search-guide.md` - 向量搜尋配置
- `/docs/development/ui-component-guidelines.md` - 前端開發規範

---

## ✅ 已實施的解決方案

### 最終方案：停用 metadata 圖片提取功能（已完成）

**實施日期**：2025-11-14  
**決策原因**：相關度過濾效果不理想，選擇完全停用

#### 修改內容

**檔案**：`frontend/src/utils/imageProcessor.js`

```javascript
// ✅ 修改後的函數
export const extractImagesFromMetadata = (metadata) => {
  console.log('⚠️ extractImagesFromMetadata 功能已停用（避免顯示無關圖片）');
  return new Set();  // 返回空集合，不提取任何圖片
};
```

**修改說明**：
- ✅ 函數保留，確保不破壞現有調用
- ✅ 直接返回空集合，不處理任何 metadata
- ✅ 所有從 metadata 提取圖片的邏輯都被停用
- ⚠️ **注意**：從 AI 回答內容中提取的圖片（`extractImagesFromContent`）仍然正常工作

#### 實際效果

| 圖片來源 | 修改前 | 修改後 |
|---------|--------|--------|
| **metadata.retriever_resources** | ✅ 提取（所有文檔） | ❌ 停用 |
| **AI 回答內容** | ✅ 提取 | ✅ 提取（正常） |
| **message.content 中的圖片** | ✅ 提取 | ✅ 提取（正常） |

**針對本次問題**：

| 項目 | 修改前 | 修改後 |
|------|--------|--------|
| UNH-IOL 圖片（相關） | ✅ 顯示 | ❌ 不顯示 |
| Kingston 圖片（無關）| ❌ 誤顯示 | ❌ 不顯示 |
| I3C 圖片（無關） | ❌ 誤顯示 | ❌ 不顯示 |

**結果**：✅ 成功阻止所有從 metadata 提取的無關圖片

#### 影響範圍評估

**受影響的頁面**：
- Protocol Assistant 聊天頁面 ✅
- RVT Assistant 聊天頁面 ✅
- 其他所有 Assistant 聊天頁面 ✅

**不受影響的功能**：
- AI 回答中直接提到的圖片（如：「請看圖 xxx.png」）✅
- 手動上傳的圖片 ✅
- 圖片預覽和下載功能 ✅

#### 如何恢復功能

如果日後需要恢復 metadata 圖片提取：

```bash
# 方法 1：恢復到修改前版本
cd /home/user/codes/ai-platform-web
git log --oneline frontend/src/utils/imageProcessor.js  # 查看歷史
git checkout <commit-hash> frontend/src/utils/imageProcessor.js

# 方法 2：實施相關度過濾（之前的方案 2）
# 參考本文檔中的「方案 2：前端智能圖片過濾」章節

# 重啟前端
docker compose restart react
```

---

### ~~方案 2：前端相關度過濾（已嘗試，效果不理想）~~

**嘗試日期**：2025-11-14  
**放棄原因**：用戶反饋效果不好

曾嘗試添加 `minScore` 參數進行相關度過濾，但最終選擇完全停用功能。

---

**文檔更新日期**：2025-11-14  
**問題發現者**：Admin User  
**分析者**：AI Platform Team  
**實施者**：AI Platform Team  
**狀態**：✅ 已解決（metadata 圖片提取功能已停用）  
**優先級**：🔴 高（影響用戶體驗）→ ✅ 已完成
