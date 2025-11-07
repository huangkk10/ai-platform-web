# 🔧 向量搜尋段落切斷問題分析與解決方案

**分析日期**: 2025-11-08  
**問題類型**: 段落不連續、上下文缺失  
**解決策略**: 不使用 S2 Chunking 的替代方案

---

## 📋 問題描述

### 🎯 核心問題

**「段落被切斷不連續」** 指的是：

當使用基於 Markdown 標題的結構化 Chunking 時，可能出現以下問題：

```markdown
## 測試環境準備

首先，您需要安裝以下工具：
- Visual Studio 2019
- Python 3.8+
- Git

### 硬體需求

記憶體至少 8GB...  ← 這段被切成新段落

### 軟體配置

繼續前面的安裝步驟...  ← 上下文中斷！
```

**問題**：
1. **上下文缺失**：用戶搜尋「軟體配置」時，看不到前面的「測試環境準備」說明
2. **參考資訊不完整**：段落之間的邏輯關係被打斷
3. **閱讀體驗差**：需要手動查找前後文

---

## 🔍 問題根源分析

### 1. **Markdown Parser 的切分邏輯**

```python
# 目前的切分方式
def parse(self, markdown_content: str):
    # 找到所有標題
    headings = find_all_headings(markdown_content)
    
    for idx, heading in enumerate(headings):
        start_line = heading['line_num']
        end_line = headings[idx + 1]['line_num']  # 下一個標題的位置
        
        # 提取段落內容（只包含本段落）
        section_content = lines[start_line + 1:end_line]
        # ❌ 問題：不包含父段落或子段落的內容
```

### 2. **向量搜尋只返回匹配段落**

```python
# 目前的搜尋邏輯
results = search_sections(query="軟體配置", limit=3)
# 返回：
# [
#   {section_id: "sec_5", title: "軟體配置", content: "繼續前面..."},
#   # ❌ 缺少前面的「測試環境準備」上下文
# ]
```

### 3. **結果格式化時的資訊損失**

```python
# 目前只顯示匹配段落的內容
def _format_section_results_to_standard(section_results):
    for section in section_results:
        content = section['content']  # ❌ 只有本段落
        # 缺少父段落、子段落、兄弟段落
```

---

## 💡 解決方案（不使用 S2 Chunking）

### 🌟 方案 1：**上下文視窗擴展** ⭐⭐⭐⭐⭐ (推薦)

**原理**：在返回搜尋結果時，自動附加前後段落的內容。

#### 實現方式

```python
class SectionSearchService:
    """段落搜尋服務（增強版）"""
    
    def search_sections_with_expanded_context(
        self,
        query: str,
        source_table: str,
        limit: int = 5,
        threshold: float = 0.7,
        context_window: int = 1  # ✨ 新增：上下文視窗大小
    ):
        """
        搜尋段落並自動擴展上下文
        
        Args:
            context_window: 
                - 0: 只返回匹配段落
                - 1: 附加前 1 段 + 後 1 段
                - 2: 附加前 2 段 + 後 2 段
        """
        
        # 1. 執行基礎向量搜尋
        base_results = self.search_sections(query, source_table, limit, threshold)
        
        # 2. 為每個結果擴展上下文
        expanded_results = []
        for result in base_results:
            expanded = self._expand_context(
                result, 
                source_table, 
                context_window
            )
            expanded_results.append(expanded)
        
        return expanded_results
    
    def _expand_context(self, section, source_table, window_size):
        """
        擴展段落上下文
        
        返回格式：
        {
            'matched_section': {...},      # 匹配的段落
            'context_before': [...],       # 前面的段落
            'context_after': [...],        # 後面的段落
            'combined_content': "...",     # 合併後的完整內容
        }
        """
        
        # 獲取前後段落
        before_sections = self._get_adjacent_sections(
            source_table,
            section['source_id'],
            section['section_id'],
            direction='before',
            count=window_size
        )
        
        after_sections = self._get_adjacent_sections(
            source_table,
            section['source_id'],
            section['section_id'],
            direction='after',
            count=window_size
        )
        
        # 組合內容
        combined_parts = []
        
        # 前文
        for prev_section in before_sections:
            combined_parts.append(
                f"[上文] {prev_section['heading_text']}\n"
                f"{prev_section['content']}"
            )
        
        # 主要匹配段落（高亮）
        combined_parts.append(
            f"✨ [匹配段落] {section['heading_text']}\n"
            f"{section['content']}"
        )
        
        # 後文
        for next_section in after_sections:
            combined_parts.append(
                f"[下文] {next_section['heading_text']}\n"
                f"{next_section['content']}"
            )
        
        return {
            'matched_section': section,
            'context_before': before_sections,
            'context_after': after_sections,
            'combined_content': "\n\n".join(combined_parts),
            'similarity': section['similarity']  # 保留原始相似度
        }
```

#### 資料庫查詢實現

```python
def _get_adjacent_sections(self, source_table, source_id, section_id, direction, count):
    """
    獲取相鄰段落
    
    使用策略：
    1. 根據 section_id（如 "sec_3"）的順序編號來判斷前後
    2. 同時考慮文檔結構（同一 source_id）
    """
    
    # 解析當前段落的編號
    current_num = int(section_id.split('_')[1])
    
    with connection.cursor() as cursor:
        if direction == 'before':
            # 獲取前面的段落（編號更小）
            cursor.execute("""
                SELECT section_id, heading_level, heading_text, content, section_path
                FROM document_section_embeddings
                WHERE source_table = %s 
                  AND source_id = %s
                  AND CAST(SUBSTRING(section_id FROM 5) AS INTEGER) < %s
                ORDER BY CAST(SUBSTRING(section_id FROM 5) AS INTEGER) DESC
                LIMIT %s
            """, [source_table, source_id, current_num, count])
            
            results = cursor.fetchall()
            # 反轉順序（從舊到新）
            return list(reversed([self._row_to_dict(row) for row in results]))
        
        else:  # after
            # 獲取後面的段落（編號更大）
            cursor.execute("""
                SELECT section_id, heading_level, heading_text, content, section_path
                FROM document_section_embeddings
                WHERE source_table = %s 
                  AND source_id = %s
                  AND CAST(SUBSTRING(section_id FROM 5) AS INTEGER) > %s
                ORDER BY CAST(SUBSTRING(section_id FROM 5) AS INTEGER) ASC
                LIMIT %s
            """, [source_table, source_id, current_num, count])
            
            return [self._row_to_dict(row) for row in cursor.fetchall()]
```

#### 優點

✅ **無需重新向量化**：使用現有的段落向量  
✅ **靈活可控**：可調整 context_window 大小  
✅ **效能好**：只需額外查詢前後段落（簡單的資料庫查詢）  
✅ **用戶體驗佳**：自動提供完整上下文  

#### 使用範例

```python
# API 請求
POST /api/protocol-guides/search_sections/
{
    "query": "軟體配置",
    "limit": 3,
    "context_window": 1  # ✨ 新參數
}

# 回應
{
    "results": [
        {
            "matched_section": {
                "title": "軟體配置",
                "content": "繼續前面的安裝步驟...",
                "similarity": 0.92
            },
            "context_before": [
                {
                    "title": "測試環境準備",
                    "content": "首先，您需要安裝以下工具..."
                }
            ],
            "context_after": [
                {
                    "title": "環境變數設定",
                    "content": "接下來配置環境變數..."
                }
            ],
            "combined_content": "[上文] 測試環境準備\n首先...\n\n✨ [匹配段落] 軟體配置\n繼續...\n\n[下文] 環境變數設定\n接下來..."
        }
    ]
}
```

---

### 🌟 方案 2：**階層式內容組合** ⭐⭐⭐⭐

**原理**：在向量生成時，就將父段落的摘要資訊加入子段落中。

#### 實現方式

```python
class EnhancedMarkdownParser(MarkdownStructureParser):
    """增強的 Markdown 解析器（包含層級上下文）"""
    
    def parse_with_hierarchical_context(self, markdown_content, document_title):
        """
        解析時自動附加父段落資訊
        """
        
        # 1. 基礎解析
        sections = super().parse(markdown_content, document_title)
        
        # 2. 為每個段落添加階層上下文
        for section in sections:
            section.enriched_content = self._build_enriched_content(
                section, 
                sections
            )
        
        return sections
    
    def _build_enriched_content(self, section, all_sections):
        """
        構建包含層級資訊的增強內容
        
        格式：
        [文檔標題] > [父段落] > [當前段落]
        
        父段落摘要：...
        ---
        當前段落內容：...
        """
        
        content_parts = []
        
        # 1. 添加完整路徑
        content_parts.append(f"路徑: {section.path}")
        
        # 2. 添加父段落摘要（如果有）
        if section.parent_id:
            parent = self._find_section_by_id(all_sections, section.parent_id)
            if parent:
                # 取父段落的前 200 字作為摘要
                parent_summary = parent.content[:200] + "..." if len(parent.content) > 200 else parent.content
                content_parts.append(
                    f"\n上層段落 [{parent.title}] 摘要:\n{parent_summary}\n"
                    f"--- [當前段落開始] ---"
                )
        
        # 3. 添加當前段落完整內容
        content_parts.append(section.content)
        
        return "\n\n".join(content_parts)
```

#### 向量生成時使用增強內容

```python
class ProtocolGuideVectorService(BaseKnowledgeBaseVectorService):
    
    def _get_content_for_vectorization(self, instance):
        """使用增強內容進行向量化"""
        
        # 解析 Markdown（包含層級上下文）
        parser = EnhancedMarkdownParser()
        sections = parser.parse_with_hierarchical_context(
            instance.content,
            instance.title
        )
        
        # 返回增強後的內容
        for section in sections:
            # ✨ 使用 enriched_content 而非原始 content
            yield section.section_id, section.enriched_content
```

#### 優點

✅ **向量包含上下文**：搜尋時自動考慮父段落資訊  
✅ **語義更準確**：AI 能理解段落在文檔中的位置  
✅ **無需額外查詢**：上下文已嵌入向量中  

#### 缺點

❌ **向量較大**：每個段落包含父段落摘要  
❌ **重複資訊**：父段落內容在多個子段落中重複  
❌ **重新向量化**：需要重新生成所有向量  

---

### 🌟 方案 3：**智能段落合併** ⭐⭐⭐

**原理**：在搜尋結果格式化時，自動合併屬於同一主題的相鄰段落。

#### 實現方式

```python
def _format_section_results_with_smart_merge(self, section_results, limit=5):
    """
    智能合併段落結果
    
    合併策略：
    1. 如果多個結果屬於同一文檔的連續段落，合併它們
    2. 如果結果的相似度都很高（> 0.8），可能是同一主題的不同部分
    3. 合併時保留最高相似度
    """
    
    # 1. 按文檔 ID 和段落順序分組
    grouped = {}
    for section in section_results:
        doc_id = section['source_id']
        section_num = int(section['section_id'].split('_')[1])
        
        if doc_id not in grouped:
            grouped[doc_id] = []
        
        grouped[doc_id].append({
            'section': section,
            'section_num': section_num
        })
    
    # 2. 對每個文檔的段落進行分析和合併
    merged_results = []
    
    for doc_id, sections in grouped.items():
        # 按段落編號排序
        sections.sort(key=lambda x: x['section_num'])
        
        # 檢查是否為連續段落
        groups = self._group_consecutive_sections(sections)
        
        for group in groups:
            # 合併連續的段落
            merged = self._merge_section_group(group)
            merged_results.append(merged)
    
    return merged_results[:limit]

def _group_consecutive_sections(self, sections):
    """
    將連續的段落分組
    
    例如：sec_2, sec_3, sec_4 → [sec_2, sec_3, sec_4]
         sec_2, sec_5, sec_6 → [sec_2], [sec_5, sec_6]
    """
    groups = []
    current_group = []
    
    for i, item in enumerate(sections):
        if not current_group:
            current_group.append(item)
        else:
            # 檢查是否連續（編號差 1）
            prev_num = current_group[-1]['section_num']
            curr_num = item['section_num']
            
            if curr_num - prev_num == 1:
                # 連續，加入當前組
                current_group.append(item)
            else:
                # 不連續，開始新組
                groups.append(current_group)
                current_group = [item]
    
    if current_group:
        groups.append(current_group)
    
    return groups

def _merge_section_group(self, group):
    """
    合併一組段落
    """
    if len(group) == 1:
        return group[0]['section']
    
    # 取最高相似度
    max_similarity = max(s['section']['similarity'] for s in group)
    
    # 合併內容
    merged_content_parts = []
    for item in group:
        section = item['section']
        merged_content_parts.append(
            f"## {section['heading_text']}\n{section['content']}"
        )
    
    # 使用第一個段落的資訊作為基礎
    base_section = group[0]['section']
    
    return {
        'section_id': f"{group[0]['section']['section_id']}_to_{group[-1]['section']['section_id']}",
        'source_id': base_section['source_id'],
        'heading_text': f"{base_section['heading_text']} (包含 {len(group)} 個相關段落)",
        'content': "\n\n".join(merged_content_parts),
        'similarity': max_similarity,
        'merged_sections_count': len(group)
    }
```

#### 優點

✅ **自動化**：無需手動配置  
✅ **保留結構**：合併後仍保留各段落標題  
✅ **效能好**：只在結果格式化時處理  

#### 缺點

❌ **邏輯複雜**：需要正確判斷哪些段落應該合併  
❌ **可能合併錯誤**：相鄰但不相關的段落可能被誤合併  

---

### 🌟 方案 4：**父子段落自動附加** ⭐⭐⭐⭐

**原理**：在返回段落時，自動附加其父段落和直接子段落。

#### 實現方式

```python
def search_sections_with_family(self, query, source_table, limit=5, threshold=0.7):
    """
    搜尋段落並附加「家族」資訊
    
    家族包括：
    - 父段落（提供上層背景）
    - 當前段落（匹配結果）
    - 所有子段落（提供詳細內容）
    """
    
    # 1. 基礎搜尋
    base_results = self.search_sections(query, source_table, limit, threshold)
    
    # 2. 為每個結果附加家族
    enriched_results = []
    
    for result in base_results:
        family = {
            'matched_section': result,
            'parent': None,
            'children': [],
            'combined_content': ''
        }
        
        # 獲取父段落
        if result.get('parent_section_id'):
            family['parent'] = self._get_section_by_id(
                source_table,
                result['source_id'],
                result['parent_section_id']
            )
        
        # 獲取所有子段落
        family['children'] = self._get_children_sections(
            source_table,
            result['source_id'],
            result['section_id']
        )
        
        # 組合內容
        content_parts = []
        
        # 父段落（作為背景）
        if family['parent']:
            content_parts.append(
                f"📚 背景 - {family['parent']['heading_text']}\n"
                f"{family['parent']['content'][:300]}...\n"
            )
        
        # 當前段落（主要內容）
        content_parts.append(
            f"🎯 {result['heading_text']}\n"
            f"{result['content']}\n"
        )
        
        # 子段落（詳細內容）
        if family['children']:
            content_parts.append("📖 詳細說明：\n")
            for child in family['children']:
                content_parts.append(
                    f"  • {child['heading_text']}\n"
                    f"    {child['content'][:200]}...\n"
                )
        
        family['combined_content'] = "\n".join(content_parts)
        enriched_results.append(family)
    
    return enriched_results
```

#### 優點

✅ **結構清晰**：父子關係明確  
✅ **上下文完整**：包含完整的主題樹  
✅ **查詢效能好**：利用資料庫的 parent_section_id 索引  

---

## 📊 方案對比與推薦

| 方案 | 實現難度 | 效能 | 上下文完整性 | 用戶體驗 | 推薦度 |
|-----|---------|------|------------|---------|--------|
| **方案 1: 上下文視窗** | 簡單 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 方案 2: 階層式內容 | 中等 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| 方案 3: 智能合併 | 複雜 | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| 方案 4: 父子附加 | 簡單 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

---

## 🎯 最終推薦策略

### 🥇 **最佳方案：方案 1（上下文視窗擴展） + 方案 4（父子段落附加）**

**組合策略**：

```python
def ultimate_search_with_full_context(
    self, 
    query, 
    source_table, 
    limit=5, 
    threshold=0.7,
    context_mode='auto'  # 'auto', 'window', 'family', 'both'
):
    """
    終極搜尋方案：自適應上下文策略
    
    Args:
        context_mode:
            - 'auto': 自動判斷（推薦）
            - 'window': 只使用視窗擴展（簡單查詢）
            - 'family': 只使用父子結構（結構化查詢）
            - 'both': 兩者都用（完整上下文）
    """
    
    # 1. 基礎搜尋
    results = self.search_sections(query, source_table, limit, threshold)
    
    # 2. 根據模式選擇策略
    if context_mode == 'auto':
        # 自動判斷：如果找到的段落層級深（level > 2），使用 family
        # 否則使用 window
        avg_level = sum(r['heading_level'] for r in results) / len(results)
        use_family = avg_level > 2
    else:
        use_family = context_mode in ['family', 'both']
    
    # 3. 應用上下文擴展
    if use_family:
        # 使用父子結構
        enriched = self._add_family_context(results, source_table)
    else:
        # 使用視窗擴展
        enriched = self._add_window_context(results, source_table, window=1)
    
    # 4. 如果是 'both' 模式，再加上視窗
    if context_mode == 'both' and use_family:
        enriched = self._add_window_context(enriched, source_table, window=1)
    
    return enriched
```

### 實施步驟

#### Phase 1: 基礎實現（1-2 天）

1. **實現 `_get_adjacent_sections()` 方法**
   - 支援獲取前/後 N 個段落
   - 優化 SQL 查詢效能

2. **實現 `search_sections_with_expanded_context()` 方法**
   - 支援 `context_window` 參數
   - 返回擴展後的結果

3. **更新 API 端點**
   - 在 `search_sections` API 中添加 `context_window` 參數
   - 更新回應格式

#### Phase 2: 父子結構支援（2-3 天）

4. **實現 `_get_family_context()` 方法**
   - 獲取父段落
   - 獲取所有子段落
   - 組合成結構化結果

5. **實現自動模式判斷**
   - 根據段落層級自動選擇策略
   - 提供手動覆寫選項

#### Phase 3: 優化與測試（2-3 天）

6. **效能優化**
   - 批量查詢優化
   - 添加快取機制

7. **完整測試**
   - 測試不同 `context_window` 值
   - 測試父子結構準確性
   - 對比新舊系統效果

---

## 📈 預期效果

### Before（目前系統）

```
查詢：軟體配置

結果 1:
  標題：軟體配置
  內容：繼續前面的安裝步驟，打開配置文件...
  相似度：92%
  
  ❌ 問題：不知道「前面」指的是什麼
```

### After（應用方案 1）

```
查詢：軟體配置

結果 1:
  [上文] 測試環境準備
  首先，您需要安裝以下工具：
  - Visual Studio 2019
  - Python 3.8+
  - Git
  
  ✨ [匹配段落] 軟體配置
  繼續前面的安裝步驟，打開配置文件...
  
  [下文] 環境變數設定
  接下來配置 PATH 環境變數...
  
  相似度：92%
  
  ✅ 解決：完整的上下文，用戶能理解全貌
```

---

## 🔧 實施優先級

### 🚀 立即實施（Week 1）

1. **方案 1: 上下文視窗擴展**
   - 實現 `_get_adjacent_sections()`
   - 添加 `context_window` 參數到 API
   - 預設 `context_window=1`

### 📅 短期優化（Week 2-3）

2. **方案 4: 父子段落附加**
   - 實現 `_get_family_context()`
   - 添加 `context_mode` 參數

### 🔮 長期改進（Month 2+）

3. **智能策略**
   - 自動判斷最佳 context_mode
   - 根據查詢類型調整策略
   - 機器學習優化

---

## ✅ 總結

**不使用 S2 Chunking 的最佳解決方案：**

1. ✅ **上下文視窗擴展**（最實用、最易實現）
2. ✅ **父子段落自動附加**（結構化、語義完整）
3. ✅ **組合使用**（最佳用戶體驗）

**核心優勢：**
- 🎯 保留 Markdown 結構化優勢
- 🚀 無需重新向量化
- 💡 靈活可控的上下文策略
- ⚡ 查詢效能優異

**實施建議：**
- 從方案 1 開始（1-2 天即可完成）
- 根據用戶反饋逐步優化
- 保持系統簡單可維護

---

**📅 更新日期**: 2025-11-08  
**✍️ 分析者**: AI Platform Team  
**🎯 狀態**: 待實施（建議優先實施方案 1）
