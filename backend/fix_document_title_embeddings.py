#!/usr/bin/env python
"""
修復文檔標題段落的向量缺失問題

此腳本會：
1. 查詢所有 is_document_title=true 且向量為 NULL 的段落
2. 為每個段落生成 title_embedding 和 content_embedding
3. 更新 document_section_embeddings 表

背景：
- CrystalDiskMark 5 等文檔的標題段落沒有向量
- 導致 Stage 1 搜尋（95% 標題權重）無法找到最佳匹配
- 完美的標題匹配被 SQL 的 WHERE title_embedding IS NOT NULL 過濾掉

修復策略：
- title_embedding: 使用段落的 heading_text
- content_embedding: 使用文檔的前 500 字元（如果沒有內容則使用標題）

執行方式：
    docker exec -it ai-django python fix_document_title_embeddings.py
"""

import os
import sys
import django

# Django 設定
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.services.embedding_service import get_embedding_service
from django.db import connection
import logging

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fix_document_title_embeddings(source_table='protocol_guide'):
    """
    為文檔標題段落生成向量
    
    Args:
        source_table: 來源表名稱 (protocol_guide 或 rvt_guide)
    """
    logger.info(f"🚀 開始修復 {source_table} 的文檔標題段落向量")
    logger.info("=" * 70)
    
    service = get_embedding_service()
    
    # 查詢沒有向量的文檔標題段落
    with connection.cursor() as cursor:
        cursor.execute(f"""
            SELECT 
                dse.id, 
                dse.source_id,
                dse.heading_text,
                COALESCE(pg.content, ''),
                COALESCE(pg.title, dse.heading_text)
            FROM document_section_embeddings dse
            LEFT JOIN {source_table} pg ON pg.id = dse.source_id
            WHERE dse.source_table = %s
              AND dse.is_document_title = true
              AND dse.title_embedding IS NULL
            ORDER BY dse.source_id
        """, [source_table])
        
        sections = cursor.fetchall()
    
    if not sections:
        logger.info(f"✅ {source_table} 沒有需要修復的文檔標題段落")
        logger.info("=" * 70)
        return
    
    logger.info(f"📊 發現 {len(sections)} 個需要修復的文檔標題段落\n")
    
    success_count = 0
    fail_count = 0
    
    for section_id, doc_id, heading_text, content, doc_title in sections:
        try:
            logger.info(f"處理段落 ID={section_id}, 文檔 ID={doc_id}")
            logger.info(f"  📝 標題: '{heading_text}'")
            logger.info(f"  📄 文檔長度: {len(content)} 字元")
            
            # 生成標題向量（使用段落標題）
            title_text = heading_text or doc_title
            logger.info(f"  🔤 生成標題向量: '{title_text}'")
            title_embedding = service.generate_embedding(title_text)
            
            # 生成內容向量（使用文檔前 500 字元或完整內容）
            if content and len(content) > 0:
                # 取前 500 字元（約 1000 tokens，適合 embedding 模型）
                content_preview = content[:500]
                logger.info(f"  📚 生成內容向量: 使用前 {len(content_preview)} 字元")
            else:
                # 如果沒有內容，使用標題
                content_preview = title_text
                logger.info(f"  📚 生成內容向量: 使用標題（文檔無內容）")
            
            content_embedding = service.generate_embedding(content_preview)
            
            # 計算 word_count
            word_count = len(content_preview.split()) if content_preview else 0
            
            # 更新資料庫
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE document_section_embeddings
                    SET title_embedding = %s,
                        content_embedding = %s,
                        word_count = %s,
                        updated_at = NOW()
                    WHERE id = %s
                """, [title_embedding, content_embedding, word_count, section_id])
            
            logger.info(f"  ✅ 成功更新向量")
            logger.info(f"     - title_embedding: 1024 維")
            logger.info(f"     - content_embedding: 1024 維")
            logger.info(f"     - word_count: {word_count}")
            logger.info("")
            success_count += 1
            
        except Exception as e:
            logger.error(f"  ❌ 失敗: 段落 ID={section_id}")
            logger.error(f"     錯誤: {str(e)}")
            logger.error("")
            fail_count += 1
    
    logger.info("=" * 70)
    logger.info(f"📊 修復統計:")
    logger.info(f"   ✅ 成功: {success_count} 個")
    logger.info(f"   ❌ 失敗: {fail_count} 個")
    logger.info(f"   📈 成功率: {success_count/(success_count+fail_count)*100:.1f}%" if (success_count+fail_count) > 0 else "   📈 成功率: N/A")
    logger.info("=" * 70)


def verify_fix(source_table='protocol_guide'):
    """驗證修復結果"""
    logger.info(f"\n🔍 驗證 {source_table} 的修復結果")
    logger.info("=" * 70)
    
    with connection.cursor() as cursor:
        # 檢查是否還有未修復的
        cursor.execute("""
            SELECT COUNT(*)
            FROM document_section_embeddings
            WHERE source_table = %s
              AND is_document_title = true
              AND title_embedding IS NULL
        """, [source_table])
        
        remaining = cursor.fetchone()[0]
        
        if remaining == 0:
            logger.info(f"✅ 所有文檔標題段落都已有向量\n")
        else:
            logger.warning(f"⚠️  還有 {remaining} 個文檔標題段落缺少向量\n")
        
        # 列出所有文檔標題段落的狀態
        cursor.execute("""
            SELECT 
                dse.id,
                dse.source_id,
                dse.heading_text,
                dse.word_count,
                dse.title_embedding IS NOT NULL as has_title_vec,
                dse.content_embedding IS NOT NULL as has_content_vec,
                vector_dims(dse.title_embedding) as title_dims,
                vector_dims(dse.content_embedding) as content_dims
            FROM document_section_embeddings dse
            WHERE dse.source_table = %s
              AND dse.is_document_title = true
            ORDER BY dse.id
        """, [source_table])
        
        results = cursor.fetchall()
        
        if not results:
            logger.info(f"ℹ️  {source_table} 沒有文檔標題段落")
        else:
            logger.info(f"📋 文檔標題段落狀態:")
            logger.info(f"{'ID':<6} {'Doc ID':<8} {'標題':<30} {'Words':<7} {'Title':<7} {'Content':<9} {'Dims':<10} {'狀態':<4}")
            logger.info(f"{'-'*90}")
            
            for row in results:
                section_id, doc_id, title, word_count, has_title, has_content, title_dims, content_dims = row
                title_display = (title[:27] + '...') if len(title) > 30 else title
                dims = f"{title_dims}/{content_dims}" if title_dims and content_dims else "N/A"
                status = "✅" if has_title and has_content else "❌"
                logger.info(
                    f"{section_id:<6} {doc_id:<8} {title_display:<30} {word_count:<7} "
                    f"{str(has_title):<7} {str(has_content):<9} {dims:<10} {status:<4}"
                )
    
    logger.info("=" * 70)


def show_statistics(source_table='protocol_guide'):
    """顯示統計資訊"""
    logger.info(f"\n📊 {source_table} 統計資訊")
    logger.info("=" * 70)
    
    with connection.cursor() as cursor:
        # 總段落數
        cursor.execute("""
            SELECT COUNT(*) 
            FROM document_section_embeddings 
            WHERE source_table = %s
        """, [source_table])
        total_sections = cursor.fetchone()[0]
        
        # 文檔標題段落數
        cursor.execute("""
            SELECT COUNT(*) 
            FROM document_section_embeddings 
            WHERE source_table = %s AND is_document_title = true
        """, [source_table])
        doc_title_sections = cursor.fetchone()[0]
        
        # 有向量的文檔標題段落數
        cursor.execute("""
            SELECT COUNT(*) 
            FROM document_section_embeddings 
            WHERE source_table = %s 
              AND is_document_title = true
              AND title_embedding IS NOT NULL
        """, [source_table])
        doc_title_with_vectors = cursor.fetchone()[0]
        
        logger.info(f"總段落數: {total_sections}")
        logger.info(f"文檔標題段落數: {doc_title_sections}")
        logger.info(f"有向量的文檔標題段落: {doc_title_with_vectors}")
        logger.info(f"向量覆蓋率: {doc_title_with_vectors/doc_title_sections*100:.1f}%" if doc_title_sections > 0 else "向量覆蓋率: N/A")
    
    logger.info("=" * 70)


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("🔧 修復文檔標題段落向量缺失問題")
    print("=" * 70)
    print()
    
    # 修復 protocol_guide
    print("📦 處理 protocol_guide")
    print()
    fix_document_title_embeddings('protocol_guide')
    verify_fix('protocol_guide')
    show_statistics('protocol_guide')
    
    # 修復 rvt_guide
    print("\n" + "=" * 70)
    print("📦 處理 rvt_guide")
    print()
    fix_document_title_embeddings('rvt_guide')
    verify_fix('rvt_guide')
    show_statistics('rvt_guide')
    
    print("\n" + "=" * 70)
    print("✅ 所有知識庫修復完成！")
    print("=" * 70)
    print()
    print("🔍 建議下一步:")
    print("   1. 測試 Stage 1 搜尋: python tests/test_stage1_sql_direct.py")
    print("   2. 檢查搜尋結果中 CrystalDiskMark 5 是否在 top 3")
    print("   3. 驗證相似度是否 > 0.90")
    print()
