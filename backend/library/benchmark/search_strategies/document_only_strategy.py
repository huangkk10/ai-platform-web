"""
純全文向量搜尋策略
==================

特性：
- 只使用 document_embeddings 表（全文向量）
- 高召回率，可能精準度較低
- 適合：廣泛查詢、內容深度匹配
- 自動使用 stage2 配置（title=10%, content=90%）

參數：
- document_threshold: 全文搜尋閾值（預設 0.65）
"""

from .base_strategy import BaseSearchStrategy
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class DocumentOnlyStrategy(BaseSearchStrategy):
    """
    純全文向量搜尋策略
    
    ✅ 自動整合 title/content 權重（來自 SearchThresholdSetting stage2）
    """
    
    def __init__(self, search_service):
        super().__init__(
            search_service=search_service,
            name='document_only',
            description='純全文向量搜尋（高召回率，title=10%/content=90%）',
            document_threshold=0.65
        )
    
    def execute(
        self,
        query: str,
        limit: int = 10,
        **params
    ) -> List[Dict[str, Any]]:
        """
        執行純全文搜尋
        
        ⚠️ 不使用 search_knowledge()（那是給 Protocol Assistant 用的）
        ⚠️ 直接呼叫 search_with_vectors() 並指定 search_mode='document_only'
        
        title/content 權重會自動從 SearchThresholdSetting.stage2 讀取
        """
        # 合併參數
        final_params = self.get_params(**params)
        threshold = final_params.get('document_threshold', 0.65)
        
        self._log(
            f"執行純全文搜尋 | query='{query[:40]}...' | "
            f"threshold={threshold} | limit={limit} | "
            f"⚠️ title/content 權重自動使用 DB stage2 配置（10/90）"
        )
        
        try:
            # 呼叫底層搜尋方法（繞過 search_knowledge）
            results = self.search_service.search_with_vectors(
                query=query,
                limit=limit,
                threshold=threshold,
                search_mode='document_only',  # ⚠️ 強制只搜尋全文
                stage=2  # ⚠️ 使用 stage2 配置（title=10%, content=90%）
            )
            
            # 標記來源和策略
            for result in results:
                result['source'] = 'document'
                result['strategy'] = self.name
                result['weight_applied'] = 1.0  # 純全文，無額外權重
                # 標準化格式
                result = self._format_result_metadata(result)
            
            self._log(
                f"✅ 返回 {len(results)} 個全文結果 "
                f"(title/content 權重已自動應用)"
            )
            return results
            
        except Exception as e:
            self._log(f"❌ 全文搜尋失敗: {str(e)}", level='error')
            logger.exception("全文搜尋異常詳情：")
            return []
