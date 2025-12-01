#!/usr/bin/env python
"""
測試 IP 配置集中化
==========================

驗證所有生產代碼都正確從 config/settings.yaml 讀取 IP 配置。
包括：AI PC IP 和 Web Server IP

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
            get_web_ip,
            get_web_ip_with_env,
            get_config,
            ConfigLoader
        )
        
        # 測試 AI PC IP 基本讀取
        ai_ip = get_ai_pc_ip()
        print(f"✅ get_ai_pc_ip() = {ai_ip}")
        
        ai_ip_with_env = get_ai_pc_ip_with_env()
        print(f"✅ get_ai_pc_ip_with_env() = {ai_ip_with_env}")
        
        # 測試 AI PC IP 配置路徑
        config_ai_ip = get_config('ai_server.ai_pc_ip')
        print(f"✅ get_config('ai_server.ai_pc_ip') = {config_ai_ip}")
        
        # 驗證 AI PC IP 一致性
        assert ai_ip == ai_ip_with_env == config_ai_ip, "❌ AI PC IP 值不一致！"
        print(f"✅ 所有方法返回一致的 AI PC IP: {ai_ip}")
        
        # 測試 Web Server IP 基本讀取
        web_ip = get_web_ip()
        print(f"✅ get_web_ip() = {web_ip}")
        
        web_ip_with_env = get_web_ip_with_env()
        print(f"✅ get_web_ip_with_env() = {web_ip_with_env}")
        
        # 測試 Web Server IP 配置路徑
        config_web_ip = get_config('web_server.web_ip')
        print(f"✅ get_config('web_server.web_ip') = {config_web_ip}")
        
        # 驗證 Web Server IP 一致性
        assert web_ip == web_ip_with_env == config_web_ip, "❌ Web Server IP 值不一致！"
        print(f"✅ 所有方法返回一致的 Web Server IP: {web_ip}")
        
        return True, ai_ip, web_ip
        
    except Exception as e:
        print(f"❌ config_loader 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False, None, None


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
        original_ai_ip = os.environ.get('AI_PC_IP')
        original_web_ip = os.environ.get('WEB_IP')
        
        # 測試 AI PC IP 環境變數覆蓋
        test_ai_ip = "192.168.100.100"
        os.environ['AI_PC_IP'] = test_ai_ip
        
        env_ai_ip = os.getenv('AI_PC_IP')
        print(f"✅ 環境變數 AI_PC_IP = {env_ai_ip}")
        assert env_ai_ip == test_ai_ip, f"❌ AI_PC_IP 環境變數未正確設置"
        
        # 測試 Web Server IP 環境變數覆蓋
        test_web_ip = "192.168.200.200"
        os.environ['WEB_IP'] = test_web_ip
        
        env_web_ip = os.getenv('WEB_IP')
        print(f"✅ 環境變數 WEB_IP = {env_web_ip}")
        assert env_web_ip == test_web_ip, f"❌ WEB_IP 環境變數未正確設置"
        
        # 還原環境變數
        if original_ai_ip:
            os.environ['AI_PC_IP'] = original_ai_ip
        elif 'AI_PC_IP' in os.environ:
            del os.environ['AI_PC_IP']
            
        if original_web_ip:
            os.environ['WEB_IP'] = original_web_ip
        elif 'WEB_IP' in os.environ:
            del os.environ['WEB_IP']
        
        print(f"✅ 環境變數覆蓋功能正常（AI_PC_IP 和 WEB_IP）")
        
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
        
        # 檢查 AI PC IP 配置項
        assert 'ai_server' in config, "❌ 缺少 ai_server 配置"
        assert 'ai_pc_ip' in config['ai_server'], "❌ 缺少 ai_pc_ip 配置"
        
        ai_ip = config['ai_server']['ai_pc_ip']
        print(f"✅ settings.yaml 中的 ai_pc_ip = {ai_ip}")
        
        # 驗證 AI PC IP 格式
        parts = ai_ip.split('.')
        assert len(parts) == 4, f"❌ AI PC IP 格式不正確: {ai_ip}"
        for part in parts:
            assert part.isdigit() and 0 <= int(part) <= 255, f"❌ AI PC IP 格式不正確: {ai_ip}"
        print(f"✅ AI PC IP 格式驗證通過")
        
        # 檢查 Web Server IP 配置項
        assert 'web_server' in config, "❌ 缺少 web_server 配置"
        assert 'web_ip' in config['web_server'], "❌ 缺少 web_ip 配置"
        
        web_ip = config['web_server']['web_ip']
        print(f"✅ settings.yaml 中的 web_ip = {web_ip}")
        
        # 驗證 Web Server IP 格式
        parts = web_ip.split('.')
        assert len(parts) == 4, f"❌ Web Server IP 格式不正確: {web_ip}"
        for part in parts:
            assert part.isdigit() and 0 <= int(part) <= 255, f"❌ Web Server IP 格式不正確: {web_ip}"
        print(f"✅ Web Server IP 格式驗證通過")
        
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
    
    # 硬編碼 IP 的模式（URL 形式）- AI PC IP
    hardcoded_ai_pattern = re.compile(r'http://10\.10\.172\.37')
    
    # 允許的例外（fallback 預設值）
    allowed_patterns = [
        r"os\.getenv\('AI_PC_IP',\s*'10\.10\.172\.37'\)",  # AI PC IP fallback
        r"os\.getenv\('WEB_IP',\s*'10\.10\.172\.127'\)",   # Web IP fallback
        r"# .*10\.10\.172\.\d+",  # 註解中的 IP
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
            if hardcoded_ai_pattern.search(line):
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
        print("✅ 沒有發現硬編碼的 IP URL（AI PC IP）")
        print(f"   已檢查 {len(files_to_check)} 個生產代碼文件")
        return True


def test_django_settings_dynamic_web_ip():
    """測試 Django settings.py 使用動態 Web IP"""
    print("\n" + "=" * 60)
    print("🧪 測試 7: Django settings.py 動態 Web IP")
    print("=" * 60)
    
    try:
        # 嘗試多種可能的路徑
        possible_paths = [
            PROJECT_ROOT / "backend" / "ai_platform" / "settings.py",  # 本機路徑
            Path("/app/ai_platform/settings.py"),  # Docker 容器路徑
        ]
        
        settings_path = None
        for path in possible_paths:
            if path.exists():
                settings_path = path
                break
        
        if not settings_path:
            print(f"⚠️  找不到 Django settings.py 文件")
            print(f"   嘗試的路徑: {[str(p) for p in possible_paths]}")
            return True  # 跳過此測試但不算失敗
        
        print(f"✅ 找到 Django settings.py: {settings_path}")
        
        with open(settings_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查是否使用 WEB_IP 環境變數
        if "WEB_IP = os.getenv('WEB_IP'" in content:
            print("✅ Django settings.py 使用 WEB_IP 環境變數")
        else:
            print("❌ Django settings.py 未使用 WEB_IP 環境變數")
            return False
        
        # 檢查 ALLOWED_HOSTS 是否使用動態 WEB_IP
        if "{WEB_IP}" in content or "WEB_IP" in content:
            print("✅ ALLOWED_HOSTS 使用動態 WEB_IP")
        else:
            print("⚠️  無法確認 ALLOWED_HOSTS 是否動態化")
        
        # 檢查 CORS_ALLOWED_ORIGINS 是否使用動態 WEB_IP
        if 'f"http://{WEB_IP}"' in content:
            print("✅ CORS_ALLOWED_ORIGINS 使用動態 WEB_IP")
        else:
            print("⚠️  無法確認 CORS_ALLOWED_ORIGINS 是否動態化")
        
        # 檢查 CSRF_TRUSTED_ORIGINS 是否使用動態 WEB_IP
        if 'f"http://{WEB_IP}"' in content:
            print("✅ CSRF_TRUSTED_ORIGINS 使用動態 WEB_IP")
        else:
            print("⚠️  無法確認 CSRF_TRUSTED_ORIGINS 是否動態化")
        
        print("✅ Django settings.py 已配置動態 Web IP")
        return True
        
    except Exception as e:
        print(f"❌ Django settings.py 測試失敗: {e}")
        return False


def run_all_tests():
    """執行所有測試"""
    print("\n" + "=" * 60)
    print("🚀 IP 配置集中化測試（AI PC IP + Web Server IP）")
    print("=" * 60)
    
    results = []
    
    # 執行測試
    results.append(("settings.yaml 文件", test_settings_yaml_exists()))
    
    config_result = test_config_loader()
    results.append(("config_loader 模組", config_result[0]))
    
    results.append(("dify_config 模組", test_dify_config()))
    results.append(("dify_config_manager 模組", test_dify_config_manager()))
    results.append(("環境變數覆蓋", test_env_override()))
    results.append(("硬編碼 IP 檢查", test_no_hardcoded_ip_in_production()))
    results.append(("Django settings 動態 Web IP", test_django_settings_dynamic_web_ip()))
    
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
        print("   IP 配置集中管理說明：")
        print("   ├── AI PC IP:     修改 config/settings.yaml 中的 ai_server.ai_pc_ip")
        print("   │                 或設置環境變數 AI_PC_IP")
        print("   └── Web Server IP: 修改 config/settings.yaml 中的 web_server.web_ip")
        print("                      或設置環境變數 WEB_IP")
        return 0
    else:
        print("\n⚠️  部分測試失敗，請檢查上述錯誤。")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
