#!/usr/bin/env python
"""
測試方案 B：文檔標題段落自動創建

此腳本會：
1. 在 Protocol Guide 中新增一篇測試文章
2. 檢查 document_section_embeddings 表中是否自動生成了文檔標題段落
3. 驗證文檔標題段落的特徵：
   - section_id = 'doc_{id}'
   - heading_level = 0
   - is_document_title = true
   - title_embedding 和 content_embedding 不為 NULL
   - 向量維度為 1024

執行方式：
    docker exec -it ai-django python test_document_title_section_auto_creation.py
"""

import os
import sys
import django

# Django 設定
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.models import ProtocolGuide
from django.db import connection
from django.contrib.auth import get_user_model
import logging

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

User = get_user_model()


def test_auto_create_document_title_section():
    """測試文檔標題段落自動創建"""
    
    print("\n" + "=" * 70)
    print("🧪 測試方案 B：文檔標題段落自動創建")
    print("=" * 70)
    print()
    
    # 步驟 1：創建測試文章
    print("📝 步驟 1：創建測試文章")
    print("-" * 70)
    
    try:
        # 獲取或創建測試用戶
        user = User.objects.filter(username='admin').first()
        if not user:
            user = User.objects.create_user(
                username='test_user',
                email='test@example.com',
                password='test123'
            )
            logger.info("✅ 創建測試用戶: test_user")
        else:
            logger.info(f"✅ 使用現有用戶: {user.username}")
        
        # 創建測試文章
        test_title = "方案B測試 - 文檔標題段落自動生成測試"
        test_content = """# 測試標題 1

這是第一個段落的內容。

## 測試標題 2

這是第二個段落的內容。

### 測試標題 3

這是第三個段落的內容，包含更多細節。
"""
        
        guide = ProtocolGuide.objects.create(
            title=test_title,
            content=test_content
        )
        
        logger.info(f"✅ 測試文章創建成功")
        logger.info(f"   - ID: {guide.id}")
        logger.info(f"   - 標題: {guide.title}")
        logger.info(f"   - 內容長度: {len(guide.content)} 字元")
        print()
        
    except Exception as e:
        logger.error(f"❌ 創建測試文章失敗: {str(e)}")
        return
    
    # 步驟 2：等待向量生成（給系統一點時間）
    print("⏳ 步驟 2：等待向量生成...")
    print("-" * 70)
    import time
    time.sleep(3)
    logger.info("✅ 等待完成")
    print()
    
    # 步驟 3：檢查文檔標題段落
    print("🔍 步驟 3：檢查文檔標題段落")
    print("-" * 70)
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                id,
                section_id,
                heading_level,
                heading_text,
                is_document_title,
                LENGTH(content) as content_len,
                title_embedding IS NOT NULL as has_title_vec,
                content_embedding IS NOT NULL as has_content_vec,
                vector_dims(title_embedding) as title_dims,
                vector_dims(content_embedding) as content_dims
            FROM document_section_embeddings
            WHERE source_table = 'protocol_guide'
              AND source_id = %s
              AND is_document_title = true
        """, [guide.id])
        
        doc_title_section = cursor.fetchone()
    
    if not doc_title_section:
        logger.error(f"❌ 未找到文檔標題段落！")
        logger.error(f"   檢查點：")
        logger.error(f"   - 是否自動調用了 SectionVectorizationService？")
        logger.error(f"   - perform_create 方法是否正確傳遞了 document_title？")
        logger.error(f"   - _store_document_title_section 方法是否被執行？")
        
        # 列出該文檔的所有段落
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    section_id,
                    heading_level,
                    heading_text,
                    is_document_title
                FROM document_section_embeddings
                WHERE source_table = 'protocol_guide'
                  AND source_id = %s
                ORDER BY id
            """, [guide.id])
            
            all_sections = cursor.fetchall()
            
            if all_sections:
                logger.info(f"\n📋 該文檔的所有段落：")
                for sec in all_sections:
                    logger.info(f"   - section_id={sec[0]}, level={sec[1]}, title='{sec[2]}', is_doc_title={sec[3]}")
            else:
                logger.warning(f"⚠️  該文檔完全沒有段落向量！")
        
        print()
        return
    
    # 解析結果
    (
        section_id_db, section_id, heading_level, heading_text, is_doc_title,
        content_len, has_title_vec, has_content_vec, title_dims, content_dims
    ) = doc_title_section
    
    logger.info(f"✅ 找到文檔標題段落！")
    logger.info(f"   - 段落 ID (DB): {section_id_db}")
    logger.info(f"   - section_id: {section_id} {'✅ 正確' if section_id == f'doc_{guide.id}' else '❌ 錯誤'}")
    logger.info(f"   - heading_level: {heading_level} {'✅ 正確' if heading_level == 0 else '❌ 錯誤'}")
    logger.info(f"   - heading_text: '{heading_text}'")
    logger.info(f"   - is_document_title: {is_doc_title} {'✅ 正確' if is_doc_title else '❌ 錯誤'}")
    logger.info(f"   - content 長度: {content_len} 字元")
    logger.info(f"   - has_title_embedding: {has_title_vec} {'✅' if has_title_vec else '❌'}")
    logger.info(f"   - has_content_embedding: {has_content_vec} {'✅' if has_content_vec else '❌'}")
    logger.info(f"   - title_embedding 維度: {title_dims} {'✅ 正確' if title_dims == 1024 else '❌ 錯誤'}")
    logger.info(f"   - content_embedding 維度: {content_dims} {'✅ 正確' if content_dims == 1024 else '❌ 錯誤'}")
    print()
    
    # 步驟 4：檢查其他段落
    print("📊 步驟 4：統計所有段落")
    print("-" * 70)
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE is_document_title = true) as doc_title_count,
                COUNT(*) FILTER (WHERE is_document_title = false) as regular_count
            FROM document_section_embeddings
            WHERE source_table = 'protocol_guide'
              AND source_id = %s
        """, [guide.id])
        
        stats = cursor.fetchone()
        total, doc_title_count, regular_count = stats
    
    logger.info(f"總段落數: {total}")
    logger.info(f"  - 文檔標題段落: {doc_title_count} {'✅' if doc_title_count == 1 else '❌ 應該為 1'}")
    logger.info(f"  - 一般段落: {regular_count}")
    print()
    
    # 步驟 5：測試搜尋功能
    print("🔍 步驟 5：測試 Stage 1 搜尋")
    print("-" * 70)
    
    query = "方案B測試"
    logger.info(f"查詢: '{query}'")
    
    with connection.cursor() as cursor:
        # 生成查詢向量
        from api.services.embedding_service import get_embedding_service
        service = get_embedding_service()
        query_embedding = service.generate_embedding(query)
        query_embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
        
        # 執行 Stage 1 搜尋（95% 標題權重）
        cursor.execute("""
            WITH scored_sections AS (
                SELECT 
                    id,
                    section_id,
                    heading_text,
                    is_document_title,
                    (1 - (title_embedding <=> %s::vector)) AS title_similarity,
                    (1 - (content_embedding <=> %s::vector)) AS content_similarity,
                    (
                        0.95 * (1 - (title_embedding <=> %s::vector)) +
                        0.05 * (1 - (content_embedding <=> %s::vector))
                    ) AS weighted_similarity
                FROM document_section_embeddings
                WHERE source_table = 'protocol_guide'
                  AND source_id = %s
                  AND title_embedding IS NOT NULL
                  AND content_embedding IS NOT NULL
            )
            SELECT 
                section_id,
                heading_text,
                is_document_title,
                ROUND((title_similarity * 100)::numeric, 2) as title_pct,
                ROUND((content_similarity * 100)::numeric, 2) as content_pct,
                ROUND((weighted_similarity * 100)::numeric, 2) as weighted_pct
            FROM scored_sections
            ORDER BY weighted_similarity DESC
            LIMIT 5;
        """, [query_embedding_str, query_embedding_str, query_embedding_str, query_embedding_str, guide.id])
        
        results = cursor.fetchall()
    
    if not results:
        logger.warning("⚠️  搜尋無結果")
    else:
        logger.info(f"✅ 搜尋結果 (Top {len(results)}):")
        logger.info(f"{'排名':<6} {'section_id':<15} {'標題':<30} {'是否文檔標題':<12} {'標題%':<8} {'內容%':<8} {'加權%':<8}")
        logger.info("-" * 100)
        
        for i, row in enumerate(results, 1):
            result_section_id, heading, is_doc, title_pct, content_pct, weighted_pct = row
            heading_display = (heading[:27] + '...') if len(heading) > 30 else heading
            doc_title_mark = "✅ 是" if is_doc else "否"
            
            logger.info(
                f"{i:<6} {result_section_id:<15} {heading_display:<30} {doc_title_mark:<12} "
                f"{title_pct:<8} {content_pct:<8} {weighted_pct:<8}"
            )
        
        # 檢查文檔標題段落是否排名第一
        first_result = results[0]
        if first_result[2]:  # is_document_title
            logger.info("\n✅ 文檔標題段落排名第一！搜尋品質正常。")
        else:
            logger.warning("\n⚠️  文檔標題段落未排名第一，可能需要調整權重。")
    
    print()
    
    # 最終總結
    print("=" * 70)
    print("📊 測試總結")
    print("=" * 70)
    
    # 檢查所有條件
    all_passed = True
    checks = [
        ("文檔標題段落存在", doc_title_section is not None),
        ("section_id 格式正確", section_id == f'doc_{guide.id}'),
        ("heading_level 為 0", heading_level == 0),
        ("is_document_title 為 true", is_doc_title),
        ("title_embedding 存在", has_title_vec),
        ("content_embedding 存在", has_content_vec),
        ("title_embedding 維度 1024", title_dims == 1024),
        ("content_embedding 維度 1024", content_dims == 1024),
        ("只有一個文檔標題段落", doc_title_count == 1),
        ("搜尋結果存在", len(results) > 0 if results else False)
    ]
    
    for check_name, passed in checks:
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status} - {check_name}")
        if not passed:
            all_passed = False
    
    print()
    
    if all_passed:
        logger.info("🎉 方案 B 測試完全成功！")
        logger.info("   - 新增文章時自動創建文檔標題段落 ✅")
        logger.info("   - 文檔標題段落包含完整向量 ✅")
        logger.info("   - Stage 1 搜尋品質正常 ✅")
    else:
        logger.warning("⚠️  方案 B 測試部分失敗，請檢查上述 FAIL 項目。")
    
    print("=" * 70)
    print()
    
    # 自動清理測試數據
    logger.info(f"🧹 自動清理測試文章 (ID={guide.id})")
    guide.delete()
    logger.info(f"✅ 測試文章已刪除")


if __name__ == '__main__':
    test_auto_create_document_title_section()
