#!/usr/bin/env python3
"""
測試兩種模式：
1. use_unified_weights=True: 兩階段使用相同配置（使用 stage1 配置）
2. use_unified_weights=False: 兩階段使用不同配置（stage1 和 stage2 分別配置）
"""

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ai_platform.settings")
django.setup()

from library.protocol_guide.search_service import ProtocolGuideSearchService
from api.models import SearchThresholdSetting

def test_mode(use_unified: bool):
    """測試特定模式"""
    print("\n" + "="*80)
    print(f"🧪 測試模式: use_unified_weights={use_unified}")
    print("="*80)
    
    # 更新資料庫配置
    setting = SearchThresholdSetting.objects.get(assistant_type="protocol_assistant")
    setting.use_unified_weights = use_unified
    setting.save()
    
    print(f"\n✅ 已設定 use_unified_weights={use_unified}")
    print(f"\n【配置資訊】")
    print(f"  第一階段: 標題 {setting.stage1_title_weight}% / 內容 {setting.stage1_content_weight}% / threshold {setting.stage1_threshold}")
    print(f"  第二階段: 標題 {setting.stage2_title_weight}% / 內容 {setting.stage2_content_weight}% / threshold {setting.stage2_threshold}")
    
    service = ProtocolGuideSearchService()
    test_query = "IOL"
    
    # 測試 Stage 1
    print(f"\n【Stage 1 搜尋】")
    results_s1 = service.search_knowledge(query=test_query, limit=3, stage=1)
    print(f"結果數量: {len(results_s1)}")
    if results_s1:
        print(f"首個結果: {results_s1[0].get('title', 'N/A')}, score={results_s1[0].get('score', 0):.3f}")
    
    # 測試 Stage 2
    print(f"\n【Stage 2 搜尋】")
    results_s2 = service.search_knowledge(query=test_query, limit=3, stage=2)
    print(f"結果數量: {len(results_s2)}")
    if results_s2:
        print(f"首個結果: {results_s2[0].get('title', 'N/A')}, score={results_s2[0].get('score', 0):.3f}")
    
    # 比較
    if results_s1 and results_s2:
        score_diff = abs(results_s1[0].get('score', 0) - results_s2[0].get('score', 0))
        print(f"\n【結果比較】")
        print(f"  分數差異: {score_diff:.4f}")
        
        if use_unified:
            if score_diff < 0.01:
                print(f"  ✅ 符合預期：統一模式下兩階段分數相同")
            else:
                print(f"  ❌ 異常：統一模式下兩階段分數應該相同")
        else:
            if score_diff > 0.01:
                print(f"  ✅ 符合預期：非統一模式下兩階段分數不同")
            else:
                print(f"  ⚠️ 注意：非統一模式下分數相同（可能配置值剛好相同）")

def main():
    print("="*80)
    print("🔍 兩階段搜尋機制完整驗證")
    print("="*80)
    
    # 測試兩種模式
    test_mode(use_unified=True)
    test_mode(use_unified=False)
    
    print("\n" + "="*80)
    print("✅ 測試完成")
    print("="*80)

if __name__ == "__main__":
    main()
