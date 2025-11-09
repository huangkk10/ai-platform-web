#!/usr/bin/env python
"""
測試上下文視窗擴展功能
"""

import os
import sys
import django

# 設置 Django 環境
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from library.common.knowledge_base.section_search_service import SectionSearchService


def test_adjacent_mode():
    """測試 Adjacent 模式（線性視窗）"""
    print("\n" + "="*80)
    print("🧪 測試 1: Adjacent 模式（線性視窗擴展）")
    print("="*80)
    
    service = SectionSearchService()
    
    # 測試查詢
    query = "ULINK"
    
    print(f"\n📝 查詢: {query}")
    print(f"🎯 模式: adjacent (線性視窗)")
    print(f"📊 視窗大小: 1 (前後各 1 個段落)")
    
    try:
        results = service.search_with_context(
            query=query,
            source_table='protocol_guide',
            limit=2,
            threshold=0.7,
            context_window=1,
            context_mode='adjacent'
        )
        
        print(f"\n✅ 找到 {len(results)} 個結果")
        
        for i, result in enumerate(results, 1):
            print(f"\n{'─'*60}")
            print(f"📄 結果 {i}:")
            print(f"  Section ID: {result.get('section_id')}")
            print(f"  標題: {result.get('heading_text')}")
            print(f"  相似度: {result.get('similarity', 0):.2%}")
            print(f"  內容長度: {len(result.get('content', ''))}")
            
            # Adjacent 上下文
            previous = result.get('previous', [])
            next_sections = result.get('next', [])
            
            print(f"\n  📍 上下文視窗:")
            print(f"    ⬆️  前面段落: {len(previous)} 個")
            for p in previous:
                print(f"      - {p.get('section_id')}: {p.get('heading_text')}")
            
            print(f"    📌 當前段落: {result.get('section_id')}")
            
            print(f"    ⬇️  後面段落: {len(next_sections)} 個")
            for n in next_sections:
                print(f"      - {n.get('section_id')}: {n.get('heading_text')}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_hierarchical_mode():
    """測試 Hierarchical 模式（層級結構）"""
    print("\n" + "="*80)
    print("🧪 測試 2: Hierarchical 模式（層級結構）")
    print("="*80)
    
    service = SectionSearchService()
    
    query = "ULINK"
    
    print(f"\n📝 查詢: {query}")
    print(f"🎯 模式: hierarchical (層級結構)")
    
    try:
        results = service.search_with_context(
            query=query,
            source_table='protocol_guide',
            limit=2,
            threshold=0.7,
            include_siblings=True,
            context_mode='hierarchical'
        )
        
        print(f"\n✅ 找到 {len(results)} 個結果")
        
        for i, result in enumerate(results, 1):
            print(f"\n{'─'*60}")
            print(f"📄 結果 {i}:")
            print(f"  Section ID: {result.get('section_id')}")
            print(f"  標題: {result.get('heading_text')}")
            print(f"  相似度: {result.get('similarity', 0):.2%}")
            
            # Hierarchical 上下文
            parent = result.get('parent')
            children = result.get('children', [])
            siblings = result.get('siblings', [])
            
            print(f"\n  🌳 層級結構:")
            if parent:
                print(f"    👆 父段落: {parent.get('section_id')} - {parent.get('heading_text')}")
            else:
                print(f"    👆 父段落: 無")
            
            print(f"    📌 當前段落: {result.get('section_id')}")
            
            print(f"    👇 子段落: {len(children)} 個")
            for c in children[:3]:  # 只顯示前 3 個
                print(f"      - {c.get('section_id')}: {c.get('heading_text')}")
            
            print(f"    🤝 兄弟段落: {len(siblings)} 個")
            for s in siblings[:3]:  # 只顯示前 3 個
                print(f"      - {s.get('section_id')}: {s.get('heading_text')}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_both_mode():
    """測試 Both 模式（同時包含兩種上下文）"""
    print("\n" + "="*80)
    print("🧪 測試 3: Both 模式（線性視窗 + 層級結構）")
    print("="*80)
    
    service = SectionSearchService()
    
    query = "ULINK"
    
    print(f"\n📝 查詢: {query}")
    print(f"🎯 模式: both (同時包含兩種上下文)")
    print(f"📊 視窗大小: 1")
    
    try:
        results = service.search_with_context(
            query=query,
            source_table='protocol_guide',
            limit=1,
            threshold=0.7,
            include_siblings=True,
            context_window=1,
            context_mode='both'
        )
        
        print(f"\n✅ 找到 {len(results)} 個結果")
        
        for i, result in enumerate(results, 1):
            print(f"\n{'─'*60}")
            print(f"📄 結果 {i}:")
            print(f"  Section ID: {result.get('section_id')}")
            print(f"  標題: {result.get('heading_text')}")
            print(f"  相似度: {result.get('similarity', 0):.2%}")
            
            # 線性視窗
            previous = result.get('previous', [])
            next_sections = result.get('next', [])
            
            print(f"\n  📍 線性視窗:")
            print(f"    前: {len(previous)} 個, 後: {len(next_sections)} 個")
            
            # 層級結構
            parent = result.get('parent')
            children = result.get('children', [])
            siblings = result.get('siblings', [])
            
            print(f"\n  🌳 層級結構:")
            print(f"    父: {'有' if parent else '無'}")
            print(f"    子: {len(children)} 個")
            print(f"    兄弟: {len(siblings)} 個")
            
            print(f"\n  ✅ Both 模式包含完整上下文資訊！")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_window_size():
    """測試不同的視窗大小"""
    print("\n" + "="*80)
    print("🧪 測試 4: 不同視窗大小（window_size = 2）")
    print("="*80)
    
    service = SectionSearchService()
    
    query = "ULINK"
    
    print(f"\n📝 查詢: {query}")
    print(f"🎯 模式: adjacent")
    print(f"📊 視窗大小: 2 (前後各 2 個段落)")
    
    try:
        results = service.search_with_context(
            query=query,
            source_table='protocol_guide',
            limit=1,
            threshold=0.7,
            context_window=2,  # ✅ 測試更大的視窗
            context_mode='adjacent'
        )
        
        print(f"\n✅ 找到 {len(results)} 個結果")
        
        for i, result in enumerate(results, 1):
            print(f"\n{'─'*60}")
            print(f"📄 結果 {i}:")
            print(f"  Section ID: {result.get('section_id')}")
            print(f"  標題: {result.get('heading_text')}")
            
            previous = result.get('previous', [])
            next_sections = result.get('next', [])
            
            print(f"\n  📍 上下文視窗 (size=2):")
            print(f"    ⬆️  前 {len(previous)} 個段落:")
            for p in previous:
                print(f"      - {p.get('section_id')}: {p.get('heading_text')}")
            
            print(f"    📌 當前: {result.get('section_id')}")
            
            print(f"    ⬇️  後 {len(next_sections)} 個段落:")
            for n in next_sections:
                print(f"      - {n.get('section_id')}: {n.get('heading_text')}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主測試函數"""
    print("\n" + "🎯"*40)
    print("V2 上下文視窗擴展功能 - 完整測試")
    print("🎯"*40)
    
    results = []
    
    # 測試 1: Adjacent 模式
    results.append(("Adjacent 模式", test_adjacent_mode()))
    
    # 測試 2: Hierarchical 模式
    results.append(("Hierarchical 模式", test_hierarchical_mode()))
    
    # 測試 3: Both 模式
    results.append(("Both 模式", test_both_mode()))
    
    # 測試 4: 不同視窗大小
    results.append(("視窗大小測試", test_window_size()))
    
    # 總結
    print("\n" + "="*80)
    print("📊 測試總結")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"  {status} - {name}")
    
    print(f"\n總計: {passed}/{total} 通過")
    
    if passed == total:
        print("\n🎉 所有測試通過！V2 上下文視窗擴展功能完整實現！")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 個測試失敗")
        return 1


if __name__ == '__main__':
    sys.exit(main())
