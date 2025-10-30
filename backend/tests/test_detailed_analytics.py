#!/usr/bin/env python
"""
詳細的 Analytics 測試 - 檢查 question_analysis 和 satisfaction_analysis
"""

import os
import django

# 設置 Django 環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from library.rvt_analytics.statistics_manager_refactored import RVTStatisticsManager

def main():
    print("\n" + "="*80)
    print("詳細 Analytics 測試")
    print("="*80)
    
    manager = RVTStatisticsManager()
    stats = manager.get_comprehensive_stats(days=7)
    
    print(f"\n📋 所有欄位: {list(stats.keys())}")
    
    print(f"\n🔎 question_analysis 檢查:")
    if 'question_analysis' in stats:
        qa = stats['question_analysis']
        print(f"  ✅ 存在")
        print(f"  總問題數: {qa.get('total_questions', 0)}")
        print(f"  分類數量: {len(qa.get('category_distribution', {}))}")
        if qa.get('category_distribution'):
            print(f"  前 3 個分類:")
            for cat, count in list(qa.get('category_distribution', {}).items())[:3]:
                print(f"    - {cat}: {count}")
    else:
        print(f"  ❌ 不存在")
    
    print(f"\n🔎 satisfaction_analysis 檢查:")
    if 'satisfaction_analysis' in stats:
        sa = stats['satisfaction_analysis']
        print(f"  ✅ 存在")
        if 'basic_stats' in sa:
            bs = sa['basic_stats']
            print(f"  有幫助: {bs.get('helpful_count', 0)}")
            print(f"  沒幫助: {bs.get('unhelpful_count', 0)}")
            print(f"  未評分: {bs.get('unrated_count', 0)}")
            print(f"  滿意度: {bs.get('satisfaction_rate', 0):.1%}")
    else:
        print(f"  ❌ 不存在")

if __name__ == '__main__':
    main()
