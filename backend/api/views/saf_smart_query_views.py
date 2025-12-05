"""
SAF Smart Query API Views
=========================

提供 LLM Smart API Router 的 API 入口點。

功能：
1. 智能查詢：自動分析用戶意圖，路由到正確的 API
2. 回答生成：將查詢結果轉換為自然語言回答
3. 健康檢查：檢查服務狀態

入口：
- POST /api/saf/smart-query/ - 智能查詢主入口
- GET /api/saf/smart-query/health/ - 健康檢查
- GET /api/saf/smart-query/intents/ - 獲取支援的意圖類型

作者：AI Platform Team
創建日期：2025-12-05
"""

import logging
import time
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)


@csrf_exempt
@api_view(['POST'])
@authentication_classes([])  # 禁用認證（避免 SessionAuthentication 的 CSRF 檢查）
@permission_classes([AllowAny])  # 允許外部調用（Dify 整合用）
def smart_query(request):
    """
    SAF 智能查詢 API
    
    POST /api/saf/smart-query/
    
    Request Body:
    {
        "query": "用戶問題（如：WD 有哪些專案？）",
        "user_id": "可選的用戶識別碼"
    }
    
    Response:
    {
        "success": true,
        "query": "原始問題",
        "intent": {
            "type": "query_projects_by_customer",
            "parameters": {"customer": "WD"},
            "confidence": 0.95,
            "is_valid": true
        },
        "result": {
            "status": "success",
            "data": [...],
            "count": 5,
            "message": "找到 5 個 WD 的專案"
        },
        "answer": {
            "answer": "**WD** 目前擁有 **5** 個專案：\n\n...",
            "table": [...],
            "summary": "WD 擁有 5 個專案"
        },
        "metadata": {
            "query_time_ms": 1234.56,
            "user_id": "xxx",
            "source": "saf_smart_query"
        }
    }
    """
    start_time = time.time()
    
    try:
        # 解析請求
        data = request.data
        query = data.get('query', '').strip()
        user_id = data.get('user_id', str(request.user.id) if request.user else 'anonymous')
        
        # 驗證查詢
        if not query:
            return Response(
                {
                    "success": False,
                    "error": "查詢內容不能為空",
                    "error_code": "EMPTY_QUERY"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        logger.info(f"[Smart Query] 收到查詢: '{query}' (user={user_id})")
        
        # 導入並執行智能查詢
        from library.saf_integration.smart_query import (
            SmartQueryService,
            SAFResponseGenerator
        )
        
        # 執行查詢
        service = SmartQueryService()
        query_result = service.query(query, user_id)
        
        # 生成回答
        generator = SAFResponseGenerator()
        answer = generator.generate(query_result)
        
        # 組合最終結果
        elapsed_time = (time.time() - start_time) * 1000
        
        response_data = {
            "success": query_result.get('success', False),
            "query": query,
            "intent": query_result.get('intent', {}),
            "result": query_result.get('result', {}),
            "answer": answer,
            "metadata": {
                **query_result.get('metadata', {}),
                "total_time_ms": round(elapsed_time, 2)
            }
        }
        
        logger.info(
            f"[Smart Query] 查詢完成: "
            f"intent={response_data['intent'].get('type', 'unknown')}, "
            f"success={response_data['success']}, "
            f"time={elapsed_time:.2f}ms"
        )
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        elapsed_time = (time.time() - start_time) * 1000
        logger.error(f"[Smart Query] 查詢失敗: {str(e)}", exc_info=True)
        
        return Response(
            {
                "success": False,
                "error": str(e),
                "error_code": "QUERY_FAILED",
                "metadata": {
                    "total_time_ms": round(elapsed_time, 2)
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def smart_query_health(request):
    """
    SAF Smart Query 健康檢查
    
    GET /api/saf/smart-query/health/
    
    Response:
    {
        "status": "healthy",
        "components": {
            "intent_analyzer": "healthy",
            "query_router": "healthy",
            "saf_api": "healthy",
            "dify_api": "healthy"
        },
        "version": "1.0.0"
    }
    """
    try:
        components = {}
        
        # 檢查 Smart Query 模組
        try:
            from library.saf_integration.smart_query import (
                SAFIntentAnalyzer,
                QueryRouter
            )
            
            # 嘗試初始化
            analyzer = SAFIntentAnalyzer()
            router = QueryRouter()
            
            components['intent_analyzer'] = 'healthy'
            components['query_router'] = 'healthy'
        except Exception as e:
            logger.error(f"Smart Query 模組檢查失敗: {e}")
            components['intent_analyzer'] = f'unhealthy: {str(e)}'
            components['query_router'] = f'unhealthy: {str(e)}'
        
        # 檢查 SAF API
        try:
            from library.saf_integration.api_client import SAFAPIClient
            client = SAFAPIClient()
            health_result = client.health_check()
            components['saf_api'] = health_result.get('status', 'unknown')
        except Exception as e:
            logger.error(f"SAF API 檢查失敗: {e}")
            components['saf_api'] = f'unhealthy: {str(e)}'
        
        # 檢查 Dify 配置
        try:
            from library.config.dify_config_manager import (
                get_saf_intent_analyzer_config,
                get_saf_analyzer_config
            )
            intent_config = get_saf_intent_analyzer_config()
            analyzer_config = get_saf_analyzer_config()
            
            if intent_config.validate() and analyzer_config.validate():
                components['dify_config'] = 'healthy'
            else:
                components['dify_config'] = 'unhealthy: config validation failed'
        except Exception as e:
            logger.error(f"Dify 配置檢查失敗: {e}")
            components['dify_config'] = f'unhealthy: {str(e)}'
        
        # 判斷整體狀態
        all_healthy = all(
            v == 'healthy' for v in components.values()
        )
        
        return Response({
            "status": "healthy" if all_healthy else "degraded",
            "components": components,
            "version": "1.0.0"
        })
        
    except Exception as e:
        logger.error(f"健康檢查失敗: {str(e)}")
        return Response({
            "status": "unhealthy",
            "error": str(e),
            "version": "1.0.0"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def smart_query_intents(request):
    """
    獲取支援的意圖類型
    
    GET /api/saf/smart-query/intents/
    
    Response:
    {
        "intents": [
            {
                "type": "query_projects_by_customer",
                "description": "按客戶查詢專案",
                "required_parameters": ["customer"],
                "example": "WD 有哪些專案？"
            },
            ...
        ]
    }
    """
    try:
        from library.saf_integration.smart_query.intent_types import IntentType
        
        intent_info = []
        
        examples = {
            IntentType.QUERY_PROJECTS_BY_CUSTOMER: "WD 有哪些專案？",
            IntentType.QUERY_PROJECTS_BY_CONTROLLER: "SM2264 控制器用在哪些專案？",
            IntentType.QUERY_PROJECT_DETAIL: "DEMETER 專案的詳細資訊",
            IntentType.QUERY_PROJECT_SUMMARY: "DEMETER 的測試結果如何？",
            IntentType.COUNT_PROJECTS: "WD 有幾個專案？",
            IntentType.LIST_ALL_CUSTOMERS: "有哪些客戶？",
            IntentType.LIST_ALL_CONTROLLERS: "有哪些控制器？",
        }
        
        for intent in IntentType:
            if intent != IntentType.UNKNOWN:
                intent_info.append({
                    "type": intent.value,
                    "description": intent.get_description(),
                    "required_parameters": intent.get_required_parameters(),
                    "optional_parameters": intent.get_optional_parameters(),
                    "example": examples.get(intent, "")
                })
        
        return Response({
            "intents": intent_info,
            "count": len(intent_info)
        })
        
    except Exception as e:
        logger.error(f"獲取意圖類型失敗: {str(e)}")
        return Response({
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def smart_query_analyze(request):
    """
    僅執行意圖分析（不執行查詢）
    
    POST /api/saf/smart-query/analyze/
    
    Request Body:
    {
        "query": "用戶問題"
    }
    
    Response:
    {
        "intent": "query_projects_by_customer",
        "parameters": {"customer": "WD"},
        "confidence": 0.95,
        "is_valid": true
    }
    
    用途：測試意圖分析結果，無需實際調用 SAF API
    """
    try:
        query = request.data.get('query', '').strip()
        
        if not query:
            return Response(
                {"error": "查詢內容不能為空"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from library.saf_integration.smart_query.intent_analyzer import SAFIntentAnalyzer
        
        analyzer = SAFIntentAnalyzer()
        user_id = str(request.user.id) if request.user else 'anonymous'
        
        result = analyzer.analyze(query, user_id)
        
        return Response({
            "query": query,
            "intent": result.intent.value,
            "parameters": result.parameters,
            "confidence": result.confidence,
            "is_valid": result.is_valid(),
            "raw_response": result.raw_response
        })
        
    except Exception as e:
        logger.error(f"意圖分析失敗: {str(e)}")
        return Response({
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
