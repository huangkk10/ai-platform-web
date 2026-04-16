#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
詳細檢查資料集內容和段落
"""

import requests
import json

# Dify API 配置
DIFY_CONFIG = {
    'base_url': 'http://10.253.43.244',
    'dataset_api_key': 'dataset-JLa32OwILQHkgPqYStTCW4sC'
}

TARGET_DATASET_ID = 'cb1eeadb-880a-4c54-aafc-0777487b5238'

def check_dataset_segments():
    """檢查資料集的所有段落內容"""
    print("🔍 檢查資料集段落內容...")
    
    headers = {
        'Authorization': f'Bearer {DIFY_CONFIG["dataset_api_key"]}',
        'Content-Type': 'application/json'
    }
    
    try:
        # 獲取文檔列表
        docs_response = requests.get(
            f'{DIFY_CONFIG["base_url"]}/v1/datasets/{TARGET_DATASET_ID}/documents',
            headers=headers,
            timeout=30
        )
        
        if docs_response.status_code == 200:
            docs_data = docs_response.json()
            documents = docs_data.get('data', [])
            
            print(f"📊 找到 {len(documents)} 個文檔")
            
            for doc in documents:
                doc_id = doc.get('id')
                doc_name = doc.get('name', 'N/A')
                
                print(f"\n📄 文檔: {doc_name}")
                print(f"   🆔 ID: {doc_id}")
                print(f"   📊 狀態: {doc.get('indexing_status', 'N/A')}")
                print(f"   📏 字數: {doc.get('word_count', 0)}")
                
                # 獲取文檔段落
                if doc_id:
                    segments_response = requests.get(
                        f'{DIFY_CONFIG["base_url"]}/v1/datasets/{TARGET_DATASET_ID}/documents/{doc_id}/segments',
                        headers=headers,
                        timeout=30
                    )
                    
                    if segments_response.status_code == 200:
                        segments_data = segments_response.json()
                        segments = segments_data.get('data', [])
                        
                        print(f"   🧩 段落數量: {len(segments)}")
                        
                        for i, segment in enumerate(segments, 1):
                            print(f"\n   📝 段落 {i}:")
                            print(f"      🆔 ID: {segment.get('id', 'N/A')}")
                            print(f"      📏 字數: {segment.get('word_count', 0)}")
                            print(f"      🏷️ 位置: {segment.get('position', 0)}")
                            print(f"      📊 狀態: {segment.get('status', 'N/A')}")
                            print(f"      🔧 是否啟用: {segment.get('enabled', False)}")
                            
                            content = segment.get('content', '')
                            if content:
                                print(f"      📖 內容: {content[:200]}...")
                            else:
                                print(f"      ⚠️ 沒有內容")
                    else:
                        print(f"   ❌ 無法獲取段落: HTTP {segments_response.status_code}")
        else:
            print(f"❌ 獲取文檔失敗: HTTP {docs_response.status_code}")
            
    except Exception as e:
        print(f"❌ 檢查段落異常: {e}")

def check_retrieval_test():
    """測試檢索功能（使用 economy 模式）"""
    print(f"\n🔍 測試資料集檢索功能...")
    
    headers = {
        'Authorization': f'Bearer {DIFY_CONFIG["dataset_api_key"]}',
        'Content-Type': 'application/json'
    }
    
    # 嘗試不同的檢索配置
    test_configs = [
        {
            'name': 'economy 模式',
            'config': {
                'query': '張小明',
                'retrieval_model': {
                    'search_method': 'semantic_search',
                    'reranking_enable': False,
                    'top_k': 3,
                    'score_threshold_enabled': False
                }
            }
        },
        {
            'name': 'keyword 模式',
            'config': {
                'query': '技術部',
                'retrieval_model': {
                    'search_method': 'keyword_search',
                    'reranking_enable': False,
                    'top_k': 3,
                    'score_threshold_enabled': False
                }
            }
        }
    ]
    
    for test_config in test_configs:
        print(f"\n🧪 測試 {test_config['name']}:")
        
        try:
            response = requests.post(
                f'{DIFY_CONFIG["base_url"]}/v1/datasets/{TARGET_DATASET_ID}/retrieve',
                headers=headers,
                json=test_config['config'],
                timeout=30
            )
            
            print(f"   📥 回應: HTTP {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                records = data.get('query', {}).get('records', [])
                
                print(f"   🎯 找到 {len(records)} 個結果")
                
                for i, record in enumerate(records[:2], 1):
                    segment = record.get('segment', {})
                    print(f"      {i}. 段落 {segment.get('id', 'N/A')}")
                    print(f"         🎯 分數: {record.get('score', 0):.4f}")
                    print(f"         📖 內容: {segment.get('content', '')[:100]}...")
            else:
                print(f"   ❌ 檢索失敗: HTTP {response.status_code}")
                print(f"   回應: {response.text}")
                
        except Exception as e:
            print(f"   ❌ 測試異常: {e}")

def main():
    print("🔬 資料集內容詳細分析")
    print("=" * 50)
    print(f"🎯 目標資料集: {TARGET_DATASET_ID}")
    print("=" * 50)
    
    # 1. 檢查段落內容
    check_dataset_segments()
    
    # 2. 測試檢索功能
    check_retrieval_test()
    
    print(f"\n📊 分析總結:")
    print("如果段落內容完整且檢索有結果，說明資料集本身沒問題")
    print("問題可能在於應用配置沒有正確關聯知識庫")

if __name__ == "__main__":
    main()