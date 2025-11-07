#!/usr/bin/env python
"""
為 CrystalDiskMark 5 文檔生成段落向量
"""

import os
import sys
import django

# 設定 Django 環境
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.models import ProtocolGuide
from library.protocol_guide import ProtocolGuideVectorService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_section_vectors_for_crystaldiskmark():
    """為 CrystalDiskMark 5 文檔生成段落向量"""
    
    try:
        # 獲取文檔
        doc = ProtocolGuide.objects.get(id=16, title='CrystalDiskMark 5')
        logger.info(f"✅ 找到文檔: {doc.title} (ID: {doc.id})")
        logger.info(f"   內容長度: {len(doc.content)} 字元")
        
        # 初始化向量服務
        vector_service = ProtocolGuideVectorService()
        
        # 生成段落向量
        logger.info("🔄 開始生成段落向量...")
        result = vector_service.generate_and_store_section_vectors(doc)
        
        if result:
            logger.info(f"✅ 成功生成段落向量！")
            logger.info(f"   生成的段落數: {result.get('section_count', 'N/A')}")
        else:
            logger.error("❌ 段落向量生成失敗")
            
    except ProtocolGuide.DoesNotExist:
        logger.error("❌ 找不到 CrystalDiskMark 5 文檔（ID: 16）")
    except Exception as e:
        logger.error(f"❌ 錯誤: {str(e)}", exc_info=True)


if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("為 CrystalDiskMark 5 生成段落向量")
    logger.info("=" * 60)
    generate_section_vectors_for_crystaldiskmark()
    logger.info("=" * 60)
    logger.info("完成！")
    logger.info("=" * 60)
