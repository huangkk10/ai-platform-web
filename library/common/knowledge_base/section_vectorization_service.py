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
            # ✅ 步驟 1：先創建並處理文檔標題段落（is_document_title=true）
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
                        content=markdown_content[:500] if markdown_content else clean_title,  # 使用前 500 字元
                        parent_id=None,
                        path=clean_title,
                        word_count=len((markdown_content[:500] if markdown_content else clean_title).split()),
                        has_code=False,
                        has_images=False
                    )
                    
                    # 生成文檔標題段落的向量（使用特殊標記 is_document_title=true）
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
                    logger.error(
                        f"❌ 文檔標題段落創建失敗: {source_table}.{source_id} - {str(e)}",
                        exc_info=True
                    )
            else:
                logger.warning(f"⚠️  文檔 {source_table}.{source_id} 沒有提供 document_title，跳過文檔標題段落")
            
            # ✅ 步驟 2：解析 Markdown 結構（正常的段落）
            sections = self.parser.parse(markdown_content, document_title)
            
            if not sections:
                logger.warning(f"文檔 {source_table}.{source_id} 解析不出段落")
                # 如果有文檔標題段落，仍然算成功
                if doc_title_vectorized:
                    return {
                        'success': True,
                        'total_sections': 1,  # 只有文檔標題段落
                        'vectorized_count': 1,
                        'sections': [],
                        'has_document_title_section': True
                    }
                return {
                    'success': False,
                    'total_sections': 0,
                    'vectorized_count': 0,
                    'sections': [],
                    'error': '無法解析段落'
                }
            
            # ✅ 步驟 3：為每個 Markdown 段落生成向量
            vectorized_count = 1 if doc_title_vectorized else 0  # 初始計數包含文檔標題段落
            for section in sections:
                try:
                    # 準備完整上下文（包含路徑和內容）
                    full_context = f"{section.path}\n\n{section.content}"
                    
                    # 生成向量（傳遞 document_title）
                    success = self._store_section_embedding(
                        source_table=source_table,
                        source_id=source_id,
                        section=section,
                        full_context=full_context,
                        document_title=document_title  # ✅ 傳遞文檔標題
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
    
    def _store_document_title_section(
        self,
        source_table: str,
        source_id: int,
        section: MarkdownSection,
        document_title: str
    ) -> bool:
        """
        專門處理文檔標題段落的向量生成和儲存
        
        此方法為文檔創建一個特殊的標題段落（is_document_title=true），
        用於 Stage 1 搜尋的標題權重計算。
        
        特點：
        - section_id 格式：doc_{source_id}
        - heading_level: 0（特殊標記）
        - is_document_title: true
        - title_embedding: 使用文檔標題生成
        - content_embedding: 使用文檔前 500 字元生成
        
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
                        true,
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
            logger.error(
                f"❌ 儲存文檔標題段落 {section.section_id} 失敗: {str(e)}",
                exc_info=True
            )
            return False
    
    def _store_section_embedding(
        self,
        source_table: str,
        source_id: int,
        section: MarkdownSection,
        full_context: str,
        document_title: str = ""  # ✅ 添加文檔標題參數
    ) -> bool:
        """
        生成並儲存段落向量到資料庫（包含標題和內容的分離向量）
        
        Args:
            source_table: 來源表名
            source_id: 來源記錄 ID
            section: 段落數據
            full_context: 完整上下文（路徑 + 內容）
            document_title: 文檔標題（用於 document_title 欄位）
        
        Returns:
            成功 True，失敗 False
        """
        try:
            # ✅ 生成標題向量（1024 維）
            title_embedding = None
            if section.title and section.title.strip():
                title_embedding = self.embedding_service.generate_embedding(section.title)
            
            # ✅ 生成內容向量（1024 維）
            content_embedding = None
            if section.content and section.content.strip():
                content_embedding = self.embedding_service.generate_embedding(section.content)
            
            # ✅ 生成完整上下文向量（向後兼容，舊欄位）
            embedding = self.embedding_service.generate_embedding(full_context)
            
            # 轉換為 pgvector 格式
            embedding_str = '[' + ','.join(map(str, embedding)) + ']'
            title_embedding_str = '[' + ','.join(map(str, title_embedding)) + ']' if title_embedding is not None else None
            content_embedding_str = '[' + ','.join(map(str, content_embedding)) + ']' if content_embedding is not None else None
            
            # 🔧 生成 document_id（使用 source_table + source_id 的組合）
            # 格式：protocol_guide_20, rvt_guide_15 等
            document_id = f"{source_table}_{source_id}"
            
            # ✅ 儲存到資料庫（包含三個向量欄位 + document_id + document_title）
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
                        created_at, updated_at
                    ) VALUES (
                        %s, %s, %s,
                        %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, 
                        %s::vector, %s::vector, %s::vector,
                        %s, %s, %s,
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
