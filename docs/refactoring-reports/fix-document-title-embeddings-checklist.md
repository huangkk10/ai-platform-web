# 修復文檔標題段落向量 - 執行檢查清單

## 🎯 目標
確保所有文檔標題段落（`is_document_title=true`）都有向量，並且未來新增/修改文章時自動生成。

---

## ✅ 階段 1：立即修復（補救現有資料）

### 1.1 創建修復腳本
- [ ] 創建 `backend/fix_document_title_embeddings.py`
- [ ] 腳本包含：
  - [ ] `fix_document_title_embeddings()` - 生成缺失的向量
  - [ ] `verify_fix()` - 驗證修復結果
  - [ ] 支援 protocol_guide 和 rvt_guide

### 1.2 執行修復
```bash
docker exec -it ai-django python fix_document_title_embeddings.py
```

**預期輸出**：
```
修復完成: 4 成功, 0 失敗
✅ 所有文檔標題段落都已有向量
```

### 1.3 驗證修復結果
```sql
SELECT 
    id, heading_text,
    title_embedding IS NOT NULL as has_title,
    content_embedding IS NOT NULL as has_content,
    vector_dims(title_embedding) as dims
FROM document_section_embeddings
WHERE source_table = 'protocol_guide'
  AND is_document_title = true;
```

**預期結果**：
- [ ] 4 個段落都有 `has_title = true`
- [ ] 4 個段落都有 `has_content = true`
- [ ] 向量維度都是 `1024`

### 1.4 測試搜尋效果
```bash
cd /app
python tests/test_stage1_sql_direct.py
```

**預期結果**：
- [ ] CrystalDiskMark 5 (ID=160) 出現在 top 10
- [ ] 排名應該在前 3 名
- [ ] 相似度應該 > 0.90

---

## 🛠️ 階段 2：根治問題（修改向量生成邏輯）

### 2.1 定位代碼

**需要檢查的檔案**：
- [ ] `library/common/knowledge_base/section_vector_service.py`
- [ ] `library/protocol_guide/vector_service.py`
- [ ] `library/rvt_guide/vector_service.py`
- [ ] `library/protocol_guide/viewset_manager.py`
- [ ] `library/rvt_guide/viewset_manager.py`

### 2.2 查找問題邏輯

**尋找以下模式**：

```python
# ❌ 模式 1：跳過空內容
if not section.content or section.word_count == 0:
    continue

# ❌ 模式 2：明確跳過文檔標題
if section.is_document_title:
    continue

# ❌ 模式 3：只處理有內容的段落
if section.word_count > 0:
    # 處理
else:
    continue
```

### 2.3 修改向量生成邏輯

**修改位置**：`library/common/knowledge_base/section_vector_service.py`

**核心修改**：
```python
def generate_section_embeddings(self, section):
    # ✅ 特殊處理文檔標題段落
    if section.is_document_title:
        return self._generate_document_title_embeddings(section)
    
    # 一般段落處理
    if not section.content or section.word_count == 0:
        return None
    
    # ... 原有邏輯

def _generate_document_title_embeddings(self, section):
    """為文檔標題段落生成向量"""
    # 標題向量：使用段落標題
    title_embedding = self.generate_embedding(section.heading_text)
    
    # 內容向量：使用文檔前 500 字
    document = self._get_source_document(section)
    content_preview = document.content[:500] if document.content else section.heading_text
    content_embedding = self.generate_embedding(content_preview)
    
    return {
        'title_embedding': title_embedding,
        'content_embedding': content_embedding,
        'word_count': len(content_preview.split())
    }
```

### 2.4 修改 ViewSet Manager

**確保觸發向量生成**：

```python
# library/protocol_guide/viewset_manager.py
# library/rvt_guide/viewset_manager.py

def perform_create(self, serializer):
    instance = serializer.save()
    # ✅ 生成段落向量（包括文檔標題）
    self.generate_section_embeddings_for_document(instance)
    return instance

def perform_update(self, serializer):
    instance = serializer.save()
    # ✅ 重新生成段落向量
    self.regenerate_section_embeddings_for_document(instance)
    return instance
```

### 2.5 添加資料驗證

**在向量生成後檢查**：

```python
def validate_document_section_embeddings(source_table, source_id):
    """驗證文檔標題段落是否有向量"""
    # 檢查 is_document_title=true 的段落
    # 確保都有 title_embedding 和 content_embedding
    # 如果缺失，記錄 WARNING
```

---

## 🧪 階段 3：全面測試

### 3.1 測試新增文章（Protocol Assistant）

**步驟**：
1. [ ] 在 Web UI 新增測試文章
   - 標題: "測試向量自動生成"
   - 內容: "這是一篇測試文章..."

2. [ ] 檢查資料庫
```sql
SELECT 
    dse.id, dse.heading_text, dse.is_document_title,
    dse.title_embedding IS NOT NULL as has_vec,
    vector_dims(dse.title_embedding) as dims
FROM document_section_embeddings dse
WHERE dse.source_table = 'protocol_guide'
  AND dse.source_id = (SELECT id FROM protocol_guide WHERE title = '測試向量自動生成')
  AND dse.is_document_title = true;
```

**預期結果**：
- [ ] 找到 1 個文檔標題段落
- [ ] `is_document_title = true`
- [ ] `has_vec = true`
- [ ] `dims = 1024`

### 3.2 測試新增文章（RVT Assistant）

**重複 3.1 的步驟**：
- [ ] 新增 RVT Guide 測試文章
- [ ] 檢查 `rvt_guide` 表的段落向量
- [ ] 確認文檔標題段落有向量

### 3.3 測試修改文章

**步驟**：
1. [ ] 修改測試文章標題
   - 原標題: "測試向量自動生成"
   - 新標題: "測試向量自動生成【已修改】"

2. [ ] 檢查向量是否更新
```sql
SELECT 
    dse.heading_text,
    dse.updated_at,
    pg.updated_at as doc_updated_at
FROM document_section_embeddings dse
LEFT JOIN protocol_guide pg ON pg.id = dse.source_id
WHERE dse.source_table = 'protocol_guide'
  AND dse.is_document_title = true
  AND pg.title LIKE '測試向量自動生成%';
```

**預期結果**：
- [ ] `heading_text` 已更新為新標題
- [ ] `dse.updated_at >= doc_updated_at` （向量已重新生成）

### 3.4 測試搜尋準確度

**測試 1：CrystalDiskMark 搜尋**
```bash
python tests/test_stage1_sql_direct.py
```

**預期結果**：
- [ ] CrystalDiskMark 5 在 top 3
- [ ] 相似度 > 0.90

**測試 2：其他文檔搜尋**
- [ ] 搜尋 "UNH-IOL" → 應該找到 UNH-IOL 文檔
- [ ] 搜尋 "Burn in Test" → 應該找到 Burn in Test 文檔

---

## 📊 驗證標準

### ✅ 修復成功標準

**資料完整性**：
- [ ] 所有 `is_document_title=true` 的段落都有向量
- [ ] 向量維度都是 1024
- [ ] `word_count > 0` （不再是 0）

**功能正確性**：
- [ ] 新增文章自動生成文檔標題段落向量
- [ ] 修改文章自動更新文檔標題段落向量
- [ ] Protocol Assistant 和 RVT Assistant 都正常運作

**搜尋準確度**：
- [ ] Stage 1 能找到最佳標題匹配
- [ ] CrystalDiskMark 5 搜尋測試通過
- [ ] 其他文檔搜尋測試通過

---

## 🚨 回滾計劃

如果修復出現問題，可以回滾：

### 回滾步驟 1：刪除新生成的向量
```sql
-- 查看修復的向量（檢查 updated_at）
SELECT id, heading_text, updated_at
FROM document_section_embeddings
WHERE source_table = 'protocol_guide'
  AND is_document_title = true
  AND updated_at > '2025-11-26 00:00:00';

-- 如果需要回滾，清除向量
UPDATE document_section_embeddings
SET title_embedding = NULL,
    content_embedding = NULL,
    word_count = 0
WHERE id IN (162, 159, 160, 163);
```

### 回滾步驟 2：還原代碼
```bash
# 如果修改了代碼，使用 git 還原
git checkout library/common/knowledge_base/section_vector_service.py
git checkout library/protocol_guide/viewset_manager.py
git checkout library/rvt_guide/viewset_manager.py
```

---

## 📝 執行記錄

### 階段 1 執行記錄
- [ ] 腳本創建時間: ____________
- [ ] 執行時間: ____________
- [ ] 修復結果: 成功 ____ 個，失敗 ____ 個
- [ ] 驗證結果: □ 通過 □ 失敗
- [ ] 備註: ________________________________

### 階段 2 執行記錄
- [ ] 代碼定位完成: ____________
- [ ] 修改完成時間: ____________
- [ ] 代碼審查: □ 通過 □ 需要修改
- [ ] 備註: ________________________________

### 階段 3 執行記錄
- [ ] 新增文章測試: □ 通過 □ 失敗
- [ ] 修改文章測試: □ 通過 □ 失敗
- [ ] 搜尋準確度測試: □ 通過 □ 失敗
- [ ] 備註: ________________________________

---

## 🎯 最終確認

修復完成後，確認以下所有項目：

### 資料層面
- [ ] `protocol_guide` 的 4 個文檔標題段落都有向量
- [ ] `rvt_guide` 沒有缺失向量的文檔標題段落
- [ ] 所有向量維度都是 1024
- [ ] 所有文檔標題段落的 `word_count > 0`

### 代碼層面
- [ ] 向量生成邏輯包含文檔標題段落處理
- [ ] ViewSet Manager 觸發段落向量生成
- [ ] 添加了資料驗證邏輯
- [ ] 日誌記錄完整

### 測試層面
- [ ] 新增文章測試通過（Protocol + RVT）
- [ ] 修改文章測試通過
- [ ] Stage 1 搜尋準確度測試通過
- [ ] CrystalDiskMark 5 搜尋測試通過

---

**更新日期**：2025-11-26  
**負責人**：________________  
**最後更新**：________________
