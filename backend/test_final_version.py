#!/usr/bin/env python
"""
最終測試：確認不同版本會產生不同的搜尋結果

這個腳本不依賴 BenchmarkTestRunner，直接調用 search_with_vectors 來驗證版本差異化
"""
import os
import sys
import django

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from library.protocol_guide.search_service import ProtocolGuideSearchService
from api.models import BenchmarkTestCase, SearchAlgorithmVersion

def test_final():
    """最終測試"""
    
    test_case = BenchmarkTestCase.objects.filter(is_active=True).first()
    query = test_case.question
    
    print(f"\n{'='*80}")
    print(f"測試題目: {query}")
    print(f"預期文檔 IDs: {test_case.expected_document_ids}")
    print(f"{'='*80}\n")
    
    service = ProtocolGuideSearchService()
    
    # 測試所有版本
    versions = SearchAlgorithmVersion.objects.filter(id__in=[5, 6, 7, 8, 9]).order_by('id')
    results_by_version = {}
    
    for version in versions:
        params = version.parameters or {}
        strategy = params.get('strategy', 'auto')
        
        # 決定搜尋模式
        if strategy == 'section_only':
            search_mode = 'section_only'
            threshold = params.get('section_threshold', 0.75)
        elif strategy == 'document_only':
            search_mode = 'document_only'
            threshold = params.get('document_threshold', 0.65)
        else:
            search_mode = 'auto'
            threshold = 0.7
        
        print(f"\n🔍 測試 {version.version_name} (ID={version.id})")
        print(f"   策略: {strategy}")
        print(f"   參數: {params}")
        print(f"   search_mode: {search_mode}, threshold: {threshold}")
        
        # 執行搜尋
        results = service.search_with_vectors(
            query=query,
            limit=10,
            threshold=threshold,
            search_mode=search_mode,
            stage=1
        )
        
        ids = [r.get('metadata', {}).get('id') for r in results]
        print(f"   返回 IDs: {ids}")
        
        results_by_version[version.id] = {
            'version_name': version.version_name,
            'strategy': strategy,
            'ids': ids
        }
    
    # 比較結果
    print(f"\n{'='*80}")
    print("📊 比較結果")
    print(f"{'='*80}\n")
    
    all_ids = [tuple(r['ids']) for r in results_by_version.values()]
    unique_ids = set(all_ids)
    
    print(f"測試版本數: {len(results_by_version)}")
    print(f"不同結果數: {len(unique_ids)}")
    
    if len(unique_ids) == 1:
        print(f"\n❌ 所有版本返回相同的結果 - 版本差異化失敗")
    else:
        print(f"\n✅ 不同版本產生了不同的結果 - 版本差異化成功！")
    
    # 詳細比較
    print(f"\n詳細結果：")
    for v_id, result in results_by_version.items():
        print(f"\n版本 {v_id} - {result['version_name']}")
        print(f"  策略: {result['strategy']}")
        print(f"  IDs: {result['ids']}")
    
    # 特別比較 V1 vs V2
    if 5 in results_by_version and 6 in results_by_version:
        v1_ids = set(results_by_version[5]['ids'])
        v2_ids = set(results_by_version[6]['ids'])
        
        print(f"\n🔎 V1 (section_only) vs V2 (document_only):")
        print(f"  共同文檔: {v1_ids & v2_ids}")
        print(f"  V1 獨有: {v1_ids - v2_ids}")
        print(f"  V2 獨有: {v2_ids - v1_ids}")
        
        if v1_ids == v2_ids:
            print(f"  ❌ V1 和 V2 完全相同")
        else:
            print(f"  ✅ V1 和 V2 有差異")

if __name__ == '__main__':
    test_final()
