"""
搜尋策略系統
===========

提供多種搜尋策略供 Benchmark 測試使用，不影響 Protocol Assistant 的現有功能。

可用策略：
- SectionOnlyStrategy: 純段落向量搜尋
- DocumentOnlyStrategy: 純全文向量搜尋
- HybridWeightedStrategy: 混合權重搜尋（四維權重系統）
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

__all__ = [
    'BaseSearchStrategy',
    'SectionOnlyStrategy',
    'DocumentOnlyStrategy',
    'HybridWeightedStrategy',
]
