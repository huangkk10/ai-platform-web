"""
通用向量搜尋助手
================

提供知識庫向量搜尋的通用實現，避免重複代碼。

核心流程：
1. 向量搜尋 (embedding_service.search_similar_documents)
2. 批量查詢 DB (一次查詢所有 IDs，避免 N+1 問題)
3. 格式化結果 (統一格式)

使用方式：
```python
from library.common.knowledge_base.vector_search_helper import search_with_vectors_generic

results = search_with_vectors_generic(
    query="如何連接",
    model_class=ProtocolGuide,
    source_table='protocol_guide',
    limit=5,
    threshold=0.3,
    use_1024=True
)
```

重構目標：
- 所有知識庫共用此模組
- 消除重複的 _get_xxx_results() 函數
- 統一向量搜尋實現方式
"""

from typing import List, Type, Dict, Any, Callable, Optional
from django.db import models
import logging

logger = logging.getLogger(__name__)


def _get_weights_for_assistant(source_table: str, stage: int = 1) -> tuple:
    """
    根據 source_table 獲取權重配置（支援兩階段）
    
    Args:
        source_table: 向量表中的 source_table 值 (如 'protocol_guide')
        stage: 搜尋階段 (1=段落, 2=全文)
    
    Returns:
        (title_weight, content_weight) 元組，值為 0.0-1.0 的浮點數
    
    Example:
        >>> _get_weights_for_assistant('protocol_guide', stage=1)
        (0.6, 0.4)  # 第一階段 60% 標題 / 40% 內容
        >>> _get_weights_for_assistant('protocol_guide', stage=2)
        (0.5, 0.5)  # 第二階段 50% 標題 / 50% 內容
    """
    from api.models import SearchThresholdSetting
    
    # 映射 source_table 到 assistant_type
    table_to_type = {
        'protocol_guide': 'protocol_assistant',
        'rvt_guide': 'rvt_assistant',
        'know_issue': 'know_issue_assistant',  # 預留
    }
    
    assistant_type = table_to_type.get(source_table)
    if not assistant_type:
        logger.warning(f"未知的 source_table: {source_table}，使用預設權重 60/40")
        return 0.6, 0.4
    
    try:
        setting = SearchThresholdSetting.objects.get(assistant_type=assistant_type)
        
        # 根據配置策略選擇權重
        if setting.use_unified_weights or stage == 1:
            # 使用第一階段配置
            title_weight = setting.stage1_title_weight / 100.0
            content_weight = setting.stage1_content_weight / 100.0
            logger.info(
                f"載入第一階段權重配置: {assistant_type} -> "
                f"標題 {setting.stage1_title_weight}% / 內容 {setting.stage1_content_weight}%"
            )
        else:
            # 使用第二階段配置
            title_weight = setting.stage2_title_weight / 100.0
            content_weight = setting.stage2_content_weight / 100.0
            logger.info(
                f"載入第二階段權重配置: {assistant_type} -> "
                f"標題 {setting.stage2_title_weight}% / 內容 {setting.stage2_content_weight}%"
            )
        
        return title_weight, content_weight
        
    except SearchThresholdSetting.DoesNotExist:
        logger.warning(f"找不到 {assistant_type} 的權重配置，使用預設值 60/40")
        return 0.6, 0.4
    except Exception as e:
        logger.error(f"讀取權重配置失敗: {str(e)}，使用預設值 60/40")
        return 0.6, 0.4


def search_with_vectors_generic(
    query: str,
    model_class: Type[models.Model],
    source_table: str,
    limit: int = 10,
    threshold: float = 0.0,
    use_1024: bool = True,
    content_formatter: Optional[Callable] = None,
    stage: int = 1
) -> List[Dict[str, Any]]:
    """
    通用向量搜尋函數 - 所有知識庫共用（支援兩階段）
    
    Args:
        query: 查詢文本
        model_class: Django Model 類別 (如 ProtocolGuide, RVTGuide)
        source_table: 向量表中的 source_table 值 (如 'protocol_guide')
        limit: 返回結果數量
        threshold: 相似度閾值 (建議設為 0.0，由上層過濾)
        use_1024: 是否使用 1024 維向量表
        content_formatter: 可選的內容格式化函數 func(item) -> str
        stage: 搜尋階段 (1=段落, 2=全文)
    
    Returns:
        格式化的搜尋結果列表:
        [
            {
                'content': '...',
                'score': 0.85,
                'title': '...',
                'metadata': {'id': 1, 'created_at': '...', ...}
            },
            ...
        ]
    
    Raises:
        Exception: 向量搜尋過程中的錯誤
    
    Example:
        >>> from api.models import ProtocolGuide
        >>> # 第一階段段落搜尋
        >>> results = search_with_vectors_generic(
        ...     query="ULINK 連接",
        ...     model_class=ProtocolGuide,
        ...     source_table='protocol_guide',
        ...     limit=5,
        ...     stage=1
        ... )
        >>> # 第二階段全文搜尋
        >>> results = search_with_vectors_generic(
        ...     query="ULINK 連接",
        ...     model_class=ProtocolGuide,
        ...     source_table='protocol_guide',
        ...     limit=5,
        ...     stage=2
        ... )
    """
    try:
        # 步驟 1: 讀取權重配置（根據 stage）
        title_weight, content_weight = _get_weights_for_assistant(source_table, stage=stage)
        
        # 步驟 2: 向量搜尋（使用多向量方法）
        from api.services.embedding_service import get_embedding_service
        
        model_type = 'ultra_high' if use_1024 else 'standard'
        embedding_service = get_embedding_service(model_type)
        
        # ✅ 使用支援權重的多向量搜尋方法
        vector_results = embedding_service.search_similar_documents_multi(
            query=query,
            source_table=source_table,
            limit=limit,
            threshold=threshold,
            title_weight=title_weight,
            content_weight=content_weight
        )
        
        if not vector_results:
            logger.info(f"向量搜尋無結果: {source_table}, query='{query}', stage={stage}")
            return []
        
        logger.info(
            f"✅ 多向量搜尋找到 {len(vector_results)} 條結果: {source_table} "
            f"(Stage {stage}, 權重: {title_weight*100:.0f}%/{content_weight*100:.0f}%)"
        )
        
        # 步驟 3: 批量查詢 DB（避免 N+1 問題）
        items_dict = fetch_records_by_ids(
            model_class=model_class,
            source_ids=[r['source_id'] for r in vector_results]
        )
        
        # 步驟 4: 格式化結果
        formatted_results = format_vector_results(
            vector_results=vector_results,
            items_dict=items_dict,
            model_class=model_class,
            content_formatter=content_formatter
        )
        
        return formatted_results
        
    except Exception as e:
        logger.error(f"通用向量搜尋失敗 ({source_table}, stage={stage}): {str(e)}", exc_info=True)
        return []


def fetch_records_by_ids(
    model_class: Type[models.Model],
    source_ids: List[int]
) -> Dict[int, models.Model]:
    """
    批量查詢 DB 記錄（避免 N+1 問題）
    
    使用 Django ORM 的 filter(id__in=...) 一次性查詢所有記錄，
    比循環調用 objects.get() 效率高得多。
    
    Args:
        model_class: Django Model 類別
        source_ids: 要查詢的 ID 列表
    
    Returns:
        {id: model_instance} 字典
    
    Example:
        >>> from api.models import ProtocolGuide
        >>> items = fetch_records_by_ids(ProtocolGuide, [1, 2, 3])
        >>> items[1].title
        'ULINK Protocol 連接測試指南'
    """
    try:
        if not source_ids:
            logger.warning("fetch_records_by_ids: source_ids 為空")
            return {}
        
        # 使用 Django ORM 批量查詢（一次 SQL 查詢）
        items = model_class.objects.filter(id__in=source_ids)
        items_dict = {item.id: item for item in items}
        
        # 檢查是否有缺失的記錄
        missing_ids = set(source_ids) - set(items_dict.keys())
        if missing_ids:
            logger.warning(
                f"批量查詢缺失記錄: {model_class.__name__}, IDs={missing_ids}"
            )
        
        return items_dict
        
    except Exception as e:
        logger.error(f"批量查詢失敗: {model_class.__name__}, {str(e)}", exc_info=True)
        return {}


def format_vector_results(
    vector_results: List[Dict],
    items_dict: Dict[int, models.Model],
    model_class: Type[models.Model],
    content_formatter: Optional[Callable] = None
) -> List[Dict[str, Any]]:
    """
    格式化向量搜尋結果為統一的 Dify 知識庫格式
    
    Args:
        vector_results: 向量搜尋原始結果 (來自 embedding_service)
        items_dict: DB 記錄字典 {id: instance}
        model_class: Model 類別 (用於日誌)
        content_formatter: 可選的內容格式化函數 func(item) -> str
    
    Returns:
        統一格式的結果列表
        [
            {
                'content': '文檔內容...',
                'score': 0.85,  # 相似度分數
                'title': '文檔標題',
                'metadata': {
                    'id': 1,
                    'created_at': '2025-10-16T16:28:54.568258',
                    'updated_at': '2025-10-16T16:28:54.568279'
                }
            }
        ]
    
    Note:
        - 保持向量搜尋的順序（按相似度排序）
        - 自動處理缺失的記錄
        - 支援自定義內容格式化邏輯
    """
    formatted_results = []
    
    for vector_result in vector_results:
        source_id = vector_result['source_id']
        
        # 檢查記錄是否存在
        if source_id not in items_dict:
            logger.warning(
                f"格式化時找不到記錄: {model_class.__name__} ID={source_id}"
            )
            continue
        
        item = items_dict[source_id]
        
        # 獲取內容 - 優先級：自定義格式化器 > get_search_content() > content 屬性
        if content_formatter and callable(content_formatter):
            content = content_formatter(item)
        elif hasattr(item, 'get_search_content') and callable(item.get_search_content):
            content = item.get_search_content()
        elif hasattr(item, 'content'):
            content = item.content
        else:
            content = str(item)
            logger.warning(
                f"無法獲取內容，使用 str(): {model_class.__name__} ID={source_id}"
            )
        
        # 組裝結果
        formatted_results.append({
            'content': content,
            'score': float(vector_result['similarity_score']),
            'title': getattr(item, 'title', str(item)),
            'metadata': {
                'id': item.id,
                'created_at': item.created_at.isoformat() if hasattr(item, 'created_at') else None,
                'updated_at': item.updated_at.isoformat() if hasattr(item, 'updated_at') else None,
            }
        })
    
    logger.info(
        f"格式化完成: {model_class.__name__}, "
        f"輸入 {len(vector_results)} 條，輸出 {len(formatted_results)} 條"
    )
    
    return formatted_results


# 向後兼容別名
search_knowledge_with_vectors = search_with_vectors_generic
