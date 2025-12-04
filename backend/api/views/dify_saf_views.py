"""
Dify SAF 外部知識庫 API Views

提供 Dify 外部知識庫的 API 入口點

入口：POST /api/dify/saf/retrieval/

支援的 knowledge_id：
- saf_projects: 專案搜尋（完整資訊）
- saf_summary: 專案統計
- saf_project_names: 專案名稱清單（輕量級）

作者：AI Platform Team
創建日期：2025-12-04
"""

import logging
import time
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from library.saf_integration import (
    get_saf_knowledge_handler,
    get_supported_knowledge_ids,
    check_saf_health
)

logger = logging.getLogger(__name__)

# SAF API Key 配置（可在 settings.py 中覆蓋）
SAF_API_KEY = getattr(settings, 'SAF_EXTERNAL_API_KEY', 'saf-api-key-2025')


def verify_api_key(request) -> bool:
    """
    驗證 Dify 傳來的 API Key
    
    Dify 會在 Header 中帶入：Authorization: Bearer <api_key>
    
    Returns:
        是否驗證通過
    """
    auth_header = request.headers.get('Authorization', '')
    
    if not auth_header:
        return False
    
    # 解析 Bearer token
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]  # 移除 'Bearer ' 前綴
        return token == SAF_API_KEY
    
    return False


@api_view(['POST'])
@permission_classes([AllowAny])  # 使用自訂 API Key 驗證
def saf_retrieval(request):
    """
    Dify SAF 外部知識庫檢索 API
    
    POST /api/dify/saf/retrieval/
    
    Headers:
        Authorization: Bearer <api_key>
    
    Request Body (Dify 標準格式):
    {
        "knowledge_id": "saf_projects",  // 知識庫 ID
        "query": "搜尋關鍵字",
        "retrieval_setting": {
            "top_k": 10,            // 返回結果數量
            "score_threshold": 0.3  // 分數閾值
        }
    }
    
    Response (Dify 標準格式):
    {
        "records": [
            {
                "content": "內容",
                "score": 0.85,
                "title": "標題",
                "metadata": {...}
            }
        ]
    }
    """
    start_time = time.time()
    
    try:
        # 驗證 API Key
        if not verify_api_key(request):
            logger.warning("[SAF API] API Key 驗證失敗")
            return Response(
                {"error": "Invalid API Key"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # 解析請求
        data = request.data
        
        knowledge_id = data.get('knowledge_id', '')
        query = data.get('query', '')
        retrieval_setting = data.get('retrieval_setting', {})
        
        # 記錄請求
        logger.info(
            f"[SAF API] 收到請求: "
            f"knowledge_id='{knowledge_id}', "
            f"query='{query[:50]}...' " if len(query) > 50 else f"query='{query}', "
            f"retrieval_setting={retrieval_setting}"
        )
        
        # 驗證必要參數
        if not knowledge_id:
            logger.warning("[SAF API] 缺少 knowledge_id")
            return Response(
                {"error": "缺少 knowledge_id 參數"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 獲取 handler 並處理請求
        handler = get_saf_knowledge_handler()
        result = handler.handle_retrieval(
            knowledge_id=knowledge_id,
            query=query,
            retrieval_setting=retrieval_setting
        )
        
        # 計算響應時間
        elapsed_time = time.time() - start_time
        
        # 記錄結果
        record_count = len(result.get('records', []))
        logger.info(
            f"[SAF API] 請求完成: "
            f"knowledge_id='{knowledge_id}', "
            f"返回 {record_count} 條記錄, "
            f"耗時 {elapsed_time:.2f}s"
        )
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"[SAF API] 請求處理失敗: {str(e)}", exc_info=True)
        return Response(
            {
                "records": [],
                "error": f"處理請求時發生錯誤: {str(e)}"
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def saf_health(request):
    """
    SAF 服務健康檢查 API
    
    GET /api/dify/saf/health/
    
    Response:
    {
        "status": "healthy",
        "saf_server": {...},
        "supported_knowledge_ids": ["saf_projects", "saf_summary", "saf_project_names"]
    }
    """
    try:
        handler = get_saf_knowledge_handler()
        health_info = handler.health_check()
        
        return Response(health_info, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"[SAF API] 健康檢查失敗: {str(e)}")
        return Response(
            {
                "status": "error",
                "error": str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def saf_endpoints(request):
    """
    獲取支援的知識庫端點資訊
    
    GET /api/dify/saf/endpoints/
    
    Response:
    {
        "supported_knowledge_ids": [
            {
                "id": "saf_projects",
                "description": "SAF 專案搜尋...",
                "example_query": "WD"
            }
        ]
    }
    """
    try:
        knowledge_ids = get_supported_knowledge_ids()
        
        endpoints_info = [
            {
                "id": "saf_projects",
                "description": "SAF 專案搜尋 - 搜尋專案名稱、客戶、儲存類型等",
                "example_query": "WD",
                "fields": ["projectName", "customer", "storageType", "capacity"]
            },
            {
                "id": "saf_summary",
                "description": "SAF 專案統計 - 查詢專案的測試摘要資訊",
                "example_query": "DEMETER",
                "fields": ["totalTests", "passedTests", "failedTests", "passRate"]
            },
            {
                "id": "saf_project_names",
                "description": "SAF 專案名稱清單 - 輕量級查詢，快速取得專案名稱",
                "example_query": "Micron",
                "fields": ["projectName", "customer"]
            },
            {
                "id": "saf_db",
                "description": "SAF 專案搜尋（向後相容）",
                "example_query": "Samsung",
                "fields": ["projectName", "customer"]
            }
        ]
        
        return Response({
            "supported_knowledge_ids": endpoints_info,
            "total_count": len(endpoints_info)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"[SAF API] 獲取端點資訊失敗: {str(e)}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
