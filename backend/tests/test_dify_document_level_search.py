#!/usr/bin/env python
"""
Dify 外部知識庫 API - 文檔級搜尋測試
============================================================
測試目標：
1. 模擬 Dify 發送 SOP 查詢
2. 驗證返回完整文檔（而非截斷的 section）
3. 確認返回格式符合 Dify 規格
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
import json
import logging

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def format_dify_response(results: list, knowledge_id: str) -> dict:
    """
    將搜尋結果格式化為 Dify 外部知識庫 API 格式
    
    Args:
        results: 搜尋結果列表
        knowledge_id: 知識庫 ID
        
    Returns:
        Dify API 格式的回應
    """
    records = []
    
    for result in results:
        content = result.get('content', '')
        metadata = result.get('metadata', {})
        score = result.get('score', 0.0)
        
        # 構建 Dify 格式的記錄
        record = {
            'content': content,
            'score': float(score),
            'title': metadata.get('document_title', 'Untitled'),
            'metadata': {
                'source_table': metadata.get('source_table', ''),
                'document_id': metadata.get('document_id', ''),
                'is_full_document': metadata.get('is_full_document', False),
                'sections_count': metadata.get('sections_count', 0)
            }
        }
        
        records.append(record)
    
    return {
        'records': records
    }


def test_sop_query_via_dify():
    """測試：模擬 Dify 發送 SOP 查詢"""
    logger.info("\n" + "=" * 80)
    logger.info("🔍 Dify 整合測試：SOP 查詢")
    logger.info("=" * 80)
    
    # 模擬 Dify 發送的請求參數
    query = "IOL 放測 SOP"
    retrieval_setting = {
        'top_k': 3,
        'score_threshold': 0.5
    }
    
    logger.info(f"\n📤 Dify 請求參數:")
    logger.info(f"   Query: {query}")
    logger.info(f"   Top K: {retrieval_setting['top_k']}")
    logger.info(f"   Threshold: {retrieval_setting['score_threshold']}")
    
    # 執行搜尋
    service = ProtocolGuideSearchService()
    results = service.search_knowledge(
        query=query,
        limit=retrieval_setting['top_k'],
        threshold=retrieval_setting['score_threshold'],
        use_vector=True
    )
    
    # 格式化為 Dify 回應格式
    dify_response = format_dify_response(results, 'protocol_guide')
    
    logger.info(f"\n📥 Dify 回應:")
    logger.info(f"   記錄數: {len(dify_response['records'])}")
    
    # 顯示每個記錄的詳細資訊
    for i, record in enumerate(dify_response['records'], 1):
        logger.info(f"\n📄 記錄 {i}:")
        logger.info(f"   標題: {record['title']}")
        logger.info(f"   分數: {record['score']:.4f}")
        logger.info(f"   內容長度: {len(record['content'])} 字元")
        logger.info(f"   是否完整文檔: {record['metadata']['is_full_document']}")
        logger.info(f"   包含 Sections: {record['metadata']['sections_count']}")
        
        # 驗證
        if record['metadata']['is_full_document']:
            if len(record['content']) >= 1000:
                logger.info(f"   ✅ 驗證通過：完整文檔，長度 >= 1000 字元")
            else:
                logger.warning(f"   ⚠️  警告：完整文檔但長度較短 ({len(record['content'])} 字元)")
        else:
            logger.error(f"   ❌ 驗證失敗：應該返回完整文檔，但返回的是 section")
        
        # 顯示內容預覽（前 300 字元）
        preview = record['content'][:300] if len(record['content']) > 300 else record['content']
        logger.info(f"   📝 內容預覽:\n{preview}...")
    
    # 輸出完整的 JSON 格式（可供 Dify 使用）
    logger.info(f"\n📋 完整 Dify API 回應 (JSON):")
    print(json.dumps(dify_response, ensure_ascii=False, indent=2))
    
    return dify_response


def test_regular_query_via_dify():
    """測試：模擬 Dify 發送普通查詢"""
    logger.info("\n" + "=" * 80)
    logger.info("🔍 Dify 整合測試：普通查詢（應返回 section）")
    logger.info("=" * 80)
    
    query = "網路設定"
    retrieval_setting = {
        'top_k': 3,
        'score_threshold': 0.5
    }
    
    logger.info(f"\n📤 Dify 請求參數:")
    logger.info(f"   Query: {query}")
    logger.info(f"   Top K: {retrieval_setting['top_k']}")
    logger.info(f"   Threshold: {retrieval_setting['score_threshold']}")
    
    # 執行搜尋
    service = ProtocolGuideSearchService()
    results = service.search_knowledge(
        query=query,
        limit=retrieval_setting['top_k'],
        threshold=retrieval_setting['score_threshold'],
        use_vector=True
    )
    
    # 格式化為 Dify 回應格式
    dify_response = format_dify_response(results, 'protocol_guide')
    
    logger.info(f"\n📥 Dify 回應:")
    logger.info(f"   記錄數: {len(dify_response['records'])}")
    
    # 顯示每個記錄的詳細資訊
    for i, record in enumerate(dify_response['records'], 1):
        logger.info(f"\n📄 記錄 {i}:")
        logger.info(f"   標題: {record['title']}")
        logger.info(f"   分數: {record['score']:.4f}")
        logger.info(f"   內容長度: {len(record['content'])} 字元")
        logger.info(f"   是否完整文檔: {record['metadata']['is_full_document']}")
        
        # 驗證
        if not record['metadata']['is_full_document']:
            logger.info(f"   ✅ 驗證通過：返回 section 級結果")
        else:
            logger.warning(f"   ⚠️  警告：應該返回 section，但返回的是完整文檔")
        
        # 顯示內容預覽
        preview = record['content'][:200] if len(record['content']) > 200 else record['content']
        logger.info(f"   📝 內容預覽:\n{preview}...")
    
    return dify_response


def compare_results():
    """對比測試：顯示 SOP vs 普通查詢的差異"""
    logger.info("\n" + "=" * 80)
    logger.info("📊 對比測試：SOP 查詢 vs 普通查詢")
    logger.info("=" * 80)
    
    service = ProtocolGuideSearchService()
    
    # SOP 查詢
    sop_results = service.search_knowledge(
        query="IOL 放測 SOP",
        limit=3,
        threshold=0.5,
        use_vector=True
    )
    
    # 普通查詢
    regular_results = service.search_knowledge(
        query="網路設定",
        limit=3,
        threshold=0.5,
        use_vector=True
    )
    
    logger.info(f"\n📊 統計對比:")
    logger.info(f"   SOP 查詢結果數: {len(sop_results)}")
    logger.info(f"   普通查詢結果數: {len(regular_results)}")
    
    if sop_results:
        sop_metadata = sop_results[0].get('metadata', {})
        sop_content_length = len(sop_results[0].get('content', ''))
        logger.info(f"\n   SOP 查詢特徵:")
        logger.info(f"      - 是否完整文檔: {sop_metadata.get('is_full_document', False)}")
        logger.info(f"      - 內容長度: {sop_content_length} 字元")
        logger.info(f"      - 包含 Sections: {sop_metadata.get('sections_count', 0)}")
    
    if regular_results:
        regular_metadata = regular_results[0].get('metadata', {})
        regular_content_length = len(regular_results[0].get('content', ''))
        logger.info(f"\n   普通查詢特徵:")
        logger.info(f"      - 是否完整文檔: {regular_metadata.get('is_full_document', False)}")
        logger.info(f"      - 內容長度: {regular_content_length} 字元")
        logger.info(f"      - 包含 Sections: {regular_metadata.get('sections_count', 'N/A')}")
    
    # 計算差異
    if sop_results and regular_results:
        length_ratio = sop_content_length / regular_content_length if regular_content_length > 0 else 0
        logger.info(f"\n   📈 內容長度比例 (SOP / 普通): {length_ratio:.2f}x")
        
        if length_ratio >= 2.0:
            logger.info(f"   ✅ SOP 查詢返回的內容顯著更長（{length_ratio:.1f} 倍）")
        else:
            logger.warning(f"   ⚠️  SOP 查詢內容長度增長不明顯")


if __name__ == '__main__':
    logger.info("\n" + "="*80)
    logger.info("開始 Dify 外部知識庫 API 整合測試")
    logger.info("="*80)
    
    try:
        # 測試 1: SOP 查詢
        test_sop_query_via_dify()
        
        # 測試 2: 普通查詢
        test_regular_query_via_dify()
        
        # 測試 3: 對比分析
        compare_results()
        
        logger.info("\n" + "="*80)
        logger.info("✅ 所有 Dify 整合測試完成")
        logger.info("="*80)
        logger.info("\n💡 下一步：在 Dify Studio 中配置外部知識庫")
        logger.info("   Knowledge ID: protocol_guide")
        logger.info("   API Endpoint: http://10.10.172.127/api/dify/knowledge/retrieval/")
        logger.info("   測試查詢: 'IOL 放測 SOP'")
        logger.info("="*80)
        
    except Exception as e:
        logger.error(f"\n❌ 測試失敗：{str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
