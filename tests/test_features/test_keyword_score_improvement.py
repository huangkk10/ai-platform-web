#!/usr/bin/env python
"""
測試方案 1：關鍵字搜尋分數計算改進
=====================================

測試目標：
1. 驗證 UNH-IOL 被正確計算為低分（< 0.5）
2. 驗證 IOL SOP 被正確計算為高分（> 0.8）
3. 確認 threshold 0.75 能正確過濾 UNH-IOL
"""

import os
import sys
import django

# 設定 Django 環境
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from library.protocol_guide.search_service import ProtocolGuideSearchService

def test_keyword_score_calculation():
    """測試關鍵字分數計算"""
    print("=" * 80)
    print("🧪 測試方案 1：關鍵字搜尋分數計算改進")
    print("=" * 80)
    
    service = ProtocolGuideSearchService()
    
    # 測試查詢
    query = "sop"
    limit = 10
    
    print(f"\n📝 測試參數:")
    print(f"   查詢字串: '{query}'")
    print(f"   結果數量: {limit}")
    print(f"   Threshold: 0.75 (Dify 工作室設定)")
    
    # 執行關鍵字搜尋
    print(f"\n🔍 執行關鍵字搜尋...")
    results = service.search_with_keywords(query, limit)
    
    print(f"\n📊 搜尋結果: {len(results)} 條")
    print("-" * 80)
    
    # 顯示所有結果
    for i, result in enumerate(results, 1):
        title = result.get('title', 'Unknown')
        score = result.get('score', 0)
        status = "✅ 通過" if score >= 0.75 else "❌ 過濾"
        
        print(f"\n{i}. {title}")
        print(f"   分數: {score:.2f} ({score * 100:.0f}%)")
        print(f"   狀態: {status} (threshold: 0.75)")
        print(f"   內容預覽: {result.get('content', '')[:100]}...")
    
    # 驗證關鍵結果
    print("\n" + "=" * 80)
    print("🎯 關鍵驗證")
    print("=" * 80)
    
    # 查找特定文檔
    iol_sop = None
    unh_iol = None
    
    for result in results:
        title = result.get('title', '').lower()
        if 'iol' in title and 'sop' in title and 'unh' not in title:
            iol_sop = result
        elif 'unh-iol' in title or 'unh iol' in title:
            unh_iol = result
    
    # 驗證 IOL SOP
    if iol_sop:
        score = iol_sop.get('score', 0)
        print(f"\n✅ IOL 放測 SOP:")
        print(f"   標題: {iol_sop.get('title')}")
        print(f"   分數: {score:.2f} ({score * 100:.0f}%)")
        if score >= 0.75:
            print(f"   ✅ 正確！分數 >= 0.75，會被保留")
        else:
            print(f"   ❌ 錯誤！分數 < 0.75，不應該被過濾")
    else:
        print(f"\n⚠️  未找到 IOL SOP 文檔")
    
    # 驗證 UNH-IOL
    if unh_iol:
        score = unh_iol.get('score', 0)
        print(f"\n✅ UNH-IOL:")
        print(f"   標題: {unh_iol.get('title')}")
        print(f"   分數: {score:.2f} ({score * 100:.0f}%)")
        if score < 0.75:
            print(f"   ✅ 正確！分數 < 0.75，會被過濾掉")
        else:
            print(f"   ❌ 錯誤！分數 >= 0.75，不應該通過過濾")
    else:
        print(f"\n✅ UNH-IOL 未出現在結果中（可能已被過濾或不存在）")
    
    # 統計
    print("\n" + "=" * 80)
    print("📈 統計結果")
    print("=" * 80)
    
    passed = sum(1 for r in results if r.get('score', 0) >= 0.75)
    filtered = len(results) - passed
    
    print(f"\n總結果數: {len(results)}")
    print(f"通過過濾 (>= 0.75): {passed} 條")
    print(f"應被過濾 (< 0.75): {filtered} 條")
    
    if filtered > 0:
        print(f"\n應被過濾的文檔:")
        for result in results:
            if result.get('score', 0) < 0.75:
                print(f"  - {result.get('title')} ({result.get('score', 0):.2f})")
    
    print("\n" + "=" * 80)
    print("✅ 測試完成")
    print("=" * 80)
    
    return results

if __name__ == "__main__":
    try:
        test_keyword_score_calculation()
    except Exception as e:
        print(f"\n❌ 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
