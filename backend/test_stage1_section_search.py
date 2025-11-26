#!/usr/bin/env python
"""測試 Stage 1 段落搜尋，查看實際找到的是哪個段落"""

import os
import sys
import django

# 設定 Django 環境
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.services.embedding_service import get_embedding_service
from django.db import connection

def test_stage1_search():
    """測試 Stage 1 段落搜尋"""
    
    query = "CrystalDiskMark ？"  # 清理後的查詢
    
    print(f"\n{'='*80}")
    print(f"🔍 測試 Stage 1 段落搜尋 (模擬實際搜尋)")
    print(f"{'='*80}\n")
    print(f"查詢: {query}")
    print(f"權重: 標題 95% / 內容 5%")
    print(f"source_table: protocol_guide_section")
    print(f"limit: 5 (多看幾筆)")
    print(f"\n執行搜尋...")
    
    # 使用 embedding_service 的多向量搜尋
    service = get_embedding_service()
    
    results = service.search_similar_documents_multi(
        query=query,
        source_table='protocol_guide_section',  # 使用段落來源
        limit=5,
        threshold=0.0,  # 不設門檻，看所有結果
        title_weight=0.95,  # Stage 1: 標題 95%
        content_weight=0.05  # Stage 1: 內容 5%
    )
    
    print(f"\n{'='*80}")
    print(f"📊 搜尋結果 (前 5 名)")
    print(f"{'='*80}\n")
    
    if results:
        for i, result in enumerate(results, 1):
            source_id = result.get('source_id')
            combined_score = result.get('combined_score', 0)
            
            # 從 document_section_embeddings 查詢段落資訊
            title = 'N/A'
            parent_id = None
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT dse.section_title, dse.document_id, pg.title as parent_title
                    FROM document_section_embeddings dse
                    LEFT JOIN protocol_guide pg ON dse.document_id = pg.id
                    WHERE dse.id = %s AND dse.source_table = 'protocol_guide'
                """, [source_id])
                row = cursor.fetchone()
                if row:
                    title = row[0] or 'N/A'
                    parent_id = row[1]
                    parent_title = row[2] or 'N/A'
                else:
                    parent_title = 'N/A'
            
            # 標記 CrystalDiskMark 相關的段落
            is_cdm = " ⭐ [CrystalDiskMark 相關]" if 'CrystalDiskMark' in title or 'CrystalDiskMark' in parent_title else ""
            
            print(f"結果 {i}:{is_cdm}")
            print(f"  段落 ID: {source_id}")
            print(f"  段落標題: {title}")
            print(f"  父文檔: {parent_title}")
            print(f"  組合分數: {combined_score:.4f} ({combined_score*100:.2f}%)")
            
            # 顯示詳細分數
            if 'title_score' in result:
                title_score = result['title_score']
                print(f"  ├─ 標題分數: {title_score:.4f} (權重 95%)")
            if 'content_score' in result:
                content_score = result['content_score']
                print(f"  └─ 內容分數: {content_score:.4f} (權重 5%)")
            
            print()
    else:
        print("⚠️ 沒有找到任何結果")
    
    # 總結
    print(f"\n{'='*80}")
    print(f"🎯 Stage 1 搜尋結果分析")
    print(f"{'='*80}\n")
    
    if results:
        top_result = results[0]
        top_id = top_result.get('source_id')
        
        # 從資料庫查詢第一名結果的詳細資訊
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT dse.section_title, dse.document_id, pg.title as parent_title
                FROM document_section_embeddings dse
                LEFT JOIN protocol_guide pg ON dse.document_id = pg.id
                WHERE dse.id = %s AND dse.source_table = 'protocol_guide'
            """, [top_id])
            row = cursor.fetchone()
            
            if row:
                section_title = row[0] or 'N/A'
                parent_id = row[1]
                parent_title = row[2] or 'N/A'
                
                print(f"第 1 名結果:")
                print(f"  段落 ID: {top_id}")
                print(f"  段落標題: {section_title}")
                print(f"  父文檔 ID: {parent_id}")
                print(f"  父文檔: {parent_title}")
                
                if 'CrystalDiskMark' in section_title or 'CrystalDiskMark' in parent_title:
                    print(f"\n✅ Stage 1 找到 CrystalDiskMark 相關段落")
                else:
                    print(f"\n❌ Stage 1 沒有找到 CrystalDiskMark 相關段落")
                    print(f"   找到的是: {parent_title} - {section_title}")
            else:
                print(f"❌ 無法查詢到段落資訊 (ID={top_id})")
    else:
        print("❌ 沒有找到任何結果")
    
    # 檢查是否有 CrystalDiskMark 5 文檔的段落
    print(f"\n{'='*80}")
    print(f"📋 檢查 CrystalDiskMark 5 文檔的段落")
    print(f"{'='*80}\n")
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) 
            FROM document_section_embeddings 
            WHERE source_table = 'protocol_guide' 
              AND document_id = 16
        """)
        count = cursor.fetchone()[0]
        
        print(f"CrystalDiskMark 5 (文檔 ID=16) 的段落數量: {count}")
        
        if count > 0:
            cursor.execute("""
                SELECT id, section_title, heading_level
                FROM document_section_embeddings 
                WHERE source_table = 'protocol_guide' 
                  AND document_id = 16
                ORDER BY id
                LIMIT 10
            """)
            
            print(f"\n段落列表:")
            for idx, row in enumerate(cursor.fetchall(), 1):
                section_id, section_title, level = row
                print(f"  {idx}. ID={section_id}, 標題='{section_title}', 階層={level}")
        else:
            print("⚠️ CrystalDiskMark 5 文檔沒有段落資料！")
            print("   這可能是為什麼 Stage 1 找不到 CrystalDiskMark 的原因")
    
    print(f"\n{'='*80}\n")

if __name__ == '__main__':
    test_stage1_search()
