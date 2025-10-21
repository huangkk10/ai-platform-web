"""
測試新的 Dify 配置管理器
驗證配置管理器是否能正常工作
"""

import sys
import os

# 添加路徑以便導入 library
sys.path.insert(0, '/home/user/codes/ai-platform-web/')

def test_import_config_manager():
    """測試導入配置管理器"""
    try:
        from library.config import (
            DifyConfigManager, 
            DifyAppConfig,
            get_rvt_guide_config,
            get_protocol_known_issue_config,
            validate_all_dify_configs
        )
        print("✅ 成功導入所有配置管理組件")
        return True
    except ImportError as e:
        print(f"❌ 導入失敗: {e}")
        return False


def test_config_manager():
    """測試配置管理器基本功能"""
    try:
        from library.config import DifyConfigManager
        
        # 創建配置管理器
        manager = DifyConfigManager()
        print("✅ 成功創建 DifyConfigManager 實例")
        
        # 獲取支援的應用列表
        apps = manager.list_available_apps()
        print(f"✅ 支援的應用: {list(apps.keys())}")
        
        # 測試獲取 RVT Guide 配置
        rvt_config = manager.get_rvt_guide_config()
        print(f"✅ 成功獲取 RVT Guide 配置: {rvt_config.app_name}")
        
        # 驗證配置
        is_valid = rvt_config.validate()
        print(f"✅ RVT Guide 配置驗證: {'通過' if is_valid else '失敗'}")
        
        return True
    except Exception as e:
        print(f"❌ 配置管理器測試失敗: {e}")
        return False


def test_convenience_functions():
    """測試便利函數"""
    try:
        from library.config import get_rvt_guide_config, get_protocol_known_issue_config
        
        # 測試 RVT Guide 配置
        rvt_config = get_rvt_guide_config()
        print(f"✅ RVT Guide 便利函數: {rvt_config.app_name}")
        
        # 測試 Protocol Known Issue 配置
        protocol_config = get_protocol_known_issue_config()
        print(f"✅ Protocol Known Issue 便利函數: {protocol_config.app_name}")
        
        # 測試配置對象的方法
        safe_config = rvt_config.get_safe_config()
        assert 'api_key_prefix' in safe_config
        assert 'api_key' not in safe_config
        print("✅ 安全配置功能正常")
        
        return True
    except Exception as e:
        print(f"❌ 便利函數測試失敗: {e}")
        return False


def test_backward_compatibility():
    """測試向後兼容性"""
    try:
        # 測試舊的導入方式
        from library.config.dify_app_configs import get_rvt_guide_config as old_get_rvt_guide_config
        
        old_config = old_get_rvt_guide_config()
        print(f"✅ 舊的配置函數正常: {old_config.get('app_name', 'Unknown')}")
        
        # 測試新的配置管理器
        from library.config import get_rvt_guide_config
        
        new_config = get_rvt_guide_config()
        print(f"✅ 新的配置函數正常: {new_config.app_name}")
        
        # 比較配置內容是否一致
        assert old_config['api_key'] == new_config.api_key
        assert old_config['api_url'] == new_config.api_url
        print("✅ 新舊配置內容一致")
        
        return True
    except Exception as e:
        print(f"❌ 向後兼容性測試失敗: {e}")
        return False


def test_validation_and_safety():
    """測試配置驗證和安全功能"""
    try:
        from library.config import validate_all_dify_configs, get_all_dify_configs_safe
        
        # 驗證所有配置
        validation_results = validate_all_dify_configs()
        print(f"✅ 配置驗證結果: {validation_results}")
        
        # 獲取安全配置
        safe_configs = get_all_dify_configs_safe()
        print(f"✅ 安全配置應用數量: {len(safe_configs)}")
        
        # 確保沒有暴露敏感信息
        for app_type, config in safe_configs.items():
            if 'api_key' in config:
                print(f"⚠️  警告: {app_type} 配置中仍包含完整 API key")
                return False
            if 'api_key_prefix' in config:
                print(f"✅ {app_type} API key 已安全處理")
        
        return True
    except Exception as e:
        print(f"❌ 驗證和安全功能測試失敗: {e}")
        return False


def main():
    """主測試函數"""
    print("🚀 開始測試新的 Dify 配置管理器")
    print("=" * 60)
    
    tests = [
        ("導入功能測試", test_import_config_manager),
        ("配置管理器基本功能測試", test_config_manager),
        ("便利函數測試", test_convenience_functions),
        ("向後兼容性測試", test_backward_compatibility),
        ("驗證和安全功能測試", test_validation_and_safety),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        if test_func():
            passed += 1
            print(f"✅ {test_name} 通過")
        else:
            print(f"❌ {test_name} 失敗")
    
    print("\n" + "=" * 60)
    print(f"📊 測試結果: {passed}/{total} 通過")
    
    if passed == total:
        print("🎉 所有測試通過！新的 Dify 配置管理器已準備就緒")
        return True
    else:
        print("⚠️  部分測試失敗，請檢查代碼")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)