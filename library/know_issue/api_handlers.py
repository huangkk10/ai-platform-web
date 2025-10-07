"""
Know Issue API Handlers - API 處理器
====================================

處理 Know Issue 相關的 API 請求：
- Dify 知識庫搜索 API
- 外部 API 整合
"""

import json
import logging
from typing import List, Dict, Any
from rest_framework import status
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class KnowIssueAPIHandler:
    """Know Issue API 處理器 - 處理外部 API 請求"""
    
    def __init__(self):
        self.logger = logger
    
    def handle_dify_know_issue_search_api(self, request) -> Response:
        """
        處理 Dify Know Issue 搜索 API
        
        Args:
            request: HTTP 請求
            
        Returns:
            Response: DRF 回應
        """
        try:
            # 記錄請求來源
            self.logger.info(f"Dify Know Issue API request from: {request.META.get('REMOTE_ADDR')}")
            
            # 解析請求數據
            data = json.loads(request.body) if request.body else {}
            query = data.get('query', '')
            knowledge_id = data.get('knowledge_id', 'know_issue_db')
            retrieval_setting = data.get('retrieval_setting', {})
            
            top_k = retrieval_setting.get('top_k', 5)
            score_threshold = retrieval_setting.get('score_threshold', 0.0)
            
            self.logger.info(f"Know Issue search - Query: {query}, Top K: {top_k}, Score threshold: {score_threshold}")
            
            # 驗證必要參數
            if not query:
                return Response({
                    'error_code': 2001,
                    'error_msg': 'Query parameter is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 搜索 Know Issue 資料
            search_results = self._search_know_issue_knowledge(query, limit=top_k)
            
            # 過濾分數低於閾值的結果
            filtered_results = [
                result for result in search_results 
                if result['score'] >= score_threshold
            ]
            
            self.logger.info(f"Know Issue search found {len(search_results)} results, {len(filtered_results)} after filtering")
            
            # 構建符合 Dify 規格的響應
            records = []
            for result in filtered_results:
                record = {
                    'content': result['content'],
                    'score': result['score'],
                    'title': result['title'],
                    'metadata': result['metadata']
                }
                records.append(record)
                self.logger.info(f"Added Know Issue record: {record['title']}")
            
            response_data = {
                'records': records
            }
            
            self.logger.info(f"Know Issue API response: Found {len(records)} results")
            return Response(response_data, status=status.HTTP_200_OK)
            
        except json.JSONDecodeError:
            return Response({
                'error_code': 1001,
                'error_msg': 'Invalid JSON format'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            self.logger.error(f"Dify Know Issue search error: {str(e)}")
            return Response({
                'error_code': 2001,
                'error_msg': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _search_know_issue_knowledge(self, query_text: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        搜索 Know Issue 知識
        
        Args:
            query_text: 搜索文字
            limit: 結果數量限制
            
        Returns:
            List[Dict[str, Any]]: 搜索結果
        """
        try:
            # 嘗試使用 library 中的搜索服務
            try:
                from library.data_processing.database_search import DatabaseSearchService
                service = DatabaseSearchService()
                return service.search_know_issue_knowledge(query_text, limit)
            except ImportError:
                # 如果 library 不可用，返回空結果
                self.logger.warning("DatabaseSearchService 不可用")
                return []
                
        except Exception as e:
            self.logger.error(f"Know Issue 搜索失敗: {str(e)}")
            return []