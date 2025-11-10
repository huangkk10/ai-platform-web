#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
測試完整文檔展開功能
===================

驗證 _expand_to_full_document() 是否正常工作
"""

import os
import sys
import django

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from library.protocol_guide.search_service import ProtocolGuideSearchService


def test_full_document_expansion():
    """測試完整文檔展開"""
    
    service = ProtocolGuideSearchService()
    
    test_queries = [
        "Cup顏色全文",
        "Cup 的完整內容",
        "請給我 Cup 的所有資訊",
    ]
    
    print("=" * 80)
    print("🧪 測試完整文檔展開功能")
    print("=" * 80)
    print()
    
    for query in test_queries:
        print(f"查詢: '{query}'")
        print("-" * 80)
        
        try:
            # 執行搜尋
            results = service.search_knowledge(
                query=query,
                limit=2,
                use_vector=True,
                threshold=0.5
            )
            
            print(f"結果數量: {len(results)}")
            
            for i, result in enumerate(results, 1):
                print(f"\n結果 {i}:")
                print(f"  標題: {result.get('title', 'N/A')}")
                print(f"  分數: {result.get('score', 0):.4f}")
                
                metadata = result.get('metadata', {})
                is_full_doc = metadata.get('is_full_document', False)
                document_id = metadata.get('document_id', 'N/A')
                sections_count = metadata.get('sections_count', 0)
                
                print(f"  類型: {'✅ 完整文檔' if is_full_doc else '❌ Section'}")
                print(f"  Document ID: {document_id}")
                
                if is_full_doc:
                    print(f"  包含段落數: {sections_count}")
                
                content = result.get('content', '')
                print(f"  內容長度: {len(content)} 字元")
                
                # 顯示內容預覽
                content_preview = content[:200] + '...' if len(content) > 200 else content
                print(f"  內容預覽:")
                for line in content_preview.split('\n')[:5]:
                    print(f"    {line}")
                
                if len(content_preview.split('\n')) > 5:
                    print("    ...")
            
            print()
            
        except Exception as e:
            print(f"❌ 錯誤: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print("=" * 80)
        print()


if __name__ == '__main__':
    test_full_document_expansion()
