"""
RVT Guide 智能搜尋路由器（Smart Search Router）

根據用戶查詢自動決定搜尋策略：
- 模式 A：關鍵字優先全文搜尋（含全文關鍵字）
- 模式 B：標準兩階段搜尋（無全文關鍵字）

基於 Protocol Guide 的成功實現，適配 RVT Guide 使用

Author: AI Platform Team
Date: 2025-11-11
"""

import logging
from typing import Dict, Any

# 導入關鍵字檢測器
from library.common.query_analysis import contains_full_document_keywords

# 導入兩個處理器
from .keyword_triggered_handler import KeywordTriggeredSearchHandler
from .two_tier_handler import TwoTierSearchHandler

logger = logging.getLogger(__name__)


class SmartSearchRouter:
    """
    RVT Guide 智能搜尋路由器
    
    根據用戶查詢中的關鍵字自動路由到不同的搜尋策略：
    - 含全文關鍵字 → 模式 A（直接全文搜尋）
    - 無全文關鍵字 → 模式 B（兩階段搜尋）
    """
    
    def __init__(self):
        """初始化路由器和兩個處理器"""
        self.mode_a_handler = KeywordTriggeredSearchHandler()
        self.mode_b_handler = TwoTierSearchHandler()
    
    def route_search_strategy(self, user_query: str) -> str:
        """
        根據用戶問題決定搜尋策略
        
        Args:
            user_query: 用戶查詢字串
            
        Returns:
            str: 'mode_a' 或 'mode_b'
        """
        # 檢查是否包含全文關鍵字
        contains_keyword, matched_keyword = contains_full_document_keywords(user_query)
        
        if contains_keyword:
            logger.info(f"🔍 RVT 智能路由: 用戶查詢='{user_query[:50]}...'")
            logger.info(f"   檢測全文關鍵字: True (含: {matched_keyword})")
            logger.info(f"   路由決策: mode_a (關鍵字優先全文搜尋)")
            return 'mode_a'
        else:
            logger.info(f"🔍 RVT 智能路由: 用戶查詢='{user_query[:50]}...'")
            logger.info(f"   檢測全文關鍵字: False")
            logger.info(f"   路由決策: mode_b (標準兩階段搜尋)")
            return 'mode_b'
    
    def handle_smart_search(
        self,
        user_query: str,
        conversation_id: str,
        user_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        智能搜尋主入口
        
        Args:
            user_query: 用戶查詢
            conversation_id: 對話 ID
            user_id: 用戶 ID
            **kwargs: 其他參數（如 request 物件）
            
        Returns:
            Dict: 搜尋結果
                {
                    'answer': str,              # AI 回答
                    'mode': str,                # 搜尋模式 ('mode_a', 'mode_b', 'error')
                    'is_fallback': bool,        # 是否為降級模式
                    'stage': int (optional),    # 階段（僅模式 B）
                    'message_id': str,
                    'conversation_id': str,
                    'response_time': float,
                    'tokens': dict,
                    'metadata': dict,           # Dify metadata（包含引用來源）
                }
        """
        # 決定搜尋策略
        search_mode = self.route_search_strategy(user_query)
        
        try:
            if search_mode == 'mode_a':
                # 模式 A：關鍵字優先全文搜尋
                return self.mode_a_handler.handle_keyword_triggered_search(
                    user_query=user_query,
                    conversation_id=conversation_id,
                    user_id=user_id,
                    **kwargs
                )
            else:
                # 模式 B：標準兩階段搜尋
                return self.mode_b_handler.handle_two_tier_search(
                    user_query=user_query,
                    conversation_id=conversation_id,
                    user_id=user_id,
                    **kwargs
                )
        
        except Exception as e:
            logger.error(f"❌ RVT 智能搜尋路由失敗: {str(e)}", exc_info=True)
            
            # 降級：返回錯誤訊息
            return {
                'answer': f"抱歉，搜尋過程發生錯誤：{str(e)}",
                'mode': 'error',
                'is_fallback': True,
                'error': str(e),
            }
