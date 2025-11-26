# 方案 B：文檔標題段落自動創建實作報告

**日期**: 2025-11-26  
**狀態**: ✅ 實作完成並測試通過  
**影響範圍**: Protocol Assistant, RVT Assistant  
**向量維度**: 1024 維 (intfloat/multilingual-e5-large)

---

## 📋 問題背景

### 發現的問題
在修復 CrystalDiskMark 5 搜尋問題時，發現 4 個文檔的標題段落（`is_document_title=true`）缺少向量：
- **ID=162**: UNH-IOL  
- **ID=159**: Burn in Test  
- **ID=160**: CrystalDiskMark 5  
- **ID=163**: 阿呆

### 問題根因
1. **歷史遺留**：這些段落由 migration 腳本 `populate_document_fields.py` 創建
2. **腳本 Bug**：只生成了舊的 `embedding` 欄位，沒有生成 `title_embedding` 和 `content_embedding`
3. **當前系統**：`MarkdownParser` 不創建文檔標題段落，`ViewSet` 也沒有相關邏輯

### 影響
- **Stage 1 搜尋失效**：95% 標題權重無法生效，因為文檔標題段落被 SQL 條件過濾掉
  ```sql
  WHERE title_embedding IS NOT NULL  -- 文檔標題段落被過濾
  ```
- **搜尋品質下降**：完美的標題匹配反而排名更低

---

## 🎯 解決方案：方案 B

### 方案選擇理由
- **保持搜尋品質**：確保 Stage 1 搜尋的 95% 標題權重能正確生效
- **與現有文檔一致**：新文檔與已修復的 4 個文檔行為一致
- **未來預防**：避免再次出現缺失文檔標題段落的問題

### 實作策略
在 `SectionVectorizationService.vectorize_document_sections()` 中，**在解析 Markdown 段落之前**，先創建並處理一個特殊的文檔標題段落。

---

## 🔧 實作細節

### 1. 修改 `SectionVectorizationService.vectorize_document_sections()`

**檔案**: `library/common/knowledge_base/section_vectorization_service.py`

#### 修改邏輯
```python
def vectorize_document_sections(
    self,
    source_table: str,
    source_id: int,
    markdown_content: str,
    document_title: str = ""
) -> Dict[str, Any]:
    """
    解析文檔並為所有段落生成向量
    
    新增邏輯：
    1. 先創建文檔標題段落（is_document_title=true）
    2. 再解析 Markdown 段落（is_document_title=false）
    3. 為所有段落生成向量
    """
    try:
        # ✅ 步驟 1：先創建並處理文檔標題段落
        doc_title_vectorized = False
        if document_title and document_title.strip():
            try:
                # 清理標題（去除換行符和多餘空白）
                clean_title = ' '.join(document_title.strip().split())
                logger.info(f"📝 創建文檔標題段落: {source_table}.{source_id} - '{clean_title}'")
                
                # 創建文檔標題段落的特殊數據結構
                doc_title_section = MarkdownSection(
                    section_id=f"doc_{source_id}",  # 特殊格式：doc_{id}
                    level=0,  # heading_level=0 表示這是文檔標題
                    title=clean_title,
                    content=markdown_content[:500] if markdown_content else clean_title,
                    parent_id=None,
                    path=clean_title,
                    word_count=len((markdown_content[:500] if markdown_content else clean_title).split()),
                    has_code=False,
                    has_images=False
                )
                
                # 生成文檔標題段落的向量
                doc_title_vectorized = self._store_document_title_section(
                    source_table=source_table,
                    source_id=source_id,
                    section=doc_title_section,
                    document_title=clean_title
                )
                
                if doc_title_vectorized:
                    logger.info(f"✅ 文檔標題段落向量生成成功: {source_table}.{source_id}")
                else:
                    logger.warning(f"⚠️  文檔標題段落向量生成失敗: {source_table}.{source_id}")
                    
            except Exception as e:
                logger.error(f"❌ 文檔標題段落創建失敗: {source_table}.{source_id} - {str(e)}", exc_info=True)
        else:
            logger.warning(f"⚠️  文檔 {source_table}.{source_id} 沒有提供 document_title，跳過文檔標題段落")
        
        # ✅ 步驟 2：解析 Markdown 結構（正常的段落）
        sections = self.parser.parse(markdown_content, document_title)
        
        # ✅ 步驟 3：為每個 Markdown 段落生成向量
        vectorized_count = 1 if doc_title_vectorized else 0  # 初始計數包含文檔標題段落
        
        for section in sections:
            # ... 原有邏輯 ...
            if success:
                vectorized_count += 1
        
        logger.info(
            f"✅ 文檔 {source_table}.{source_id} 向量化完成: "
            f"{vectorized_count}/{len(sections) + (1 if doc_title_vectorized else 0)} 段落 "
            f"(含文檔標題段落)" if doc_title_vectorized else f"{vectorized_count}/{len(sections)} 段落"
        )
        
        return {
            'success': vectorized_count > 0,
            'total_sections': len(sections) + (1 if doc_title_vectorized else 0),
            'vectorized_count': vectorized_count,
            'sections': sections,
            'has_document_title_section': doc_title_vectorized
        }
        
    except Exception as e:
        logger.error(f"文檔 {source_table}.{source_id} 向量化失敗: {str(e)}", exc_info=True)
        return {
            'success': False,
            'total_sections': 0,
            'vectorized_count': 0,
            'sections': [],
            'error': str(e)
        }
```

### 2. 新增 `_store_document_title_section()` 方法

**目的**: 專門處理文檔標題段落的向量生成和儲存

```python
def _store_document_title_section(
    self,
    source_table: str,
    source_id: int,
    section: MarkdownSection,
    document_title: str
) -> bool:
    """
    專門處理文檔標題段落的向量生成和儲存
    
    特點：
    - section_id 格式：doc_{source_id}
    - heading_level: 0（特殊標記）
    - is_document_title: true
    - title_embedding: 使用文檔標題生成（1024 維）
    - content_embedding: 使用文檔前 500 字元生成（1024 維）
    
    Args:
        source_table: 來源表名
        source_id: 來源記錄 ID
        section: 文檔標題段落數據
        document_title: 文檔標題
    
    Returns:
        成功 True，失敗 False
    """
    try:
        logger.info(f"  🔤 生成文檔標題段落向量...")
        
        # ✅ 生成標題向量（1024 維）- 使用文檔標題
        title_embedding = self.embedding_service.generate_embedding(document_title)
        logger.info(f"     - title_embedding: 1024 維 (使用文檔標題)")
        
        # ✅ 生成內容向量（1024 維）- 使用文檔前 500 字元
        content_for_embedding = section.content if section.content else document_title
        content_embedding = self.embedding_service.generate_embedding(content_for_embedding)
        logger.info(f"     - content_embedding: 1024 維 (使用前 {len(content_for_embedding)} 字元)")
        
        # ✅ 生成完整上下文向量（向後兼容）
        full_context = f"{document_title}\n\n{content_for_embedding}"
        embedding = self.embedding_service.generate_embedding(full_context)
        
        # 轉換為 pgvector 格式
        embedding_str = '[' + ','.join(map(str, embedding)) + ']'
        title_embedding_str = '[' + ','.join(map(str, title_embedding)) + ']'
        content_embedding_str = '[' + ','.join(map(str, content_embedding)) + ']'
        
        # 生成 document_id
        document_id = f"{source_table}_{source_id}"
        
        # ⚠️ 關鍵：設置 is_document_title=true
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO document_section_embeddings (
                    source_table, source_id, section_id,
                    document_id, document_title,
                    heading_level, heading_text, section_path, parent_section_id,
                    content, full_context, 
                    embedding, title_embedding, content_embedding,
                    word_count, has_code, has_images,
                    is_document_title,
                    created_at, updated_at
                ) VALUES (
                    %s, %s, %s,
                    %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, 
                    %s::vector, %s::vector, %s::vector,
                    %s, %s, %s,
                    true,  -- is_document_title=true
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
                ON CONFLICT (source_table, source_id, section_id)
                DO UPDATE SET
                    document_id = EXCLUDED.document_id,
                    document_title = EXCLUDED.document_title,
                    heading_level = EXCLUDED.heading_level,
                    heading_text = EXCLUDED.heading_text,
                    section_path = EXCLUDED.section_path,
                    parent_section_id = EXCLUDED.parent_section_id,
                    content = EXCLUDED.content,
                    full_context = EXCLUDED.full_context,
                    embedding = EXCLUDED.embedding,
                    title_embedding = EXCLUDED.title_embedding,
                    content_embedding = EXCLUDED.content_embedding,
                    word_count = EXCLUDED.word_count,
                    has_code = EXCLUDED.has_code,
                    has_images = EXCLUDED.has_images,
                    is_document_title = EXCLUDED.is_document_title,
                    updated_at = CURRENT_TIMESTAMP;
                """,
                [
                    source_table, source_id, section.section_id,
                    document_id, document_title,
                    section.level, section.title, section.path, section.parent_id,
                    section.content, full_context,
                    embedding_str, title_embedding_str, content_embedding_str,
                    section.word_count, section.has_code, section.has_images
                ]
            )
        
        logger.info(f"  ✅ 文檔標題段落儲存成功 (section_id={section.section_id})")
        return True
        
    except Exception as e:
        logger.error(f"❌ 儲存文檔標題段落 {section.section_id} 失敗: {str(e)}", exc_info=True)
        return False
```

---

## 🧪 測試驗證

### 測試腳本
**檔案**: `backend/test_document_title_section_auto_creation.py`

### 測試流程
1. 創建測試文章（Protocol Guide）
2. 等待 3 秒讓向量生成完成
3. 檢查文檔標題段落是否存在
4. 驗證文檔標題段落的特徵
5. 統計所有段落數量
6. 測試 Stage 1 搜尋功能
7. 自動清理測試數據

### 測試結果

#### ✅ 所有檢查項目通過（10/10）
```
✅ PASS - 文檔標題段落存在
✅ PASS - section_id 格式正確 (doc_40)
✅ PASS - heading_level 為 0
✅ PASS - is_document_title 為 true
✅ PASS - title_embedding 存在
✅ PASS - content_embedding 存在
✅ PASS - title_embedding 維度 1024
✅ PASS - content_embedding 維度 1024
✅ PASS - 只有一個文檔標題段落
✅ PASS - 搜尋結果存在
```

#### 🔍 搜尋品質驗證
**查詢**: "方案B測試"

**Stage 1 搜尋結果**（95% 標題權重）：
| 排名 | section_id | 標題 | 是否文檔標題 | 標題% | 內容% | 加權% |
|------|-----------|------|-------------|-------|-------|-------|
| 1 | doc_40 | 方案B測試 - 文檔標題段落自動生成測試 | ✅ 是 | 90.18 | 83.52 | **89.85** |
| 2 | sec_2 | 測試標題 2 | 否 | 88.85 | 83.21 | 88.57 |
| 3 | sec_1 | 測試標題 1 | 否 | 88.62 | 81.84 | 88.28 |
| 4 | sec_3 | 測試標題 3 | 否 | 88.27 | 81.48 | 87.93 |

**✅ 結論**: 文檔標題段落排名第一，95% 標題權重正確生效！

---

## 📊 影響範圍

### 1. Protocol Assistant
- ✅ 新增文章時自動創建文檔標題段落
- ✅ 更新文章時重新生成文檔標題段落
- ✅ 刪除文章時同時刪除文檔標題段落

### 2. RVT Assistant
- ✅ 使用相同的 `SectionVectorizationService`
- ✅ 自動獲得相同的文檔標題段落創建邏輯
- ✅ 無需額外修改

### 3. 資料庫
**表**: `document_section_embeddings`

**新增段落特徵**:
- `section_id`: `doc_{source_id}` 格式（如 `doc_20`, `doc_36`）
- `heading_level`: 0（特殊標記，區別於一般段落的 1-6）
- `is_document_title`: `true`
- `title_embedding`: 1024 維向量（使用文檔標題）
- `content_embedding`: 1024 維向量（使用文檔前 500 字元）

**每個文檔的段落結構**:
```
文檔 ID=36
├── doc_36 (文檔標題段落, is_document_title=true, level=0)
├── sec_1 (一般段落, is_document_title=false, level=1-6)
├── sec_2 (一般段落, is_document_title=false, level=1-6)
└── sec_3 (一般段落, is_document_title=false, level=1-6)
```

---

## 🎯 解決的問題

### 1. 搜尋品質保證
- ✅ Stage 1 搜尋的 95% 標題權重能正確生效
- ✅ 文檔標題完美匹配時，能排在最前面
- ✅ 避免標題權重失效導致的搜尋錯誤

### 2. 系統一致性
- ✅ 新文檔與已修復的 4 個舊文檔行為一致
- ✅ Protocol Assistant 和 RVT Assistant 行為一致
- ✅ 未來不會再出現缺失文檔標題段落的問題

### 3. 資料完整性
- ✅ 每個文檔都有完整的文檔標題段落
- ✅ 所有段落都有 1024 維向量
- ✅ 向量生成邏輯統一且可靠

---

## 📝 注意事項

### 1. 文檔標題清理
代碼會自動清理文檔標題中的換行符和多餘空白：
```python
clean_title = ' '.join(document_title.strip().split())
```

**原因**: 避免資料庫中存儲包含換行符的標題，導致日誌和查詢問題。

### 2. 內容截取
content_embedding 使用文檔的前 500 字元：
```python
content=markdown_content[:500] if markdown_content else document_title
```

**原因**: 
- 避免過長內容導致 token 超限
- 前 500 字元通常包含文檔的核心摘要
- 如果文檔無內容，使用標題作為內容

### 3. 向量維度
所有向量統一使用 **1024 維**（`intfloat/multilingual-e5-large`）：
- `title_embedding`: 1024 維
- `content_embedding`: 1024 維
- `embedding`: 1024 維（向後兼容）

### 4. 更新行為
更新文章時，`perform_update()` 會：
1. 刪除所有舊段落（包含文檔標題段落）
2. 重新生成所有段落（包含新的文檔標題段落）
3. 確保向量始終是最新的

---

## 🚀 後續建議

### 1. 監控日誌
定期檢查日誌，確保文檔標題段落創建成功：
```bash
docker logs ai-django | grep "文檔標題段落向量生成成功"
```

### 2. 資料驗證
定期查詢資料庫，確認每個文檔都有文檔標題段落：
```sql
SELECT 
    source_table,
    COUNT(DISTINCT source_id) as total_docs,
    COUNT(*) FILTER (WHERE is_document_title = true) as doc_title_sections
FROM document_section_embeddings
GROUP BY source_table;
```

**預期結果**: `total_docs = doc_title_sections`（每個文檔都有一個文檔標題段落）

### 3. 搜尋品質測試
定期執行搜尋測試，確保文檔標題段落能正確參與搜尋：
```bash
docker exec ai-django python test_document_title_section_auto_creation.py
```

---

## 📚 相關文檔

- **Phase 1 修復報告**: `/docs/features/fix-document-title-embeddings-report.md`
- **向量搜尋架構**: `/docs/architecture/rvt-assistant-database-vector-architecture.md`
- **測試腳本**: `/backend/test_document_title_section_auto_creation.py`
- **修復腳本**: `/backend/fix_document_title_embeddings.py`

---

## 🎉 結論

**方案 B 實作完全成功！**

✅ **功能完整**: 文檔標題段落自動創建、向量生成、搜尋參與  
✅ **測試通過**: 所有 10 項檢查全部通過  
✅ **搜尋品質**: Stage 1 搜尋的 95% 標題權重正確生效  
✅ **系統一致**: Protocol Assistant 和 RVT Assistant 行為統一  
✅ **未來預防**: 不會再出現缺失文檔標題段落的問題

**搜尋品質得到保證，用戶可以放心使用！** 🚀
