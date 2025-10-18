"""
段落搜尋服務

提供基於向量的段落級別語義搜尋功能。
"""

import logging
from typing import List, Dict, Any, Optional
from django.db import connection
from api.services.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)


class SectionSearchService:
    """段落搜尋服務"""
    
    def __init__(self):
        self.embedding_service = get_embedding_service('ultra_high')  # 1024 維
    
    def search_sections(
        self,
        query: str,
        source_table: str,
        min_level: Optional[int] = None,
        max_level: Optional[int] = None,
        limit: int = 5,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        搜尋段落
        
        Args:
            query: 查詢文本
            source_table: 來源表名 (如 'protocol_guide')
            min_level: 最小標題層級 (1-6)
            max_level: 最大標題層級 (1-6)
            limit: 返回結果數量
            threshold: 相似度閾值 (0-1)
        
        Returns:
            段落列表 [{
                'section_id': str,
                'source_id': int,
                'heading_level': int,
                'heading_text': str,
                'section_path': str,
                'content': str,
                'similarity': float,
                'word_count': int,
                'has_code': bool,
                'has_images': bool
            }]
        """
        try:
            # 生成查詢向量
            query_embedding = self.embedding_service.generate_embedding(query)
            embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
            
            # 建立 SQL 查詢
            sql = """
                SELECT 
                    section_id,
                    source_id,
                    heading_level,
                    heading_text,
                    section_path,
                    content,
                    1 - (embedding <=> %s::vector) as similarity,
                    word_count,
                    has_code,
                    has_images
                FROM document_section_embeddings
                WHERE source_table = %s
            """
            
            params = [embedding_str, source_table]
            
            # 添加層級過濾
            if min_level is not None:
                sql += " AND heading_level >= %s"
                params.append(min_level)
            
            if max_level is not None:
                sql += " AND heading_level <= %s"
                params.append(max_level)
            
            # 添加相似度閾值
            sql += " AND (1 - (embedding <=> %s::vector)) >= %s"
            params.extend([embedding_str, threshold])
            
            # 排序和限制
            sql += " ORDER BY embedding <=> %s::vector LIMIT %s"
            params.extend([embedding_str, limit])
            
            # 執行查詢
            with connection.cursor() as cursor:
                cursor.execute(sql, params)
                columns = [col[0] for col in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            logger.info(
                f"🔍 段落搜尋: query='{query}', "
                f"source={source_table}, "
                f"level={min_level}-{max_level}, "
                f"results={len(results)}"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"段落搜尋失敗: {str(e)}", exc_info=True)
            return []
    
    def search_with_context(
        self,
        query: str,
        source_table: str,
        limit: int = 3,
        include_siblings: bool = False
    ) -> List[Dict[str, Any]]:
        """
        搜尋段落（包含上下文）
        
        Args:
            query: 查詢文本
            source_table: 來源表名
            limit: 返回結果數量
            include_siblings: 是否包含兄弟段落
        
        Returns:
            段落列表（包含 parent, children, siblings）
        """
        # 基礎搜尋
        sections = self.search_sections(query, source_table, limit=limit)
        
        # 為每個段落添加上下文
        for section in sections:
            try:
                # 獲取父段落
                parent = self._get_parent_section(
                    source_table,
                    section['source_id'],
                    section['section_id']
                )
                section['parent'] = parent
                
                # 獲取子段落
                children = self._get_child_sections(
                    source_table,
                    section['source_id'],
                    section['section_id']
                )
                section['children'] = children
                
                # 獲取兄弟段落（可選）
                if include_siblings:
                    siblings = self._get_sibling_sections(
                        source_table,
                        section['source_id'],
                        section['section_id']
                    )
                    section['siblings'] = siblings
                
            except Exception as e:
                logger.error(f"獲取段落上下文失敗: {str(e)}", exc_info=True)
        
        return sections
    
    def _get_parent_section(
        self,
        source_table: str,
        source_id: int,
        section_id: str
    ) -> Optional[Dict[str, Any]]:
        """獲取父段落"""
        try:
            with connection.cursor() as cursor:
                # 查找當前段落的 parent_section_id
                cursor.execute(
                    """
                    SELECT parent_section_id
                    FROM document_section_embeddings
                    WHERE source_table = %s AND source_id = %s AND section_id = %s;
                    """,
                    [source_table, source_id, section_id]
                )
                
                row = cursor.fetchone()
                if not row or not row[0]:
                    return None
                
                parent_id = row[0]
                
                # 獲取父段落詳細資料
                cursor.execute(
                    """
                    SELECT 
                        section_id, heading_level, heading_text,
                        section_path, content, word_count
                    FROM document_section_embeddings
                    WHERE source_table = %s AND source_id = %s AND section_id = %s;
                    """,
                    [source_table, source_id, parent_id]
                )
                
                row = cursor.fetchone()
                if row:
                    columns = ['section_id', 'heading_level', 'heading_text',
                              'section_path', 'content', 'word_count']
                    return dict(zip(columns, row))
                
        except Exception as e:
            logger.error(f"獲取父段落失敗: {str(e)}", exc_info=True)
        
        return None
    
    def _get_child_sections(
        self,
        source_table: str,
        source_id: int,
        parent_section_id: str
    ) -> List[Dict[str, Any]]:
        """獲取子段落"""
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT 
                        section_id, heading_level, heading_text,
                        section_path, content, word_count
                    FROM document_section_embeddings
                    WHERE source_table = %s 
                      AND source_id = %s 
                      AND parent_section_id = %s
                    ORDER BY section_id;
                    """,
                    [source_table, source_id, parent_section_id]
                )
                
                columns = ['section_id', 'heading_level', 'heading_text',
                          'section_path', 'content', 'word_count']
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"獲取子段落失敗: {str(e)}", exc_info=True)
            return []
    
    def _get_sibling_sections(
        self,
        source_table: str,
        source_id: int,
        section_id: str
    ) -> List[Dict[str, Any]]:
        """獲取兄弟段落（相同父段落的其他子段落）"""
        try:
            with connection.cursor() as cursor:
                # 先獲取當前段落的父 ID
                cursor.execute(
                    """
                    SELECT parent_section_id
                    FROM document_section_embeddings
                    WHERE source_table = %s AND source_id = %s AND section_id = %s;
                    """,
                    [source_table, source_id, section_id]
                )
                
                row = cursor.fetchone()
                if not row:
                    return []
                
                parent_id = row[0]
                
                # 查找所有相同父 ID 的段落（排除自己）
                cursor.execute(
                    """
                    SELECT 
                        section_id, heading_level, heading_text,
                        section_path, content, word_count
                    FROM document_section_embeddings
                    WHERE source_table = %s 
                      AND source_id = %s 
                      AND parent_section_id = %s
                      AND section_id != %s
                    ORDER BY section_id;
                    """,
                    [source_table, source_id, parent_id, section_id]
                )
                
                columns = ['section_id', 'heading_level', 'heading_text',
                          'section_path', 'content', 'word_count']
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"獲取兄弟段落失敗: {str(e)}", exc_info=True)
            return []
