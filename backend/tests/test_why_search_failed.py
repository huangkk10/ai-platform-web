#!/usr/bin/env python3
"""
測試為什麼語義搜尋找不到 CrystalDiskMark
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
import django
django.setup()

from django.db import connection

query = "crystaldiskmark 如何放測"

print("=" * 80)
print(f"測試查詢: {query}")
print("=" * 80)

# 步驟 1: 生成查詢向量
from api.services.embedding_service import get_embedding_service

service = get_embedding_service()
query_embedding = service.generate_embedding(query)

print(f"\n✅ 查詢向量生成成功: {len(query_embedding)} 維")

# 步驟 2: 直接用 SQL 搜尋
with connection.cursor() as cursor:
    sql = """
    SELECT 
        source_id,
        LEFT(text_content, 100) as preview,
        1 - (embedding <=> %s::vector) as similarity
    FROM document_embeddings 
    WHERE source_table = 'protocol_guide'
    ORDER BY similarity DESC
    LIMIT 5;
    """
    
    cursor.execute(sql, [query_embedding])
    results = cursor.fetchall()
    
    print(f"\n📊 搜尋結果（直接 SQL）:")
    print("-" * 80)
    for source_id, preview, similarity in results:
        print(f"ID {source_id}: 相似度 {similarity:.2%}")
        print(f"  內容: {preview}...")
        print()

# 步驟 3: 測試不同閾值
print("\n📈 測試不同 threshold:")
print("-" * 80)

for threshold in [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]:
    with connection.cursor() as cursor:
        sql = """
        SELECT COUNT(*)
        FROM document_embeddings 
        WHERE source_table = 'protocol_guide'
          AND (1 - (embedding <=> %s::vector)) >= %s
        """
        cursor.execute(sql, [query_embedding, threshold])
        count = cursor.fetchone()[0]
        print(f"  Threshold {threshold}: {count} 條結果")

# 步驟 4: 檢查 ID 16 的相似度
with connection.cursor() as cursor:
    sql = """
    SELECT 
        source_id,
        text_content,
        1 - (embedding <=> %s::vector) as similarity
    FROM document_embeddings 
    WHERE source_table = 'protocol_guide'
      AND source_id = 16
    """
    cursor.execute(sql, [query_embedding])
    result = cursor.fetchone()
    
    if result:
        source_id, content, similarity = result
        print(f"\n🎯 CrystalDiskMark (ID 16) 的相似度:")
        print(f"  相似度: {similarity:.2%}")
        print(f"  內容預覽: {content[:200]}...")
        
        if similarity < 0.5:
            print(f"\n⚠️ 相似度 {similarity:.2%} < 0.5，會被 threshold 過濾掉！")
        else:
            print(f"\n✅ 相似度 {similarity:.2%} >= 0.5，應該會被找到")
