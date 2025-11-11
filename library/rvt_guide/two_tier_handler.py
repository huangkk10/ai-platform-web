"""
模式 B：RVT Guide 兩階段搜尋處理器（方案 B：查詢重寫策略）

兩階段智能路由策略：
1. 第一階段：段落級搜尋（發送原查詢給 Dify）
2. 檢測 AI 回答是否不確定
3. 如果不確定 → 第二階段：全文級搜尋（添加「完整內容」觸發詞）
4. 仍不確定 → 降級模式（返回友善提示 + 引用來源）

流程（方案 B）：
階段 1: 發送原查詢 → Dify 段落搜尋 → AI 回答 → 檢測不確定
└─ 如果確定 → 返回結果
└─ 如果不確定 → 階段 2

階段 2: 發送「原查詢 + 完整內容」→ Dify 全文搜尋 → AI 回答 → 檢測不確定
└─ 如果確定 → 返回結果（標記為 Stage 2 成功）
└─ 如果不確定 → 降級模式（「請參考以下文件。」+ metadata）

基於 Protocol Guide 的成功實現，適配 RVT Guide 使用

Author: AI Platform Team
Date: 2025-11-11
"""

import logging
import time
from typing import Dict, Any, List

from library.dify_integration.chat_client import DifyChatClient
from library.config.dify_config_manager import get_rvt_guide_config
from library.common.ai_response import is_uncertain_response

logger = logging.getLogger(__name__)


class TwoTierSearchHandler:
    """
    模式 B 處理器：RVT Guide 兩階段搜尋（方案 B）
    
    適用場景：用戶查詢不包含全文關鍵字（標準查詢）
    
    方案 B 改進：
    - Stage 1：發送原查詢給 Dify（段落級搜尋）
    - Stage 2：發送「原查詢 + 完整內容」給 Dify（全文級搜尋）
    - 不再執行 RVT Assistant 向量搜尋
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
            config = get_rvt_guide_config()
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
                {
                    'answer': str,
                    'mode': 'mode_b',
                    'stage': int,           # 1 或 2
                    'is_fallback': bool,
                    'fallback_reason': str (optional),
                    'message_id': str,
                    'conversation_id': str,
                    'response_time': float,
                    'tokens': dict,
                    'metadata': dict,       # Dify metadata（包含引用來源）
                }
        """
        start_time = time.time()
        
        logger.info(f"🔄 RVT 模式 B: 兩階段搜尋（方案 B）")
        logger.info(f"   查詢: {user_query[:50]}...")
        
        try:
            # === 階段 1：段落級搜尋 ===
            logger.info(f"   階段 1: 發送原查詢給 Dify（段落級搜尋）...")
            
            # ✅ 方案 B：直接請求 Dify（不執行 RVT Assistant 搜尋）
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
            logger.info(f"   🔄 進入階段 2: 發送「原查詢 + 完整內容」給 Dify（全文級搜尋）...")
            
            # ✅ 方案 B：添加「完整內容」觸發詞，引導 Dify 全文搜尋
            stage_2_response = self._request_dify_chat(
                query=user_query,
                conversation_id=conversation_id,
                user_id=user_id,
                is_full_search=True  # Stage 2 = 全文搜尋（添加「完整內容」）
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
            logger.error(f"❌ RVT 模式 B 處理失敗: {str(e)}", exc_info=True)
            raise
    
    def _request_dify_chat(
        self,
        query: str,
        conversation_id: str,
        user_id: str,
        is_full_search: bool = False
    ) -> Dict[str, Any]:
        """
        請求 Dify AI 回答（方案 B：查詢重寫策略）
        
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
            # ✅ 方案 B：根據搜尋階段重寫查詢（而非傳遞上下文）
            if is_full_search:
                # Stage 2：添加全文觸發詞，引導 Dify 進行全文搜尋
                rewritten_query = f"{query} 完整內容"
                logger.info(f"   📝 Stage 2 查詢重寫: {query} → {rewritten_query}")
            else:
                # Stage 1：保持原查詢，Dify 進行段落級搜尋
                rewritten_query = query
            
            # 使用 DifyChatClient（只傳查詢，不傳上下文）
            response = self.dify_client.chat(
                question=rewritten_query,  # ✅ 只傳查詢（無上下文）
                conversation_id=conversation_id if conversation_id else "",
                user=user_id,
                verbose=False
            )
            
            return response
        
        except Exception as e:
            logger.error(f"❌ RVT Dify 請求失敗: {str(e)}", exc_info=True)
            raise
