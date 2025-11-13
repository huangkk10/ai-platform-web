# Protocol Assistant 無關圖片問題 - 快速參考指南

## 🎯 問題摘要

**現象**：詢問「iol root密碼」時出現 Kingston 開卡的圖片  
**原因**：文檔搜尋返回了多個低相關度文檔，前端提取了所有文檔中的圖片  
**影響**：用戶體驗差，顯示了與問題無關的圖片

---

## ⚡ 快速修復（5 分鐘）

### 步驟 1：執行修復腳本

```bash
# 進入 Django 容器
docker exec -it ai-django bash

# 執行修復腳本
python /app/fix_protocol_image_threshold.py

# 輸入 'y' 確認調整
```

### 步驟 2：驗證修復效果

```bash
# 測試查詢
1. 前往 Protocol Assistant
2. 詢問「iol root密碼」
3. 確認不再出現 Kingston 圖片
4. 確認仍然返回 UNH-IOL 相關內容
```

---

## 📊 技術細節

### 根本原因

1. **文檔搜尋 threshold=0.8 過低**
   - UNH-IOL 文檔：83% 相似度 ✅
   - Kingston 開卡：68% 相似度 ❌ (應該被過濾)

2. **前端圖片提取邏輯無過濾**
   ```javascript
   // 問題代碼
   extractImagesFromMetadata(metadata) {
     // 提取所有 retriever_resources 中的圖片
     // 沒有判斷文檔相關性
   }
   ```

3. **Dify 回應包含所有引用來源**
   - Dify 將所有搜尋結果視為引用來源
   - 前端解析時提取了所有圖片

### 修復原理

**調整 threshold 從 0.8 到 0.85**

```
修改前：
├─ UNH-IOL (83%) → 包含 ✅
├─ Kingston (68%) → 包含 ❌ (誤報)
└─ I3C (65%) → 包含 ❌ (誤報)

修改後：
├─ UNH-IOL (83%) → 過濾掉 ⚠️ (需要測試)
├─ Kingston (68%) → 過濾掉 ✅
└─ I3C (65%) → 過濾掉 ✅
```

**⚠️ 注意**：threshold=0.85 可能過高，如果 UNH-IOL (83%) 被過濾，建議調整到 0.82

---

## 🔧 進階解決方案

### 方案 1：動態 Threshold（推薦）

```python
# 根據文檔相似度差異自動調整
def smart_threshold(results):
    if len(results) == 0:
        return []
    
    # 取最高分
    top_score = results[0]['score']
    
    # 過濾：只保留與最高分差距 < 0.15 的文檔
    filtered = [r for r in results if r['score'] >= top_score - 0.15]
    
    return filtered
```

### 方案 2：前端智能過濾

```javascript
// frontend/src/utils/imageProcessor.js
export const extractImagesFromMetadata = (metadata, aiAnswer) => {
  const resources = metadata?.retriever_resources;
  
  return resources
    .filter(r => r.score >= 0.80 || aiAnswer.includes(r.title))
    .flatMap(r => extractImagesFromResource(r));
};
```

### 方案 3：Dify 提示詞優化

在 Dify 工作室添加：
```
只引用相似度 > 80% 的文檔
如果文檔不相關，不要提及
```

---

## 📋 測試檢查清單

- [ ] IOL 密碼查詢不顯示 Kingston 圖片
- [ ] CrystalDiskMark 查詢顯示正確圖片
- [ ] 相關文檔仍然正常返回
- [ ] 搜尋速度沒有明顯下降

---

## 📚 完整文檔

詳細分析請參考：
`/docs/troubleshooting/protocol-assistant-irrelevant-images-issue.md`

---

---

## ✅ 已實施的解決方案

### 方案：停用 metadata 圖片提取功能

**實施日期**：2025-11-14  
**實施方式**：前端函數停用

#### 修改內容

**檔案**：`frontend/src/utils/imageProcessor.js`

```javascript
// ✅ 修改後
export const extractImagesFromMetadata = (metadata) => {
  console.log('⚠️ extractImagesFromMetadata 功能已停用（避免顯示無關圖片）');
  return new Set();  // 返回空集合，不提取任何圖片
};
```

**修改前**：函數會從所有 `retriever_resources` 中提取圖片  
**修改後**：函數直接返回空集合，不提取任何圖片

#### 效果

| 項目 | 修改前 | 修改後 |
|------|--------|--------|
| UNH-IOL 圖片 | ✅ 顯示 | ❌ 不顯示 |
| Kingston 圖片 | ❌ 誤顯示 | ❌ 不顯示 |
| I3C 圖片 | ❌ 誤顯示 | ❌ 不顯示 |

**結果**：所有從 metadata 提取的圖片都不再顯示，包括相關和不相關的圖片。

#### 影響範圍

- ✅ Protocol Assistant：不再顯示無關圖片
- ✅ RVT Assistant：不再顯示無關圖片  
- ✅ 所有 Assistant：metadata 圖片功能統一停用
- ⚠️ **注意**：從 AI 回答內容中提取的圖片（`extractImagesFromContent`）仍然正常工作

#### 如何恢復

如果需要恢復圖片提取功能：

```bash
# 恢復到修改前的版本
cd /home/user/codes/ai-platform-web
git checkout frontend/src/utils/imageProcessor.js

# 重啟前端
docker compose restart react
```

---

**更新日期**：2025-11-14  
**問題編號**：PROTO-IMG-001  
**嚴重程度**：🔴 高（影響用戶體驗）  
**狀態**：✅ 已解決（metadata 圖片提取功能已停用）
