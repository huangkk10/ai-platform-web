"""
模式 B：兩階段搜尋處理器（使用顯式 search_mode 參數）

兩階段智能路由策略：
1. 第一階段：段落級搜尋（search_mode='auto'）
2. 檢測 AI 回答是否不確定
3. 如果不確定 → 第二階段：全文級搜尋（search_mode='document_only'）
4. 仍不確定 → 降級模式（返回友善提示 + 引用來源）

流程（使用 search_mode）：
階段 1: 發送原查詢 + inputs={'search_mode': 'auto'} → Dify 段落搜尋 → AI 回答 → 檢測不確定
└─ 如果確定 → 返回結果
└─ 如果不確定 → 階段 2

階段 2: 發送原查詢 + inputs={'search_mode': 'document_only'} → Dify 全文搜尋 → AI 回答 → 檢測不確定
└─ 如果確定 → 返回結果（標記為 Stage 2 成功）
└─ 如果不確定 → 降級模式（「請參考以下文件。」+ metadata）

Author: AI Platform Team
Date: 2025-11-11
Updated: 2025-11-13 (使用顯式 search_mode 參數，取代查詢重寫)
"""

import logging
import time
from typing import Dict, Any, List

from library.dify_integration.chat_client import DifyChatClient
from library.config.dify_config_manager import get_protocol_guide_config
from library.common.ai_response import is_uncertain_response  # ✅ 移除 format_fallback_response

logger = logging.getLogger(__name__)


class TwoTierSearchHandler:
    """
    模式 B 處理器：兩階段搜尋（使用顯式 search_mode）
    
    適用場景：用戶查詢不包含全文關鍵字（標準查詢）
    
    改進實現（2025-11-13）：
    - Stage 1：發送原查詢 + inputs={'search_mode': 'auto'}（段落級搜尋）
    - Stage 2：發送原查詢 + inputs={'search_mode': 'document_only'}（全文級搜尋）
    - 不再執行 Protocol Assistant 向量搜尋
    - 不再使用查詢重寫（添加「完整」關鍵字）
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
    
    def handle_two_tier_search(
        self,
        user_query: str,
        conversation_id: str,
        user_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        處理兩階段搜尋（方案 B）
        
        Args:
            user_query: 用戶查詢
            conversation_id: 對話 ID
            user_id: 用戶 ID
            **kwargs: 其他參數
            
        Returns:
            Dict: 搜尋結果
        """
        start_time = time.time()
        
        logger.info(f"🔄 模式 B: 兩階段搜尋（方案 B）")
        logger.info(f"   查詢: {user_query[:50]}...")
        
        try:
            # === 階段 1：段落級搜尋 ===
            logger.info(f"   階段 1: 發送原查詢給 Dify（段落級搜尋）...")
            
            # ✅ 方案 B：直接請求 Dify（不執行 Protocol Assistant 搜尋）
            stage_1_response = self._request_dify_chat(
                query=user_query,
                conversation_id=conversation_id,
                user_id=user_id,
                is_full_search=False  # Stage 1 = 段落搜尋
            )
            
            stage_1_answer = stage_1_response.get('answer', '')
            
            # 檢測 AI 回答是否不確定
            is_stage_1_uncertain, stage_1_keyword = is_uncertain_response(stage_1_answer)
            
            if not is_stage_1_uncertain:
                # 階段 1 回答確定，直接返回
                logger.info(f"   ✅ 階段 1 回答確定")
                response_time = time.time() - start_time
                logger.info(f"   響應時間: {response_time:.2f} 秒")
                
                return {
                    'answer': stage_1_answer,
                    'mode': 'mode_b',
                    'stage': 1,
                    'is_fallback': False,
                    'message_id': stage_1_response.get('message_id'),
                    'conversation_id': stage_1_response.get('conversation_id', conversation_id),
                    'response_time': response_time,
                    'tokens': stage_1_response.get('metadata', {}).get('usage', {}),
                    'metadata': stage_1_response.get('raw_response', {}).get('metadata', {}),  # ✅ 添加完整 metadata（包含引用來源）
                }
            
            # === 階段 2：全文級搜尋 ===
            logger.info(f"   ⚠️ 階段 1 回答不確定 (含關鍵字: {stage_1_keyword})")
            logger.info(f"   🔄 進入階段 2: 發送「原查詢 + 完整」給 Dify（全文級搜尋）...")
            
            # ✅ 方案 B：添加「完整」觸發詞，引導 Dify 全文搜尋
            stage_2_response = self._request_dify_chat(
                query=user_query,
                conversation_id=conversation_id,
                user_id=user_id,
                is_full_search=True  # Stage 2 = 全文搜尋（添加「完整」）
            )
            
            stage_2_answer = stage_2_response.get('answer', '')
            
            # 檢測階段 2 回答是否不確定
            is_stage_2_uncertain, stage_2_keyword = is_uncertain_response(stage_2_answer)
            
            response_time = time.time() - start_time
            
            if not is_stage_2_uncertain:
                # 階段 2 回答確定，返回
                logger.info(f"   ✅ 階段 2 回答確定")
                logger.info(f"   響應時間: {response_time:.2f} 秒")
                
                return {
                    'answer': stage_2_answer,
                    'mode': 'mode_b',
                    'stage': 2,
                    'is_fallback': False,
                    'message_id': stage_2_response.get('message_id'),
                    'conversation_id': stage_2_response.get('conversation_id', conversation_id),
                    'response_time': response_time,
                    'tokens': stage_2_response.get('metadata', {}).get('usage', {}),
                    'metadata': stage_2_response.get('raw_response', {}).get('metadata', {}),  # ✅ 添加完整 metadata（包含引用來源）
                }
            else:
                # 階段 2 仍不確定，進入降級模式：組合 AI 原始回答 + 友善提示
                logger.info(f"   ⚠️ 階段 2 回答不確定 (含關鍵字: {stage_2_keyword})")
                logger.info(f"   🔄 進入降級模式：組合 AI 原始回答 + 友善提示（保持透明度）")
                
                # ✅ 方案 B：組合回答 - 保留 AI 原始分析 + 友善提示
                original_answer = stage_2_response.get('answer', '').strip()
                combined_answer = f"{original_answer}\n\n---\n\n💡 **建議您參考以下文件以獲取更準確的資訊。**"
                
                return {
                    'answer': combined_answer,  # ✅ 組合回答（原始 + 提示）
                    'mode': 'mode_b',
                    'stage': 2,
                    'is_fallback': True,
                    'fallback_reason': f'階段 2 AI 回答不確定 (含: {stage_2_keyword})',
                    'message_id': stage_2_response.get('message_id'),
                    'conversation_id': stage_2_response.get('conversation_id', conversation_id),
                    'response_time': response_time,
                    'tokens': stage_2_response.get('metadata', {}).get('usage', {}),
                    'metadata': stage_2_response.get('raw_response', {}).get('metadata', {}),  # ✅ 傳遞完整 metadata（包含引用來源）
                }
        
        except Exception as e:
            logger.error(f"❌ 模式 B 處理失敗: {str(e)}", exc_info=True)
            raise
    
    def _request_dify_chat(
        self,
        query: str,
        conversation_id: str,
        user_id: str,
        is_full_search: bool = False
    ) -> Dict[str, Any]:
        """
        請求 Dify AI 回答（支援顯式 search_mode）
        
        Args:
            query: 用戶查詢
            conversation_id: 對話 ID
            user_id: 用戶 ID
            is_full_search: 是否為全文搜尋階段（Stage 2）
            
        Returns:
            Dict: Dify 回應
                {
                    'answer': str,
                    'message_id': str,
                    'conversation_id': str,
                    'metadata': dict,
                    'raw_response': dict
                }
        """
        try:
            # ✅ 改進：不需要查詢重寫，使用顯式 search_mode
            # 保持原查詢不變
            rewritten_query = query
            
            if is_full_search:
                # Stage 2：通過 inputs 傳遞文檔搜索模式
                logger.info(f"   📝 Stage 2: 使用文檔搜索模式 (search_mode='document_only')")
                inputs = {
                    'search_mode': 'document_only',  # ← 顯式指定文檔搜索
                    'require_detailed_answer': 'true'
                }
            else:
                # Stage 1：使用自動模式（段落優先）
                logger.info(f"   📝 Stage 1: 使用自動搜索模式 (search_mode='auto')")
                inputs = {
                    'search_mode': 'auto'
                }
            
            # 使用 DifyChatClient
            response = self.dify_client.chat(
                question=rewritten_query,  # ✅ 原查詢（無修改）
                conversation_id=conversation_id if conversation_id else "",
                user=user_id,
                inputs=inputs,  # ← 通過 inputs 傳遞 search_mode
                verbose=False
            )
            
            return response
        
        except Exception as e:
            logger.error(f"❌ Protocol Dify 請求失敗: {str(e)}", exc_info=True)
            raise
