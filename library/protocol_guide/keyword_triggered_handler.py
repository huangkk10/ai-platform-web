"""
模式 A：關鍵字優先全文搜尋處理器（方案 B：查詢重寫策略）

當用戶查詢包含全文關鍵字時，直接發送查詢給 Dify AI（含全文關鍵字）。
如果 AI 回答不確定，則進入降級模式，返回友善提示 + 引用來源。

流程（方案 B）：
1. 檢測到全文關鍵字
2. 發送原查詢給 Dify（讓 Dify 自己搜尋知識庫）
3. 檢測 AI 回答是否不確定
4. 如果不確定 → 降級模式（「請參考以下文件。」+ metadata）

Author: AI Platform Team
Date: 2025-11-11
Updated: 2025-11-11 (方案 B 重構)
"""

import logging
import time
from typing import Dict, Any, List

from library.dify_integration.chat_client import DifyChatClient
from library.config.dify_config_manager import get_protocol_guide_config
from library.common.ai_response import is_uncertain_response  # ✅ 移除 format_fallback_response

logger = logging.getLogger(__name__)


class KeywordTriggeredSearchHandler:
    """
    模式 A 處理器：關鍵字優先全文搜尋（方案 B）
    
    適用場景：用戶查詢包含全文關鍵字（如：完整、全文、所有步驟、詳細等）
    
    方案 B 改進：
    - 不再執行 Protocol Assistant 向量搜尋
    - 直接發送原查詢給 Dify（含全文關鍵字）
    - 讓 Dify 使用自己的知識庫進行搜尋
    - 引用來源來自 Dify 的 metadata.retriever_resources
    """
    
    def __init__(self):
        """初始化處理器"""
        # Dify 客戶端（延遲加載）
        self._dify_client = None
    
    @property
    def dify_client(self):
        """延遲加載 Dify 客戶端"""
        if self._dify_client is None:
            config = get_protocol_guide_config()
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
        處理關鍵字優先全文搜尋（方案 B）
        
        Args:
            user_query: 用戶查詢（含全文關鍵字）
            conversation_id: 對話 ID
            user_id: 用戶 ID
            **kwargs: 其他參數
            
        Returns:
            Dict: 搜尋結果
        """
        start_time = time.time()
        
        logger.info(f"📋 模式 A: 關鍵字優先全文搜尋（方案 B）")
        logger.info(f"   查詢: {user_query[:50]}...")
        
        try:
            # ✅ 方案 B：直接請求 Dify AI（不執行 Protocol Assistant 搜尋）
            logger.info(f"   步驟 1: 請求 Dify AI 回答（含全文關鍵字）...")
            ai_response = self._request_dify_chat(
                query=user_query,  # 保持原查詢（已含「完整」等關鍵字）
                conversation_id=conversation_id,
                user_id=user_id
            )
            
            ai_answer = ai_response.get('answer', '')
            
            # 步驟 2：檢測 AI 回答是否不確定
            is_uncertain, matched_keyword = is_uncertain_response(ai_answer)
            
            response_time = time.time() - start_time
            
            if is_uncertain:
                # 進入降級模式：組合 AI 原始回答 + 友善提示
                logger.info(f"   ⚠️ AI 回答不確定 (含關鍵字: {matched_keyword})")
                logger.info(f"   🔄 進入降級模式：組合 AI 原始回答 + 友善提示（保持透明度）")
                
                # ✅ 方案 B：組合回答 - 保留 AI 原始分析 + 友善提示
                original_answer = ai_answer.strip()
                combined_answer = f"{original_answer}\n\n---\n\n💡 **建議您參考以下文件以獲取更準確的資訊。**"
                
                return {
                    'answer': combined_answer,  # ✅ 組合回答（原始 + 提示）
                    'mode': 'mode_a',
                    'is_fallback': True,
                    'fallback_reason': f'AI 回答不確定 (含: {matched_keyword})',
                    'message_id': ai_response.get('message_id'),
                    'conversation_id': ai_response.get('conversation_id', conversation_id),
                    'response_time': response_time,
                    'tokens': ai_response.get('metadata', {}).get('usage', {}),
                    'metadata': ai_response.get('raw_response', {}).get('metadata', {}),  # ✅ 傳遞完整 metadata（包含引用來源）
                }
            else:
                # AI 回答確定，正常返回
                logger.info(f"   ✅ AI 回答確定")
                logger.info(f"   響應時間: {response_time:.2f} 秒")
                
                return {
                    'answer': ai_answer,
                    'mode': 'mode_a',
                    'is_fallback': False,
                    'message_id': ai_response.get('message_id'),
                    'conversation_id': ai_response.get('conversation_id', conversation_id),
                    'response_time': response_time,
                    'tokens': ai_response.get('metadata', {}).get('usage', {}),
                    'metadata': ai_response.get('raw_response', {}).get('metadata', {}),  # ✅ 添加完整 metadata（包含引用來源）
                }
        
        except Exception as e:
            logger.error(f"❌ 模式 A 處理失敗: {str(e)}", exc_info=True)
            raise
    
    def _request_dify_chat(
        self,
        query: str,
        conversation_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        請求 Dify AI 回答（方案 B：不傳遞上下文）
        
        Args:
            query: 用戶查詢
            conversation_id: 對話 ID
            user_id: 用戶 ID
            
        Returns:
            Dict: Dify 回應
        """
        try:
            # ✅ 方案 B：直接傳遞原查詢（不添加搜尋結果上下文）
            # Mode A 的查詢通常已包含全文關鍵字（如「完整」、「全文」）
            
            # 使用 DifyChatClient（只傳查詢，不傳上下文）
            response = self.dify_client.chat(
                question=query,  # ✅ 只傳查詢（無上下文）
                conversation_id=conversation_id if conversation_id else "",
                user=user_id,
                verbose=False
            )
            
            return response
        
        except Exception as e:
            logger.error(f"❌ Dify 請求失敗: {str(e)}", exc_info=True)
            raise
