# 向量維度使用情況審計報告

**審計日期**: 2025-10-22  
**審計人員**: AI Assistant  
**目的**: 確認專案是否完全遷移到 1024 維向量，或仍存在其他維度的向量資料庫

---

## 📊 審計結果總結

### ✅ 資料庫層面：完全使用 1024 維

#### 主要向量表
```sql
-- 1. document_embeddings (文檔級向量)
embedding vector(1024)  ✅ 已為 1024 維

-- 2. document_section_embeddings (段落級向量)
embedding vector(1024)  ✅ 已為 1024 維
```

**結論**: ✅ **資料庫層面已完全統一為 1024 維，無其他維度的向量表存在**

---

## 🔍 程式碼層面：發現混用情況

### ⚠️ 問題 1: `get_embedding_service()` 預設使用 768 維

**位置**: `backend/api/services/embedding_service.py:48-61`

```python
def __init__(self, model_type: str = 'standard'):
    """
    初始化嵌入服務
    
    Args:
        model_type: 模型類型 ('lightweight', 'standard', 'high_precision')
    """
    if model_type not in self.MODEL_CONFIGS:
        # 如果是舊的模型名稱，回退到輕量級模型
        if isinstance(model_type, str) and 'MiniLM' in model_type:
            model_type = 'lightweight'
        else:
            model_type = 'standard'  # ⚠️ 默認使用 768 維標準模型
```

**問題說明**:
- 當調用 `get_embedding_service()` 時（無參數），預設使用 `'standard'` 模型
- `'standard'` 模型為 768 維：`paraphrase-multilingual-mpnet-base-v2`
- **這會導致維度不匹配錯誤**（資料庫是 1024 維，但生成的向量是 768 維）

---

### ⚠️ 問題 2: 多處程式碼未指定模型類型

**發現位置** (共 12 處):

#### 後端管理命令
```python
# backend/api/management/commands/generate_know_issue_embeddings.py:77
embedding_service = get_embedding_service()  # ⚠️ 未指定，預設 768 維
```

**實際情況**: 此檔案有 `--model-type` 參數，預設為 `ultra_high`，但程式碼中未使用該參數！

#### ViewSet 中的調用
```python
# backend/api/views/viewsets.py:1067
service = get_embedding_service()  # 註解說「使用 1024 維模型」，但實際未指定

# backend/api/views/viewsets/knowledge_viewsets.py (4 處)
# Line 661, 788, 1139, 1315
embedding_service = get_embedding_service()  # ⚠️ 未指定
```

#### Mixin 中的調用
```python
# backend/api/views/mixins/vector_management_mixin.py (2 處)
# Line 75, 149
service = get_embedding_service()  # ⚠️ 未指定
```

#### Library 中的調用
```python
# library/common/knowledge_base/base_vector_service.py (3 處)
# Line 54, 91, 153
service = self._get_embedding_service()  # ⚠️ 未指定
return get_embedding_service()  # ⚠️ 未指定

# library/protocol_guide/viewset_manager.py:155
service = get_embedding_service()  # ⚠️ 未指定
```

---

### ✅ 正確使用 1024 維的地方

以下程式碼**正確**指定了 `ultra_high` (1024 維):

```python
# ✅ library/rvt_analytics/chat_vector_service.py:35
self.embedding_service = get_embedding_service('ultra_high')

# ✅ library/rvt_analytics/tasks.py:51
embedding_service = get_embedding_service('ultra_high')

# ✅ library/common/knowledge_base/section_search_service.py:19
self.embedding_service = get_embedding_service('ultra_high')

# ✅ library/common/knowledge_base/section_vectorization_service.py:21
self.embedding_service = get_embedding_service('ultra_high')

# ✅ library/common/knowledge_base/vector_search_helper.py:90
model_type = 'ultra_high' if use_1024 else 'standard'
```

---

### 🗄️ 舊版相容代碼（已棄用）

**位置**: `backend/api/services/embedding_service.py:370-382`

```python
def search_rvt_guide_with_vectors_768_legacy(query: str, limit: int = 5, threshold: float = 0.0) -> List[dict]:
    """
    ⚠️ DEPRECATED - 已棄用，保留以防回滾需要
    
    使用768維向量搜索 RVT Guide（舊版）
    這是從 1024 維遷移前的版本，僅供緊急回滾使用
    """
    service = get_embedding_service('standard')  # 使用768維模型
    
    # 搜索相似向量
    vector_results = service.search_similar_documents(
        query=query,
        source_table='rvt_guide',
        limit=limit,
        threshold=threshold,
        use_1024_table=False  # 使用舊的768維表格
    )
```

**狀態**: 此函數已標記為 DEPRECATED，但仍存在於程式碼中

---

## 🎯 問題影響分析

### 高風險情況

#### 1. **維度不匹配錯誤**
當程式碼調用 `get_embedding_service()` 而未指定模型類型時：
- 生成的向量維度：**768 維**
- 資料庫欄位維度：**1024 維**
- **結果**: PostgreSQL 會拒絕插入，報錯 `dimension mismatch`

#### 2. **潛在的資料不一致**
如果某些程式碼生成 768 維向量，某些生成 1024 維：
- 相同內容的向量會不一致
- 搜尋結果會不正確
- 相似度計算會失敗

---

## ✅ 修復建議

### 建議 1: 修改預設模型為 1024 維（推薦）⭐⭐⭐⭐⭐

**修改位置**: `backend/api/services/embedding_service.py`

```python
def __init__(self, model_type: str = 'ultra_high'):  # ✅ 改為 ultra_high
    """
    初始化嵌入服務
    
    Args:
        model_type: 模型類型 (預設: 'ultra_high' - 1024維)
    """
    if model_type not in self.MODEL_CONFIGS:
        # 如果是舊的模型名稱，回退到 ultra_high
        if isinstance(model_type, str) and 'MiniLM' in model_type:
            model_type = 'lightweight'
        else:
            model_type = 'ultra_high'  # ✅ 預設使用 1024 維
```

**影響範圍**: 
- ✅ 所有未指定模型的 `get_embedding_service()` 調用都會使用 1024 維
- ✅ 無需修改 12 處調用代碼
- ⚠️ 需要測試確保無副作用

**風險**: 低（因為資料庫已是 1024 維）

---

### 建議 2: 顯式指定所有調用（保守）⭐⭐⭐⭐

**修改所有 12 處調用**，明確指定 `'ultra_high'`:

```python
# ❌ 修改前
embedding_service = get_embedding_service()

# ✅ 修改後
embedding_service = get_embedding_service('ultra_high')
```

**優點**:
- ✅ 明確清晰，無歧義
- ✅ 不會影響其他可能依賴預設值的代碼

**缺點**:
- ⚠️ 需要修改 12 處代碼
- ⚠️ 未來容易遺漏

---

### 建議 3: 刪除舊版相容代碼⭐⭐⭐

**刪除以下已棄用函數**:
- `search_rvt_guide_with_vectors_768_legacy()`
- `_get_rvt_guide_results()` (已有註解標記為 DEPRECATED)

**理由**:
- 資料庫已無 768 維表格
- 保留這些代碼會造成混淆
- 如果真需要回滾，可以從 Git 歷史恢復

---

## 📋 修復檢查清單

### 階段 1: 立即修復（必須）✅
- [ ] 修改 `OpenSourceEmbeddingService.__init__()` 預設值為 `'ultra_high'`
- [ ] 修復 `generate_know_issue_embeddings.py` 中未使用 `model_type` 參數的問題
- [ ] 測試所有向量生成功能是否正常

### 階段 2: 代碼清理（強烈建議）✅
- [ ] 刪除 `search_rvt_guide_with_vectors_768_legacy()` 函數
- [ ] 刪除 `_get_rvt_guide_results()` 函數
- [ ] 移除 `use_1024_table` 參數（已無意義，資料庫統一為 1024 維）

### 階段 3: 代碼審查（可選）🔧
- [ ] 顯式指定所有 `get_embedding_service()` 調用的模型類型
- [ ] 添加單元測試驗證向量維度
- [ ] 更新相關文檔

---

## 🧪 測試建議

### 測試 1: 驗證預設模型維度
```python
# tests/test_vector_search/test_embedding_dimension.py

def test_default_embedding_service_dimension():
    """測試預設 embedding service 使用 1024 維"""
    from api.services.embedding_service import get_embedding_service
    
    service = get_embedding_service()
    test_embedding = service.generate_embedding("測試文本")
    
    assert len(test_embedding) == 1024, f"預設維度應為 1024，實際為 {len(test_embedding)}"
    print("✅ 預設 embedding service 維度正確：1024 維")
```

### 測試 2: 驗證資料庫插入
```python
def test_vector_insertion_to_database():
    """測試向量可以正確插入資料庫"""
    from api.services.embedding_service import get_embedding_service
    
    service = get_embedding_service()
    
    # 生成測試向量
    success = service.store_document_embedding(
        source_table='test_table',
        source_id=99999,
        content="測試內容",
        use_1024_table=True
    )
    
    assert success, "向量插入失敗"
    
    # 清理測試資料
    service.delete_document_embedding('test_table', 99999, use_1024_table=True)
    
    print("✅ 向量插入資料庫測試通過")
```

---

## 📊 統計數據

### 模型配置
| 模型類型 | 模型名稱 | 維度 | 使用狀況 |
|---------|---------|------|---------|
| `lightweight` | paraphrase-multilingual-MiniLM-L12-v2 | 384 | ❌ 未使用 |
| `standard` | paraphrase-multilingual-mpnet-base-v2 | 768 | ⚠️ 預設但不應使用 |
| `high_precision` | sentence-transformers/all-mpnet-base-v2 | 768 | ❌ 未使用 |
| `ultra_high` | intfloat/multilingual-e5-large | 1024 | ✅ 應該使用 |
| `maximum` | sentence-transformers/all-MiniLM-L6-v2 | 384 | ❌ 測試用 |

### 程式碼調用統計
| 調用方式 | 數量 | 狀態 |
|---------|------|------|
| `get_embedding_service('ultra_high')` | 4 處 | ✅ 正確 |
| `get_embedding_service()` | 12 處 | ⚠️ 潛在問題 |
| `get_embedding_service('standard')` | 1 處 | ❌ 已棄用函數中 |

---

## 🎯 結論

### 當前狀態
- ✅ **資料庫層面**: 已完全統一為 1024 維
- ⚠️ **程式碼層面**: 存在預設值不一致的風險
- ⚠️ **潛在問題**: 12 處調用可能生成 768 維向量，導致維度不匹配錯誤

### 建議行動
1. **立即修復**: 更改 `get_embedding_service()` 預設值為 `'ultra_high'`
2. **清理代碼**: 刪除已棄用的 768 維相容代碼
3. **測試驗證**: 確保所有向量生成功能正常運作

### 風險評估
- **當前風險**: 🟡 中等（可能導致向量生成失敗）
- **修復後風險**: 🟢 低（完全統一為 1024 維）

---

**📅 更新日期**: 2025-10-22  
**📝 版本**: v1.0  
**✍️ 審計人員**: AI Platform Team  
**🎯 下一步**: 執行建議 1 的修復方案
