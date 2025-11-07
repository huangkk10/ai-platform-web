#!/usr/bin/env python3
"""
測試 Threshold 調整效果
========================

測試修改後的向量搜尋 threshold：
- 段落搜尋：0.3 → 0.7
- 文檔搜尋：0.0 → 0.6

使用方式：
    docker exec ai-django python test_threshold_adjustment.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from library.protocol_guide.search_service import ProtocolGuideSearchService
from library.rvt_guide.search_service import RVTGuideSearchService


def test_protocol_guide_search():
    """測試 Protocol Guide 搜尋"""
    print("=" * 60)
    print("🔍 測試 Protocol Guide 搜尋")
    print("=" * 60)
    
    service = ProtocolGuideSearchService()
    
    test_queries = [
        "UART 配置",
        "Serial Port",
        "測試流程",
        "如何進行測試",
    ]
    
    for query in test_queries:
        print(f"\n📝 問題：{query}")
        print("-" * 60)
        
        # 執行搜尋
        results = service.search_knowledge(query, limit=3, use_vector=True)
        
        if results:
            print(f"✅ 找到 {len(results)} 個結果：\n")
            for i, result in enumerate(results, 1):
                score = result.get('score', 0)
                title = result.get('title', 'N/A')
                content_preview = result.get('content', '')[:100]
                
                print(f"  {i}. 相似度：{score:.2%}")
                print(f"     標題：{title}")
                print(f"     內容：{content_preview}...")
                print()
        else:
            print("❌ 沒有找到相關結果")
            print("   （這可能代表：）")
            print("   - 沒有高於 threshold 的結果")
            print("   - Protocol Guide 沒有段落向量資料")
            print()


def test_rvt_guide_search():
    """測試 RVT Guide 搜尋"""
    print("\n" + "=" * 60)
    print("🔍 測試 RVT Guide 搜尋")
    print("=" * 60)
    
    service = RVTGuideSearchService()
    
    test_queries = [
        "RVT 測試步驟",
        "如何執行測試",
    ]
    
    for query in test_queries:
        print(f"\n📝 問題：{query}")
        print("-" * 60)
        
        # 執行搜尋
        results = service.search_knowledge(query, limit=3, use_vector=True)
        
        if results:
            print(f"✅ 找到 {len(results)} 個結果：\n")
            for i, result in enumerate(results, 1):
                score = result.get('score', 0)
                title = result.get('title', 'N/A')
                content_preview = result.get('content', '')[:100]
                
                print(f"  {i}. 相似度：{score:.2%}")
                print(f"     標題：{title}")
                print(f"     內容：{content_preview}...")
                print()
        else:
            print("❌ 沒有找到相關結果")
            print()


def show_threshold_info():
    """顯示當前 threshold 設定"""
    print("=" * 60)
    print("⚙️  當前 Threshold 設定")
    print("=" * 60)
    print()
    print("📊 雙層搜尋策略：")
    print("  第一層 - 段落搜尋：threshold = 0.7")
    print("           (只返回相似度 ≥ 70% 的段落)")
    print()
    print("  第二層 - 文檔搜尋：threshold = 0.6")
    print("           (備用方案，只返回相似度 ≥ 60% 的文檔)")
    print()
    print("💡 預期效果：")
    print("  ✅ 大幅減少不相關內容")
    print("  ✅ 避免「混到其他資料」的問題")
    print("  ✅ 保持系統健壯性（雙層備援）")
    print()


if __name__ == '__main__':
    show_threshold_info()
    
    # 測試 Protocol Guide
    test_protocol_guide_search()
    
    # 測試 RVT Guide
    test_rvt_guide_search()
    
    print("\n" + "=" * 60)
    print("📋 測試完成")
    print("=" * 60)
    print()
    print("💡 注意事項：")
    print("  - 如果 Protocol Guide 沒有結果，請先生成段落向量")
    print("  - 如果相似度都低於 threshold，會返回空結果")
    print("  - 這是正常的！比返回不相關內容更好")
    print()
