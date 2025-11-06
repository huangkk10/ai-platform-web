#!/usr/bin/env python3
"""
測試 Protocol Guide 段落搜尋效果
===================================
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from library.protocol_guide.search_service import ProtocolGuideSearchService


def test_section_search():
    """測試段落搜尋"""
    print('=' * 70)
    print('🧪 Protocol Guide 段落搜尋測試（Threshold = 0.7）')
    print('=' * 70)
    print()

    service = ProtocolGuideSearchService()

    test_queries = [
        ('UART配置', '測試硬體相關問題'),
        ('測試步驟', '測試流程相關問題'),
        ('如何進行測試', '通用測試問題'),
        ('Serial Port', '英文測試'),
    ]

    for query, desc in test_queries:
        print(f'📝 問題: {query} ({desc})')
        print('-' * 70)
        
        results = service.search_knowledge(query, limit=3, use_vector=True)
        
        if results:
            print(f'✅ 找到 {len(results)} 個結果:\n')
            for i, r in enumerate(results, 1):
                score = r.get('score', 0)
                title = r.get('title', 'N/A')
                sections = r.get('metadata', {}).get('sections_found', 0)
                
                print(f'  {i}. 相似度: {score:.2%}')
                print(f'     標題: {title}')
                if sections:
                    print(f'     相關段落數: {sections}')
                print()
        else:
            print('❌ 沒有找到相關結果（相似度都 < 70%）')
            print()
        print()


if __name__ == '__main__':
    test_section_search()
