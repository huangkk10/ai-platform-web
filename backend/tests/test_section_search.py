"""
測試段落搜尋功能

驗證新的 Chunking 系統的搜尋效果。
"""

import os
import django

# Django 設置
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from library.common.knowledge_base.section_search_service import SectionSearchService


def test_search_sections():
    """測試段落搜尋功能"""
    
    service = SectionSearchService()
    
    # 測試查詢列表
    test_queries = [
        {
            'query': 'ULINK 連接失敗怎麼辦',
            'description': '精確問題查詢'
        },
        {
            'query': '如何準備測試環境',
            'description': '一般性查詢'
        },
        {
            'query': 'Samsung Protocol 測試',
            'description': '特定品牌查詢'
        },
        {
            'query': '效能優化',
            'description': '主題查詢'
        },
        {
            'query': '錯誤碼',
            'description': '關鍵字查詢'
        }
    ]
    
    print("\n" + "="*80)
    print("🔍 段落搜尋測試 (Chunking 系統)")
    print("="*80 + "\n")
    
    for test in test_queries:
        query = test['query']
        description = test['description']
        
        print(f"\n📝 測試查詢: \"{query}\" ({description})")
        print("-" * 80)
        
        # 執行搜尋
        results = service.search_sections(
            query=query,
            source_table='protocol_guide',
            limit=3,
            threshold=0.5
        )
        
        if results:
            print(f"✅ 找到 {len(results)} 個相關段落:\n")
            
            for i, result in enumerate(results, 1):
                print(f"{i}. [{result['section_id']}] {result['heading_text']}")
                print(f"   相似度: {result['similarity']:.2%}")
                print(f"   路徑: {result['section_path']}")
                print(f"   內容長度: {result['word_count']} 字元")
                
                # 顯示內容預覽
                content_preview = result['content'][:100].replace('\n', ' ')
                print(f"   內容預覽: {content_preview}...")
                print()
        else:
            print("❌ 未找到相關段落\n")


def test_level_filtering():
    """測試層級過濾功能"""
    
    service = SectionSearchService()
    
    print("\n" + "="*80)
    print("📊 層級過濾測試")
    print("="*80 + "\n")
    
    query = "測試"
    
    # 測試不同層級
    levels = [
        (1, 1, "只搜尋 H1 (章節)"),
        (2, 2, "只搜尋 H2 (小節)"),
        (3, 3, "只搜尋 H3 (子節)"),
        (None, None, "搜尋所有層級")
    ]
    
    for min_level, max_level, description in levels:
        print(f"\n🎯 {description}")
        print("-" * 80)
        
        results = service.search_sections(
            query=query,
            source_table='protocol_guide',
            min_level=min_level,
            max_level=max_level,
            limit=5,
            threshold=0.5
        )
        
        print(f"找到 {len(results)} 個段落:")
        for result in results[:3]:  # 只顯示前 3 個
            level_mark = '#' * result['heading_level']
            print(f"  {level_mark} {result['heading_text']} (相似度: {result['similarity']:.2%})")


def test_search_with_context():
    """測試包含上下文的搜尋"""
    
    service = SectionSearchService()
    
    print("\n" + "="*80)
    print("🌳 上下文搜尋測試")
    print("="*80 + "\n")
    
    query = "ULINK 連接"
    
    print(f"查詢: \"{query}\"")
    print("-" * 80)
    
    results = service.search_with_context(
        query=query,
        source_table='protocol_guide',
        limit=2,
        include_siblings=True
    )
    
    if results:
        for i, result in enumerate(results, 1):
            print(f"\n{i}. 主要段落: {result['heading_text']}")
            print(f"   相似度: {result['similarity']:.2%}")
            
            # 顯示父段落
            if result.get('parent'):
                parent = result['parent']
                print(f"\n   📂 父段落: {parent['heading_text']}")
                print(f"      內容: {parent['content'][:60]}...")
            
            # 顯示子段落
            if result.get('children'):
                print(f"\n   📄 子段落 ({len(result['children'])} 個):")
                for child in result['children'][:2]:
                    print(f"      - {child['heading_text']}")
            
            # 顯示兄弟段落
            if result.get('siblings'):
                print(f"\n   🔗 兄弟段落 ({len(result['siblings'])} 個):")
                for sibling in result['siblings'][:2]:
                    print(f"      - {sibling['heading_text']}")
    else:
        print("❌ 未找到相關段落")


def compare_old_vs_new_system():
    """對比新舊系統的搜尋結果"""
    
    from django.db import connection
    from api.services.embedding_service import get_embedding_service
    
    embedding_service = get_embedding_service('ultra_high')
    section_service = SectionSearchService()
    
    print("\n" + "="*80)
    print("⚖️  新舊系統對比測試")
    print("="*80 + "\n")
    
    test_query = "ULINK 測試環境準備"
    
    print(f"測試查詢: \"{test_query}\"\n")
    
    # 舊系統：搜尋整篇文檔
    print("📕 舊系統 (整篇文檔):")
    print("-" * 80)
    
    query_embedding = embedding_service.generate_embedding(test_query)
    embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                source_id,
                text_content,
                1 - (embedding <=> %s::vector) as similarity
            FROM document_embeddings
            WHERE source_table = 'protocol_guide'
              AND (1 - (embedding <=> %s::vector)) >= 0.5
            ORDER BY embedding <=> %s::vector
            LIMIT 3;
        """, [embedding_str, embedding_str, embedding_str])
        
        old_results = cursor.fetchall()
    
    if old_results:
        for i, (source_id, content, similarity) in enumerate(old_results, 1):
            print(f"{i}. 文檔 ID: {source_id}")
            print(f"   相似度: {similarity:.2%}")
            print(f"   內容長度: {len(content)} 字元")
            print(f"   內容預覽: {content[:100]}...")
            print()
    else:
        print("❌ 未找到結果\n")
    
    # 新系統：搜尋段落
    print("\n📗 新系統 (段落級別):")
    print("-" * 80)
    
    new_results = section_service.search_sections(
        query=test_query,
        source_table='protocol_guide',
        limit=3,
        threshold=0.5
    )
    
    if new_results:
        for i, result in enumerate(new_results, 1):
            print(f"{i}. [{result['section_id']}] {result['heading_text']}")
            print(f"   相似度: {result['similarity']:.2%}")
            print(f"   路徑: {result['section_path']}")
            print(f"   內容長度: {result['word_count']} 字元")
            print(f"   內容預覽: {result['content'][:100]}...")
            print()
    else:
        print("❌ 未找到結果\n")
    
    # 對比分析
    print("\n" + "="*80)
    print("📊 對比分析")
    print("="*80)
    
    if old_results and new_results:
        old_avg_length = sum(len(r[1]) for r in old_results) / len(old_results)
        new_avg_length = sum(r['word_count'] for r in new_results) / len(new_results)
        
        old_avg_similarity = sum(r[2] for r in old_results) / len(old_results)
        new_avg_similarity = sum(r['similarity'] for r in new_results) / len(new_results)
        
        print(f"\n平均內容長度:")
        print(f"  舊系統: {old_avg_length:.0f} 字元")
        print(f"  新系統: {new_avg_length:.0f} 字元")
        print(f"  減少: {(1 - new_avg_length/old_avg_length)*100:.1f}%")
        
        print(f"\n平均相似度:")
        print(f"  舊系統: {old_avg_similarity:.2%}")
        print(f"  新系統: {new_avg_similarity:.2%}")
        print(f"  提升: {(new_avg_similarity - old_avg_similarity)*100:.1f}%")


if __name__ == "__main__":
    print("\n🧪 開始測試段落搜尋功能...\n")
    
    try:
        # 基本搜尋測試
        test_search_sections()
        
        # 層級過濾測試
        test_level_filtering()
        
        # 上下文搜尋測試
        test_search_with_context()
        
        # 新舊系統對比
        compare_old_vs_new_system()
        
        print("\n" + "="*80)
        print("✅ 所有測試完成！")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {str(e)}\n")
        import traceback
        traceback.print_exc()
