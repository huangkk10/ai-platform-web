# 🔧 權重配置修復報告

## 📅 修復日期
2025-11-06

## 🔴 問題描述

**用戶反饋**：
- 在管理後台設定 Protocol Assistant 為 **0% 標題權重 / 100% 內容權重**
- 搜尋 "crystaldiskmark"（該關鍵字只出現在標題中，內容沒有）
- **預期行為**：應該找不到結果（因為標題權重 = 0%）
- **實際行為**：仍然找到結果

## 🔍 根因分析

### 問題定位

搜尋程式碼**沒有使用**多向量搜尋方法，導致權重配置無法生效：

```python
# ❌ 舊程式碼（vector_search_helper.py LINE 97-102）
vector_results = embedding_service.search_similar_documents(  # 錯誤的方法
    query=query,
    source_table=source_table,
    limit=limit,
    threshold=threshold,
    use_1024_table=use_1024
)
```

**問題**：
1. `search_similar_documents` 只查詢 `embedding` 欄位（段落向量）
2. 沒有使用 `title_embedding` 和 `content_embedding`
3. 沒有傳遞 `title_weight` 和 `content_weight` 參數

### SQL 查詢對比

**舊方法（錯誤）**：
```sql
SELECT 
    de.source_table,
    de.source_id,
    1 - (de.embedding <=> query_vector) as similarity_score  -- 只用段落向量
FROM document_embeddings de
ORDER BY de.embedding <=> query_vector
```

**新方法（正確）**：
```sql
SELECT 
    de.source_table,
    de.source_id,
    1 - (de.title_embedding <=> query) as title_score,
    1 - (de.content_embedding <=> query) as content_score,
    (title_weight * title_score) + (content_weight * content_score) as final_score
FROM document_embeddings de
ORDER BY final_score DESC
```

## ✅ 修復內容

### 1. 新增權重讀取函數

**檔案**：`/library/common/knowledge_base/vector_search_helper.py`

```python
def _get_weights_for_assistant(source_table: str) -> tuple:
    """
    根據 source_table 獲取權重配置
    
    從資料庫讀取 SearchThresholdSetting，並將整數權重（0-100）
    轉換為浮點數權重（0.0-1.0）
    """
    from api.models import SearchThresholdSetting
    
    # 映射 source_table 到 assistant_type
    table_to_type = {
        'protocol_guide': 'protocol_assistant',
        'rvt_guide': 'rvt_assistant',
    }
    
    assistant_type = table_to_type.get(source_table)
    if not assistant_type:
        return 0.6, 0.4  # 預設值
    
    try:
        setting = SearchThresholdSetting.objects.get(assistant_type=assistant_type)
        title_weight = setting.title_weight / 100.0  # 60 -> 0.6
        content_weight = setting.content_weight / 100.0  # 40 -> 0.4
        
        logger.info(
            f"載入權重配置: {assistant_type} -> "
            f"標題 {setting.title_weight}% / 內容 {setting.content_weight}%"
        )
        
        return title_weight, content_weight
    except:
        return 0.6, 0.4  # 預設值
```

### 2. 更新搜尋呼叫

**檔案**：`/library/common/knowledge_base/vector_search_helper.py`

```python
def search_with_vectors_generic(...):
    try:
        # ✅ 步驟 1: 讀取權重配置
        title_weight, content_weight = _get_weights_for_assistant(source_table)
        
        # ✅ 步驟 2: 使用多向量搜尋方法
        embedding_service = get_embedding_service(model_type)
        
        vector_results = embedding_service.search_similar_documents_multi(  # 正確的方法
            query=query,
            source_table=source_table,
            limit=limit,
            threshold=threshold,
            title_weight=title_weight,      # ✅ 傳遞標題權重
            content_weight=content_weight   # ✅ 傳遞內容權重
        )
        
        logger.info(
            f"✅ 多向量搜尋找到 {len(vector_results)} 條結果: {source_table} "
            f"(權重: {title_weight*100:.0f}%/{content_weight*100:.0f}%)"
        )
```

### 3. 重啟服務

```bash
docker compose restart django
```

## 🧪 驗證測試

### 測試場景 1：0% 標題權重

**設定**：
```
Protocol Assistant: 0% 標題 / 100% 內容
```

**測試資料**：
```
標題：「CrystalDiskMark 效能測試指南」
內容：「本文介紹如何使用該工具進行測試...」（不包含 CrystalDiskMark）
```

**測試步驟**：
1. 搜尋 "CrystalDiskMark"
2. 觀察搜尋結果

**預期結果**：
- ❌ 應該找不到結果（或分數 < 0.1）
- 原因：關鍵字只在標題，但標題權重 = 0%

### 測試場景 2：100% 標題權重

**設定**：
```
Protocol Assistant: 100% 標題 / 0% 內容
```

**測試資料**：
```
標題：「測試指南」（不包含特定關鍵字）
內容：「詳細的 ULINK 連接測試步驟...」
```

**測試步驟**：
1. 搜尋 "ULINK 連接"
2. 觀察搜尋結果

**預期結果**：
- ❌ 應該找不到結果（或分數 < 0.1）
- 原因：關鍵字只在內容，但內容權重 = 0%

### 測試場景 3：平衡權重

**設定**：
```
RVT Assistant: 60% 標題 / 40% 內容
```

**測試資料 A**：
```
標題：「Samsung SSD 測試」（包含 Samsung）
內容：「其他內容...」（不包含 Samsung）
```

**測試資料 B**：
```
標題：「測試指南」（不包含 Samsung）
內容：「Samsung 相關測試步驟...」（包含 Samsung）
```

**測試步驟**：
1. 搜尋 "Samsung"
2. 比較兩筆資料的分數

**預期結果**：
- ✅ 資料 A 分數應該較高
- 原因：標題匹配權重 60% > 內容匹配權重 40%

## 📊 日誌驗證

修復後，搜尋時應該會在日誌中看到：

```
[INFO] library.common.knowledge_base.vector_search_helper: 載入權重配置: protocol_assistant -> 標題 0% / 內容 100%
[INFO] library.common.knowledge_base.vector_search_helper: ✅ 多向量搜尋找到 3 條結果: protocol_guide (權重: 0%/100%)
```

**驗證命令**：
```bash
docker logs ai-django --tail 100 | grep "載入權重配置"
docker logs ai-django --tail 100 | grep "多向量搜尋"
```

## 🎯 影響範圍

### 受影響的功能
- ✅ Protocol Assistant 向量搜尋
- ✅ RVT Assistant 向量搜尋
- ✅ 所有使用 `search_with_vectors_generic` 的知識庫

### 不受影響的功能
- ✅ Threshold（相似度閾值）配置
- ✅ 向量生成和儲存
- ✅ UI 權重設定介面

## 🔧 技術細節

### 權重轉換

**資料庫儲存**：整數 0-100
```sql
title_weight = 60
content_weight = 40
```

**API 使用**：浮點數 0.0-1.0
```python
title_weight = 0.6
content_weight = 0.4
```

**轉換公式**：
```python
decimal_weight = integer_weight / 100.0
```

### 分數計算公式

```
final_score = (title_weight × title_similarity) + (content_weight × content_similarity)
```

**範例計算**：

場景：60% 標題 / 40% 內容
- 標題相似度：0.8
- 內容相似度：0.5

```
final_score = (0.6 × 0.8) + (0.4 × 0.5)
            = 0.48 + 0.20
            = 0.68
```

## 📝 修改檔案清單

1. ✅ `/library/common/knowledge_base/vector_search_helper.py`
   - 新增 `_get_weights_for_assistant()` 函數
   - 修改 `search_with_vectors_generic()` 函數
   - 更新日誌訊息

2. ✅ `/docs/debugging/weight-configuration-not-working-issue.md`
   - 問題分析文檔

3. ✅ `/docs/features/weight-configuration-fix-report.md`
   - 修復報告（本檔案）

## ✅ 驗證檢查清單

### 程式碼修改
- [x] 新增權重讀取函數
- [x] 更新搜尋呼叫使用 `search_similar_documents_multi`
- [x] 添加日誌輸出權重資訊
- [x] 重啟 Django 服務

### 功能測試
- [ ] 測試 0% 標題權重場景
- [ ] 測試 100% 標題權重場景
- [ ] 測試平衡權重場景 (60/40)
- [ ] 確認日誌有載入權重訊息
- [ ] 確認搜尋結果符合預期

### 文檔更新
- [x] 建立問題分析文檔
- [x] 建立修復報告
- [x] 建立測試驗證腳本

## 🎓 經驗教訓

### 1. 多向量實作需要端到端驗證

雖然完成了：
- ✅ 資料庫表結構（`title_embedding`, `content_embedding`）
- ✅ 向量生成和儲存（`store_document_embeddings_multi`）
- ✅ UI 權重配置介面

但遺漏了：
- ❌ 搜尋函數沒有使用多向量方法
- ❌ 沒有讀取權重配置

**教訓**：新功能開發要確保**所有環節都連接正確**。

### 2. 新舊方法並存的風險

系統同時存在兩個搜尋方法：
- `search_similar_documents`（舊）
- `search_similar_documents_multi`（新）

容易誤用舊方法，導致新功能無效。

**建議**：未來應該廢棄舊方法，統一使用新方法。

### 3. UI 配置正常 ≠ 功能正常

用戶可以正常設定權重並儲存到資料庫，但後端程式碼沒有讀取和使用這些設定。

**建議**：開發新功能時，應該同時進行端到端測試。

## 🚀 後續優化建議

### 1. 重構建議

- 廢棄 `search_similar_documents`
- 統一使用 `search_similar_documents_multi`
- 預設從資料庫讀取權重

### 2. 測試自動化

- 建立權重配置測試案例
- 自動驗證搜尋結果
- 整合到 CI/CD

### 3. 監控和分析

- 記錄實際使用的權重
- 追蹤搜尋效果
- 分析最佳權重配置

---

**修復者**: AI Assistant  
**審核者**: 待審核  
**狀態**: ✅ 已修復，待測試驗證  
**嚴重程度**: 🔴 高（核心功能未生效）  
**修復時間**: 30 分鐘
