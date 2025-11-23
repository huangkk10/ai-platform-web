#!/usr/bin/env python
"""
直接測試 search_with_vectors 方法，繞過 ProtocolGuideSearchService 的智能搜索邏輯
"""
import os
import sys
import django

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from library.protocol_guide.search_service import ProtocolGuideSearchService
from api.models import BenchmarkTestCase

def test_direct_search():
    """直接測試搜索方法"""
    
    test_case = BenchmarkTestCase.objects.filter(is_active=True).first()
    query = test_case.question
    print(f"\n測試題目: {query}\n")
    
    service = ProtocolGuideSearchService()
    
    # 測試 1: section_only 模式
    print("=" * 80)
    print("測試 section_only 模式")
    print("=" * 80)
    results_section = service.search_with_vectors(
        query=query,
        limit=10,
        threshold=0.75,
        search_mode='section_only',
        stage=1
    )
    ids_section = [r.get('metadata', {}).get('id') for r in results_section]
    print(f"Section 返回 {len(results_section)} 個結果")
    print(f"IDs: {ids_section}\n")
    
    # 測試 2: document_only 模式
    print("=" * 80)
    print("測試 document_only 模式")
    print("=" * 80)
    results_document = service.search_with_vectors(
        query=query,
        limit=10,
        threshold=0.65,
        search_mode='document_only',
        stage=1
    )
    ids_document = [r.get('metadata', {}).get('id') for r in results_document]
    print(f"Document 返回 {len(results_document)} 個結果")
    print(f"IDs: {ids_document}\n")
    
    # 比較
    print("=" * 80)
    print("比較結果")
    print("=" * 80)
    print(f"Section IDs: {ids_section}")
    print(f"Document IDs: {ids_document}")
    
    if ids_section == ids_document:
        print("\n❌ section_only 和 document_only 返回相同的 IDs！")
    else:
        print("\n✅ section_only 和 document_only 返回不同的 IDs！")
        print(f"   共同 IDs: {set(ids_section) & set(ids_document)}")
        print(f"   Section 獨有: {set(ids_section) - set(ids_document)}")
        print(f"   Document 獨有: {set(ids_document) - set(ids_section)}")

if __name__ == '__main__':
    test_direct_search()
