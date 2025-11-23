"""
調試搜尋結果結構
================

檢查 section_only 和 document_only 返回的結果結構
"""

import os
import sys
import django

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from library.protocol_guide.search_service import ProtocolGuideSearchService
import json

def debug_result_structure():
    service = ProtocolGuideSearchService()
    query = "Burn in Test 測試失敗時如何排查？"
    
    print("=" * 80)
    print("段落搜尋結果結構 (section_only)")
    print("=" * 80)
    
    section_results = service.search_with_vectors(
        query=query,
        limit=3,
        threshold=0.75,
        search_mode='section_only',
        stage=1
    )
    
    print(f"\n返回 {len(section_results)} 個結果\n")
    
    for i, result in enumerate(section_results[:2], 1):
        print(f"結果 {i}:")
        print(f"  Keys: {list(result.keys())}")
        print(f"  document_id: {result.get('document_id', 'MISSING')}")
        print(f"  metadata.document_id: {result.get('metadata', {}).get('document_id', 'MISSING')}")
        print(f"  metadata.id: {result.get('metadata', {}).get('id', 'MISSING')}")
        print(f"  id: {result.get('id', 'MISSING')}")
        print(f"  similarity/score: {result.get('similarity', result.get('score', 'MISSING'))}")
        print()
    
    print("=" * 80)
    print("全文搜尋結果結構 (document_only)")
    print("=" * 80)
    
    document_results = service.search_with_vectors(
        query=query,
        limit=3,
        threshold=0.65,
        search_mode='document_only',
        stage=2
    )
    
    print(f"\n返回 {len(document_results)} 個結果\n")
    
    for i, result in enumerate(document_results[:2], 1):
        print(f"結果 {i}:")
        print(f"  Keys: {list(result.keys())}")
        print(f"  document_id: {result.get('document_id', 'MISSING')}")
        print(f"  metadata.document_id: {result.get('metadata', {}).get('document_id', 'MISSING')}")
        print(f"  metadata.id: {result.get('metadata', {}).get('id', 'MISSING')}")
        print(f"  id: {result.get('id', 'MISSING')}")
        print(f"  similarity/score: {result.get('similarity', result.get('score', 'MISSING'))}")
        print()

if __name__ == "__main__":
    debug_result_structure()
