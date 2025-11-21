#!/usr/bin/env python
"""驗證測試案例質量腳本"""

import os, sys, django, time
sys.path.insert(0, "/app")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ai_platform.settings")
django.setup()

from api.models import BenchmarkTestCase
from library.protocol_guide.search_service import ProtocolGuideSearchService

# 初始化搜尋服務
search_service = ProtocolGuideSearchService()

# 獲取所有測試案例
test_cases = BenchmarkTestCase.objects.filter(is_active=True).order_by("id")
total = test_cases.count()

print(f"\n{"="*80}")
print(f"🚀 開始驗證測試案例質量")
print(f"{"="*80}")
print(f"📊 測試範圍: {total} 題")
print(f"⚙️  搜尋參數: top_k=5, threshold=0.5")
print(f"{"="*80}\n")

passed, failed = 0, 0
failed_cases = []

for idx, test_case in enumerate(test_cases, 1):
    try:
        # 執行搜尋
        results = search_service.search_knowledge(
            query=test_case.question,
            top_k=5,
            similarity_threshold=0.5
        )
        
        # 提取返回的文檔 IDs
        returned_ids = [r["id"] for r in results]
        expected_ids = test_case.expected_document_ids
        
        # 檢查是否找到預期文檔
        found_ids = [exp_id for exp_id in expected_ids if exp_id in returned_ids]
        min_required = test_case.min_required_matches or 1
        is_passed = len(found_ids) >= min_required
        
        if is_passed:
            passed += 1
            status = "✅"
            detail = f"找到 {len(found_ids)}/{len(expected_ids)} 個預期文檔"
        else:
            failed += 1
            status = "❌"
            detail = f"找到 {len(found_ids)}/{len(expected_ids)} 個預期文檔"
            failed_cases.append({
                "id": test_case.id,
                "question": test_case.question,
                "difficulty": test_case.difficulty_level,
                "expected": expected_ids,
                "returned": returned_ids,
                "scores": [r.get("similarity", 0) for r in results[:3]]
            })
        
        print(f"[{idx:2d}/{total}] {status} | {test_case.difficulty_level:6s} | {detail}")
        print(f"       Q: {test_case.question[:60]}...")
        
        if not is_passed:
            print(f"       預期: {expected_ids}, 實際: {returned_ids[:3]}")
        
    except Exception as e:
        failed += 1
        print(f"[{idx:2d}/{total}] ❌ | ERROR  | {str(e)[:50]}")

pass_rate = (passed / total * 100) if total > 0 else 0

print(f"\n{"="*80}")
print(f"📊 驗證結果摘要")
print(f"{"="*80}")
print(f"✅ 通過: {passed} 題")
print(f"❌ 失敗: {failed} 題")
print(f"📈 通過率: {pass_rate:.1f}% ({passed}/{total})")
print(f"🎯 目標: ≥80% (40+/50)")

if pass_rate >= 80:
    print(f"✅ 已達標！")
else:
    need_fix = int(total * 0.8) - passed
    print(f"⚠️  未達標，需要改進 {need_fix} 題")

print(f"{"="*80}\n")

# 失敗案例分析
if failed_cases:
    print(f"❌ 失敗案例分析 ({len(failed_cases)} 題):")
    print(f"{"-"*80}")
    for idx, case in enumerate(failed_cases[:10], 1):  # 只顯示前10個
        print(f"\n{idx}. [{case["id"]}] {case["difficulty"]}")
        print(f"   Q: {case["question"][:70]}...")
        print(f"   預期: {case["expected"]}")
        print(f"   實際: {case["returned"][:3]}")
        if case["scores"]:
            print(f"   分數: {[f"{s:.3f}" for s in case["scores"]]}")

print(f"\n{"="*80}")
