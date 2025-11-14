#!/usr/bin/env python
"""
測試兩階段權重切換
==================

測試切換 use_unified_weights 後，系統是否正確使用不同階段的權重。
"""

import os
import sys
import django

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.models import SearchThresholdSetting
from library.common.threshold_manager import get_threshold_manager


def main():
    print("\n" + "="*70)
    print("🔄 測試兩階段權重切換")
    print("="*70)
    
    try:
        # 獲取 Protocol Assistant 配置
        setting = SearchThresholdSetting.objects.get(assistant_type='protocol_assistant')
        
        print(f"\n📊 當前配置：")
        print(f"   use_unified_weights: {setting.use_unified_weights}")
        
        # 測試統一權重模式（use_unified_weights=True）
        print(f"\n" + "="*60)
        print("測試 1：統一權重模式（use_unified_weights=True）")
        print("="*60)
        
        setting.use_unified_weights = True
        setting.save()
        
        # 清除快取
        manager = get_threshold_manager()
        manager.refresh_cache()
        
        stage1_threshold = manager.get_threshold('protocol_assistant', stage=1)
        stage1_title, stage1_content = manager.get_weights('protocol_assistant', stage=1)
        
        stage2_threshold = manager.get_threshold('protocol_assistant', stage=2)
        stage2_title, stage2_content = manager.get_weights('protocol_assistant', stage=2)
        
        print(f"\n📊 Stage 1：")
        print(f"   Threshold: {stage1_threshold}")
        print(f"   Weights: {stage1_title*100:.0f}% / {stage1_content*100:.0f}%")
        
        print(f"\n📊 Stage 2：")
        print(f"   Threshold: {stage2_threshold}")
        print(f"   Weights: {stage2_title*100:.0f}% / {stage2_content*100:.0f}%")
        
        if stage1_threshold == stage2_threshold and stage1_title == stage2_title:
            print(f"\n✅ 統一權重模式：Stage 1 和 Stage 2 使用相同配置（預期行為）")
        else:
            print(f"\n❌ 統一權重模式：Stage 1 和 Stage 2 配置不同（非預期行為）")
        
        # 測試獨立權重模式（use_unified_weights=False）
        print(f"\n" + "="*60)
        print("測試 2：獨立權重模式（use_unified_weights=False）")
        print("="*60)
        
        setting.use_unified_weights = False
        setting.save()
        
        # 清除快取
        manager.refresh_cache()
        
        stage1_threshold = manager.get_threshold('protocol_assistant', stage=1)
        stage1_title, stage1_content = manager.get_weights('protocol_assistant', stage=1)
        
        stage2_threshold = manager.get_threshold('protocol_assistant', stage=2)
        stage2_title, stage2_content = manager.get_weights('protocol_assistant', stage=2)
        
        print(f"\n📊 Stage 1（段落搜尋）：")
        print(f"   Threshold: {stage1_threshold}")
        print(f"   Weights: {stage1_title*100:.0f}% / {stage1_content*100:.0f}%")
        
        print(f"\n📊 Stage 2（全文搜尋）：")
        print(f"   Threshold: {stage2_threshold}")
        print(f"   Weights: {stage2_title*100:.0f}% / {stage2_content*100:.0f}%")
        
        if stage1_threshold != stage2_threshold or stage1_title != stage2_title:
            print(f"\n✅ 獨立權重模式：Stage 1 和 Stage 2 使用不同配置（預期行為）")
            
            # 顯示差異
            print(f"\n📈 配置差異：")
            print(f"   Threshold 差異: {stage1_threshold} -> {stage2_threshold} (Δ {stage2_threshold - stage1_threshold:+.2f})")
            print(f"   Title Weight 差異: {stage1_title*100:.0f}% -> {stage2_title*100:.0f}% (Δ {(stage2_title - stage1_title)*100:+.0f}%)")
            print(f"   Content Weight 差異: {stage1_content*100:.0f}% -> {stage2_content*100:.0f}% (Δ {(stage2_content - stage1_content)*100:+.0f}%)")
        else:
            print(f"\n❌ 獨立權重模式：Stage 1 和 Stage 2 使用相同配置（非預期行為）")
        
        # 恢復為統一權重模式
        print(f"\n" + "="*60)
        print("🔄 恢復為統一權重模式")
        print("="*60)
        
        setting.use_unified_weights = True
        setting.save()
        manager.refresh_cache()
        
        print(f"\n✅ 已恢復為 use_unified_weights=True")
        
        print(f"\n" + "="*70)
        print("🎉 兩階段權重切換測試完成！")
        print("="*70)
        
        return 0
    
    except Exception as e:
        print(f"\n❌ 測試失敗：{str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
