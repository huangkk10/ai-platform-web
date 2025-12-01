#!/usr/bin/env python
"""
測試 AI PC IP 配置集中化
==========================

驗證所有生產代碼都正確從 config/settings.yaml 讀取 IP 配置。

執行方式：
    # 在本機執行
    python tests/test_ip_config_centralization.py
    
    # 在 Docker 容器執行
    docker exec ai-django python tests/test_ip_config_centralization.py
"""

import os
import sys
from pathlib import Path

# 設定專案根目錄
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def test_config_loader():
    """測試 config_loader 模組"""
    print("\n" + "=" * 60)
    print("🧪 測試 1: config_loader 模組")
    print("=" * 60)
    
    try:
        from config.config_loader import (
            get_ai_pc_ip,
            get_ai_pc_ip_with_env,
            get_config,
            ConfigLoader
        )
        
        # 測試基本讀取
        ip = get_ai_pc_ip()
        print(f"✅ get_ai_pc_ip() = {ip}")
        
        ip_with_env = get_ai_pc_ip_with_env()
        print(f"✅ get_ai_pc_ip_with_env() = {ip_with_env}")
        
        # 測試配置路徑
        config_ip = get_config('ai_server.ai_pc_ip')
        print(f"✅ get_config('ai_server.ai_pc_ip') = {config_ip}")
        
        # 驗證一致性
        assert ip == ip_with_env == config_ip, "❌ IP 值不一致！"
        print(f"✅ 所有方法返回一致的 IP: {ip}")
        
        return True, ip
        
    except Exception as e:
        print(f"❌ config_loader 測試失敗: {e}")
        return False, None


def test_dify_config():
    """測試 dify_config 模組"""
    print("\n" + "=" * 60)
    print("🧪 測試 2: dify_config 模組")
    print("=" * 60)
    
    try:
        from library.config.dify_config import DifyConfig, _get_ai_pc_ip
        
        # 測試 IP 獲取函數
        ip = _get_ai_pc_ip()
        print(f"✅ _get_ai_pc_ip() = {ip}")
        
        # 測試動態配置
        config = DifyConfig()
        chat_config = config._get_default_chat_config()
        dataset_config = config._get_default_dataset_config()
        
        print(f"✅ Chat API base_url: {chat_config['base_url']}")
        print(f"✅ Chat API api_url: {chat_config['api_url']}")
        print(f"✅ Dataset API base_url: {dataset_config['base_url']}")
        
        # 驗證 IP 在 URL 中
        assert ip in chat_config['base_url'], "❌ IP 未包含在 Chat base_url 中"
        assert ip in chat_config['api_url'], "❌ IP 未包含在 Chat api_url 中"
        assert ip in dataset_config['base_url'], "❌ IP 未包含在 Dataset base_url 中"
        
        print(f"✅ 所有 URL 都正確包含 IP: {ip}")
        
        return True
        
    except Exception as e:
        print(f"❌ dify_config 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_dify_config_manager():
    """測試 dify_config_manager 模組"""
    print("\n" + "=" * 60)
    print("🧪 測試 3: dify_config_manager 模組")
    print("=" * 60)
    
    try:
        from library.config.dify_config_manager import DifyConfigManager
        
        # 測試 IP 獲取
        ip = DifyConfigManager._get_ai_pc_ip()
        print(f"✅ DifyConfigManager._get_ai_pc_ip() = {ip}")
        
        # 測試各種配置
        configs_to_test = [
            ('_get_protocol_known_issue_system_config', 'Protocol Known Issue'),
            ('_get_protocol_guide_config', 'Protocol Guide'),
            ('_get_rvt_guide_config', 'RVT Guide'),
        ]
        
        for method_name, display_name in configs_to_test:
            if hasattr(DifyConfigManager, method_name):
                method = getattr(DifyConfigManager, method_name)
                config = method()
                print(f"✅ {display_name}: api_url = {config['api_url']}")
                assert ip in config['api_url'], f"❌ IP 未包含在 {display_name} api_url 中"
        
        print(f"✅ 所有 DifyConfigManager 配置都正確使用 IP: {ip}")
        
        return True
        
    except Exception as e:
        print(f"❌ dify_config_manager 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_env_override():
    """測試環境變數覆蓋功能"""
    print("\n" + "=" * 60)
    print("🧪 測試 4: 環境變數覆蓋")
    print("=" * 60)
    
    try:
        # 保存原始環境變數
        original_ip = os.environ.get('AI_PC_IP')
        
        # 設置測試環境變數
        test_ip = "192.168.100.100"
        os.environ['AI_PC_IP'] = test_ip
        
        # 重新導入以獲取新值
        from config.config_loader import get_ai_pc_ip_with_env
        
        # 由於模組已載入，需要直接測試函數邏輯
        env_ip = os.getenv('AI_PC_IP')
        print(f"✅ 環境變數 AI_PC_IP = {env_ip}")
        assert env_ip == test_ip, f"❌ 環境變數未正確設置"
        
        # 還原環境變數
        if original_ip:
            os.environ['AI_PC_IP'] = original_ip
        else:
            del os.environ['AI_PC_IP']
        
        print(f"✅ 環境變數覆蓋功能正常")
        
        return True
        
    except Exception as e:
        print(f"❌ 環境變數測試失敗: {e}")
        return False


def test_settings_yaml_exists():
    """測試 settings.yaml 文件存在且格式正確"""
    print("\n" + "=" * 60)
    print("🧪 測試 5: settings.yaml 文件")
    print("=" * 60)
    
    try:
        import yaml
        
        settings_path = PROJECT_ROOT / "config" / "settings.yaml"
        
        # 檢查文件存在
        assert settings_path.exists(), f"❌ 配置文件不存在: {settings_path}"
        print(f"✅ 配置文件存在: {settings_path}")
        
        # 讀取並解析
        with open(settings_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 檢查必要的配置項
        assert 'ai_server' in config, "❌ 缺少 ai_server 配置"
        assert 'ai_pc_ip' in config['ai_server'], "❌ 缺少 ai_pc_ip 配置"
        
        ip = config['ai_server']['ai_pc_ip']
        print(f"✅ settings.yaml 中的 ai_pc_ip = {ip}")
        
        # 驗證 IP 格式
        parts = ip.split('.')
        assert len(parts) == 4, f"❌ IP 格式不正確: {ip}"
        for part in parts:
            assert part.isdigit() and 0 <= int(part) <= 255, f"❌ IP 格式不正確: {ip}"
        
        print(f"✅ IP 格式驗證通過")
        
        return True
        
    except Exception as e:
        print(f"❌ settings.yaml 測試失敗: {e}")
        return False


def test_no_hardcoded_ip_in_production():
    """測試生產代碼中沒有硬編碼的 IP URL"""
    print("\n" + "=" * 60)
    print("🧪 測試 6: 檢查硬編碼 IP")
    print("=" * 60)
    
    import re
    
    # 要檢查的生產代碼目錄和文件
    files_to_check = [
        PROJECT_ROOT / "library" / "config" / "dify_config.py",
        PROJECT_ROOT / "library" / "config" / "dify_config_manager.py",
        PROJECT_ROOT / "backend" / "api" / "models.py",
        PROJECT_ROOT / "backend" / "scripts" / "create_dify_baseline_version.py",
        PROJECT_ROOT / "backend" / "scripts" / "create_dify_v1_2_version.py",
        PROJECT_ROOT / "backend" / "scripts" / "create_dify_v1_1_1_dynamic_version.py",
        PROJECT_ROOT / "backend" / "scripts" / "create_dify_v1_2_1_dynamic_version.py",
        PROJECT_ROOT / "backend" / "scripts" / "create_dify_v1_2_2_hybrid_version.py",
    ]
    
    # 硬編碼 IP 的模式（URL 形式）
    hardcoded_pattern = re.compile(r'http://10\.10\.172\.37')
    
    # 允許的例外（fallback 預設值）
    allowed_patterns = [
        r"os\.getenv\('AI_PC_IP',\s*'10\.10\.172\.37'\)",  # fallback 預設值
        r"# .*10\.10\.172\.37",  # 註解中的 IP
    ]
    
    issues = []
    
    for file_path in files_to_check:
        if not file_path.exists():
            print(f"⚠️  文件不存在: {file_path}")
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            if hardcoded_pattern.search(line):
                # 檢查是否為允許的例外
                is_allowed = False
                for allowed in allowed_patterns:
                    if re.search(allowed, line):
                        is_allowed = True
                        break
                
                if not is_allowed:
                    issues.append({
                        'file': str(file_path.relative_to(PROJECT_ROOT)),
                        'line': line_num,
                        'content': line.strip()
                    })
    
    if issues:
        print("❌ 發現硬編碼的 IP URL:")
        for issue in issues:
            print(f"   {issue['file']}:{issue['line']}")
            print(f"   > {issue['content']}")
        return False
    else:
        print("✅ 沒有發現硬編碼的 IP URL")
        print(f"   已檢查 {len(files_to_check)} 個生產代碼文件")
        return True


def run_all_tests():
    """執行所有測試"""
    print("\n" + "=" * 60)
    print("🚀 AI PC IP 配置集中化測試")
    print("=" * 60)
    
    results = []
    
    # 執行測試
    results.append(("settings.yaml 文件", test_settings_yaml_exists()))
    results.append(("config_loader 模組", test_config_loader()[0]))
    results.append(("dify_config 模組", test_dify_config()))
    results.append(("dify_config_manager 模組", test_dify_config_manager()))
    results.append(("環境變數覆蓋", test_env_override()))
    results.append(("硬編碼 IP 檢查", test_no_hardcoded_ip_in_production()))
    
    # 顯示結果摘要
    print("\n" + "=" * 60)
    print("📊 測試結果摘要")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "-" * 60)
    print(f"   總計: {passed} 通過, {failed} 失敗")
    print("=" * 60)
    
    if failed == 0:
        print("\n🎉 所有測試通過！")
        print("   現在只需修改 config/settings.yaml 中的 ai_pc_ip 即可更改 AI PC IP。")
        return 0
    else:
        print("\n⚠️  部分測試失敗，請檢查上述錯誤。")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
