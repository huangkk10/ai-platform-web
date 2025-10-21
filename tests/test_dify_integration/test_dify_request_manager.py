"""
測試新的 Dify 請求管理器功能
驗證 library/dify_integration/request_manager.py 是否正常工作
"""

import sys
import os

# 添加路徑以便導入 library
sys.path.insert(0, '/home/user/codes/ai-platform-web/')

def test_import_functionality():
    """測試 library 導入功能"""
    try:
        from library.dify_integration import (
            DifyRequestManager, 
            DifyResponseHandler, 
            make_dify_request,
            process_dify_answer,
            handle_conversation_error
        )
        print("✅ 成功導入所有 Dify 請求管理組件")
        return True
    except ImportError as e:
        print(f"❌ 導入失敗: {e}")
        return False


def test_request_manager():
    """測試請求管理器基本功能"""
    try:
        from library.dify_integration import DifyRequestManager
        
        # 創建請求管理器實例
        manager = DifyRequestManager(max_retries=2, retry_delay=0.5)
        print("✅ 成功創建 DifyRequestManager 實例")
        
        # 檢查屬性
        assert manager.max_retries == 2
        assert manager.retry_delay == 0.5
        assert manager.default_timeout == 60
        print("✅ DifyRequestManager 屬性設置正確")
        
        return True
    except Exception as e:
        print(f"❌ DifyRequestManager 測試失敗: {e}")
        return False


def test_response_handler():
    """測試響應處理器功能"""
    try:
        from library.dify_integration import DifyResponseHandler
        
        # 測試字符串處理
        result1 = DifyResponseHandler.process_answer_field("這是一個正常的回答")
        assert result1 == "這是一個正常的回答"
        print("✅ 字符串 answer 處理正確")
        
        # 測試數組處理
        result2 = DifyResponseHandler.process_answer_field(["這是", "數組", "回答"])
        assert result2 == "這是 數組 回答"
        print("✅ 數組 answer 處理正確")
        
        # 測試空數組處理
        result3 = DifyResponseHandler.process_answer_field([])
        assert "無法提供回答" in result3
        print("✅ 空數組 answer 處理正確")
        
        # 測試其他類型處理
        result4 = DifyResponseHandler.process_answer_field(123)
        assert result4 == "123"
        print("✅ 其他類型 answer 處理正確")
        
        return True
    except Exception as e:
        print(f"❌ DifyResponseHandler 測試失敗: {e}")
        return False


def test_convenience_functions():
    """測試便利函數"""
    try:
        from library.dify_integration import process_dify_answer
        
        # 測試便利函數
        result = process_dify_answer(["測試", "便利", "函數"])
        assert result == "測試 便利 函數"
        print("✅ process_dify_answer 便利函數工作正常")
        
        return True
    except Exception as e:
        print(f"❌ 便利函數測試失敗: {e}")
        return False


def main():
    """主測試函數"""
    print("🚀 開始測試新的 Dify 請求管理器")
    print("=" * 60)
    
    tests = [
        ("導入功能測試", test_import_functionality),
        ("請求管理器測試", test_request_manager), 
        ("響應處理器測試", test_response_handler),
        ("便利函數測試", test_convenience_functions)
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
        print("🎉 所有測試通過！新的 Dify 請求管理器已準備就緒")
        return True
    else:
        print("⚠️  部分測試失敗，請檢查代碼")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)