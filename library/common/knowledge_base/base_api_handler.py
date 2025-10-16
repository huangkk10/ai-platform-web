"""
知識庫 API 處理器基礎類別
=========================

提供所有知識庫 API 端點的通用實現：
- Dify 外部知識庫搜索 API
- 知識庫聊天 API
- 配置資訊 API

子類只需要設定必要的類別屬性即可使用。
"""

import json
import time
import logging
from abc import ABC, abstractmethod
from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class BaseKnowledgeBaseAPIHandler(ABC):
    """
    知識庫 API 處理器基礎類別
    
    子類需要設定的屬性：
    - knowledge_id: 知識庫 ID（用於 Dify API）
    - config_key: 配置鍵名（用於獲取 Dify 配置）
    - source_table: 資料來源表名（用於向量搜索）
    - model_class: Django Model 類別
    
    使用範例：
    ```python
    class ProtocolGuideAPIHandler(BaseKnowledgeBaseAPIHandler):
        knowledge_id = 'protocol_guide_db'
        config_key = 'protocol_guide'
        source_table = 'protocol_guide'
        model_class = ProtocolGuide
    ```
    """
    
    # 子類必須設定這些屬性
    knowledge_id = None
    config_key = None
    source_table = None
    model_class = None
    
    @classmethod
    def get_knowledge_id(cls):
        """獲取知識庫 ID"""
        if cls.knowledge_id is None:
            raise NotImplementedError(f"{cls.__name__} must define 'knowledge_id' attribute")
        return cls.knowledge_id
    
    @classmethod
    def get_config_key(cls):
        """獲取配置鍵名"""
        if cls.config_key is None:
            raise NotImplementedError(f"{cls.__name__} must define 'config_key' attribute")
        return cls.config_key
    
    @classmethod
    def get_source_table(cls):
        """獲取資料來源表名"""
        if cls.source_table is None:
            raise NotImplementedError(f"{cls.__name__} must define 'source_table' attribute")
        return cls.source_table
    
    @classmethod
    def get_model_class(cls):
        """獲取 Model 類別"""
        if cls.model_class is None:
            raise NotImplementedError(f"{cls.__name__} must define 'model_class' attribute")
        return cls.model_class
    
    @classmethod
    def handle_dify_search_api(cls, request):
        """
        處理 Dify 知識庫外部搜索 API
        
        統一的 Dify 知識庫搜索實現，子類通常不需要覆寫。
        如果需要特殊的搜索邏輯，可以覆寫 perform_search 方法。
        """
        try:
            # 記錄請求來源
            logger.info(f"{cls.__name__} Dify API request from: {request.META.get('REMOTE_ADDR')}")
            
            # 解析請求數據
            data = json.loads(request.body) if request.body else {}
            query = data.get('query', '')
            knowledge_id = data.get('knowledge_id', cls.get_knowledge_id())
            retrieval_setting = data.get('retrieval_setting', {})
            
            top_k = retrieval_setting.get('top_k', 5)
            score_threshold = retrieval_setting.get('score_threshold', 0.0)
            
            logger.info(f"{cls.__name__} search - Query: {query}, Top K: {top_k}, Score threshold: {score_threshold}")
            
            # 驗證必要參數
            if not query:
                return Response({
                    'error_code': 2001,
                    'error_msg': 'Query parameter is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 執行搜索
            search_results = cls.perform_search(query, limit=top_k)
            
            # 過濾分數低於閾值的結果
            filtered_results = [
                result for result in search_results 
                if result.get('score', 0) >= score_threshold
            ]
            
            logger.info(f"{cls.__name__} search found {len(search_results)} results, {len(filtered_results)} after filtering")
            
            # 構建符合 Dify 規格的響應
            records = []
            for result in filtered_results:
                record = {
                    'content': result['content'],
                    'score': result['score'],
                    'title': result.get('title', ''),
                    'metadata': result.get('metadata', {})
                }
                records.append(record)
            
            response_data = {
                'records': records
            }
            
            logger.info(f"{cls.__name__} API response: Found {len(records)} results")
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except json.JSONDecodeError:
            return Response({
                'error_code': 1001,
                'error_msg': 'Invalid JSON format'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"{cls.__name__} Dify search error: {str(e)}")
            return Response({
                'error_code': 2001,
                'error_msg': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @classmethod
    def perform_search(cls, query, limit=5):
        """
        執行實際的搜索邏輯
        
        子類可以覆寫此方法來實現自定義的搜索邏輯。
        預設使用通用的搜索服務。
        
        Returns:
            list: 搜索結果列表，每個結果包含 content, score, title, metadata
        """
        try:
            # 嘗試使用搜索服務
            from .base_search_service import BaseKnowledgeBaseSearchService
            
            # 創建搜索服務實例（子類需要實現）
            search_service = cls.get_search_service()
            return search_service.search_knowledge(query, limit=limit)
            
        except Exception as e:
            logger.error(f"{cls.__name__} search service error: {str(e)}")
            # 使用備用搜索邏輯
            return cls.fallback_search(query, limit)
    
    @classmethod
    def get_search_service(cls):
        """
        獲取搜索服務實例
        
        子類需要實現此方法，返回對應的搜索服務實例
        """
        raise NotImplementedError(f"{cls.__name__} must implement 'get_search_service' method")
    
    @classmethod
    def fallback_search(cls, query, limit=5):
        """
        備用搜索邏輯（當搜索服務不可用時）
        
        使用基本的資料庫查詢進行搜索
        """
        try:
            model = cls.get_model_class()
            
            # 基本的資料庫搜索
            results = model.objects.filter(
                title__icontains=query
            ) | model.objects.filter(
                content__icontains=query
            )
            
            results = results[:limit]
            
            search_results = []
            for item in results:
                search_results.append({
                    'content': item.content if hasattr(item, 'content') else str(item),
                    'score': 0.5,  # 預設分數
                    'title': item.title if hasattr(item, 'title') else str(item),
                    'metadata': {
                        'id': item.id,
                        'created_at': item.created_at.isoformat() if hasattr(item, 'created_at') else None,
                    }
                })
            
            return search_results
            
        except Exception as e:
            logger.error(f"{cls.__name__} fallback search error: {str(e)}")
            return []
    
    @classmethod
    def handle_chat_api(cls, request):
        """
        處理知識庫聊天 API
        
        統一的聊天 API 實現。
        子類可以覆寫 get_chat_config 方法來自定義配置。
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
            
            # 獲取配置
            config = cls.get_chat_config()
            
            # 檢查必要配置
            api_url = config.get('api_url')
            api_key = config.get('api_key')
            
            if not api_url or not api_key:
                return Response({
                    'success': False,
                    'error': f'{cls.__name__} API 配置不完整'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # 記錄請求
            logger.info(f"{cls.__name__} chat request from user: {request.user.username if request.user.is_authenticated else 'guest'}")
            
            # 準備請求
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'inputs': {},
                'query': message,
                'response_mode': 'blocking',
                'user': f"{cls.get_source_table()}_user_{request.user.id if request.user.is_authenticated else 'guest'}"
            }
            
            if conversation_id:
                payload['conversation_id'] = conversation_id
            
            start_time = time.time()
            
            # 使用 library 中的 Dify 請求管理器
            try:
                from library.dify_integration import make_dify_request, process_dify_answer
                
                response = make_dify_request(
                    api_url=api_url,
                    headers=headers,
                    payload=payload,
                    timeout=config.get('timeout', 60),
                    handle_400_answer_format_error=True
                )
            except Exception as req_error:
                logger.error(f"{cls.__name__} request error: {str(req_error)}")
                return Response({
                    'success': False,
                    'error': f'{cls.__name__} API 請求錯誤: {str(req_error)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                answer = process_dify_answer(result.get('answer', ''))
                
                logger.info(f"{cls.__name__} chat success: response_time={elapsed:.2f}s")
                
                # 記錄對話（可選）
                cls.record_conversation(request, result, message, answer, elapsed)
                
                return Response({
                    'success': True,
                    'answer': answer,
                    'conversation_id': result.get('conversation_id', ''),
                    'message_id': result.get('message_id', ''),
                    'response_time': elapsed,
                    'metadata': result.get('metadata', {}),
                    'usage': result.get('usage', {}),
                }, status=status.HTTP_200_OK)
            else:
                error_msg = f"{cls.__name__} API 錯誤: {response.status_code} - {response.text}"
                logger.error(error_msg)
                
                return Response({
                    'success': False,
                    'error': error_msg
                }, status=response.status_code)
            
        except Exception as e:
            logger.error(f"{cls.__name__} chat error: {str(e)}")
            return Response({
                'success': False,
                'error': f'{cls.__name__} 服務器錯誤: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @classmethod
    def get_chat_config(cls):
        """
        獲取聊天配置
        
        子類可以覆寫此方法來提供自定義配置
        """
        try:
            from library.config import get_config_by_key
            config_obj = get_config_by_key(cls.get_config_key())
            return config_obj.to_dict() if hasattr(config_obj, 'to_dict') else config_obj
        except Exception as e:
            logger.error(f"{cls.__name__} config error: {str(e)}")
            return {}
    
    @classmethod
    def record_conversation(cls, request, result, message, answer, response_time):
        """
        記錄對話（可選功能）
        
        子類可以覆寫此方法來實現自定義的對話記錄邏輯
        """
        try:
            from library.conversation_management import (
                CONVERSATION_MANAGEMENT_AVAILABLE, 
                record_complete_exchange
            )
            
            if CONVERSATION_MANAGEMENT_AVAILABLE:
                record_complete_exchange(
                    request=request,
                    session_id=result.get('conversation_id', ''),
                    user_message=message,
                    assistant_message=answer,
                    response_time=response_time,
                    token_usage=result.get('usage', {}),
                    metadata={
                        'dify_message_id': result.get('message_id', ''),
                        'knowledge_base': cls.get_source_table(),
                    }
                )
        except Exception as e:
            logger.warning(f"{cls.__name__} conversation recording failed: {str(e)}")
    
    @classmethod
    def handle_config_api(cls, request):
        """
        處理配置資訊 API
        
        返回安全的配置信息（不包含敏感數據如 API key）
        """
        try:
            config = cls.get_chat_config()
            
            # 移除敏感資訊
            safe_config = {k: v for k, v in config.items() if k not in ['api_key', 'api_secret']}
            
            return Response({
                'success': True,
                'config': safe_config
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"{cls.__name__} config API error: {str(e)}")
            return Response({
                'success': False,
                'error': f'獲取 {cls.__name__} 配置失敗: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
