#!/usr/bin/env python
"""
重新生成段落的多向量（title_embedding + content_embedding）
"""

import os
import sys
import django

# 設定 Django 環境
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from django.db import connection
from api.services.embedding_service import get_embedding_service
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def regenerate_section_multi_vectors():
    """重新生成所有段落的多向量"""
    
    # 初始化 embedding service
    embedding_service = get_embedding_service('ultra_high')  # 1024 維
    
    # 獲取所有段落（包含文件標題）
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT dse.id, dse.source_table, dse.source_id, dse.section_id, 
                   dse.heading_text, dse.content,
                   CASE 
                       WHEN dse.source_table = 'protocol_guide' THEN pg.title
                       WHEN dse.source_table = 'rvt_guide' THEN rg.title
                       ELSE NULL
                   END as doc_title
            FROM document_section_embeddings dse
            LEFT JOIN protocol_guide pg ON dse.source_table = 'protocol_guide' AND pg.id = dse.source_id
            LEFT JOIN rvt_guide rg ON dse.source_table = 'rvt_guide' AND rg.id = dse.source_id
            ORDER BY dse.source_table, dse.source_id, dse.id;
        """)
        
        sections = cursor.fetchall()
        total = len(sections)
        
        logger.info(f"📊 找到 {total} 個段落需要生成多向量")
    
    success_count = 0
    fail_count = 0
    
    for idx, (section_id, source_table, source_id, section_id_str, heading_text, content, doc_title) in enumerate(sections, 1):
        try:
            # 生成標題向量（包含文件標題）
            if doc_title and heading_text:
                title_text = f"{doc_title} - {heading_text}"
            elif doc_title:
                title_text = doc_title
            elif heading_text:
                title_text = heading_text
            else:
                title_text = ""
            
            title_embedding = embedding_service.generate_embedding(title_text) if title_text else None
            
            # 生成內容向量
            content_text = content or ""
            content_embedding = embedding_service.generate_embedding(content_text) if content_text else None
            
            # 更新資料庫
            if title_embedding is not None and content_embedding is not None:
                title_embedding_str = '[' + ','.join(map(str, title_embedding)) + ']'
                content_embedding_str = '[' + ','.join(map(str, content_embedding)) + ']'
                
                with connection.cursor() as cursor:
                    cursor.execute("""
                        UPDATE document_section_embeddings
                        SET title_embedding = %s::vector,
                            content_embedding = %s::vector,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s;
                    """, [title_embedding_str, content_embedding_str, section_id])
                
                success_count += 1
                
                if idx % 10 == 0:
                    logger.info(f"✅ 進度: {idx}/{total} ({success_count} 成功, {fail_count} 失敗)")
            else:
                fail_count += 1
                logger.warning(f"⚠️ 段落 {section_id} 缺少標題或內容")
        
        except Exception as e:
            fail_count += 1
            logger.error(f"❌ 段落 {section_id} 處理失敗: {str(e)}")
    
    logger.info("=" * 60)
    logger.info(f"🎉 多向量生成完成！")
    logger.info(f"   總計: {total} 個段落")
    logger.info(f"   成功: {success_count} 個")
    logger.info(f"   失敗: {fail_count} 個")
    logger.info("=" * 60)


if __name__ == '__main__':
    regenerate_section_multi_vectors()
