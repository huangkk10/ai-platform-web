#!/usr/bin/env python
"""
測試「iol 密碼」查詢的向量搜尋排名問題
驗證為什麼 sec_5（包含密碼）的排名不在前面
"""

import os
import sys
import django

# 設置 Django 環境
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.services.embedding_service import get_embedding_service
from django.db import connection
from api.models import ProtocolGuide

def test_section_ranking():
    """測試分段向量搜尋排名"""
    service = get_embedding_service()
    query = "iol 密碼"
    
    print('='*100)
    print(f'🔍 測試查詢: "{query}"')
    print('='*100)
    print()
    
    # 1. 查詢所有 IOL 相關分段
    print('【步驟1】查詢 IOL 文件的所有分段')
    print('-'*100)
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                section_id,
                heading_text,
                LENGTH(content) as content_length,
                (content ILIKE '%iol%') as has_iol,
                (content ILIKE '%密碼%' OR content ILIKE '%password%') as has_password,
                LEFT(content, 100) as preview
            FROM document_section_embeddings
            WHERE source_table = 'protocol_guide'
              AND source_id = 10
            ORDER BY section_id;
        """)
        
        sections = cursor.fetchall()
        
        print(f'找到 {len(sections)} 個分段:\n')
        
        for sec_id, heading, length, has_iol, has_password, preview in sections:
            marker = []
            if has_iol:
                marker.append('IOL')
            if has_password:
                marker.append('密碼')
            
            markers = f"[{'+'.join(marker)}]" if marker else ""
            print(f'{sec_id:12} | {length:4}字 | {heading[:40]:40} | {markers}')
            
            if has_password:
                print(f'             └─> ⭐ 目標分段！內容: {preview}...')
    
    print()
    print('='*100)
    print('【步驟2】執行向量搜尋並分析排名')
    print('-'*100)
    
    # 2. 執行向量搜尋
    query_vector = service.generate_embedding(query)
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                section_id,
                heading_text,
                LENGTH(content) as content_length,
                1 - (content_embedding <=> %s::vector) as similarity,
                content
            FROM document_section_embeddings
            WHERE source_table = 'protocol_guide'
              AND source_id = 10
              AND content_embedding IS NOT NULL
            ORDER BY content_embedding <=> %s::vector
            LIMIT 10;
        """, [query_vector, query_vector])
        
        results = cursor.fetchall()
        
        print(f'\n向量搜尋結果（按相似度排序）:\n')
        print(f'{"排名":^6} {"Section ID":^12} {"相似度":^10} {"長度":^8} {"標題":40} 關鍵字')
        print('-'*100)
        
        target_rank = None
        
        for i, (sec_id, heading, length, similarity, content) in enumerate(results, 1):
            has_iol = 'iol' in content.lower()
            has_password = '密碼' in content or 'password' in content.lower()
            
            markers = []
            if has_iol:
                markers.append('IOL')
            if has_password:
                markers.append('密碼')
            
            marker_str = f"[{'+'.join(markers)}]" if markers else ""
            
            row = f'{i:^6} {sec_id:^12} {similarity:^10.4f} {length:^8} {heading[:40]:40} {marker_str}'
            
            if has_password and has_iol:
                print(f'⭐ {row}  ← 目標分段！')
                target_rank = i
                
                # 顯示密碼位置
                idx = content.find('密碼')
                if idx >= 0:
                    context = content[max(0, idx-50):idx+80]
                    print(f'   └─> 內容: ...{context}...')
            else:
                print(f'   {row}')
        
        print()
        print('='*100)
        print('【分析結果】')
        print('-'*100)
        
        if target_rank:
            print(f'✅ 找到目標分段: sec_5')
            print(f'📊 排名: 第 {target_rank} 名')
            
            if target_rank <= 3:
                print(f'✅ 狀態: 正常（排名在前3名）')
            elif target_rank <= 5:
                print(f'⚠️  狀態: 可能有問題（排名第 {target_rank}，如果 top_k < {target_rank} 會被過濾）')
            else:
                print(f'❌ 狀態: 有問題（排名太後，可能被過濾）')
            
            print()
            print('問題分析:')
            print('1. sec_5 包含「密碼為1」的正確答案')
            print('2. 但向量相似度排名不在最前面')
            print('3. 原因: 短文本（doc_10 只有7字元）的 IOL 密度更高，相似度更高')
            print('4. sec_5 有 186 字元，「密碼」關鍵字被其他內容稀釋')
        else:
            print('❌ 未找到包含密碼資訊的分段！')
    
    print()
    print('='*100)
    print('【步驟3】測試不同查詢詞的效果')
    print('-'*100)
    
    test_queries = [
        ("iol 密碼", "原始查詢"),
        ("密碼", "只查密碼"),
        ("sudo 密碼", "更具體的查詢"),
        ("執行指令 密碼", "加入上下文"),
    ]
    
    for test_query, description in test_queries:
        query_vector = service.generate_embedding(test_query)
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    section_id,
                    1 - (content_embedding <=> %s::vector) as similarity
                FROM document_section_embeddings
                WHERE source_table = 'protocol_guide'
                  AND source_id = 10
                  AND section_id = 'sec_5'
                  AND content_embedding IS NOT NULL;
            """, [query_vector])
            
            result = cursor.fetchone()
            if result:
                sec_id, similarity = result
                print(f'查詢: "{test_query:20}" ({description:15}) | sec_5 相似度: {similarity:.4f}')
    
    print()
    print('='*100)
    print('【建議】')
    print('-'*100)
    print('''
1. 短期方案: 調整查詢策略
   - 拆分「iol 密碼」為兩次查詢: "iol" + "密碼"
   - 或使用更具體的查詢: "iol sudo 密碼"

2. 中期方案: 調整權重配置
   - 降低 Title Weight (95% → 70%)
   - 提高 Content Weight (5% → 30%)
   - 在 VSA 版本管理中測試

3. 長期方案: 優化分段策略
   - 將 sec_5 拆分為更小的子分段
   - 例如: sec_5_2 只包含 "sudo su, 密碼為1"
   - 重新生成向量

4. 最佳方案: 混合搜尋 (RRF)
   - 結合向量搜尋和關鍵字搜尋
   - 使用 Reciprocal Rank Fusion 合併結果
    ''')
    
    print('='*100)

if __name__ == '__main__':
    test_section_ranking()
