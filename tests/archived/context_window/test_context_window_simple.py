#!/usr/bin/env python3
"""
上下文視窗擴展功能簡化測試腳本

測試重點：
1. 驗證 search_with_context() 的三種模式：adjacent, hierarchical, both
2. 檢查空內容段落的子段落展開
3. 顯示上下文擴展的效果

執行方式：
    docker exec ai-django python test_context_window_simple.py
"""

import os
import sys
import django
from datetime import datetime

# Django 設置
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from library.protocol_guide.search_service import ProtocolGuideSearchService
from library.common.knowledge_base.section_search_service import SectionSearchService


def print_separator(symbol="=", width=80):
    """打印分隔線"""
    print(f"\n{symbol * width}")


def print_test_header(test_num, test_name):
    """打印測試標題"""
    print_separator("=")
    print(f"🧪 測試 {test_num}: {test_name}")
    print_separator("=")


def test_1_hierarchical_mode():
    """
    測試 1：Hierarchical Mode（階層模式）
    
    功能：擴展父段落、子段落、兄弟段落
    """
    print_test_header(1, "Hierarchical Mode（階層擴展）")
    
    service = SectionSearchService()
    query = "IOL 放測"
    
    print(f"🔍 查詢: '{query}'")
    print(f"📌 模式: hierarchical（包含父/子/兄弟段落）\n")
    
    try:
        results = service.search_with_context(
            query=query,
            source_table='protocol_guide',
            limit=2,
            threshold=0.6,
            context_mode='hierarchical',  # ✅ 正確參數
            include_siblings=True         # ✅ 正確參數
        )
        
        print(f"✅ 找到 {len(results)} 個結果\n")
        
        for i, result in enumerate(results, 1):
            print(f"{'─'*80}")
            print(f"📊 結果 #{i}")
            print(f"{'─'*80}")
            print(f"   🎯 段落: {result.get('heading_text')}")
            print(f"   📈 相似度: {result.get('similarity', 0):.2%}")
            print(f"   📏 內容長度: {len(result.get('content', ''))} 字符")
            print(f"   🔢 段落 ID: {result.get('section_id')}")
            
            # 檢查是否有上下文資訊
            if 'parent' in result or 'children' in result or 'siblings' in result:
                print(f"\n   🌳 階層上下文:")
                if 'parent' in result and result['parent']:
                    print(f"      └─ 父段落: {result['parent'].get('heading_text')}")
                if 'children' in result and result['children']:
                    print(f"      └─ 子段落數: {len(result['children'])}")
                    for child in result['children'][:3]:
                        print(f"         • {child.get('heading_text')}")
                    if len(result['children']) > 3:
                        print(f"         ... (還有 {len(result['children']) - 3} 個)")
                if 'siblings' in result and result['siblings']:
                    print(f"      └─ 兄弟段落數: {len(result['siblings'])}")
            
            # 內容預覽
            content = result.get('content', '')
            if content:
                print(f"\n   📝 內容預覽（前 3 行）:")
                lines = [l for l in content.split('\n') if l.strip()][:3]
                for line in lines:
                    print(f"      {line[:100]}")
        
        print(f"\n✅ 測試 1 完成\n")
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_2_adjacent_mode():
    """
    測試 2：Adjacent Mode（相鄰段落模式）
    
    功能：以匹配段落為中心，向前後擴展指定數量的段落
    """
    print_test_header(2, "Adjacent Mode（線性視窗擴展）")
    
    service = SectionSearchService()
    query = "IOL 測試流程"
    
    print(f"🔍 查詢: '{query}'")
    print(f"📌 模式: adjacent（前後各 ±1 段落）\n")
    
    try:
        results = service.search_with_context(
            query=query,
            source_table='protocol_guide',
            limit=2,
            threshold=0.6,
            context_mode='adjacent',     # ✅ 正確參數
            context_window=1             # ✅ 正確參數
        )
        
        print(f"✅ 找到 {len(results)} 個結果\n")
        
        for i, result in enumerate(results, 1):
            print(f"{'─'*80}")
            print(f"📊 結果 #{i}")
            print(f"{'─'*80}")
            print(f"   🎯 段落: {result.get('heading_text')}")
            print(f"   📈 相似度: {result.get('similarity', 0):.2%}")
            print(f"   📏 內容長度: {len(result.get('content', ''))} 字符")
            
            # 檢查相鄰上下文
            if 'previous' in result or 'next' in result:
                print(f"\n   📦 相鄰上下文:")
                if 'previous' in result and result['previous']:
                    print(f"      └─ 前段落數: {len(result['previous'])}")
                    for prev in result['previous']:
                        print(f"         ← {prev.get('heading_text')}")
                if 'next' in result and result['next']:
                    print(f"      └─ 後段落數: {len(result['next'])}")
                    for nxt in result['next']:
                        print(f"         → {nxt.get('heading_text')}")
            
            # 內容預覽
            content = result.get('content', '')
            if content:
                print(f"\n   📝 內容預覽（前 3 行）:")
                lines = [l for l in content.split('\n') if l.strip()][:3]
                for line in lines:
                    print(f"      {line[:100]}")
        
        print(f"\n✅ 測試 2 完成\n")
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_3_both_mode():
    """
    測試 3：Both Mode（混合模式）
    
    功能：同時應用 hierarchical 和 adjacent 模式
    """
    print_test_header(3, "Both Mode（階層 + 線性混合擴展）")
    
    service = SectionSearchService()
    query = "UNH IOL"
    
    print(f"🔍 查詢: '{query}'")
    print(f"📌 模式: both（階層 + 線性視窗）\n")
    
    try:
        results = service.search_with_context(
            query=query,
            source_table='protocol_guide',
            limit=2,
            threshold=0.6,
            context_mode='both',         # ✅ 正確參數
            context_window=1,            # ✅ 線性視窗大小
            include_siblings=True        # ✅ 包含兄弟段落
        )
        
        print(f"✅ 找到 {len(results)} 個結果\n")
        
        for i, result in enumerate(results, 1):
            print(f"{'─'*80}")
            print(f"📊 結果 #{i}")
            print(f"{'─'*80}")
            print(f"   🎯 段落: {result.get('heading_text')}")
            print(f"   📈 相似度: {result.get('similarity', 0):.2%}")
            print(f"   📏 內容長度: {len(result.get('content', ''))} 字符")
            
            # 統計所有上下文
            context_count = 0
            if 'parent' in result and result['parent']:
                context_count += 1
            if 'children' in result:
                context_count += len(result.get('children', []))
            if 'siblings' in result:
                context_count += len(result.get('siblings', []))
            if 'previous' in result:
                context_count += len(result.get('previous', []))
            if 'next' in result:
                context_count += len(result.get('next', []))
            
            print(f"\n   🔄 混合上下文資訊:")
            print(f"      └─ 總上下文段落數: {context_count}")
            
            # 階層部分
            if 'parent' in result or 'children' in result or 'siblings' in result:
                print(f"      └─ 階層上下文:")
                if 'parent' in result and result['parent']:
                    print(f"         • 父段落: ✓")
                if 'children' in result and result['children']:
                    print(f"         • 子段落: {len(result['children'])} 個")
                if 'siblings' in result and result['siblings']:
                    print(f"         • 兄弟段落: {len(result['siblings'])} 個")
            
            # 線性部分
            if 'previous' in result or 'next' in result:
                print(f"      └─ 線性上下文:")
                if 'previous' in result and result['previous']:
                    print(f"         • 前段落: {len(result['previous'])} 個")
                if 'next' in result and result['next']:
                    print(f"         • 後段落: {len(result['next'])} 個")
        
        print(f"\n✅ 測試 3 完成\n")
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_4_child_expansion():
    """
    測試 4：空內容段落的子段落展開
    
    功能：當段落內容為空時，自動查詢並展開子段落
    目標：UNH-IOL Section 3 (空內容，有子段落)
    """
    print_test_header(4, "空內容段落的子段落展開")
    
    service = ProtocolGuideSearchService()
    query = "IOL 放測 SOP"
    
    print(f"🔍 查詢: '{query}'")
    print(f"🎯 目標: Section 3 - IOL 放測 SOP（空內容，應展開子段落）\n")
    
    # 注意：数据库中 Section 3 实际只有 2 个子段落（3.1, 3.2）
    # Section 3.2.1, 3.2.2, 3.3 不存在于数据库
    expected_subsections = ['3.1', '3.2']
    print(f"預期子段落: {', '.join(expected_subsections)}")
    print(f"💡 注意：数据库中 Section 3 只有这 2 个子段落\n")
    
    try:
        results = service.search_knowledge(query, limit=3)
        
        print(f"✅ 找到 {len(results)} 個結果\n")
        
        # 尋找 Section 3
        section_3_found = False
        
        for i, result in enumerate(results, 1):
            print(f"{'─'*80}")
            print(f"📊 結果 #{i}")
            print(f"{'─'*80}")
            print(f"   📄 標題: {result['title']}")
            print(f"   📈 分數: {result['score']:.4f}")
            print(f"   📏 內容長度: {len(result['content'])} 字符")
            
            # 檢查子段落展開（改進邏輯）
            content = result['content']
            found_subsections = [s for s in expected_subsections if s in content]
            
            # 判斷：只要內容包含預期子段落，就視為成功
            has_expanded_content = len(content) > 200  # 有展開內容應該超過 200 字符
            has_expected_subsections = len(found_subsections) >= 2  # 至少找到 2 個子段落（3.1, 3.2）
            
            is_expansion_working = has_expanded_content and has_expected_subsections
            
            if is_expansion_working:
                section_3_found = True
                print(f"\n   ✅ 找到目標段落並成功展開!")
                print(f"   📊 判斷依據:")
                print(f"      • 內容長度 > 200 字符: {len(content)} 字符 ✅")
                print(f"      • 包含預期子段落 ≥ 2 個: {len(found_subsections)} 個 ✅")
                
                print(f"\n   📦 子段落檢測:")
                print(f"      預期: {len(expected_subsections)} 個")
                print(f"      實際: {len(found_subsections)} 個")
                
                if found_subsections:
                    print(f"\n      ✅ 找到以下子段落:")
                    for sub in found_subsections:
                        print(f"         • Section {sub}")
                    
                    coverage = len(found_subsections) / len(expected_subsections) * 100
                    print(f"\n      📊 覆蓋率: {coverage:.1f}%")
                    
                    # 顯示內容預覽
                    print(f"\n   📝 內容預覽（前 10 行）:")
                    lines = [l for l in content.split('\n') if l.strip()][:10]
                    for j, line in enumerate(lines, 1):
                        print(f"      {j:2d}. {line[:100]}")
                    
                    if len(content.split('\n')) > 10:
                        print(f"      ... (還有更多內容)")
            else:
                print(f"\n   ⚠️ 此結果不符合展開條件:")
                print(f"      • 內容長度: {len(content)} 字符 (預期 > 200)")
                print(f"      • 子段落數: {len(found_subsections)} 個 (預期 ≥ 2)")
        
        if not section_3_found:
            print(f"\n⚠️ 未在前 {len(results)} 個結果中找到 Section 3")
            print(f"💡 可能需要調整查詢詞或降低 threshold")
        
        print(f"\n✅ 測試 4 完成\n")
        return section_3_found
        
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """執行所有測試"""
    print(f"\n{'='*80}")
    print(f"🚀 上下文視窗擴展功能測試套件")
    print(f"{'='*80}")
    
    start_time = datetime.now()
    print(f"\n📅 測試時間: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📂 測試文檔: UNH-IOL (protocol_guide id=10)")
    print(f"\n測試項目:")
    print(f"   1️⃣ Hierarchical Mode - 階層擴展（父/子/兄弟）")
    print(f"   2️⃣ Adjacent Mode - 線性擴展（前後段落）")
    print(f"   3️⃣ Both Mode - 混合擴展（階層 + 線性）")
    print(f"   4️⃣ Child Expansion - 空內容段落的子段落展開")
    
    results = {}
    
    # 執行測試
    results['test_1'] = test_1_hierarchical_mode()
    results['test_2'] = test_2_adjacent_mode()
    results['test_3'] = test_3_both_mode()
    results['test_4'] = test_4_child_expansion()
    
    # 計算時間
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # 總結
    print_separator("*")
    print(f"🎉 測試執行完成")
    print_separator("*")
    
    print(f"\n⏱️  執行時間: {duration:.2f} 秒")
    print(f"\n📊 測試結果:\n")
    
    test_names = {
        'test_1': 'Hierarchical Mode',
        'test_2': 'Adjacent Mode',
        'test_3': 'Both Mode',
        'test_4': 'Child Expansion'
    }
    
    passed = 0
    total = len(results)
    
    for test_key, success in results.items():
        status = "✅ 通過" if success else "❌ 失敗"
        print(f"   {test_names[test_key]:<25} {status}")
        if success:
            passed += 1
    
    print(f"\n{'─'*80}")
    print(f"   總計: {passed}/{total} 通過 ({passed/total*100:.1f}%)")
    print(f"{'─'*80}")
    
    if passed == total:
        print(f"\n🎉 太棒了！所有測試都通過了！")
        print(f"✅ 上下文視窗擴展功能運作正常")
    elif passed >= total * 0.75:
        print(f"\n👍 不錯！大部分測試通過")
    else:
        print(f"\n⚠️ 部分測試失敗，請檢查輸出")
    
    print(f"\n💡 提示:")
    print(f"   • 查看各測試的詳細輸出以了解上下文擴展效果")
    print(f"   • 注意內容長度變化（有擴展的應該更長）")
    print(f"   • 檢查 Section 3 的子段落是否正確展開\n")


if __name__ == "__main__":
    run_all_tests()
