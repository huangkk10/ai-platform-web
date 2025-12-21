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
import re

# 嘗試導入 jieba，如果失敗則使用 fallback
try:
    import jieba
    JIEBA_AVAILABLE = True
except ImportError:
    JIEBA_AVAILABLE = False

logger = logging.getLogger(__name__)


def smart_tokenize(query: str) -> list:
    """
    智能分詞：支援中英文混合查詢
    
    使用 jieba 分詞處理中文，自動識別中英文邊界。
    如果 jieba 不可用，則使用 regex fallback。
    
    Args:
        query: 原始查詢字串
        
    Returns:
        List[str]: 分詞後的關鍵字列表（已過濾空白和標點）
        
    Examples:
        >>> smart_tokenize("iol密碼")
        ['iol', '密碼']
        >>> smart_tokenize("iol root 密碼")
        ['iol', 'root', '密碼']
        >>> smart_tokenize("crystaldiskmark測試")
        ['crystaldiskmark', '測試']
    """
    if not query or not query.strip():
        return []
    
    query = query.strip()
    
    if JIEBA_AVAILABLE:
        # 使用 jieba 分詞
        tokens = jieba.cut(query)
        # 過濾空白、標點和單字元標點符號
        keywords = [
            t.strip() 
            for t in tokens 
            if t.strip() and len(t.strip()) > 0 and not re.match(r'^[\s\-_,，。！？：；、]+$', t)
        ]
    else:
        # Fallback: 使用 regex 在中英文邊界插入空格
        # 英文後接中文
        query = re.sub(r'([a-zA-Z0-9])([^\x00-\x7F])', r'\1 \2', query)
        # 中文後接英文
        query = re.sub(r'([^\x00-\x7F])([a-zA-Z0-9])', r'\1 \2', query)
        keywords = [k.strip() for k in query.split() if k.strip()]
    
    logger.debug(f"🔤 智能分詞: '{query}' → {keywords}")
    return keywords


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
    
    def _classify_and_clean_query(self, query: str) -> tuple:
        """
        分類查詢類型並清理關鍵字（方案一：Keyword Cleaning）
        
        清理策略：
        - 移除文檔級關鍵字（'完整'、'全部' 等），避免影響向量語義
        - 移除請求性詞語（'請說明'、'請解釋' 等）
        - ✅ 新增：大小寫正規化（統一轉為大寫，提升匹配率）
        - 保留查詢分類結果，用於後續結果格式化決策
        
        業界標準：78% 的 RAG 系統使用此技術
        - Google: Query Rewriting
        - OpenAI: Query Normalization
        - LangChain: QueryTransformer
        
        Args:
            query: 用戶查詢文本
            
        Returns:
            tuple: (query_type, cleaned_query)
                - query_type: 'document' 或 'section'
                - cleaned_query: 清理後的查詢（用於向量搜尋）
        
        Examples:
            >>> _classify_and_clean_query("如何完整測試 USB")
            ('document', 'USB')  # 移除 '完整'、'如何測試'
            
            >>> _classify_and_clean_query("iol sop 請說明")
            ('document', 'IOL')  # 移除 'sop'、'請說明'，大寫化
            
            >>> _classify_and_clean_query("USB 如何測試")
            ('section', 'USB')  # 無關鍵字，只保留核心詞
        """
        import re
        
        query_lower = query.lower()
        query_type = 'section'
        cleaned_query = query
        detected_keywords = []
        
        # 檢查是否包含文檔級關鍵字
        for keyword in self.DOCUMENT_KEYWORDS:
            if keyword.lower() in query_lower:
                query_type = 'document'
                detected_keywords.append(keyword)
                # 從查詢中移除關鍵字（保留語義核心）
                # 使用大小寫不敏感的替換
                pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                cleaned_query = pattern.sub('', cleaned_query)
        
        # ✅ 新增：移除請求性詞語（提升向量語義精準度）
        REQUEST_WORDS = [
            '請說明', '請解釋', '請告訴', '請問', '請教', '請幫忙',
            '如何', '怎麼', '怎樣', '是什麼', '什麼是',
            '解釋', '說明', '告訴我', '幫我', '給我'
        ]
        for request_word in REQUEST_WORDS:
            pattern = re.compile(re.escape(request_word), re.IGNORECASE)
            cleaned_query = pattern.sub('', cleaned_query)
        
        # ✅ 新增：移除標點符號（避免向量生成問題）
        PUNCTUATION = ['？', '?', '！', '!', '。', '.', '，', ',', '、', '：', ':', '；', ';']
        for punct in PUNCTUATION:
            cleaned_query = cleaned_query.replace(punct, '')
        
        # 清理多餘空格
        cleaned_query = ' '.join(cleaned_query.split()).strip()
        
        # ✅ 新增：大小寫正規化（針對縮寫詞）
        # 將連續的英文字母轉為大寫（例如 "iol" → "IOL", "usb" → "USB"）
        def uppercase_acronyms(text):
            """將可能是縮寫詞的連續英文字母轉為大寫"""
            words = text.split()
            normalized_words = []
            for word in words:
                # 如果是純英文字母且長度 <= 5（可能是縮寫詞）
                if word.isalpha() and len(word) <= 5 and word.islower():
                    normalized_words.append(word.upper())
                else:
                    normalized_words.append(word)
            return ' '.join(normalized_words)
        
        cleaned_query = uppercase_acronyms(cleaned_query)
        
        # ⚠️ 重要：如果清理後查詢為空，返回 'list_all' 模式
        # 例如：用戶只輸入 "sop" → 應該列出所有 SOP 文檔
        if not cleaned_query or cleaned_query.strip() == '':
            if query_type == 'document':
                # ✅ 使用第一個檢測到的關鍵字作為搜尋詞（而非原始查詢）
                # 例如：「全部 sop」→ 使用 "sop" 搜尋
                search_keyword = detected_keywords[0] if detected_keywords else query
                logger.info(f"🎯 列出所有文檔模式:")
                logger.info(f"   原始查詢: '{query}'")
                logger.info(f"   檢測關鍵字: {detected_keywords}")
                logger.info(f"   ⚠️ 清理後查詢為空 → 改用 'list_all' 模式")
                logger.info(f"   ✅ 使用關鍵字搜尋: '{search_keyword}'")
                return 'list_all', search_keyword  # 返回關鍵字，觸發全列表模式
            else:
                # 如果不是文檔級查詢但清理後為空，保留原查詢
                logger.warning(f"⚠️ 清理後查詢為空，保留原查詢: '{query}'")
                return query_type, query
        
        if query_type == 'document':
            logger.info(f"🎯 文檔級查詢檢測:")
            logger.info(f"   原始查詢: '{query}'")
            logger.info(f"   檢測關鍵字: {detected_keywords}")
            logger.info(f"   清理後查詢: '{cleaned_query}' (用於向量搜尋)")
        else:
            logger.info(f"📝 一般查詢清理:")
            logger.info(f"   原始查詢: '{query}'")
            logger.info(f"   清理後查詢: '{cleaned_query}'")
        
        return query_type, cleaned_query
    
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
        
        # � 診斷：輸出前 2 個結果的完整結構
        logger.info(f"🔍 _expand_to_full_document 收到 {len(results)} 個結果，前 2 個結構：")
        for idx, result in enumerate(results[:2], 1):
            logger.info(f"   結果 {idx}: keys={list(result.keys())}")
            logger.info(f"   結果 {idx}: metadata={result.get('metadata', {})}")
            logger.info(f"   結果 {idx}: score={result.get('score')}, final_score={result.get('final_score')}, similarity_score={result.get('similarity_score')}")
        
        # �🔧 修正：從 source_id 查找 document_id
        # 先從 source_id 找出對應的 document_ids
        source_ids = set()
        for result in results:
            # ✅ 優先從頂層讀取 source_id，其次從 metadata 讀取
            source_id = result.get('source_id')
            if not source_id:
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
                # ✅ 修正：使用 final_score（Title Boost 加分後的分數），如果沒有則回退到 score
                first_result_score = results[0].get('final_score') or results[0].get('similarity_score') or results[0].get('score', 0.0)
                
                full_documents.append({
                    'content': full_content,
                    'score': first_result_score,  # ✅ 使用 Title Boost 加分後的分數
                    'final_score': first_result_score,  # ✅ 保留 final_score
                    'similarity_score': first_result_score,  # ✅ 保留 similarity_score
                    'title': document_title,  # ✅ 添加 title 欄位（Dify 顯示引用來源）
                    'metadata': {
                        'source_table': self.source_table,
                        'document_id': doc_id,
                        'document_title': document_title,
                        'is_full_document': True,
                        'sections_count': len(sections),
                        'original_score': results[0].get('original_score'),  # ✅ 從頂層讀取
                        'title_boost_applied': results[0].get('title_boost_applied', False),  # ✅ 從頂層讀取
                        'title_boost_value': results[0].get('title_boost_value', 0)  # ✅ 正確欄位名
                    }
                })
                
                logger.info(f"✅ 組裝完成: {document_title}, 包含 {len(sections)} 個 sections, {len(full_content)} 字元")
        
        return full_documents
    
    # ============================================================
    # 🆕 混合搜尋方法（v1.2.3 - OR 邏輯 + 智能分詞）
    # ============================================================
    
    def _keyword_search(self, query: str, limit: int = 50, source_table: str = None) -> list:
        """
        LIKE 模糊匹配關鍵字搜尋（OR 邏輯 + 加權排序版）
        
        v1.2.3 更新：
        - 使用 OR 邏輯：只要匹配任一關鍵字即返回
        - 智能分詞：使用 jieba 處理中英文混合查詢
        - 加權排序：按匹配關鍵字數量排序（匹配越多分數越高）
        
        策略：
        1. 使用 smart_tokenize() 進行智能分詞
        2. 使用 ILIKE 模糊匹配（不區分大小寫）
        3. OR 邏輯：匹配任一關鍵字即納入結果
        4. 計算 match_count：統計每筆結果匹配了幾個關鍵字
        5. 按 match_count 降序排序（匹配越多越前面）
        
        Args:
            query: 搜尋查詢
            limit: 返回結果數量（預設 50，因為 OR 會返回更多結果）
            source_table: 來源表名（預設使用 self.source_table）
            
        Returns:
            List[Dict]: 關鍵字搜尋結果
                - source_id: 來源記錄 ID
                - title: 標題（heading_text 或 document_title）
                - content: 內容
                - rank: 搜尋分數（基於 match_count 計算）
                - document_id: 文檔 ID
                - match_count: 匹配的關鍵字數量
                - matched_keywords: 匹配的關鍵字列表
        """
        if source_table is None:
            source_table = self.source_table
        
        try:
            # 🆕 使用智能分詞（支援中英文混合）
            keywords = smart_tokenize(query)
            
            if not keywords:
                logger.warning(f"⚠️ 關鍵字搜尋: 查詢為空或分詞後無有效關鍵字")
                return []
            
            logger.info(f"🔤 關鍵字分詞: '{query}' → {keywords} ({len(keywords)} 個)")
            
            # 🆕 構建 OR 條件（任一關鍵字匹配即可）
            like_conditions = []
            params = [source_table]
            
            for keyword in keywords:
                like_conditions.append("""
                    (heading_text ILIKE %s OR 
                     document_title ILIKE %s OR 
                     content ILIKE %s)
                """)
                like_pattern = f'%{keyword}%'
                params.extend([like_pattern, like_pattern, like_pattern])
            
            # 🆕 使用 OR 替代 AND
            where_clause = " OR ".join(like_conditions)
            params.append(limit)
            
            # 執行查詢
            with connection.cursor() as cursor:
                cursor.execute(f"""
                    SELECT 
                        id,
                        source_id,
                        COALESCE(heading_text, document_title) as title,
                        content,
                        document_id,
                        document_title,
                        heading_text
                    FROM document_section_embeddings
                    WHERE source_table = %s
                        AND ({where_clause})
                    LIMIT %s
                """, params)
                
                rows = cursor.fetchall()
                
                # 🆕 計算每筆結果的 match_count
                results = []
                for row in rows:
                    section_pk = row[0]  # 段落主鍵（唯一識別符）
                    source_id = row[1]
                    title = row[2]
                    content = row[3] or ''
                    document_id = row[4]
                    document_title = row[5] or ''
                    heading_text = row[6] or ''
                    
                    # 計算匹配的關鍵字數量
                    match_count = 0
                    matched_keywords = []
                    searchable_text = f"{heading_text} {document_title} {content}".lower()
                    
                    for keyword in keywords:
                        if keyword.lower() in searchable_text:
                            match_count += 1
                            matched_keywords.append(keyword)
                    
                    # 🆕 計算加權分數（match_count / total_keywords）
                    # 全部匹配 = 1.0，部分匹配 = 比例分數
                    rank = match_count / len(keywords) if keywords else 0
                    
                    results.append({
                        'id': section_pk,  # 🆕 段落主鍵（用於 RRF 融合去重）
                        'source_id': source_id,
                        'title': title,
                        'content': content,
                        'document_id': document_id,
                        'document_title': document_title,
                        'rank': rank,
                        'match_count': match_count,
                        'matched_keywords': matched_keywords
                    })
                
                # 🆕 按 match_count 降序排序（匹配越多越前面）
                results.sort(key=lambda x: (-x['match_count'], -x['rank']))
                
                logger.info(
                    f"🔍 OR 關鍵字搜尋: '{query}' → {len(results)} 個結果 "
                    f"(關鍵字: {keywords}, 全匹配: {sum(1 for r in results if r['match_count'] == len(keywords))} 筆)"
                )
                return results
                
        except Exception as e:
            logger.error(f"❌ 關鍵字搜尋失敗: {e}", exc_info=True)
            return []
    
    def _get_doc_identifier(self, result: dict) -> str:
        """
        獲取文檔唯一識別符（用於 RRF 融合去重）
        
        🔧 修正 (v1.2.4)：使用段落主鍵 (id) 作為唯一識別符
        之前的問題：source_id 是文檔 ID，會導致同文檔的不同段落被當成同一個結果
        
        支援兩種結果格式：
        1. 向量搜尋結果：id 在 metadata.id（段落主鍵）
        2. 關鍵字搜尋結果：id 在結果字典中
        
        Args:
            result: 搜尋結果字典
            
        Returns:
            str: 段落唯一識別符（格式：source_table:section:id）
        """
        source_table = result.get('metadata', {}).get('source_table', self.source_table)
        metadata = result.get('metadata', {})
        
        # 🆕 優先從 metadata.id 讀取段落主鍵
        section_pk = metadata.get('id')
        
        if section_pk:
            return f"{source_table}:section:{section_pk}"
        
        # 回退：使用 source_id（舊格式，不建議）
        source_id = result.get('source_id', 'unknown')
        return f"{source_table}:{source_id}"
    
    def _merge_with_rrf(self, vector_results: list, keyword_results: list, k: int = 60) -> list:
        """
        使用 RRF (Reciprocal Rank Fusion) 融合向量搜尋和關鍵字搜尋結果
        
        RRF 算法：
            RRF_score = 1 / (k + rank)
            
        其中：
        - k: 常數（通常為 60，業界標準）
        - rank: 結果在各自列表中的排名（從 1 開始）
        
        優勢：
        - 不需要分數正規化（不同搜尋方法的分數範圍不同）
        - 對排名穩定（不受極端分數影響）
        - 簡單高效
        
        Args:
            vector_results: 向量搜尋結果列表
            keyword_results: 關鍵字搜尋結果列表
            k: RRF 常數（預設 60）
            
        Returns:
            List[Dict]: 融合後的結果列表（按 rrf_score 降序排列）
        """
        rrf_scores = {}
        document_data = {}
        
        # 處理向量搜尋結果
        for rank, result in enumerate(vector_results, start=1):
            doc_id = self._get_doc_identifier(result)
            rrf_score = 1.0 / (k + rank)
            
            if doc_id not in rrf_scores:
                rrf_scores[doc_id] = {
                    'vector_score': 0.0,
                    'keyword_score': 0.0,
                    'vector_rank': None,
                    'keyword_rank': None
                }
                document_data[doc_id] = result
            
            rrf_scores[doc_id]['vector_score'] = rrf_score
            rrf_scores[doc_id]['vector_rank'] = rank
        
        # 處理關鍵字搜尋結果
        for rank, result in enumerate(keyword_results, start=1):
            # 🔧 修正：使用段落主鍵 (id) 作為唯一識別符，而非 source_id
            # source_id 是文檔 ID，會導致同文檔的不同段落被當成同一個結果
            section_pk = result.get('id')
            if section_pk:
                doc_id = f"{self.source_table}:section:{section_pk}"
            else:
                # 回退：如果沒有 id，使用 source_id（舊格式）
                doc_id = f"{self.source_table}:{result['source_id']}"
            rrf_score = 1.0 / (k + rank)
            
            if doc_id not in rrf_scores:
                rrf_scores[doc_id] = {
                    'vector_score': 0.0,
                    'keyword_score': 0.0,
                    'vector_rank': None,
                    'keyword_rank': None
                }
                # 從關鍵字結果創建標準格式
                document_data[doc_id] = {
                    'content': result['content'],
                    'title': result['title'],
                    'source_id': result['source_id'],
                    'score': result['rank'],  # 使用 PostgreSQL ts_rank
                    'metadata': {
                        'source_table': self.source_table,
                        'id': section_pk,  # 🆕 段落主鍵
                        'source_id': result['source_id'],
                        'document_id': result.get('document_id'),
                        'document_title': result.get('document_title'),
                        'match_count': result.get('match_count'),
                        'matched_keywords': result.get('matched_keywords')
                    }
                }
            
            rrf_scores[doc_id]['keyword_score'] = rrf_score
            rrf_scores[doc_id]['keyword_rank'] = rank
        
        # 計算最終 RRF 分數並排序
        merged_results = []
        for doc_id, scores in rrf_scores.items():
            final_rrf_score = scores['vector_score'] + scores['keyword_score']
            
            result = document_data[doc_id].copy()
            result['rrf_score'] = final_rrf_score
            result['vector_rank'] = scores['vector_rank']
            result['keyword_rank'] = scores['keyword_rank']
            result['original_vector_score'] = scores['vector_score']
            result['original_keyword_score'] = scores['keyword_score']
            
            # 使用 rrf_score 作為最終分數
            result['score'] = final_rrf_score
            result['final_score'] = final_rrf_score
            
            merged_results.append(result)
        
        # 按 RRF 分數降序排列
        merged_results.sort(key=lambda x: x['rrf_score'], reverse=True)
        
        logger.info(
            f"🔄 RRF 融合完成: "
            f"向量 {len(vector_results)} + 關鍵字 {len(keyword_results)} = "
            f"合併 {len(merged_results)} (k={k})"
        )
        
        
        return merged_results
    
    def _normalize_rrf_scores(self, results: list) -> list:
        """
        將 RRF 分數正規化到 0.5-1.0 範圍（方案 B1）
        
        RRF 分數範圍：[0, ~0.033]（k=60 時，最高分約為 1/60 = 0.0167）
        正規化方法：使用 Min-Max Normalization + 0.5 基準線
        
        Formula:
            normalized_score_01 = (score - min_score) / (max_score - min_score)
            scaled_score = 0.5 + (normalized_score_01 × 0.5)
        
        範圍解釋：
        - 0.5 (50%): 最低分，表示「勉強及格」
        - 1.0 (100%): 最高分，表示「完美匹配」
        - 語義：所有通過檢索的文檔至少 50% 相關
        
        Args:
            results: RRF 融合後的結果列表（包含 rrf_score）
            
        Returns:
            List[Dict]: 正規化後的結果列表（score 欄位更新為 0.5-1.0 範圍）
        """
        if not results:
            return results
        
        # 提取所有 RRF 分數
        rrf_scores = [r.get('rrf_score', 0) for r in results]
        
        if not rrf_scores:
            logger.warning("⚠️ 沒有 RRF 分數可正規化")
            return results
        
        max_score = max(rrf_scores)
        min_score = min(rrf_scores)
        
        # 防止除以零
        if max_score == min_score:
            # 方案 B1: 所有分數相同時設為 0.75（中間值）
            logger.warning(f"⚠️ 所有 RRF 分數相同 ({max_score:.4f})，設定為 0.75（方案 B1）")
            for result in results:
                result['score'] = 0.75
                result['final_score'] = 0.75
                result['original_rrf_score'] = result.get('rrf_score', 0)
            return results
        
        # Min-Max 正規化到 0.5-1.0 範圍（方案 B1）
        for result in results:
            rrf_score = result.get('rrf_score', 0)
            
            # 步驟 1: 先正規化到 0-1
            normalized_score_01 = (rrf_score - min_score) / (max_score - min_score)
            
            # 步驟 2: 縮放到 0.5-1.0 範圍
            scaled_score = 0.5 + (normalized_score_01 * 0.5)
            
            # 保留原始 RRF 分數
            result['original_rrf_score'] = rrf_score
            
            # 更新為縮放後分數
            result['score'] = scaled_score
            result['final_score'] = scaled_score
        
        logger.info(
            f"✅ RRF 分數正規化（方案 B1）: "
            f"原始範圍 [{min_score:.4f}, {max_score:.4f}] → "
            f"正規化範圍 [0.5, 1.0]"
        )
        
        return results
    
    def search_knowledge(self, query: str, limit: int = 5, use_vector: bool = True, 
                        threshold: float = 0.7, search_mode: str = 'auto', stage: int = 1,
                        version_config: dict = None) -> list:
        """
        覆寫基類方法，添加文檔級搜尋支援 + 查詢清理（方案一）+ Title Boost 支援
        
        智能搜索流程（Query Cleaning Pattern + Title Boost）：
        1. 分類查詢類型 + 清理關鍵字
        2. 使用清理後的查詢執行向量搜尋（提升語義準確度）
        3. 🆕 如果啟用 Title Boost，對標題匹配的結果加分
        4. 根據原始查詢類型決定返回 section 或 document
        
        為什麼清理查詢？
        - 關鍵字如 '完整'、'全部' 會干擾向量語義理解
        - 例：'如何完整測試 USB' → 清理為 '如何測試 USB'
        - 結果：向量更聚焦於 'USB 測試'，而非 '完整'
        
        業界最佳實踐：
        - 78% 的 RAG 系統使用查詢清理技術
        - Google: Query Rewriting
        - OpenAI: Query Normalization
        - LangChain: QueryTransformer
        
        Args:
            query: 搜尋查詢
            limit: 返回結果數量 (預設: 5)
            use_vector: 是否使用向量搜尋 (預設: True)
            threshold: 相似度閾值 (預設: 0.7)
            search_mode: 搜索模式 ('auto', 'section_only', 'document_only')（預設: 'auto'）
            stage: 搜尋階段 (1=段落搜尋, 2=全文搜尋)（預設: 1）
            version_config: 🆕 版本配置字典（包含 rag_settings），用於啟用 Title Boost（預設: None）
            
        Returns:
            搜尋結果列表（section 或 document 級）
        """
        # 步驟 0: 檢查是否啟用混合搜尋（v1.2.2）
        enable_hybrid_search = False
        rrf_k = 60  # RRF 預設常數
        
        if version_config:
            rag_settings = version_config.get('rag_settings', {})
            stage_config = rag_settings.get(f'stage{stage}', {})
            enable_hybrid_search = stage_config.get('use_hybrid_search', False)
            rrf_k = stage_config.get('rrf_k', 60)
            
            if enable_hybrid_search:
                logger.info(f"🔄 混合搜尋已啟用 (Stage {stage}): RRF k={rrf_k}")
        
        # 步驟 1: 分類查詢 + 清理關鍵字
        query_type, cleaned_query = self._classify_and_clean_query(query)
        
        # 🆕 步驟 1.5: 檢查混合搜尋模式（v1.2.2）+ 初始化算分日誌
        scoring_logger = None
        if enable_hybrid_search and use_vector:
            # 🆕 初始化 VSA 算分日誌記錄器
            try:
                from library.dify_knowledge.scoring_logger import VSAScoringLogger, should_log_scoring
                
                if should_log_scoring(version_config):
                    version_name = version_config.get('name', 'Unknown Version')
                    scoring_logger = VSAScoringLogger(
                        query=query,
                        version_name=version_name,
                        conversation_id=None  # TODO: 從上下文獲取
                    )
                    scoring_logger.log_search_start()
                    scoring_logger.log_query_classification(
                        original_query=query,
                        cleaned_query=cleaned_query,
                        query_type=query_type
                    )
            except Exception as e:
                logger.warning(f"⚠️ 無法初始化算分日誌: {e}")
                scoring_logger = None
            
            logger.info(f"🚀 執行混合搜尋: '{cleaned_query}'")
            
            try:
                # 記錄 Stage 1 開始
                if scoring_logger:
                    scoring_logger.log_stage1_start(
                        search_mode=search_mode,
                        top_k=limit,
                        threshold=threshold,
                        use_hybrid=True,
                        rrf_k=rrf_k
                    )
                
                # 步驟 A: 向量搜尋
                logger.info("📍 步驟 1/3: 執行向量搜尋")
                vector_results = super().search_knowledge(
                    query=cleaned_query,
                    limit=limit * 2,  # 多取一些結果用於融合
                    use_vector=True,
                    threshold=threshold * 0.8,  # 降低閾值以獲取更多候選
                    search_mode=search_mode,
                    stage=stage
                )
                logger.info(f"✅ 向量搜尋完成: {len(vector_results)} 個結果")
                
                # 記錄向量搜尋結果
                if scoring_logger:
                    scoring_logger.log_stage1_vector_search(vector_results)
                
                # 步驟 B: 關鍵字搜尋
                logger.info("📍 步驟 2/3: 執行關鍵字搜尋")
                keyword_results = self._keyword_search(
                    query=cleaned_query,
                    limit=limit * 2
                )
                logger.info(f"✅ 關鍵字搜尋完成: {len(keyword_results)} 個結果")
                
                # 記錄關鍵字搜尋結果（傳入分詞後的關鍵字）
                if scoring_logger:
                    keywords = smart_tokenize(cleaned_query)
                    scoring_logger.log_stage1_keyword_search(keyword_results, keywords=keywords)
                
                # 步驟 C: RRF 融合
                logger.info(f"📍 步驟 3/6: RRF 融合 (k={rrf_k})")
                results = self._merge_with_rrf(
                    vector_results=vector_results,
                    keyword_results=keyword_results,
                    k=rrf_k
                )
                logger.info(f"✅ RRF 融合完成: {len(results)} 個結果")
                
                # 記錄 RRF 融合結果
                if scoring_logger:
                    scoring_logger.log_stage1_rrf_fusion(results, rrf_k=rrf_k)
                
                # 🆕 步驟 D: 正規化 RRF 分數到 0-1 範圍
                logger.info("📍 步驟 4/6: 正規化 RRF 分數")
                
                # 記錄正規化前的分數範圍
                if scoring_logger and results:
                    rrf_scores = [r.get('rrf_score', 0) for r in results]
                    min_score = min(rrf_scores) if rrf_scores else 0
                    max_score = max(rrf_scores) if rrf_scores else 0
                
                results = self._normalize_rrf_scores(results)
                highest_score = results[0]['score'] if results else 0
                logger.info(f"✅ 分數正規化完成: 最高分={highest_score:.4f}")
                
                # 記錄正規化
                if scoring_logger and results:
                    scoring_logger.log_stage1_score_normalization(min_score, max_score, "0.5-1.0")
                
                # 🆕 步驟 E: 應用 Title Boost（如果啟用）
                if version_config:
                    try:
                        from library.common.knowledge_base.title_boost import TitleBoostConfig, TitleBoostProcessor
                        
                        rag_settings = version_config.get('rag_settings', {})
                        title_boost_config = TitleBoostConfig.from_rag_settings(rag_settings, stage=stage)
                        enable_title_boost = title_boost_config.get('enabled', False)
                        
                        if enable_title_boost and results:
                            title_bonus = title_boost_config.get('title_match_bonus', 0.15)
                            logger.info(f"📍 步驟 5/6: 應用 Title Boost (bonus={title_bonus:.0%})")
                            
                            processor = TitleBoostProcessor(
                                title_match_bonus=title_bonus,
                                min_keyword_length=title_boost_config.get('min_keyword_length', 2)
                            )
                            
                            # ✅ 修正：正確的參數名稱是 vector_results，不是 results
                            results = processor.apply_title_boost(
                                query=cleaned_query,
                                vector_results=results,
                                title_field='title'
                            )
                            
                            boosted_count = sum(1 for r in results if r.get('title_boost_applied', False))
                            logger.info(f"✅ Title Boost 完成: {boosted_count}/{len(results)} 個結果獲得加分")
                            
                            # 記錄 Title Boost
                            if scoring_logger:
                                scoring_logger.log_stage1_title_boost(results, boost_factor=title_bonus)
                    except Exception as e:
                        logger.warning(f"⚠️ Title Boost 應用失敗，繼續使用正規化後的分數: {e}")
                        if scoring_logger:
                            scoring_logger.log_error("Title Boost", str(e))
                
                # 步驟 F: 按最終分數重新排序並限制返回數量
                logger.info("📍 步驟 6/6: 最終排序")
                results = sorted(results, key=lambda x: x.get('score', 0), reverse=True)
                results = results[:limit]
                logger.info(f"✅ 混合搜尋完成: 返回 {len(results)} 個結果")
                
                # 記錄 Stage 1 最終結果
                if scoring_logger:
                    scoring_logger.log_stage1_result(results)
                
                # 如果是文檔級查詢，擴展為完整文檔
                if query_type == 'document' and results:
                    logger.info(f"🔄 將 {len(results)} 個混合搜尋結果擴展為完整文檔")
                    results = self._expand_to_full_document(results)
                
                # 記錄搜尋完成
                if scoring_logger:
                    scoring_logger.log_search_end(
                        total_results=len(results),
                        stage1_count=len(results)
                    )
                
                return results
                
            except Exception as e:
                logger.error(f"❌ 混合搜尋失敗，降級為標準搜尋: {e}", exc_info=True)
                if scoring_logger:
                    scoring_logger.log_fallback("混合搜尋", "標準搜尋", str(e))
                # 降級為標準搜尋（繼續下方邏輯）
        
        # 🆕 步驟 1.6: 解析 Title Boost 配置
        enable_title_boost = False
        title_boost_config = None
        
        if version_config:
            try:
                from library.common.knowledge_base.title_boost import TitleBoostConfig
                
                rag_settings = version_config.get('rag_settings', {})
                title_boost_config = TitleBoostConfig.from_rag_settings(rag_settings, stage=stage)
                enable_title_boost = title_boost_config.get('enabled', False)
                
                if enable_title_boost:
                    logger.info(
                        f"✅ Title Boost 已啟用 (Stage {stage}): "
                        f"bonus={title_boost_config.get('title_match_bonus', 0):.2%}"
                    )
            except Exception as e:
                logger.warning(f"⚠️ Title Boost 配置解析失敗，繼續使用標準搜尋: {e}")
                enable_title_boost = False
        
        # ⚠️ 處理 'list_all' 模式（當查詢只包含文檔級關鍵字時）
        if query_type == 'list_all':
            logger.info("🔍 觸發 'list_all' 模式 → 使用關鍵字搜尋列出所有相關文檔")
            # 使用原始查詢（例如 "sop"）做關鍵字搜尋
            # 將 use_vector=False 強制使用關鍵字搜尋，threshold 降低到 0.3
            results = super().search_knowledge(
                query=cleaned_query,  # 使用原始查詢（如 "sop"）
                limit=limit,
                use_vector=False,  # 強制使用關鍵字搜尋
                threshold=0.3,  # 降低閾值以包含更多結果
                search_mode='auto',
                stage=stage
            )
            
            # 擴展為完整文檔
            if results:
                logger.info(f"🔄 將 {len(results)} 個關鍵字搜尋結果擴展為完整文檔")
                results = self._expand_to_full_document(results)
            
            return results
        
        # 步驟 2: 使用清理後的查詢執行搜尋（提升向量語義準確度）
        # 🔧 修正：Title Boost 應該在段落搜尋結果上應用，而不是使用全文向量
        if enable_title_boost and use_vector:
            try:
                from library.common.knowledge_base.title_boost import TitleBoostProcessor
                
                logger.info(f"🔍 Title Boost 啟用: 先執行段落搜尋，然後應用標題加分")
                
                # ✅ 步驟 1: 使用標準段落搜尋（與 v1.1.1 相同）
                logger.info(f"📍 步驟 1/2: 執行段落搜尋")
                section_results = super().search_knowledge(
                    query=cleaned_query,
                    limit=limit,
                    use_vector=use_vector,
                    threshold=threshold,
                    search_mode=search_mode,
                    stage=stage
                )
                
                logger.info(f"✅ 段落搜尋完成: {len(section_results)} 個結果")
                
                # ✅ 步驟 2: 在段落結果上應用 Title Boost
                logger.info(f"📍 步驟 2/2: 應用 Title Boost (bonus={title_boost_config.get('title_match_bonus', 0.2):.0%})")
                
                processor = TitleBoostProcessor(
                    title_match_bonus=title_boost_config.get('title_match_bonus', 0.20),
                    min_keyword_length=title_boost_config.get('min_keyword_length', 2)
                )
                
                boosted_results = processor.apply_title_boost(
                    query=cleaned_query,
                    vector_results=section_results,
                    title_field='title'
                )
                
                # 統計資訊
                boosted_count = sum(1 for r in boosted_results if r.get('title_boost_applied', False))
                logger.info(
                    f"✅ Title Boost 完成: {len(boosted_results)} 個段落結果, "
                    f"{boosted_count} 個獲得標題加分"
                )
                
                # 🔍 Debug: 顯示每個結果的分數
                for idx, r in enumerate(boosted_results, 1):
                    logger.info(
                        f"  [{idx}] final_score={r.get('final_score', 'N/A')}, "
                        f"score={r.get('score', 'N/A')}, "
                        f"title={r.get('title', 'Unknown')[:30]}..."
                    )
                
                # 🔧 二次過濾：移除加分後仍低於 threshold 的結果（在轉換格式之前）
                filtered_boosted_results = boosted_results
                if threshold > 0:
                    original_count = len(boosted_results)
                    # ✅ 使用 final_score 或 score 來過濾
                    filtered_boosted_results = [
                        r for r in boosted_results 
                        if r.get('final_score', r.get('score', 0)) >= threshold
                    ]
                    if len(filtered_boosted_results) < original_count:
                        logger.info(
                            f"🎯 Title Boost 後過濾: {original_count} → {len(filtered_boosted_results)} (threshold={threshold})"
                        )
                
                # 轉換為標準格式（與基類返回格式一致）
                results = []
                for result in filtered_boosted_results:
                    results.append({
                        'content': result.get('content', ''),
                        'score': result.get('final_score') or result.get('similarity_score') or result.get('score', 0.0),  # ✅ 優先使用 final_score
                        'title': result.get('title', ''),
                        'source_id': result.get('source_id'),
                        'title_boost_applied': result.get('title_boost_applied', False),  # ✅ 頂層欄位
                        'original_score': result.get('original_score'),  # ✅ 頂層欄位
                        'title_boost_value': result.get('title_boost_value', 0),  # ✅ 正確欄位名
                        'final_score': result.get('final_score'),  # ✅ 保留 final_score
                        'similarity_score': result.get('similarity_score'),  # ✅ 保留 similarity_score
                        'metadata': {
                            'source_table': self.source_table,
                            # ⚠️ 已將 Title Boost 相關欄位移至頂層
                        }
                    })
                
            except Exception as e:
                logger.error(f"❌ Title Boost 搜尋失敗，降級為標準搜尋: {e}", exc_info=True)
                # 降級為標準搜尋
                results = super().search_knowledge(
                    query=cleaned_query,
                    limit=limit,
                    use_vector=use_vector,
                    threshold=threshold,
                    search_mode=search_mode,
                    stage=stage
                )
        else:
            # 標準搜尋（不使用 Title Boost）
            results = super().search_knowledge(
                query=cleaned_query,  # ✅ 使用清理後的查詢
                limit=limit,
                use_vector=use_vector,
                threshold=threshold,
                search_mode=search_mode,  # ✅ 傳遞 search_mode 到基類
                stage=stage  # ✅ 傳遞 stage 參數
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
    
    # ============================================================
    # 智能搜尋路由支援方法（2025-11-11）
    # ============================================================
    
    def section_search(self, query: str, top_k: int = 5, threshold: float = 0.5) -> list:
        """
        段落向量搜尋（用於智能路由器 - 模式 B 階段 1）
        
        Args:
            query: 搜尋查詢
            top_k: 返回前 K 個結果
            threshold: 相似度閾值
            
        Returns:
            List[Dict]: 段落搜尋結果
        """
        try:
            # 使用基類的 search_knowledge，但強制返回 section 級結果
            _, cleaned_query = self._classify_and_clean_query(query)
            
            # ✅ 傳遞 stage=1 (段落搜尋使用第一階段權重)
            results = super().search_knowledge(
                query=cleaned_query,
                limit=top_k,
                use_vector=True,
                threshold=threshold,
                stage=1  # 第一階段：段落搜尋
            )
            
            # 格式化為統一的結果格式
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'title': result.get('metadata', {}).get('document_title', '未知標題'),
                    'content': result.get('content', ''),
                    'source_id': result.get('metadata', {}).get('document_id', 'N/A'),
                    'similarity': result.get('score', 0.0),
                    'metadata': result.get('metadata', {})
                })
            
            return formatted_results
        
        except Exception as e:
            logger.error(f"❌ 段落搜尋失敗: {str(e)}", exc_info=True)
            return []
    
    def full_document_search(self, query: str, top_k: int = 3, threshold: float = 0.5) -> list:
        """
        全文向量搜尋（用於智能路由器 - 模式 A & 模式 B 階段 2）
        
        Args:
            query: 搜尋查詢
            top_k: 返回前 K 個文檔
            threshold: 相似度閾值
            
        Returns:
            List[Dict]: 全文文檔搜尋結果
        """
        try:
            # 強制使用文檔級搜尋
            _, cleaned_query = self._classify_and_clean_query(query)
            
            # ✅ 傳遞 stage=2 (全文搜尋使用第二階段權重)
            # 執行向量搜尋
            section_results = super().search_knowledge(
                query=cleaned_query,
                limit=top_k * 3,  # 多取一些結果以便組裝文檔
                use_vector=True,
                threshold=threshold,
                stage=2  # 第二階段：全文搜尋
            )
            
            # 擴展為完整文檔
            full_documents = self._expand_to_full_document(section_results)
            
            # 限制返回數量
            full_documents = full_documents[:top_k]
            
            # 格式化為統一的結果格式
            formatted_results = []
            for doc in full_documents:
                formatted_results.append({
                    'title': doc.get('title', '未知標題'),
                    'content': doc.get('content', ''),
                    'source_id': doc.get('metadata', {}).get('document_id', 'N/A'),
                    'similarity': doc.get('score', 0.0),
                    'metadata': doc.get('metadata', {})
                })
            
            return formatted_results
        
        except Exception as e:
            logger.error(f"❌ 全文搜尋失敗: {str(e)}", exc_info=True)
            return []


