#!/usr/bin/env python
"""
測試 DifyKnowledgeSearchHandler 的分數過濾 Bug
==============================================

檢查為什麼 88.45% 的相似度會被過濾掉
"""

import os
import sys
import django

# Django 環境設置
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

def test_score_filtering():
    """測試分數過濾邏輯"""
    print("=" * 80)
    print("🔍 測試 DifyKnowledgeSearchHandler 分數過濾邏輯")
    print("=" * 80)
    
    # 模擬搜尋結果（包含 UNH-IOL 的 88.45% 相似度）
    mock_results = [
        {
            'title': 'UNH-IOL',
            'content': 'UNH-IOL 相關內容...',
            'score': 0.8845,  # 88.45% 相似度
            'metadata': {}
        },
        {
            'title': 'I3C 相關說明',
            'content': 'I3C 協議說明...',
            'score': 0.7925,  # 79.25% 相似度
            'metadata': {}
        },
        {
            'title': '其他文檔',
            'content': '其他內容...',
            'score': 0.7500,  # 75% 相似度
            'metadata': {}
        }
    ]
    
    threshold = 0.8  # 80% threshold
    
    print(f"\n📊 測試資料:")
    print(f"   Threshold: {threshold} (80%)")
    print(f"   搜尋結果數: {len(mock_results)}")
    for i, result in enumerate(mock_results, 1):
        print(f"   結果 {i}: {result['title']} - 分數: {result['score']:.4f} ({result['score']*100:.2f}%)")
    
    # 測試當前的過濾邏輯
    print(f"\n🔬 測試過濾邏輯: if result.get('score', 0) >= score_threshold")
    
    filtered_results = [
        result for result in mock_results 
        if result.get('score', 0) >= threshold
    ]
    
    print(f"\n✅ 過濾結果:")
    print(f"   過濾前: {len(mock_results)} 條")
    print(f"   過濾後: {len(filtered_results)} 條")
    
    if filtered_results:
        print(f"\n   通過過濾的結果:")
        for i, result in enumerate(filtered_results, 1):
            print(f"   {i}. {result['title']} - {result['score']:.4f} ({result['score']*100:.2f}%)")
    else:
        print(f"\n   ❌ 沒有結果通過過濾！")
    
    # 分析每個結果
    print(f"\n🔍 詳細分析:")
    for i, result in enumerate(mock_results, 1):
        score = result.get('score', 0)
        passed = score >= threshold
        status = "✅ 通過" if passed else "❌ 被過濾"
        print(f"   結果 {i}: {result['title']}")
        print(f"      分數: {score:.4f} ({score*100:.2f}%)")
        print(f"      Threshold: {threshold:.4f} ({threshold*100:.2f}%)")
        print(f"      {score:.4f} >= {threshold:.4f} ? {passed}")
        print(f"      結果: {status}")
        print()
    
    # 驗證問題
    print("=" * 80)
    print("🎯 問題分析:")
    print("=" * 80)
    
    unh_iol_result = mock_results[0]
    print(f"UNH-IOL 資料:")
    print(f"   分數: {unh_iol_result['score']} (88.45%)")
    print(f"   Threshold: {threshold} (80%)")
    print(f"   0.8845 >= 0.8 ? {0.8845 >= 0.8}")
    print(f"   應該通過: ✅ 是")
    
    if len(filtered_results) == 0:
        print(f"\n❌ Bug 確認: 邏輯上應該通過但實際被過濾了！")
        print(f"   可能原因: 分數欄位格式不一致或比較邏輯錯誤")
    elif unh_iol_result in filtered_results:
        print(f"\n✅ 過濾邏輯正確: UNH-IOL 通過過濾")
    else:
        print(f"\n⚠️ 異常狀態: 有結果通過但 UNH-IOL 沒有通過")
    
    print("\n" + "=" * 80)

def test_actual_search_results():
    """測試實際的搜尋結果資料結構"""
    print("\n" + "=" * 80)
    print("🔍 測試實際搜尋結果的資料結構")
    print("=" * 80)
    
    from library.protocol_guide.search_service import ProtocolGuideSearchService
    
    service = ProtocolGuideSearchService()
    
    # 執行實際搜尋
    query = 'iol'
    results = service.search_knowledge(
        query=query,
        limit=5,
        threshold=0.8,
        search_mode='section_only',
        stage=1
    )
    
    print(f"\n📊 實際搜尋結果:")
    print(f"   查詢: '{query}'")
    print(f"   結果數: {len(results)}")
    
    if results:
        print(f"\n   結果詳情:")
        for i, result in enumerate(results, 1):
            print(f"\n   結果 {i}:")
            print(f"      title: {result.get('title', 'N/A')}")
            print(f"      score: {result.get('score', 'N/A')} (類型: {type(result.get('score'))})")
            print(f"      content 長度: {len(result.get('content', ''))}")
            
            # 檢查 score 欄位
            score = result.get('score', 0)
            if isinstance(score, (int, float)):
                print(f"      score >= 0.8 ? {score >= 0.8}")
            else:
                print(f"      ⚠️ score 不是數字類型！")
    else:
        print(f"\n   ❌ 沒有搜尋結果")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    try:
        test_score_filtering()
        test_actual_search_results()
        
        print("\n✅ 測試完成")
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
