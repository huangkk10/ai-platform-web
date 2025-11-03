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
    
    def search_knowledge(self, query, limit=5, use_vector=True):
        """
        搜索知識庫
        
        智能搜索策略：
        1. 優先嘗試向量搜索
        2. 如果向量搜索失敗或結果不足，使用關鍵字搜索
        3. 合併並去重結果
        """
        try:
            results = []
            
            # 嘗試向量搜索
            if use_vector:
                try:
                    vector_results = self.search_with_vectors(query, limit)
                    if vector_results:
                        results.extend(vector_results)
                        self.logger.info(f"向量搜索返回 {len(vector_results)} 條結果")
                except Exception as e:
                    self.logger.warning(f"向量搜索失敗: {str(e)}")
            
            # 如果結果不足，使用關鍵字搜索補充
            if len(results) < limit:
                remaining = limit - len(results)
                keyword_results = self.search_with_keywords(query, remaining)
                
                # 去重（避免重複的結果）
                existing_ids = {r.get('metadata', {}).get('id') for r in results}
                for kr in keyword_results:
                    kr_id = kr.get('metadata', {}).get('id')
                    if kr_id not in existing_ids:
                        results.append(kr)
                        existing_ids.add(kr_id)
                
                self.logger.info(f"關鍵字搜索補充 {len(keyword_results)} 條結果")
            
            return results[:limit]
            
        except Exception as e:
            self.logger.error(f"搜索失敗: {str(e)}")
            return []
    
    def search_with_vectors(self, query, limit=5):
        """
        使用向量進行搜索 (通用實現 - 已重構)
        
        ✨ 重構亮點：
        - 優先使用段落向量搜尋（更精準）
        - 備用整篇文檔向量搜尋
        - 所有知識庫共用此實現
        - 子類無需覆寫，除非有特殊邏輯
        
        子類可以通過覆寫 _get_item_content() 來自定義內容格式化
        """
        try:
            # 🎯 優先使用段落向量搜尋
            try:
                from .section_search_service import SectionSearchService
                section_service = SectionSearchService()
                
                section_results = section_service.search_sections(
                    query=query,
                    source_table=self.source_table,
                    limit=limit,
                    threshold=0.7  # 段落搜尋閾值（提高精準度，避免混到其他資料）
                )
                
                if section_results:
                    self.logger.info(f"✅ 段落向量搜尋成功: {len(section_results)} 個結果")
                    # 將段落結果轉換為標準格式
                    return self._format_section_results_to_standard(section_results, limit)
            except Exception as section_error:
                self.logger.warning(f"⚠️ 段落向量搜尋失敗，使用整篇文檔搜尋: {str(section_error)}")
            
            # 備用：整篇文檔向量搜尋
            from .vector_search_helper import search_with_vectors_generic
            
            results = search_with_vectors_generic(
                query=query,
                model_class=self.model_class,
                source_table=self.source_table,
                limit=limit,
                threshold=0.6,  # 備用方案也要有品質保證，避免不相關內容
                use_1024=True,
                content_formatter=self._get_item_content
            )
            
            self.logger.info(f"📄 整篇文檔向量搜尋返回 {len(results)} 個結果")
            return results
            
        except Exception as e:
            self.logger.error(f"向量搜索錯誤: {str(e)}")
            return []
    
    def search_with_keywords(self, query, limit=5):
        """
        使用關鍵字進行搜索（✨ 已改進：智能分數計算）
        
        改進內容：
        - ✅ 根據匹配位置、頻率、欄位權重計算真實相似度
        - ✅ 標題匹配：0.7 ~ 1.0
        - ✅ 內容匹配：0.3 ~ 0.6
        - ✅ 支援任意 threshold 過濾
        
        基於資料庫的關鍵字搜索
        """
        try:
            from django.db.models import Q
            
            # 構建搜索條件
            q_objects = Q()
            for field in self.default_search_fields:
                if hasattr(self.model_class, field):
                    q_objects |= Q(**{f"{field}__icontains": query})
            
            # 執行搜索（查詢更多結果以便排序後選擇 top-k）
            items = self.model_class.objects.filter(q_objects)[:limit * 2]
            
            self.logger.debug(f"🔍 關鍵字搜索: 查詢 '{query}' 返回 {len(items)} 個匹配項")
            
            # 計算每個結果的相似度分數
            results = []
            for item in items:
                # ✅ 使用智能分數計算
                score = self._calculate_keyword_score(item, query)
                result = self._format_item_to_result(item, score=score)
                results.append(result)
            
            # 按分數降序排序
            results.sort(key=lambda x: x.get('score', 0), reverse=True)
            
            # 返回 top-k 結果
            top_results = results[:limit]
            
            if top_results:
                self.logger.info(
                    f"📊 關鍵字搜索結果: {len(top_results)} 條 | "
                    f"分數範圍: {top_results[0].get('score', 0):.2f} ~ {top_results[-1].get('score', 0):.2f}"
                )
            
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
                        if heading:
                            section_contents.append(f"## {heading}\n{content}")
                        else:
                            section_contents.append(content)
                    
                    combined_content = "\n\n".join(section_contents)
                    
                    # ✅ 修復：添加圖片資訊（如果文檔有圖片方法）
                    if hasattr(item, 'get_images_summary'):
                        images_summary = item.get_images_summary()
                        if images_summary:
                            combined_content += f"\n\n{images_summary}"
                    
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
