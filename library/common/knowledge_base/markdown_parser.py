"""
Markdown 結構解析器

用於將 Markdown 文檔解析為結構化段落，支援層級關係和元數據提取。
"""

import re
from typing import List, Optional
from dataclasses import dataclass, field


@dataclass
class MarkdownSection:
    """Markdown 段落數據結構"""
    section_id: str              # 唯一 ID (如 'sec_1', 'sec_2')
    level: int                   # 標題層級 (1-6)
    title: str                   # 標題文字
    content: str                 # 段落內容（不含子段落）
    path: str                    # 完整路徑 (如 'Guide > Chapter > Section')
    parent_id: Optional[str]     # 父段落 ID
    children_ids: List[str] = field(default_factory=list)  # 子段落 IDs
    start_line: int = 0          # 起始行號
    end_line: int = 0            # 結束行號
    
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
        if not markdown_content or not markdown_content.strip():
            return []
        
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
        sections = []
        for idx, heading in enumerate(headings):
            # 計算段落內容範圍
            start_line = heading['line_num']
            end_line = headings[idx + 1]['line_num'] if idx + 1 < len(headings) else len(lines)
            
            # 提取段落內容（排除標題行，包含到下一個標題前）
            section_lines = lines[start_line + 1:end_line]
            section_content = '\n'.join(section_lines).strip()
            
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
    
    def _find_parent_section(self, headings: List[dict], current_idx: int) -> Optional[str]:
        """查找父段落 ID"""
        current_level = headings[current_idx]['level']
        
        # 向前查找第一個層級更高（數字更小）的標題
        for i in range(current_idx - 1, -1, -1):
            if headings[i]['level'] < current_level:
                return f"sec_{i + 1}"
        
        return None
    
    def _build_section_path(self, headings: List[dict], current_idx: int, document_title: str) -> str:
        """建立段落完整路徑"""
        path_parts = []
        
        if document_title:
            path_parts.append(document_title)
        
        current_level = headings[current_idx]['level']
        
        # 收集所有祖先標題
        ancestors = []
        for i in range(current_idx):
            if headings[i]['level'] < current_level:
                # 只保留直接祖先
                ancestors = [h for h in ancestors if h['level'] < headings[i]['level']]
                ancestors.append(headings[i])
        
        # 添加祖先標題到路徑
        for ancestor in ancestors:
            path_parts.append(ancestor['title'])
        
        # 添加當前標題
        path_parts.append(headings[current_idx]['title'])
        
        return ' > '.join(path_parts)
    
    def _link_parent_children(self, sections: List[MarkdownSection]):
        """建立父子段落關聯"""
        section_dict = {s.section_id: s for s in sections}
        
        for section in sections:
            if section.parent_id and section.parent_id in section_dict:
                parent = section_dict[section.parent_id]
                if section.section_id not in parent.children_ids:
                    parent.children_ids.append(section.section_id)
    
    def _create_single_section(self, content: str, title: str) -> MarkdownSection:
        """創建單一段落（無標題情況）"""
        has_code = bool(self.code_block_pattern.search(content))
        has_images = bool(self.image_pattern.search(content))
        
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
            has_code=has_code,
            has_images=has_images,
            word_count=len(content)
        )
