#!/usr/bin/env python3
"""
測試批量測試 API 端點
使用 Session 認證
"""

import requests
import json

# API 基礎 URL
BASE_URL = "http://localhost"
LOGIN_URL = f"{BASE_URL}/api/auth/login/"
BATCH_TEST_URL = f"{BASE_URL}/api/benchmark/versions/batch_test/"

# 測試資料
TEST_DATA = {
    "version_ids": [3, 4, 5],  # Baseline Version, Baseline Test, V1
    "test_case_ids": [1, 2],   # 兩個 ULINK 測試案例
    "batch_name": "API 測試批次",
    "notes": "測試 REST API 端點功能",
    "force_retest": False
}

def test_batch_api():
    """測試批量測試 API"""
    
    # 創建 session
    session = requests.Session()
    
    print("=" * 80)
    print("📋 批量測試 API 端點測試")
    print("=" * 80)
    
    # 步驟 1: 登入
    print("\n🔐 步驟 1: 用戶登入")
    login_data = {
        "username": "Eric_huang",  # 使用實際的 staff 用戶名
        "password": "1234"         # 替換為實際密碼
    }
    
    try:
        login_response = session.post(LOGIN_URL, json=login_data)
        if login_response.status_code == 200:
            print("✅ 登入成功")
            print(f"   用戶: {login_response.json().get('user', {}).get('username')}")
        else:
            print(f"❌ 登入失敗: {login_response.status_code}")
            print(f"   回應: {login_response.text}")
            return
    except Exception as e:
        print(f"❌ 登入異常: {str(e)}")
        return
    
    # 步驟 2: 發送批量測試請求
    print("\n🚀 步驟 2: 發送批量測試請求")
    print(f"   版本 ID: {TEST_DATA['version_ids']}")
    print(f"   測試案例 ID: {TEST_DATA['test_case_ids']}")
    print(f"   批次名稱: {TEST_DATA['batch_name']}")
    
    try:
        # 獲取 CSRF token（如果需要）
        csrf_token = session.cookies.get('csrftoken', '')
        headers = {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrf_token,
            'Referer': BASE_URL
        }
        
        # 發送 POST 請求
        print("\n⏳ 執行中（這可能需要幾秒鐘）...")
        batch_response = session.post(
            BATCH_TEST_URL,
            json=TEST_DATA,
            headers=headers,
            timeout=60  # 60 秒超時
        )
        
        # 步驟 3: 檢查回應
        print(f"\n📊 步驟 3: 檢查回應")
        print(f"   狀態碼: {batch_response.status_code}")
        
        if batch_response.status_code == 200:
            print("✅ API 請求成功")
            
            # 解析回應
            response_data = batch_response.json()
            
            # 顯示關鍵資訊
            print("\n" + "=" * 80)
            print("📈 批量測試結果")
            print("=" * 80)
            
            if response_data.get('success'):
                print(f"✅ 測試執行成功")
                print(f"\n📌 批次資訊:")
                print(f"   - 批次 ID: {response_data.get('batch_id')}")
                print(f"   - 批次名稱: {response_data.get('batch_name')}")
                
                # 測試執行 ID
                test_run_ids = response_data.get('test_run_ids', [])
                print(f"\n🔢 測試執行 ID: {test_run_ids}")
                
                # 摘要資訊
                summary = response_data.get('summary', {})
                if summary:
                    print(f"\n📊 執行摘要:")
                    print(f"   - 測試版本數: {summary.get('total_versions_tested')}")
                    print(f"   - 測試案例數: {summary.get('total_test_cases')}")
                    print(f"   - 總測試執行數: {summary.get('total_tests_executed')}")
                    print(f"   - 執行時間: {summary.get('execution_time'):.2f} 秒")
                
                # 比較結果
                comparison = response_data.get('comparison', {})
                if comparison:
                    best_version = comparison.get('best_version')
                    if best_version:
                        print(f"\n🏆 最佳版本:")
                        print(f"   - 版本: {best_version.get('version_name')}")
                        print(f"   - 總分: {best_version.get('overall_score'):.2f}")
                        print(f"   - 精準度: {best_version.get('precision'):.2f}")
                        print(f"   - 召回率: {best_version.get('recall'):.2f}")
                        print(f"   - F1 分數: {best_version.get('f1_score'):.2f}")
                    
                    # 所有版本排名
                    ranking = comparison.get('ranking', {}).get('by_overall_score', [])
                    if ranking:
                        print(f"\n📊 版本排名 (按總分):")
                        for idx, v in enumerate(ranking, 1):
                            print(f"   {idx}. {v['version_name']}: {v['overall_score']:.2f}")
                
                print("\n" + "=" * 80)
                print("✅ API 端點測試完成！")
                print("=" * 80)
                
            else:
                print(f"❌ 測試執行失敗")
                print(f"   錯誤: {response_data.get('error')}")
        
        elif batch_response.status_code == 403:
            print("❌ 權限不足（需要 staff 權限）")
        elif batch_response.status_code == 400:
            print("❌ 請求參數錯誤")
            print(f"   回應: {batch_response.text}")
        else:
            print(f"❌ 請求失敗: {batch_response.status_code}")
            print(f"   回應: {batch_response.text[:500]}")
            
    except requests.Timeout:
        print("❌ 請求超時（超過 60 秒）")
    except Exception as e:
        print(f"❌ 請求異常: {str(e)}")

if __name__ == "__main__":
    test_batch_api()
