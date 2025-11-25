"""
Title Boost Module
標題匹配加分模組

提供標題精準匹配的加分機制，用於提升搜尋結果準確度。

核心組件：
- TitleMatcher: 標題匹配器（關鍵詞提取與匹配判定）
- TitleBoostProcessor: 標題加分處理器（應用加分邏輯）
- TitleBoostConfig: 配置管理器（從版本配置解析設定）

使用方式：
```python
from library.common.knowledge_base.title_boost import TitleBoostProcessor

processor = TitleBoostProcessor(title_match_bonus=0.15)
boosted_results = processor.apply_title_boost(
    query="IOL SOP",
    vector_results=search_results
)
```
"""

from .matcher import TitleMatcher
from .processor import TitleBoostProcessor
from .config import TitleBoostConfig

__all__ = [
    'TitleMatcher',
    'TitleBoostProcessor',
    'TitleBoostConfig'
]
