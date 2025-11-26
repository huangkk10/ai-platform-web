#!/usr/bin/env python
"""直接使用 SQL 測試 Stage 1 段落搜尋"""

import os
import sys
import django

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.services.embedding_service import get_embedding_service
from django.db import connection

def test_stage1_sql():
    """使用 SQL 直接測試 Stage 1"""
    
    query = "CrystalDiskMark ？"
    
    print(f"\n{'='*80}")
    print(f"🔍 Stage 1 SQL 測試")
    print(f"{'='*80}\n")
    print(f"查詢: {query}")
    print(f"權重: 標題 95% / 內容 5%")
    print(f"\n生成向量...")
    
    # 生成查詢向量
    service = get_embedding_service()
    query_embedding = service.generate_embedding(query)
    embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
    
    print(f"✅ 向量生成完成 ({len(query_embedding)} 維)\n")
    print(f"執行 SQL 查詢...")
    
    # 使用與實際 Stage 1 相同的 SQL
    sql = f"""
        SELECT 
            dse.source_id,
            dse.heading_text,
            pg.title as doc_title,
            (0.95 * (1 - (dse.title_embedding <=> %s::vector))) + 
            (0.05 * (1 - (dse.content_embedding <=> %s::vector))) as similarity,
            (1 - (dse.title_embedding <=> %s::vector)) as title_score,
            (1 - (dse.content_embedding <=> %s::vector)) as content_score
        FROM document_section_embeddings dse
        LEFT JOIN protocol_guide pg ON dse.source_table = 'protocol_guide' AND pg.id = dse.source_id
        WHERE dse.source_table = 'protocol_guide'
          AND dse.title_embedding IS NOT NULL
          AND dse.content_embedding IS NOT NULL
        ORDER BY similarity DESC
        LIMIT 10
    """
    
    with connection.cursor() as cursor:
        cursor.execute(sql, [embedding_str, embedding_str, embedding_str, embedding_str])
        results = cursor.fetchall()
    
    print(f"\n{'='*80}")
    print(f"📊 搜尋結果 (前 10 名)")
    print(f"{'='*80}\n")
    
    for i, row in enumerate(results, 1):
        source_id, heading_text, doc_title, similarity, title_score, content_score = row
        
        # 標記 CrystalDiskMark 相關
        is_cdm = " ⭐ [CrystalDiskMark 相關]" if 'CrystalDiskMark' in str(doc_title) else ""
        
        print(f"結果 {i}:{is_cdm}")
        print(f"  文檔 ID: {source_id}")
        print(f"  文檔標題: {doc_title}")
        print(f"  段落標題: {heading_text}")
        print(f"  組合分數: {similarity:.4f} ({similarity*100:.2f}%)")
        print(f"  ├─ 標題分數: {title_score:.4f} (權重 95%)")
        print(f"  └─ 內容分數: {content_score:.4f} (權重 5%)")
        print()
    
    # 分析結果
    print(f"{'='*80}")
    print(f"🎯 Stage 1 搜尋分析")
    print(f"{'='*80}\n")
    
    if results:
        top_result = results[0]
        top_doc_title = top_result[2]
        
        if 'CrystalDiskMark' in str(top_doc_title):
            print(f"✅ Stage 1 正確找到 CrystalDiskMark 相關段落")
            print(f"   文檔: {top_doc_title}")
        else:
            print(f"❌ Stage 1 沒有找到 CrystalDiskMark 相關段落")
            print(f"   找到的是: {top_doc_title}")
            
            # 檢查 CrystalDiskMark 的排名
            cdm_results = [r for r in results if 'CrystalDiskMark' in str(r[2])]
            if cdm_results:
                cdm_result = cdm_results[0]
                rank = results.index(cdm_result) + 1
                print(f"\n📊 CrystalDiskMark 5 實際排名: 第 {rank} 名")
                print(f"   相似度: {cdm_result[3]:.4f}")
            else:
                print(f"\n⚠️ CrystalDiskMark 5 不在前 10 名結果中")
    
    print(f"\n{'='*80}\n")

if __name__ == '__main__':
    test_stage1_sql()
