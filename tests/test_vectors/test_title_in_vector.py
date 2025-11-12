#!/usr/bin/env python
"""
測試腳本：驗證段落的 title_embedding 是否包含文件標題
"""
import os
import sys
import django

# 設置 Django 環境
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from django.db import connection
from api.services.embedding_service import get_embedding_service

def test_title_embedding_includes_doc_title():
    """測試 title_embedding 是否包含文件標題"""
    
    print("=" * 80)
    print("🔍 測試：驗證 title_embedding 是否包含文件標題")
    print("=" * 80)
    
    # 初始化 embedding service
    embedding_service = get_embedding_service('ultra_high')
    
    # 測試案例 1: CrystalDiskMark 5
    print("\n📊 測試案例 1: CrystalDiskMark 5")
    print("-" * 80)
    
    # 生成測試查詢向量
    query_with_title = "CrystalDiskMark 5 boot into system"  # 包含文件標題
    query_without_title = "boot into system"  # 只有段落標題
    
    query_vec_with = embedding_service.generate_embedding(query_with_title)
    query_vec_without = embedding_service.generate_embedding(query_without_title)
    
    # 查詢 CrystalDiskMark 5 的 sec_2 段落（heading: "2.When boot into system."）
    with connection.cursor() as cursor:
        # 格式化向量為 PostgreSQL 接受的格式
        query_vec_with_str = '[' + ','.join(map(str, query_vec_with)) + ']'
        query_vec_without_str = '[' + ','.join(map(str, query_vec_without)) + ']'
        
        cursor.execute("""
            SELECT 
                pg.title as doc_title,
                dse.heading_text,
                dse.section_id,
                -- 使用包含文件標題的查詢
                1 - (dse.title_embedding <=> %s::vector) as similarity_with_doc_title,
                -- 使用不包含文件標題的查詢
                1 - (dse.title_embedding <=> %s::vector) as similarity_without_doc_title
            FROM document_section_embeddings dse
            JOIN protocol_guide pg ON pg.id = dse.source_id
            WHERE dse.source_table = 'protocol_guide' 
              AND pg.id = 16  -- CrystalDiskMark 5
              AND dse.section_id = 'sec_2'  -- "2.When boot into system."
        """, [query_vec_with_str, query_vec_without_str])
        
        result = cursor.fetchone()
        if result:
            doc_title, heading, section_id, sim_with, sim_without = result
            print(f"文件標題: {doc_title}")
            print(f"段落標題: {heading}")
            print(f"段落 ID: {section_id}")
            print(f"\n相似度比較:")
            print(f"  查詢 '{query_with_title}' → 相似度: {sim_with:.4f}")
            print(f"  查詢 '{query_without_title}' → 相似度: {sim_without:.4f}")
            
            if sim_with > sim_without:
                improvement = ((sim_with - sim_without) / sim_without) * 100
                print(f"\n✅ 結論: title_embedding 包含文件標題！")
                print(f"   包含文件標題的查詢相似度提升 {improvement:.1f}%")
            else:
                print(f"\n❌ 結論: title_embedding 可能不包含文件標題")
    
    # 測試案例 2: UNH-IOL（對比組）
    print("\n" + "=" * 80)
    print("📊 測試案例 2: UNH-IOL（對比組）")
    print("-" * 80)
    
    # 生成測試查詢向量
    query_iol = "UNH-IOL 5"  # 包含 "IOL" 和 "5"
    query_vec_iol = embedding_service.generate_embedding(query_iol)
    query_vec_iol_str = '[' + ','.join(map(str, query_vec_iol)) + ']'
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                pg.title as doc_title,
                dse.heading_text,
                dse.section_id,
                1 - (dse.title_embedding <=> %s::vector) as similarity
            FROM document_section_embeddings dse
            JOIN protocol_guide pg ON pg.id = dse.source_id
            WHERE dse.source_table = 'protocol_guide' 
              AND pg.id = 10  -- UNH-IOL
              AND dse.heading_text LIKE '%IOL%'
            ORDER BY similarity DESC
            LIMIT 1
        """, [query_vec_iol_str])
        
        result = cursor.fetchone()
        if result:
            doc_title, heading, section_id, similarity = result
            print(f"文件標題: {doc_title}")
            print(f"段落標題: {heading}")
            print(f"段落 ID: {section_id}")
            print(f"相似度: {similarity:.4f}")
    
    # 測試案例 3: 實際搜索 "crystaldiskmark 5"
    print("\n" + "=" * 80)
    print("📊 測試案例 3: 實際搜索 'crystaldiskmark 5'")
    print("-" * 80)
    
    query = "crystaldiskmark 5"
    query_vec = embedding_service.generate_embedding(query)
    query_vec_str = '[' + ','.join(map(str, query_vec)) + ']'
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                pg.title as doc_title,
                dse.heading_text,
                dse.section_id,
                1 - (dse.title_embedding <=> %s::vector) as title_similarity,
                1 - (dse.content_embedding <=> %s::vector) as content_similarity,
                (0.4 * (1 - (dse.title_embedding <=> %s::vector))) + 
                (0.6 * (1 - (dse.content_embedding <=> %s::vector))) as final_score
            FROM document_section_embeddings dse
            JOIN protocol_guide pg ON pg.id = dse.source_id
            WHERE dse.source_table = 'protocol_guide'
              AND dse.title_embedding IS NOT NULL
              AND dse.content_embedding IS NOT NULL
            ORDER BY final_score DESC
            LIMIT 5
        """, [query_vec_str, query_vec_str, query_vec_str, query_vec_str])
        
        results = cursor.fetchall()
        print(f"\n查詢: '{query}'")
        print(f"權重配置: title 40% + content 60%")
        print("\nTop 5 結果:")
        print("-" * 80)
        
        for i, (doc_title, heading, section_id, title_sim, content_sim, final) in enumerate(results, 1):
            print(f"\n{i}. {doc_title} - {section_id}")
            print(f"   段落標題: {heading[:60]}...")
            print(f"   標題相似度: {title_sim:.4f}")
            print(f"   內容相似度: {content_sim:.4f}")
            print(f"   最終分數: {final:.4f}")
    
    print("\n" + "=" * 80)
    print("✅ 測試完成")
    print("=" * 80)

if __name__ == '__main__':
    test_title_embedding_includes_doc_title()
