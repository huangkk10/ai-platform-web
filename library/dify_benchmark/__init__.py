"""
Dify Benchmark Library

提供完整的 Dify 配置版本測試和對比功能

主要組件：
1. DifyBatchTester - 多版本批量測試器
2. DifyTestRunner - 單版本測試執行器
3. DifyAPIClient - Dify API 呼叫封裝
4. KeywordEvaluator - 關鍵字評分器

使用流程：
1. 建立 Dify 配置版本 (DifyConfigVersion)
2. 準備測試案例 (DifyBenchmarkTestCase)
3. 使用 DifyBatchTester 執行多版本對比測試
4. 查看測試結果和對比報告

範例：
    from library.dify_benchmark import DifyBatchTester
    
    tester = DifyBatchTester()
    results = tester.run_batch_test(
        version_ids=[1, 2, 3],
        test_case_ids=[1, 2, 3, 4, 5],
        batch_name="RAG 配置對比測試"
    )
    
    print(f"最佳版本: {results['comparison']['best_version']}")
    print(f"通過率: {results['comparison']['best_pass_rate']}%")
"""

from .dify_batch_tester import DifyBatchTester
from .dify_test_runner import DifyTestRunner
from .dify_api_client import DifyAPIClient
from .evaluators import KeywordEvaluator

__version__ = '1.0.0'

__all__ = [
    'DifyBatchTester',
    'DifyTestRunner',
    'DifyAPIClient',
    'KeywordEvaluator',
]

# Library 可用性標誌
DIFY_BENCHMARK_LIBRARY_AVAILABLE = True
