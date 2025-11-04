#!/usr/bin/env python
"""
初始化 Threshold 設定 - 為 Protocol 和 RVT Assistant 創建預設值
"""

import os
import sys
import django

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.models import SearchThresholdSetting
from django.contrib.auth.models import User

def init_threshold_settings():
    """初始化 threshold 設定"""
    print("=" * 80)
    print("🎯 初始化 Threshold 設定")
    print("=" * 80)
    
    # 獲取管理員用戶（用於 updated_by）
    try:
        admin_user = User.objects.filter(is_staff=True).first()
        if not admin_user:
            admin_user = User.objects.filter(is_superuser=True).first()
    except:
        admin_user = None
    
    # 定義預設設定
    default_settings = [
        {
            'assistant_type': 'protocol_assistant',
            'master_threshold': 0.75,
            'description': 'Protocol Assistant 的預設 threshold 設定。段落向量使用 0.75，文檔向量自動計算為 0.64 (0.75*0.85)，關鍵字自動計算為 0.38 (0.75*0.5)。',
        },
        {
            'assistant_type': 'rvt_assistant',
            'master_threshold': 0.70,
            'description': 'RVT Assistant 的預設 threshold 設定。段落向量使用 0.70，文檔向量自動計算為 0.60 (0.70*0.85)，關鍵字自動計算為 0.35 (0.70*0.5)。',
        },
    ]
    
    # 創建或更新設定
    for setting_data in default_settings:
        assistant_type = setting_data['assistant_type']
        
        setting, created = SearchThresholdSetting.objects.get_or_create(
            assistant_type=assistant_type,
            defaults={
                'master_threshold': setting_data['master_threshold'],
                'description': setting_data['description'],
                'is_active': True,
                'updated_by': admin_user,
            }
        )
        
        if created:
            print(f"\n✅ 創建新設定:")
            print(f"   Assistant: {setting.get_assistant_type_display()}")
            print(f"   Master Threshold: {setting.master_threshold}")
            print(f"   計算後的 threshold:")
            thresholds = setting.get_calculated_thresholds()
            for key, value in thresholds.items():
                print(f"     - {key}: {value}")
        else:
            print(f"\n⚠️ 設定已存在:")
            print(f"   Assistant: {setting.get_assistant_type_display()}")
            print(f"   當前 Master Threshold: {setting.master_threshold}")
            print(f"   （若要更新，請使用 Web 管理介面）")
    
    print("\n" + "=" * 80)
    print("✅ Threshold 設定初始化完成")
    print("=" * 80)
    
    # 顯示所有設定
    print("\n📊 當前所有 Threshold 設定:")
    all_settings = SearchThresholdSetting.objects.filter(is_active=True)
    for setting in all_settings:
        print(f"\n{setting.get_assistant_type_display()}:")
        print(f"  Master Threshold: {setting.master_threshold}")
        print(f"  計算後的 threshold:")
        thresholds = setting.get_calculated_thresholds()
        for key, value in thresholds.items():
            print(f"    - {key}: {value}")
        print(f"  說明: {setting.description}")

if __name__ == "__main__":
    try:
        init_threshold_settings()
    except Exception as e:
        print(f"\n❌ 初始化失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
