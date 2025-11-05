#!/usr/bin/env python3
"""
測試 Dify API 是否提供獲取應用參數的端點
"""

import requests
import json

# Protocol Guide 配置
DIFY_BASE_URL = "http://10.10.172.37"
PROTOCOL_GUIDE_API_KEY = "app-MgZZOhADkEmdUrj2DtQLJ23G"

def test_dify_endpoints():
    """測試多個可能的 Dify API 端點"""
    
    headers = {
        'Authorization': f'Bearer {PROTOCOL_GUIDE_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    # 可能的端點列表
    test_endpoints = [
        # 應用參數相關
        '/v1/parameters',
        '/v1/app/parameters',
        '/v1/apps/parameters',
        '/v1/meta',
        '/v1/info',
        '/v1/config',
        
        # 應用資訊相關
        '/api/app',
        '/api/app/info',
        '/api/app/meta',
        
        # Console API（可能需要不同的認證）
        '/console/api/app',
        '/console/api/apps',
        
        # 其他可能的端點
        '/v1/apps',
        '/v1/application',
    ]
    
    print("=" * 80)
    print("🔍 測試 Dify API 端點")
    print(f"📍 Base URL: {DIFY_BASE_URL}")
    print(f"🔑 API Key: {PROTOCOL_GUIDE_API_KEY[:15]}...")
    print("=" * 80)
    print()
    
    results = []
    
    for endpoint in test_endpoints:
        url = f"{DIFY_BASE_URL}{endpoint}"
        
        try:
            # 嘗試 GET 請求
            response = requests.get(url, headers=headers, timeout=5)
            
            status = response.status_code
            
            if status == 200:
                print(f"✅ {endpoint}")
                print(f"   Status: {status}")
                try:
                    data = response.json()
                    print(f"   Response: {json.dumps(data, indent=2, ensure_ascii=False)[:200]}...")
                    results.append({
                        'endpoint': endpoint,
                        'status': status,
                        'data': data
                    })
                except:
                    print(f"   Response: {response.text[:200]}")
                print()
            elif status == 404:
                print(f"❌ {endpoint} - 404 Not Found")
            elif status == 401:
                print(f"🔒 {endpoint} - 401 Unauthorized (需要不同的認證)")
            elif status == 403:
                print(f"🚫 {endpoint} - 403 Forbidden")
            else:
                print(f"⚠️  {endpoint} - Status: {status}")
                print(f"   Response: {response.text[:100]}")
                print()
                
        except requests.exceptions.Timeout:
            print(f"⏱️  {endpoint} - Timeout")
        except requests.exceptions.ConnectionError:
            print(f"🔌 {endpoint} - Connection Error")
        except Exception as e:
            print(f"❌ {endpoint} - Error: {str(e)}")
    
    print()
    print("=" * 80)
    print("📊 測試結果總結")
    print("=" * 80)
    
    if results:
        print(f"\n✅ 找到 {len(results)} 個可用端點：\n")
        for result in results:
            print(f"  • {result['endpoint']}")
            if 'retrieval' in str(result['data']).lower() or 'threshold' in str(result['data']).lower():
                print(f"    ⭐ 可能包含 retrieval 設定！")
    else:
        print("\n❌ 未找到可用的參數端點")
        print("\n💡 建議：")
        print("  1. Dify 可能不提供公開的參數獲取 API")
        print("  2. 可能需要使用 Console API（需要管理員權限）")
        print("  3. 考慮從聊天回應的 metadata 中推斷設定")
    
    print()

if __name__ == '__main__':
    test_dify_endpoints()
