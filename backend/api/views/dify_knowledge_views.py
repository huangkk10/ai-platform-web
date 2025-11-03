"""
Dify 外部知識庫 API Views
========================================

本模組包含所有 Dify 外部知識庫相關的 API 端點。

重構說明：
- 使用依賴注入模式，消除循環依賴
- Library 層不再依賴 api.views
- 搜索函數從 library 直接獲取並注入到 Handler

主要 API：
- dify_knowledge_search()          - 統一知識庫搜索入口
- dify_know_issue_search()         - Know Issue 知識庫
- dify_ocr_storage_benchmark_search() - OCR 知識庫
- dify_rvt_guide_search()          - RVT Guide 知識庫
- dify_protocol_guide_search()     - Protocol Guide 知識庫

Created: 2025-10-17
Author: AI Platform Team
"""

import json
import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.db import models

logger = logging.getLogger(__name__)

# 導入 Library 服務
try:
    from library.dify_knowledge import (
        DifyKnowledgeSearchHandler,
        DIFY_KNOWLEDGE_LIBRARY_AVAILABLE
    )
    # 導入搜索服務
    from library.data_processing.database_search import (
        DatabaseSearchService,
        search_postgres_knowledge  # 獨立函數
    )
    from library.rvt_guide.search_service import RVTGuideSearchService
    from library.protocol_guide.search_service import ProtocolGuideSearchService
    
    # 導入 Know Issue Library
    from library.know_issue import (
        handle_dify_know_issue_search_api,
        KNOW_ISSUE_LIBRARY_AVAILABLE
    )
    
    # 導入 AI OCR Library
    from library.ai_ocr import (
        AIOCRAPIHandler,
        AI_OCR_LIBRARY_AVAILABLE,
        search_ocr_storage_benchmark_unified,
        fallback_dify_ocr_storage_benchmark_search
    )
    
    # 導入 RVT Guide Library (沒有 RVT_GUIDE_LIBRARY_AVAILABLE)
    from library.rvt_guide import (
        RVTGuideAPIHandler,
        fallback_dify_rvt_guide_search
    )
    RVT_GUIDE_LIBRARY_AVAILABLE = True  # 手動設置
    
    LIBRARIES_AVAILABLE = True
except ImportError as e:
    logger.error(f"導入 Library 失敗: {e}")
    DIFY_KNOWLEDGE_LIBRARY_AVAILABLE = False
    KNOW_ISSUE_LIBRARY_AVAILABLE = False
    AI_OCR_LIBRARY_AVAILABLE = False
    RVT_GUIDE_LIBRARY_AVAILABLE = False
    LIBRARIES_AVAILABLE = False

# 導入 Models（僅用於 Protocol Guide 的備用搜索）
try:
    from api.models import ProtocolGuide
except ImportError:
    ProtocolGuide = None


# ============= 依賴注入核心函數 =============

def get_search_functions_registry():
    """
    獲取搜索函數註冊表（依賴注入）
    
    這個函數創建並返回一個包含所有搜索服務的字典，
    用於注入到 DifyKnowledgeSearchHandler 中。
    
    Returns:
        dict: 搜索函數字典
            {
                'know_issue': callable,
                'rvt_guide': callable,
                'protocol_guide': callable,
                'ocr_benchmark': callable,
                'employee': callable,
            }
    """
    try:
        # 創建服務實例
        db_service = DatabaseSearchService()
        rvt_service = RVTGuideSearchService()
        protocol_service = ProtocolGuideSearchService()
        
        # 構建搜索函數字典
        search_functions = {
            'know_issue': db_service.search_know_issue_knowledge,
            'rvt_guide': rvt_service.search_knowledge,
            'protocol_guide': protocol_service.search_knowledge,
            'ocr_benchmark': db_service.search_ocr_storage_benchmark,
            'employee': search_postgres_knowledge,  # 使用獨立函數
        }
        
        logger.info("✅ 搜索函數註冊表創建成功")
        return search_functions
        
    except Exception as e:
        logger.error(f"創建搜索函數註冊表失敗: {e}")
        # 返回空字典，讓 Handler 使用內部備用機制
        return {}


def create_dify_search_handler():
    """
    創建配置好的 Dify 搜索處理器（依賴注入）
    
    使用依賴注入模式創建 Handler，避免循環依賴。
    
    Returns:
        DifyKnowledgeSearchHandler: 配置好的搜索處理器實例
    """
    try:
        # 獲取搜索函數註冊表
        search_functions = get_search_functions_registry()
        
        # 創建 Handler，注入搜索函數
        handler = DifyKnowledgeSearchHandler(search_functions=search_functions)
        
        logger.debug("✅ Dify 搜索處理器創建成功（使用依賴注入）")
        return handler
        
    except Exception as e:
        logger.error(f"創建 Dify 搜索處理器失敗: {e}")
        # 返回沒有注入的 Handler（使用內部備用機制）
        return DifyKnowledgeSearchHandler()


# ============= 搜索輔助函數（向後兼容） =============

def search_know_issue_knowledge(query_text, limit=5):
    """
    搜索 Know Issue 知識庫
    
    向後兼容函數：此函數保留是為了兼容性，
    實際搜索由 library/data_processing/database_search.py 執行。
    
    Args:
        query_text: 搜索關鍵字
        limit: 返回結果數量限制
        
    Returns:
        list: 搜索結果列表
    """
    try:
        if LIBRARIES_AVAILABLE:
            service = DatabaseSearchService()
            return service.search_know_issue_knowledge(query_text, limit)
        else:
            logger.warning("DatabaseSearchService 不可用，使用備用實現")
            return []
    except Exception as e:
        logger.error(f"Know Issue 搜索失敗: {str(e)}")
        return []


def search_rvt_guide_knowledge(query_text, limit=5):
    """
    搜索 RVT Guide 知識庫
    
    向後兼容函數：此函數保留是為了兼容性，
    實際搜索由 library/rvt_guide/search_service.py 執行。
    
    Args:
        query_text: 搜索關鍵字
        limit: 返回結果數量限制
        
    Returns:
        list: 搜索結果列表
    """
    try:
        if LIBRARIES_AVAILABLE:
            service = RVTGuideSearchService()
            return service.search_knowledge(query_text, limit=limit)
        else:
            logger.warning("RVTGuideSearchService 不可用，使用備用實現")
            return []
    except Exception as e:
        logger.error(f"RVT Guide 搜索失敗: {str(e)}")
        return []


def search_protocol_guide_knowledge(query_text, limit=5):
    """
    搜索 Protocol Guide 知識庫
    
    向後兼容函數：此函數保留是為了兼容性，
    實際搜索由 library/protocol_guide/search_service.py 執行。
    
    Args:
        query_text: 搜索關鍵字
        limit: 返回結果數量限制
        
    Returns:
        list: 搜索結果列表
    """
    try:
        if LIBRARIES_AVAILABLE:
            service = ProtocolGuideSearchService()
            return service.search_knowledge(query_text, limit=limit)
        else:
            logger.warning("ProtocolGuideSearchService 不可用，使用備用實現")
            return []
    except Exception as e:
        logger.error(f"Protocol Guide 搜索失敗: {str(e)}")
        return []


def search_ocr_storage_benchmark(query_text, limit=5):
    """
    搜索 OCR Storage Benchmark 資料
    
    向後兼容函數：此函數保留是為了兼容性，
    優先使用 library/ai_ocr/search_service.py。
    
    Args:
        query_text: 搜索關鍵字
        limit: 返回結果數量限制
        
    Returns:
        list: 搜索結果列表
    """
    try:
        if AI_OCR_LIBRARY_AVAILABLE and search_ocr_storage_benchmark_unified:
            # 優先使用 AI OCR library 中的統一搜索服務
            return search_ocr_storage_benchmark_unified(query_text, limit)
        elif LIBRARIES_AVAILABLE:
            # 備用：使用資料庫搜索服務
            service = DatabaseSearchService()
            return service.search_ocr_storage_benchmark(query_text, limit)
        else:
            logger.warning("所有搜索服務都不可用，使用最基本備用")
            return []
    except Exception as e:
        logger.error(f"OCR Storage Benchmark 搜索失敗: {str(e)}")
        return []


# ============= Dify 外部知識庫 API 端點 =============

@api_view(['POST'])
@permission_classes([])  # 公開 API，但會檢查 Authorization header
@csrf_exempt
def dify_knowledge_search(request):
    """
    Dify 統一知識庫搜索 API - 主要入口
    
    🌟 這是推薦使用的統一 API 端點，通過 knowledge_id 自動路由到對應的知識庫。
    
    請求格式：
        POST /api/dify/knowledge/retrieval/
        {
            "knowledge_id": "rvt_guide_db",  # 知識庫 ID
            "query": "Jenkins",               # 搜索查詢
            "retrieval_setting": {
                "top_k": 3,                   # 返回結果數量
                "score_threshold": 0.5        # 分數閾值
            }
        }
    
    支援的 knowledge_id：
        - employee_database, employee_db: 員工知識庫
        - know_issue_db, know_issue: Know Issue 知識庫
        - rvt_guide_db, rvt_guide: RVT Guide 知識庫
        - protocol_guide_db, protocol_guide: Protocol Guide 知識庫
        - ocr_storage_benchmark, ocr_benchmark: OCR 知識庫
    
    返回格式：
        {
            "records": [
                {
                    "content": "文檔內容...",
                    "score": 0.85,
                    "title": "文檔標題",
                    "metadata": {...}
                }
            ]
        }
    """
    try:
        if DIFY_KNOWLEDGE_LIBRARY_AVAILABLE:
            # 🎯 使用依賴注入創建 Handler
            handler = create_dify_search_handler()
            
            # 解析請求資料
            data = json.loads(request.body) if request.body else {}
            knowledge_id = data.get('knowledge_id', 'employee_database')
            query = data.get('query', '')
            retrieval_setting = data.get('retrieval_setting', {})
            
            # ⚠️ Dify 外部知識庫 API 不會傳遞 score_threshold，需要我們自己設定
            # 從請求中獲取，如果沒有則使用預設值 0.7
            score_threshold = retrieval_setting.get('score_threshold', 0.0)
            
            # 🔧 強制應用最低 threshold（防止低分結果）
            if score_threshold < 0.65:
                score_threshold = 0.7  # 強制使用 0.7 作為最低閾值
                logger.info(f"⚠️ Dify 未傳遞 score_threshold，強制使用 0.7")
            
            logger.info(f"📊 使用 score_threshold={score_threshold} 進行搜索")
            
            # 執行搜索
            result = handler.search(
                knowledge_id=knowledge_id,
                query=query,
                top_k=retrieval_setting.get('top_k', 5),
                score_threshold=score_threshold
            )
            
            logger.info(f"✅ 知識庫搜索成功: {knowledge_id}, query='{query}', results={len(result.get('records', []))}")
            return Response(result)
        else:
            # 備用實現
            logger.warning("Dify Knowledge Library 不可用，使用備用實現")
            try:
                from library.dify_knowledge.fallback_handlers import fallback_dify_knowledge_search
                return fallback_dify_knowledge_search(request)
            except ImportError:
                # 最終備用方案
                logger.error("Dify Knowledge Library 完全不可用")
                return Response({
                    'error_code': 2001,
                    'error_msg': 'Knowledge search service temporarily unavailable'
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
                
    except Exception as e:
        logger.error(f"Dify knowledge search error: {str(e)}", exc_info=True)
        return Response({
            'error_code': 2001,
            'error_msg': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([])  # 公開 API，但會檢查 Authorization header
@csrf_exempt
def dify_know_issue_search(request):
    """
    Dify Know Issue 外部知識庫 API 端點
    
    🔄 舊版 API，建議使用 dify_knowledge_search() 統一入口。
    
    請求格式：與 dify_knowledge_search 相同
    """
    try:
        if KNOW_ISSUE_LIBRARY_AVAILABLE and handle_dify_know_issue_search_api:
            # 使用 Know Issue library 中的 API 處理器
            return handle_dify_know_issue_search_api(request)
        else:
            # 使用備用實現
            logger.warning("Know Issue Library 不可用，使用備用實現")
            try:
                from library.know_issue.fallback_handlers import fallback_dify_know_issue_search
                return fallback_dify_know_issue_search(request)
            except ImportError:
                # 最終備用方案
                logger.error("Know Issue Library 完全不可用")
                return Response({
                    'error_code': 2001,
                    'error_msg': 'Know Issue search service temporarily unavailable'
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
    except Exception as e:
        logger.error(f"Dify Know Issue search error: {str(e)}", exc_info=True)
        return Response({
            'error_code': 2001,
            'error_msg': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([])  # 公開 API，但會檢查 Authorization header
@csrf_exempt
def dify_ocr_storage_benchmark_search(request):
    """
    Dify OCR Storage Benchmark 外部知識庫 API 端點
    
    🔄 舊版 API，建議使用 dify_knowledge_search() 統一入口。
    
    請求格式：與 dify_knowledge_search 相同
    """
    try:
        if AI_OCR_LIBRARY_AVAILABLE and AIOCRAPIHandler:
            # 使用 AI OCR library 中的 API 處理器
            return AIOCRAPIHandler.handle_dify_ocr_storage_benchmark_search_api(request)
        elif fallback_dify_ocr_storage_benchmark_search:
            # 使用 library 中維護的備用實現
            return fallback_dify_ocr_storage_benchmark_search(request)
        else:
            # library 完全不可用時的最終錯誤處理
            logger.error("AI OCR Library 完全不可用")
            return Response({
                'error_code': 2001,
                'error_msg': 'OCR Storage Benchmark search service temporarily unavailable'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
    except Exception as e:
        logger.error(f"Dify OCR Storage Benchmark search error: {str(e)}", exc_info=True)
        return Response({
            'error_code': 2001,
            'error_msg': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([])  # 公開 API，但會檢查 Authorization header
@csrf_exempt
def dify_rvt_guide_search(request):
    """
    Dify RVT Guide 外部知識庫搜索 API
    
    🔄 舊版 API，建議使用 dify_knowledge_search() 統一入口。
    
    請求格式：與 dify_knowledge_search 相同
    """
    try:
        if RVT_GUIDE_LIBRARY_AVAILABLE and RVTGuideAPIHandler:
            return RVTGuideAPIHandler.handle_dify_search_api(request)
        elif fallback_dify_rvt_guide_search:
            # 使用 library 中的備用實現
            return fallback_dify_rvt_guide_search(request)
        else:
            # library 完全不可用時的最終錯誤處理
            logger.error("RVT Guide library 完全不可用")
            return Response({
                'error_code': 2001,
                'error_msg': 'RVT Guide service temporarily unavailable'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        logger.error(f"Dify RVT Guide search error: {str(e)}", exc_info=True)
        return Response({
            'error_code': 2001,
            'error_msg': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([])  # 公開 API
@csrf_exempt
def dify_protocol_guide_search(request):
    """
    Dify Protocol Guide 知識庫搜索 API
    
    🔄 舊版 API，建議使用 dify_knowledge_search() 統一入口。
    
    請求格式：與 dify_knowledge_search 相同
    """
    try:
        # 嘗試從 library 導入 Protocol Guide API Handler
        try:
            from library.protocol_guide import ProtocolGuideAPIHandler
            if ProtocolGuideAPIHandler:
                return ProtocolGuideAPIHandler.handle_dify_search_api(request)
        except (ImportError, AttributeError):
            pass
        
        # 備用實現：直接搜索
        logger.warning("Protocol Guide Library 不可用，使用備用搜索")
        query = request.data.get('query', '')
        
        if ProtocolGuide:
            records = list(ProtocolGuide.objects.filter(
                models.Q(title__icontains=query) |
                models.Q(content__icontains=query) |
                models.Q(protocol_name__icontains=query)
            )[:5].values('id', 'title', 'protocol_name', 'content'))
            
            return Response({
                'records': [{
                    'content': f"{r['protocol_name']} - {r['title']}\n\n{r['content'][:500]}",
                    'score': 0.5,
                    'title': r['title'],
                    'metadata': {'protocol_name': r['protocol_name']}
                } for r in records]
            })
        else:
            return Response({
                'error_code': 2001,
                'error_msg': 'Protocol Guide service not available'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
    except Exception as e:
        logger.error(f"Protocol Guide 搜索失敗: {str(e)}", exc_info=True)
        return Response({'error': str(e)}, status=500)


# ============= 向後兼容導出 =============

__all__ = [
    # 搜索輔助函數
    'search_know_issue_knowledge',
    'search_rvt_guide_knowledge',
    'search_protocol_guide_knowledge',
    'search_ocr_storage_benchmark',
    
    # Dify API 端點
    'dify_knowledge_search',
    'dify_know_issue_search',
    'dify_ocr_storage_benchmark_search',
    'dify_rvt_guide_search',
    'dify_protocol_guide_search',
    
    # 依賴注入工具
    'get_search_functions_registry',
    'create_dify_search_handler',
]
