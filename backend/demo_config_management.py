#!/usr/bin/env python
"""
二階段搜尋權重配置 - 管理配置示範

本腳本展示如何透過 Django ORM 管理兩階段搜尋權重配置

使用方式:
    docker exec -it ai-django python demo_config_management.py

作者：AI Assistant
日期：2025-11-14
"""

import os
import sys
import django

# 設定 Django 環境
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.models import SearchThresholdSetting

def print_section(title):
    """打印章節標題"""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")

def print_config(setting):
    """打印配置詳細資訊"""
    print(f"Assistant Type: {setting.assistant_type}")
    print(f"模式: {'統一權重' if setting.use_unified_weights else '獨立權重'}")
    print()
    print("Stage 1 配置 (段落搜尋):")
    print(f"  • Threshold: {setting.stage1_threshold}")
    print(f"  • Title Weight: {setting.stage1_title_weight}%")
    print(f"  • Content Weight: {setting.stage1_content_weight}%")
    print(f"  • 權重總和: {setting.stage1_title_weight + setting.stage1_content_weight}%")
    print()
    print("Stage 2 配置 (全文搜尋):")
    print(f"  • Threshold: {setting.stage2_threshold}")
    print(f"  • Title Weight: {setting.stage2_title_weight}%")
    print(f"  • Content Weight: {setting.stage2_content_weight}%")
    print(f"  • 權重總和: {setting.stage2_title_weight + setting.stage2_content_weight}%")
    print()

# ==================== 示範 1：查看現有配置 ====================

print_section("示範 1: 查看現有配置")

print("📋 查詢所有配置:\n")

for setting in SearchThresholdSetting.objects.all():
    print(f"🔹 {setting.assistant_type}:")
    print(f"   統一權重: {setting.use_unified_weights}")
    print(f"   Stage 1: {setting.stage1_threshold} (權重 {setting.stage1_title_weight}%/{setting.stage1_content_weight}%)")
    print(f"   Stage 2: {setting.stage2_threshold} (權重 {setting.stage2_title_weight}%/{setting.stage2_content_weight}%)")
    print()

# ==================== 示範 2：修改為獨立權重模式 ====================

print_section("示範 2: 修改為獨立權重模式")

print("📝 操作步驟:\n")
print("1. 查詢 Protocol Assistant 配置")
setting = SearchThresholdSetting.objects.get(assistant_type='protocol_assistant')

print("   原始配置:")
print(f"   • use_unified_weights: {setting.use_unified_weights}")
print(f"   • stage1_threshold: {setting.stage1_threshold}")
print(f"   • stage2_threshold: {setting.stage2_threshold}")
print()

print("2. 修改為獨立權重模式")
original_unified = setting.use_unified_weights
original_s1_threshold = setting.stage1_threshold
original_s2_threshold = setting.stage2_threshold

setting.use_unified_weights = False
setting.stage1_threshold = 0.75
setting.stage1_title_weight = 65
setting.stage1_content_weight = 35
setting.stage2_threshold = 0.55
setting.stage2_title_weight = 45
setting.stage2_content_weight = 55
setting.save()

print("   ✅ 配置已更新")
print()

print("3. 驗證修改結果")
setting.refresh_from_db()
print(f"   • use_unified_weights: {setting.use_unified_weights}")
print(f"   • Stage 1: threshold={setting.stage1_threshold}, weights={setting.stage1_title_weight}%/{setting.stage1_content_weight}%")
print(f"   • Stage 2: threshold={setting.stage2_threshold}, weights={setting.stage2_title_weight}%/{setting.stage2_content_weight}%")
print()

print("4. 測試兩階段配置差異")

from library.common.threshold_manager import get_threshold_manager
manager = get_threshold_manager()
manager._refresh_cache()  # 重新載入配置

threshold_s1 = manager.get_threshold('protocol_assistant', stage=1)
weights_s1 = manager.get_weights('protocol_assistant', stage=1)

threshold_s2 = manager.get_threshold('protocol_assistant', stage=2)
weights_s2 = manager.get_weights('protocol_assistant', stage=2)

print(f"   ThresholdManager 讀取結果:")
print(f"   • Stage 1: threshold={threshold_s1}, weights={int(weights_s1[0]*100)}%/{int(weights_s1[1]*100)}%")
print(f"   • Stage 2: threshold={threshold_s2}, weights={int(weights_s2[0]*100)}%/{int(weights_s2[1]*100)}%")
print()

if threshold_s1 != threshold_s2:
    print("   ✅ 兩階段配置已成功分離！")
else:
    print("   ⚠️ 兩階段配置相同（可能仍在統一模式）")

# ==================== 示範 3：恢復為統一權重模式 ====================

print_section("示範 3: 恢復為統一權重模式")

print("📝 操作步驟:\n")
print("1. 切換回統一權重模式")
setting.use_unified_weights = True
setting.stage1_threshold = original_s1_threshold
setting.stage2_threshold = original_s2_threshold
setting.save()

print("   ✅ 配置已恢復")
print()

print("2. 驗證恢復結果")
manager._refresh_cache()

threshold_s1 = manager.get_threshold('protocol_assistant', stage=1)
threshold_s2 = manager.get_threshold('protocol_assistant', stage=2)

print(f"   • Stage 1 threshold: {threshold_s1}")
print(f"   • Stage 2 threshold: {threshold_s2}")

if threshold_s1 == threshold_s2:
    print("   ✅ 統一權重模式已恢復（兩階段使用相同配置）")
else:
    print("   ⚠️ 兩階段配置不同（獨立模式）")

# ==================== 示範 4：批量管理多個 Assistant ====================

print_section("示範 4: 批量管理多個 Assistant")

print("📝 範例：將所有 Assistant 切換到獨立權重模式\n")

configs = {
    'protocol_assistant': {
        'stage1': {'threshold': 0.70, 'title': 60, 'content': 40},
        'stage2': {'threshold': 0.60, 'title': 50, 'content': 50},
    },
    'rvt_assistant': {
        'stage1': {'threshold': 0.75, 'title': 70, 'content': 30},
        'stage2': {'threshold': 0.65, 'title': 60, 'content': 40},
    }
}

print("批量更新配置:")
for assistant_type, config in configs.items():
    setting = SearchThresholdSetting.objects.get(assistant_type=assistant_type)
    
    setting.use_unified_weights = False
    
    # Stage 1
    setting.stage1_threshold = config['stage1']['threshold']
    setting.stage1_title_weight = config['stage1']['title']
    setting.stage1_content_weight = config['stage1']['content']
    
    # Stage 2
    setting.stage2_threshold = config['stage2']['threshold']
    setting.stage2_title_weight = config['stage2']['title']
    setting.stage2_content_weight = config['stage2']['content']
    
    setting.save()
    
    print(f"✅ {assistant_type} 已更新")

print()
print("驗證更新結果:")

manager._refresh_cache()

for assistant_type in configs.keys():
    t1 = manager.get_threshold(assistant_type, stage=1)
    t2 = manager.get_threshold(assistant_type, stage=2)
    w1 = manager.get_weights(assistant_type, stage=1)
    w2 = manager.get_weights(assistant_type, stage=2)
    
    print(f"\n{assistant_type}:")
    print(f"  Stage 1: {t1} ({int(w1[0]*100)}%/{int(w1[1]*100)}%)")
    print(f"  Stage 2: {t2} ({int(w2[0]*100)}%/{int(w2[1]*100)}%)")

# 恢復原始配置
print("\n\n恢復所有配置到統一權重模式...")
for assistant_type in ['protocol_assistant', 'rvt_assistant']:
    setting = SearchThresholdSetting.objects.get(assistant_type=assistant_type)
    setting.use_unified_weights = True
    setting.save()

print("✅ 配置已恢復")

# ==================== 總結 ====================

print_section("✅ 示範總結")

print("📊 已展示的管理方式:\n")
print("1. ✅ 查看現有配置")
print("   • SearchThresholdSetting.objects.all()")
print("   • SearchThresholdSetting.objects.get(assistant_type='xxx')")
print()

print("2. ✅ 修改配置")
print("   • setting.use_unified_weights = False")
print("   • setting.stage1_threshold = 0.75")
print("   • setting.stage1_title_weight = 65")
print("   • setting.save()")
print()

print("3. ✅ 驗證配置生效")
print("   • manager.get_threshold(assistant_type, stage=1)")
print("   • manager.get_weights(assistant_type, stage=1)")
print()

print("4. ✅ 批量管理")
print("   • 迴圈更新多個 Assistant 配置")
print("   • manager._refresh_cache() 重新載入配置")
print()

print("=" * 80)
print("🎯 配置管理功能完全就緒，可以正式使用！")
print("=" * 80)
print()

print("📝 實際使用建議:")
print("   • 開發/測試階段：使用 Django Shell 直接修改")
print("   • 生產環境：建議使用 Django Admin 或前端介面")
print("   • 整合測試：透過 Dify Studio 驗證配置效果")
print()
