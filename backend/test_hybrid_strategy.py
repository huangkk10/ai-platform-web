"""
測試混合權重策略 (V3-V5)
============================

測試目標：
- V3 (section_weight=0.7, document_weight=0.3)
- V4 (section_weight=0.5, document_weight=0.5)
- V5 (section_weight=0.8, document_weight=0.2)

預期結果：
- 每個版本應該返回不同的結果（權重不同）
- 與 V1 (section_only) 和 V2 (document_only) 比較
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.models import SearchAlgorithmVersion
from library.protocol_guide.search_service import ProtocolGuideSearchService
from library.benchmark.search_strategies import HybridWeightedStrategy

def test_hybrid_strategy():
    """測試混合權重策略"""
    
    # 測試查詢
    query = "Burn in Test 測試失敗時如何排查？"
    
    print("=" * 80)
    print(f"測試題目: {query}")
    print("=" * 80)
    
    # 獲取版本配置
    versions = SearchAlgorithmVersion.objects.filter(
        id__in=[7, 8, 9]  # V3, V4, V5
    ).order_by('id')
    
    service = ProtocolGuideSearchService()
    results_by_version = {}
    
    for version in versions:
        print(f"\n{'=' * 80}")
        print(f"版本: {version.version_name} (ID={version.id})")
        print(f"參數: {version.parameters}")
        print('=' * 80)
        
        params = version.parameters or {}
        section_weight = params.get('section_weight', 0.7)
        document_weight = params.get('document_weight', 0.3)
        section_threshold = params.get('section_threshold', 0.75)
        document_threshold = params.get('document_threshold', 0.65)
        
        print(f"執行混合權重搜尋:")
        print(f"  section_weight={section_weight}")
        print(f"  document_weight={document_weight}")
        print(f"  section_threshold={section_threshold}")
        print(f"  document_threshold={document_threshold}")
        
        # 使用 HybridWeightedStrategy
        hybrid_strategy = HybridWeightedStrategy(service)
        results = hybrid_strategy.execute(
            query=query,
            limit=10,
            section_weight=section_weight,
            document_weight=document_weight,
            section_threshold=section_threshold,
            document_threshold=document_threshold
        )
        
        # 提取文檔 IDs
        doc_ids = []
        for result in results:
            doc_id = result.get('metadata', {}).get('document_id') or result.get('document_id')
            if doc_id:
                doc_ids.append(doc_id)
        
        results_by_version[version.id] = {
            'version_name': version.version_name,
            'doc_ids': doc_ids,
            'section_weight': section_weight,
            'document_weight': document_weight,
            'result_count': len(results)
        }
        
        print(f"\n結果:")
        print(f"  返回文檔數: {len(results)}")
        print(f"  文檔 IDs: {doc_ids}")
        
        # 顯示前 3 個結果的分數詳情
        print(f"\n  前 3 個結果詳情:")
        for i, result in enumerate(results[:3], 1):
            print(f"    {i}. Doc ID={result.get('document_id', 'N/A')}")
            print(f"       section_score={result.get('section_score', 0):.4f} (weighted: {result.get('section_weighted_score', 0):.4f})")
            print(f"       document_score={result.get('document_score', 0):.4f} (weighted: {result.get('document_weighted_score', 0):.4f})")
            print(f"       final_score={result.get('final_score', 0):.4f}")
            print(f"       source={result.get('source', 'N/A')}")
    
    # 比較結果
    print("\n" + "=" * 80)
    print("📊 比較結果")
    print("=" * 80)
    
    print(f"\n測試版本數: {len(results_by_version)}")
    
    # 檢查是否有不同結果
    all_ids = [tuple(r['doc_ids']) for r in results_by_version.values()]
    unique_results = len(set(all_ids))
    
    print(f"不同結果數: {unique_results}")
    
    if unique_results > 1:
        print("✅ 不同版本產生了不同的結果 - 混合權重策略成功！")
    else:
        print("❌ 所有版本返回相同結果 - 混合權重策略可能有問題")
    
    # 詳細比較
    print("\n各版本結果:")
    for version_id, data in results_by_version.items():
        print(f"  {data['version_name']} (section={data['section_weight']}, document={data['document_weight']}):")
        print(f"    IDs: {data['doc_ids']}")
    
    # V3 vs V4 比較
    if 7 in results_by_version and 8 in results_by_version:
        v3_ids = set(results_by_version[7]['doc_ids'])
        v4_ids = set(results_by_version[8]['doc_ids'])
        
        common = v3_ids & v4_ids
        v3_only = v3_ids - v4_ids
        v4_only = v4_ids - v3_ids
        
        print(f"\n🔎 V3 (70-30) vs V4 (50-50):")
        print(f"  共同文檔: {common}")
        print(f"  V3 獨有: {v3_only}")
        print(f"  V4 獨有: {v4_only}")
        
        if v3_only or v4_only:
            print(f"  ✅ V3 和 V4 有差異")
        else:
            print(f"  ⚠️ V3 和 V4 完全相同")
    
    # V3 vs V5 比較
    if 7 in results_by_version and 9 in results_by_version:
        v3_ids = set(results_by_version[7]['doc_ids'])
        v5_ids = set(results_by_version[9]['doc_ids'])
        
        common = v3_ids & v5_ids
        v3_only = v3_ids - v5_ids
        v5_only = v5_ids - v3_ids
        
        print(f"\n🔎 V3 (70-30) vs V5 (80-20):")
        print(f"  共同文檔: {common}")
        print(f"  V3 獨有: {v3_only}")
        print(f"  V5 獨有: {v5_only}")
        
        if v3_only or v5_only:
            print(f"  ✅ V3 和 V5 有差異")
        else:
            print(f"  ⚠️ V3 和 V5 完全相同")

if __name__ == "__main__":
    test_hybrid_strategy()
