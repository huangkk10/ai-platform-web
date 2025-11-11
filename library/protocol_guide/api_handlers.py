"""
Protocol Guide API 處理器
========================

使用基礎類別快速實現 Protocol Guide 的所有 API 端點。

代碼量：僅 15 行！（對比原始方式的 300+ 行）
"""

from library.common.knowledge_base import BaseKnowledgeBaseAPIHandler
from api.models import ProtocolGuide


class ProtocolGuideAPIHandler(BaseKnowledgeBaseAPIHandler):
    """
    Protocol Guide API 處理器
    
    繼承自 BaseKnowledgeBaseAPIHandler，自動獲得：
    - handle_dify_search_api()  - Dify 知識庫搜索
    - handle_chat_api()         - 聊天 API
    - handle_config_api()       - 配置信息 API
    """
    
    # 設定必要的類別屬性
    knowledge_id = 'protocol_guide_db'      # Dify 知識庫 ID
    config_key = 'protocol_guide'           # 配置鍵名
    source_table = 'protocol_guide'         # 資料表名
    model_class = ProtocolGuide             # Model 類別
    
    @classmethod
    def get_search_service(cls):
        """返回搜索服務實例"""
        from .search_service import ProtocolGuideSearchService
        return ProtocolGuideSearchService()
    
    @classmethod
    def get_chat_config(cls):
        """
        獲取 Protocol Guide 聊天配置
        使用 DifyConfigManager 獲取配置
        """
        try:
            from library.config.dify_config_manager import get_protocol_guide_config
            config_obj = get_protocol_guide_config()
            return config_obj.to_dict()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Protocol Guide 配置獲取失敗: {str(e)}")
            return {}
    
    # ===== 智能搜尋路由器整合（2025-11-11）=====
    
    @classmethod
    def handle_chat_api(cls, request):
        """
        處理知識庫聊天 API（使用智能搜尋路由器）
        
        覆寫基類方法，使用 SmartSearchRouter 實現兩階段搜尋策略：
        - 模式 A：關鍵字優先全文搜尋（含全文關鍵字）
        - 模式 B：標準兩階段搜尋（無全文關鍵字）
        
        Args:
            request: Django request 對象
            
        Returns:
            Response: Django REST Framework Response
        """
        from rest_framework.response import Response
        from rest_framework import status
        import logging
        import time
        
        logger = logging.getLogger(__name__)
        
        try:
            # 解析請求數據
            data = request.data
            message = data.get('message', '').strip()
            conversation_id = data.get('conversation_id', '')
            
            # 驗證輸入
            if not message:
                return Response({
                    'success': False,
                    'error': '訊息內容不能為空'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 獲取用戶 ID
            user_id = f"protocol_guide_user_{request.user.id if request.user.is_authenticated else 'guest'}"
            
            logger.info(f"📩 Protocol Guide Chat Request")
            logger.info(f"   User: {request.user.username if request.user.is_authenticated else 'guest'}")
            logger.info(f"   Message: {message[:50]}...")
            logger.info(f"   Conversation ID: {conversation_id if conversation_id else 'New'}")
            
            # 使用智能搜尋路由器
            from .smart_search_router import SmartSearchRouter
            
            router = SmartSearchRouter()
            
            start_time = time.time()
            
            # 執行智能搜尋
            result = router.handle_smart_search(
                user_query=message,
                conversation_id=conversation_id,
                user_id=user_id,
                request=request
            )
            
            elapsed = time.time() - start_time
            
            # 處理結果
            if result.get('mode') == 'error':
                logger.error(f"❌ 智能搜尋失敗: {result.get('error')}")
                return Response({
                    'success': False,
                    'error': result.get('error', '搜尋失敗')
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # 成功回應
            logger.info(f"✅ 智能搜尋完成")
            logger.info(f"   模式: {result.get('mode')}")
            logger.info(f"   階段: {result.get('stage', 'N/A')}")
            logger.info(f"   是否降級: {result.get('is_fallback', False)}")
            logger.info(f"   響應時間: {elapsed:.2f} 秒")
            
            return Response({
                'success': True,
                'answer': result.get('answer', ''),
                'mode': result.get('mode'),
                'stage': result.get('stage'),
                'is_fallback': result.get('is_fallback', False),
                'fallback_reason': result.get('fallback_reason'),
                'message_id': result.get('message_id'),
                'conversation_id': result.get('conversation_id', conversation_id),
                'response_time': elapsed,
                'tokens': result.get('tokens', {}),
                'metadata': result.get('metadata', {}),  # ✅ 添加 metadata（包含引用來源）
                'search_results_count': len(result.get('search_results', []))
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"❌ Protocol Guide Chat API 錯誤: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': f'服務器錯誤: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
