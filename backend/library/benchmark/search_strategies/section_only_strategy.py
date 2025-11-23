"""
純段落向量搜尋策略
==================

特性：
- 只使用 section_multi_vectors 表（段落向量）
- 高精準度，低召回率
- 適合：精確查詢、特定片段搜尋
- 自動使用 stage1 配置（title=95%, content=5%）

參數：
- section_threshold: 段落搜尋閾值（預設 0.75）
"""

from .base_strategy import BaseSearchStrategy
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class SectionOnlyStrategy(BaseSearchStrategy):
    """
    純段落向量搜尋策略
    
    ✅ 自動整合 title/content 權重（來自 SearchThresholdSetting stage1）
    """
    
    def __init__(self, search_service):
        super().__init__(
            search_service=search_service,
            name='section_only',
            description='純段落向量搜尋（高精準度，title=95%/content=5%）',
            section_threshold=0.75
        )
    
    def execute(
        self,
        query: str,
        limit: int = 10,
        **params
    ) -> List[Dict[str, Any]]:
        """
        執行純段落搜尋
        
        ⚠️ 不使用 search_knowledge()（那是給 Protocol Assistant 用的）
        ⚠️ 直接呼叫 search_with_vectors() 並指定 search_mode='section_only'
        
        title/content 權重會自動從 SearchThresholdSetting.stage1 讀取
        """
        # 合併參數
        final_params = self.get_params(**params)
        threshold = final_params.get('section_threshold', 0.75)
        
        self._log(
            f"執行純段落搜尋 | query='{query[:40]}...' | "
            f"threshold={threshold} | limit={limit} | "
            f"⚠️ title/content 權重自動使用 DB stage1 配置（95/5）"
        )
        
        try:
            # 呼叫底層搜尋方法（繞過 search_knowledge）
            results = self.search_service.search_with_vectors(
                query=query,
                limit=limit,
                threshold=threshold,
                search_mode='section_only',  # ⚠️ 強制只搜尋段落
                stage=1  # ⚠️ 使用 stage1 配置（title=95%, content=5%）
            )
            
            # 標記來源和策略
            for result in results:
                result['source'] = 'section'
                result['strategy'] = self.name
                result['weight_applied'] = 1.0  # 純段落，無額外權重
                # 標準化格式
                result = self._format_result_metadata(result)
            
            self._log(
                f"✅ 返回 {len(results)} 個段落結果 "
                f"(title/content 權重已自動應用)"
            )
            return results
            
        except Exception as e:
            self._log(f"❌ 段落搜尋失敗: {str(e)}", level='error')
            logger.exception("段落搜尋異常詳情：")
            return []
