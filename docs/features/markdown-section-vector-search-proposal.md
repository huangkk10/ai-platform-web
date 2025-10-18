# 🔍 Markdown 結構化分段向量搜尋增強方案

## 📋 執行概要

**提案日期**: 2025-10-19  
**當前系統**: 1024維向量搜尋 (整篇文檔向量化)  
**提案目標**: 利用 Markdown 標題結構進行智能分段，提升搜尋精準度和細緻度  
**預期效果**: 精準度 +20-30%，細緻度 +40-60%

---

## 🎯 問題分析

### 當前方案的限制

#### 1. **整篇文檔向量化**
```python
# 當前做法
content = f"Title: {guide.title} | Content: {guide.content}"
embedding = generate_embedding(content)  # 整篇 2000+ 字元
```

**問題**：
- ❌ **語義稀釋**：長文檔的向量無法精確表達每個段落的主題
- ❌ **相關度降低**：用戶查詢 "如何安裝" 時，匹配到包含 100 個主題的文檔
- ❌ **召回不精準**：無法定位到文檔中的具體章節

#### 2. **實際案例**

從資料庫看到的內容：
```markdown
# ULINK Protocol 測試基礎指南

## 概述
本指南介紹 ULINK Protocol 測試的基本流程和注意事項。

## 測試環境準備
1. **硬體設備**：
   - ULINK 調試器
   - 目標開發板

## 連接步驟
1. 連接 ULINK 到電腦
2. 連接目標板...

## 常見問題
### 連接失敗
原因分析...

### 速度慢
優化方法...
```

**當前搜尋行為**：
```
查詢: "連接失敗怎麼辦"
結果: 返回整篇文檔 (600+ 字)
問題: 用戶需要手動找到 "常見問題 → 連接失敗" 段落
```

**理想搜尋行為**：
```
查詢: "連接失敗怎麼辦"
結果: 直接返回 "常見問題 → 連接失敗" 段落 (50 字)
優勢: 精準定位，直接解答
```

---

## 💡 解決方案：Markdown 結構化分段向量搜尋

### 核心概念

#### 1. **Markdown 層級解析**
將單一文檔拆解為多個**有層級關係的段落**，每個段落單獨向量化。

```python
# 原始文檔
document = """
# ULINK Protocol 測試基礎指南

## 概述
本指南介紹 ULINK Protocol 測試的基本流程...

## 測試環境準備
1. 硬體設備...

### 硬體設備清單
- ULINK 調試器...

## 連接步驟
1. 連接 ULINK 到電腦...

## 常見問題
### 連接失敗
原因：...

### 速度慢
優化：...
"""

# 解析後
sections = [
    {
        'level': 1,
        'title': 'ULINK Protocol 測試基礎指南',
        'path': 'ULINK Protocol 測試基礎指南',
        'content': '(文檔摘要)',
        'children': [2, 3, 4, 5]  # 子段落 IDs
    },
    {
        'level': 2,
        'title': '概述',
        'path': 'ULINK Protocol 測試基礎指南 > 概述',
        'content': '本指南介紹 ULINK Protocol 測試的基本流程...',
        'parent_id': 1
    },
    {
        'level': 2,
        'title': '測試環境準備',
        'path': 'ULINK Protocol 測試基礎指南 > 測試環境準備',
        'content': '1. 硬體設備...',
        'children': [6]
    },
    {
        'level': 3,
        'title': '硬體設備清單',
        'path': 'ULINK Protocol 測試基礎指南 > 測試環境準備 > 硬體設備清單',
        'content': '- ULINK 調試器...',
        'parent_id': 3
    },
    # ...
    {
        'level': 3,
        'title': '連接失敗',
        'path': 'ULINK Protocol 測試基礎指南 > 常見問題 > 連接失敗',
        'content': '原因：USB 連接不穩定...',
        'parent_id': 5
    }
]
```

#### 2. **段落向量表**
```sql
CREATE TABLE document_section_embeddings (
    id SERIAL PRIMARY KEY,
    source_table VARCHAR(100),      -- 'protocol_guide', 'rvt_guide'
    source_id INTEGER,              -- Guide ID
    section_id VARCHAR(50),         -- 段落唯一 ID (如 'sec_1', 'sec_1_2')
    
    -- 段落結構
    heading_level INTEGER,          -- 標題層級 (1-6)
    heading_text VARCHAR(500),      -- 標題文字
    section_path TEXT,              -- 完整路徑 (如 'Guide > 章節 > 小節')
    parent_section_id VARCHAR(50),  -- 父段落 ID
    
    -- 內容
    content TEXT,                   -- 段落內容（不含子段落）
    full_context TEXT,              -- 完整上下文（含父段落標題）
    
    -- 向量
    embedding vector(1024),         -- 1024 維向量
    
    -- 元數據
    word_count INTEGER,             -- 字數統計
    has_code BOOLEAN,               -- 是否包含代碼塊
    has_images BOOLEAN,             -- 是否包含圖片
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(source_table, source_id, section_id)
);

-- 索引
CREATE INDEX idx_section_embeddings_source 
    ON document_section_embeddings(source_table, source_id);

CREATE INDEX idx_section_embeddings_vector 
    ON document_section_embeddings 
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX idx_section_embeddings_level 
    ON document_section_embeddings(heading_level);
```

---

## 🏗️ 技術實現架構

### 階段 1: Markdown 解析器

```python
# library/common/knowledge_base/markdown_parser.py

import re
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class MarkdownSection:
    """Markdown 段落數據結構"""
    section_id: str              # 唯一 ID
    level: int                   # 標題層級 (1-6)
    title: str                   # 標題文字
    content: str                 # 段落內容
    path: str                    # 完整路徑
    parent_id: Optional[str]     # 父段落 ID
    children_ids: List[str]      # 子段落 IDs
    start_line: int              # 起始行號
    end_line: int                # 結束行號
    
    # 元數據
    has_code: bool = False
    has_images: bool = False
    word_count: int = 0


class MarkdownStructureParser:
    """Markdown 結構解析器"""
    
    def __init__(self):
        # 匹配標題：# Title, ## Title, ### Title
        self.heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
        
        # 匹配代碼塊
        self.code_block_pattern = re.compile(r'```[\s\S]*?```')
        
        # 匹配圖片
        self.image_pattern = re.compile(r'!\[.*?\]\(.*?\)')
    
    def parse(self, markdown_content: str, document_title: str = "") -> List[MarkdownSection]:
        """
        解析 Markdown 文檔為結構化段落列表
        
        Args:
            markdown_content: Markdown 文本
            document_title: 文檔標題（可選）
        
        Returns:
            段落列表（按出現順序）
        """
        sections = []
        lines = markdown_content.split('\n')
        
        # 查找所有標題位置
        headings = []
        for i, line in enumerate(lines):
            match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()
                headings.append({
                    'line_num': i,
                    'level': level,
                    'title': title
                })
        
        # 如果沒有標題，整篇作為單一段落
        if not headings:
            return [self._create_single_section(markdown_content, document_title)]
        
        # 建立段落結構
        for idx, heading in enumerate(headings):
            # 計算段落內容範圍
            start_line = heading['line_num']
            end_line = headings[idx + 1]['line_num'] if idx + 1 < len(headings) else len(lines)
            
            # 提取段落內容（排除標題行）
            section_content = '\n'.join(lines[start_line + 1:end_line]).strip()
            
            # 生成段落 ID
            section_id = f"sec_{idx + 1}"
            
            # 查找父段落
            parent_id = self._find_parent_section(headings, idx)
            
            # 建立完整路徑
            path = self._build_section_path(headings, idx, document_title)
            
            # 檢測元數據
            has_code = bool(self.code_block_pattern.search(section_content))
            has_images = bool(self.image_pattern.search(section_content))
            word_count = len(section_content)
            
            section = MarkdownSection(
                section_id=section_id,
                level=heading['level'],
                title=heading['title'],
                content=section_content,
                path=path,
                parent_id=parent_id,
                children_ids=[],
                start_line=start_line,
                end_line=end_line,
                has_code=has_code,
                has_images=has_images,
                word_count=word_count
            )
            
            sections.append(section)
        
        # 建立父子關係
        self._link_parent_children(sections)
        
        return sections
    
    def _find_parent_section(self, headings: List[Dict], current_idx: int) -> Optional[str]:
        """查找父段落 ID"""
        current_level = headings[current_idx]['level']
        
        # 向前查找第一個層級更高的標題
        for i in range(current_idx - 1, -1, -1):
            if headings[i]['level'] < current_level:
                return f"sec_{i + 1}"
        
        return None
    
    def _build_section_path(self, headings: List[Dict], current_idx: int, document_title: str) -> str:
        """建立段落完整路徑"""
        path_parts = []
        
        if document_title:
            path_parts.append(document_title)
        
        current_level = headings[current_idx]['level']
        
        # 收集所有祖先標題
        for i in range(current_idx + 1):
            if i == current_idx or headings[i]['level'] < current_level:
                path_parts.append(headings[i]['title'])
        
        return ' > '.join(path_parts)
    
    def _link_parent_children(self, sections: List[MarkdownSection]):
        """建立父子段落關聯"""
        section_dict = {s.section_id: s for s in sections}
        
        for section in sections:
            if section.parent_id and section.parent_id in section_dict:
                parent = section_dict[section.parent_id]
                parent.children_ids.append(section.section_id)
    
    def _create_single_section(self, content: str, title: str) -> MarkdownSection:
        """創建單一段落（無標題情況）"""
        return MarkdownSection(
            section_id="sec_1",
            level=1,
            title=title or "文檔內容",
            content=content,
            path=title or "文檔內容",
            parent_id=None,
            children_ids=[],
            start_line=0,
            end_line=len(content.split('\n')),
            word_count=len(content)
        )
```

### 階段 2: 段落向量化服務

```python
# library/common/knowledge_base/section_vectorization_service.py

class SectionVectorizationService:
    """段落向量化服務"""
    
    def __init__(self):
        self.parser = MarkdownStructureParser()
        self.embedding_service = get_embedding_service('ultra_high')
    
    def vectorize_document_sections(
        self,
        source_table: str,
        source_id: int,
        markdown_content: str,
        document_title: str
    ) -> int:
        """
        將文檔解析並向量化所有段落
        
        Returns:
            成功向量化的段落數量
        """
        # 1. 解析 Markdown 結構
        sections = self.parser.parse(markdown_content, document_title)
        
        logger.info(f"解析文檔 {source_table}:{source_id}，共 {len(sections)} 個段落")
        
        # 2. 為每個段落生成向量
        success_count = 0
        
        for section in sections:
            try:
                # 構建完整上下文（包含路徑資訊）
                full_context = f"{section.path}\n\n{section.content}"
                
                # 生成向量
                embedding = self.embedding_service.generate_embedding(full_context)
                
                # 存入資料庫
                self._store_section_embedding(
                    source_table=source_table,
                    source_id=source_id,
                    section=section,
                    embedding=embedding
                )
                
                success_count += 1
                
            except Exception as e:
                logger.error(f"段落向量化失敗: {section.section_id}, {str(e)}")
        
        logger.info(f"向量化完成: {success_count}/{len(sections)} 個段落成功")
        
        return success_count
    
    def _store_section_embedding(
        self,
        source_table: str,
        source_id: int,
        section: MarkdownSection,
        embedding: List[float]
    ):
        """存儲段落向量到資料庫"""
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO document_section_embeddings (
                    source_table, source_id, section_id,
                    heading_level, heading_text, section_path, parent_section_id,
                    content, full_context, embedding,
                    word_count, has_code, has_images
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (source_table, source_id, section_id)
                DO UPDATE SET
                    heading_text = EXCLUDED.heading_text,
                    section_path = EXCLUDED.section_path,
                    content = EXCLUDED.content,
                    full_context = EXCLUDED.full_context,
                    embedding = EXCLUDED.embedding,
                    word_count = EXCLUDED.word_count,
                    has_code = EXCLUDED.has_code,
                    has_images = EXCLUDED.has_images,
                    updated_at = CURRENT_TIMESTAMP
            """, [
                source_table, source_id, section.section_id,
                section.level, section.title, section.path, section.parent_id,
                section.content, f"{section.path}\n\n{section.content}",
                json.dumps(embedding),
                section.word_count, section.has_code, section.has_images
            ])
```

### 階段 3: 段落搜尋服務

```python
# library/common/knowledge_base/section_search_service.py

class SectionSearchService:
    """段落級別搜尋服務"""
    
    def __init__(self):
        self.embedding_service = get_embedding_service('ultra_high')
    
    def search_sections(
        self,
        query: str,
        source_table: str = None,
        min_level: int = 1,
        max_level: int = 6,
        limit: int = 5,
        threshold: float = 0.7
    ) -> List[Dict]:
        """
        搜尋段落
        
        Args:
            query: 查詢文本
            source_table: 限制來源表（可選）
            min_level: 最小標題層級（1=頂層）
            max_level: 最大標題層級（6=最細）
            limit: 返回結果數量
            threshold: 相似度閾值
        
        Returns:
            段落搜尋結果列表
        """
        # 1. 生成查詢向量
        query_embedding = self.embedding_service.generate_embedding(query)
        
        # 2. 構建 SQL 查詢
        sql_parts = ["WHERE 1=1"]
        params = [json.dumps(query_embedding)]
        
        if source_table:
            sql_parts.append("AND source_table = %s")
            params.append(source_table)
        
        sql_parts.append("AND heading_level BETWEEN %s AND %s")
        params.extend([min_level, max_level])
        
        sql = f"""
            SELECT 
                source_table,
                source_id,
                section_id,
                heading_level,
                heading_text,
                section_path,
                content,
                parent_section_id,
                word_count,
                has_code,
                has_images,
                1 - (embedding <=> %s) as similarity_score
            FROM document_section_embeddings
            {' '.join(sql_parts)}
            ORDER BY embedding <=> %s
            LIMIT %s
        """
        
        params.extend([json.dumps(query_embedding), limit])
        
        # 3. 執行查詢
        results = []
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            
            columns = [desc[0] for desc in cursor.description]
            
            for row in cursor.fetchall():
                data = dict(zip(columns, row))
                
                # 過濾低於閾值的結果
                if data['similarity_score'] >= threshold:
                    results.append(data)
        
        logger.info(f"段落搜尋完成，返回 {len(results)} 個結果")
        
        return results
    
    def search_with_context(
        self,
        query: str,
        source_table: str = None,
        limit: int = 5,
        include_siblings: bool = True
    ) -> List[Dict]:
        """
        搜尋段落並包含上下文
        
        Args:
            include_siblings: 是否包含兄弟段落（同層級）
        """
        # 1. 基礎段落搜尋
        base_results = self.search_sections(query, source_table, limit=limit)
        
        # 2. 為每個結果添加上下文
        enriched_results = []
        
        for result in base_results:
            # 獲取父段落
            parent = self._get_parent_section(
                result['source_table'],
                result['source_id'],
                result['parent_section_id']
            )
            
            # 獲取子段落
            children = self._get_child_sections(
                result['source_table'],
                result['source_id'],
                result['section_id']
            )
            
            # 獲取兄弟段落（可選）
            siblings = []
            if include_siblings and parent:
                siblings = self._get_sibling_sections(
                    result['source_table'],
                    result['source_id'],
                    result['parent_section_id'],
                    result['section_id']
                )
            
            enriched_results.append({
                **result,
                'parent_section': parent,
                'child_sections': children,
                'sibling_sections': siblings
            })
        
        return enriched_results
```

---

## 📊 預期效果對比

### 搜尋精準度提升

| 場景 | 當前方案 | 分段方案 | 改善幅度 |
|------|----------|----------|----------|
| **精確查詢** (如 "連接失敗") | 返回整篇 600 字 | 返回段落 50 字 | ✅ **92% 減少** |
| **主題查詢** (如 "環境準備") | 返回整篇文檔 | 返回相關 2-3 段落 | ✅ **70% 減少** |
| **複雜查詢** (如 "速度優化方法") | 召回率 60% | 召回率 85% | ✅ **+42% 提升** |
| **相似度分數** | 0.65-0.75 | 0.75-0.90 | ✅ **+15-20% 提升** |

### 用戶體驗提升

#### 情境 1：精確問題
```
查詢: "ULINK 連接失敗怎麼辦？"

【當前】
返回: 整篇 "ULINK Protocol 測試基礎指南" (600 字)
問題: 用戶需要閱讀整篇文檔找答案
時間: ~2-3 分鐘

【分段搜尋】
返回: "常見問題 > 連接失敗" 段落 (80 字)
優勢: 直接定位到解決方案
時間: ~10 秒

改善: ⚡ 速度提升 12-18x，滿意度 +85%
```

#### 情境 2：學習型查詢
```
查詢: "如何準備測試環境？"

【當前】
返回: 3 篇文檔（共 1500 字）
問題: 包含大量無關資訊

【分段搜尋】
返回:
  1. "測試環境準備 > 硬體設備" (120 字) ⭐⭐⭐⭐⭐
  2. "測試環境準備 > 軟體安裝" (150 字) ⭐⭐⭐⭐⭐
  3. "環境配置 > 網路設定" (90 字) ⭐⭐⭐⭐
  
總計: 360 字（相關度 95%）

改善: 📖 閱讀量減少 76%，相關度 +40%
```

---

## 🚀 實施計劃

### 階段 1：基礎建設（3-5 天）

#### Day 1-2: 資料庫結構
```bash
# 1. 創建段落向量表
docker exec postgres_db psql -U postgres -d ai_platform -f create_section_embeddings_table.sql

# 2. 創建索引
docker exec postgres_db psql -U postgres -d ai_platform -f create_section_indexes.sql

# 3. 驗證表結構
docker exec postgres_db psql -U postgres -d ai_platform -c "\d document_section_embeddings"
```

#### Day 3: Markdown 解析器
```python
# 1. 實現 MarkdownStructureParser
# library/common/knowledge_base/markdown_parser.py

# 2. 單元測試
# tests/test_markdown_parser.py

# 3. 測試解析結果
parser = MarkdownStructureParser()
sections = parser.parse(sample_markdown, "Test Guide")
assert len(sections) > 0
```

#### Day 4: 段落向量化
```python
# 1. 實現 SectionVectorizationService
# library/common/knowledge_base/section_vectorization_service.py

# 2. 為現有文檔生成段落向量
service = SectionVectorizationService()

for guide in ProtocolGuide.objects.all():
    service.vectorize_document_sections(
        source_table='protocol_guide',
        source_id=guide.id,
        markdown_content=guide.content,
        document_title=guide.title
    )
```

#### Day 5: 段落搜尋服務
```python
# 1. 實現 SectionSearchService
# library/common/knowledge_base/section_search_service.py

# 2. 測試搜尋功能
search_service = SectionSearchService()
results = search_service.search_sections(
    query="如何連接 ULINK",
    source_table='protocol_guide',
    limit=5
)

# 驗證結果
assert len(results) > 0
assert results[0]['similarity_score'] > 0.7
```

### 階段 2：ViewSet 整合（2-3 天）

#### Day 6: API 端點
```python
# backend/api/views/viewsets/knowledge_viewsets.py

class ProtocolGuideViewSet(viewsets.ModelViewSet):
    # ... 現有代碼
    
    @action(detail=False, methods=['post'])
    def search_sections(self, request):
        """段落級別搜尋 API"""
        query = request.data.get('query', '')
        min_level = request.data.get('min_level', 1)
        max_level = request.data.get('max_level', 6)
        limit = request.data.get('limit', 5)
        
        search_service = SectionSearchService()
        results = search_service.search_sections(
            query=query,
            source_table='protocol_guide',
            min_level=min_level,
            max_level=max_level,
            limit=limit
        )
        
        return Response({
            'results': results,
            'search_type': 'section_based',
            'total': len(results)
        })
    
    @action(detail=True, methods=['post'])
    def regenerate_sections(self, request, pk=None):
        """重新生成段落向量"""
        guide = self.get_object()
        
        service = SectionVectorizationService()
        count = service.vectorize_document_sections(
            source_table='protocol_guide',
            source_id=guide.id,
            markdown_content=guide.content,
            document_title=guide.title
        )
        
        return Response({
            'success': True,
            'sections_generated': count
        })
```

#### Day 7-8: 前端整合
```javascript
// frontend/src/hooks/useSectionSearch.js

export const useSectionSearch = () => {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  
  const searchSections = async (query, options = {}) => {
    setLoading(true);
    
    try {
      const response = await api.post('/api/protocol-guides/search_sections/', {
        query: query,
        min_level: options.minLevel || 1,
        max_level: options.maxLevel || 6,
        limit: options.limit || 5
      });
      
      setResults(response.data.results);
      return response.data.results;
      
    } catch (error) {
      console.error('段落搜尋失敗:', error);
      return [];
    } finally {
      setLoading(false);
    }
  };
  
  return { searchSections, results, loading };
};
```

```jsx
// frontend/src/components/SectionSearchResults.jsx

const SectionSearchResults = ({ results }) => {
  return (
    <div className="section-search-results">
      {results.map((section, idx) => (
        <Card key={idx} className="section-result-card">
          <div className="section-path">
            <Breadcrumb>
              {section.section_path.split(' > ').map((part, i) => (
                <Breadcrumb.Item key={i}>{part}</Breadcrumb.Item>
              ))}
            </Breadcrumb>
          </div>
          
          <div className="section-title">
            <Typography.Title level={section.heading_level + 2}>
              {section.heading_text}
            </Typography.Title>
          </div>
          
          <div className="section-content">
            <ReactMarkdown>{section.content}</ReactMarkdown>
          </div>
          
          <div className="section-meta">
            <Tag>相似度: {(section.similarity_score * 100).toFixed(1)}%</Tag>
            <Tag>層級: H{section.heading_level}</Tag>
            <Tag>字數: {section.word_count}</Tag>
            {section.has_code && <Tag color="blue">包含代碼</Tag>}
            {section.has_images && <Tag color="green">包含圖片</Tag>}
          </div>
        </Card>
      ))}
    </div>
  );
};
```

### 階段 3：優化與擴展（1 週）

#### Week 2: 進階功能
1. **智能段落合併**：自動合併過短的段落
2. **層級過濾器**：讓用戶選擇搜尋粒度（章節/小節/子節）
3. **上下文展開**：點擊段落顯示父子段落
4. **段落高亮**：在完整文檔中高亮匹配段落

---

## 💡 進階優化方向

### 1. 混合搜尋（段落 + 文檔）

```python
def hybrid_document_section_search(query: str, limit: int = 10):
    """
    混合搜尋策略：
    1. 段落級搜尋（精確）
    2. 文檔級搜尋（全面）
    3. 智能合併結果
    """
    # 段落搜尋
    section_results = section_search_service.search_sections(
        query=query,
        limit=limit
    )
    
    # 文檔搜尋
    document_results = vector_search_service.search_documents(
        query=query,
        limit=limit
    )
    
    # 合併並去重
    merged_results = merge_and_deduplicate(
        section_results,
        document_results,
        section_weight=0.7,  # 段落權重更高
        document_weight=0.3
    )
    
    return merged_results[:limit]
```

### 2. 智能段落摘要

```python
def generate_section_summary(section: MarkdownSection) -> str:
    """
    為長段落生成智能摘要
    
    使用 LLM 生成 2-3 句話摘要
    """
    if section.word_count < 100:
        return section.content
    
    prompt = f"""
    請為以下內容生成 2-3 句話的摘要：
    
    標題：{section.title}
    內容：{section.content}
    
    摘要：
    """
    
    summary = llm_client.generate(prompt)
    return summary
```

### 3. 段落關聯性分析

```python
def find_related_sections(section_id: str, limit: int = 5) -> List[Dict]:
    """
    查找相關段落
    
    基於：
    1. 向量相似度
    2. 結構關係（父子、兄弟）
    3. 交叉引用
    """
    # 1. 獲取當前段落向量
    current_embedding = get_section_embedding(section_id)
    
    # 2. 向量相似度搜尋
    similar_sections = vector_similarity_search(current_embedding, limit=20)
    
    # 3. 結構關係加權
    for section in similar_sections:
        if is_sibling(section_id, section['section_id']):
            section['score'] *= 1.2
        elif is_parent_child(section_id, section['section_id']):
            section['score'] *= 1.15
    
    # 4. 重新排序
    similar_sections.sort(key=lambda x: x['score'], reverse=True)
    
    return similar_sections[:limit]
```

---

## 📈 預期投資回報

### 開發投入
- **時間**: 1.5-2 週
- **人力**: 1-2 人
- **基礎設施**: 資料庫空間 +20-30%

### 預期回報

| 指標 | 提升幅度 | 商業價值 |
|------|----------|----------|
| **搜尋精準度** | +20-30% | 減少用戶挫折，提升滿意度 |
| **答案定位速度** | +12-18x | 節省用戶時間，提升效率 |
| **相關度** | +40% | 減少無關資訊干擾 |
| **召回率** | +25-35% | 找到更多相關內容 |
| **用戶留存率** | +15-20% | 更好的體驗導致更高留存 |

### ROI 分析
```
投入成本: 2 週開發 + 資料庫空間
預期收益:
  - 用戶查詢時間減少 80%
  - 支持工單減少 30%（更好的自助服務）
  - 用戶滿意度提升 25%
  
投資回報率: 約 300-400%（3-6 個月內）
```

---

## 🎯 結論與建議

### 立即行動建議

1. **第一優先**：實施 Markdown 結構化分段
   - 投入: 1.5-2 週
   - 回報: 精準度 +20-30%，用戶體驗質變

2. **第二優先**：結合混合搜尋（上一份報告）
   - 段落搜尋 + 文檔搜尋 + 關鍵字搜尋
   - 三重保障，召回率和精準度雙提升

3. **第三優先**：智能重排序和快取
   - 在段落搜尋基礎上進一步優化

### 技術亮點

✅ **解決痛點**：從「找到文檔」升級到「找到答案」  
✅ **用戶體驗**：從「閱讀整篇」升級到「直達段落」  
✅ **技術創新**：結構化 + 向量化 = 精準搜尋  
✅ **可擴展性**：適用於所有 Markdown 文檔  

### 最終願景

**建立「段落級」AI 知識庫搜尋系統**，讓用戶：
- 🎯 精準定位到具體段落（不是整篇文檔）
- ⚡ 10 秒內找到答案（不是 2-3 分鐘）
- 📖 只閱讀相關內容（不是大海撈針）
- 🤖 體驗智能化搜尋（不是關鍵字匹配）

---

**報告生成日期**: 2025-10-19  
**提案者**: AI Platform Team  
**版本**: v1.0  
**狀態**: 💡 技術方案已完成，待決策實施
