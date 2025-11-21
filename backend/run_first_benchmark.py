#!/usr/bin/env python
"""
首次 Benchmark 測試執行腳本

用法：
    docker exec ai-django python /app/run_first_benchmark.py
    
或在 Django shell 中：
    docker exec -it ai-django python manage.py shell
    然後執行：exec(open('/app/run_first_benchmark.py').read())
"""

import sys
import os
import django

# Django 設定
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from django.utils import timezone
from api.models import SearchAlgorithmVersion, BenchmarkTestCase
from library.benchmark.test_runner import BenchmarkTestRunner

print("=" * 80)
print("🚀 Protocol Assistant Benchmark 系統 - 首次完整測試")
print("=" * 80)
print()

# ============================================================================
# Step 1: 確認測試版本
# ============================================================================
print("📋 Step 1/5: 確認測試版本...")
try:
    version = SearchAlgorithmVersion.objects.get(version_code='v2.1.0-baseline')
    print(f"   ✅ 找到版本: {version.version_code}")
    print(f"      名稱: {version.version_name}")
    print(f"      描述: {version.description}")
    print(f"      ID: {version.id}")
except SearchAlgorithmVersion.DoesNotExist:
    print("   ❌ 錯誤：找不到 v2.1.0-baseline 版本")
    print("   請先創建版本：")
    print("   SearchAlgorithmVersion.objects.create(")
    print("       version_code='v2.1.0-baseline',")
    print("       name='Baseline Version',")
    print("       is_baseline=True")
    print("   )")
    sys.exit(1)

print()

# ============================================================================
# Step 2: 獲取測試案例
# ============================================================================
print("📋 Step 2/5: 獲取測試案例...")
test_cases = list(BenchmarkTestCase.objects.filter(is_active=True).order_by('id'))
print(f"   ✅ 找到 {len(test_cases)} 個啟用的測試案例")

if len(test_cases) == 0:
    print("   ❌ 錯誤：沒有可用的測試案例")
    sys.exit(1)

# 顯示前 5 個測試案例
print("   前 5 個測試案例：")
for i, tc in enumerate(test_cases[:5], 1):
    print(f"      {i}. [{tc.category}] {tc.question[:50]}...")

print()

# ============================================================================
# Step 3: 詢問執行數量
# ============================================================================
print("📋 Step 3/5: 選擇執行數量...")
print(f"   總共有 {len(test_cases)} 個測試案例")
print()
print("   建議選項：")
print("   1) 快速測試：前 5 題 (約 1 分鐘)")
print("   2) 中型測試：前 10 題 (約 2 分鐘)")
print("   3) 完整測試：全部 50 題 (約 10 分鐘)")
print()

# 自動選擇（可修改）
test_count = 10  # 預設執行 10 題
print(f"   ✅ 自動選擇：執行前 {test_count} 題測試")
print()

# ============================================================================
# Step 4: 初始化測試執行器
# ============================================================================
print("📋 Step 4/5: 初始化測試執行器...")
try:
    runner = BenchmarkTestRunner(
        version_id=version.id,
        verbose=True  # 顯示詳細輸出
    )
    print("   ✅ 測試執行器初始化成功")
except Exception as e:
    print(f"   ❌ 錯誤：{str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# ============================================================================
# Step 5: 執行測試
# ============================================================================
print("📋 Step 5/5: 執行測試...")
print("=" * 80)
print()

try:
    test_run = runner.run_batch_tests(
        test_cases=test_cases[:test_count],
        run_name=f"首次完整測試 - {timezone.now().strftime('%Y-%m-%d %H:%M')}",
        run_type='manual',
        notes=f"執行前 {test_count} 個測試案例以驗證系統功能"
    )
    
    print()
    print("=" * 80)
    print("✅ 測試執行完成！")
    print("=" * 80)
    print()
    
    # 顯示結果摘要
    print("📊 測試結果摘要：")
    print(f"   執行 ID: {test_run.id}")
    print(f"   執行名稱: {test_run.run_name}")
    print(f"   狀態: {test_run.status}")
    print(f"   總測試數: {test_run.total_test_cases}")
    print(f"   已完成: {test_run.completed_test_cases}")
    print(f"   通過數: {test_run.passed_test_cases}")
    print(f"   失敗數: {test_run.failed_test_cases}")
    print()
    print(f"   📈 整體評分: {test_run.overall_score:.2f}")
    print(f"   🎯 Precision: {test_run.precision_pct:.1f}%")
    print(f"   📊 Recall: {test_run.recall_pct:.1f}%")
    print(f"   ⚖️  F1 Score: {test_run.f1_score_pct:.1f}%")
    print(f"   🚀 NDCG: {test_run.ndcg_pct:.1f}%")
    print(f"   ⏱️  平均回應時間: {test_run.avg_time_ms:.0f} ms")
    print()
    
    # 顯示執行時間
    if test_run.started_at and test_run.completed_at:
        duration = (test_run.completed_at - test_run.started_at).total_seconds()
        print(f"   ⏳ 總執行時間: {duration:.1f} 秒")
    
    print()
    print("=" * 80)
    print("🎉 Phase 3 系統驗證成功！")
    print("=" * 80)
    print()
    print("📝 後續步驟：")
    print("   1. 查看詳細結果：SELECT * FROM benchmark_test_result WHERE test_run_id = {};".format(test_run.id))
    print("   2. 分析失敗案例：找出 is_passed = FALSE 的記錄")
    print("   3. 準備進入 Phase 4：開發 REST API")
    print()

except Exception as e:
    print()
    print("=" * 80)
    print("❌ 測試執行失敗")
    print("=" * 80)
    print()
    print(f"錯誤訊息: {str(e)}")
    print()
    print("詳細錯誤追蹤：")
    import traceback
    traceback.print_exc()
    sys.exit(1)
