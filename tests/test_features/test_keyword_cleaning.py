#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
測試關鍵字清理功能（方案一：Keyword Cleaning）
==========================================

測試場景：
1. 包含關鍵字的查詢 → 應被清理
2. 不包含關鍵字的查詢 → 保持原樣
3. 多個關鍵字的查詢 → 全部清理
4. 大小寫混合 → 正確識別和清理

預期效果：
- 原始查詢：'如何完整測試 USB'
- 清理後：'如何測試 USB'
- 結果：向量搜尋更聚焦於 'USB 測試'
"""

import os
import sys
import django

# Django 設定
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from library.protocol_guide.search_service import ProtocolGuideSearchService


def test_keyword_cleaning():
    """測試關鍵字清理功能"""
    
    service = ProtocolGuideSearchService()
    
    test_cases = [
        # (查詢, 預期查詢類型, 預期清理後查詢)
        ("如何完整測試 USB", "document", "如何測試 USB"),
        ("USB 測試的所有步驟", "document", "USB 測試的步驟"),
        ("請給我 USB 的全部測試流程", "document", "請給我 USB 的測試流程"),
        ("完整的 ULINK SOP", "document", "的 ULINK"),
        ("USB 如何測試", "section", "USB 如何測試"),
        ("測試 USB 功能", "section", "測試 USB 功能"),
        ("SOP 文件在哪", "document", "文件在哪"),
        ("標準作業流程", "document", ""),
        ("完整 全部 所有步驟", "document", ""),
    ]
    
    print("=" * 80)
    print("🧪 測試關鍵字清理功能（方案一：Keyword Cleaning）")
    print("=" * 80)
    print()
    
    for i, (query, expected_type, expected_cleaned) in enumerate(test_cases, 1):
        print(f"測試案例 {i}:")
        print(f"  原始查詢: '{query}'")
        
        try:
            query_type, cleaned_query = service._classify_and_clean_query(query)
            
            print(f"  查詢類型: {query_type}")
            print(f"  清理後查詢: '{cleaned_query}'")
            
            # 驗證
            type_match = "✅" if query_type == expected_type else "❌"
            clean_match = "✅" if cleaned_query == expected_cleaned else "❌"
            
            print(f"  類型檢查: {type_match} (預期: {expected_type})")
            print(f"  清理檢查: {clean_match} (預期: '{expected_cleaned}')")
            
            if query_type == expected_type and cleaned_query == expected_cleaned:
                print("  ✅ 通過")
            else:
                print("  ❌ 失敗")
                
        except Exception as e:
            print(f"  ❌ 錯誤: {str(e)}")
        
        print()
    
    print("=" * 80)
    print()


def test_real_search():
    """測試實際搜尋效果"""
    
    service = ProtocolGuideSearchService()
    
    print("=" * 80)
    print("🔍 實際搜尋測試")
    print("=" * 80)
    print()
    
    test_queries = [
        "如何完整測試 USB",
        "USB 測試的所有步驟",
        "USB 如何測試"
    ]
    
    for query in test_queries:
        print(f"查詢: '{query}'")
        print("-" * 80)
        
        try:
            # 執行搜尋
            results = service.search_knowledge(
                query=query,
                limit=3,
                use_vector=True,
                threshold=0.5
            )
            
            print(f"結果數量: {len(results)}")
            
            for i, result in enumerate(results, 1):
                print(f"\n結果 {i}:")
                print(f"  分數: {result.get('score', 0):.4f}")
                print(f"  標題: {result.get('title', 'N/A')}")
                
                metadata = result.get('metadata', {})
                is_full_doc = metadata.get('is_full_document', False)
                print(f"  類型: {'完整文檔' if is_full_doc else 'Section'}")
                
                content = result.get('content', '')
                content_preview = content[:150] + '...' if len(content) > 150 else content
                print(f"  內容預覽: {content_preview}")
            
        except Exception as e:
            print(f"❌ 搜尋錯誤: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print()
        print("=" * 80)
        print()


if __name__ == '__main__':
    print("\n")
    print("🚀 開始測試關鍵字清理功能")
    print()
    
    # 測試 1: 關鍵字清理邏輯
    test_keyword_cleaning()
    
    # 測試 2: 實際搜尋效果
    test_real_search()
    
    print("✅ 測試完成")
