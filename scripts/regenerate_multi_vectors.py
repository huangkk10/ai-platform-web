"""
多向量資料遷移腳本

為所有現有資料重新生成標題和內容向量
"""

import os
import sys
import django

# Django 設定
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.models import ProtocolGuide, RVTGuide
from library.protocol_guide.vector_service import ProtocolGuideVectorService
from library.rvt_guide.vector_service import RVTGuideVectorService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def regenerate_protocol_vectors():
    """重新生成 Protocol Guide 向量"""
    logger.info("=" * 60)
    logger.info("開始重新生成 Protocol Guide 向量")
    logger.info("=" * 60)
    
    service = ProtocolGuideVectorService()
    guides = ProtocolGuide.objects.all()
    
    total = guides.count()
    success_count = 0
    failed_count = 0
    
    for i, guide in enumerate(guides, 1):
        logger.info(f"\n[{i}/{total}] 處理: {guide.title[:50]}...")
        
        try:
            if service.generate_and_store_vector(guide, action='migration'):
                success_count += 1
                logger.info(f"✅ 成功")
            else:
                failed_count += 1
                logger.error(f"❌ 失敗")
        except Exception as e:
            failed_count += 1
            logger.error(f"❌ 異常: {str(e)}")
    
    logger.info("\n" + "=" * 60)
    logger.info(f"Protocol Guide 遷移完成: 成功 {success_count}, 失敗 {failed_count}")
    logger.info("=" * 60)
    
    return success_count, failed_count


def regenerate_rvt_vectors():
    """重新生成 RVT Guide 向量"""
    logger.info("\n" + "=" * 60)
    logger.info("開始重新生成 RVT Guide 向量")
    logger.info("=" * 60)
    
    service = RVTGuideVectorService()
    guides = RVTGuide.objects.all()
    
    total = guides.count()
    success_count = 0
    failed_count = 0
    
    for i, guide in enumerate(guides, 1):
        logger.info(f"\n[{i}/{total}] 處理: {guide.title[:50]}...")
        
        try:
            if service.generate_and_store_vector(guide, action='migration'):
                success_count += 1
                logger.info(f"✅ 成功")
            else:
                failed_count += 1
                logger.error(f"❌ 失敗")
        except Exception as e:
            failed_count += 1
            logger.error(f"❌ 異常: {str(e)}")
    
    logger.info("\n" + "=" * 60)
    logger.info(f"RVT Guide 遷移完成: 成功 {success_count}, 失敗 {failed_count}")
    logger.info("=" * 60)
    
    return success_count, failed_count


def verify_migration():
    """驗證遷移結果"""
    from django.db import connection
    
    logger.info("\n" + "=" * 60)
    logger.info("驗證遷移結果")
    logger.info("=" * 60)
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                source_table,
                COUNT(*) as total,
                COUNT(title_embedding) as has_title,
                COUNT(content_embedding) as has_content,
                COUNT(CASE WHEN title_embedding IS NOT NULL AND content_embedding IS NOT NULL THEN 1 END) as complete
            FROM document_embeddings
            GROUP BY source_table
            ORDER BY source_table;
        """)
        
        results = cursor.fetchall()
        
        logger.info("\n向量統計：")
        logger.info(f"{'來源表':<20} {'總數':<10} {'有標題':<10} {'有內容':<10} {'完整':<10}")
        logger.info("-" * 60)
        
        for row in results:
            source_table, total, has_title, has_content, complete = row
            logger.info(f"{source_table:<20} {total:<10} {has_title:<10} {has_content:<10} {complete:<10}")
        
        # 檢查完整性
        cursor.execute("""
            SELECT COUNT(*) 
            FROM document_embeddings 
            WHERE title_embedding IS NULL OR content_embedding IS NULL;
        """)
        incomplete_count = cursor.fetchone()[0]
        
        if incomplete_count > 0:
            logger.warning(f"\n⚠️ 警告：有 {incomplete_count} 筆記錄的向量不完整")
            return False
        else:
            logger.info(f"\n✅ 所有向量都已完整生成")
            return True


if __name__ == '__main__':
    try:
        # 重新生成 Protocol Guide 向量
        protocol_success, protocol_failed = regenerate_protocol_vectors()
        
        # 重新生成 RVT Guide 向量
        rvt_success, rvt_failed = regenerate_rvt_vectors()
        
        # 驗證結果
        is_complete = verify_migration()
        
        # 總結
        logger.info("\n" + "=" * 60)
        logger.info("遷移總結")
        logger.info("=" * 60)
        logger.info(f"Protocol Guide: 成功 {protocol_success}, 失敗 {protocol_failed}")
        logger.info(f"RVT Guide: 成功 {rvt_success}, 失敗 {rvt_failed}")
        logger.info(f"總計: 成功 {protocol_success + rvt_success}, 失敗 {protocol_failed + rvt_failed}")
        logger.info(f"遷移狀態: {'✅ 完成' if is_complete and protocol_failed == 0 and rvt_failed == 0 else '❌ 有錯誤'}")
        logger.info("=" * 60)
        
        sys.exit(0 if is_complete and protocol_failed == 0 and rvt_failed == 0 else 1)
        
    except Exception as e:
        logger.error(f"\n❌ 遷移失敗: {str(e)}", exc_info=True)
        sys.exit(1)
