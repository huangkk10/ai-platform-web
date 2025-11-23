"""
Dify Benchmark Evaluators Package

提供多種評分方式：
1. KeywordEvaluator: 100% 關鍵字匹配評分
2. AIEvaluator: GPT-4 基於的智能評分（可選）
"""

from .keyword_evaluator import KeywordEvaluator

__all__ = [
    'KeywordEvaluator',
]
