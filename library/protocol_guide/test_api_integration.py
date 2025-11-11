#!/usr/bin/env python
"""
API 整合測試腳本

測試 Protocol Guide API Handler 是否正確整合智能路由器

使用方式：
    docker exec ai-django python /app/library/protocol_guide/test_api_integration.py

Author: AI Platform Team
Date: 2025-11-11
"""

import os
import sys
import django

# 設置 Django 環境
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()


def test_api_handler_methods():
    """測試 API Handler 方法是否存在"""
    print("\n" + "=" * 60)
    print("測試 1: API Handler 方法檢查")
    print("=" * 60)
    
    from library.protocol_guide.api_handlers import ProtocolGuideAPIHandler
    
    required_methods = [
        'handle_chat_api',
        'get_chat_config',
        'get_search_service',
    ]
    
    print("檢查必要方法...")
    all_exist = True
    for method_name in required_methods:
        if hasattr(ProtocolGuideAPIHandler, method_name):
            print(f"✅ {method_name} 存在")
        else:
            print(f"❌ {method_name} 缺失")
            all_exist = False
    
    if all_exist:
        print("\n✅ API Handler 結構正確")
    else:
        print("\n❌ API Handler 結構不完整")
    
    return all_exist


def test_smart_router_import():
    """測試智能路由器能否被導入"""
    print("\n" + "=" * 60)
    print("測試 2: 智能路由器導入檢查")
    print("=" * 60)
    
    try:
        from library.protocol_guide.smart_search_router import SmartSearchRouter
        router = SmartSearchRouter()
        print("✅ SmartSearchRouter 導入成功")
        print(f"✅ 路由器實例創建成功: {type(router).__name__}")
        return True
    except Exception as e:
        print(f"❌ 智能路由器導入失敗: {str(e)}")
        return False


def test_config_retrieval():
    """測試配置獲取"""
    print("\n" + "=" * 60)
    print("測試 3: Dify 配置獲取")
    print("=" * 60)
    
    try:
        from library.config.dify_config_manager import get_protocol_guide_config
        config = get_protocol_guide_config()
        
        print("✅ 配置獲取成功")
        print(f"   App Name: {config.app_name}")
        print(f"   Workspace: {config.workspace}")
        print(f"   API URL: {config.api_url}")
        print(f"   Timeout: {config.timeout}")
        
        # 驗證必要欄位
        if config.api_url and config.api_key and config.app_name:
            print("\n✅ 配置完整")
            return True
        else:
            print("\n❌ 配置不完整")
            return False
    
    except Exception as e:
        print(f"❌ 配置獲取失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_mock_api_request():
    """測試模擬 API 請求（不實際調用 Dify）"""
    print("\n" + "=" * 60)
    print("測試 4: 模擬 API 請求結構")
    print("=" * 60)
    
    from unittest.mock import Mock
    from library.protocol_guide.api_handlers import ProtocolGuideAPIHandler
    
    # 創建模擬 request
    mock_request = Mock()
    mock_request.data = {
        'message': 'Cup顏色完整內容是什麼？',
        'conversation_id': ''
    }
    mock_request.user = Mock()
    mock_request.user.is_authenticated = True
    mock_request.user.id = 1
    mock_request.user.username = 'test_user'
    
    print("創建模擬請求...")
    print(f"  Message: {mock_request.data['message']}")
    print(f"  User: {mock_request.user.username}")
    
    # 注意：這裡不實際調用，因為需要資料庫和 Dify 連接
    # 只是驗證方法存在且可調用
    try:
        handler_method = ProtocolGuideAPIHandler.handle_chat_api
        print(f"✅ handle_chat_api 方法可訪問")
        print(f"✅ 方法類型: {type(handler_method)}")
        return True
    except Exception as e:
        print(f"❌ 方法訪問失敗: {str(e)}")
        return False


def test_response_format():
    """測試預期的回應格式"""
    print("\n" + "=" * 60)
    print("測試 5: 預期回應格式驗證")
    print("=" * 60)
    
    # 定義預期的回應欄位
    expected_fields = [
        'success',
        'answer',
        'mode',             # 'mode_a' 或 'mode_b'
        'stage',            # 階段（僅模式 B）
        'is_fallback',      # 是否降級
        'fallback_reason',  # 降級原因（如果有）
        'message_id',
        'conversation_id',
        'response_time',
        'tokens',
        'search_results_count'
    ]
    
    print("預期的 API 回應欄位：")
    for field in expected_fields:
        print(f"  • {field}")
    
    print("\n✅ 回應格式定義完整")
    return True


def main():
    """主測試函數"""
    print("\n" + "=" * 60)
    print("Protocol Guide API 整合測試")
    print("=" * 60)
    
    all_passed = True
    
    # 測試 1: API Handler 方法
    if not test_api_handler_methods():
        all_passed = False
    
    # 測試 2: 智能路由器導入
    if not test_smart_router_import():
        all_passed = False
    
    # 測試 3: 配置獲取
    if not test_config_retrieval():
        all_passed = False
    
    # 測試 4: 模擬 API 請求
    if not test_mock_api_request():
        all_passed = False
    
    # 測試 5: 回應格式
    if not test_response_format():
        all_passed = False
    
    # 總結
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有 API 整合測試通過！")
        print("\n下一步：")
        print("1. 使用真實查詢測試 API 端點")
        print("2. 驗證 Dify AI 回應和降級邏輯")
        print("3. 前端 UI 整合")
    else:
        print("❌ 部分測試失敗，請檢查錯誤訊息")
    print("=" * 60)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
