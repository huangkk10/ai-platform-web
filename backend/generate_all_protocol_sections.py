#!/usr/bin/env python
"""
為所有 Protocol Guide 生成段落向量（簡化版）
"""
import os
import sys
import django

# 設定 Django 環境
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.models import ProtocolGuide
from library.common.knowledge_base.section_vectorization_service import SectionVectorizationService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """為所有 Protocol Guide 生成段落向量"""
    
    logger.info("=" * 70)
    logger.info("🚀 Protocol Guide 段落向量批量生成")
    logger.info("=" * 70)
    
    # 初始化服務
    service = SectionVectorizationService()
    
    # 獲取所有 Protocol Guide
    guides = ProtocolGuide.objects.all().order_by('id')
    total_guides = guides.count()
    
    logger.info(f"📊 找到 {total_guides} 篇 Protocol Guide")
    logger.info("")
    
    if total_guides == 0:
        logger.warning("⚠️  沒有找到任何 Protocol Guide")
        return
    
    # 統計
    success_count = 0
    fail_count = 0
    total_sections = 0
    
    # 處理每篇文檔
    for i, guide in enumerate(guides, 1):
        logger.info(f"\n{'='*70}")
        logger.info(f"📝 [{i}/{total_guides}] ID: {guide.id} - {guide.title}")
        logger.info(f"{'='*70}")
        logger.info(f"內容長度: {len(guide.content) if guide.content else 0} 字元")
        
        try:
            # 生成段落向量
            logger.info("⏳ 開始生成段落向量...")
            
            result = service.vectorize_document_sections(
                source_table='protocol_guide',
                source_id=guide.id,
                markdown_content=guide.content,
                document_title=guide.title
            )
            
            if result['success']:
                section_count = result.get('vectorized_count', 0)
                logger.info(f"✅ 成功生成 {section_count} 個段落向量")
                success_count += 1
                total_sections += section_count
            else:
                error = result.get('error', '未知錯誤')
                logger.error(f"❌ 生成失敗: {error}")
                fail_count += 1
                
        except Exception as e:
            logger.error(f"❌ 處理失敗: {str(e)}", exc_info=True)
            fail_count += 1
    
    # 最終統計
    logger.info("\n" + "=" * 70)
    logger.info("📊 生成結果統計")
    logger.info("=" * 70)
    logger.info(f"✅ 成功: {success_count}/{total_guides} 篇")
    logger.info(f"❌ 失敗: {fail_count}/{total_guides} 篇")
    logger.info(f"📄 總共生成: {total_sections} 個段落")
    logger.info("=" * 70)
    
    if success_count > 0:
        logger.info("")
        logger.info("🎉 段落向量生成完成！")
        logger.info("")
        logger.info("💡 下一步：")
        logger.info("   1. 測試搜尋 'crystaldiskmark 5'")
        logger.info("   2. 應該可以找到 CrystalDiskMark 5 文檔了")
        logger.info("")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("\n⚠️  使用者中斷")
    except Exception as e:
        logger.error(f"\n❌ 執行失敗: {str(e)}", exc_info=True)
