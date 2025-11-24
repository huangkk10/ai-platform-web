#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修復現有向量的 document_id 和 document_title 欄位
==================================================

問題：舊的向量記錄缺少 document_id 和 document_title
影響：無法使用 _expand_to_full_document() 功能
"""

import os
import sys
import django

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from django.db import connection


def fix_document_ids():
    """修復所有缺少 document_id 的記錄"""
    
    print("=" * 80)
    print("🔧 修復 document_id 和 document_title 欄位")
    print("=" * 80)
    print()
    
    # 步驟 1：檢查需要修復的記錄數
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                source_table,
                COUNT(*) as count
            FROM document_section_embeddings
            WHERE document_id IS NULL OR document_id = ''
            GROUP BY source_table;
        """)
        
        results = cursor.fetchall()
        
        if not results:
            print("✅ 沒有需要修復的記錄")
            return
        
        total = sum(row[1] for row in results)
        print(f"需要修復的記錄:")
        for source_table, count in results:
            print(f"  - {source_table}: {count} 筆")
        print(f"  總計: {total} 筆")
        print()
    
    # 步驟 2：批量修復（設定 document_id）
    print("開始修復...")
    fixed_count = 0
    
    with connection.cursor() as cursor:
        # 對每個 source_table 分別處理
        for source_table, _ in results:
            # 從對應的 source table 查詢標題
            if source_table == 'protocol_guide':
                cursor.execute("""
                    UPDATE document_section_embeddings dse
                    SET 
                        document_id = CONCAT(%s, '_', dse.source_id::text),
                        document_title = pg.title
                    FROM protocol_guide pg
                    WHERE dse.source_table = %s
                        AND dse.source_id = pg.id
                        AND (dse.document_id IS NULL OR dse.document_id = '');
                """, [source_table, source_table])
                
            elif source_table == 'rvt_guide':
                cursor.execute("""
                    UPDATE document_section_embeddings dse
                    SET 
                        document_id = CONCAT(%s, '_', dse.source_id::text),
                        document_title = rg.title
                    FROM rvt_guide rg
                    WHERE dse.source_table = %s
                        AND dse.source_id = rg.id
                        AND (dse.document_id IS NULL OR dse.document_id = '');
                """, [source_table, source_table])
            
            else:
                # 其他 source_table：只設定 document_id，不設定 document_title
                cursor.execute("""
                    UPDATE document_section_embeddings
                    SET document_id = CONCAT(%s, '_', source_id::text)
                    WHERE source_table = %s
                        AND (document_id IS NULL OR document_id = '');
                """, [source_table, source_table])
            
            updated = cursor.rowcount
            fixed_count += updated
            print(f"  ✅ {source_table}: 修復 {updated} 筆")
    
    print()
    print(f"✅ 修復完成！總計 {fixed_count} 筆記錄")
    print()
    
    # 步驟 3：驗證修復結果
    print("驗證修復結果:")
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                source_table,
                COUNT(*) as total,
                COUNT(document_id) as has_doc_id,
                COUNT(document_title) as has_doc_title
            FROM document_section_embeddings
            GROUP BY source_table;
        """)
        
        results = cursor.fetchall()
        for source_table, total, has_doc_id, has_doc_title in results:
            doc_id_percent = (has_doc_id / total * 100) if total > 0 else 0
            doc_title_percent = (has_doc_title / total * 100) if total > 0 else 0
            print(f"  {source_table}:")
            print(f"    - 總計: {total} 筆")
            print(f"    - 有 document_id: {has_doc_id} ({doc_id_percent:.1f}%)")
            print(f"    - 有 document_title: {has_doc_title} ({doc_title_percent:.1f}%)")
    
    print()
    print("=" * 80)


if __name__ == '__main__':
    fix_document_ids()
