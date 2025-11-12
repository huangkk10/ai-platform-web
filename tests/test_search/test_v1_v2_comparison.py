#!/usr/bin/env python
"""
檢查 V1 vs V2 實際返回的資料差異
用於理解為什麼 V1 無法回答問題
"""

import os
import sys
import django

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from library.common.knowledge_base.section_search_service import SectionSearchService


def test_v1_vs_v2_comparison():
    """對比 V1 和 V2 返回的資料"""
    print("\n" + "="*80)
    print("🔍 V1 vs V2 資料對比測試")
    print("="*80)
    
    service = SectionSearchService()
    query = "iol 如何放測"
    
    # V1 搜尋
    print("\n" + "─"*80)
    print("📊 V1 基礎搜尋（無上下文）")
    print("─"*80)
    
    v1_results = service.search_sections(
        query=query,
        source_table='protocol_guide',
        limit=2,
        threshold=0.7
    )
    
    print(f"\n找到 {len(v1_results)} 個結果")
    
    for i, result in enumerate(v1_results, 1):
        print(f"\n結果 {i}:")
        print(f"  Section ID: {result.get('section_id')}")
        print(f"  標題: {result.get('heading_text')}")
        print(f"  相似度: {result.get('similarity', 0):.2%}")
        print(f"  內容長度: {len(result.get('content', ''))} 字元")
        print(f"  內容預覽: {result.get('content', '')[:200]}...")
        
        # 檢查是否有上下文
        has_context = any(key in result for key in ['parent', 'children', 'previous', 'next'])
        print(f"  ❌ 包含上下文: {has_context}")
    
    # V2 搜尋（Adjacent 模式）
    print("\n" + "─"*80)
    print("📊 V2 上下文搜尋（Adjacent 模式）")
    print("─"*80)
    
    v2_results = service.search_with_context(
        query=query,
        source_table='protocol_guide',
        limit=2,
        threshold=0.7,
        context_window=1,
        context_mode='adjacent'
    )
    
    print(f"\n找到 {len(v2_results)} 個結果")
    
    total_v2_content = 0
    
    for i, result in enumerate(v2_results, 1):
        print(f"\n結果 {i}:")
        print(f"  Section ID: {result.get('section_id')}")
        print(f"  標題: {result.get('heading_text')}")
        print(f"  相似度: {result.get('similarity', 0):.2%}")
        
        # 計算總內容量
        main_content = len(result.get('content', ''))
        previous_content = sum(len(p.get('content', '')) for p in result.get('previous', []))
        next_content = sum(len(n.get('content', '')) for n in result.get('next', []))
        
        total_content = main_content + previous_content + next_content
        total_v2_content += total_content
        
        print(f"  主要內容: {main_content} 字元")
        print(f"  前段落內容: {previous_content} 字元 (共 {len(result.get('previous', []))} 個)")
        print(f"  後段落內容: {next_content} 字元 (共 {len(result.get('next', []))} 個)")
        print(f"  ✅ 總內容量: {total_content} 字元")
        
        # 顯示上下文段落標題
        previous = result.get('previous', [])
        next_sections = result.get('next', [])
        
        if previous:
            print(f"\n  ⬆️  前段落:")
            for p in previous:
                print(f"      - {p.get('section_id')}: {p.get('heading_text')}")
                print(f"        內容: {p.get('content', '')[:100]}...")
        
        print(f"\n  📌 當前段落: {result.get('section_id')}")
        print(f"        內容: {result.get('content', '')[:100]}...")
        
        if next_sections:
            print(f"\n  ⬇️  後段落:")
            for n in next_sections:
                print(f"      - {n.get('section_id')}: {n.get('heading_text')}")
                print(f"        內容: {n.get('content', '')[:100]}...")
    
    # 總結對比
    print("\n" + "="*80)
    print("📊 V1 vs V2 資料量對比")
    print("="*80)
    
    v1_total_content = sum(len(r.get('content', '')) for r in v1_results)
    
    print(f"\nV1 總內容量: {v1_total_content} 字元")
    print(f"V2 總內容量: {total_v2_content} 字元")
    print(f"\n✅ V2 比 V1 多 {total_v2_content - v1_total_content} 字元")
    print(f"   增加倍數: {total_v2_content / v1_total_content:.2f}x")
    
    # 結論
    print("\n" + "="*80)
    print("🎯 結論")
    print("="*80)
    print("\n為什麼 V1 無法回答問題？")
    print("  1. V1 只返回匹配段落的標題和內容")
    print("  2. 如果關鍵資訊在前後段落中，V1 看不到")
    print("  3. AI 收到的上下文不完整，無法理解完整流程")
    
    print("\n為什麼 V2 可以回答？")
    print("  1. V2 返回匹配段落 + 前後相鄰段落")
    print(f"  2. 提供 {total_v2_content / v1_total_content:.2f}x 的上下文資訊")
    print("  3. AI 可以看到完整的測試流程表格")
    print("  4. 能夠理解上下文並給出完整答案")
    
    print("\n✅ 這是正常的！V2 的設計目的就是解決這個問題。")


if __name__ == '__main__':
    test_v1_vs_v2_comparison()
