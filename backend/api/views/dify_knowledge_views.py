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

# 🆕 Baseline 版本緩存（模組級別）
_baseline_version_cache = {
    'version_code': None,
    'last_updated': None
}

def get_baseline_version_code():
    """
    獲取當前 Baseline 版本代碼（帶緩存）
    
    緩存策略：
    - 第一次調用時從資料庫讀取並緩存
    - 後續調用直接返回緩存值
    - VSA 切換版本時會清除緩存（通過 set_baseline API）
    
    Returns:
        str: Baseline 版本代碼（如 'dify-two-tier-v1.1.1'）
    """
    from api.models import DifyConfigVersion
    
    # 檢查緩存
    if _baseline_version_cache['version_code']:
        logger.debug(f"📦 使用緩存的 Baseline 版本: {_baseline_version_cache['version_code']}")
        return _baseline_version_cache['version_code']
    
    # 從資料庫查詢
    try:
        baseline_version = DifyConfigVersion.objects.filter(
            is_baseline=True,
            is_active=True
        ).first()
        
        if baseline_version:
            version_code = baseline_version.version_code
            # 更新緩存
            _baseline_version_cache['version_code'] = version_code
            _baseline_version_cache['last_updated'] = __import__('datetime').datetime.now()
            logger.info(f"✅ 載入並緩存 Baseline 版本: {version_code}")
            return version_code
        else:
            logger.warning("⚠️ 找不到 Baseline 版本，返回預設值 v1.2.1")
            return 'dify-two-tier-v1.2.1'
    except Exception as e:
        logger.error(f"❌ 查詢 Baseline 版本失敗: {str(e)}")
        return 'dify-two-tier-v1.2.1'

def clear_baseline_version_cache():
    """
    清除 Baseline 版本緩存
    
    應該在以下情況調用：
    - VSA 切換版本時（set_baseline API）
    - 手動重置時
    """
    _baseline_version_cache['version_code'] = None
    _baseline_version_cache['last_updated'] = None
    logger.info("🗑️ Baseline 版本緩存已清除")

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


def search_rvt_guide_knowledge(query_text, limit=5, threshold=0.7):
    """
    搜索 RVT Guide 知識庫
    
    向後兼容函數：此函數保留是為了兼容性，
    實際搜索由 library/rvt_guide/search_service.py 執行。
    
    Args:
        query_text: 搜索關鍵字
        limit: 返回結果數量限制
        threshold: 相似度閾值 (0.0 ~ 1.0)，來自 Dify Studio 或 Database
        
    Returns:
        list: 搜索結果列表
    """
    try:
        if LIBRARIES_AVAILABLE:
            service = RVTGuideSearchService()
            # ✅ 傳遞 threshold 參數到底層搜索服務
            return service.search_knowledge(query_text, limit=limit, threshold=threshold)
        else:
            logger.warning("RVTGuideSearchService 不可用，使用備用實現")
            return []
    except Exception as e:
        logger.error(f"RVT Guide 搜索失敗: {str(e)}")
        return []


def search_protocol_guide_knowledge(query_text, limit=5, threshold=0.7):
    """
    搜索 Protocol Guide 知識庫
    
    向後兼容函數：此函數保留是為了兼容性，
    實際搜索由 library/protocol_guide/search_service.py 執行。
    
    Args:
        query_text: 搜索關鍵字
        limit: 返回結果數量限制
        threshold: 相似度閾值 (0.0 ~ 1.0)，來自 Dify Studio 或 Database
        
    Returns:
        list: 搜索結果列表
    """
    try:
        if LIBRARIES_AVAILABLE:
            service = ProtocolGuideSearchService()
            # ✅ 傳遞 threshold 參數到底層搜索服務
            return service.search_knowledge(query_text, limit=limit, threshold=threshold)
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
            
            # 🔍 檢測特殊標記 __FULL_SEARCH__（二階段搜尋 Stage 2 標記）
            search_mode = 'auto'  # 預設為 'auto'（段落搜尋）
            stage = 1  # ✅ 預設為 Stage 1（段落搜尋）
            
            if '__FULL_SEARCH__' in query:
                # 檢測到 Stage 2 標記
                search_mode = 'document_only'  # 切換為全文搜尋
                stage = 2  # ✅ 設置為 Stage 2（全文搜尋）
                query = query.replace('__FULL_SEARCH__', '').strip()  # 清理標記
                logger.info(f"🎯 檢測到 Stage 2 標記，切換到全文搜尋模式 (stage={stage})")
                logger.info(f"🧹 清理後查詢: '{query}'")
            
            # ✅ 也支援從 Dify inputs 接收 search_mode（如果 Dify 工作室有配置）
            inputs = data.get('inputs', {})
            if 'search_mode' in inputs and '__FULL_SEARCH__' not in data.get('query', ''):
                # 如果 inputs 中有 search_mode，且不是來自標記，則使用 inputs 的值
                search_mode = inputs.get('search_mode', search_mode)
                # ✅ 根據 search_mode 設置 stage
                if search_mode in ['document_only', 'document_preferred']:
                    stage = 2
            
            # 🎯 三層優先順序 Threshold 管理（支援兩階段）
            # 優先級 1：Dify Studio 設定（用戶當下設定）
            dify_threshold = retrieval_setting.get('score_threshold')
            
            # ✅ 修正：將 0.0 視為「未設定」（因為 0.0 threshold 會返回所有結果，通常不是用戶本意）
            if dify_threshold is not None and dify_threshold > 0:
                # Dify 有設定有效的 threshold（> 0），使用 Dify 的值
                score_threshold = dify_threshold
                logger.info(
                    f"🎯 [優先級 1] 使用 Dify Studio threshold={score_threshold} | "
                    f"knowledge_id='{knowledge_id}' | query='{query}' | search_mode='{search_mode}' | stage={stage}"
                )
            else:
                # Dify 沒有設定 threshold，使用 ThresholdManager（優先級 2: Database，優先級 3: Default）
                try:
                    from library.common.threshold_manager import get_threshold_manager
                    
                    # 將 knowledge_id 映射到 assistant_type
                    assistant_type_mapping = {
                        'protocol_assistant': 'protocol_assistant',
                        'protocol_guide': 'protocol_assistant',
                        'protocol_guide_db': 'protocol_assistant',
                        'rvt_guide': 'rvt_assistant',
                        'rvt_guide_db': 'rvt_assistant',
                        'rvt_assistant': 'rvt_assistant',
                    }
                    assistant_type = assistant_type_mapping.get(knowledge_id, 'protocol_assistant')
                    
                    manager = get_threshold_manager()
                    # ✅ 傳遞 stage 參數給 ThresholdManager
                    score_threshold = manager.get_threshold(
                        assistant_type=assistant_type,
                        dify_threshold=None,  # 傳入 None，讓 Manager 使用 Database 或 Default
                        stage=stage  # ✅ 根據 stage 選擇對應的 threshold
                    )
                    
                    logger.info(
                        f"📊 [優先級 2/3] Dify 未設定，使用 ThresholdManager threshold={score_threshold} | "
                        f"assistant_type='{assistant_type}' | knowledge_id='{knowledge_id}' | query='{query}' | "
                        f"search_mode='{search_mode}' | stage={stage}"
                    )
                except Exception as e:
                    # 如果 ThresholdManager 失敗，使用硬編碼預設值
                    score_threshold = 0.7
                    logger.warning(
                        f"⚠️ ThresholdManager 失敗，使用硬編碼預設值 0.7: {e}"
                    )
            
            # 🆕 載入版本配置（支援 Title Boost）
            # 方案 B：動態讀取 Baseline 版本（帶緩存優化）
            version_config = None
            
            # 步驟 1：嘗試從 inputs 中讀取 version_code（優先級最高）
            version_code = inputs.get('version_code')
            
            # 步驟 2：如果沒有指定，則使用緩存的 Baseline 版本
            if not version_code:
                version_code = get_baseline_version_code()  # ✅ 使用帶緩存的函數
                logger.info(f"🎯 使用 Baseline 版本: {version_code}")
            else:
                logger.info(f"📌 使用指定版本: {version_code} (來自 Dify inputs)")
            
            # 步驟 3：載入版本配置
            try:
                from api.models import DifyConfigVersion
                version = DifyConfigVersion.objects.get(
                    version_code=version_code,
                    is_active=True
                )
                version_config = {
                    'version_code': version.version_code,
                    'version_name': version.version_name,
                    'rag_settings': version.rag_settings,
                    'model_config': version.model_config
                }
                logger.info(f"✅ 載入版本配置: {version_code} (Title Boost Stage1={version.rag_settings.get('stage1', {}).get('title_match_bonus', 0)}%, Stage2={version.rag_settings.get('stage2', {}).get('title_match_bonus', 0)}%)")
            except DifyConfigVersion.DoesNotExist:
                logger.warning(f"⚠️ 找不到版本: {version_code}，使用預設配置（無 Title Boost）")
            except Exception as e:
                logger.error(f"❌ 載入版本配置失敗: {str(e)}")
            
            # 執行搜索（threshold、search_mode 和 stage 會一路傳遞到 SQL 查詢）
            result = handler.search(
                knowledge_id=knowledge_id,
                query=query,
                top_k=retrieval_setting.get('top_k', 5),
                score_threshold=score_threshold,  # ✅ 傳遞 Dify 的 threshold
                search_mode=search_mode,  # ✅ 傳遞 search_mode
                stage=stage,  # ✅ 傳遞 stage 參數
                version_config=version_config  # 🆕 傳遞版本配置（啟用 Title Boost）
            )
            
            logger.info(f"✅ 知識庫搜索成功: {knowledge_id}, query='{query}', mode='{search_mode}', stage={stage}, results={len(result.get('records', []))}")
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


# ============= Baseline 版本管理 API =============

@api_view(['POST'])
@csrf_exempt
def set_baseline_version(request, version_id):
    """
    設定指定版本為 Baseline 版本
    
    URL: POST /api/dify/versions/<version_id>/set_baseline/
    
    功能：
    1. 驗證版本存在且 is_active=True
    2. 將所有版本的 is_baseline 設為 False
    3. 將指定版本的 is_baseline 設為 True
    4. 清除 Baseline 版本快取
    
    Args:
        request: Django request 物件
        version_id (int): 版本 ID
    
    Returns:
        Response:
            成功 (200):
                {
                    "success": true,
                    "message": "已成功設定 Baseline 版本",
                    "baseline_version": {
                        "id": 3,
                        "version_code": "dify-two-tier-v1.2.2",
                        "version_name": "Dify 二階搜尋 v1.2.2 (Hybrid Search + Title Boost)",
                        "description": "...",
                        "is_baseline": true,
                        "is_active": true
                    }
                }
            失敗 (400/404/500):
                {
                    "success": false,
                    "error": "錯誤訊息"
                }
    
    Example:
        curl -X POST "http://localhost/api/dify/versions/3/set_baseline/" \
             -H "Content-Type: application/json"
    
    Created: 2025-11-27
    Author: AI Platform Team
    """
    from api.models import DifyConfigVersion
    from django.db import transaction
    
    try:
        # 步驟 1: 驗證版本存在且啟用
        try:
            target_version = DifyConfigVersion.objects.get(id=version_id)
        except DifyConfigVersion.DoesNotExist:
            logger.warning(f"⚠️ 版本 ID {version_id} 不存在")
            return Response({
                'success': False,
                'error': f'版本 ID {version_id} 不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # 檢查版本是否啟用
        if not target_version.is_active:
            logger.warning(f"⚠️ 版本 {target_version.version_code} 未啟用，無法設為 Baseline")
            return Response({
                'success': False,
                'error': f'版本「{target_version.version_name}」未啟用，請先啟用該版本'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 步驟 2 & 3: 使用事務更新資料庫（原子操作）
        with transaction.atomic():
            # 將所有版本的 is_baseline 設為 False
            updated_count = DifyConfigVersion.objects.filter(
                is_baseline=True
            ).update(is_baseline=False)
            
            logger.info(f"🔄 已將 {updated_count} 個舊 Baseline 版本取消")
            
            # 將目標版本設為 Baseline
            target_version.is_baseline = True
            target_version.save()
            
            logger.info(f"✅ 已設定新 Baseline: {target_version.version_code}")
        
        # 步驟 4: 清除快取
        clear_baseline_version_cache()
        logger.info("🗑️ Baseline 快取已清除")
        
        # 返回成功回應
        return Response({
            'success': True,
            'message': '已成功設定 Baseline 版本',
            'baseline_version': {
                'id': target_version.id,
                'version_code': target_version.version_code,
                'version_name': target_version.version_name,
                'description': target_version.description,
                'retrieval_mode': target_version.retrieval_mode,
                'is_baseline': target_version.is_baseline,
                'is_active': target_version.is_active,
                'created_at': target_version.created_at.isoformat() if target_version.created_at else None,
                'updated_at': target_version.updated_at.isoformat() if target_version.updated_at else None
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"❌ 設定 Baseline 版本失敗: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': f'設定 Baseline 版本時發生錯誤: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_baseline_version_info(request):
    """
    獲取當前 Baseline 版本詳細資訊
    
    URL: GET /api/dify/versions/baseline/
    
    Returns:
        Response:
            成功 (200):
                {
                    "success": true,
                    "baseline_version": {
                        "id": 3,
                        "version_code": "dify-two-tier-v1.2.2",
                        "version_name": "...",
                        "is_baseline": true,
                        "is_active": true,
                        "rag_settings": {...}
                    },
                    "cached": false
                }
            失敗 (404):
                {
                    "success": false,
                    "error": "找不到 Baseline 版本"
                }
    
    Example:
        curl -X GET "http://localhost/api/dify/versions/baseline/"
    
    Created: 2025-11-27
    Author: AI Platform Team
    """
    from api.models import DifyConfigVersion
    
    try:
        # 查詢 Baseline 版本
        baseline_version = DifyConfigVersion.objects.filter(
            is_baseline=True,
            is_active=True
        ).first()
        
        if not baseline_version:
            logger.warning("⚠️ 找不到 Baseline 版本")
            return Response({
                'success': False,
                'error': '找不到 Baseline 版本'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # 檢查是否使用快取
        using_cache = bool(_baseline_version_cache.get('version_code'))
        
        return Response({
            'success': True,
            'baseline_version': {
                'id': baseline_version.id,
                'version_code': baseline_version.version_code,
                'version_name': baseline_version.version_name,
                'description': baseline_version.description,
                'retrieval_mode': baseline_version.retrieval_mode,
                'is_baseline': baseline_version.is_baseline,
                'is_active': baseline_version.is_active,
                'rag_settings': baseline_version.rag_settings,
                'model_config': baseline_version.model_config,
                'created_at': baseline_version.created_at.isoformat() if baseline_version.created_at else None,
                'updated_at': baseline_version.updated_at.isoformat() if baseline_version.updated_at else None
            },
            'cached': using_cache
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"❌ 獲取 Baseline 版本失敗: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': f'獲取 Baseline 版本時發生錯誤: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
    
    # Baseline 版本管理 API
    'set_baseline_version',
    'get_baseline_version_info',
    
    # 依賴注入工具
    'get_search_functions_registry',
    'create_dify_search_handler',
]
