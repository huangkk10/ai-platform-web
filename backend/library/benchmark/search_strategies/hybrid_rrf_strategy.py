"""
混合 RRF 搜尋策略（向量 + 關鍵字 + RRF 融合）
============================================

來自 Dify v1.2.2 一階搜尋的搜尋策略。

特性：
- 結合向量搜尋（語義理解）和關鍵字搜尋（精確匹配）
- 使用 RRF (Reciprocal Rank Fusion) 算法融合結果
- 可選 Title Boost 加分
- 適合：需要同時兼顧語義和精確關鍵字匹配的查詢

參數：
- rrf_k: RRF 融合常數（預設 60，業界標準）
- title_match_bonus: 標題匹配加分（預設 0.15，即 15%）
- section_threshold: 搜尋閾值（預設 0.80）
- title_weight: 標題權重（預設 95）
- content_weight: 內容權重（預設 5）

🎯 解決的問題：
- 純向量搜尋：語義理解好，但精確關鍵字（如 "iol 密碼"）排名不佳
- 純關鍵字搜尋：精確匹配好，但語義理解弱
- 混合 RRF：結合兩者優點，排名穩定

算法流程：
1. 執行向量搜尋（語義理解）
2. 執行關鍵字搜尋（精確匹配）
3. RRF 融合（排名融合，k=60）
4. 分數正規化（0.5-1.0 範圍）
5. 可選 Title Boost 加分
6. 按最終分數排序返回
"""

from .base_strategy import BaseSearchStrategy
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class HybridRRFStrategy(BaseSearchStrategy):
    """
    混合 RRF 搜尋策略
    
    ✅ 結合向量搜尋和關鍵字搜尋
    ✅ 使用 RRF 算法融合結果
    ✅ 可選 Title Boost 加分
    """
    
    def __init__(self, search_service):
        super().__init__(
            search_service=search_service,
            name='hybrid_rrf',
            description='混合搜尋（向量 + 關鍵字 + RRF 融合）- 來自 Dify v1.2.2',
            # RRF 配置
            rrf_k=60,
            use_hybrid_search=True,
            # Title Boost 配置
            title_match_bonus=0.15,
            min_keyword_length=2,
            # 搜尋配置
            section_threshold=0.80,
            title_weight=95,
            content_weight=5,
            top_k=20
        )
    
    def execute(
        self,
        query: str,
        limit: int = 10,
        **params
    ) -> List[Dict[str, Any]]:
        """
        執行混合 RRF 搜尋
        
        步驟：
        1. 使用 search_knowledge() 並傳入混合搜尋配置
        2. 服務層會自動執行：向量搜尋 → 關鍵字搜尋 → RRF 融合 → Title Boost
        3. 標記來源並返回結果
        """
        # 合併參數
        final_params = self.get_params(**params)
        
        rrf_k = final_params.get('rrf_k', 60)
        title_match_bonus = final_params.get('title_match_bonus', 0.15)
        min_keyword_length = final_params.get('min_keyword_length', 2)
        section_threshold = final_params.get('section_threshold', 0.80)
        title_weight = final_params.get('title_weight', 95)
        content_weight = final_params.get('content_weight', 5)
        top_k = final_params.get('top_k', limit * 2)
        
        self._log(
            f"執行混合 RRF 搜尋 | query='{query[:40]}...' | "
            f"rrf_k={rrf_k} | title_bonus={title_match_bonus:.0%} | "
            f"threshold={section_threshold} | limit={limit}"
        )
        
        try:
            # 構建模擬的 version_config（讓 search_knowledge 啟用混合搜尋）
            version_config = {
                'name': 'V6 - Hybrid RRF (Benchmark)',
                'rag_settings': {
                    'stage1': {
                        'use_hybrid_search': True,
                        'rrf_k': rrf_k,
                        'title_match_bonus': title_match_bonus,
                        'min_keyword_length': min_keyword_length,
                        'threshold': section_threshold,
                        'title_weight': title_weight,
                        'content_weight': content_weight,
                        'top_k': top_k,
                        # 啟用動態配置
                        'use_dynamic_threshold': False,  # Benchmark 使用固定值
                    }
                }
            }
            
            self._log(f"→ Step 1: 呼叫 search_knowledge (混合搜尋模式)")
            
            # 呼叫 search_knowledge 並傳入配置（觸發混合搜尋邏輯）
            results = self.search_service.search_knowledge(
                query=query,
                limit=limit,
                use_vector=True,
                threshold=section_threshold,
                search_mode='section_only',  # 段落搜尋（一階）
                stage=1,
                version_config=version_config  # ⚠️ 傳入配置以啟用混合搜尋
            )
            
            self._log(f"✅ 混合搜尋返回 {len(results)} 個結果")
            
            # 標記來源和策略
            for result in results:
                result['source'] = 'hybrid_rrf'
                result['strategy'] = self.name
                # 添加 RRF 相關標記
                result['rrf_k'] = rrf_k
                result['title_boost_enabled'] = title_match_bonus > 0
                # 標準化格式
                result = self._format_result_metadata(result)
            
            # 記錄詳細結果（前 3 個）
            if results:
                self._log("→ Top 3 結果:")
                for i, r in enumerate(results[:3], 1):
                    score = r.get('score', 0)
                    rrf_score = r.get('rrf_score', 'N/A')
                    title = r.get('title', 'N/A')[:30]
                    boosted = "⭐" if r.get('title_boost_applied', False) else ""
                    self._log(
                        f"   {i}. [{score:.4f}] {title}... {boosted}"
                        f" (RRF: {rrf_score})"
                    )
            
            self._log(
                f"✅ 返回 {len(results)} 個混合 RRF 結果 "
                f"(向量+關鍵字+RRF 融合已完成)"
            )
            return results
            
        except Exception as e:
            self._log(f"❌ 混合 RRF 搜尋失敗: {str(e)}", level='error')
            logger.exception("混合 RRF 搜尋異常詳情：")
            
            # 降級為純向量搜尋
            self._log("⚠️ 降級為純向量搜尋", level='warning')
            try:
                fallback_results = self.search_service.search_with_vectors(
                    query=query,
                    limit=limit,
                    threshold=section_threshold,
                    search_mode='section_only',
                    stage=1
                )
                for result in fallback_results:
                    result['source'] = 'section_fallback'
                    result['strategy'] = f"{self.name}_fallback"
                return fallback_results
            except Exception as fallback_error:
                self._log(f"❌ 降級搜尋也失敗: {str(fallback_error)}", level='error')
                return []
