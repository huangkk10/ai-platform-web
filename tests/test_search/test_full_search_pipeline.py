#!/usr/bin/env python
"""
完整流程測試：模擬 Protocol Assistant 實際查詢
測試混合搜尋（向量 + 關鍵字）+ threshold 過濾
"""

import os
import sys
import django
import json

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from library.protocol_guide.search_service import ProtocolGuideSearchService
from library.dify_knowledge import DifyKnowledgeSearchHandler

def test_full_search_pipeline():
    """測試完整的搜尋管道"""
    print("=" * 80)
    print("🔬 完整流程測試：Protocol Assistant 搜尋")
    print("=" * 80)
    
    query = "sop"
    threshold = 0.75
    top_k = 3
    
    print(f"\n📝 測試參數:")
    print(f"   查詢: '{query}'")
    print(f"   Threshold: {threshold}")
    print(f"   Top K: {top_k}")
    
    # === 步驟 1：執行混合搜尋 ===
    print(f"\n" + "=" * 80)
    print("📊 步驟 1：執行混合搜尋（向量 + 關鍵字）")
    print("=" * 80)
    
    service = ProtocolGuideSearchService()
    
    # 執行完整搜尋（包含向量和關鍵字）
    results = service.search_knowledge(query, limit=top_k, use_vector=True)
    
    print(f"\n搜尋結果: {len(results)} 條")
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result.get('title', 'Unknown')}")
        print(f"   分數: {result.get('score', 0):.2f}")
        print(f"   內容: {result.get('content', '')[:100]}...")
    
    # === 步驟 2：應用 threshold 過濾 ===
    print(f"\n" + "=" * 80)
    print("📊 步驟 2：應用 Threshold 過濾")
    print("=" * 80)
    
    print(f"\n過濾前: {len(results)} 條結果")
    
    filtered_results = [r for r in results if r.get('score', 0) >= threshold]
    rejected_results = [r for r in results if r.get('score', 0) < threshold]
    
    print(f"過濾後: {len(filtered_results)} 條結果")
    print(f"被拒絕: {len(rejected_results)} 條結果")
    
    if rejected_results:
        print(f"\n❌ 被拒絕的結果 (分數 < {threshold}):")
        for result in rejected_results:
            title = result.get('title', 'Unknown')
            score = result.get('score', 0)
            print(f"   - {title} ({score:.2f})")
    
    if filtered_results:
        print(f"\n✅ 通過過濾的結果 (分數 >= {threshold}):")
        for result in filtered_results:
            title = result.get('title', 'Unknown')
            score = result.get('score', 0)
            print(f"   - {title} ({score:.2f})")
    
    # === 步驟 3：使用 DifyKnowledgeSearchHandler 過濾 ===
    print(f"\n" + "=" * 80)
    print("📊 步驟 3：使用 DifyKnowledgeSearchHandler 過濾")
    print("=" * 80)
    
    handler = DifyKnowledgeSearchHandler()
    
    # 模擬 Dify 的過濾邏輯
    dify_filtered = handler.filter_results_by_score(results, threshold)
    
    print(f"\nDify 過濾結果: {len(dify_filtered)} 條")
    
    if dify_filtered:
        print(f"\n最終返回給 Dify 的結果:")
        for i, result in enumerate(dify_filtered, 1):
            print(f"{i}. {result.get('title', 'Unknown')} ({result.get('score', 0):.2f})")
    
    # === 驗證結果 ===
    print(f"\n" + "=" * 80)
    print("🎯 驗證結果")
    print("=" * 80)
    
    # 檢查 UNH-IOL 是否被正確過濾
    unh_iol_in_final = any('UNH-IOL' in r.get('title', '') for r in dify_filtered)
    
    print(f"\n✅ 關鍵驗證:")
    print(f"   UNH-IOL 是否出現在最終結果: {'是' if unh_iol_in_final else '否'}")
    
    if not unh_iol_in_final:
        print(f"   ✅ 正確！UNH-IOL 已被過濾掉（分數 < {threshold}）")
    else:
        print(f"   ❌ 錯誤！UNH-IOL 不應該出現（分數應該 < {threshold}）")
    
    print(f"\n📊 統計:")
    print(f"   初始搜尋結果: {len(results)} 條")
    print(f"   通過過濾: {len(filtered_results)} 條")
    print(f"   被拒絕: {len(rejected_results)} 條")
    print(f"   過濾率: {len(rejected_results)/len(results)*100:.1f}%" if results else "   過濾率: N/A")
    
    print(f"\n" + "=" * 80)
    print("✅ 測試完成")
    print("=" * 80)
    
    return dify_filtered

if __name__ == "__main__":
    try:
        test_full_search_pipeline()
    except Exception as e:
        print(f"\n❌ 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
