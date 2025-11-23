"""
快速測試 V3 是否使用混合權重策略
"""
import os
import sys
import django

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from library.benchmark.test_runner import BenchmarkTestRunner
from api.models import BenchmarkTestCase

# 測試 V3 (混合權重 70-30)
print("=" * 80)
print("快速測試 V3 - 混合權重 70-30")
print("=" * 80)

runner = BenchmarkTestRunner(version_id=7, verbose=True)
test_case = BenchmarkTestCase.objects.first()

print(f"\n測試題目: {test_case.question}")
print(f"預期文檔: {test_case.expected_document_ids}\n")

result = runner.run_single_test(test_case, save_to_db=False)

print(f"\n結果:")
print(f"  返回文檔 IDs: {result['returned_document_ids']}")
print(f"  Precision: {result['precision']:.4f}")
print(f"  Recall: {result['recall']:.4f}")
print(f"  F1 Score: {result['f1_score']:.4f}")
print(f"  響應時間: {result['response_time']:.2f} ms")
