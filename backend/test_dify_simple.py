#!/usr/bin/env python
"""
🎯 Dify Benchmark 簡化真實測試
直接使用 DifyTestRunner 發送真實問題

執行方式：
docker exec ai-django python /app/test_dify_simple.py
"""

import os
import sys
import django
import time
from datetime import datetime

# Django 設置
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.models import DifyConfigVersion, DifyBenchmarkTestCase
from library.dify_benchmark.dify_test_runner import DifyTestRunner

def main():
    print("\n" + "=" * 80)
    print("  🎯 Dify Benchmark 簡化真實測試")
    print("=" * 80)
    print(f"\n測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 1. 獲取測試版本
    try:
        version = DifyConfigVersion.objects.get(version_name="Dify 二階搜尋 v1.1")
        print(f"✅ 測試版本: {version.version_name}")
        print(f"   API URL: {version.dify_api_url}")
        print(f"   API Key: {version.dify_api_key[:20]}...\n")
    except DifyConfigVersion.DoesNotExist:
        print("❌ 找不到測試版本 'Dify 二階搜尋 v1.1'")
        print("\n可用版本:")
        for v in DifyConfigVersion.objects.filter(is_active=True):
            print(f"   - {v.version_name}")
        return 1
    
    # 2. 獲取測試案例（取前 3 個）
    test_cases = list(DifyBenchmarkTestCase.objects.filter(is_active=True)[:3])
    
    if not test_cases:
        print("❌ 沒有找到活躍的測試案例")
        return 1
    
    print(f"📋 測試案例: {len(test_cases)} 個\n")
    for i, tc in enumerate(test_cases, 1):
        print(f"   {i}. {tc.question[:60]}...")
        if tc.answer_keywords:
            print(f"      關鍵字: {tc.answer_keywords}")
    
    # 3. 順序執行測試
    print("\n" + "-" * 80)
    print("🐢 測試 1: 順序執行 (舊模式)")
    print("-" * 80)
    
    runner_sequential = DifyTestRunner(
        version=version,
        use_ai_evaluator=False,  # 使用關鍵字評分
        max_workers=1
    )
    
    try:
        start_time = time.time()
        test_run_seq = runner_sequential.run_batch_tests(
            test_cases=test_cases,
            run_name=f"順序測試 {datetime.now().strftime('%H:%M:%S')}",
            batch_id=f"seq_{int(time.time())}"
        )
        elapsed_seq = time.time() - start_time
        
        print(f"\n✅ 順序執行完成")
        print(f"   耗時: {elapsed_seq:.2f} 秒")
        print(f"   測試 ID: {test_run_seq.id}")
        print(f"   通過: {test_run_seq.passed_cases}/{test_run_seq.total_test_cases}")
        
        # 顯示每個測試的答案
        results_seq = test_run_seq.results.all()
        for i, result in enumerate(results_seq, 1):
            print(f"\n   📝 測試 {i}:")
            print(f"      問題: {result.test_case.question[:50]}...")
            print(f"      通過: {'✅' if result.is_passed else '❌'}")
            print(f"      分數: {result.score}/{result.test_case.max_score}")
            print(f"      回應: {result.dify_answer[:150]}...")
            print(f"      耗時: {result.response_time}s")
        
    except Exception as e:
        print(f"\n❌ 順序執行失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        elapsed_seq = 0
    
    time.sleep(2)
    
    # 4. 並行執行測試
    print("\n" + "-" * 80)
    print("🚀 測試 2: 並行執行 (新模式 - 3 個線程)")
    print("-" * 80)
    
    runner_parallel = DifyTestRunner(
        version=version,
        use_ai_evaluator=False,
        max_workers=3  # 3 個並行線程
    )
    
    try:
        start_time = time.time()
        test_run_par = runner_parallel.run_batch_tests_parallel(
            test_cases=test_cases,
            run_name=f"並行測試 {datetime.now().strftime('%H:%M:%S')}",
            batch_id=f"par_{int(time.time())}"
        )
        elapsed_par = time.time() - start_time
        
        print(f"\n✅ 並行執行完成")
        print(f"   耗時: {elapsed_par:.2f} 秒")
        print(f"   測試 ID: {test_run_par.id}")
        print(f"   通過: {test_run_par.passed_cases}/{test_run_par.total_test_cases}")
        
        # 顯示每個測試的答案
        results_par = test_run_par.results.all()
        for i, result in enumerate(results_par, 1):
            print(f"\n   📝 測試 {i}:")
            print(f"      問題: {result.test_case.question[:50]}...")
            print(f"      通過: {'✅' if result.is_passed else '❌'}")
            print(f"      分數: {result.score}/{result.test_case.max_score}")
            print(f"      回應: {result.dify_answer[:150]}...")
            print(f"      耗時: {result.response_time}s")
        
    except Exception as e:
        print(f"\n❌ 並行執行失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        elapsed_par = 0
    
    # 5. 效能對比
    if elapsed_seq > 0 and elapsed_par > 0:
        print("\n" + "=" * 80)
        print("  📊 效能對比")
        print("=" * 80)
        print(f"\n順序執行: {elapsed_seq:.2f} 秒")
        print(f"並行執行: {elapsed_par:.2f} 秒")
        print(f"加速比: {elapsed_seq/elapsed_par:.2f}x")
        print(f"效能提升: {((elapsed_seq-elapsed_par)/elapsed_seq*100):.1f}%")
        
        if elapsed_par < elapsed_seq:
            print("\n✅ 並行執行顯著快於順序執行！")
        else:
            print("\n⚠️  並行執行未能提升效能")
    
    print("\n" + "=" * 80)
    print("  🎉 測試完成")
    print("=" * 80)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
