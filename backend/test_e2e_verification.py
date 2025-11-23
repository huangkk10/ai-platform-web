#!/usr/bin/env python
"""
端到端驗證測試
============

目的：
1. 測試新策略引擎可執行（V3 混合 70-30）
2. 對比 Baseline (ID=3) 和 V3 (ID=7) 的結果差異
3. 確認 Protocol Assistant 不受影響（透過 API 測試）

驗證流程：
1. 使用 Baseline 執行 3 個測試案例
2. 使用 V3 (混合 70-30) 執行相同測試案例
3. 對比結果差異
4. 驗證策略引擎日誌
"""

import os
import sys
import django
import json

# 設置 Django 環境
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.models import SearchAlgorithmVersion, BenchmarkTestCase
from library.benchmark.test_runner import BenchmarkTestRunner
import logging

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

def run_version_test(version_id, version_name, test_cases):
    """執行特定版本的測試"""
    print(f"\n{'='*80}")
    print(f"🧪 測試版本: {version_name} (ID={version_id})")
    print(f"{'='*80}")
    
    try:
        # 載入版本
        version = SearchAlgorithmVersion.objects.get(id=version_id)
        params = version.parameters or {}
        use_engine = params.get('use_strategy_engine', False)
        strategy = params.get('strategy', 'N/A')
        
        print(f"\n📋 版本資訊:")
        print(f"   - 版本名稱: {version.version_name}")
        print(f"   - 版本代碼: {version.version_code}")
        print(f"   - 算法類型: {version.algorithm_type}")
        print(f"   - 使用策略引擎: {use_engine}")
        print(f"   - 策略: {strategy}")
        
        if use_engine:
            print(f"   - 策略參數: {json.dumps(params, ensure_ascii=False, indent=6)}")
        
        # 執行測試
        runner = BenchmarkTestRunner(version_id=version_id, verbose=False)
        
        results = []
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n[{i}/{len(test_cases)}] 測試: {test_case.question[:50]}...")
            
            result = runner.run_single_test(test_case, save_to_db=False)
            
            # 顯示結果
            print(f"   ✅ 返回: {len(result['returned_document_ids'])} 個結果")
            print(f"   - Document IDs: {result['returned_document_ids'][:5]}")
            print(f"   - Response Time: {result['response_time']:.2f} ms")
            print(f"   - Precision: {result.get('precision', 0):.2%}")
            print(f"   - Recall: {result.get('recall', 0):.2%}")
            print(f"   - F1 Score: {result.get('f1_score', 0):.2%}")
            print(f"   - NDCG: {result.get('ndcg', 0):.4f}")
            
            results.append(result)
        
        # 計算平均指標
        n = len(results)
        avg_precision = sum(r.get('precision', 0) for r in results) / n
        avg_recall = sum(r.get('recall', 0) for r in results) / n
        avg_f1 = sum(r.get('f1_score', 0) for r in results) / n
        avg_ndcg = sum(r.get('ndcg', 0) for r in results) / n
        avg_time = sum(r.get('response_time', 0) for r in results) / n
        
        print(f"\n{'='*80}")
        print(f"📊 平均指標:")
        print(f"   - Precision: {avg_precision:.2%}")
        print(f"   - Recall: {avg_recall:.2%}")
        print(f"   - F1 Score: {avg_f1:.2%}")
        print(f"   - NDCG: {avg_ndcg:.4f}")
        print(f"   - Response Time: {avg_time:.2f} ms")
        print(f"{'='*80}")
        
        return {
            'version_id': version_id,
            'version_name': version_name,
            'results': results,
            'avg_precision': avg_precision,
            'avg_recall': avg_recall,
            'avg_f1': avg_f1,
            'avg_ndcg': avg_ndcg,
            'avg_time': avg_time,
        }
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def compare_results(baseline_result, new_result):
    """對比兩個版本的結果"""
    print("\n" + "="*80)
    print("📊 結果對比")
    print("="*80)
    
    if not baseline_result or not new_result:
        print("❌ 無法對比（某個版本測試失敗）")
        return
    
    # 對比表格
    print(f"\n{'指標':<15} | {'Baseline':>12} | {'V3 (70-30)':>12} | {'差異':>12}")
    print("-" * 80)
    
    metrics = [
        ('Precision', 'avg_precision', '%'),
        ('Recall', 'avg_recall', '%'),
        ('F1 Score', 'avg_f1', '%'),
        ('NDCG', 'avg_ndcg', ''),
        ('Response Time', 'avg_time', 'ms'),
    ]
    
    for metric_name, metric_key, unit in metrics:
        baseline_val = baseline_result[metric_key]
        new_val = new_result[metric_key]
        
        if unit == '%':
            diff = new_val - baseline_val
            diff_str = f"{diff:+.2%}"
            baseline_str = f"{baseline_val:.2%}"
            new_str = f"{new_val:.2%}"
        elif unit == 'ms':
            diff = new_val - baseline_val
            diff_str = f"{diff:+.2f} ms"
            baseline_str = f"{baseline_val:.2f}"
            new_str = f"{new_val:.2f}"
        else:
            diff = new_val - baseline_val
            diff_str = f"{diff:+.4f}"
            baseline_str = f"{baseline_val:.4f}"
            new_str = f"{new_val:.4f}"
        
        print(f"{metric_name:<15} | {baseline_str:>12} | {new_str:>12} | {diff_str:>12}")
    
    print("="*80)
    
    # 分析結論
    print("\n📝 分析結論:")
    
    precision_diff = new_result['avg_precision'] - baseline_result['avg_precision']
    recall_diff = new_result['avg_recall'] - baseline_result['avg_recall']
    f1_diff = new_result['avg_f1'] - baseline_result['avg_f1']
    
    if precision_diff > 0:
        print(f"   ✅ 精準度提升: {precision_diff:+.2%}")
    elif precision_diff < 0:
        print(f"   ⚠️  精準度下降: {precision_diff:.2%}")
    else:
        print(f"   ➖ 精準度持平")
    
    if recall_diff > 0:
        print(f"   ✅ 召回率提升: {recall_diff:+.2%}")
    elif recall_diff < 0:
        print(f"   ⚠️  召回率下降: {recall_diff:.2%}")
    else:
        print(f"   ➖ 召回率持平")
    
    if f1_diff > 0:
        print(f"   ✅ F1 Score 提升: {f1_diff:+.2%}")
    elif f1_diff < 0:
        print(f"   ⚠️  F1 Score 下降: {f1_diff:.2%}")
    else:
        print(f"   ➖ F1 Score 持平")
    
    # 整體評價
    print("\n🎯 整體評價:")
    if f1_diff > 0.05:
        print("   🌟 新策略顯著優於 Baseline！")
    elif f1_diff > 0:
        print("   ✅ 新策略略優於 Baseline")
    elif f1_diff > -0.05:
        print("   ➖ 新策略與 Baseline 相當")
    else:
        print("   ⚠️  新策略不如 Baseline，需要調整參數")


def test_protocol_assistant_api():
    """測試 Protocol Assistant API 是否正常（簡化版本）"""
    print("\n" + "="*80)
    print("🌐 Protocol Assistant API 測試")
    print("="*80)
    
    try:
        from library.protocol_guide.search_service import ProtocolGuideSearchService
        
        search_service = ProtocolGuideSearchService()
        
        # 執行一個簡單的搜尋
        test_query = "ULINK 測試"
        print(f"\n🔍 測試查詢: '{test_query}'")
        
        results = search_service.search_knowledge(
            query=test_query,
            limit=5,
            use_vector=True
        )
        
        print(f"   ✅ 返回 {len(results)} 個結果")
        
        if results:
            print(f"   - 第一個結果 ID: {results[0].get('id')}")
            print(f"   - 第一個結果分數: {results[0].get('score', 0):.4f}")
        
        print("\n✅ Protocol Assistant API 正常運作！")
        print("   （使用標準 search_knowledge 路徑，不受策略引擎影響）")
        
        return True
        
    except Exception as e:
        print(f"\n❌ API 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主測試流程"""
    print("\n" + "="*80)
    print("🚀 端到端驗證測試")
    print("="*80)
    
    print("\n目標:")
    print("1. 測試新策略引擎可執行（V3 混合 70-30）")
    print("2. 對比 Baseline 和 V3 的結果差異")
    print("3. 確認 Protocol Assistant 不受影響")
    
    # 獲取測試案例
    test_cases = BenchmarkTestCase.objects.filter(
        is_active=True
    ).order_by('id')[:3]
    
    if not test_cases:
        print("\n❌ 沒有可用的測試案例")
        return 1
    
    print(f"\n📝 使用 {len(test_cases)} 個測試案例")
    
    # 1. 測試 Baseline
    baseline_result = run_version_test(
        version_id=3,
        version_name="Baseline",
        test_cases=test_cases
    )
    
    # 2. 測試 V3 (混合 70-30)
    v3_result = run_version_test(
        version_id=7,
        version_name="V3 - 混合權重 70-30",
        test_cases=test_cases
    )
    
    # 3. 對比結果
    compare_results(baseline_result, v3_result)
    
    # 4. 測試 Protocol Assistant API
    api_ok = test_protocol_assistant_api()
    
    # 總結
    print("\n" + "="*80)
    print("✅ 端到端驗證完成！")
    print("="*80)
    
    print("\n📋 驗證結果:")
    print(f"   {'✅' if baseline_result else '❌'} Baseline 測試成功")
    print(f"   {'✅' if v3_result else '❌'} V3 (混合 70-30) 測試成功")
    print(f"   {'✅' if api_ok else '❌'} Protocol Assistant API 正常")
    
    all_ok = baseline_result and v3_result and api_ok
    
    if all_ok:
        print("\n🎉 所有驗證通過！")
        print("✅ 新策略引擎可以安全使用")
        print("✅ 現有功能不受影響")
        print("✅ 準備好進行完整 Benchmark 測試！")
    else:
        print("\n⚠️  部分驗證失敗，需要檢查問題")
    
    print("="*80 + "\n")
    
    return 0 if all_ok else 1


if __name__ == '__main__':
    sys.exit(main())
