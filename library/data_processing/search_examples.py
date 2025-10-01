"""
資料庫搜索服務使用範例
展示如何在不同場景下使用新的搜索功能
"""

from library.data_processing.database_search import DatabaseSearchService


def example_basic_search():
    """基本搜索範例"""
    print("=== 基本搜索範例 ===")
    
    # 1. 搜索 Know Issue
    print("\n1. Know Issue 搜索:")
    results = DatabaseSearchService.search_know_issue_knowledge("Protocol", limit=3)
    for result in results:
        print(f"  - {result['title']} (分數: {result['score']})")
        print(f"    來源: {result['metadata']['source']}")
    
    # 2. 搜索 RVT Guide
    print("\n2. RVT Guide 搜索:")
    results = DatabaseSearchService.search_rvt_guide_knowledge("usage", limit=3)
    for result in results:
        print(f"  - {result['title']} (分數: {result['score']})")
        print(f"    分類: {result['metadata']['main_category']}")
    
    # 3. 搜索 OCR Storage Benchmark
    print("\n3. OCR Storage Benchmark 搜索:")
    results = DatabaseSearchService.search_ocr_storage_benchmark("Samsung", limit=3)
    for result in results:
        print(f"  - {result['title']} (分數: {result['score']})")
        print(f"    設備: {result['metadata']['device_model']}")


def example_comprehensive_search():
    """綜合搜索範例"""
    print("\n=== 綜合搜索範例 ===")
    
    # 同時搜索所有知識庫
    all_results = DatabaseSearchService.search_all_knowledge_bases("test", limit_per_type=2)
    
    print(f"\n搜索 'test' 的綜合結果:")
    for knowledge_type, results in all_results.items():
        print(f"\n📂 {knowledge_type.upper()}:")
        for result in results:
            print(f"  - {result['title']} (分數: {result['score']})")


def example_api_integration():
    """API 整合範例"""
    print("\n=== API 整合範例 ===")
    
    # 模擬 Dify API 調用的搜索邏輯
    def mock_dify_search(knowledge_id, query, top_k=5, score_threshold=0.5):
        """模擬 Dify 知識庫搜索"""
        
        if knowledge_id in ['know_issue_db', 'know_issue']:
            results = DatabaseSearchService.search_know_issue_knowledge(query, limit=top_k)
        elif knowledge_id in ['rvt_guide_db', 'rvt_guide']:
            results = DatabaseSearchService.search_rvt_guide_knowledge(query, limit=top_k)
        elif knowledge_id in ['ocr_benchmark', 'storage_benchmark']:
            results = DatabaseSearchService.search_ocr_storage_benchmark(query, limit=top_k)
        else:
            results = []
        
        # 過濾低分結果
        filtered_results = [r for r in results if r['score'] >= score_threshold]
        
        # 轉換為 Dify 格式
        records = []
        for result in filtered_results:
            record = {
                'content': result['content'],
                'score': result['score'],
                'title': result['title'],
                'metadata': result['metadata']
            }
            records.append(record)
        
        return {'records': records}
    
    # 測試不同的知識庫搜索
    test_cases = [
        ('know_issue_db', 'Protocol', 3, 0.5),
        ('rvt_guide_db', 'usage', 3, 0.6),
        ('ocr_benchmark', 'Samsung', 3, 0.5)
    ]
    
    for knowledge_id, query, top_k, threshold in test_cases:
        print(f"\n🔍 搜索 {knowledge_id}: '{query}'")
        result = mock_dify_search(knowledge_id, query, top_k, threshold)
        print(f"   找到 {len(result['records'])} 個符合條件的結果 (閾值: {threshold})")
        
        for i, record in enumerate(result['records'], 1):
            print(f"   {i}. {record['title']} (分數: {record['score']})")


def example_backward_compatibility():
    """向後相容範例"""
    print("\n=== 向後相容範例 ===")
    
    # 使用舊的函數名稱
    from library.data_processing.database_search import (
        search_know_issue_knowledge,
        search_rvt_guide_knowledge,
        search_ocr_storage_benchmark
    )
    
    print("\n使用舊的函數名稱:")
    
    # 這些函數調用與之前完全相同
    results1 = search_know_issue_knowledge("Protocol", 2)
    results2 = search_rvt_guide_knowledge("usage", 2)
    results3 = search_ocr_storage_benchmark("Samsung", 2)
    
    print(f"  search_know_issue_knowledge: {len(results1)} 個結果")
    print(f"  search_rvt_guide_knowledge: {len(results2)} 個結果")
    print(f"  search_ocr_storage_benchmark: {len(results3)} 個結果")
    
    print("\n✅ 舊代碼無需修改即可使用新的 library!")


if __name__ == "__main__":
    """
    使用說明:
    
    在 Django 環境中運行此範例:
    python manage.py shell
    >>> exec(open('search_examples.py').read())
    """
    
    try:
        example_basic_search()
        example_comprehensive_search()
        example_api_integration()
        example_backward_compatibility()
        
        print("\n" + "="*50)
        print("🎉 所有範例執行完成!")
        print("="*50)
        
    except ImportError as e:
        print(f"❌ 導入錯誤: {e}")
        print("請確保在 Django 環境中運行此腳本")
        
    except Exception as e:
        print(f"❌ 執行錯誤: {e}")