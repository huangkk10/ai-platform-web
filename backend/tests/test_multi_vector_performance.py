"""
多向量搜索性能測試

對比單向量和多向量搜索的性能差異
"""

import os
import sys
import django
import time

# Django 設定
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.services.embedding_service import get_embedding_service
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_generation_performance():
    """測試向量生成性能"""
    
    logger.info("=" * 80)
    logger.info("測試向量生成性能")
    logger.info("=" * 80)
    
    service = get_embedding_service('ultra_high')
    
    test_title = "UNH-IOL Protocol 測試指南"
    test_content = """
    這是一個詳細的測試指南，包含以下內容：
    1. 測試環境準備
    2. 測試步驟說明
    3. 結果分析方法
    4. 常見問題解決
    
    請按照步驟進行測試。
    """
    
    # 測試單向量生成（舊方法）
    logger.info("\n🔹 單向量生成（舊方法）：")
    combined_content = f"Title: {test_title}\n\nContent:\n{test_content}"
    
    start_time = time.time()
    single_vector = service.generate_embedding(combined_content)
    single_time = time.time() - start_time
    
    logger.info(f"  生成時間: {single_time:.3f} 秒")
    logger.info(f"  向量維度: {len(single_vector)}")
    
    # 測試多向量生成（新方法）
    logger.info("\n🔹 多向量生成（新方法）：")
    
    start_time = time.time()
    title_vector = service.generate_embedding(test_title)
    content_vector = service.generate_embedding(test_content)
    multi_time = time.time() - start_time
    
    logger.info(f"  生成時間: {multi_time:.3f} 秒")
    logger.info(f"  標題向量維度: {len(title_vector)}")
    logger.info(f"  內容向量維度: {len(content_vector)}")
    logger.info(f"  時間差異: {(multi_time - single_time):.3f} 秒 ({(multi_time/single_time - 1)*100:.1f}%)")
    
    logger.info("\n" + "=" * 80)
    logger.info("✅ 向量生成性能測試完成")
    logger.info("=" * 80)


def test_search_performance():
    """測試搜索性能"""
    
    logger.info("\n" + "=" * 80)
    logger.info("測試搜索性能")
    logger.info("=" * 80)
    
    service = get_embedding_service('ultra_high')
    
    test_queries = [
        "UNH-IOL",
        "Protocol 測試",
        "測試步驟",
        "問題排查",
        "測試環境"
    ]
    
    # 單向量搜索性能
    logger.info("\n🔹 單向量搜索性能：")
    single_times = []
    
    for query in test_queries:
        start_time = time.time()
        results = service.search_similar_documents(
            query=query,
            source_table='protocol_guide',
            limit=5,
            threshold=0.3
        )
        search_time = time.time() - start_time
        single_times.append(search_time)
        logger.info(f"  查詢 '{query}': {search_time:.3f} 秒 (結果數: {len(results)})")
    
    avg_single = sum(single_times) / len(single_times)
    logger.info(f"  平均時間: {avg_single:.3f} 秒")
    
    # 多向量搜索性能
    logger.info("\n🔹 多向量搜索性能：")
    multi_times = []
    
    for query in test_queries:
        start_time = time.time()
        results = service.search_similar_documents_multi(
            query=query,
            source_table='protocol_guide',
            limit=5,
            threshold=0.3,
            title_weight=0.6,
            content_weight=0.4
        )
        search_time = time.time() - start_time
        multi_times.append(search_time)
        logger.info(f"  查詢 '{query}': {search_time:.3f} 秒 (結果數: {len(results)})")
    
    avg_multi = sum(multi_times) / len(multi_times)
    logger.info(f"  平均時間: {avg_multi:.3f} 秒")
    
    # 性能對比
    logger.info("\n📊 性能對比：")
    logger.info(f"  單向量平均: {avg_single:.3f} 秒")
    logger.info(f"  多向量平均: {avg_multi:.3f} 秒")
    logger.info(f"  時間差異: {(avg_multi - avg_single):.3f} 秒 ({(avg_multi/avg_single - 1)*100:.1f}%)")
    
    if avg_multi < avg_single * 1.5:
        logger.info("  ✅ 多向量搜索性能可接受（增加時間 < 50%）")
    else:
        logger.info("  ⚠️ 多向量搜索可能需要優化")
    
    logger.info("\n" + "=" * 80)
    logger.info("✅ 搜索性能測試完成")
    logger.info("=" * 80)


def test_batch_search_performance():
    """測試批量搜索性能"""
    
    logger.info("\n" + "=" * 80)
    logger.info("測試批量搜索性能（10 次查詢）")
    logger.info("=" * 80)
    
    service = get_embedding_service('ultra_high')
    
    # 單向量批量搜索
    logger.info("\n🔹 單向量批量搜索：")
    start_time = time.time()
    
    for i in range(10):
        service.search_similar_documents(
            query=f"測試 {i}",
            source_table='protocol_guide',
            limit=3,
            threshold=0.3
        )
    
    single_batch_time = time.time() - start_time
    logger.info(f"  總時間: {single_batch_time:.3f} 秒")
    logger.info(f"  平均每次: {single_batch_time/10:.3f} 秒")
    
    # 多向量批量搜索
    logger.info("\n🔹 多向量批量搜索：")
    start_time = time.time()
    
    for i in range(10):
        service.search_similar_documents_multi(
            query=f"測試 {i}",
            source_table='protocol_guide',
            limit=3,
            threshold=0.3,
            title_weight=0.6,
            content_weight=0.4
        )
    
    multi_batch_time = time.time() - start_time
    logger.info(f"  總時間: {multi_batch_time:.3f} 秒")
    logger.info(f"  平均每次: {multi_batch_time/10:.3f} 秒")
    
    # 批量性能對比
    logger.info("\n📊 批量性能對比：")
    logger.info(f"  單向量總時間: {single_batch_time:.3f} 秒")
    logger.info(f"  多向量總時間: {multi_batch_time:.3f} 秒")
    logger.info(f"  時間差異: {(multi_batch_time - single_batch_time):.3f} 秒 ({(multi_batch_time/single_batch_time - 1)*100:.1f}%)")
    
    logger.info("\n" + "=" * 80)
    logger.info("✅ 批量搜索性能測試完成")
    logger.info("=" * 80)


if __name__ == '__main__':
    try:
        # 測試 1：向量生成性能
        test_generation_performance()
        
        # 測試 2：單次搜索性能
        test_search_performance()
        
        # 測試 3：批量搜索性能
        test_batch_search_performance()
        
        logger.info("\n✅ 所有性能測試完成！")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"\n❌ 測試失敗: {str(e)}", exc_info=True)
        sys.exit(1)
