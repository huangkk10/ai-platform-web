#!/usr/bin/env python
"""
測試不同搜尋版本是否產生不同的結果

測試目標：
1. V1 (section_only) vs V2 (document_only) 應該產生不同的文檔 ID 列表
2. V3-V5 (不同權重) 可能產生相似但不完全相同的結果

執行方式：
docker exec ai-django python test_version_differentiation.py
"""
import os
import sys
import django

# Django 設定
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from library.benchmark.test_runner import BenchmarkTestRunner
from api.models import BenchmarkTestCase

def test_version_differentiation():
    """測試版本差異化"""
    
    # 取得一個測試題目
    test_case = BenchmarkTestCase.objects.filter(is_active=True).first()
    
    if not test_case:
        print("❌ 找不到測試題目")
        return
    
    print(f"\n{'='*80}")
    print(f"測試題目: {test_case.question}")
    print(f"預期文檔 IDs: {test_case.expected_document_ids}")
    print(f"{'='*80}\n")
    
    # 測試所有版本 (ID 5-9: V1-V5)
    results_by_version = {}
    
    version_ids = [5, 6, 7, 8, 9]  # V1, V2, V3, V4, V5
    
    for version_id in version_ids:
        try:
            print(f"\n🔍 測試版本 {version_id} ...")
            
            # 創建測試執行器
            runner = BenchmarkTestRunner(version_id=version_id, verbose=True)
            
            # 執行單個測試
            result = runner.run_single_test(test_case, save_to_db=False)
            
            # 儲存結果
            returned_ids = result.get('returned_document_ids', [])
            results_by_version[version_id] = {
                'version_name': runner.version.version_name,
                'version_code': runner.version.version_code,
                'strategy': runner.version.parameters.get('strategy'),
                'parameters': runner.version.parameters,
                'returned_ids': returned_ids,
                'precision': result.get('precision', 0),
                'recall': result.get('recall', 0),
                'f1_score': result.get('f1_score', 0),
            }
            
            print(f"  ✅ 版本名稱: {runner.version.version_name}")
            print(f"  📋 策略: {runner.version.parameters.get('strategy')}")
            print(f"  🎯 返回文檔 IDs: {returned_ids[:5]}... (共 {len(returned_ids)} 個)")
            print(f"  📊 Precision: {result.get('precision', 0):.3f}, Recall: {result.get('recall', 0):.3f}")
            
        except Exception as e:
            print(f"  ❌ 版本 {version_id} 測試失敗: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # 比較結果
    print(f"\n{'='*80}")
    print("📊 版本比較結果")
    print(f"{'='*80}\n")
    
    # 檢查是否所有版本返回相同的文檔 ID
    all_ids = [tuple(r['returned_ids']) for r in results_by_version.values()]
    unique_ids = set(all_ids)
    
    print(f"✅ 測試的版本數: {len(results_by_version)}")
    print(f"📋 不同的結果數: {len(unique_ids)}")
    
    if len(unique_ids) == 1:
        print(f"\n❌ 問題：所有版本返回相同的文檔 ID！")
        print(f"   這表示版本配置沒有生效。")
    else:
        print(f"\n✅ 成功：不同版本產生了不同的結果！")
        print(f"\n詳細比較：")
        for v_id, result in results_by_version.items():
            print(f"\n版本 {v_id} ({result['version_code']}):")
            print(f"  策略: {result['strategy']}")
            print(f"  參數: {result['parameters']}")
            print(f"  返回 IDs: {result['returned_ids'][:5]}...")
            print(f"  效能: P={result['precision']:.3f}, R={result['recall']:.3f}, F1={result['f1_score']:.3f}")
    
    # 特別比較 V1 vs V2
    if 5 in results_by_version and 6 in results_by_version:
        v1_ids = set(results_by_version[5]['returned_ids'])
        v2_ids = set(results_by_version[6]['returned_ids'])
        
        print(f"\n🔎 V1 (section_only) vs V2 (document_only) 比較：")
        print(f"  V1 返回: {len(v1_ids)} 個文檔")
        print(f"  V2 返回: {len(v2_ids)} 個文檔")
        print(f"  共同文檔: {len(v1_ids & v2_ids)} 個")
        print(f"  V1 獨有: {len(v1_ids - v2_ids)} 個")
        print(f"  V2 獨有: {len(v2_ids - v1_ids)} 個")
        
        if v1_ids == v2_ids:
            print(f"  ❌ V1 和 V2 返回完全相同的文檔 ID")
        else:
            print(f"  ✅ V1 和 V2 返回不同的文檔 ID")

if __name__ == '__main__':
    test_version_differentiation()
