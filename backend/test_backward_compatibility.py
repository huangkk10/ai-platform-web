#!/usr/bin/env python
"""
測試向後兼容性
============

目的：
1. 確認現有版本（Baseline ID=3, Current ID=4）使用舊路徑
2. 確認搜尋結果格式正確
3. 確認沒有錯誤或異常

預期行為：
- version.parameters 沒有 use_strategy_engine 或為 False
- 日誌顯示「使用標準搜尋方法（向後兼容）」
- 返回結果包含 document_id 和 score
"""

import os
import sys
import django

# 設置 Django 環境
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.models import SearchAlgorithmVersion, BenchmarkTestCase
from library.benchmark.test_runner import BenchmarkTestRunner
import logging

# 設置日誌
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

def test_version_backward_compatibility(version_id, version_name):
    """測試特定版本的向後兼容性"""
    print(f"\n{'='*80}")
    print(f"🧪 測試版本: {version_name} (ID={version_id})")
    print(f"{'='*80}")
    
    try:
        # 載入版本
        version = SearchAlgorithmVersion.objects.get(id=version_id)
        print(f"\n✅ 版本資訊:")
        print(f"   - 版本名稱: {version.version_name}")
        print(f"   - 版本代碼: {version.version_code}")
        print(f"   - 算法類型: {version.algorithm_type}")
        print(f"   - 參數: {version.parameters}")
        
        # 檢查參數
        params = version.parameters or {}
        use_strategy_engine = params.get('use_strategy_engine', False)
        
        print(f"\n🔍 參數檢查:")
        print(f"   - use_strategy_engine: {use_strategy_engine}")
        
        if use_strategy_engine:
            print(f"   ⚠️  警告: 此版本啟用了策略引擎（應該為 False）")
            return False
        else:
            print(f"   ✅ 正確: 使用舊路徑（向後兼容）")
        
        # 獲取測試案例
        test_cases = BenchmarkTestCase.objects.filter(
            is_active=True
        ).order_by('id')[:3]  # 只測試前 3 個
        
        if not test_cases:
            print(f"\n⚠️  沒有可用的測試案例")
            return False
        
        print(f"\n📝 測試案例: {len(test_cases)} 個")
        
        # 執行測試
        runner = BenchmarkTestRunner(version_id=version_id, verbose=True)
        
        success_count = 0
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n[{i}/{len(test_cases)}] 測試: {test_case.question[:50]}...")
            
            result = runner.run_single_test(test_case, save_to_db=False)
            
            # 驗證結果格式
            if result.get('returned_document_ids'):
                print(f"   ✅ 返回 {len(result['returned_document_ids'])} 個結果")
                print(f"   - Document IDs: {result['returned_document_ids'][:3]}...")
                print(f"   - Response Time: {result['response_time']:.2f} ms")
                print(f"   - Precision: {result.get('precision', 0):.2%}")
                print(f"   - Recall: {result.get('recall', 0):.2%}")
                success_count += 1
            else:
                print(f"   ⚠️  沒有返回結果")
        
        print(f"\n{'='*80}")
        print(f"📊 測試結果: {success_count}/{len(test_cases)} 成功")
        print(f"{'='*80}")
        
        return success_count == len(test_cases)
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主測試流程"""
    print("\n" + "="*80)
    print("🧪 向後兼容性測試")
    print("="*80)
    print("\n目標:")
    print("1. 確認現有版本使用舊路徑（search_knowledge）")
    print("2. 確認搜尋結果格式正確")
    print("3. 確認沒有錯誤或異常")
    
    # 測試版本列表
    test_versions = [
        (3, "Baseline"),
        (4, "Current"),
    ]
    
    results = {}
    
    for version_id, version_name in test_versions:
        try:
            success = test_version_backward_compatibility(version_id, version_name)
            results[version_name] = success
        except Exception as e:
            print(f"\n❌ 版本 {version_name} (ID={version_id}) 測試失敗: {str(e)}")
            results[version_name] = False
    
    # 總結
    print("\n" + "="*80)
    print("📊 測試總結")
    print("="*80)
    
    all_passed = True
    for version_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {version_name}")
        if not success:
            all_passed = False
    
    print("\n" + "="*80)
    if all_passed:
        print("🎉 所有測試通過！向後兼容性驗證成功！")
        print("✅ 現有版本不受影響，可以安全使用新策略引擎。")
    else:
        print("⚠️  部分測試失敗，需要檢查問題。")
    print("="*80 + "\n")
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
