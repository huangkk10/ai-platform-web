"""
分析混合權重策略的分數差異
==========================

比較 V3, V4, V5 的詳細分數
"""

import os
import sys
import django

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.models import SearchAlgorithmVersion
from library.protocol_guide.search_service import ProtocolGuideSearchService
from library.benchmark.search_strategies import HybridWeightedStrategy

def analyze_score_differences():
    """分析分數差異"""
    
    query = "Burn in Test 測試失敗時如何排查？"
    
    print("=" * 80)
    print(f"測試題目: {query}")
    print("=" * 80)
    
    versions = SearchAlgorithmVersion.objects.filter(
        id__in=[7, 8, 9]
    ).order_by('id')
    
    service = ProtocolGuideSearchService()
    all_results = {}
    
    for version in versions:
        params = version.parameters or {}
        section_weight = params.get('section_weight', 0.7)
        document_weight = params.get('document_weight', 0.3)
        section_threshold = params.get('section_threshold', 0.75)
        document_threshold = params.get('document_threshold', 0.65)
        
        hybrid_strategy = HybridWeightedStrategy(service)
        results = hybrid_strategy.execute(
            query=query,
            limit=15,  # 多取一些
            section_weight=section_weight,
            document_weight=document_weight,
            section_threshold=section_threshold,
            document_threshold=document_threshold
        )
        
        all_results[version.version_code] = {
            'name': version.version_name,
            'weights': f"{section_weight}/{document_weight}",
            'results': results
        }
    
    # 顯示每個版本的前 15 名分數
    print("\n" + "=" * 80)
    print("各版本的前 15 名文檔及分數")
    print("=" * 80)
    
    for version_code, data in all_results.items():
        print(f"\n{data['name']} (權重: {data['weights']}):")
        print(f"{'排名':<4} {'Doc ID':<8} {'Final Score':<12} {'Section':<10} {'Document':<10} {'來源':<8}")
        print("-" * 70)
        
        for rank, result in enumerate(data['results'], 1):
            doc_id = result.get('document_id', 'N/A')
            final_score = result.get('final_score', 0)
            section_score = result.get('section_weighted_score', 0)
            document_score = result.get('document_weighted_score', 0)
            source = result.get('source', 'N/A')
            
            print(f"{rank:<4} {doc_id:<8} {final_score:<12.4f} {section_score:<10.4f} {document_score:<10.4f} {source:<8}")
    
    # 比較排名差異
    print("\n" + "=" * 80)
    print("📊 排名比較（前 10 名）")
    print("=" * 80)
    
    v3_ids = [r.get('document_id') for r in all_results['v3.3-hybrid-70-30']['results'][:10]]
    v4_ids = [r.get('document_id') for r in all_results['v3.4-hybrid-50-50']['results'][:10]]
    v5_ids = [r.get('document_id') for r in all_results['v3.5-hybrid-80-20']['results'][:10]]
    
    print(f"\nV3 (70-30): {v3_ids}")
    print(f"V4 (50-50): {v4_ids}")
    print(f"V5 (80-20): {v5_ids}")
    
    if v3_ids != v4_ids:
        print("\n✅ V3 和 V4 的前 10 名有差異")
    else:
        print("\n⚠️ V3 和 V4 的前 10 名相同")
    
    if v3_ids != v5_ids:
        print("✅ V3 和 V5 的前 10 名有差異")
    else:
        print("⚠️ V3 和 V5 的前 10 名相同")
    
    if v4_ids != v5_ids:
        print("✅ V4 和 V5 的前 10 名有差異")
    else:
        print("⚠️ V4 和 V5 的前 10 名相同")

if __name__ == "__main__":
    analyze_score_differences()
