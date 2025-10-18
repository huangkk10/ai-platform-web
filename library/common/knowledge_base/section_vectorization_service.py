"""
段落向量化服務

用於為 Markdown 段落生成 1024 維向量並儲存到資料庫。
"""

import logging
from typing import List, Dict, Any
from django.db import connection
from .markdown_parser import MarkdownStructureParser, MarkdownSection
from api.services.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)


class SectionVectorizationService:
    """段落向量化服務"""
    
    def __init__(self):
        self.parser = MarkdownStructureParser()
        self.embedding_service = get_embedding_service('ultra_high')  # 1024 維
    
    def vectorize_document_sections(
        self,
        source_table: str,
        source_id: int,
        markdown_content: str,
        document_title: str = ""
    ) -> Dict[str, Any]:
        """
        解析文檔並為所有段落生成向量
        
        Args:
            source_table: 來源表名 (如 'protocol_guide')
            source_id: 來源記錄 ID
            markdown_content: Markdown 文本
            document_title: 文檔標題（可選）
        
        Returns:
            結果統計 {
                'success': True/False,
                'total_sections': int,
                'vectorized_count': int,
                'sections': List[MarkdownSection]
            }
        """
        try:
            # 解析 Markdown 結構
            sections = self.parser.parse(markdown_content, document_title)
            
            if not sections:
                logger.warning(f"文檔 {source_table}.{source_id} 解析不出段落")
                return {
                    'success': False,
                    'total_sections': 0,
                    'vectorized_count': 0,
                    'sections': [],
                    'error': '無法解析段落'
                }
            
            # 為每個段落生成向量
            vectorized_count = 0
            for section in sections:
                try:
                    # 準備完整上下文（包含路徑和內容）
                    full_context = f"{section.path}\n\n{section.content}"
                    
                    # 生成向量
                    success = self._store_section_embedding(
                        source_table=source_table,
                        source_id=source_id,
                        section=section,
                        full_context=full_context
                    )
                    
                    if success:
                        vectorized_count += 1
                    
                except Exception as e:
                    logger.error(
                        f"段落 {section.section_id} 向量生成失敗: {str(e)}",
                        exc_info=True
                    )
            
            logger.info(
                f"✅ 文檔 {source_table}.{source_id} 向量化完成: "
                f"{vectorized_count}/{len(sections)} 段落"
            )
            
            return {
                'success': vectorized_count > 0,
                'total_sections': len(sections),
                'vectorized_count': vectorized_count,
                'sections': sections
            }
            
        except Exception as e:
            logger.error(
                f"文檔 {source_table}.{source_id} 向量化失敗: {str(e)}",
                exc_info=True
            )
            return {
                'success': False,
                'total_sections': 0,
                'vectorized_count': 0,
                'sections': [],
                'error': str(e)
            }
    
    def _store_section_embedding(
        self,
        source_table: str,
        source_id: int,
        section: MarkdownSection,
        full_context: str
    ) -> bool:
        """
        生成並儲存段落向量到資料庫
        
        Args:
            source_table: 來源表名
            source_id: 來源記錄 ID
            section: 段落數據
            full_context: 完整上下文（路徑 + 內容）
        
        Returns:
            成功 True，失敗 False
        """
        try:
            # 生成 1024 維向量
            embedding = self.embedding_service.generate_embedding(full_context)
            
            # 轉換為 pgvector 格式
            embedding_str = '[' + ','.join(map(str, embedding)) + ']'
            
            # 儲存到資料庫
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO document_section_embeddings (
                        source_table, source_id, section_id,
                        heading_level, heading_text, section_path, parent_section_id,
                        content, full_context, embedding,
                        word_count, has_code, has_images,
                        created_at, updated_at
                    ) VALUES (
                        %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s::vector,
                        %s, %s, %s,
                        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    )
                    ON CONFLICT (source_table, source_id, section_id)
                    DO UPDATE SET
                        heading_level = EXCLUDED.heading_level,
                        heading_text = EXCLUDED.heading_text,
                        section_path = EXCLUDED.section_path,
                        parent_section_id = EXCLUDED.parent_section_id,
                        content = EXCLUDED.content,
                        full_context = EXCLUDED.full_context,
                        embedding = EXCLUDED.embedding,
                        word_count = EXCLUDED.word_count,
                        has_code = EXCLUDED.has_code,
                        has_images = EXCLUDED.has_images,
                        updated_at = CURRENT_TIMESTAMP;
                    """,
                    [
                        source_table, source_id, section.section_id,
                        section.level, section.title, section.path, section.parent_id,
                        section.content, full_context, embedding_str,
                        section.word_count, section.has_code, section.has_images
                    ]
                )
            
            return True
            
        except Exception as e:
            logger.error(
                f"儲存段落 {section.section_id} 向量失敗: {str(e)}",
                exc_info=True
            )
            return False
    
    def delete_document_sections(self, source_table: str, source_id: int) -> int:
        """
        刪除文檔的所有段落向量
        
        Args:
            source_table: 來源表名
            source_id: 來源記錄 ID
        
        Returns:
            刪除的段落數量
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    DELETE FROM document_section_embeddings
                    WHERE source_table = %s AND source_id = %s;
                    """,
                    [source_table, source_id]
                )
                deleted_count = cursor.rowcount
                
            logger.info(
                f"✅ 刪除 {source_table}.{source_id} 的 {deleted_count} 個段落向量"
            )
            
            return deleted_count
            
        except Exception as e:
            logger.error(
                f"刪除 {source_table}.{source_id} 段落向量失敗: {str(e)}",
                exc_info=True
            )
            return 0
