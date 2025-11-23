#!/usr/bin/env python
"""
簡單測試：驗證 V1 (section_only) vs V2 (document_only) 是否產生不同結果
"""
import os
import sys
import django

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from library.benchmark.test_runner import BenchmarkTestRunner
from api.models import BenchmarkTestCase

def test_simple():
    """簡單測試"""
    
    # 使用一個測試題目
    test_case = BenchmarkTestCase.objects.filter(is_active=True).first()
    print(f"\n測試題目: {test_case.question}\n")
    
    # V1: section_only (ID=5)
    print("=" * 80)
    print("測試 V1 (section_only) - ID=5")
    print("=" * 80)
    runner_v1 = BenchmarkTestRunner(version_id=5, verbose=True)
    result_v1 = runner_v1.run_single_test(test_case, save_to_db=False)
    ids_v1 = result_v1['returned_document_ids']
    print(f"V1 返回 IDs: {ids_v1}\n")
    
    # V2: document_only (ID=6)
    print("=" * 80)
    print("測試 V2 (document_only) - ID=6")
    print("=" * 80)
    runner_v2 = BenchmarkTestRunner(version_id=6, verbose=True)
    result_v2 = runner_v2.run_single_test(test_case, save_to_db=False)
    ids_v2 = result_v2['returned_document_ids']
    print(f"V2 返回 IDs: {ids_v2}\n")
    
    # 比較
    print("=" * 80)
    print("比較結果")
    print("=" * 80)
    print(f"V1 IDs: {ids_v1}")
    print(f"V2 IDs: {ids_v2}")
    
    if ids_v1 == ids_v2:
        print("\n❌ V1 和 V2 返回相同的 IDs - 配置沒有生效！")
    else:
        print("\n✅ V1 和 V2 返回不同的 IDs - 配置生效！")
        print(f"   共同 IDs: {set(ids_v1) & set(ids_v2)}")
        print(f"   V1 獨有: {set(ids_v1) - set(ids_v2)}")
        print(f"   V2 獨有: {set(ids_v2) - set(ids_v1)}")

if __name__ == '__main__':
    test_simple()
