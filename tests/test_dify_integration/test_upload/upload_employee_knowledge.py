#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
將完整的員工資料上傳到指定的知識庫
支援多種上傳方式：新建知識庫或添加到現有知識庫
"""

import requests
import json
import os
from datetime import datetime

# Dify API 配置
DIFY_CONFIG = {
    'base_url': 'http://10.253.43.244',
    'dataset_api_key': 'dataset-JLa32OwILQHkgPqYStTCW4sC'
}

def read_employee_data():
    """讀取員工資料檔案"""
    file_path = '/home/user/codes/ai-platform-web/tests/test_dify_integration/company_employees_data.md'
    
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        print(f"❌ 找不到員工資料檔案: {file_path}")
        return None

def create_new_dataset():
    """創建新的員工知識庫"""
    print("🆕 創建新的「公司員工資訊管理」知識庫...")
    
    headers = {
        'Authorization': f'Bearer {DIFY_CONFIG["dataset_api_key"]}',
        'Content-Type': 'application/json'
    }
    
    dataset_data = {
        'name': '公司員工資訊管理',
        'description': '包含完整員工資料的知識庫，支援員工查詢、部門統計、薪資分析等功能',
        'indexing_technique': 'economy',  # 使用 economy 模式避免嵌入模型問題
        'permission': 'only_me'
    }
    
    try:
        response = requests.post(
            f'{DIFY_CONFIG["base_url"]}/v1/datasets',
            headers=headers,
            json=dataset_data,
            timeout=30
        )
        
        if response.status_code == 200:
            dataset = response.json()
            dataset_id = dataset.get('id')
            print(f"✅ 知識庫創建成功!")
            print(f"   📋 名稱: {dataset.get('name')}")
            print(f"   🆔 ID: {dataset_id}")
            return dataset_id
        else:
            print(f"❌ 創建知識庫失敗: HTTP {response.status_code}")
            print(f"回應: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 創建知識庫異常: {e}")
        return None

def upload_employee_data(dataset_id, employee_data):
    """上傳員工資料到知識庫"""
    print(f"📤 上傳員工資料到知識庫 {dataset_id}...")
    
    headers = {
        'Authorization': f'Bearer {DIFY_CONFIG["dataset_api_key"]}',
        'Content-Type': 'application/json'
    }
    
    upload_data = {
        'name': '公司員工完整資料.md',
        'text': employee_data,
        'indexing_technique': 'economy',
        'process_rule': {
            'mode': 'automatic',
            'rules': {
                'pre_processing_rules': [
                    {'id': 'remove_extra_spaces', 'enabled': True},
                    {'id': 'remove_urls_emails', 'enabled': False}
                ],
                'segmentation': {
                    'separator': '\\n\\n',
                    'max_tokens': 500
                }
            }
        }
    }
    
    try:
        response = requests.post(
            f'{DIFY_CONFIG["base_url"]}/v1/datasets/{dataset_id}/document/create_by_text',
            headers=headers,
            json=upload_data,
            timeout=30
        )
        
        if response.status_code == 200:
            document = response.json()
            print(f"✅ 員工資料上傳成功!")
            print(f"   📄 文檔名稱: {document.get('name')}")
            print(f"   🆔 文檔 ID: {document.get('id')}")
            print(f"   📊 字數: {document.get('word_count', 0)}")
            return document.get('id')
        else:
            print(f"❌ 上傳失敗: HTTP {response.status_code}")
            print(f"回應: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 上傳異常: {e}")
        return None

def test_knowledge_retrieval(dataset_id):
    """測試知識庫檢索功能"""
    print(f"\n🔍 測試知識庫檢索功能...")
    
    headers = {
        'Authorization': f'Bearer {DIFY_CONFIG["dataset_api_key"]}',
        'Content-Type': 'application/json'
    }
    
    # 測試不同的查詢
    test_queries = [
        '張小明的薪資是多少？',
        '技術部有哪些員工？',
        '誰是薪資最高的員工？',
        '業務部門的平均薪資',
        '2023年入職的員工有誰？'
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🧪 測試查詢 {i}: {query}")
        
        search_data = {
            'query': query,
            'retrieval_model': {
                'search_method': 'keyword_search',  # 使用關鍵字搜尋避免嵌入模型問題
                'reranking_enable': False,
                'top_k': 3,
                'score_threshold_enabled': False
            }
        }
        
        try:
            response = requests.post(
                f'{DIFY_CONFIG["base_url"]}/v1/datasets/{dataset_id}/retrieve',
                headers=headers,
                json=search_data,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                records = data.get('query', {}).get('records', [])
                
                print(f"   📊 找到 {len(records)} 個相關結果")
                
                for j, record in enumerate(records[:2], 1):
                    segment = record.get('segment', {})
                    content = segment.get('content', '')
                    score = record.get('score', 0)
                    
                    print(f"   📝 結果 {j} (分數: {score:.4f}): {content[:100]}...")
            else:
                print(f"   ❌ 查詢失敗: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ 查詢異常: {e}")

def main():
    print("🚀 公司員工資訊知識庫管理工具")
    print("=" * 60)
    
    # 1. 讀取員工資料
    print("📖 讀取員工資料...")
    employee_data = read_employee_data()
    
    if not employee_data:
        print("❌ 無法讀取員工資料，程序終止")
        return
    
    print(f"✅ 員工資料讀取成功，共 {len(employee_data)} 個字元")
    
    # 2. 詢問使用者選擇
    print(f"\n📋 請選擇操作方式:")
    print("1. 創建新的「公司員工資訊管理」知識庫")
    print("2. 添加到現有知識庫")
    
    choice = input("\n請輸入選擇 (1 或 2): ").strip()
    
    dataset_id = None
    
    if choice == '1':
        # 創建新知識庫
        dataset_id = create_new_dataset()
    elif choice == '2':
        # 使用現有知識庫
        dataset_id = input("請輸入知識庫 ID: ").strip()
        if not dataset_id:
            print("❌ 無效的知識庫 ID")
            return
    else:
        print("❌ 無效的選擇")
        return
    
    if not dataset_id:
        print("❌ 無法獲得有效的知識庫 ID，程序終止")
        return
    
    # 3. 上傳員工資料
    print(f"\n📤 準備上傳資料到知識庫: {dataset_id}")
    document_id = upload_employee_data(dataset_id, employee_data)
    
    if not document_id:
        print("❌ 資料上傳失敗，程序終止")
        return
    
    # 4. 測試檢索功能
    test_knowledge_retrieval(dataset_id)
    
    # 5. 輸出總結
    print(f"\n🎉 員工知識庫設置完成!")
    print("=" * 60)
    print(f"📋 知識庫 ID: {dataset_id}")
    print(f"📄 文檔 ID: {document_id}")
    print(f"🔗 您可以在 Dify UI 中查看: http://10.253.43.244/datasets/{dataset_id}")
    print(f"🤖 接下來可以在 Chat 應用中關聯此知識庫進行對話測試")

if __name__ == "__main__":
    main()