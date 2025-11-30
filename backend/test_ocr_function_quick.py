#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OCR Function API 快速測試
=========================

快速驗證 OCR Function 配置和 API 連接。
這個測試腳本專注於基本功能驗證，執行時間短。

使用方式：
    docker exec ai-django python tests/test_dify_integration/test_ocr_function_quick.py
"""

import os
import sys
import requests

# 設置 Django 環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')

import django
django.setup()

from library.config.dify_config_manager import (
    get_ocr_function_config,
    DifyConfigManager
)


def main():
    """快速測試主函數"""
    print("=" * 60)
    print("🚀 OCR Function API 快速測試")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    # 測試 1: 配置載入
    print("\n📋 測試 1: 配置載入")
    try:
        config = get_ocr_function_config()
        print(f"  ✅ 配置載入成功")
        print(f"     App Name: {config.app_name}")
        print(f"     Workspace: {config.workspace}")
        print(f"     API URL: {config.api_url}")
        print(f"     API Key: {config.api_key[:15]}...")
        print(f"     Timeout: {config.timeout}s")
        passed += 1
    except Exception as e:
        print(f"  ❌ 配置載入失敗: {e}")
        failed += 1
        return 1
    
    # 測試 2: SUPPORTED_APPS
    print("\n📋 測試 2: SUPPORTED_APPS 檢查")
    if 'ocr_function' in DifyConfigManager.SUPPORTED_APPS:
        print(f"  ✅ 'ocr_function' 已在 SUPPORTED_APPS 中")
        passed += 1
    else:
        print(f"  ❌ 'ocr_function' 未在 SUPPORTED_APPS 中")
        failed += 1
    
    # 測試 3: 配置驗證
    print("\n📋 測試 3: 配置驗證")
    if config.validate():
        print(f"  ✅ 配置驗證通過")
        passed += 1
    else:
        print(f"  ❌ 配置驗證失敗")
        failed += 1
    
    # 測試 4: API 連接
    print("\n📋 測試 4: API 連接測試")
    try:
        headers = {
            'Authorization': f'Bearer {config.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'inputs': {},
            'query': '你好，這是連接測試。請簡單回應。',
            'response_mode': 'blocking',
            'user': 'quick_test'
        }
        
        print(f"  正在連接 {config.api_url}...")
        response = requests.post(
            config.api_url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ API 連接成功 (HTTP 200)")
            if 'answer' in data:
                answer_preview = data['answer'][:80] + '...' if len(data['answer']) > 80 else data['answer']
                print(f"     AI 回應: {answer_preview}")
            passed += 1
        else:
            print(f"  ❌ API 連接失敗 (HTTP {response.status_code})")
            print(f"     錯誤: {response.text[:200]}")
            failed += 1
            
    except requests.Timeout:
        print(f"  ❌ API 連接超時")
        failed += 1
    except requests.ConnectionError as e:
        print(f"  ❌ 連接錯誤: {e}")
        failed += 1
    except Exception as e:
        print(f"  ❌ API 測試失敗: {e}")
        failed += 1
    
    # 總結
    total = passed + failed
    print("\n" + "=" * 60)
    print(f"📊 測試結果: {passed}/{total} 通過")
    
    if failed == 0:
        print("✅ 快速測試全部通過！")
        print("\n💡 提示: 執行完整測試請使用:")
        print("   docker exec ai-django python tests/test_dify_integration/test_ocr_function.py")
        return 0
    else:
        print(f"❌ 有 {failed} 個測試失敗")
        return 1


if __name__ == '__main__':
    sys.exit(main())
