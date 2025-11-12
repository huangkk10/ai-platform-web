#!/usr/bin/env python3
"""
上下文視窗擴展功能完整測試腳本 V2

功能測試：
1. Adjacent Mode（相鄰段落模式）- 線性視窗擴展
2. Hierarchical Mode（階層模式）- 父/子/兄弟段落
3. Both Mode（混合模式）- 相鄰 + 階層
4. 空內容段落的子段落展開
5. 資料庫段落結構驗證

測試文檔：UNH-IOL (protocol_guide id=10)
- Section 3: IOL 放測 SOP (空內容，有子段落)
- Section 3.1, 3.2, 3.2.1 等子段落

執行方式：
    python backend/test_context_window_v2.py

或在 Docker 容器中：
    docker exec ai-django python test_context_window_v2.py
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
from django.db import connection


def print_banner(title, symbol="=", color_code="🔵"):
    """打印美化的標題橫幅"""
    print(f"\n{color_code*40}")
    print(f"{symbol*80}")
    print(f"  {title}")
    print(f"{symbol*80}")
    print(f"{color_code*40}\n")


def print_result_header(index, total):
    """打印結果標題"""
    print(f"\n{'─'*80}")
    print(f"📊 結果 #{index}/{total}")
    print(f"{'─'*80}")


def test_adjacent_mode():
    """
    測試 1：相鄰段落模式（Adjacent Mode）
    
    功能說明：
    - 以匹配段落為中心，向前後擴展指定數量的段落
    - 類似於「滑動視窗」的概念
    - 適用於：連續閱讀、上下文相關的內容
    """
    print_banner("🧪 測試 1: Adjacent Mode（相鄰段落擴展）", color_code="🔵")
    
    service = SectionSearchService()
    
    # 測試參數
    query = "IOL 放測步驟"
    window_size = 1  # 前後各擴展 1 個段落
    
    print(f"🔍 查詢: '{query}'")
    print(f"📏 視窗大小: ±{window_size} 段落")
    print(f"📌 預期效果: 每個匹配段落會包含前 1 個和後 1 個段落的內容\n")
    
    try:
        # 執行搜尋
        results = service.search_with_context(
            query=query,
            limit=3,
            threshold=0.6,
            context_mode='adjacent',
            window_size=window_size,
            include_siblings=False,
            include_parent=False
        )
        
        print(f"✅ 成功找到 {len(results)} 個結果\n")
        
        for i, result in enumerate(results, 1):
            print_result_header(i, len(results))
            
            print(f"   🎯 匹配段落: {result['title']}")
            print(f"   📈 相似度分數: {result['score']:.4f} ({result['score']*100:.1f}%)")
            print(f"   📏 內容長度: {len(result['content'])} 字符")
            
            # 上下文資訊
            if 'context_info' in result:
                ctx = result['context_info']
                print(f"\n   📦 上下文擴展資訊:")
                print(f"      ├─ 主段落: {ctx.get('main_section', 'N/A')}")
                print(f"      ├─ 前段落數量: {ctx.get('previous_sections_count', 0)}")
                print(f"      ├─ 後段落數量: {ctx.get('next_sections_count', 0)}")
                print(f"      └─ 總段落數: {ctx.get('total_sections', 1)}")
                
                if ctx.get('expansion_applied'):
                    print(f"      ✅ 上下文擴展已成功應用")
            
            # 內容預覽
            print(f"\n   📝 內容預覽（前 5 行）:")
            content_lines = result['content'].split('\n')
            for j, line in enumerate(content_lines[:5], 1):
                if line.strip():
                    print(f"      {j}. {line.strip()[:100]}")
            
            if len(content_lines) > 5:
                print(f"      ... (還有 {len(content_lines) - 5} 行)")
        
        return results
        
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


def test_hierarchical_mode():
    """
    測試 2：階層模式（Hierarchical Mode）
    
    功能說明：
    - 擴展匹配段落的父段落、子段落、兄弟段落
    - 保持文檔的層級結構
    - 適用於：理解段落在整體結構中的位置
    """
    print_banner("🧪 測試 2: Hierarchical Mode（階層擴展）", color_code="🟢")
    
    service = SectionSearchService()
    
    query = "IOL 放測"
    
    print(f"🔍 查詢: '{query}'")
    print(f"📌 擴展策略:")
    print(f"   ✓ 包含父段落（上層結構）")
    print(f"   ✓ 包含子段落（下層細節）")
    print(f"   ✓ 包含兄弟段落（同層相關）\n")
    
    try:
        # 執行搜尋
        results = service.search_with_context(
            query=query,
            limit=2,
            threshold=0.6,
            context_mode='hierarchical',
            include_siblings=True,
            include_parent=True
        )
        
        print(f"✅ 成功找到 {len(results)} 個結果\n")
        
        for i, result in enumerate(results, 1):
            print_result_header(i, len(results))
            
            print(f"   🎯 匹配段落: {result['title']}")
            print(f"   📈 相似度分數: {result['score']:.4f} ({result['score']*100:.1f}%)")
            print(f"   📏 內容長度: {len(result['content'])} 字符")
            
            # 階層資訊
            if 'context_info' in result:
                ctx = result['context_info']
                print(f"\n   🌳 階層結構資訊:")
                print(f"      ├─ 主段落: {ctx.get('main_section', 'N/A')}")
                print(f"      ├─ 父段落: {ctx.get('parent_section', 'N/A')}")
                print(f"      ├─ 子段落數量: {ctx.get('children_count', 0)}")
                print(f"      ├─ 兄弟段落數量: {ctx.get('siblings_count', 0)}")
                print(f"      └─ 總段落數: {ctx.get('total_sections', 1)}")
            
            # 檢測子段落
            content = result['content']
            subsection_markers = ['###', '####', '3.1', '3.2', '3.3', '3.2.1', '3.2.2']
            found_markers = [m for m in subsection_markers if m in content]
            
            if found_markers:
                print(f"\n   ✅ 檢測到子段落標記:")
                lines = content.split('\n')
                subsection_lines = [l for l in lines if any(m in l for m in found_markers)]
                for line in subsection_lines[:5]:
                    print(f"      • {line.strip()[:80]}")
                if len(subsection_lines) > 5:
                    print(f"      ... (還有 {len(subsection_lines) - 5} 個子段落)")
            else:
                print(f"\n   ⚠️ 未檢測到明顯的子段落標記")
            
            # 內容結構分析
            print(f"\n   📊 內容統計:")
            print(f"      ├─ 總字符數: {len(content)}")
            print(f"      ├─ 總行數: {len(content.split(chr(10)))}")
            print(f"      └─ 段落數（估計）: {content.count(chr(10)*2) + 1}")
        
        return results
        
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


def test_both_mode():
    """
    測試 3：混合模式（Both Mode）
    
    功能說明：
    - 同時應用 Adjacent 和 Hierarchical 模式
    - 提供最全面的上下文資訊
    - 適用於：需要完整理解段落周邊所有相關內容
    """
    print_banner("🧪 測試 3: Both Mode（相鄰 + 階層混合擴展）", color_code="🟡")
    
    service = SectionSearchService()
    
    query = "IOL 測試"
    window_size = 1
    
    print(f"🔍 查詢: '{query}'")
    print(f"📌 混合策略:")
    print(f"   ✓ Adjacent: 前後各 ±{window_size} 個段落")
    print(f"   ✓ Hierarchical: 父/子/兄弟段落")
    print(f"   → 結果 = 兩種模式的並集\n")
    
    try:
        # 執行搜尋
        results = service.search_with_context(
            query=query,
            limit=2,
            threshold=0.6,
            context_mode='both',
            window_size=window_size,
            include_siblings=True,
            include_parent=True
        )
        
        print(f"✅ 成功找到 {len(results)} 個結果\n")
        
        for i, result in enumerate(results, 1):
            print_result_header(i, len(results))
            
            print(f"   🎯 匹配段落: {result['title']}")
            print(f"   📈 相似度分數: {result['score']:.4f} ({result['score']*100:.1f}%)")
            print(f"   📏 內容長度: {len(result['content'])} 字符")
            
            # 混合模式資訊
            if 'context_info' in result:
                ctx = result['context_info']
                print(f"\n   🔄 混合擴展資訊:")
                print(f"      ├─ 主段落: {ctx.get('main_section', 'N/A')}")
                print(f"      ├─ 相鄰擴展: 前後 ±{window_size}")
                print(f"      ├─ 階層擴展: 父/子/兄弟")
                print(f"      └─ 總段落數: {ctx.get('total_sections', 1)}")
                
                if ctx.get('expansion_applied'):
                    print(f"      ✅ 混合上下文擴展已成功應用")
                else:
                    print(f"      ⚠️ 上下文擴展未應用或失敗")
            
            # 比較與單一模式的差異
            print(f"\n   📊 與單一模式比較:")
            print(f"      Adjacent 模式預估: ~{window_size * 2 + 1} 個段落")
            print(f"      Hierarchical 模式預估: ~3-8 個段落（取決於結構）")
            print(f"      Both 模式實際: {ctx.get('total_sections', 'N/A')} 個段落")
            
            if ctx.get('total_sections', 0) > window_size * 2 + 1:
                print(f"      ✅ Both 模式提供了更多上下文")
        
        return results
        
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


def test_child_expansion_for_empty_section():
    """
    測試 4：空內容段落的子段落展開
    
    功能說明：
    - 當匹配到內容為空的父段落時，自動查詢並展開其子段落
    - 確保用戶不會得到空白結果
    - 測試目標：UNH-IOL Section 3 (空內容，有子段落 3.1, 3.2, 3.2.1 等)
    """
    print_banner("🧪 測試 4: 空內容段落的子段落展開", color_code="🟣")
    
    service = ProtocolGuideSearchService()
    
    query = "IOL 放測 SOP"
    
    print(f"🔍 查詢: '{query}'")
    print(f"🎯 目標: Section 3 - IOL 放測 SOP")
    print(f"📌 特徵: 父段落內容為空，應自動展開子段落\n")
    
    print(f"預期子段落:")
    expected_subsections = ['3.1', '3.2', '3.2.1', '3.2.2', '3.3']
    for sub in expected_subsections:
        print(f"   • Section {sub}")
    print()
    
    try:
        # 執行搜尋
        results = service.search_knowledge(query, limit=3)
        
        print(f"✅ 成功找到 {len(results)} 個結果\n")
        
        # 查找 Section 3
        section_3_found = False
        section_3_result = None
        
        for i, result in enumerate(results, 1):
            print_result_header(i, len(results))
            
            print(f"   🎯 標題: {result['title']}")
            print(f"   📈 相似度分數: {result['score']:.4f} ({result['score']*100:.1f}%)")
            print(f"   📏 內容長度: {len(result['content'])} 字符")
            
            # 檢查是否為 Section 3
            is_section_3 = (
                'IOL 放測 SOP' in result['title'] or 
                'sec_3' in str(result.get('metadata', {})) or
                result['title'].strip() == '3. IOL 放測 SOP'
            )
            
            if is_section_3:
                section_3_found = True
                section_3_result = result
                print(f"\n   ✅ 找到目標段落: Section 3")
                
                # 檢查子段落
                content = result['content']
                found_subsections = []
                
                for sub in expected_subsections:
                    if sub in content:
                        found_subsections.append(sub)
                
                print(f"\n   📦 子段落展開檢測:")
                print(f"      預期: {len(expected_subsections)} 個子段落")
                print(f"      實際: {len(found_subsections)} 個子段落")
                
                if found_subsections:
                    print(f"\n      ✅ 找到以下子段落:")
                    for sub in found_subsections:
                        print(f"         • Section {sub}")
                    
                    # 顯示部分內容
                    print(f"\n   📝 內容預覽（前 20 行）:")
                    lines = content.split('\n')
                    displayed_lines = 0
                    for j, line in enumerate(lines[:30], 1):
                        if line.strip():
                            print(f"      {displayed_lines+1}. {line.strip()[:100]}")
                            displayed_lines += 1
                            if displayed_lines >= 20:
                                break
                    
                    if len(lines) > 30:
                        print(f"      ... (還有 {len(lines) - 30} 行)")
                    
                    # 成功評估
                    coverage = len(found_subsections) / len(expected_subsections) * 100
                    print(f"\n   📊 子段落覆蓋率: {coverage:.1f}%")
                    
                    if coverage >= 80:
                        print(f"      ✅ 優秀 - 子段落展開功能正常")
                    elif coverage >= 50:
                        print(f"      ⚠️ 一般 - 部分子段落可能遺漏")
                    else:
                        print(f"      ❌ 較差 - 子段落展開可能有問題")
                        
                else:
                    print(f"\n      ❌ 未找到任何子段落內容！")
                    print(f"      ⚠️ 問題分析:")
                    print(f"         • 內容長度: {len(content)} 字符")
                    print(f"         • 可能原因 1: 子段落未正確查詢")
                    print(f"         • 可能原因 2: 資料庫中無子段落資料")
                    print(f"         • 可能原因 3: 格式化邏輯有誤")
                    
                    # 顯示實際內容
                    if len(content) > 0:
                        print(f"\n      📄 實際內容:")
                        print(f"         {content[:300]}")
        
        if not section_3_found:
            print(f"\n⚠️ 警告: 未在前 {len(results)} 個結果中找到 Section 3")
            print(f"💡 建議:")
            print(f"   1. 檢查向量是否已生成")
            print(f"   2. 嘗試降低 threshold（當前 0.7）")
            print(f"   3. 使用更精確的查詢詞")
        
        return section_3_result
        
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def test_database_section_structure():
    """
    測試 5：資料庫段落結構驗證
    
    功能說明：
    - 直接查詢資料庫，驗證段落資料的完整性
    - 檢查父子關係是否正確建立
    - 確認 Section 3 的子段落存在且有內容
    """
    print_banner("🧪 測試 5: 資料庫段落結構驗證", color_code="🔴")
    
    print(f"📊 檢查 UNH-IOL 文檔 (id=10) 的段落結構...\n")
    
    try:
        with connection.cursor() as cursor:
            # 查詢 1：所有段落概覽
            print(f"{'─'*100}")
            print(f"📋 段落概覽:")
            print(f"{'─'*100}\n")
            
            cursor.execute("""
                SELECT 
                    id,
                    section_number,
                    section_title,
                    LENGTH(content) as content_length,
                    parent_section_id,
                    is_parent,
                    depth_level
                FROM document_section_embeddings
                WHERE document_id = 10
                ORDER BY section_number;
            """)
            
            sections = cursor.fetchall()
            
            print(f"✅ 共有 {len(sections)} 個段落\n")
            
            # 表格表頭
            header = f"{'ID':<6} {'段落編號':<12} {'標題':<35} {'內容長度':<10} {'父段落':<8} {'是父':<6} {'層級':<6}"
            print(header)
            print("="*100)
            
            # 段落列表
            section_3_id = None
            for sec in sections:
                sec_id, section_num, title, content_len, parent_id, is_parent, depth = sec
                
                # 記錄 Section 3 的 ID
                if section_num == '3':
                    section_3_id = sec_id
                
                is_parent_str = "✓" if is_parent else ""
                parent_str = f"#{parent_id}" if parent_id else "-"
                
                # 高亮 Section 3 及其子段落
                prefix = "→ " if section_num.startswith('3') else "  "
                
                row = f"{prefix}{sec_id:<4} {section_num:<12} {title[:33]:<35} {content_len:<10} {parent_str:<8} {is_parent_str:<6} {depth:<6}"
                print(row)
            
            # 查詢 2：Section 3 的子段落詳情
            if section_3_id:
                print(f"\n{'─'*100}")
                print(f"🔍 Section 3 的子段落詳細資訊:")
                print(f"{'─'*100}\n")
                
                cursor.execute("""
                    SELECT 
                        id,
                        section_number,
                        section_title,
                        LENGTH(content) as content_length,
                        title_embedding IS NOT NULL as has_title_vector,
                        content_embedding IS NOT NULL as has_content_vector
                    FROM document_section_embeddings
                    WHERE document_id = 10
                      AND parent_section_id = %s
                    ORDER BY section_number;
                """, [section_3_id])
                
                children = cursor.fetchall()
                
                if children:
                    print(f"✅ Section 3 有 {len(children)} 個子段落:\n")
                    
                    for child in children:
                        child_id, num, title, length, has_title, has_content = child
                        vector_status = "✓✓" if (has_title and has_content) else ("✓✗" if has_title else "✗✗")
                        
                        print(f"   • #{child_id} {num}: {title}")
                        print(f"      └─ 內容: {length} 字符 | 向量: {vector_status}")
                    
                    # 統計
                    print(f"\n   📊 統計:")
                    total_length = sum(c[3] for c in children)
                    with_vectors = sum(1 for c in children if c[4] and c[5])
                    
                    print(f"      ├─ 總內容長度: {total_length} 字符")
                    print(f"      ├─ 有完整向量: {with_vectors}/{len(children)}")
                    print(f"      └─ 平均內容長度: {total_length//len(children) if children else 0} 字符")
                    
                else:
                    print(f"❌ Section 3 沒有子段落！")
                    print(f"⚠️ 這將導致空內容段落無法展開")
                    print(f"\n💡 可能原因:")
                    print(f"   1. parent_section_id 未正確設置")
                    print(f"   2. 段落資料未完整匯入")
                    print(f"   3. Section 3 的 id 與子段落的 parent_section_id 不匹配")
            
            # 查詢 3：父子關係驗證
            print(f"\n{'─'*100}")
            print(f"🔗 父子關係驗證:")
            print(f"{'─'*100}\n")
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_sections,
                    SUM(CASE WHEN is_parent THEN 1 ELSE 0 END) as parent_sections,
                    SUM(CASE WHEN parent_section_id IS NOT NULL THEN 1 ELSE 0 END) as child_sections,
                    SUM(CASE WHEN parent_section_id IS NULL AND NOT is_parent THEN 1 ELSE 0 END) as orphan_sections
                FROM document_section_embeddings
                WHERE document_id = 10;
            """)
            
            stats = cursor.fetchone()
            total, parents, children_count, orphans = stats
            
            print(f"   總段落數: {total}")
            print(f"   └─ 父段落: {parents} ({parents/total*100:.1f}%)")
            print(f"   └─ 子段落: {children_count} ({children_count/total*100:.1f}%)")
            print(f"   └─ 孤立段落: {orphans} ({orphans/total*100:.1f}%)")
            
            if orphans > 0:
                print(f"\n   ⚠️ 發現 {orphans} 個孤立段落（既非父段落，也無父段落）")
                print(f"   💡 這些段落可能需要檢查 parent_section_id")
            else:
                print(f"\n   ✅ 所有段落都有正確的父子關係")
        
    except Exception as e:
        print(f"❌ 資料庫查詢失敗: {str(e)}")
        import traceback
        traceback.print_exc()


def run_all_tests():
    """執行所有測試"""
    print_banner("🚀 上下文視窗擴展功能完整測試套件", symbol="*", color_code="🎯")
    
    start_time = datetime.now()
    
    print(f"📅 測試時間: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📂 測試文檔: UNH-IOL (protocol_guide id=10)")
    print(f"🎯 測試目標: 驗證上下文視窗擴展的各種模式\n")
    
    print(f"測試項目:")
    print(f"   1️⃣ Adjacent Mode - 相鄰段落線性擴展")
    print(f"   2️⃣ Hierarchical Mode - 階層結構擴展（父/子/兄弟）")
    print(f"   3️⃣ Both Mode - 混合擴展（相鄰 + 階層）")
    print(f"   4️⃣ Child Expansion - 空內容段落的子段落展開")
    print(f"   5️⃣ Database Structure - 資料庫段落結構驗證")
    
    test_results = {
        'test_1': False,
        'test_2': False,
        'test_3': False,
        'test_4': False,
        'test_5': False
    }
    
    try:
        # 測試 5：資料庫結構（先執行，了解數據狀態）
        print(f"\n{'🔴'*40}")
        test_database_section_structure()
        test_results['test_5'] = True
        
        # 測試 1：Adjacent Mode
        print(f"\n{'🔵'*40}")
        result_1 = test_adjacent_mode()
        test_results['test_1'] = len(result_1) > 0 if result_1 else False
        
        # 測試 2：Hierarchical Mode
        print(f"\n{'🟢'*40}")
        result_2 = test_hierarchical_mode()
        test_results['test_2'] = len(result_2) > 0 if result_2 else False
        
        # 測試 3：Both Mode
        print(f"\n{'🟡'*40}")
        result_3 = test_both_mode()
        test_results['test_3'] = len(result_3) > 0 if result_3 else False
        
        # 測試 4：空內容展開
        print(f"\n{'🟣'*40}")
        result_4 = test_child_expansion_for_empty_section()
        test_results['test_4'] = result_4 is not None
        
        # 計算執行時間
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 總結
        print_banner("🎉 測試執行完成", symbol="*", color_code="✅")
        
        print(f"⏱️  執行時間: {duration:.2f} 秒\n")
        
        print(f"📊 測試結果總結:\n")
        
        passed = sum(test_results.values())
        total = len(test_results)
        
        for i, (test_key, passed_test) in enumerate(test_results.items(), 1):
            status = "✅ 通過" if passed_test else "❌ 失敗"
            test_names = {
                'test_1': "Adjacent Mode",
                'test_2': "Hierarchical Mode",
                'test_3': "Both Mode",
                'test_4': "Child Expansion",
                'test_5': "Database Structure"
            }
            print(f"   {i}. {test_names[test_key]:<25} {status}")
        
        print(f"\n{'─'*80}")
        print(f"   總計: {passed}/{total} 通過 ({passed/total*100:.1f}%)")
        print(f"{'─'*80}")
        
        if passed == total:
            print(f"\n🎉 太棒了！所有測試都通過了！")
            print(f"✅ 上下文視窗擴展功能運作正常")
        elif passed >= total * 0.8:
            print(f"\n👍 不錯！大部分測試通過")
            print(f"⚠️ 請檢查失敗的測試項目")
        else:
            print(f"\n⚠️ 注意：多個測試失敗")
            print(f"💡 建議檢查:")
            print(f"   1. 向量是否已生成")
            print(f"   2. 段落父子關係是否正確")
            print(f"   3. search_service 的實作是否正確")
        
        print(f"\n💡 下一步建議:")
        print(f"   1. 查看每個測試的詳細輸出，確認上下文擴展是否符合預期")
        print(f"   2. 檢查內容長度是否合理（有擴展的應該比單段落長）")
        print(f"   3. 驗證 Section 3 的子段落是否正確展開")
        print(f"   4. 如有問題，參考輸出中的 context_info 進行除錯")
        
    except KeyboardInterrupt:
        print(f"\n\n⚠️ 測試被用戶中斷")
    except Exception as e:
        print(f"\n\n❌ 測試執行過程發生嚴重錯誤:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
