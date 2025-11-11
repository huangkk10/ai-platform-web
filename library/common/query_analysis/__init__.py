"""
Query Analysis Module

提供查詢分析相關功能：
- 關鍵字檢測
- 查詢意圖分析
"""

from .keyword_detector import (
    contains_full_document_keywords,
    FULL_DOCUMENT_KEYWORDS,
)

__all__ = [
    'contains_full_document_keywords',
    'FULL_DOCUMENT_KEYWORDS',
]
