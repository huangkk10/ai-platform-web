"""
知識庫搜索服務基礎類別
======================

提供統一的搜索邏輯，包括向量搜索和關鍵字搜索。
"""

import logging
from abc import ABC

logger = logging.getLogger(__name__)


class BaseKnowledgeBaseSearchService(ABC):
    """
    知識庫搜索服務基礎類別
    
    子類需要設定的屬性：
    - model_class: Django Model 類別
    - source_table: 資料來源表名
    - default_search_fields: 預設搜索欄位列表
    
    使用範例：
    ```python
    class ProtocolGuideSearchService(BaseKnowledgeBaseSearchService):
        model_class = ProtocolGuide
        source_table = 'protocol_guide'
        default_search_fields = ['title', 'content', 'protocol_name']
    ```
    """
    
    # 子類必須設定這些屬性
    model_class = None
    source_table = None
    default_search_fields = ['title', 'content']
    
    def __init__(self):
        self.logger = logger
        self._validate_attributes()
    
    def _validate_attributes(self):
        """驗證必要屬性是否已設定"""
        if self.model_class is None:
            raise NotImplementedError(f"{self.__class__.__name__} must define 'model_class' attribute")
        if self.source_table is None:
            raise NotImplementedError(f"{self.__class__.__name__} must define 'source_table' attribute")
    
    def search_knowledge(self, query, limit=5, use_vector=True, threshold=0.7, search_mode='auto', stage=1):
        """
        搜索知識庫（支援兩階段權重配置）
        
        智能搜索策略：
        1. 優先嘗試向量搜索
        2. 如果向量搜索失敗或結果不足，使用關鍵字搜索
        3. 合併並去重結果
        
        Args:
            query: 查詢字串
            limit: 返回結果數量上限
            use_vector: 是否使用向量搜索
            threshold: 相似度閾值 (0.0 ~ 1.0)，來自 Dify Studio 設定
            search_mode: 搜索模式（傳遞給 search_with_vectors）
                - 'auto': 自動模式（預設）
                - 'section_only': 只搜索段落
                - 'document_only': 只搜索文檔
            stage: 搜尋階段 (1=段落搜尋, 2=全文搜尋)
        """
        try:
            results = []
            
            # 嘗試向量搜索
            if use_vector:
                try:
                    vector_results = self.search_with_vectors(query, limit, threshold, search_mode, stage)
                    if vector_results:
                        results.extend(vector_results)
                        self.logger.info(f"向量搜索返回 {len(vector_results)} 條結果 (threshold={threshold}, mode={search_mode}, stage={stage})")
                except Exception as e:
                    self.logger.warning(f"向量搜索失敗: {str(e)}")
            
            # 如果結果不足，使用關鍵字搜索補充
            if len(results) < limit:
                remaining = limit - len(results)
                # 關鍵字搜索使用較低的 threshold (threshold * 0.5)
                keyword_threshold = max(threshold * 0.5, 0.3)
                keyword_results = self.search_with_keywords(query, remaining, keyword_threshold)
                
                # 去重（避免重複的結果）
                existing_ids = {r.get('metadata', {}).get('id') for r in results}
                for kr in keyword_results:
                    kr_id = kr.get('metadata', {}).get('id')
                    if kr_id not in existing_ids:
                        results.append(kr)
                        existing_ids.add(kr_id)
                
                self.logger.info(f"關鍵字搜索補充 {len(keyword_results)} 條結果 (threshold={keyword_threshold:.2f})")
            
            return results[:limit]
            
        except Exception as e:
            self.logger.error(f"搜索失敗: {str(e)}")
            return []
    
    def search_with_vectors(self, query, limit=5, threshold=0.7, search_mode='auto', stage=1):
        """
        使用向量進行搜索 (通用實現 - 已重構，支援顯式搜索模式和兩階段權重)
        
        ✨ 重構亮點：
        - 優先使用段落向量搜尋（更精準）
        - 備用整篇文檔向量搜尋
        - ✅ 支援顯式 search_mode 參數（直接控制搜索類型）
        - ✅ 支援兩階段權重配置（stage 1=段落, stage 2=全文）
        - 所有知識庫共用此實現
        - 子類無需覆寫，除非有特殊邏輯
        - ✅ threshold 可完全參數化，來自 Dify Studio
        
        子類可以通過覆寫 _get_item_content() 來自定義內容格式化
        
        Args:
            query: 查詢字串
            limit: 返回結果數量上限
            threshold: 相似度閾值 (0.0 ~ 1.0)，來自 Dify Studio 設定
            search_mode: 搜索模式（顯式控制）
                - 'auto': 自動模式（段落優先，允許降級，預設）
                - 'section_only': 只搜索段落（不降級）
                - 'document_only': 只搜索文檔（跳過段落）
                - 'section_preferred': 優先段落（同 auto）
                - 'document_preferred': 優先文檔
            stage: 搜尋階段 (1=段落搜尋, 2=全文搜尋)
        """
        try:
            # === 模式 1：只搜索文檔（顯式指定）===
            if search_mode == 'document_only':
                self.logger.info(f"🎯 顯式文檔搜索模式 (search_mode='document_only', threshold={threshold}, stage={stage})")
                from .vector_search_helper import search_with_vectors_generic
                
                # 使用降級閾值
                doc_threshold = max(threshold * 0.85, 0.5)
                
                results = search_with_vectors_generic(
                    query=query,
                    model_class=self.model_class,
                    source_table=self.source_table,
                    limit=limit,
                    threshold=doc_threshold,
                    use_1024=True,
                    content_formatter=self._get_item_content,
                    stage=stage  # ✅ 傳遞 stage 參數
                )
                
                self.logger.info(f"📄 文檔搜索返回 {len(results)} 個結果 (threshold={doc_threshold:.2f}, stage={stage})")
                return results
            
            # === 模式 2：只搜索段落（不降級）===
            elif search_mode == 'section_only':
                self.logger.info(f"🎯 顯式段落搜索模式 (search_mode='section_only', threshold={threshold}, stage={stage})")
                from .section_search_service import SectionSearchService
                section_service = SectionSearchService()
                
                section_results = section_service.search_sections(
                    query=query,
                    source_table=self.source_table,
                    limit=limit,
                    threshold=threshold,
                    stage=stage  # ✅ 傳遞 stage 參數
                )
                
                if section_results:
                    self.logger.info(f"✅ 段落搜索成功: {len(section_results)} 個結果 (stage={stage})")
                    return self._format_section_results_to_standard(section_results, limit)
                else:
                    self.logger.info(f"⚠️ 段落搜索無結果（不降級）")
                    return []
            
            # === 模式 3：自動模式（段落優先，允許降級）===
            else:  # 'auto', 'section_preferred'
                self.logger.info(f"🎯 自動搜索模式 (search_mode='{search_mode}', 優先段落, stage={stage})")
                
                # 🎯 優先使用段落向量搜尋
                try:
                    from .section_search_service import SectionSearchService
                    section_service = SectionSearchService()
                    
                    section_results = section_service.search_sections(
                        query=query,
                        source_table=self.source_table,
                        limit=limit,
                        threshold=threshold,  # ✅ 使用傳入的 threshold
                        stage=stage  # ✅ 傳遞 stage 參數
                    )
                    
                    if section_results:
                        self.logger.info(f"✅ 段落向量搜尋成功: {len(section_results)} 個結果 (threshold={threshold}, stage={stage})")
                        # 將段落結果轉換為標準格式
                        return self._format_section_results_to_standard(section_results, limit)
                except Exception as section_error:
                    self.logger.warning(f"⚠️ 段落向量搜尋失敗，使用整篇文檔搜尋: {str(section_error)}")
                
                # 備用：整篇文檔向量搜尋（使用稍低的 threshold）
                from .vector_search_helper import search_with_vectors_generic
                
                # 文檔搜索使用稍低的 threshold (threshold * 0.85)
                doc_threshold = max(threshold * 0.85, 0.5)
                
                results = search_with_vectors_generic(
                    query=query,
                    model_class=self.model_class,
                    source_table=self.source_table,
                    limit=limit,
                    threshold=doc_threshold,  # ✅ 使用動態計算的 threshold
                    use_1024=True,
                    content_formatter=self._get_item_content,
                    stage=stage  # ✅ 傳遞 stage 參數
                )
                
                self.logger.info(f"📄 整篇文檔向量搜尋返回 {len(results)} 個結果 (threshold={doc_threshold:.2f}, stage={stage})")
                return results
            
        except Exception as e:
            self.logger.error(f"向量搜索錯誤: {str(e)}")
            return []
    
    def search_with_keywords(self, query, limit=5, threshold=0.3):
        """
        使用關鍵字進行搜索（✨ 已改進：智能分數計算）
        
        改進內容：
        - ✅ 根據匹配位置、頻率、欄位權重計算真實相似度
        - ✅ 標題匹配：0.7 ~ 1.0
        - ✅ 內容匹配：0.3 ~ 0.6
        - ✅ 支援任意 threshold 過濾
        
        基於資料庫的關鍵字搜索
        
        Args:
            query: 查詢字串
            limit: 返回結果數量上限
            threshold: 相似度閾值 (0.0 ~ 1.0)，通常比向量搜索低
        """
        try:
            from django.db.models import Q
            
            # 構建搜索條件
            q_objects = Q()
            for field in self.default_search_fields:
                if hasattr(self.model_class, field):
                    q_objects |= Q(**{f"{field}__icontains": query})
            
            # 執行搜索（查詢更多結果以便排序後選擇 top-k）
            items = self.model_class.objects.filter(q_objects)[:limit * 3]
            
            self.logger.debug(f"🔍 關鍵字搜索: 查詢 '{query}' 返回 {len(items)} 個匹配項")
            
            # 計算每個結果的相似度分數並過濾
            results = []
            for item in items:
                # ✅ 使用智能分數計算
                score = self._calculate_keyword_score(item, query)
                
                # ✅ 使用傳入的 threshold 過濾
                if score >= threshold:
                    result = self._format_item_to_result(item, score=score)
                    results.append(result)
            
            # 按分數降序排序
            results.sort(key=lambda x: x.get('score', 0), reverse=True)
            
            # 返回 top-k 結果
            top_results = results[:limit]
            
            if top_results:
                self.logger.info(
                    f"📊 關鍵字搜索結果: {len(top_results)} 條 (threshold={threshold:.2f}) | "
                    f"分數範圍: {top_results[0].get('score', 0):.2f} ~ {top_results[-1].get('score', 0):.2f}"
                )
            else:
                self.logger.info(f"📊 關鍵字搜索: 無結果通過 threshold={threshold:.2f}")
            
            return top_results
            
        except Exception as e:
            self.logger.error(f"❌ 關鍵字搜索錯誤: {str(e)}")
            return []
    
    def _format_section_results_to_standard(self, section_results, limit=5):
        """
        將段落搜尋結果轉換為標準的 Dify 知識庫格式
        
        段落搜尋返回多個段落，需要：
        1. 按 source_id 分組
        2. 合併同一文檔的段落
        3. 保留最高相似度
        """
        try:
            # 按文檔 ID 分組段落
            doc_sections = {}
            for section in section_results:
                doc_id = section['source_id']
                if doc_id not in doc_sections:
                    doc_sections[doc_id] = {
                        'sections': [],
                        'max_similarity': section['similarity']
                    }
                doc_sections[doc_id]['sections'].append(section)
                if section['similarity'] > doc_sections[doc_id]['max_similarity']:
                    doc_sections[doc_id]['max_similarity'] = section['similarity']
            
            # 獲取完整文檔資訊並格式化
            results = []
            for doc_id, data in sorted(doc_sections.items(), key=lambda x: x[1]['max_similarity'], reverse=True)[:limit]:
                try:
                    item = self.model_class.objects.get(id=doc_id)
                    
                    # 組合段落內容（只顯示相關段落）
                    section_contents = []
                    for section in data['sections'][:3]:  # 最多顯示 3 個相關段落
                        heading = section.get('heading_text', '')
                        content = section.get('content', '')
                        section_id = section.get('section_id', '')
                        
                        # ✅ 修復：如果段落內容為空（章節標題），查詢並展開子段落
                        if not content and section_id:
                            try:
                                from django.db import connection
                                with connection.cursor() as cursor:
                                    # 查詢子段落（parent_section_id = 當前 section_id）
                                    cursor.execute("""
                                        SELECT section_id, heading_text, content
                                        FROM document_section_embeddings
                                        WHERE source_table = %s 
                                          AND source_id = %s
                                          AND parent_section_id = %s
                                        ORDER BY section_id
                                        LIMIT 10
                                    """, [self.source_table, doc_id, section_id])
                                    
                                    children_rows = cursor.fetchall()
                                    
                                if children_rows:
                                    self.logger.info(f"  📑 段落 '{heading}' 無內容，展開 {len(children_rows)} 個子段落")
                                    # 添加章節標題
                                    if heading:
                                        section_contents.append(f"## {heading}")
                                    # 添加所有子段落內容
                                    for child_section_id, child_heading, child_content in children_rows:
                                        if child_content:  # 只添加有內容的子段落
                                            if child_heading:
                                                section_contents.append(f"### {child_heading}\n{child_content}")
                                            else:
                                                section_contents.append(child_content)
                                else:
                                    # 沒有子段落，保留原邏輯
                                    if heading:
                                        section_contents.append(f"## {heading}\n{content}")
                                    else:
                                        section_contents.append(content)
                            except Exception as child_error:
                                self.logger.warning(f"查詢子段落失敗: {str(child_error)}")
                                # 回退到原邏輯
                                if heading:
                                    section_contents.append(f"## {heading}\n{content}")
                                else:
                                    section_contents.append(content)
                        else:
                            # 正常段落：有內容
                            if heading:
                                section_contents.append(f"## {heading}\n{content}")
                            else:
                                section_contents.append(content)
                    
                    combined_content = "\n\n".join(section_contents)
                    
                    # ✅ 修復：只添加段落範圍內的圖片資訊
                    if hasattr(item, 'images'):
                        section_image_ids = self._extract_image_ids_from_sections(data['sections'][:3])
                        if section_image_ids:
                            images_info = self._get_section_images_summary(item, section_image_ids)
                            if images_info:
                                combined_content += f"\n\n{images_info}"
                    
                    result = {
                        'content': combined_content,
                        'score': data['max_similarity'],
                        'title': getattr(item, 'title', ''),
                        'metadata': {
                            'id': doc_id,
                            'sections_found': len(data['sections']),
                            'max_similarity': data['max_similarity']
                        }
                    }
                    results.append(result)
                except self.model_class.DoesNotExist:
                    self.logger.warning(f"文檔 {doc_id} 不存在")
                    continue
            
            return results
            
        except Exception as e:
            self.logger.error(f"段落結果轉換錯誤: {str(e)}")
            return []
    
    def _extract_image_ids_from_sections(self, sections):
        """
        從段落內容中提取圖片 ID
        
        搜尋段落內容中的圖片引用，格式如：
        - [IMG:35]
        - **[IMG:46] 2.jpg**
        - 如圖所示，**[IMG:47] 3.jpg**
        
        Returns:
            set: 圖片 ID 集合
        """
        import re
        image_ids = set()
        
        for section in sections:
            content = section.get('content', '')
            # 使用正則表達式提取所有 [IMG:數字] 格式
            matches = re.findall(r'\[IMG:(\d+)\]', content)
            image_ids.update(int(img_id) for img_id in matches)
        
        return image_ids
    
    def _get_section_images_summary(self, item, image_ids):
        """
        獲取指定圖片的摘要資訊（只包含段落中引用的圖片）
        
        Args:
            item: 文檔對象
            image_ids: 圖片 ID 集合
            
        Returns:
            str: 圖片摘要資訊
        """
        try:
            # 獲取指定 ID 的圖片
            images = item.images.filter(id__in=image_ids, is_active=True).order_by('display_order')
            
            if not images.exists():
                return ""
            
            summaries = []
            for img in images:
                parts = []
                if img.title:
                    parts.append(f"{img.title}")
                if img.description:
                    parts.append(f"{img.description}")
                if img.filename:
                    parts.append(f"({img.filename})")
                
                if parts:
                    summaries.append(f"**[IMG:{img.id}]** {' '.join(parts)}")
                else:
                    summaries.append(f"**[IMG:{img.id}]**")
            
            if summaries:
                return f"> 相關圖片說明：\n> " + "\n> ".join(summaries)
            return ""
            
        except Exception as e:
            self.logger.warning(f"獲取段落圖片摘要失敗: {str(e)}")
            return ""
    
    def _format_search_results(self, raw_results):
        """
        格式化搜索結果為統一格式
        """
        formatted_results = []
        
        for result in raw_results:
            formatted_results.append({
                'content': result.get('content', ''),
                'score': result.get('score', 0.0),
                'title': result.get('title', ''),
                'metadata': result.get('metadata', {})
            })
        
        return formatted_results
    
    def _calculate_keyword_score(self, item, query):
        """
        計算關鍵字匹配的相似度分數
        
        評分邏輯：
        1. 標題完全匹配：1.0
        2. 標題部分匹配：0.7 ~ 0.95（根據位置）
        3. 內容開頭匹配：0.5 ~ 0.6
        4. 內容中間匹配：0.3 ~ 0.5
        5. 內容末尾匹配：0.3 ~ 0.4
        
        考慮因素：
        - 匹配位置（越早出現越相關）
        - 匹配次數（出現越多越相關，但有上限）
        - 匹配欄位（標題 > 內容）
        
        Args:
            item: 資料庫記錄對象
            query: 查詢字串
            
        Returns:
            float: 相似度分數 (0.3 ~ 1.0)
        """
        try:
            query_lower = query.lower().strip()
            if not query_lower:
                return 0.3
            
            max_score = 0.0
            
            # === 1. 檢查標題匹配 ===
            title = getattr(item, 'title', '').lower()
            if title and query_lower in title:
                # 完全匹配
                if query_lower == title.strip():
                    max_score = max(max_score, 1.0)
                    self.logger.debug(f"✅ 標題完全匹配: '{item.title}' | 分數: 1.0")
                else:
                    # 部分匹配 - 根據位置計算
                    position = title.find(query_lower)
                    title_length = len(title)
                    count = title.count(query_lower)
                    
                    # 位置因素 (0.0 ~ 1.0)：越早出現越相關
                    position_factor = 1.0 - (position / title_length) if title_length > 0 else 0.5
                    
                    # 密度因素 (最多 +0.2)
                    density_bonus = min(count * 0.05, 0.2)
                    
                    # 標題匹配基礎分 0.7，加上位置和密度加成
                    title_score = 0.7 + (position_factor * 0.25) + density_bonus
                    max_score = max(max_score, min(title_score, 0.95))
                    
                    self.logger.debug(
                        f"✅ 標題部分匹配: '{item.title[:50]}...' | "
                        f"位置: {position}/{title_length} | 次數: {count} | 分數: {title_score:.2f}"
                    )
            
            # === 2. 檢查內容匹配 ===
            content = getattr(item, 'content', '').lower()
            if content and query_lower in content:
                position = content.find(query_lower)
                content_length = len(content)
                count = content.count(query_lower)
                
                # 位置因素 (0.0 ~ 1.0)
                position_factor = 1.0 - (position / content_length) if content_length > 0 else 0.5
                
                # 密度因素 (最多 +0.3)
                density_bonus = min(count * 0.05, 0.3)
                
                # 內容匹配基礎分 0.3，加上位置和密度加成
                content_score = 0.3 + (position_factor * 0.2) + density_bonus
                
                # 內容匹配最高 0.6（避免超過標題匹配）
                content_score = min(content_score, 0.6)
                
                # 如果沒有標題匹配，才使用內容分數
                if max_score == 0.0:
                    max_score = content_score
                
                self.logger.debug(
                    f"📄 內容匹配: '{item.title[:50]}...' | "
                    f"位置: {position}/{content_length} | 次數: {count} | 分數: {content_score:.2f}"
                )
            
            # === 3. 返回最終分數 ===
            final_score = max(max_score, 0.3)  # 至少 0.3（有匹配才會進這個函數）
            
            self.logger.debug(f"🎯 最終分數: {final_score:.2f} | 文檔: '{getattr(item, 'title', 'Unknown')[:50]}...'")
            
            return final_score
            
        except Exception as e:
            self.logger.error(f"❌ 分數計算失敗: {str(e)}")
            return 0.3  # 錯誤時返回最低分
    
    def _format_item_to_result(self, item, score=None):
        """
        將資料庫記錄格式化為搜索結果
        
        Args:
            item: 資料庫記錄對象
            score: 相似度分數（可選）。如果未提供，將使用預設值 0.5
        """
        return {
            'content': self._get_item_content(item),
            'score': score if score is not None else 0.5,
            'title': getattr(item, 'title', str(item)),
            'metadata': {
                'id': item.id,
                'created_at': item.created_at.isoformat() if hasattr(item, 'created_at') else None,
                'updated_at': item.updated_at.isoformat() if hasattr(item, 'updated_at') else None,
            }
        }
    
    def _get_item_content(self, item):
        """
        獲取記錄的搜索內容
        
        子類可以覆寫此方法來自定義內容獲取邏輯
        """
        if hasattr(item, 'get_search_content'):
            return item.get_search_content()
        elif hasattr(item, 'content'):
            return item.content
        else:
            return str(item)
