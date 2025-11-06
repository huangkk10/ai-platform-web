"""
多向量搜索功能測試

測試標題/內容分開計算分數的功能
"""

import os
import sys
import django

# Django 設定
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.services.embedding_service import get_embedding_service
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_multi_vector_search():
    """測試多向量搜索功能"""
    
    logger.info("=" * 80)
    logger.info("測試多向量搜索功能")
    logger.info("=" * 80)
    
    # 獲取 embedding 服務
    service = get_embedding_service('ultra_high')
    
    # 測試查詢 1：標題相關查詢
    logger.info("\n【測試 1】標題相關查詢：'UNH-IOL'")
    logger.info("-" * 80)
    
    query1 = "UNH-IOL"
    
    # 單向量搜索（舊方法）
    logger.info("\n🔹 單向量搜索（舊方法）：")
    single_results = service.search_similar_documents(
        query=query1,
        source_table='protocol_guide',
        limit=3,
        threshold=0.3
    )
    
    for i, result in enumerate(single_results, 1):
        logger.info(f"  {i}. ID={result['source_id']}, 相似度={result['similarity_score']:.3f}")
    
    # 多向量搜索（新方法）- 標題權重 60%
    logger.info("\n🔹 多向量搜索（標題權重 60%）：")
    multi_results = service.search_similar_documents_multi(
        query=query1,
        source_table='protocol_guide',
        limit=3,
        threshold=0.3,
        title_weight=0.6,
        content_weight=0.4
    )
    
    for i, result in enumerate(multi_results, 1):
        logger.info(
            f"  {i}. ID={result['source_id']}, "
            f"標題分數={result['title_score']:.3f}, "
            f"內容分數={result['content_score']:.3f}, "
            f"最終分數={result['final_score']:.3f}, "
            f"匹配類型={result['match_type']}"
        )
    
    # 多向量搜索 - 標題權重 80%
    logger.info("\n🔹 多向量搜索（標題權重 80%）：")
    multi_results_title = service.search_similar_documents_multi(
        query=query1,
        source_table='protocol_guide',
        limit=3,
        threshold=0.3,
        title_weight=0.8,
        content_weight=0.2
    )
    
    for i, result in enumerate(multi_results_title, 1):
        logger.info(
            f"  {i}. ID={result['source_id']}, "
            f"標題分數={result['title_score']:.3f}, "
            f"內容分數={result['content_score']:.3f}, "
            f"最終分數={result['final_score']:.3f}, "
            f"匹配類型={result['match_type']}"
        )
    
    # 測試查詢 2：內容相關查詢
    logger.info("\n\n【測試 2】內容相關查詢：'測試步驟'")
    logger.info("-" * 80)
    
    query2 = "測試步驟"
    
    # 多向量搜索 - 內容權重 70%
    logger.info("\n🔹 多向量搜索（內容權重 70%）：")
    multi_results_content = service.search_similar_documents_multi(
        query=query2,
        source_table='protocol_guide',
        limit=3,
        threshold=0.3,
        title_weight=0.3,
        content_weight=0.7
    )
    
    for i, result in enumerate(multi_results_content, 1):
        logger.info(
            f"  {i}. ID={result['source_id']}, "
            f"標題分數={result['title_score']:.3f}, "
            f"內容分數={result['content_score']:.3f}, "
            f"最終分數={result['final_score']:.3f}, "
            f"匹配類型={result['match_type']}"
        )
    
    # 測試查詢 3：RVT Guide 搜索
    logger.info("\n\n【測試 3】RVT Guide 搜索：'Ansible'")
    logger.info("-" * 80)
    
    query3 = "Ansible"
    
    # 多向量搜索
    logger.info("\n🔹 多向量搜索（平衡權重）：")
    rvt_results = service.search_similar_documents_multi(
        query=query3,
        source_table='rvt_guide',
        limit=3,
        threshold=0.3,
        title_weight=0.6,
        content_weight=0.4
    )
    
    for i, result in enumerate(rvt_results, 1):
        logger.info(
            f"  {i}. ID={result['source_id']}, "
            f"標題分數={result['title_score']:.3f}, "
            f"內容分數={result['content_score']:.3f}, "
            f"最終分數={result['final_score']:.3f}, "
            f"匹配類型={result['match_type']}"
        )
    
    logger.info("\n" + "=" * 80)
    logger.info("✅ 多向量搜索測試完成")
    logger.info("=" * 80)


def test_multi_vector_weights():
    """測試不同權重配置的影響"""
    
    logger.info("\n" + "=" * 80)
    logger.info("測試不同權重配置的影響")
    logger.info("=" * 80)
    
    service = get_embedding_service('ultra_high')
    query = "Protocol 測試"
    
    weight_configs = [
        (0.8, 0.2, "強調標題"),
        (0.6, 0.4, "平衡權重"),
        (0.4, 0.6, "強調內容"),
        (0.2, 0.8, "極重內容"),
    ]
    
    for title_weight, content_weight, description in weight_configs:
        logger.info(f"\n🔹 {description}（標題={title_weight}, 內容={content_weight}）：")
        
        results = service.search_similar_documents_multi(
            query=query,
            source_table='protocol_guide',
            limit=3,
            threshold=0.3,
            title_weight=title_weight,
            content_weight=content_weight
        )
        
        for i, result in enumerate(results, 1):
            logger.info(
                f"  {i}. ID={result['source_id']}, "
                f"標題={result['title_score']:.3f}, "
                f"內容={result['content_score']:.3f}, "
                f"最終={result['final_score']:.3f}"
            )
    
    logger.info("\n" + "=" * 80)
    logger.info("✅ 權重測試完成")
    logger.info("=" * 80)


if __name__ == '__main__':
    try:
        # 測試 1：多向量搜索功能
        test_multi_vector_search()
        
        # 測試 2：不同權重配置
        test_multi_vector_weights()
        
        logger.info("\n✅ 所有測試完成！")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"\n❌ 測試失敗: {str(e)}", exc_info=True)
        sys.exit(1)
