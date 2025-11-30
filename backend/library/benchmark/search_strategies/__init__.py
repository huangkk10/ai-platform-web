"""
搜尋策略系統
===========

提供多種搜尋策略供 Benchmark 測試使用，不影響 Protocol Assistant 的現有功能。

可用策略：
- SectionOnlyStrategy: 純段落向量搜尋
- DocumentOnlyStrategy: 純全文向量搜尋
- HybridWeightedStrategy: 混合權重搜尋（四維權重系統）
- HybridRRFStrategy: 混合 RRF 搜尋（向量 + 關鍵字 + RRF 融合）⭐ 來自 Dify v1.2.2
- BalancedHybridStrategy: 平衡混合策略（50-50）
- ThreeLayerStrategy: 三層策略（段落+全文+關鍵字）

使用方式：
```python
from library.benchmark.search_strategies import SearchStrategyEngine

engine = SearchStrategyEngine()
results = engine.execute_strategy(
    strategy_name='hybrid_weighted',
    query="ULINK IOL 測試",
    limit=10,
    section_weight=0.7,
    document_weight=0.3
)
```
"""

from .base_strategy import BaseSearchStrategy
from .section_only_strategy import SectionOnlyStrategy
from .document_only_strategy import DocumentOnlyStrategy
from .hybrid_weighted_strategy import HybridWeightedStrategy
from .hybrid_rrf_strategy import HybridRRFStrategy


def get_strategy(strategy_type: str, search_service, **params):
    """
    獲取搜尋策略實例
    
    Args:
        strategy_type: 策略類型 ('section_only', 'document_only', 'hybrid_weighted', 'hybrid_rrf')
        search_service: ProtocolGuideSearchService 實例
        **params: 策略參數
        
    Returns:
        BaseSearchStrategy: 策略實例
        
    Raises:
        ValueError: 不支援的策略類型
    """
    strategy_map = {
        'section_only': SectionOnlyStrategy,
        'document_only': DocumentOnlyStrategy,
        'hybrid_weighted': HybridWeightedStrategy,
        'hybrid_rrf': HybridRRFStrategy,
    }
    
    strategy_class = strategy_map.get(strategy_type)
    if not strategy_class:
        raise ValueError(f"不支援的策略類型: {strategy_type}. 可用類型: {list(strategy_map.keys())}")
    
    return strategy_class(search_service, **params)


__all__ = [
    'BaseSearchStrategy',
    'SectionOnlyStrategy',
    'DocumentOnlyStrategy',
    'HybridWeightedStrategy',
    'HybridRRFStrategy',
    'get_strategy',
]
