#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
列出所有的知識庫，找到手動建立的「公司員工資訊管理」知識庫
"""

import requests
import json

# Dify API 配置
DIFY_CONFIG = {
    'base_url': 'http://10.10.172.5',
    'dataset_api_key': 'dataset-JLa32OwILQHkgPqYStTCW4sC'
}

def list_all_datasets():
    """列出所有知識庫"""
    print("📚 獲取所有知識庫列表...")
    
    headers = {
        'Authorization': f'Bearer {DIFY_CONFIG["dataset_api_key"]}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(
            f'{DIFY_CONFIG["base_url"]}/v1/datasets',
            headers=headers,
            params={'page': 1, 'limit': 20},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            datasets = data.get('data', [])
            
            print(f"✅ 找到 {len(datasets)} 個知識庫:")
            print("=" * 80)
            
            for i, dataset in enumerate(datasets, 1):
                print(f"{i}. 📋 知識庫名稱: {dataset.get('name', 'N/A')}")
                print(f"   🆔 ID: {dataset.get('id', 'N/A')}")
                print(f"   📝 描述: {dataset.get('description', 'N/A')}")
                print(f"   📊 文檔數量: {dataset.get('document_count', 0)}")
                print(f"   📅 建立時間: {dataset.get('created_at', 'N/A')}")
                print(f"   🏷️ 索引技術: {dataset.get('indexing_technique', 'N/A')}")
                print(f"   🔧 權限: {dataset.get('permission', 'N/A')}")
                print("-" * 80)
                
                # 如果是公司員工資訊管理知識庫，標記出來
                if '公司員工' in dataset.get('name', '') or '員工資訊' in dataset.get('name', ''):
                    print(f"   🎯 這可能是您手動建立的員工知識庫！")
                    print("-" * 80)
            
            return datasets
        else:
            print(f"❌ 獲取知識庫列表失敗: HTTP {response.status_code}")
            print(f"回應: {response.text}")
            return []
            
    except Exception as e:
        print(f"❌ 獲取知識庫異常: {e}")
        return []

def main():
    print("🔍 查找「公司員工資訊管理」知識庫")
    print("=" * 50)
    
    datasets = list_all_datasets()
    
    # 尋找可能的員工知識庫
    employee_datasets = []
    for dataset in datasets:
        name = dataset.get('name', '').lower()
        if any(keyword in name for keyword in ['員工', '公司', 'employee', 'company']):
            employee_datasets.append(dataset)
    
    if employee_datasets:
        print(f"\n🎯 找到 {len(employee_datasets)} 個可能的員工知識庫:")
        for dataset in employee_datasets:
            print(f"  📋 {dataset.get('name', 'N/A')} (ID: {dataset.get('id', 'N/A')})")
    else:
        print(f"\n⚠️ 沒有找到名稱包含「員工」或「公司」的知識庫")
        print("請確認您是否已經手動建立「公司員工資訊管理」知識庫")

if __name__ == "__main__":
    main()