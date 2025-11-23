#!/usr/bin/env python
"""
複製 Benchmark 測試案例到 Dify Benchmark 系統

功能：
1. 從 benchmark_test_case 表中複製測試案例
2. 調整為關鍵字評分模式（100%）
3. 設定 answer_keywords 和 expected_answer
4. 儲存到 dify_benchmark_test_case 表
"""

import os
import sys
import django

# Django setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.models import BenchmarkTestCase, DifyBenchmarkTestCase
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def copy_test_cases():
    """
    複製測試案例從 Benchmark 到 Dify Benchmark
    """
    print("=" * 80)
    print("📋 開始複製測試案例：Benchmark → Dify Benchmark")
    print("=" * 80)
    
    # 查詢所有啟用的 Benchmark 測試案例
    benchmark_cases = BenchmarkTestCase.objects.filter(is_active=True).order_by('id')
    total_cases = benchmark_cases.count()
    
    print(f"\n找到 {total_cases} 個啟用的測試案例")
    
    if total_cases == 0:
        print("⚠️  沒有可用的測試案例")
        return
    
    # 統計
    created_count = 0
    skipped_count = 0
    error_count = 0
    
    # 逐一複製
    for idx, case in enumerate(benchmark_cases, 1):
        try:
            # 檢查是否已存在（根據問題文本）
            existing = DifyBenchmarkTestCase.objects.filter(
                question=case.question
            ).first()
            
            if existing:
                logger.info(f"  [{idx}/{total_cases}] ⏭️  已存在，跳過: {case.question[:50]}...")
                skipped_count += 1
                continue
            
            # 準備關鍵字
            # 使用 expected_keywords（如果有），否則使用空陣列
            answer_keywords = case.expected_keywords if case.expected_keywords else []
            
            # 如果沒有關鍵字，嘗試從問題中提取測試類別作為關鍵字
            if not answer_keywords or len(answer_keywords) == 0:
                if case.category:
                    answer_keywords = [case.category]
            
            # 準備期望答案（使用 expected_answer_summary）
            expected_answer = case.expected_answer_summary or ""
            
            # 如果沒有期望答案，使用關鍵字提示
            if not expected_answer and answer_keywords:
                expected_answer = f"答案應包含以下關鍵字：{', '.join(answer_keywords)}"
            
            # 準備評分標準（100% 關鍵字評分）
            evaluation_criteria = {
                "method": "keyword_only",
                "keyword_weight": 100,
                "passing_score": 60,
                "description": "100% 關鍵字匹配評分"
            }
            
            # 創建 Dify 測試案例
            dify_case = DifyBenchmarkTestCase.objects.create(
                question=case.question,
                test_class_name=case.category or "未分類",
                expected_answer=expected_answer,
                answer_keywords=answer_keywords,
                evaluation_criteria=evaluation_criteria,
                difficulty_level=case.difficulty_level or "medium",
                question_type=case.question_type or "fact",
                max_score=100.00,
                is_active=True
            )
            
            logger.info(f"  [{idx}/{total_cases}] ✅ 已創建: {case.question[:50]}...")
            logger.info(f"      分類: {dify_case.test_class_name}")
            logger.info(f"      難度: {dify_case.difficulty_level}")
            logger.info(f"      關鍵字: {answer_keywords}")
            
            created_count += 1
            
        except Exception as e:
            logger.error(f"  [{idx}/{total_cases}] ❌ 失敗: {str(e)}")
            logger.error(f"      問題: {case.question[:50]}...")
            error_count += 1
    
    # 總結
    print("\n" + "=" * 80)
    print("📊 複製完成")
    print("=" * 80)
    print(f"✅ 成功創建: {created_count} 個測試案例")
    print(f"⏭️  已存在跳過: {skipped_count} 個")
    print(f"❌ 失敗: {error_count} 個")
    print(f"📝 總計: {total_cases} 個")
    print("=" * 80)
    
    # 驗證結果
    dify_total = DifyBenchmarkTestCase.objects.filter(is_active=True).count()
    print(f"\n✅ Dify Benchmark 測試案例總數: {dify_total}")
    
    # 顯示分類統計
    print("\n📊 測試案例分類統計:")
    from django.db.models import Count
    category_stats = DifyBenchmarkTestCase.objects.values('test_class_name').annotate(
        count=Count('id')
    ).order_by('-count')
    
    for stat in category_stats:
        print(f"  • {stat['test_class_name']}: {stat['count']} 個")
    
    # 顯示難度統計
    print("\n📊 測試案例難度統計:")
    difficulty_stats = DifyBenchmarkTestCase.objects.values('difficulty_level').annotate(
        count=Count('id')
    ).order_by('difficulty_level')
    
    for stat in difficulty_stats:
        print(f"  • {stat['difficulty_level']}: {stat['count']} 個")
    
    print("\n" + "=" * 80)
    print("🎉 複製完成！")
    print("=" * 80)


if __name__ == "__main__":
    try:
        copy_test_cases()
    except Exception as e:
        logger.error(f"❌ 執行失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
