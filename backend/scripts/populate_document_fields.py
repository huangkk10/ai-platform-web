import sys, os, django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from django.db import connection, transaction
from api.models import ProtocolGuide
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def populate_document_fields():
    logger.info("=" * 80)
    logger.info("開始填充文檔層級欄位")
    logger.info("=" * 80)
    
    with connection.cursor() as cursor:
        guides = ProtocolGuide.objects.all()
        total_guides = guides.count()
        
        logger.info(f"\n📊 找到 {total_guides} 個 Protocol Guide 記錄\n")
        
        if total_guides == 0:
            logger.warning("⚠️  沒有找到任何 Protocol Guide 記錄")
            return
        
        # 步驟 1: 更新現有 section 的文檔資訊
        logger.info("步驟 1: 更新現有 section 的文檔資訊")
        logger.info("-" * 80)
        
        updated_count = 0
        for guide in guides:
            guide_id = guide.id
            guide_title = guide.title
            doc_id = f"doc_{guide_id}"
            
            cursor.execute("""
                UPDATE document_section_embeddings
                SET document_id = %s, document_title = %s
                WHERE source_table = 'protocol_guide'
                    AND source_id = %s
                    AND (document_id IS NULL OR document_id = '')
            """, [doc_id, guide_title, guide_id])
            
            rows_updated = cursor.rowcount
            updated_count += rows_updated
            
            if rows_updated > 0:
                logger.info(f"✅ Guide {guide_id}: 更新 {rows_updated} 個 sections - {guide_title[:50]}...")
            else:
                logger.info(f"⚪ Guide {guide_id}: 已有資料，跳過 - {guide_title[:50]}...")
        
        logger.info(f"\n✅ 步驟 1 完成：共更新 {updated_count} 個 section 記錄\n")
        
        # 步驟 2: 創建文檔標題記錄
        logger.info("步驟 2: 創建文檔標題記錄（Level 0）")
        logger.info("-" * 80)
        
        created_count = 0
        for guide in guides:
            guide_id = guide.id
            guide_title = guide.title
            doc_id = f"doc_{guide_id}"
            
            cursor.execute("""
                SELECT COUNT(*) FROM document_section_embeddings
                WHERE document_id = %s AND is_document_title = TRUE
            """, [doc_id])
            
            if cursor.fetchone()[0] == 0:
                try:
                    from api.services.embedding_service import get_embedding_service
                    service = get_embedding_service()
                    
                    logger.info(f"   生成向量: {guide_title[:50]}...")
                    title_embedding = service.generate_embedding(guide_title)
                    
                    cursor.execute("""
                        INSERT INTO document_section_embeddings 
                        (source_table, source_id, document_id, document_title, 
                         is_document_title, section_id, heading_text, content, 
                         embedding, heading_level, parent_section_id, created_at)
                        VALUES 
                        (%s, %s, %s, %s, TRUE, %s, %s, %s, %s, 0, NULL, NOW())
                    """, [
                        'protocol_guide', guide_id, doc_id, guide_title,
                        doc_id, guide_title, guide_title, title_embedding
                    ])
                    
                    created_count += 1
                    logger.info(f"✅ Guide {guide_id}: 創建文檔標題記錄 - {guide_title[:50]}...")
                    
                except Exception as e:
                    logger.error(f"❌ Guide {guide_id}: 創建失敗 - {str(e)}")
                    raise
            else:
                logger.info(f"⚪ Guide {guide_id}: 文檔標題記錄已存在，跳過")
        
        logger.info(f"\n✅ 步驟 2 完成：創建 {created_count} 個文檔標題記錄\n")
        
        # 驗證資料
        logger.info("=" * 80)
        logger.info("資料填充完成")
        logger.info("=" * 80)
        logger.info(f"📊 總覽：")
        logger.info(f"   - 處理的 Protocol Guides: {total_guides}")
        logger.info(f"   - 更新的 Section 記錄: {updated_count}")
        logger.info(f"   - 創建的文檔標題記錄: {created_count}")
        
        cursor.execute("""
            SELECT COUNT(*) as total,
                   COUNT(DISTINCT document_id) as unique_docs,
                   SUM(CASE WHEN is_document_title THEN 1 ELSE 0 END) as doc_titles
            FROM document_section_embeddings
            WHERE source_table = 'protocol_guide'
        """)
        
        result = cursor.fetchone()
        logger.info(f"\n📈 驗證結果：")
        logger.info(f"   - 總記錄數: {result[0]}")
        logger.info(f"   - 唯一文檔數: {result[1]}")
        logger.info(f"   - 文檔標題記錄: {result[2]}")
        logger.info("=" * 80)

if __name__ == '__main__':
    try:
        with transaction.atomic():
            populate_document_fields()
            logger.info("\n✅ 所有操作已成功提交到資料庫")
    except Exception as e:
        logger.error(f"\n❌ 執行失敗：{str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
