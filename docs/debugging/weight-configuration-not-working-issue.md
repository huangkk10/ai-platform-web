# 🔴 權重配置未生效問題分析報告

## 📅 日期
2025-11-06

## 🎯 問題描述

**用戶反饋**：
- 設定 Protocol Assistant 為 0% 標題權重 / 100% 內容權重
- 搜尋 "crystaldiskmark"（只出現在標題中）
- **預期**：應該找不到結果
- **實際**：仍然找到結果

## 🔍 根因分析

### 1. 搜尋流程追蹤

```
用戶查詢
  ↓
Protocol Guide Search Service
  ↓
search_with_vectors_generic() (vector_search_helper.py)
  ↓
embedding_service.search_similar_documents()  ← ❌ 問題在這裡！
  ↓
SQL: SELECT ... FROM document_embeddings
     WHERE 1 - (de.embedding <=> query) as similarity_score
                ^^^^^^^^^^
                只查詢段落向量（title + content 混合）
                沒有使用 title_embedding 和 content_embedding
```

### 2. 程式碼證據

**檔案**: `/backend/api/services/embedding_service.py`

**目前使用的方法**（LINE 244-308）：
```python
def search_similar_documents(self, query: str, ...):
    """搜索相似文檔 - ❌ 舊方法，不支援權重"""
    
    sql = f"""
        SELECT 
            de.source_table,
            de.source_id,
            1 - (de.embedding <=> %s) as similarity_score,  ← 只用段落向量
            ...
        FROM document_embeddings de
        ...
    """
```

**應該使用的方法**（LINE 383-470）：
```python
def search_similar_documents_multi(
    self,
    query: str,
    title_weight: float = 0.6,   ← ✅ 支援權重
    content_weight: float = 0.4
):
    """使用多向量方法搜索相似文檔（方案 A：標題/內容分開計算）"""
    
    sql = f"""
        SELECT 
            de.source_table,
            de.source_id,
            -- 標題相似度
            1 - (de.title_embedding <=> %s::vector) as title_score,  ← ✅ 使用標題向量
            -- 內容相似度
            1 - (de.content_embedding <=> %s::vector) as content_score, ← ✅ 使用內容向量
            -- 加權最終分數
            (%s * (1 - (de.title_embedding <=> %s::vector))) + 
            (%s * (1 - (de.content_embedding <=> %s::vector))) as final_score,
            ...
        FROM document_embeddings de
        ...
    """
```

### 3. 呼叫鏈分析

**檔案**: `/library/common/knowledge_base/vector_search_helper.py` (LINE 97-102)

```python
def search_with_vectors_generic(...):
    embedding_service = get_embedding_service(model_type)
    
    vector_results = embedding_service.search_similar_documents(  ← ❌ 呼叫錯誤的方法
        query=query,
        source_table=source_table,
        limit=limit,
        threshold=threshold,
        use_1024_table=use_1024
    )
```

**問題**：
- 沒有傳遞 `title_weight` 和 `content_weight` 參數
- 呼叫的是 `search_similar_documents` 而不是 `search_similar_documents_multi`

## 🛠️ 修復方案

### 方案 A：修改 vector_search_helper.py（推薦）

**優點**：
- 一次修改，所有 Assistant 都受益
- 自動從資料庫讀取權重配置
- 向後相容

**步驟**：

1. **修改 `search_with_vectors_generic` 函數**
   - 從 `SearchThresholdSetting` 讀取權重配置
   - 呼叫 `search_similar_documents_multi` 而不是 `search_similar_documents`
   - 傳遞 `title_weight` 和 `content_weight` 參數

2. **權重轉換**
   - 資料庫儲存格式：整數 0-100（例如：60, 40）
   - API 需要格式：浮點數 0.0-1.0（例如：0.6, 0.4）
   - 轉換公式：`weight_decimal = weight_int / 100`

### 方案 B：修改每個 Search Service（不推薦）

**缺點**：
- 需要修改多個檔案（Protocol、RVT、Know Issue 等）
- 程式碼重複
- 容易遺漏

## 📊 影響範圍

### 受影響的 Assistant
1. ✅ Protocol Assistant
2. ✅ RVT Assistant
3. ✅ 未來所有使用 `search_with_vectors_generic` 的 Assistant

### 不受影響的功能
- ❌ Threshold（相似度閾值）仍然有效
- ❌ 向量生成和儲存正常運作
- ❌ UI 配置正常儲存到資料庫

## 🎯 預期修復後效果

### 測試場景 1：Protocol Assistant (0% 標題 / 100% 內容)
- **查詢**："crystaldiskmark"
- **資料**：
  - 標題包含："crystaldiskmark 效能測試"
  - 內容不包含該關鍵字
- **預期結果**：❌ **不應該找到**（因為標題權重 = 0）

### 測試場景 2：Protocol Assistant (100% 標題 / 0% 內容)
- **查詢**："安裝步驟"
- **資料**：
  - 標題不包含該關鍵字
  - 內容包含："詳細的安裝步驟..."
- **預期結果**：❌ **不應該找到**（因為內容權重 = 0）

### 測試場景 3：平衡查詢 (60% / 40%)
- **查詢**："Samsung 測試"
- **資料 A**：標題匹配 "Samsung 測試指南"，內容不匹配
- **資料 B**：標題不匹配，內容匹配 "Samsung 相關內容"
- **預期結果**：✅ **資料 A 分數更高**（因為標題權重較高）

## 🔧 實作細節

### 1. 讀取權重配置

```python
from api.models import SearchThresholdSetting

def get_weights_for_assistant(source_table: str):
    """根據 source_table 獲取權重配置"""
    
    # 映射 source_table 到 assistant_type
    table_to_type = {
        'protocol_guide': 'protocol_assistant',
        'rvt_guide': 'rvt_assistant',
    }
    
    assistant_type = table_to_type.get(source_table)
    if not assistant_type:
        # 預設值
        return 0.6, 0.4
    
    try:
        setting = SearchThresholdSetting.objects.get(assistant_type=assistant_type)
        title_weight = setting.title_weight / 100.0  # 轉換為小數
        content_weight = setting.content_weight / 100.0
        return title_weight, content_weight
    except SearchThresholdSetting.DoesNotExist:
        return 0.6, 0.4  # 預設值
```

### 2. 修改搜尋呼叫

```python
def search_with_vectors_generic(...):
    # ... 現有代碼
    
    # ✅ 讀取權重配置
    title_weight, content_weight = get_weights_for_assistant(source_table)
    
    # ✅ 使用多向量搜尋方法
    vector_results = embedding_service.search_similar_documents_multi(
        query=query,
        source_table=source_table,
        limit=limit,
        threshold=threshold,
        title_weight=title_weight,      # ✅ 新增
        content_weight=content_weight   # ✅ 新增
    )
```

## 📋 修復檢查清單

### 程式碼修改
- [ ] 修改 `vector_search_helper.py`
- [ ] 新增 `get_weights_for_assistant()` 函數
- [ ] 更新 `search_with_vectors_generic()` 呼叫
- [ ] 測試權重讀取邏輯

### 測試驗證
- [ ] 測試場景 1：0% 標題權重
- [ ] 測試場景 2：100% 標題權重
- [ ] 測試場景 3：平衡權重 (60/40)
- [ ] 測試場景 4：極端權重 (20/80)
- [ ] 確認資料庫查詢正確

### 文檔更新
- [ ] 更新實作報告
- [ ] 記錄 Bug 修復過程
- [ ] 更新 API 文檔（如需要）

## 🎓 經驗教訓

1. **UI 配置正常 ≠ 功能正常**
   - 資料正確儲存到資料庫
   - 但程式碼沒有讀取和使用

2. **多向量實作需要端到端驗證**
   - 向量生成 ✅
   - 向量儲存 ✅
   - 向量搜尋 ❌ ← 這裡出問題

3. **新舊方法並存的風險**
   - `search_similar_documents` (舊)
   - `search_similar_documents_multi` (新)
   - 容易誤用舊方法

## 🚀 後續優化建議

1. **重構建議**
   - 廢棄 `search_similar_documents`
   - 統一使用 `search_similar_documents_multi`
   - 預設權重改為從資料庫讀取

2. **測試自動化**
   - 建立權重測試案例
   - 自動驗證搜尋結果
   - 整合到 CI/CD

3. **監控和日誌**
   - 記錄實際使用的權重
   - 追蹤搜尋效果
   - 分析最佳權重配置

---

**建立日期**: 2025-11-06  
**嚴重程度**: 🔴 高（核心功能未生效）  
**影響範圍**: 所有使用向量搜尋的 Assistant  
**預計修復時間**: 30 分鐘
