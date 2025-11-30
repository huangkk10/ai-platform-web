#!/usr/bin/env python
"""
為 Cup 文檔重新生成段落向量
"""

import os
import sys
import django

# 設定 Django 環境
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.models import ProtocolGuide
from api.services.embedding_service import get_embedding_service
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def regenerate_cup_sections():
    """為 Cup 文檔重新生成段落向量"""
    
    try:
        # 獲取 Cup 文檔
        doc = ProtocolGuide.objects.get(title='Cup')
        logger.info(f"✅ 找到文檔: {doc.title} (ID: {doc.id})")
        logger.info(f"   內容長度: {len(doc.content)} 字元")
        logger.info(f"   內容前 200 字元:\n{doc.content[:200]}")
        logger.info("")
        
        # 初始化 embedding service
        embedding_service = get_embedding_service()
        
        # 刪除舊的段落向量
        logger.info("🗑️  刪除舊的段落向量...")
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute('''
                DELETE FROM document_section_embeddings 
                WHERE source_table = 'protocol_guide' AND source_id = %s
            ''', [doc.id])
            deleted_count = cursor.rowcount
            logger.info(f"   已刪除 {deleted_count} 個舊段落向量")
        
        # 生成新的段落向量
        logger.info("")
        logger.info("🔄 開始生成新的段落向量...")
        
        # 使用 generate_multi_vector_embeddings 方法
        result = embedding_service.generate_multi_vector_embeddings(
            source_table='protocol_guide',
            source_id=doc.id,
            title=doc.title,
            content=doc.content
        )
        
        if result['success']:
            logger.info(f"✅ 成功生成段落向量！")
            logger.info(f"   生成的段落數: {result.get('total_sections', 'N/A')}")
            
            # 驗證新資料
            with connection.cursor() as cursor:
                cursor.execute('''
                    SELECT heading_text, LENGTH(content) as content_length
                    FROM document_section_embeddings
                    WHERE source_table = 'protocol_guide' AND source_id = %s
                    ORDER BY section_id
                    LIMIT 20
                ''', [doc.id])
                
                results = cursor.fetchall()
                logger.info("")
                logger.info(f"📊 新段落列表（共 {len(results)} 個）:")
                for i, (heading, length) in enumerate(results[:15], 1):
                    heading_text = heading or '(標題)'
                    length_text = length if length else 0
                    logger.info(f"   {i}. {heading_text}: {length_text} 字元")
                if len(results) > 15:
                    logger.info(f"   ... 還有 {len(results) - 15} 個段落")
        else:
            logger.error(f"❌ 段落向量生成失敗: {result.get('error', '未知錯誤')}")
            
    except ProtocolGuide.DoesNotExist:
        logger.error("❌ 找不到 Cup 文檔")
    except Exception as e:
        logger.error(f"❌ 錯誤: {str(e)}", exc_info=True)


if __name__ == '__main__':
    logger.info("=" * 80)
    logger.info("為 Cup 文檔重新生成段落向量")
    logger.info("=" * 80)
    logger.info("")
    regenerate_cup_sections()
    logger.info("")
    logger.info("=" * 80)
    logger.info("完成！")
    logger.info("=" * 80)
