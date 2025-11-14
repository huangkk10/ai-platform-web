#!/usr/bin/env python3
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ai_platform.settings")
django.setup()

from library.protocol_guide.search_service import ProtocolGuideSearchService
from api.models import SearchThresholdSetting

# 設定為非統一模式
setting = SearchThresholdSetting.objects.get(assistant_type="protocol_assistant")
setting.use_unified_weights = False
setting.save()

print("="*80)
print("🧪 測試模式: use_unified_weights=False")
print("="*80)

print(f"\n【配置資訊】")
print(f"  第一階段: 標題 {setting.stage1_title_weight}% / 內容 {setting.stage1_content_weight}% / threshold {setting.stage1_threshold}")
print(f"  第二階段: 標題 {setting.stage2_title_weight}% / 內容 {setting.stage2_content_weight}% / threshold {setting.stage2_threshold}")

service = ProtocolGuideSearchService()

# Stage 1
print(f"\n【Stage 1 搜尋】")
results_s1 = service.search_knowledge(query="IOL", limit=3, stage=1)
print(f"結果數量: {len(results_s1)}")
if results_s1:
    print(f"首個結果: {results_s1[0].get('title', 'N/A')}, score={results_s1[0].get('score', 0):.3f}")

# Stage 2
print(f"\n【Stage 2 搜尋】")
results_s2 = service.search_knowledge(query="IOL", limit=3, stage=2)
print(f"結果數量: {len(results_s2)}")
if results_s2:
    print(f"首個結果: {results_s2[0].get('title', 'N/A')}, score={results_s2[0].get('score', 0):.3f}")

# 比較
if results_s1 and results_s2:
    score_diff = abs(results_s1[0].get('score', 0) - results_s2[0].get('score', 0))
    print(f"\n【結果比較】")
    print(f"  分數差異: {score_diff:.4f}")
    
    if score_diff > 0.01:
        print(f"  ✅ 符合預期：非統一模式下兩階段分數不同")
    else:
        print(f"  ⚠️ 分數相同或非常接近")

print("\n" + "="*80)

# 恢復為統一模式
setting.use_unified_weights = True
setting.save()
print("✅ 已恢復為統一模式")
