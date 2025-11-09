#!/usr/bin/env python3
"""
搜尋版本切換功能測試腳本
測試後端 API 是否正確支援 V1/V2 版本參數
"""

import requests
import json
import time
from datetime import datetime

# 測試配置
BASE_URL = "http://localhost"
API_ENDPOINT = f"{BASE_URL}/api/rvt-guides/search_sections/"

# 測試查詢
TEST_QUERY = "如何進行 RVT 測試"

def print_separator(title=""):
    """印出分隔線"""
    print("\n" + "=" * 80)
    if title:
        print(f"  {title}")
        print("=" * 80)

def test_v1_search():
    """測試 V1 基礎搜尋"""
    print_separator("測試 V1 基礎搜尋")
    
    payload = {
        "query": TEST_QUERY,
        "version": "v1",
        "limit": 3,
        "threshold": 0.7
    }
    
    print(f"\n📤 發送請求: POST {API_ENDPOINT}")
    print(f"📋 請求參數:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    
    start_time = time.time()
    
    try:
        response = requests.post(
            API_ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        elapsed = (time.time() - start_time) * 1000
        
        print(f"\n✅ 狀態碼: {response.status_code}")
        print(f"⏱️  回應時間: {elapsed:.0f}ms")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n📊 回應資料:")
            print(f"  - 版本: {data.get('version', 'N/A')}")
            print(f"  - 結果數量: {data.get('total', 0)}")
            print(f"  - 搜尋類型: {data.get('search_type', 'N/A')}")
            print(f"  - 執行時間: {data.get('execution_time', 'N/A')}")
            
            if data.get('results'):
                print(f"\n🔍 前 {min(3, len(data['results']))} 個結果:")
                for i, result in enumerate(data['results'][:3], 1):
                    print(f"\n  結果 {i}:")
                    print(f"    - 標題: {result.get('section_title', 'N/A')}")
                    print(f"    - 相似度: {result.get('similarity', 0):.2%}")
                    print(f"    - 內容: {result.get('content', '')[:100]}...")
            
            return True
        else:
            print(f"\n❌ 錯誤: {response.text}")
            return False
            
    except Exception as e:
        print(f"\n❌ 請求失敗: {str(e)}")
        return False

def test_v2_search():
    """測試 V2 上下文增強搜尋"""
    print_separator("測試 V2 上下文增強搜尋")
    
    payload = {
        "query": TEST_QUERY,
        "version": "v2",
        "limit": 3,
        "threshold": 0.7,
        "context_window": 1,
        "context_mode": "adjacent"
    }
    
    print(f"\n📤 發送請求: POST {API_ENDPOINT}")
    print(f"📋 請求參數:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    
    start_time = time.time()
    
    try:
        response = requests.post(
            API_ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        elapsed = (time.time() - start_time) * 1000
        
        print(f"\n✅ 狀態碼: {response.status_code}")
        print(f"⏱️  回應時間: {elapsed:.0f}ms")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n📊 回應資料:")
            print(f"  - 版本: {data.get('version', 'N/A')}")
            print(f"  - 結果數量: {data.get('total', 0)}")
            print(f"  - 搜尋類型: {data.get('search_type', 'N/A')}")
            print(f"  - 執行時間: {data.get('execution_time', 'N/A')}")
            
            if data.get('results'):
                print(f"\n🔍 前 {min(3, len(data['results']))} 個結果:")
                for i, result in enumerate(data['results'][:3], 1):
                    print(f"\n  結果 {i}:")
                    print(f"    - 標題: {result.get('section_title', 'N/A')}")
                    print(f"    - 相似度: {result.get('similarity', 0):.2%}")
                    print(f"    - 內容: {result.get('content', '')[:100]}...")
                    
                    # V2 特有：檢查上下文
                    if result.get('has_context'):
                        print(f"    - 包含上下文: ✅ 是")
                        context = result.get('context', {})
                        if context.get('previous'):
                            print(f"    - 前段落: 有")
                        if context.get('next'):
                            print(f"    - 後段落: 有")
                        if context.get('parent'):
                            print(f"    - 父段落: 有")
                    else:
                        print(f"    - 包含上下文: ❌ 否")
            
            return True
        else:
            print(f"\n❌ 錯誤: {response.text}")
            return False
            
    except Exception as e:
        print(f"\n❌ 請求失敗: {str(e)}")
        return False

def test_default_version():
    """測試預設版本（不指定 version 參數）"""
    print_separator("測試預設版本（不指定 version）")
    
    payload = {
        "query": TEST_QUERY,
        "limit": 3
    }
    
    print(f"\n📤 發送請求: POST {API_ENDPOINT}")
    print(f"📋 請求參數:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    
    try:
        response = requests.post(
            API_ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ 狀態碼: {response.status_code}")
            print(f"📊 預設版本: {data.get('version', 'N/A')}")
            
            if data.get('version') == 'v1':
                print("✅ 預設版本正確（應為 v1）")
                return True
            else:
                print(f"❌ 預設版本錯誤（預期 v1，實際 {data.get('version')}）")
                return False
        else:
            print(f"\n❌ 錯誤: {response.text}")
            return False
            
    except Exception as e:
        print(f"\n❌ 請求失敗: {str(e)}")
        return False

def compare_versions():
    """比較 V1 和 V2 的效能差異"""
    print_separator("比較 V1 vs V2 效能")
    
    results = {"v1": None, "v2": None}
    
    for version in ["v1", "v2"]:
        payload = {
            "query": TEST_QUERY,
            "version": version,
            "limit": 5,
            "threshold": 0.7
        }
        
        if version == "v2":
            payload["context_window"] = 1
            payload["context_mode"] = "adjacent"
        
        start_time = time.time()
        
        try:
            response = requests.post(
                API_ENDPOINT,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            elapsed = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                results[version] = {
                    "success": True,
                    "elapsed": elapsed,
                    "total": data.get('total', 0),
                    "execution_time": data.get('execution_time', 'N/A')
                }
            else:
                results[version] = {
                    "success": False,
                    "error": response.text
                }
                
        except Exception as e:
            results[version] = {
                "success": False,
                "error": str(e)
            }
    
    # 印出比較結果
    print("\n📊 效能比較:")
    print(f"\n{'項目':<20} {'V1':<25} {'V2':<25}")
    print("-" * 70)
    
    if results["v1"]["success"] and results["v2"]["success"]:
        print(f"{'總回應時間':<20} {results['v1']['elapsed']:<25.0f}ms {results['v2']['elapsed']:<25.0f}ms")
        print(f"{'API 執行時間':<20} {results['v1']['execution_time']:<25} {results['v2']['execution_time']:<25}")
        print(f"{'結果數量':<20} {results['v1']['total']:<25} {results['v2']['total']:<25}")
        
        # 計算差異
        time_diff = results['v2']['elapsed'] - results['v1']['elapsed']
        diff_percent = (time_diff / results['v1']['elapsed']) * 100
        
        print(f"\n⏱️  V2 比 V1 慢 {time_diff:.0f}ms ({diff_percent:.1f}%)")
        
        if diff_percent < 50:
            print("✅ 效能差異在可接受範圍內")
        else:
            print("⚠️  效能差異較大，建議優化")
    else:
        print("\n❌ 部分測試失敗，無法進行比較")

def main():
    """主測試函數"""
    print(f"""
╔════════════════════════════════════════════════════════════════╗
║     搜尋版本切換功能測試腳本                                    ║
║     Search Version Toggle Feature Test                         ║
╚════════════════════════════════════════════════════════════════╝

測試時間: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
測試目標: {API_ENDPOINT}
測試查詢: "{TEST_QUERY}"
""")
    
    results = []
    
    # 執行測試
    results.append(("預設版本測試", test_default_version()))
    results.append(("V1 基礎搜尋", test_v1_search()))
    results.append(("V2 上下文搜尋", test_v2_search()))
    
    # 效能比較
    compare_versions()
    
    # 總結
    print_separator("測試總結")
    
    print("\n📋 測試結果:")
    for test_name, success in results:
        status = "✅ 通過" if success else "❌ 失敗"
        print(f"  - {test_name:<20} {status}")
    
    total_tests = len(results)
    passed_tests = sum(1 for _, success in results if success)
    
    print(f"\n總計: {passed_tests}/{total_tests} 測試通過")
    
    if passed_tests == total_tests:
        print("\n🎉 所有測試通過！搜尋版本切換功能正常工作。")
        return 0
    else:
        print("\n⚠️  部分測試失敗，請檢查錯誤訊息。")
        return 1

if __name__ == "__main__":
    exit(main())
