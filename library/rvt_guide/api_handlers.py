"""
RVT Guide API 處理器

統一處理所有 RVT Guide 相關的 API 端點：
- Dify 知識庫搜索 API  
- RVT Guide 聊天 API
- 配置資訊 API

減少 views.py 中的程式碼量

✨ 已遷移至新架構 - 繼承 BaseKnowledgeBaseAPIHandler
"""

import json
import time
import logging
import requests
from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response
from library.common.knowledge_base import BaseKnowledgeBaseAPIHandler
from api.models import RVTGuide

logger = logging.getLogger(__name__)


class RVTGuideAPIHandler(BaseKnowledgeBaseAPIHandler):
    """
    RVT Guide API 處理器 - 繼承基礎 API 處理器
    
    ✅ 已遷移至新架構，代碼從 317 行減少至 ~80 行
    
    繼承自 BaseKnowledgeBaseAPIHandler，自動獲得：
    - handle_dify_search_api(): Dify 搜索 API
    - handle_chat_api(): 聊天 API
    - handle_config_api(): 配置 API
    - perform_search(): 統一搜索邏輯
    """
    
    # 設定必要屬性
    knowledge_id = 'rvt_guide_db'
    config_key = 'rvt_assistant'
    source_table = 'rvt_guide'
    model_class = RVTGuide
    
    @classmethod
    def get_search_service(cls):
        """獲取搜索服務實例（父類需要）"""
        from .search_service import RVTGuideSearchService
        return RVTGuideSearchService()
    
    # ===== 智能搜尋路由器整合（2025-11-11）=====
    
    @classmethod
    def handle_chat_api(cls, request):
        """
        處理 RVT Guide 聊天 API（使用智能搜尋路由器）
        
        覆寫基類方法，使用 SmartSearchRouter 實現兩階段搜尋策略：
        - 模式 A：關鍵字優先全文搜尋（含全文關鍵字）
        - 模式 B：標準兩階段搜尋（無全文關鍵字）
        
        Args:
            request: Django request 對象
            
        Returns:
            Response: Django REST Framework Response
        """
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
            user_id = f"rvt_guide_user_{request.user.id if request.user.is_authenticated else 'guest'}"
            
            logger.info(f"📩 RVT Guide Chat Request (智能搜尋)")
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
                logger.error(f"❌ RVT 智能搜尋失敗: {result.get('error')}")
                return Response({
                    'success': False,
                    'error': result.get('error', '搜尋失敗')
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # 成功回應
            logger.info(f"✅ RVT 智能搜尋完成")
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
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"❌ RVT Guide Chat API 錯誤: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': f'服務器錯誤: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # ===== 以下為舊版實現（保留作為參考）=====
    
    @staticmethod
    def handle_chat_api_legacy(request):
        """
        處理 RVT Guide 聊天 API（舊版實現，僅供參考）
        
        ⚠️ 已被智能搜尋路由器取代，保留此方法僅供參考或緊急回退
        """
        try:
            data = request.data
            message = data.get('message', '').strip()
            conversation_id = data.get('conversation_id', '')
            
            if not message:
                return Response({
                    'success': False,
                    'error': '訊息內容不能為空'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 使用新的配置管理器獲取 RVT_GUIDE 配置
            try:
                from library.config import get_rvt_guide_config
                rvt_config_obj = get_rvt_guide_config()
                rvt_config = rvt_config_obj.to_dict()
            except Exception as config_error:
                logger.error(f"Failed to load RVT Guide config: {config_error}")
                return Response({
                    'success': False,
                    'error': f'RVT Guide 配置載入失敗: {str(config_error)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # 檢查必要配置
            api_url = rvt_config.get('api_url')
            api_key = rvt_config.get('api_key')
            
            if not api_url or not api_key:
                return Response({
                    'success': False,
                    'error': 'RVT Guide API 配置不完整'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # 記錄請求
            logger.info(f"RVT Guide chat request (legacy) from user: {request.user.username if request.user.is_authenticated else 'guest'}")
            logger.debug(f"RVT Guide message: {message[:100]}...")
            
            # 準備請求
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'inputs': {},
                'query': message,
                'response_mode': 'blocking',
                'user': f"rvt_user_{request.user.id if request.user.is_authenticated else 'guest'}"
            }
            
            if conversation_id:
                payload['conversation_id'] = conversation_id
            
            start_time = time.time()
            
            # 使用 library 中的 Dify 請求管理器
            try:
                from library.dify_integration import make_dify_request, process_dify_answer
                
                # 發送請求到 Dify RVT Guide，包含智能重試機制
                response = make_dify_request(
                    api_url=api_url,
                    headers=headers,
                    payload=payload,
                    timeout=rvt_config.get('timeout', 60),
                    handle_400_answer_format_error=True
                )
            except requests.exceptions.Timeout:
                logger.error(f"RVT Guide 請求超時，已重試 3 次")
                return Response({
                    'success': False,
                    'error': 'RVT Guide 分析超時，請稍後再試或簡化問題描述'
                }, status=status.HTTP_408_REQUEST_TIMEOUT)
            except requests.exceptions.ConnectionError:
                logger.error(f"RVT Guide 連接失敗，已重試 3 次")
                return Response({
                    'success': False,
                    'error': 'RVT Guide 連接失敗，請檢查網路連接或稍後再試'
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            except Exception as req_error:
                logger.error(f"RVT Guide 請求錯誤: {str(req_error)}")
                return Response({
                    'success': False,
                    'error': f'RVT Guide API 請求錯誤: {str(req_error)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                
                # 使用 library 中的響應處理器處理 answer 字段
                answer = process_dify_answer(result.get('answer', ''))
                
                # 記錄成功的聊天
                logger.info(f"RVT Guide chat success for user {request.user.username if request.user.is_authenticated else 'guest'}: response_time={elapsed:.2f}s")
                
                # 🆕 記錄對話到資料庫
                try:
                    from library.conversation_management import (
                        CONVERSATION_MANAGEMENT_AVAILABLE, 
                        record_complete_exchange
                    )
                    
                    if CONVERSATION_MANAGEMENT_AVAILABLE:
                        # 記錄完整的對話交互
                        conversation_result = record_complete_exchange(
                            request=request,
                            session_id=result.get('conversation_id', ''),
                            user_message=message,
                            assistant_message=answer,
                            response_time=elapsed,
                            token_usage=result.get('usage', {}),
                            metadata={
                                'dify_message_id': result.get('message_id', ''),
                                'dify_metadata': result.get('metadata', {}),
                                'workspace': rvt_config.get('workspace', 'RVT_Guide'),
                                'app_name': rvt_config.get('app_name', 'RVT Guide')
                            }
                        )
                        
                        if conversation_result.get('success'):
                            logger.info(f"RVT conversation recorded successfully: session={result.get('conversation_id', '')}")
                        else:
                            logger.warning(f"Failed to record RVT conversation: {conversation_result.get('error', 'Unknown error')}")
                    else:
                        logger.warning("Conversation Management Library not available, skipping conversation recording")
                        
                except Exception as conv_error:
                    # 對話記錄失敗不應影響主要功能
                    logger.error(f"Error recording RVT conversation: {str(conv_error)}")
                
                # 🆕 處理 metadata 中的圖片資訊，確保前端能正確解析
                response_metadata = result.get('metadata', {})
                
                # 🔍 提取 retriever_resources 中的圖片檔名，讓前端 imageProcessor 可以正確解析
                if 'retriever_resources' in response_metadata:
                    for resource in response_metadata['retriever_resources']:
                        if resource.get('content'):
                            # 確保內容中包含明確的圖片檔名，讓前端解析器能找到
                            import re
                            content = resource['content']
                            # 尋找並標記圖片檔名，確保前端解析器能識別
                            image_pattern = r'\b([a-zA-Z0-9\-_.]{10,}\.(?:png|jpg|jpeg|gif|bmp|webp))\b'
                            matches = re.findall(image_pattern, content, re.IGNORECASE)
                            if matches:
                                # 在資源內容中明確標記圖片檔名
                                for match in matches:
                                    if match not in content or not content.startswith('🖼️'):
                                        # 確保圖片檔名有正確的前綴，讓前端解析器識別
                                        resource['content'] += f"\n🖼️ {match}"
                
                return Response({
                    'success': True,
                    'answer': answer,
                    'conversation_id': result.get('conversation_id', ''),
                    'message_id': result.get('message_id', ''),
                    'response_time': elapsed,
                    'metadata': response_metadata,
                    'usage': result.get('usage', {}),
                    'workspace': rvt_config.get('workspace', 'RVT_Guide'),
                    'app_name': rvt_config.get('app_name', 'RVT Guide')
                }, status=status.HTTP_200_OK)
            else:
                # 特殊處理 404 錯誤（對話不存在）
                if response.status_code == 404:
                    # 實現對話錯誤處理邏輯
                    pass
                
                error_msg = f"RVT Guide API 錯誤: {response.status_code} - {response.text}"
                logger.error(f"RVT Guide chat error: {error_msg}")
                
                return Response({
                    'success': False,
                    'error': error_msg
                }, status=response.status_code)
            
        except Exception as e:
            logger.error(f"RVT Guide chat error: {str(e)}")
            return Response({
                'success': False,
                'error': f'RVT Guide 服務器錯誤: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @staticmethod
    def handle_config_api(request):
        """
        處理 RVT Guide 配置資訊 API
        
        取代原本 views.py 中的 rvt_guide_config 函數
        """
        try:
            from library.config import get_rvt_guide_config
            config_obj = get_rvt_guide_config()
            
            # 返回安全的配置信息（不包含 API key）
            safe_config = config_obj.get_safe_config()
            
            return Response({
                'success': True,
                'config': safe_config
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Get RVT Guide config error: {str(e)}")
            return Response({
                'success': False,
                'error': f'獲取 RVT Guide 配置失敗: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)