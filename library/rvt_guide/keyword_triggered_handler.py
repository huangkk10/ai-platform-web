"""
模式 A：RVT Guide 關鍵字觸發處理器

當用戶查詢包含全文關鍵字時，直接執行全文搜尋：
- 檢測到關鍵字：「完整內容」、「全部內容」、「所有內容」等
- 直接發送原查詢給 Dify（Dify 會自動觸發全文搜尋）
- 無需階段性嘗試，一步到位

基於 Protocol Guide 的成功實現，適配 RVT Guide 使用

Author: AI Platform Team
Date: 2025-11-11
"""

import logging
import time
from typing import Dict, Any

from library.dify_integration.chat_client import DifyChatClient
from library.config.dify_config_manager import get_rvt_guide_config

logger = logging.getLogger(__name__)


class KeywordTriggeredSearchHandler:
    """
    模式 A 處理器：RVT Guide 關鍵字觸發全文搜尋
    
    適用場景：用戶查詢包含全文關鍵字（明確要求完整內容）
    
    策略：
    - 直接發送原查詢給 Dify
    - Dify 檢測到關鍵字後，自動執行全文搜尋
    - 返回完整文檔內容的 AI 分析
    """
    
    def __init__(self):
        """初始化處理器"""
        # Dify 客戶端（延遲加載）
        self._dify_client = None
    
    @property
    def dify_client(self):
        """延遲加載 Dify 客戶端"""
        if self._dify_client is None:
            config = get_rvt_guide_config()
            self._dify_client = DifyChatClient(
                api_url=config.api_url,
                api_key=config.api_key,
                base_url=config.base_url
            )
        return self._dify_client
    
    def handle_keyword_triggered_search(
        self,
        user_query: str,
        conversation_id: str,
        user_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        處理關鍵字觸發的全文搜尋
        
        Args:
            user_query: 用戶查詢（包含全文關鍵字）
            conversation_id: 對話 ID
            user_id: 用戶 ID
            **kwargs: 其他參數
            
        Returns:
            Dict: 搜尋結果
                {
                    'answer': str,
                    'mode': 'mode_a',
                    'is_fallback': False,
                    'message_id': str,
                    'conversation_id': str,
                    'response_time': float,
                    'tokens': dict,
                    'metadata': dict,       # Dify metadata（包含引用來源）
                }
        """
        start_time = time.time()
        
        logger.info(f"🔍 RVT 模式 A: 關鍵字優先全文搜尋")
        logger.info(f"   查詢: {user_query[:50]}...")
        
        try:
            # 直接發送原查詢（Dify 會自動觸發全文搜尋）
            response = self.dify_client.chat(
                question=user_query,
                conversation_id=conversation_id if conversation_id else "",
                user=user_id,
                verbose=False
            )
            
            response_time = time.time() - start_time
            logger.info(f"   ✅ RVT 模式 A 完成")
            logger.info(f"   響應時間: {response_time:.2f} 秒")
            
            return {
                'answer': response.get('answer', ''),
                'mode': 'mode_a',
                'is_fallback': False,
                'message_id': response.get('message_id'),
                'conversation_id': response.get('conversation_id', conversation_id),
                'response_time': response_time,
                'tokens': response.get('metadata', {}).get('usage', {}),
                'metadata': response.get('raw_response', {}).get('metadata', {}),  # ✅ 添加完整 metadata（包含引用來源）
            }
        
        except Exception as e:
            logger.error(f"❌ RVT 模式 A 處理失敗: {str(e)}", exc_info=True)
            raise
