#!/usr/bin/env python3
"""
測試兩階段搜尋機制
驗證 stage=1 和 stage=2 是否使用不同的權重和閾值配置
"""

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ai_platform.settings")
django.setup()

from library.protocol_guide.search_service import ProtocolGuideSearchService
from api.models import SearchThresholdSetting

def main():
    # 先檢查當前的資料庫配置
    print("="*80)
    print("📊 當前資料庫中的兩階段配置")
    print("="*80)

    try:
        setting = SearchThresholdSetting.objects.get(assistant_type="protocol_assistant")
        print(f"\n助手類型: {setting.assistant_type}")
        print(f"使用統一權重: {setting.use_unified_weights}")
        print(f"\n【第一階段配置（段落搜尋）】")
        print(f"  標題權重: {setting.stage1_title_weight}%")
        print(f"  內容權重: {setting.stage1_content_weight}%")
        print(f"  相似度閾值: {setting.stage1_threshold}")
        print(f"\n【第二階段配置（全文搜尋）】")
        print(f"  標題權重: {setting.stage2_title_weight}%")
        print(f"  內容權重: {setting.stage2_content_weight}%")
        print(f"  相似度閾值: {setting.stage2_threshold}")
    except SearchThresholdSetting.DoesNotExist:
        print("❌ 找不到 protocol_assistant 的配置")
        return

    print("\n" + "="*80)
    print("🧪 測試兩階段搜尋")
    print("="*80)

    service = ProtocolGuideSearchService()

    # 測試相同查詢在不同階段的結果
    test_query = "IOL"

    print(f"\n【測試查詢】: \"{test_query}\"")

    # 第一階段搜尋（段落搜尋）
    print("\n" + "-"*60)
    print("🔍 第一階段搜尋 (stage=1, 段落級搜尋)")
    print("-"*60)

    results_stage1 = service.search_knowledge(
        query=test_query,
        limit=5,
        use_vector=True,
        threshold=0.7,  # 外部閾值（測試是否會被資料庫配置覆蓋）
        stage=1
    )

    print(f"結果數量: {len(results_stage1)}")
    if results_stage1:
        for i, r in enumerate(results_stage1[:3], 1):
            title = r.get("title", "N/A")
            score = r.get("score", 0)
            sections = r.get("metadata", {}).get("sections_count", 0)
            print(f"  {i}. {title[:40]}, score={score:.3f}, sections={sections}")
    else:
        print("  ❌ 無結果")

    # 第二階段搜尋（全文搜尋）
    print("\n" + "-"*60)
    print("🔍 第二階段搜尋 (stage=2, 全文級搜尋)")
    print("-"*60)

    results_stage2 = service.search_knowledge(
        query=test_query,
        limit=5,
        use_vector=True,
        threshold=0.7,  # 外部閾值（測試是否會被資料庫配置覆蓋）
        stage=2
    )

    print(f"結果數量: {len(results_stage2)}")
    if results_stage2:
        for i, r in enumerate(results_stage2[:3], 1):
            title = r.get("title", "N/A")
            score = r.get("score", 0)
            sections = r.get("metadata", {}).get("sections_count", 0)
            print(f"  {i}. {title[:40]}, score={score:.3f}, sections={sections}")
    else:
        print("  ❌ 無結果")

    # 比較結果
    print("\n" + "="*80)
    print("📊 兩階段結果比較")
    print("="*80)
    print(f"第一階段結果數量: {len(results_stage1)}")
    print(f"第二階段結果數量: {len(results_stage2)}")
    
    if results_stage1 and results_stage2:
        print(f"\n第一階段首個結果分數: {results_stage1[0].get('score', 0):.3f}")
        print(f"第二階段首個結果分數: {results_stage2[0].get('score', 0):.3f}")
        
        # 檢查是否有分數差異（表示使用了不同的權重）
        score_diff = abs(results_stage1[0].get('score', 0) - results_stage2[0].get('score', 0))
        if score_diff > 0.01:
            print(f"\n✅ 兩階段使用不同權重（分數差異: {score_diff:.3f}）")
        else:
            print(f"\n⚠️ 兩階段分數相同或非常接近（差異: {score_diff:.3f}）")
            if setting.use_unified_weights:
                print("   原因：use_unified_weights=True，兩階段使用相同配置")
            else:
                print("   可能原因：兩階段配置值相同")

if __name__ == "__main__":
    main()
