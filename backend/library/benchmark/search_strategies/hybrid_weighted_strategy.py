"""
混合權重搜尋策略（四維權重系統）
==================================

四維權重系統：
1. Dimension 1: section_weight vs document_weight（可調整）
2. Dimension 2-A: Section 的 title(95%) vs content(5%)（DB stage1）
3. Dimension 2-B: Document 的 title(10%) vs content(90%)（DB stage2）

算法流程：
1. 執行段落搜尋（search_mode='section_only', stage=1）
2. 執行全文搜尋（search_mode='document_only', stage=2）
3. 按 document ID 合併結果
4. 應用 section_weight 和 document_weight
5. 排序返回

預期效果：
- section_weight=0.7, document_weight=0.3 → 平衡精準度和召回率
"""

from .base_strategy import BaseSearchStrategy
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class HybridWeightedStrategy(BaseSearchStrategy):
    """
    混合權重搜尋策略
    
    ✅ 完整整合四維權重系統
    ✅ 段落和全文結果的加權合併
    """
    
    def __init__(self, search_service):
        super().__init__(
            search_service=search_service,
            name='hybrid_weighted',
            description='混合權重搜尋（四維權重：section 0.7 + document 0.3）',
            section_weight=0.7,
            document_weight=0.3,
            section_threshold=0.75,
            document_threshold=0.65
        )
    
    def execute(
        self,
        query: str,
        limit: int = 10,
        **params
    ) -> List[Dict[str, Any]]:
        """
        執行混合權重搜尋
        
        ⚠️ 四維權重流程：
        1. 段落搜尋（stage=1）→ 自動應用 title=95%/content=5%
        2. 全文搜尋（stage=2）→ 自動應用 title=10%/content=90%
        3. 按 document ID 合併
        4. 應用 section_weight 和 document_weight
        """
        # 合併參數
        final_params = self.get_params(**params)
        
        section_weight = final_params.get('section_weight', 0.7)
        document_weight = final_params.get('document_weight', 0.3)
        section_threshold = final_params.get('section_threshold', 0.75)
        document_threshold = final_params.get('document_threshold', 0.65)
        
        # 參數驗證
        if not self._validate_weights(section_weight, document_weight):
            self._log("⚠️ 權重總和不為 1.0，自動歸一化", level='warning')
            total = section_weight + document_weight
            section_weight /= total
            document_weight /= total
        
        self._log(
            f"執行混合權重搜尋 | query='{query[:40]}...' | "
            f"section_weight={section_weight} | document_weight={document_weight} | "
            f"section_threshold={section_threshold} | document_threshold={document_threshold}"
        )
        
        try:
            # Step 1: 段落搜尋（stage=1 → title=95%/content=5%）
            self._log("→ Step 1: 執行段落向量搜尋（stage=1, title=95%/content=5%）")
            section_results = self.search_service.search_with_vectors(
                query=query,
                limit=limit * 2,  # 多取一些，合併後再裁剪
                threshold=section_threshold,
                search_mode='section_only',
                stage=1  # ⚠️ 觸發 title=95%/content=5%
            )
            self._log(f"  ✅ 段落搜尋返回 {len(section_results)} 個結果")
            
            # Step 2: 全文搜尋（stage=2 → title=10%/content=90%）
            self._log("→ Step 2: 執行全文向量搜尋（stage=2, title=10%/content=90%）")
            document_results = self.search_service.search_with_vectors(
                query=query,
                limit=limit * 2,
                threshold=document_threshold,
                search_mode='document_only',
                stage=2  # ⚠️ 觸發 title=10%/content=90%
            )
            self._log(f"  ✅ 全文搜尋返回 {len(document_results)} 個結果")
            
            # Step 3: 加權合併（Dimension 1）
            self._log(
                f"→ Step 3: 加權合併 "
                f"(section={section_weight} × {len(section_results)} results, "
                f"document={document_weight} × {len(document_results)} results)"
            )
            merged_results = self._weighted_merge(
                section_results=section_results,
                document_results=document_results,
                section_weight=section_weight,
                document_weight=document_weight
            )
            
            # Step 4: 排序和裁剪
            merged_results = sorted(
                merged_results,
                key=lambda x: x.get('final_score', 0),
                reverse=True
            )[:limit]
            
            # Step 5: 標記來源
            for result in merged_results:
                result['strategy'] = self.name
                result = self._format_result_metadata(result)
            
            self._log(
                f"✅ 返回 {len(merged_results)} 個混合結果 "
                f"(四維權重已完整應用)"
            )
            return merged_results
            
        except Exception as e:
            self._log(f"❌ 混合搜尋失敗: {str(e)}", level='error')
            logger.exception("混合搜尋異常詳情：")
            return []
    
    def _validate_weights(
        self,
        section_weight: float,
        document_weight: float
    ) -> bool:
        """驗證權重總和是否為 1.0"""
        total = section_weight + document_weight
        return abs(total - 1.0) < 0.001
    
    def _weighted_merge(
        self,
        section_results: List[Dict[str, Any]],
        document_results: List[Dict[str, Any]],
        section_weight: float,
        document_weight: float
    ) -> List[Dict[str, Any]]:
        """
        加權合併段落和全文結果
        
        合併策略：
        1. 以 document_id 為 key 建立字典
        2. 累加相同 document_id 的分數（應用權重）
        3. 保留最完整的 metadata
        4. 記錄來源（section/document/both）
        
        四維權重流程：
        - Section 結果已包含 title=95%/content=5% 的加權分數
        - Document 結果已包含 title=10%/content=90% 的加權分數
        - 這裡只需應用 section_weight 和 document_weight
        
        範例：
        - Section: doc_id=123, score=0.85（title=95%/content=5% 已應用）
        - Document: doc_id=123, score=0.72（title=10%/content=90% 已應用）
        - Final: 0.85*0.7 + 0.72*0.3 = 0.595 + 0.216 = 0.811
        """
        merged_dict = {}
        
        # 處理段落結果
        for result in section_results:
            doc_id = result.get('document_id')
            if not doc_id:
                continue
            
            weighted_score = result.get('similarity', 0) * section_weight
            
            merged_dict[doc_id] = {
                **result,
                'section_score': result.get('similarity', 0),
                'section_weight_applied': section_weight,
                'section_weighted_score': weighted_score,
                'document_score': 0,
                'document_weight_applied': 0,
                'document_weighted_score': 0,
                'final_score': weighted_score,
                'source': 'section'
            }
        
        # 處理全文結果
        for result in document_results:
            doc_id = result.get('document_id')
            if not doc_id:
                continue
            
            weighted_score = result.get('similarity', 0) * document_weight
            
            if doc_id in merged_dict:
                # 已存在（同時在段落和全文中）
                merged_dict[doc_id]['document_score'] = result.get('similarity', 0)
                merged_dict[doc_id]['document_weight_applied'] = document_weight
                merged_dict[doc_id]['document_weighted_score'] = weighted_score
                merged_dict[doc_id]['final_score'] += weighted_score
                merged_dict[doc_id]['source'] = 'both'
            else:
                # 新文檔（只在全文中）
                merged_dict[doc_id] = {
                    **result,
                    'section_score': 0,
                    'section_weight_applied': 0,
                    'section_weighted_score': 0,
                    'document_score': result.get('similarity', 0),
                    'document_weight_applied': document_weight,
                    'document_weighted_score': weighted_score,
                    'final_score': weighted_score,
                    'source': 'document'
                }
        
        # 日誌統計
        both_count = sum(1 for r in merged_dict.values() if r['source'] == 'both')
        section_only = sum(1 for r in merged_dict.values() if r['source'] == 'section')
        document_only = sum(1 for r in merged_dict.values() if r['source'] == 'document')
        
        self._log(
            f"  合併統計: both={both_count}, "
            f"section_only={section_only}, "
            f"document_only={document_only}, "
            f"total={len(merged_dict)}"
        )
        
        return list(merged_dict.values())
