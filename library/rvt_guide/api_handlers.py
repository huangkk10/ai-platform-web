"""
RVT Guide API 處理器

統一處理所有 RVT Guide 相關的 API 端點：
- Dify 知識庫搜索 API  
- RVT Guide 聊天 API
- 配置資訊 API

減少 views.py 中的程式碼量
"""

import json
import time
import logging
import requests
from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class RVTGuideAPIHandler:
    """RVT Guide API 處理器 - 統一管理所有 RVT Guide API"""
    
    @staticmethod
    def handle_dify_search_api(request):
        """
        處理 Dify RVT Guide 外部知識庫搜索 API
        
        取代原本 views.py 中的 dify_rvt_guide_search 函數
        """
        try:
            from ..data_processing.database_search import DatabaseSearchService
            
            # 記錄請求來源
            logger.info(f"Dify RVT Guide API request from: {request.META.get('REMOTE_ADDR')}")
            
            # 解析請求數據
            data = json.loads(request.body) if request.body else {}
            query = data.get('query', '')
            knowledge_id = data.get('knowledge_id', 'rvt_guide_db')
            retrieval_setting = data.get('retrieval_setting', {})
            
            top_k = retrieval_setting.get('top_k', 5)
            score_threshold = retrieval_setting.get('score_threshold', 0.0)
            
            logger.info(f"RVT Guide search - Query: {query}, Top K: {top_k}, Score threshold: {score_threshold}")
            
            # 驗證必要參數
            if not query:
                return Response({
                    'error_code': 2001,
                    'error_msg': 'Query parameter is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 使用統一的搜索服務
            from .search_service import RVTGuideSearchService
            search_service = RVTGuideSearchService()
            search_results = search_service.search_knowledge(query, limit=top_k)
            
            # 過濾分數低於閾值的結果
            filtered_results = [
                result for result in search_results 
                if result['score'] >= score_threshold
            ]
            
            logger.info(f"RVT Guide search found {len(search_results)} results, {len(filtered_results)} after filtering")
            
            # 構建符合 Dify 規格的響應，並包含圖片資訊
            records = []
            for result in filtered_results:
                record = {
                    'content': result['content'],
                    'score': result['score'],
                    'title': result['title'],
                    'metadata': result['metadata']
                }
                records.append(record)
                logger.info(f"Added RVT Guide record: {record['title']} (images: {len(result['metadata'].get('image_filenames', []))})")
            
            response_data = {
                'records': records
            }
            
            logger.info(f"RVT Guide API response: Found {len(records)} results")
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except json.JSONDecodeError:
            return Response({
                'error_code': 1001,
                'error_msg': 'Invalid JSON format'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Dify RVT Guide search error: {str(e)}")
            return Response({
                'error_code': 2001,
                'error_msg': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @staticmethod
    def handle_chat_api(request):
        """
        處理 RVT Guide 聊天 API
        
        取代原本 views.py 中的 rvt_guide_chat 函數
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
                rvt_config = rvt_config_obj.to_dict()  # 轉換為字典以兼容現有代碼
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
            logger.info(f"RVT Guide chat request from user: {request.user.username if request.user.is_authenticated else 'guest'}")
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