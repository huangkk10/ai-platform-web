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
    
    def _get_weights_for_assistant(self, source_table: str) -> tuple:
        """
        根據 source_table 獲取對應的權重配置
        
        Returns:
            tuple: (title_weight, content_weight) 範圍 0.0-1.0
        """
        from api.models import SearchThresholdSetting
        
        # 映射表名到助手類型
        table_to_type = {
            'protocol_guide': 'protocol_assistant',
            'rvt_guide': 'rvt_assistant',
        }
        
        assistant_type = table_to_type.get(source_table)
        if not assistant_type:
            logger.warning(f"未知的 source_table: {source_table}，使用預設權重 60/40")
            return (0.6, 0.4)
        
        try:
            setting = SearchThresholdSetting.objects.get(assistant_type=assistant_type)
            title_weight = setting.title_weight / 100.0
            content_weight = setting.content_weight / 100.0
            logger.info(f"📊 載入段落搜尋權重配置: {assistant_type} -> 標題 {setting.title_weight}% / 內容 {setting.content_weight}%")
            return (title_weight, content_weight)
        except SearchThresholdSetting.DoesNotExist:
            logger.warning(f"找不到 {assistant_type} 的權重配置，使用預設 60/40")
            return (0.6, 0.4)
    
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
            # ✅ 獲取權重配置
            title_weight, content_weight = self._get_weights_for_assistant(source_table)
            
            # 生成查詢向量
            query_embedding = self.embedding_service.generate_embedding(query)
            embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
            
            # ✅ 檢查是否有多向量欄位資料
            check_sql = """
                SELECT COUNT(*) 
                FROM document_section_embeddings 
                WHERE source_table = %s 
                  AND title_embedding IS NOT NULL 
                  AND content_embedding IS NOT NULL
            """
            
            with connection.cursor() as cursor:
                cursor.execute(check_sql, [source_table])
                multi_vector_count = cursor.fetchone()[0]
            
            # ✅ 如果有多向量資料，使用加權搜尋
            if multi_vector_count > 0:
                logger.info(f"✅ 使用多向量搜尋 (權重: {int(title_weight*100)}%/{int(content_weight*100)}%)")
                
                sql = f"""
                    SELECT 
                        dse.section_id,
                        dse.source_id,
                        dse.heading_level,
                        dse.heading_text,
                        dse.section_path,
                        dse.content,
                        ({title_weight} * (1 - (dse.title_embedding <=> %s::vector))) + 
                        ({content_weight} * (1 - (dse.content_embedding <=> %s::vector))) as similarity,
                        (1 - (dse.title_embedding <=> %s::vector)) as title_score,
                        (1 - (dse.content_embedding <=> %s::vector)) as content_score,
                        dse.word_count,
                        dse.has_code,
                        dse.has_images,
                        CASE 
                            WHEN dse.source_table = 'protocol_guide' THEN pg.title
                            WHEN dse.source_table = 'rvt_guide' THEN rg.title
                            ELSE NULL
                        END as doc_title
                    FROM document_section_embeddings dse
                    LEFT JOIN protocol_guide pg ON dse.source_table = 'protocol_guide' AND pg.id = dse.source_id
                    LEFT JOIN rvt_guide rg ON dse.source_table = 'rvt_guide' AND rg.id = dse.source_id
                    WHERE dse.source_table = %s
                      AND dse.title_embedding IS NOT NULL
                      AND dse.content_embedding IS NOT NULL
                """
                
                params = [embedding_str, embedding_str, embedding_str, embedding_str, source_table]
            else:
                logger.warning(f"⚠️ 段落表無多向量資料，使用舊版單一向量搜尋")
                
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
            
            # 添加相似度閾值（對於多向量，閾值應用於加權後的分數）
            if multi_vector_count > 0:
                sql += f" AND (({title_weight} * (1 - (dse.title_embedding <=> %s::vector))) + ({content_weight} * (1 - (dse.content_embedding <=> %s::vector)))) >= %s"
                params.extend([embedding_str, embedding_str, threshold])
            else:
                sql += " AND (1 - (embedding <=> %s::vector)) >= %s"
                params.extend([embedding_str, threshold])
            
            # 排序和限制
            sql += " ORDER BY similarity DESC LIMIT %s"
            params.append(limit)
            
            # 執行查詢
            with connection.cursor() as cursor:
                cursor.execute(sql, params)
                columns = [col[0] for col in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            logger.info(
                f"🔍 段落搜尋: query='{query}', "
                f"source={source_table}, "
                f"level={min_level}-{max_level}, "
                f"results={len(results)}, "
                f"weights={int(title_weight*100)}%/{int(content_weight*100)}%"
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
