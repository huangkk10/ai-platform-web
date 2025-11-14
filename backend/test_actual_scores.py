#!/usr/bin/env python
"""
測試實際搜尋結果的 score 欄位
============================

檢查實際返回的 score 值是什麼
"""

import os
import sys
import django

# Django 環境設置
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

def test_actual_scores():
    """測試實際搜尋返回的 score 值"""
    print("=" * 80)
    print("🔍 測試實際搜尋結果的 score 欄位")
    print("=" * 80)
    
    from library.protocol_guide.search_service import ProtocolGuideSearchService
    
    service = ProtocolGuideSearchService()
    
    # Stage 1: 段落搜尋
    print("\n📊 Stage 1: 段落搜尋 (auto mode)")
    print("-" * 80)
    
    query = 'iol'
    results_stage1 = service.search_knowledge(
        query=query,
        limit=3,
        threshold=0.8,
        search_mode='auto',  # 優先段落
        stage=1
    )
    
    print(f"查詢: '{query}'")
    print(f"結果數: {len(results_stage1)}")
    print(f"Threshold: 0.8 (80%)")
    
    if results_stage1:
        print(f"\n結果詳情:")
        for i, result in enumerate(results_stage1, 1):
            title = result.get('title', 'N/A')[:50]
            score = result.get('score')
            print(f"\n  結果 {i}:")
            print(f"    title: {title}")
            print(f"    score: {score}")
            print(f"    score type: {type(score)}")
            
            if isinstance(score, (int, float)):
                print(f"    score >= 0.8? {score >= 0.8}")
            elif isinstance(score, dict):
                print(f"    ⚠️ score 是 dict! 內容: {score}")
            elif score is None:
                print(f"    ⚠️ score 是 None!")
            else:
                print(f"    ⚠️ score 類型異常: {type(score)}")
    else:
        print(f"\n❌ Stage 1 沒有搜尋結果")
    
    # Stage 2: 文檔搜尋
    print("\n\n📊 Stage 2: 文檔搜尋 (document_only mode)")
    print("-" * 80)
    
    results_stage2 = service.search_knowledge(
        query=query,
        limit=3,
        threshold=0.8,
        search_mode='document_only',  # 全文搜尋
        stage=2
    )
    
    print(f"查詢: '{query}'")
    print(f"結果數: {len(results_stage2)}")
    print(f"Threshold: 0.8 (80%)")
    
    if results_stage2:
        print(f"\n結果詳情:")
        for i, result in enumerate(results_stage2, 1):
            title = result.get('title', 'N/A')[:50]
            score = result.get('score')
            print(f"\n  結果 {i}:")
            print(f"    title: {title}")
            print(f"    score: {score}")
            print(f"    score type: {type(score)}")
            
            if isinstance(score, (int, float)):
                print(f"    score >= 0.8? {score >= 0.8}")
            elif isinstance(score, dict):
                print(f"    ⚠️ score 是 dict! 內容: {score}")
            elif score is None:
                print(f"    ⚠️ score 是 None!")
            else:
                print(f"    ⚠️ score 類型異常: {type(score)}")
    else:
        print(f"\n❌ Stage 2 沒有搜尋結果")
    
    # 分析問題
    print("\n\n" + "=" * 80)
    print("🎯 問題分析")
    print("=" * 80)
    
    # 檢查日誌中提到的 "分數過濾: 3 -> 0"
    print(f"\n日誌顯示:")
    print(f"  📊 [Stage 10] 搜索返回 3 條原始結果")
    print(f"  分數過濾: 3 -> 0 (threshold: 0.8)")
    print(f"  🎯 [Stage 11] Python 二次過濾後: 0 條結果")
    
    print(f"\n可能的問題:")
    print(f"  1. ❓ score 欄位的值不是數字 (例如是 dict)")
    print(f"  2. ❓ score 欄位名稱不對 (例如是 similarity 而非 score)")
    print(f"  3. ❓ score 的值被格式化成其他結構")
    
    # 檢查原始結果結構
    if results_stage1:
        print(f"\n\n完整結果結構（Stage 1 第一筆）:")
        print("-" * 80)
        import json
        print(json.dumps(results_stage1[0], indent=2, ensure_ascii=False))
    
    if results_stage2:
        print(f"\n\n完整結果結構（Stage 2 第一筆）:")
        print("-" * 80)
        import json
        print(json.dumps(results_stage2[0], indent=2, ensure_ascii=False))

if __name__ == '__main__':
    try:
        test_actual_scores()
        print("\n✅ 測試完成")
    except Exception as e:
        print(f"\n❌ 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
