#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OCR Function 圖片辨識測試
=========================

專門測試 OCR Function API 的圖片文字辨識功能。
支持傳入自定義圖片路徑進行測試。

使用方式：
    # 使用預設測試圖片
    docker exec ai-django python tests/test_dify_integration/test_ocr_function_image.py
    
    # 使用自定義圖片
    docker exec ai-django python tests/test_dify_integration/test_ocr_function_image.py /path/to/image.jpg
"""

import os
import sys
import base64
import requests
import time

# 設置 Django 環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')

import django
django.setup()

from library.config.dify_config_manager import get_ocr_function_config


def get_mime_type(image_path):
    """根據檔案副檔名獲取 MIME 類型"""
    ext = os.path.splitext(image_path)[1].lower()
    mime_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp',
        '.webp': 'image/webp'
    }
    return mime_types.get(ext, 'image/jpeg')


def find_test_image():
    """尋找預設測試圖片"""
    default_paths = [
        '/home/user/codes/ai-platform-web/螢幕擷取畫面 2025-11-30 141051.jpg',
        '/app/螢幕擷取畫面 2025-11-30 141051.jpg',
        '螢幕擷取畫面 2025-11-30 141051.jpg',
    ]
    
    for path in default_paths:
        if os.path.exists(path):
            return path
    
    return None


def test_image_ocr(image_path):
    """執行圖片 OCR 測試"""
    print("=" * 60)
    print("🖼️  OCR Function 圖片辨識測試")
    print("=" * 60)
    
    # 檢查圖片是否存在
    if not os.path.exists(image_path):
        print(f"\n❌ 錯誤: 找不到圖片檔案")
        print(f"   路徑: {image_path}")
        return 1
    
    # 獲取配置
    print("\n📋 步驟 1: 載入 OCR Function 配置")
    try:
        config = get_ocr_function_config()
        print(f"  ✅ 配置載入成功")
        print(f"     API URL: {config.api_url}")
        print(f"     Timeout: {config.timeout}s")
    except Exception as e:
        print(f"  ❌ 配置載入失敗: {e}")
        return 1
    
    # 讀取圖片
    print(f"\n📋 步驟 2: 讀取圖片檔案")
    print(f"   檔案路徑: {image_path}")
    
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        image_size_kb = len(image_data) / 1024
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        mime_type = get_mime_type(image_path)
        
        print(f"  ✅ 圖片讀取成功")
        print(f"     檔案名稱: {os.path.basename(image_path)}")
        print(f"     檔案大小: {image_size_kb:.1f} KB")
        print(f"     MIME 類型: {mime_type}")
        print(f"     Base64 長度: {len(image_base64)} 字元")
        
    except Exception as e:
        print(f"  ❌ 圖片讀取失敗: {e}")
        return 1
    
    # 發送 OCR 請求
    print(f"\n📋 步驟 3: 發送 OCR 請求")
    
    headers = {
        'Authorization': f'Bearer {config.api_key}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'inputs': {},
        'query': '請仔細辨識這張圖片中的所有文字內容，包括標題、內容、數字等，並以結構化的方式輸出。',
        'response_mode': 'blocking',
        'user': 'ocr_test_user',
        'files': [
            {
                'type': 'image',
                'transfer_method': 'local_file',
                'upload_file_id': None,
                'url': f'data:{mime_type};base64,{image_base64}'
            }
        ]
    }
    
    print(f"   正在發送請求到 Dify OCR Function...")
    print(f"   (最長等待 {config.timeout} 秒)")
    
    start_time = time.time()
    
    try:
        response = requests.post(
            config.api_url,
            headers=headers,
            json=payload,
            timeout=config.timeout
        )
        
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200:
            print(f"  ✅ OCR 請求成功 (HTTP 200)")
            print(f"     響應時間: {elapsed_time:.2f} 秒")
            
            data = response.json()
            
            # 顯示 OCR 結果
            print(f"\n{'='*60}")
            print(f"📝 OCR 辨識結果")
            print(f"{'='*60}")
            
            if 'answer' in data:
                print(data['answer'])
            else:
                print("⚠️ 回應中沒有 'answer' 欄位")
                print(f"原始回應: {data}")
            
            print(f"{'='*60}")
            
            # 顯示詳細資訊
            print(f"\n📊 詳細資訊:")
            
            if 'conversation_id' in data:
                print(f"   對話 ID: {data['conversation_id']}")
            
            if 'message_id' in data:
                print(f"   訊息 ID: {data['message_id']}")
            
            if 'metadata' in data:
                metadata = data['metadata']
                if 'usage' in metadata:
                    usage = metadata['usage']
                    print(f"   Token 使用:")
                    print(f"     - 輸入 Token: {usage.get('prompt_tokens', 'N/A')}")
                    print(f"     - 輸出 Token: {usage.get('completion_tokens', 'N/A')}")
                    print(f"     - 總計 Token: {usage.get('total_tokens', 'N/A')}")
            
            print(f"\n✅ 圖片 OCR 測試完成！")
            return 0
            
        else:
            print(f"  ❌ OCR 請求失敗 (HTTP {response.status_code})")
            print(f"     錯誤訊息: {response.text[:500]}")
            return 1
            
    except requests.Timeout:
        print(f"  ❌ 請求超時 (>{config.timeout}秒)")
        print(f"     提示: OCR 處理可能需要較長時間，可以嘗試使用較小的圖片")
        return 1
    except requests.ConnectionError as e:
        print(f"  ❌ 連接錯誤: {e}")
        return 1
    except Exception as e:
        print(f"  ❌ 請求失敗: {e}")
        return 1


def main():
    """主函數"""
    # 獲取圖片路徑
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        print(f"使用指定圖片: {image_path}")
    else:
        image_path = find_test_image()
        if image_path:
            print(f"使用預設測試圖片: {image_path}")
        else:
            print("❌ 錯誤: 找不到預設測試圖片")
            print("\n使用方式:")
            print("  docker exec ai-django python tests/test_dify_integration/test_ocr_function_image.py /path/to/image.jpg")
            print("\n預設圖片路徑:")
            print("  /home/user/codes/ai-platform-web/螢幕擷取畫面 2025-11-30 141051.jpg")
            return 1
    
    return test_image_ocr(image_path)


if __name__ == '__main__':
    sys.exit(main())
