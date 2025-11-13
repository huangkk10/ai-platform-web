"""
智能搜尋路由器（Smart Search Router）

根據用戶查詢自動決定搜尋策略：
- 模式 A：關鍵字優先全文搜尋（含全文關鍵字）
- 模式 B：標準兩階段搜尋（無全文關鍵字）

Author: AI Platform Team
Date: 2025-11-11
"""

import logging
from typing import Dict, Any

# 導入關鍵字檢測器
from library.common.query_analysis import contains_full_document_keywords

# 導入兩個處理器（會在下面創建）
from .keyword_triggered_handler import KeywordTriggeredSearchHandler
from .two_tier_handler import TwoTierSearchHandler

logger = logging.getLogger(__name__)


class SmartSearchRouter:
    """
    智能搜尋路由器
    
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
            logger.info(f"🔍 智能路由: 用戶查詢='{user_query[:50]}...'")
            logger.info(f"   檢測全文關鍵字: True (含: {matched_keyword})")
            logger.info(f"   路由決策: mode_a (關鍵字優先全文搜尋)")
            return 'mode_a'
        else:
            logger.info(f"🔍 智能路由: 用戶查詢='{user_query[:50]}...'")
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
                    'mode': str,                # 搜尋模式
                    'is_fallback': bool,        # 是否為降級模式
                    'stage': int (optional),    # 階段（僅模式 B）
                    'search_results': list,     # 搜尋結果
                    'message_id': str,
                    'conversation_id': str,
                    'response_time': float,
                    'tokens': dict,
                }
        """
        # 決定搜尋策略
        search_mode = self.route_search_strategy(user_query)
        
        result = None
        
        try:
            if search_mode == 'mode_a':
                # 模式 A：關鍵字優先全文搜尋
                result = self.mode_a_handler.handle_keyword_triggered_search(
                    user_query=user_query,
                    conversation_id=conversation_id,
                    user_id=user_id,
                    **kwargs
                )
            else:
                # 模式 B：標準兩階段搜尋
                result = self.mode_b_handler.handle_two_tier_search(
                    user_query=user_query,
                    conversation_id=conversation_id,
                    user_id=user_id,
                    **kwargs
                )
            
            # 🆕 記錄對話到資料庫（支援 Analytics）
            self._record_conversation(
                user_query=user_query,
                conversation_id=conversation_id,
                result=result,
                kwargs=kwargs
            )
            
            return result
        
        except Exception as e:
            logger.error(f"❌ 智能搜尋路由失敗: {str(e)}", exc_info=True)
            
            # 降級：返回錯誤訊息
            return {
                'answer': f"抱歉，搜尋過程發生錯誤：{str(e)}",
                'mode': 'error',
                'is_fallback': True,
                'error': str(e),
            }
    
    def _record_conversation(
        self,
        user_query: str,
        conversation_id: str,
        result: Dict[str, Any],
        kwargs: Dict[str, Any]
    ) -> None:
        """
        記錄對話到資料庫
        
        Args:
            user_query: 用戶查詢
            conversation_id: 對話 ID
            result: 搜尋結果
            kwargs: 額外參數（包含 request）
        """
        try:
            from library.conversation_management import (
                CONVERSATION_MANAGEMENT_AVAILABLE, 
                record_complete_exchange
            )
            
            if not CONVERSATION_MANAGEMENT_AVAILABLE:
                logger.warning("Conversation Management Library 不可用，跳過對話記錄")
                return
            
            request = kwargs.get('request')
            if not request:
                logger.warning("未提供 request 物件，無法記錄對話")
                return
            
            # 只記錄成功的搜尋結果（排除錯誤模式）
            if result.get('mode') == 'error':
                logger.info("搜尋失敗，跳過對話記錄")
                return
            
            # 先確保會話存在並設置正確的 chat_type
            from library.conversation_management import get_or_create_session
            
            session_result = get_or_create_session(
                request=request,
                session_id=result.get('conversation_id', conversation_id),
                chat_type='protocol_assistant_chat'  # ⚠️ 重要！指定正確的類型
            )
            
            if not session_result.get('success'):
                logger.warning(f"⚠️ 無法建立會話: {session_result.get('error')}")
                return
            
            # 記錄完整的對話交互
            conversation_result = record_complete_exchange(
                request=request,
                session_id=result.get('conversation_id', conversation_id),
                user_message=user_query,
                assistant_message=result.get('answer', ''),
                response_time=result.get('response_time', 0),
                token_usage=result.get('tokens', {}),
                metadata={
                    'dify_message_id': result.get('message_id', ''),
                    'mode': result.get('mode'),
                    'stage': result.get('stage'),
                    'is_fallback': result.get('is_fallback', False),
                    'fallback_reason': result.get('fallback_reason', ''),
                    'dify_metadata': result.get('metadata', {}),
                    'workspace': 'Protocol_Guide',
                    'app_name': 'Protocol Assistant'
                }
            )
            
            if conversation_result.get('success'):
                logger.info(f"✅ Protocol 對話記錄成功: session={conversation_id}, mode={result.get('mode')}")
            else:
                logger.warning(f"⚠️ Protocol 對話記錄失敗: {conversation_result.get('error', 'Unknown error')}")
                
        except ImportError as import_error:
            logger.warning(f"Conversation Management Library 導入失敗: {str(import_error)}")
        except Exception as conv_error:
            # 對話記錄失敗不應影響主要功能
            logger.error(f"❌ Protocol 對話記錄錯誤: {str(conv_error)}", exc_info=True)
