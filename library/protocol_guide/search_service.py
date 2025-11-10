"""
Protocol Guide 搜索服務
=======================

使用基礎類別快速實現 Protocol Guide 的搜索功能。

✨ 重構後：代碼從 ~100 行減少至 ~30 行！
- 移除了 search_with_vectors 覆寫（現在使用基類的通用實現）
- 向量搜尋邏輯由 vector_search_helper 統一處理
- Protocol Guide 和 RVT Guide 使用相同的底層方法

🆕 文檔級搜尋功能（2025-11-10）：
- 智能查詢分類：檢測 SOP 相關關鍵字
- 文檔級結果組裝：返回完整文檔內容（2000+ 字元）
- 兼容現有搜尋：非 SOP 查詢仍返回 section 級結果
"""

from library.common.knowledge_base import BaseKnowledgeBaseSearchService
from api.models import ProtocolGuide
from django.db import connection
import logging

logger = logging.getLogger(__name__)


class ProtocolGuideSearchService(BaseKnowledgeBaseSearchService):
    """
    Protocol Guide 搜索服務
    
    繼承自 BaseKnowledgeBaseSearchService，自動獲得：
    - search_knowledge()       - 智能搜索（向量+關鍵字）- 已擴展支援文檔級搜尋
    - search_with_vectors()    - 向量搜索 (使用通用 helper)
    - search_with_keywords()   - 關鍵字搜索
    
    ✅ 重構優勢：
    - 不需要覆寫 search_with_vectors()
    - 與 RVT Guide 使用相同的實現方式
    - 代碼簡潔，易於維護
    
    🆕 文檔級搜尋增強：
    - _classify_query(): 檢測 SOP/文檔級查詢
    - _expand_to_full_document(): 組裝完整文檔內容
    - search_knowledge(): 智能選擇返回 section 或 document
    """
    
    # 設定必要的類別屬性
    model_class = ProtocolGuide
    source_table = 'protocol_guide'
    
    # 設定要搜索的欄位（簡化版，與 RVTGuide 一致）
    default_search_fields = [
        'title',    # 標題
        'content',  # 內容
    ]
    
    # 🆕 文檔級查詢關鍵字（觸發完整文檔返回）
    DOCUMENT_KEYWORDS = [
        'sop', 'SOP', '標準作業流程', '作業流程', '操作流程',
        '完整', '全部', '整個', '所有步驟', '全文',
        '教學', '教程', '指南', '手冊', '說明書'
    ]
    
    def __init__(self):
        super().__init__()
    
    def get_vector_service(self):
        """獲取向量服務（用於自動生成向量）"""
        from .vector_service import ProtocolGuideVectorService
        return ProtocolGuideVectorService()
    
    # ============================================================
    # 🆕 文檔級搜尋功能
    # ============================================================
    
    def _classify_query(self, query: str) -> str:
        """
        分類查詢類型
        
        Args:
            query: 用戶查詢文本
            
        Returns:
            'document' - 需要返回完整文檔
            'section' - 返回 section 級結果（預設）
        """
        query_lower = query.lower()
        
        # 檢查是否包含文檔級關鍵字
        for keyword in self.DOCUMENT_KEYWORDS:
            if keyword.lower() in query_lower:
                logger.info(f"🎯 檢測到文檔級查詢，關鍵字: '{keyword}'")
                return 'document'
        
        return 'section'
    
    def _expand_to_full_document(self, results: list) -> list:
        """
        將 section 級結果擴展為完整文檔
        
        Args:
            results: section 級搜尋結果列表
            
        Returns:
            完整文檔結果列表（每個文檔只返回一次，包含完整內容）
        """
        if not results:
            return []
        
        # 🔧 修正：從 source_id 查找 document_id
        # 先從 source_id 找出對應的 document_ids
        source_ids = set()
        for result in results:
            metadata = result.get('metadata', {})
            source_id = metadata.get('source_id') or metadata.get('id')
            if source_id:
                source_ids.add(source_id)
        
        if not source_ids:
            logger.warning("⚠️  搜尋結果中沒有 source_id，返回原始結果")
            return results
        
        # 從資料庫查詢 source_id 對應的 document_id
        document_ids = set()
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT document_id
                FROM document_section_embeddings
                WHERE source_table = %s
                    AND source_id = ANY(%s)
                    AND document_id IS NOT NULL
            """, [self.source_table, list(source_ids)])
            
            for row in cursor.fetchall():
                document_ids.add(row[0])
        
        if not document_ids:
            logger.warning(f"⚠️  無法從 source_ids {source_ids} 找到對應的 document_id")
            return results
        
        logger.info(f"📄 擴展為完整文檔，涉及 {len(document_ids)} 個文檔 (來自 {len(source_ids)} 個 source_ids)")
        
        # 從資料庫組裝完整文檔
        full_documents = []
        
        with connection.cursor() as cursor:
            for doc_id in document_ids:
                # 查詢該文檔的所有 sections（按 heading_level 和 id 排序）
                cursor.execute("""
                    SELECT 
                        heading_level,
                        heading_text,
                        content,
                        document_title
                    FROM document_section_embeddings
                    WHERE document_id = %s
                        AND source_table = %s
                        AND is_document_title = FALSE
                    ORDER BY heading_level, id
                """, [doc_id, self.source_table])
                
                sections = cursor.fetchall()
                
                if not sections:
                    continue
                
                # 組裝完整文檔內容
                document_title = sections[0][3]  # 從第一個 section 獲取 document_title
                full_content_parts = [f"# {document_title}\n"]
                
                for level, heading, content, _ in sections:
                    # 根據 heading_level 添加 Markdown 標題格式
                    heading_prefix = '#' * (level + 1) if level > 0 else '##'
                    full_content_parts.append(f"\n{heading_prefix} {heading}\n")
                    if content:
                        full_content_parts.append(content.strip())
                
                full_content = "\n".join(full_content_parts)
                
                # 創建文檔級結果
                full_documents.append({
                    'content': full_content,
                    'score': results[0].get('score', 0.0),  # 使用第一個結果的分數
                    'title': document_title,  # ✅ 添加 title 欄位（Dify 顯示引用來源）
                    'metadata': {
                        'source_table': self.source_table,
                        'document_id': doc_id,
                        'document_title': document_title,
                        'is_full_document': True,
                        'sections_count': len(sections)
                    }
                })
                
                logger.info(f"✅ 組裝完成: {document_title}, 包含 {len(sections)} 個 sections, {len(full_content)} 字元")
        
        return full_documents
    
    def search_knowledge(self, query: str, limit: int = 5, use_vector: bool = True, 
                        threshold: float = 0.7) -> list:
        """
        覆寫基類方法，添加文檔級搜尋支援
        
        智能搜索流程：
        1. 分類查詢類型（section vs document）
        2. 執行向量/關鍵字搜尋
        3. 如果是文檔級查詢，擴展為完整文檔
        
        Args:
            query: 搜尋查詢
            limit: 返回結果數量 (預設: 5)
            use_vector: 是否使用向量搜尋 (預設: True)
            threshold: 相似度閾值 (預設: 0.7)
            
        Returns:
            搜尋結果列表（section 或 document 級）
        """
        # 步驟 1: 分類查詢
        query_type = self._classify_query(query)
        
        # 步驟 2: 執行基礎搜尋（section 級）
        results = super().search_knowledge(
            query=query,
            limit=limit,
            use_vector=use_vector,
            threshold=threshold
        )
        
        # 步驟 3: 如果是文檔級查詢，擴展為完整文檔
        if query_type == 'document' and results:
            logger.info(f"🔄 將 {len(results)} 個 section 結果擴展為完整文檔")
            results = self._expand_to_full_document(results)
        
        return results
    
    # ============================================================
    # 可選：自定義內容格式化邏輯
    # ============================================================
    
    # def _get_item_content(self, item):
    #     """自定義內容獲取邏輯"""
    #     return f"標題: {item.title}\n內容: {item.content}"


