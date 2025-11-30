#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OCR Function API 完整測試
=========================

測試 OCR Function Dify API 配置的完整功能：
1. 配置正確性驗證
2. API 連接測試  
3. 圖片 OCR 測試
4. 錯誤處理測試

使用方式：
    docker exec ai-django python tests/test_dify_integration/test_ocr_function.py
"""

import os
import sys
import base64
import json
import requests
from pathlib import Path

# 設置 Django 環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')

import django
django.setup()

from library.config.dify_config_manager import (
    get_ocr_function_config,
    get_ocr_function_config_dict,
    DifyConfigManager
)


class TestResult:
    """測試結果類別"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def add_pass(self, test_name):
        self.passed += 1
        print(f"  ✅ {test_name}")
    
    def add_fail(self, test_name, reason):
        self.failed += 1
        self.errors.append((test_name, reason))
        print(f"  ❌ {test_name}: {reason}")
    
    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"測試結果: {self.passed}/{total} 通過")
        if self.errors:
            print(f"\n失敗的測試:")
            for name, reason in self.errors:
                print(f"  - {name}: {reason}")
        print(f"{'='*60}")
        return self.failed == 0


def test_config_exists():
    """測試配置是否存在"""
    result = TestResult()
    print("\n📋 測試 1: 配置存在性測試")
    
    try:
        config = get_ocr_function_config()
        if config is not None:
            result.add_pass("get_ocr_function_config() 返回配置對象")
        else:
            result.add_fail("get_ocr_function_config()", "返回 None")
    except Exception as e:
        result.add_fail("get_ocr_function_config()", str(e))
    
    try:
        config_dict = get_ocr_function_config_dict()
        if isinstance(config_dict, dict):
            result.add_pass("get_ocr_function_config_dict() 返回字典")
        else:
            result.add_fail("get_ocr_function_config_dict()", f"返回 {type(config_dict)}")
    except Exception as e:
        result.add_fail("get_ocr_function_config_dict()", str(e))
    
    return result


def test_config_values():
    """測試配置值正確性"""
    result = TestResult()
    print("\n📋 測試 2: 配置值正確性測試")
    
    try:
        config = get_ocr_function_config()
        
        # 檢查 API Key
        if config.api_key and config.api_key.startswith('app-'):
            result.add_pass(f"API Key 格式正確: {config.api_key[:15]}...")
        else:
            result.add_fail("API Key", f"格式不正確: {config.api_key}")
        
        # 檢查 App Name
        if config.app_name == 'OCR Function':
            result.add_pass(f"App Name 正確: {config.app_name}")
        else:
            result.add_fail("App Name", f"期望 'OCR Function'，得到 '{config.app_name}'")
        
        # 檢查 Workspace
        if config.workspace == 'OCR_Function':
            result.add_pass(f"Workspace 正確: {config.workspace}")
        else:
            result.add_fail("Workspace", f"期望 'OCR_Function'，得到 '{config.workspace}'")
        
        # 檢查 Timeout
        if config.timeout == 90:
            result.add_pass(f"Timeout 正確: {config.timeout}s")
        else:
            result.add_fail("Timeout", f"期望 90，得到 {config.timeout}")
        
        # 檢查 API URL
        if config.api_url and 'v1/chat-messages' in config.api_url:
            result.add_pass(f"API URL 正確: {config.api_url}")
        else:
            result.add_fail("API URL", f"格式不正確: {config.api_url}")
        
        # 檢查 Response Mode
        if config.response_mode == 'blocking':
            result.add_pass(f"Response Mode 正確: {config.response_mode}")
        else:
            result.add_fail("Response Mode", f"期望 'blocking'，得到 '{config.response_mode}'")
            
    except Exception as e:
        result.add_fail("配置值測試", str(e))
    
    return result


def test_supported_apps():
    """測試 SUPPORTED_APPS 是否包含 OCR Function"""
    result = TestResult()
    print("\n📋 測試 3: SUPPORTED_APPS 測試")
    
    try:
        supported = DifyConfigManager.SUPPORTED_APPS
        
        if 'ocr_function' in supported:
            result.add_pass("'ocr_function' 已加入 SUPPORTED_APPS")
        else:
            result.add_fail("SUPPORTED_APPS", "'ocr_function' 不在支援列表中")
        
        if supported.get('ocr_function') == 'OCR Function':
            result.add_pass("SUPPORTED_APPS 值正確: 'OCR Function'")
        else:
            result.add_fail("SUPPORTED_APPS 值", f"期望 'OCR Function'，得到 '{supported.get('ocr_function')}'")
            
    except Exception as e:
        result.add_fail("SUPPORTED_APPS 測試", str(e))
    
    return result


def test_config_validate():
    """測試配置驗證功能"""
    result = TestResult()
    print("\n📋 測試 4: 配置驗證測試")
    
    try:
        config = get_ocr_function_config()
        
        if config.validate():
            result.add_pass("config.validate() 返回 True")
        else:
            result.add_fail("config.validate()", "驗證失敗")
        
        safe_config = config.get_safe_config()
        if 'api_key_prefix' in safe_config:
            result.add_pass(f"安全配置 API Key 前綴: {safe_config['api_key_prefix']}")
        else:
            result.add_fail("安全配置", "缺少 api_key_prefix")
            
    except Exception as e:
        result.add_fail("配置驗證測試", str(e))
    
    return result


def test_api_connection():
    """測試 API 連接"""
    result = TestResult()
    print("\n📋 測試 5: API 連接測試")
    
    try:
        config = get_ocr_function_config()
        
        # 發送簡單測試請求
        headers = {
            'Authorization': f'Bearer {config.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'inputs': {},
            'query': '測試連接',
            'response_mode': 'blocking',
            'user': 'test_user'
        }
        
        response = requests.post(
            config.api_url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result.add_pass(f"API 連接成功 (HTTP {response.status_code})")
            
            data = response.json()
            if 'answer' in data:
                result.add_pass("收到 AI 回應")
                print(f"    回應預覽: {data['answer'][:100]}...")
            else:
                result.add_fail("API 回應", "缺少 'answer' 欄位")
        else:
            result.add_fail("API 連接", f"HTTP {response.status_code}: {response.text[:200]}")
            
    except requests.Timeout:
        result.add_fail("API 連接", "請求超時")
    except requests.ConnectionError as e:
        result.add_fail("API 連接", f"連接錯誤: {str(e)}")
    except Exception as e:
        result.add_fail("API 連接測試", str(e))
    
    return result


def test_image_ocr(image_path=None):
    """測試圖片 OCR 功能"""
    result = TestResult()
    print("\n📋 測試 6: 圖片 OCR 測試")
    
    # 如果沒有指定圖片，使用預設測試圖片
    if image_path is None:
        default_paths = [
            '/home/user/codes/ai-platform-web/螢幕擷取畫面 2025-11-30 141051.jpg',
            '/app/螢幕擷取畫面 2025-11-30 141051.jpg',
        ]
        for path in default_paths:
            if os.path.exists(path):
                image_path = path
                break
    
    if image_path is None or not os.path.exists(image_path):
        result.add_fail("圖片 OCR", f"找不到測試圖片: {image_path}")
        print("    提示: 請確認圖片路徑是否正確")
        return result
    
    try:
        config = get_ocr_function_config()
        
        # 讀取圖片並轉換為 Base64
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        image_size = len(image_data) / 1024  # KB
        result.add_pass(f"圖片讀取成功: {os.path.basename(image_path)} ({image_size:.1f} KB)")
        
        # 判斷圖片類型
        if image_path.lower().endswith('.png'):
            mime_type = 'image/png'
        elif image_path.lower().endswith(('.jpg', '.jpeg')):
            mime_type = 'image/jpeg'
        else:
            mime_type = 'image/jpeg'
        
        # 發送 OCR 請求
        headers = {
            'Authorization': f'Bearer {config.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'inputs': {},
            'query': '請辨識這張圖片中的所有文字內容',
            'response_mode': 'blocking',
            'user': 'test_user',
            'files': [
                {
                    'type': 'image',
                    'transfer_method': 'local_file',
                    'upload_file_id': None,
                    'url': f'data:{mime_type};base64,{image_base64}'
                }
            ]
        }
        
        print(f"    正在發送 OCR 請求...")
        response = requests.post(
            config.api_url,
            headers=headers,
            json=payload,
            timeout=config.timeout
        )
        
        if response.status_code == 200:
            result.add_pass(f"OCR API 請求成功 (HTTP {response.status_code})")
            
            data = response.json()
            if 'answer' in data:
                result.add_pass("收到 OCR 結果")
                print(f"\n    📝 OCR 辨識結果:")
                print(f"    {'-'*50}")
                print(f"    {data['answer']}")
                print(f"    {'-'*50}")
                
                # 顯示額外資訊
                if 'metadata' in data:
                    metadata = data['metadata']
                    if 'usage' in metadata:
                        usage = metadata['usage']
                        print(f"\n    📊 Token 使用:")
                        print(f"       - 輸入 Token: {usage.get('prompt_tokens', 'N/A')}")
                        print(f"       - 輸出 Token: {usage.get('completion_tokens', 'N/A')}")
                        print(f"       - 總計 Token: {usage.get('total_tokens', 'N/A')}")
            else:
                result.add_fail("OCR 結果", "缺少 'answer' 欄位")
        else:
            result.add_fail("OCR API 請求", f"HTTP {response.status_code}: {response.text[:300]}")
            
    except requests.Timeout:
        result.add_fail("OCR API 請求", f"請求超時 (>{config.timeout}s)")
    except Exception as e:
        result.add_fail("圖片 OCR 測試", str(e))
    
    return result


def main():
    """執行所有測試"""
    print("=" * 60)
    print("🔍 OCR Function API 完整測試")
    print("=" * 60)
    
    all_results = []
    
    # 執行所有測試
    all_results.append(test_config_exists())
    all_results.append(test_config_values())
    all_results.append(test_supported_apps())
    all_results.append(test_config_validate())
    all_results.append(test_api_connection())
    all_results.append(test_image_ocr())
    
    # 統計總結果
    total_passed = sum(r.passed for r in all_results)
    total_failed = sum(r.failed for r in all_results)
    total_tests = total_passed + total_failed
    
    print("\n" + "=" * 60)
    print(f"📊 總測試結果: {total_passed}/{total_tests} 通過")
    
    if total_failed > 0:
        print(f"\n❌ 有 {total_failed} 個測試失敗")
        for r in all_results:
            for name, reason in r.errors:
                print(f"   - {name}: {reason}")
        return 1
    else:
        print("\n✅ 所有測試通過！")
        return 0


if __name__ == '__main__':
    sys.exit(main())
