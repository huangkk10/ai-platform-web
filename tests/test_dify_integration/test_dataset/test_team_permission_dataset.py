#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試團隊權限的知識庫建立
"""

import requests
import json
import time

# Dify API 配置
DIFY_CONFIG = {
    'base_url': 'http://10.253.43.244',
    'dataset_api_key': 'dataset-JLa32OwILQHkgPqYStTCW4sC'
}

def test_team_permission_dataset():
    """測試團隊權限的知識庫"""
    print("👥 測試團隊權限知識庫建立")
    print("=" * 50)
    
    headers = {
        'Authorization': f'Bearer {DIFY_CONFIG["dataset_api_key"]}',
        'Content-Type': 'application/json'
    }
    
    # 測試不同權限設定
    test_configs = [
        {
            'name': f'團隊共享知識庫_{int(time.time())}',
            'description': '所有團隊成員都能看到的知識庫',
            'permission': 'all_team_members'
        },
        {
            'name': f'公開知識庫_{int(time.time())}',
            'description': '公開的知識庫',
            'permission': 'public'  # 嘗試公開權限
        },
        {
            'name': f'chunwei專用知識庫_{int(time.time())}',
            'description': 'chunwei 用戶專用知識庫',
            'permission': 'only_me'
        }
    ]
    
    successful_datasets = []
    
    for config in test_configs:
        print(f"\n🔸 測試: {config['name']}")
        print(f"📋 權限: {config['permission']}")
        
        try:
            response = requests.post(
                f'{DIFY_CONFIG["base_url"]}/v1/datasets',
                headers=headers,
                json=config,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                dataset_id = data.get('id')
                
                print(f"✅ 建立成功！")
                print(f"🆔 ID: {dataset_id}")
                print(f"👤 建立者: {data.get('created_by')}")
                print(f"🏢 權限: {data.get('permission')}")
                
                successful_datasets.append({
                    'id': dataset_id,
                    'name': config['name'],
                    'permission': config['permission']
                })
                
                # 測試直接 URL 訪問
                ui_url = f"{DIFY_CONFIG['base_url']}/datasets/{dataset_id}"
                print(f"🌐 直接訪問 URL: {ui_url}")
                
            else:
                print(f"❌ 失敗: {response.text}")
                
        except Exception as e:
            print(f"❌ 異常: {e}")
    
    return successful_datasets

def upload_sample_data_to_dataset(dataset_id, dataset_name):
    """向指定知識庫上傳示例資料"""
    print(f"\n📤 向 {dataset_name} 上傳員工資料...")
    
    headers = {
        'Authorization': f'Bearer {DIFY_CONFIG["dataset_api_key"]}',
        'Content-Type': 'application/json'
    }
    
    # 簡化的員工資料
    employee_data = """
# 公司員工資訊

## 技術部門
- 張小明：後端工程師，薪資 75000，擅長 Python 和 Django
- 李美華：前端工程師，薪資 70000，擅長 React 和 Vue.js

## 業務部門  
- 王大成：業務經理，薪資 65000，負責客戶關係管理
- 陳小芳：業務專員，薪資 50000，負責市場開發

## 常見問題
Q: 公司有多少員工？
A: 目前公司共有 8 名員工。

Q: 技術部門有哪些人？
A: 技術部門有張小明（後端）、李美華（前端）、劉志強（全端）、周小雅（UI/UX）。
"""
    
    upload_config = {
        'name': f'員工資料_{int(time.time())}',
        'text': employee_data,
        'indexing_technique': 'economy',
        'process_rule': {
            'mode': 'automatic'
        }
    }
    
    try:
        response = requests.post(
            f'{DIFY_CONFIG["base_url"]}/v1/datasets/{dataset_id}/document/create_by_text',
            headers=headers,
            json=upload_config,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 上傳成功！")
            print(f"📄 文檔 ID: {data.get('document', {}).get('id')}")
            print(f"📊 處理狀態: {data.get('document', {}).get('indexing_status')}")
            return True
        else:
            print(f"❌ 上傳失敗: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 上傳異常: {e}")
        return False

def main():
    print("👥 團隊權限知識庫測試")
    print("=" * 60)
    
    # 1. 建立不同權限的知識庫
    datasets = test_team_permission_dataset()
    
    # 2. 向成功建立的知識庫上傳資料
    if datasets:
        print(f"\n📤 開始上傳測試資料...")
        
        # 選擇團隊權限的知識庫上傳資料
        team_dataset = next((d for d in datasets if d['permission'] == 'all_team_members'), None)
        
        if team_dataset:
            upload_success = upload_sample_data_to_dataset(
                team_dataset['id'], 
                team_dataset['name']
            )
            
            if upload_success:
                print(f"\n🎯 測試建議:")
                print(f"1. 🌐 直接訪問: http://10.253.43.244/datasets/{team_dataset['id']}")
                print(f"2. 🔍 在 UI 搜尋: {team_dataset['name']}")
                print(f"3. 👥 確認權限設定為 'all_team_members'，應該在 UI 可見")
    
    print(f"\n📊 總結:")
    print("如果團隊權限的知識庫仍然在 UI 看不到，")
    print("問題可能是 API Token 和 UI 登入帳號在不同的工作區")

if __name__ == "__main__":
    main()