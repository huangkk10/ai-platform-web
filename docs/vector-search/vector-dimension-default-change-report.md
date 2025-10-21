# 向量維度預設值修改報告

**修改日期**: 2025-10-22  
**修改人員**: AI Platform Team  
**修改內容**: 將 `get_embedding_service()` 預設模型從 768 維改為 1024 維

---

## ✅ 修改內容

### 修改檔案
**檔案路徑**: `backend/api/services/embedding_service.py`

### 修改前
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
            model_type = 'standard'  # 默認使用 768 維標準模型
```

### 修改後
```python
def __init__(self, model_type: str = 'ultra_high'):
    """
    初始化嵌入服務
    
    Args:
        model_type: 模型類型 (預設: 'ultra_high' - 1024維多語言模型)
                   可選: 'lightweight' (384維), 'standard' (768維), 'high_precision' (768維)
    """
    if model_type not in self.MODEL_CONFIGS:
        # 如果是舊的模型名稱，回退到 ultra_high
        if isinstance(model_type, str) and 'MiniLM' in model_type:
            model_type = 'lightweight'
        else:
            model_type = 'ultra_high'  # 預設使用 1024 維模型（與資料庫一致）
```

---

## 🎯 修改原因

### 問題背景
1. **資料庫向量維度**: 已統一為 1024 維
   - `document_embeddings`: `vector(1024)` ✅
   - `document_section_embeddings`: `vector(1024)` ✅

2. **程式碼預設維度**: 原為 768 維
   - `get_embedding_service()` 預設使用 `'standard'` 模型
   - `'standard'` 模型生成 768 維向量

3. **維度不匹配問題**:
   - 當程式碼調用 `get_embedding_service()` 而未指定模型時
   - 生成 768 維向量
   - 嘗試插入 1024 維資料庫
   - **結果**: PostgreSQL 報錯 `dimension mismatch (expected 1024, got 768)`

### 影響範圍
修改前，以下 12 處程式碼存在潛在問題：
1. `backend/api/management/commands/generate_know_issue_embeddings.py` - 1 處
2. `backend/api/views/viewsets.py` - 1 處
3. `backend/api/views/viewsets/knowledge_viewsets.py` - 4 處
4. `backend/api/views/mixins/vector_management_mixin.py` - 2 處
5. `library/common/knowledge_base/base_vector_service.py` - 3 處
6. `library/protocol_guide/viewset_manager.py` - 1 處

---

## ✅ 測試驗證

### 測試腳本
**位置**: `tests/test_vector_search/test_default_embedding_dimension.py`

### 測試結果

#### 測試 1: 預設模型維度檢查 ✅
```
✅ 模型類型: ultra_high
✅ 模型名稱: intfloat/multilingual-e5-large
✅ 向量維度: 1024
✅ 預設維度正確：1024 維
```

#### 測試 2: 向量生成驗證 ✅
```
測試文本 1: USB Type-C 測試指南
  生成向量維度: 1024 ✅

測試文本 2: Protocol 測試流程
  生成向量維度: 1024 ✅

測試文本 3: RVT Assistant 使用說明
  生成向量維度: 1024 ✅

✅ 所有向量生成測試通過
```

#### 測試 3: 資料庫插入驗證 ✅
```
準備插入測試向量:
  來源表: test_dimension_check
  來源 ID: 99999

✅ 向量插入成功

資料庫驗證:
  來源表: test_dimension_check
  來源 ID: 99999
  向量維度: 1024 ✅
  內容長度: 37

✅ 資料庫中的向量維度正確：1024 維
✅ 測試資料清理成功
```

#### 測試 4: 明確指定模型類型 ✅
```
✅ lightweight     → 384 維（正確）
✅ standard        → 768 維（正確）
✅ high_precision  → 768 維（正確）
✅ ultra_high      → 1024 維（正確）

✅ 所有模型類型驗證通過
```

### 測試總結
```
總計: 4/4 個測試通過

🎉 所有測試通過！預設維度修改成功！
✅ get_embedding_service() 現在預設使用 1024 維向量
✅ 與資料庫維度完全一致
```

---

## 📊 修改效果

### 修改前 ❌
```python
# 調用方式
service = get_embedding_service()

# 結果
- 模型類型: standard
- 向量維度: 768
- 資料庫維度: 1024
- 狀態: ❌ 維度不匹配，插入失敗
```

### 修改後 ✅
```python
# 調用方式（相同）
service = get_embedding_service()

# 結果
- 模型類型: ultra_high
- 向量維度: 1024
- 資料庫維度: 1024
- 狀態: ✅ 維度一致，運作正常
```

---

## 🎯 影響分析

### 正面影響 ✅
1. **解決維度不匹配問題**
   - 所有未指定模型的調用現在都使用 1024 維
   - 與資料庫完全一致
   - 不再發生 `dimension mismatch` 錯誤

2. **提升向量品質**
   - 1024 維向量比 768 維更精確
   - 使用 `intfloat/multilingual-e5-large` 模型（最佳多語言模型）
   - 語義理解能力更強

3. **簡化維護**
   - 無需在每處調用都指定 `'ultra_high'`
   - 預設值與資料庫一致，更直觀
   - 減少未來出錯的可能性

### 向後相容性 ✅
1. **明確指定模型的程式碼不受影響**
   ```python
   # 這些調用不受影響
   service = get_embedding_service('standard')      # 仍為 768 維
   service = get_embedding_service('lightweight')   # 仍為 384 維
   service = get_embedding_service('ultra_high')    # 仍為 1024 維
   ```

2. **已棄用的函數仍可運作**
   ```python
   # 保留的舊版相容函數
   search_rvt_guide_with_vectors_768_legacy()  # 明確使用 'standard'
   ```

### 注意事項 ⚠️
1. **模型載入時間**
   - `intfloat/multilingual-e5-large` 模型較大（約 1.3 GB）
   - 首次載入需要 3-5 秒
   - 建議使用 preload 預載入服務

2. **記憶體使用**
   - 1024 維模型比 768 維模型佔用更多記憶體
   - 增加約 30-40% 記憶體使用
   - 對於記憶體受限的環境，可明確指定 `'standard'`

---

## 🔄 後續建議

### 已完成 ✅
1. ✅ 修改預設模型為 `'ultra_high'` (1024 維)
2. ✅ 創建測試腳本驗證修改
3. ✅ 測試所有功能正常運作

### 建議進行 🔧
1. **清理已棄用代碼**（優先級：中）
   - 刪除 `search_rvt_guide_with_vectors_768_legacy()`
   - 刪除 `_get_rvt_guide_results()`
   - 這些函數已無實際用途

2. **移除 `use_1024_table` 參數**（優先級：低）
   - 資料庫已統一為 1024 維
   - 此參數已無意義
   - 可以簡化 API

3. **更新文檔**（優先級：中）
   - 更新 vector-search-guide.md
   - 說明預設模型已改為 1024 維
   - 提供最佳實踐建議

---

## 📚 相關文檔

### 修改相關
- **審計報告**: `/docs/vector-search/vector-dimension-audit-report.md`
- **測試腳本**: `/tests/test_vector_search/test_default_embedding_dimension.py`
- **修改檔案**: `/backend/api/services/embedding_service.py`

### 向量搜尋相關
- **向量搜尋指南**: `/docs/vector-search/vector-search-guide.md`
- **快速參考**: `/docs/vector-search/vector-search-quick-reference.md`
- **升級摘要**: `/docs/vector-search/vector-upgrade-1024-summary.md`

---

## 🎉 結論

**修改狀態**: ✅ 成功完成

**核心改變**: 
- `get_embedding_service()` 預設模型：`'standard'` (768 維) → `'ultra_high'` (1024 維)

**測試結果**: 
- 4/4 測試通過 ✅
- 向量生成正常 ✅
- 資料庫插入正常 ✅
- 維度完全一致 ✅

**影響評估**:
- ✅ 解決維度不匹配問題
- ✅ 提升向量品質
- ✅ 保持向後相容性
- ✅ 簡化未來維護

**建議後續行動**:
1. 清理已棄用代碼
2. 更新相關文檔
3. 監控生產環境運作

---

**📅 更新日期**: 2025-10-22  
**📝 版本**: v1.0  
**✍️ 修改人員**: AI Platform Team  
**🎯 狀態**: 修改完成，測試通過
