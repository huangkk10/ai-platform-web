# 段落向量搜尋權重功能修復報告

## 📋 問題描述

### 原始問題
用戶設定 Protocol Assistant 的權重為：
- 標題權重：0%
- 內容權重：100%

但搜尋 "crystaldiskmark 5" 時仍然能找到結果（該關鍵字只存在於文檔標題中）。

### 預期行為
當標題權重設為 0% 時，搜尋結果應該：
- 完全忽略標題匹配
- 只匹配內容中的關鍵字
- 如果關鍵字只在標題中出現，應該不返回結果或分數非常低

---

## 🔍 根本原因分析

### 問題 1：段落搜尋使用單一向量
Protocol Guide 和 RVT Guide 實際上使用 **段落向量搜尋**（`SectionSearchService`），而不是整篇文檔搜尋。

`document_section_embeddings` 表原本只有一個 `embedding` 欄位：
- 這個欄位混合了標題和內容的向量
- 無法區分標題和內容的語義相似度
- 因此無法應用權重配置

### 問題 2：搜尋邏輯未支援多向量
`section_search_service.py` 的搜尋邏輯：
```sql
-- 舊版：只查詢單一 embedding 欄位
SELECT 
    section_id,
    1 - (embedding <=> query_vector) as similarity
FROM document_section_embeddings
WHERE source_table = 'protocol_guide'
```

這個查詢無法應用標題/內容權重。

---

## ✅ 解決方案

### 步驟 1：資料庫結構升級

添加多向量欄位到 `document_section_embeddings` 表：

```sql
ALTER TABLE document_section_embeddings 
ADD COLUMN title_embedding vector(1024),
ADD COLUMN content_embedding vector(1024);

-- 創建向量索引
CREATE INDEX idx_section_title_embedding 
    ON document_section_embeddings 
    USING ivfflat (title_embedding vector_cosine_ops) WITH (lists = 50);

CREATE INDEX idx_section_content_embedding 
    ON document_section_embeddings 
    USING ivfflat (content_embedding vector_cosine_ops) WITH (lists = 50);
```

### 步驟 2：重新生成多向量

執行腳本 `regenerate_section_multi_vectors.py`：
- 為每個段落分別生成 title_embedding 和 content_embedding
- 共處理 58 個段落
- 成功：53 個（Protocol: 5, RVT: 48）
- 失敗：5 個（缺少標題或內容的段落）

```bash
docker exec ai-django python regenerate_section_multi_vectors.py
```

### 步驟 3：修改搜尋服務

修改 `library/common/knowledge_base/section_search_service.py`：

#### 3.1 新增權重讀取函數

```python
def _get_weights_for_assistant(self, source_table: str) -> tuple:
    """
    根據 source_table 獲取對應的權重配置
    
    Returns:
        tuple: (title_weight, content_weight) 範圍 0.0-1.0
    """
    from api.models import SearchThresholdSetting
    
    # 映射表名到助手類型
    table_to_type = {
        'protocol_guide': 'protocol_assistant',
        'rvt_guide': 'rvt_assistant',
    }
    
    assistant_type = table_to_type.get(source_table)
    setting = SearchThresholdSetting.objects.get(assistant_type=assistant_type)
    
    title_weight = setting.title_weight / 100.0
    content_weight = setting.content_weight / 100.0
    
    logger.info(f"📊 載入段落搜尋權重配置: {assistant_type} -> "
                f"標題 {setting.title_weight}% / 內容 {setting.content_weight}%")
    
    return (title_weight, content_weight)
```

#### 3.2 更新搜尋 SQL

使用加權多向量搜尋：

```python
# 檢查是否有多向量資料
check_sql = """
    SELECT COUNT(*) 
    FROM document_section_embeddings 
    WHERE source_table = %s 
      AND title_embedding IS NOT NULL 
      AND content_embedding IS NOT NULL
"""

# 如果有多向量，使用加權搜尋
if multi_vector_count > 0:
    sql = f"""
        SELECT 
            section_id,
            source_id,
            heading_text,
            content,
            ({title_weight} * (1 - (title_embedding <=> %s::vector))) + 
            ({content_weight} * (1 - (content_embedding <=> %s::vector))) as similarity
        FROM document_section_embeddings
        WHERE source_table = %s
          AND title_embedding IS NOT NULL
          AND content_embedding IS NOT NULL
    """
```

**關鍵邏輯**：
- `title_weight * title_similarity`：標題相似度貢獻
- `content_weight * content_similarity`：內容相似度貢獻
- 最終分數 = 兩者加權總和

---

## 🧪 測試場景

### 測試 1：0% 標題權重（標題關鍵字應無效）

**設定**：
```
Protocol Assistant:
- 標題權重：0%
- 內容權重：100%
```

**測試查詢**：`"crystaldiskmark 5"`

**預期結果**：
- ❌ 不應找到標題為 "5.Install Burnin Test Pro 輸入 'License' 內容加 '-K'" 的文檔
- ✅ 只應找到內容中包含 "crystaldiskmark" 的文檔
- 如果關鍵字只在標題中，分數應為 0.0

**計算邏輯**：
```
title_similarity = 0.85 (假設標題匹配度高)
content_similarity = 0.0 (內容中無關鍵字)

final_score = (0.0 * 0.85) + (1.0 * 0.0) = 0.0
```

### 測試 2：100% 標題權重（內容關鍵字應無效）

**設定**：
```
Protocol Assistant:
- 標題權重：100%
- 內容權重：0%
```

**測試查詢**：內容中的關鍵字

**預期結果**：
- ✅ 只應找到標題匹配的文檔
- ❌ 內容匹配但標題不匹配的文檔不應出現

### 測試 3：平衡權重（60/40）

**設定**：
```
RVT Assistant:
- 標題權重：60%
- 內容權重：40%
```

**測試查詢**：同時在標題和內容中出現的關鍵字

**預期結果**：
- ✅ 標題和內容都匹配的文檔分數最高
- ✅ 標題匹配權重佔 60%
- ✅ 內容匹配權重佔 40%

---

## 📊 部署狀態

### 資料庫更新
✅ `document_section_embeddings` 表已添加 title_embedding 和 content_embedding 欄位  
✅ 向量索引已創建  
✅ 53/58 段落已生成多向量（91% 完成率）

### 程式碼更新
✅ `section_search_service.py` 已修改支援權重搜尋  
✅ 自動讀取 SearchThresholdSetting 配置  
✅ 向後相容（無多向量時使用舊版單一向量）

### 服務重啟
✅ Django 服務已重啟  
✅ 新的搜尋邏輯已生效

---

## 🎯 驗證步驟

### 1. 確認權重設定
```bash
docker exec postgres_db psql -U postgres -d ai_platform -c "
SELECT assistant_type, title_weight, content_weight 
FROM search_threshold_settings;
"
```

**預期輸出**：
```
assistant_type      | title_weight | content_weight
--------------------|--------------|---------------
protocol_assistant  |            0 |           100
rvt_assistant       |           60 |            40
```

### 2. 測試搜尋（瀏覽器）
1. 重新載入 Protocol Assistant 聊天頁面（Ctrl+F5）
2. 搜尋 "crystaldiskmark 5"
3. 觀察結果：
   - ✅ **正確**：沒有結果或分數極低（< 0.1）
   - ❌ **錯誤**：仍然找到 "5.Install Burnin Test Pro..." 文檔且分數 > 0.5

### 3. 檢查日誌
```bash
docker logs ai-django --tail 50 | grep -E "(載入段落搜尋權重|段落搜尋|多向量搜尋)"
```

**預期看到**：
```
[INFO] 📊 載入段落搜尋權重配置: protocol_assistant -> 標題 0% / 內容 100%
[INFO] ✅ 使用多向量搜尋 (權重: 0%/100%)
[INFO] 🔍 段落搜尋: query='crystaldiskmark 5', results=0, weights=0%/100%
```

---

## 📝 技術亮點

### 1. 向後相容設計
搜尋邏輯會先檢查是否有多向量資料：
- 有多向量：使用加權搜尋（支援權重）
- 無多向量：使用舊版單一向量搜尋（不支援權重，但仍能運作）

### 2. 自動權重載入
從資料庫動態讀取權重配置，無需重啟服務即可應用新的權重設定。

### 3. 完整的多向量架構
- 文檔級別：`document_embeddings` 表（title_embedding + content_embedding）
- 段落級別：`document_section_embeddings` 表（title_embedding + content_embedding）
- 統一的權重配置：`search_threshold_settings` 表

---

## 🚨 已知限制

### 1. 段落無標題或內容
5 個段落無法生成多向量（缺少標題或內容），這些段落會被排除在搜尋結果之外。

**解決方案**（未來）：
- 為無標題段落使用父段落的標題
- 為空內容段落使用預設內容或跳過

### 2. IVFFlat 索引警告
由於資料量少（58 個段落），IVFFlat 索引會顯示警告：
```
NOTICE:  ivfflat index created with little data
```

**影響**：可忽略，資料量增加後自動改善。

### 3. 權重極端情況
當權重設為 100%/0% 或 0%/100% 時：
- 搜尋完全依賴單一向量
- 可能錯過有價值的結果
- 建議使用 20/80 或 80/20 作為極端值上限

---

## 📚 相關文檔

- **權重配置 UI**：`/docs/features/weight-configuration-ui-implementation.md`
- **原始問題分析**：`/docs/debugging/weight-configuration-not-working-issue.md`
- **整篇文檔搜尋修復**：`/docs/features/weight-configuration-fix-report.md`（已過時，段落搜尋才是實際使用的方法）

---

## 🎉 總結

### 問題根源
權重配置 UI 正常工作，但實際搜尋使用的段落向量搜尋（`SectionSearchService`）沒有支援多向量，導致權重無效。

### 解決方案
1. 為段落表添加 title_embedding 和 content_embedding 欄位
2. 重新生成所有段落的多向量
3. 修改搜尋邏輯支援加權多向量搜尋

### 驗證狀態
- ✅ 資料庫升級完成
- ✅ 多向量生成完成（91% 成功率）
- ✅ 搜尋邏輯更新完成
- ⚠️ **等待用戶測試驗證**

---

**更新日期**：2025-11-06  
**執行者**：AI Assistant  
**狀態**：✅ 已部署，等待用戶驗證
