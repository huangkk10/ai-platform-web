#!/usr/bin/env python
"""
文檔級搜尋功能測試腳本
============================================================
測試目標：
1. SOP 查詢 → 返回完整文檔（2000+ 字元）
2. 普通查詢 → 返回 section 級結果
3. 驗證 document_id 和 document_title 正確填充
============================================================
"""

import sys
import os
import django

# Django setup
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from library.protocol_guide.search_service import ProtocolGuideSearchService
import logging

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_sop_query():
    """測試 1: SOP 查詢應該返回完整文檔"""
    logger.info("\n" + "=" * 80)
    logger.info("測試 1: SOP 查詢（應返回完整文檔）")
    logger.info("=" * 80)
    
    service = ProtocolGuideSearchService()
    
    # 測試查詢
    queries = [
        "IOL 放測 SOP",
        "UNH-IOL SOP",
        "IOL 操作流程",
    ]
    
    for query in queries:
        logger.info(f"\n🔍 查詢: '{query}'")
        logger.info("-" * 80)
        
        results = service.search_knowledge(
            query=query,
            limit=3,
            threshold=0.5,
            use_vector=True
        )
        
        if not results:
            logger.warning(f"❌ 沒有找到結果")
            continue
        
        # 檢查結果
        for i, result in enumerate(results, 1):
            metadata = result.get('metadata', {})
            content = result.get('content', '')
            content_length = len(content)
            
            logger.info(f"\n結果 {i}:")
            logger.info(f"  📄 文檔標題: {metadata.get('document_title', 'N/A')}")
            logger.info(f"  🆔 文檔 ID: {metadata.get('document_id', 'N/A')}")
            logger.info(f"  🎯 分數: {result.get('score', 0):.4f}")
            logger.info(f"  📏 內容長度: {content_length} 字元")
            logger.info(f"  📦 是否完整文檔: {metadata.get('is_full_document', False)}")
            logger.info(f"  📑 包含 Sections: {metadata.get('sections_count', 'N/A')}")
            
            # 顯示內容預覽
            preview = content[:200] if content_length > 200 else content
            logger.info(f"  📝 內容預覽:\n{preview}...")
            
            # 驗證
            if metadata.get('is_full_document'):
                if content_length >= 2000:
                    logger.info(f"  ✅ 通過：完整文檔，長度 >= 2000 字元")
                else:
                    logger.warning(f"  ⚠️  警告：完整文檔但長度 < 2000 字元")
            else:
                logger.warning(f"  ❌ 失敗：應該返回完整文檔，但返回的是 section")


def test_regular_query():
    """測試 2: 普通查詢應該返回 section 級結果"""
    logger.info("\n" + "=" * 80)
    logger.info("測試 2: 普通查詢（應返回 section 級結果）")
    logger.info("=" * 80)
    
    service = ProtocolGuideSearchService()
    
    # 測試查詢
    queries = [
        "網路設定",
        "USB 安裝",
        "初始化步驟",
    ]
    
    for query in queries:
        logger.info(f"\n🔍 查詢: '{query}'")
        logger.info("-" * 80)
        
        results = service.search_knowledge(
            query=query,
            limit=3,
            threshold=0.5,
            use_vector=True
        )
        
        if not results:
            logger.warning(f"⚪ 沒有找到結果（正常，可能該主題沒有相關文檔）")
            continue
        
        # 檢查結果
        for i, result in enumerate(results, 1):
            metadata = result.get('metadata', {})
            content = result.get('content', '')
            content_length = len(content)
            
            logger.info(f"\n結果 {i}:")
            logger.info(f"  📑 Section 標題: {metadata.get('section_title', 'N/A')}")
            logger.info(f"  📄 所屬文檔: {metadata.get('document_title', 'N/A')}")
            logger.info(f"  🎯 分數: {result.get('score', 0):.4f}")
            logger.info(f"  📏 內容長度: {content_length} 字元")
            logger.info(f"  📦 是否完整文檔: {metadata.get('is_full_document', False)}")
            
            # 顯示內容預覽
            preview = content[:150] if content_length > 150 else content
            logger.info(f"  📝 內容預覽:\n{preview}...")
            
            # 驗證
            if not metadata.get('is_full_document'):
                logger.info(f"  ✅ 通過：返回 section 級結果")
            else:
                logger.warning(f"  ⚠️  警告：應該返回 section，但返回的是完整文檔")


def test_query_classification():
    """測試 3: 查詢分類邏輯"""
    logger.info("\n" + "=" * 80)
    logger.info("測試 3: 查詢分類邏輯")
    logger.info("=" * 80)
    
    service = ProtocolGuideSearchService()
    
    test_cases = [
        # (查詢, 預期類型)
        ("IOL 放測 SOP", "document"),
        ("標準作業流程", "document"),
        ("完整教學", "document"),
        ("所有步驟", "document"),
        ("網路設定", "section"),
        ("USB 安裝", "section"),
        ("如何使用", "section"),
    ]
    
    for query, expected_type in test_cases:
        actual_type = service._classify_query(query)
        status = "✅" if actual_type == expected_type else "❌"
        logger.info(f"{status} '{query}' → 預期: {expected_type}, 實際: {actual_type}")


def test_database_fields():
    """測試 4: 驗證資料庫欄位"""
    logger.info("\n" + "=" * 80)
    logger.info("測試 4: 驗證資料庫欄位")
    logger.info("=" * 80)
    
    from django.db import connection
    
    with connection.cursor() as cursor:
        # 檢查欄位存在
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'document_section_embeddings'
                AND column_name IN ('document_id', 'document_title', 'is_document_title')
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        logger.info(f"\n📋 新增欄位:")
        for col_name, data_type, is_nullable in columns:
            logger.info(f"  ✅ {col_name}: {data_type} (nullable: {is_nullable})")
        
        # 檢查資料完整性
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(DISTINCT document_id) as unique_docs,
                SUM(CASE WHEN is_document_title THEN 1 ELSE 0 END) as doc_titles,
                SUM(CASE WHEN document_id IS NULL THEN 1 ELSE 0 END) as null_count
            FROM document_section_embeddings
            WHERE source_table = 'protocol_guide'
        """)
        
        result = cursor.fetchone()
        logger.info(f"\n📊 資料統計:")
        logger.info(f"  總記錄數: {result[0]}")
        logger.info(f"  唯一文檔數: {result[1]}")
        logger.info(f"  文檔標題記錄數: {result[2]}")
        logger.info(f"  NULL document_id 記錄數: {result[3]}")
        
        if result[3] == 0:
            logger.info(f"  ✅ 所有記錄都有 document_id")
        else:
            logger.warning(f"  ❌ 發現 {result[3]} 個記錄缺少 document_id")


if __name__ == '__main__':
    logger.info("\n" + "="*80)
    logger.info("開始文檔級搜尋功能測試")
    logger.info("="*80)
    
    try:
        # 測試 4: 資料庫欄位驗證（先確保基礎設施正確）
        test_database_fields()
        
        # 測試 3: 查詢分類
        test_query_classification()
        
        # 測試 1: SOP 查詢
        test_sop_query()
        
        # 測試 2: 普通查詢
        test_regular_query()
        
        logger.info("\n" + "="*80)
        logger.info("✅ 所有測試完成")
        logger.info("="*80)
        
    except Exception as e:
        logger.error(f"\n❌ 測試失敗：{str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
