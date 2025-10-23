#!/usr/bin/env python
"""
驗證 popular_questions 欄位修復

測試 RVT Analytics 的問題統計 API 是否返回 popular_questions 欄位
"""

import os
import sys
import django

# 設定 Django 環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
sys.path.insert(0, '/app')
django.setup()

from library.rvt_analytics.statistics_manager import StatisticsManager

def test_popular_questions():
    """測試 popular_questions 欄位"""
    print("=" * 60)
    print("測試 popular_questions 欄位修復")
    print("=" * 60)
    
    manager = StatisticsManager()
    
    try:
        # 獲取問題統計（使用預設 30 天）
        stats = manager._get_question_stats(days=30)
        
        print(f"\n✅ 成功獲取統計資料")
        print(f"\n📊 返回的欄位:")
        for key in stats.keys():
            print(f"  - {key}")
        
        # 檢查 popular_questions 是否存在
        if 'popular_questions' in stats:
            print(f"\n✅ popular_questions 欄位存在")
            print(f"✅ 問題數量: {len(stats['popular_questions'])}")
            
            if stats['popular_questions']:
                print(f"\n📈 前 5 個熱門問題:")
                for i, q in enumerate(stats['popular_questions'][:5], 1):
                    question_preview = q['question'][:60]
                    if len(q['question']) > 60:
                        question_preview += "..."
                    print(f"\n  {i}. 問題: {question_preview}")
                    print(f"     次數: {q['count']}, 比例: {q['percentage']}%")
            else:
                print("\n⚠️ popular_questions 列表是空的（可能沒有對話資料）")
            
            print(f"\n" + "=" * 60)
            print("✅ 測試通過 - popular_questions 欄位已正確實作")
            print("=" * 60)
            return True
            
        else:
            print(f"\n❌ popular_questions 欄位不存在!")
            print(f"   現有欄位: {list(stats.keys())}")
            print(f"\n" + "=" * 60)
            print("❌ 測試失敗 - popular_questions 欄位缺失")
            print("=" * 60)
            return False
            
    except Exception as e:
        print(f"\n❌ 測試過程發生錯誤:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_popular_questions()
    sys.exit(0 if success else 1)
