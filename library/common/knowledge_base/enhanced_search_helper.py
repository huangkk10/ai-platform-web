"""
Enhanced Vector Search Helper
增強版向量搜尋助手（包裹原有函數，不修改原函數）

設計模式：裝飾器模式
- 包裹 search_with_vectors_generic()
- 添加 Title Boost 可選功能
- 預設行為與原函數完全相同（向後兼容）

使用方式：
```python
# v1.1 方式（不變）
results = search_with_vectors_generic_v2(
    query="IOL", 
    model_class=ProtocolGuide, 
    source_table='protocol_guide'
)

# v1.2 方式（啟用 Title Boost）
results = search_with_vectors_generic_v2(
    query="IOL", 
    model_class=ProtocolGuide, 
    source_table='protocol_guide',
    enable_title_boost=True,
    title_boost_config={'title_match_bonus': 0.15}
)
```
"""

from typing import List, Dict, Any, Type, Callable, Optional
from django.db import models
import logging

logger = logging.getLogger(__name__)


def search_with_vectors_generic_v2(
    query: str,
    model_class: Type[models.Model],
    source_table: str,
    limit: int = 10,
    threshold: float = 0.0,
    use_1024: bool = True,
    content_formatter: Optional[Callable] = None,
    stage: int = 1,
    enable_title_boost: bool = False,  # 🆕 可選參數（預設 False）
    title_boost_config: Optional[Dict[str, Any]] = None  # 🆕 可選參數
) -> List[Dict[str, Any]]:
    """
    增強版向量搜尋（v1.2）- 包裹原有函數，添加 Title Boost
    
    ⚠️ 向後兼容：預設 enable_title_boost=False，行為與原函數完全相同
    
    核心設計：
    1. 調用原有的 search_with_vectors_generic()（不修改）
    2. 如果啟用 Title Boost，在結果上應用加分
    3. 失敗時返回原結果（不影響功能）
    
    Args:
        query: 查詢文本
        model_class: Django Model 類別 (如 ProtocolGuide, RVTGuide)
        source_table: 向量表中的 source_table 值 (如 'protocol_guide')
        limit: 返回結果數量
        threshold: 相似度閾值
        use_1024: 是否使用 1024 維向量表
        content_formatter: 可選的內容格式化函數
        stage: 搜尋階段 (1=段落, 2=全文)
        enable_title_boost: 是否啟用 Title Boost（預設 False）
        title_boost_config: Title Boost 配置（預設 None，使用預設配置）
    
    Returns:
        搜尋結果列表（如果啟用 Title Boost，分數可能已調整）
    
    Examples:
        >>> # v1.1 方式（預設，不啟用 Title Boost）
        >>> results = search_with_vectors_generic_v2(
        ...     query="IOL", 
        ...     model_class=ProtocolGuide, 
        ...     source_table='protocol_guide'
        ... )
        
        >>> # v1.2 方式（明確啟用 Title Boost）
        >>> results = search_with_vectors_generic_v2(
        ...     query="IOL SOP", 
        ...     model_class=ProtocolGuide, 
        ...     source_table='protocol_guide',
        ...     enable_title_boost=True,
        ...     title_boost_config={'title_match_bonus': 0.15}
        ... )
    """
    # ============================================================
    # 步驟 1：調用原有的搜尋函數（完全不修改）
    # ============================================================
    from .vector_search_helper import search_with_vectors_generic
    
    logger.debug(
        f"📍 增強版搜尋: query='{query[:30]}...', "
        f"source_table={source_table}, "
        f"stage={stage}, "
        f"title_boost={enable_title_boost}"
    )
    
    results = search_with_vectors_generic(
        query=query,
        model_class=model_class,
        source_table=source_table,
        limit=limit,
        threshold=threshold,
        use_1024=use_1024,
        content_formatter=content_formatter,
        stage=stage
    )
    
    # ============================================================
    # 步驟 2：如果未啟用 Title Boost，直接返回原結果
    # ============================================================
    if not enable_title_boost:
        logger.debug(f"✅ Title Boost 未啟用，返回原始結果 ({len(results)} 筆)")
        return results
    
    # ============================================================
    # 步驟 3：應用 Title Boost（不影響原結果）
    # ============================================================
    try:
        from .title_boost.processor import TitleBoostProcessor
        from .title_boost.config import TitleBoostConfig
        
        # 使用配置或預設值
        if title_boost_config:
            config = TitleBoostConfig.get_safe_config(title_boost_config)
        else:
            config = TitleBoostConfig.DEFAULT_CONFIG.copy()
            config['enabled'] = True  # 明確啟用
        
        # 建立處理器
        processor = TitleBoostProcessor(
            title_match_bonus=config.get('title_match_bonus', 0.15),
            min_keyword_length=config.get('min_keyword_length', 2),
            enable_progressive_bonus=config.get('enable_progressive_bonus', False)
        )
        
        # 應用 Title Boost
        logger.info(f"🎯 開始應用 Title Boost: query='{query[:30]}...', bonus={config.get('title_match_bonus', 0.15):.2%}")
        
        boosted_results = processor.apply_title_boost(
            query=query,
            vector_results=results,
            title_field='title'  # 假設格式化後的結果有 'title' 欄位
        )
        
        # 統計資訊
        stats = processor.get_boost_statistics(boosted_results)
        logger.info(
            f"✅ Title Boost 已應用: {stats['boosted_count']}/{stats['total_results']} 結果獲得加分 "
            f"(平均加分: {stats['average_boost']:.2%})"
        )
        
        return boosted_results
        
    except Exception as e:
        logger.error(f"❌ Title Boost 應用失敗: {str(e)}", exc_info=True)
        # 失敗時返回原結果（不影響功能）
        logger.warning("⚠️ Title Boost 失敗，返回原始結果")
        return results


def get_title_boost_config_from_version(version_code: str, stage: int = 1) -> Optional[Dict[str, Any]]:
    """
    從版本配置中獲取 Title Boost 設定
    
    輔助函數，用於從 DifyConfigVersion 讀取配置。
    
    Args:
        version_code: 版本代碼（如 'dify-two-tier-v1.2'）
        stage: 搜尋階段 (1 或 2)
    
    Returns:
        Title Boost 配置字典，如果版本不存在或未啟用則返回 None
    
    Examples:
        >>> config = get_title_boost_config_from_version('dify-two-tier-v1.2', stage=1)
        >>> if config and config['enabled']:
        ...     # 使用配置
        ...     pass
    """
    try:
        from api.models import DifyConfigVersion
        from .title_boost.config import TitleBoostConfig
        
        # 查詢版本
        version = DifyConfigVersion.objects.get(version_code=version_code)
        
        # 解析配置
        config = TitleBoostConfig.from_rag_settings(version.rag_settings, stage=stage)
        
        if config.get('enabled', False):
            logger.info(f"✅ 從版本 {version_code} 載入 Title Boost 配置 (Stage {stage})")
            return config
        else:
            logger.debug(f"Title Boost 未在版本 {version_code} 中啟用")
            return None
            
    except Exception as e:
        logger.error(f"讀取版本配置失敗: {str(e)}")
        return None


def search_with_title_boost_from_version(
    query: str,
    model_class: Type[models.Model],
    source_table: str,
    version_code: str,
    limit: int = 10,
    threshold: float = 0.0,
    stage: int = 1,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    使用版本配置進行 Title Boost 搜尋
    
    便利函數，自動從版本配置讀取 Title Boost 設定。
    
    Args:
        query: 查詢文本
        model_class: Django Model 類別
        source_table: 向量表名稱
        version_code: 版本代碼（如 'dify-two-tier-v1.2'）
        limit: 返回結果數量
        threshold: 相似度閾值
        stage: 搜尋階段 (1 或 2)
        **kwargs: 其他參數傳遞給 search_with_vectors_generic_v2
    
    Returns:
        搜尋結果列表
    
    Examples:
        >>> results = search_with_title_boost_from_version(
        ...     query="IOL SOP",
        ...     model_class=ProtocolGuide,
        ...     source_table='protocol_guide',
        ...     version_code='dify-two-tier-v1.2',
        ...     stage=1
        ... )
    """
    # 從版本配置讀取 Title Boost 設定
    title_boost_config = get_title_boost_config_from_version(version_code, stage=stage)
    
    # 判斷是否啟用 Title Boost
    enable_title_boost = title_boost_config is not None and title_boost_config.get('enabled', False)
    
    logger.info(
        f"📍 版本驅動搜尋: version={version_code}, "
        f"stage={stage}, "
        f"title_boost={'啟用' if enable_title_boost else '停用'}"
    )
    
    # 調用增強版搜尋
    return search_with_vectors_generic_v2(
        query=query,
        model_class=model_class,
        source_table=source_table,
        limit=limit,
        threshold=threshold,
        stage=stage,
        enable_title_boost=enable_title_boost,
        title_boost_config=title_boost_config,
        **kwargs
    )
