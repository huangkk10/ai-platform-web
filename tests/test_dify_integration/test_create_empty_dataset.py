#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試建立空知識庫的 API
"""

import requests
import json
import time

# Dify API 配置
DIFY_CONFIG = {
    'base_url': 'http://10.10.172.37',
    'dataset_api_key': 'dataset-JLa32OwILQHkgPqYStTCW4sC'
}

def test_create_empty_dataset():
    """測試建立空知識庫"""
    print("🧪 測試建立空知識庫 API")
    print("=" * 50)
    
    headers = {
        'Authorization': f'Bearer {DIFY_CONFIG["dataset_api_key"]}',
        'Content-Type': 'application/json'
    }
    
    # 測試資料
    test_datasets = [
        {
            'name': '空知識庫測試_1',
            'description': '第一個測試用空知識庫'
        },
        {
            'name': '空知識庫測試_2', 
            'permission': 'only_me',
            'description': '第二個測試用空知識庫（包含權限）'
        },
        {
            'name': f'API測試知識庫_{int(time.time())}',
            'permission': 'only_me',
            'description': '通過 API 建立的時間戳測試知識庫'
        }
    ]
    
    results = []
    
    for i, dataset_config in enumerate(test_datasets, 1):
        print(f"\n🔸 測試 {i}: {dataset_config['name']}")
        print(f"📋 配置: {json.dumps(dataset_config, ensure_ascii=False, indent=2)}")
        
        try:
            response = requests.post(
                f'{DIFY_CONFIG["base_url"]}/v1/datasets',
                headers=headers,
                json=dataset_config,
                timeout=30
            )
            
            print(f"📥 HTTP 狀態: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                dataset_id = data.get('id')
                dataset_name = data.get('name')
                
                print(f"✅ 建立成功！")
                print(f"🆔 知識庫 ID: {dataset_id}")
                print(f"📚 知識庫名稱: {dataset_name}")
                print(f"📊 完整回應: {json.dumps(data, ensure_ascii=False, indent=2)}")
                
                results.append({
                    'success': True,
                    'id': dataset_id,
                    'name': dataset_name,
                    'config': dataset_config
                })
                
                # 立即檢查是否能查詢到
                print(f"\n🔍 驗證建立的知識庫...")
                verify_response = requests.get(
                    f'{DIFY_CONFIG["base_url"]}/v1/datasets/{dataset_id}',
                    headers=headers,
                    timeout=30
                )
                
                if verify_response.status_code == 200:
                    verify_data = verify_response.json()
                    print(f"✅ 驗證成功！知識庫確實存在")
                    print(f"📊 文檔數: {verify_data.get('document_count', 0)}")
                    print(f"📏 字數: {verify_data.get('word_count', 0)}")
                else:
                    print(f"⚠️ 驗證失敗: HTTP {verify_response.status_code}")
                
            elif response.status_code == 201:
                # 有些 API 返回 201 表示創建成功
                data = response.json()
                dataset_id = data.get('id')
                dataset_name = data.get('name')
                
                print(f"✅ 建立成功！(HTTP 201)")
                print(f"🆔 知識庫 ID: {dataset_id}")
                print(f"📚 知識庫名稱: {dataset_name}")
                
                results.append({
                    'success': True,
                    'id': dataset_id,
                    'name': dataset_name,
                    'config': dataset_config
                })
                
            else:
                print(f"❌ 建立失敗！")
                print(f"📥 錯誤回應: {response.text}")
                
                results.append({
                    'success': False,
                    'error': response.text,
                    'status_code': response.status_code,
                    'config': dataset_config
                })
                
        except Exception as e:
            print(f"❌ 測試異常: {e}")
            results.append({
                'success': False,
                'error': str(e),
                'config': dataset_config
            })
    
    return results

def test_exact_curl_command():
    """測試您提供的確切 curl 命令"""
    print(f"\n🎯 測試您提供的確切 curl 命令")
    print("=" * 50)
    
    headers = {
        'Authorization': f'Bearer {DIFY_CONFIG["dataset_api_key"]}',
        'Content-Type': 'application/json'
    }
    
    # 完全按照您的 curl 命令參數
    exact_data = {
        "name": "name",
        "permission": "all_team_members"
    }
    
    print(f"📋 請求資料: {json.dumps(exact_data, ensure_ascii=False, indent=2)}")
    
    try:
        response = requests.post(
            f'{DIFY_CONFIG["base_url"]}/v1/datasets',
            headers=headers,
            json=exact_data,
            timeout=30
        )
        
        print(f"📥 HTTP 狀態: {response.status_code}")
        print(f"📤 回應內容: {response.text}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            print(f"✅ 建立成功！")
            print(f"🆔 知識庫 ID: {data.get('id')}")
            print(f"📚 知識庫名稱: {data.get('name')}")
            return data.get('id')
        else:
            print(f"❌ 建立失敗")
            return None
            
    except Exception as e:
        print(f"❌ 測試異常: {e}")
        return None

def list_all_datasets():
    """列出所有知識庫（包含新建立的）"""
    print(f"\n📋 列出所有知識庫...")
    
    headers = {
        'Authorization': f'Bearer {DIFY_CONFIG["dataset_api_key"]}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(
            f'{DIFY_CONFIG["base_url"]}/v1/datasets',
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            datasets = data.get('data', [])
            
            print(f"📊 總共找到 {len(datasets)} 個知識庫:")
            
            for dataset in datasets:
                name = dataset.get('name', 'N/A')
                dataset_id = dataset.get('id', 'N/A')
                doc_count = dataset.get('document_count', 0)
                created_at = dataset.get('created_at', 'N/A')
                
                print(f"  📚 {name}")
                print(f"     🆔 ID: {dataset_id}")
                print(f"     📊 文檔數: {doc_count}")
                print(f"     📅 建立時間: {created_at}")
                print()
                
        else:
            print(f"❌ 獲取列表失敗: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ 列表異常: {e}")

def main():
    print("🧪 Dify 空知識庫建立測試")
    print("=" * 60)
    
    # 1. 測試不同的配置
    results = test_create_empty_dataset()
    
    # 2. 測試確切的 curl 命令
    curl_result = test_exact_curl_command()
    
    # 3. 列出所有知識庫
    list_all_datasets()
    
    # 4. 總結結果
    print(f"\n📊 測試總結:")
    print("=" * 50)
    
    successful = [r for r in results if r.get('success')]
    failed = [r for r in results if not r.get('success')]
    
    print(f"✅ 成功建立: {len(successful)} 個")
    print(f"❌ 建立失敗: {len(failed)} 個")
    
    if successful:
        print(f"\n🎉 成功建立的知識庫:")
        for result in successful:
            print(f"  📚 {result['name']} (ID: {result['id']})")
    
    if failed:
        print(f"\n💥 失敗的測試:")
        for result in failed:
            print(f"  ❌ {result['config']['name']}: {result.get('error', 'Unknown error')}")
    
    if curl_result:
        print(f"\n🎯 curl 命令測試: ✅ 成功 (ID: {curl_result})")
    else:
        print(f"\n🎯 curl 命令測試: ❌ 失敗")

if __name__ == "__main__":
    main()