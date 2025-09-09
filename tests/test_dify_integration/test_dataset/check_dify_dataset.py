#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dify 知識庫檢查腳本
檢查指定資料集是否存在以及其內容
"""

import requests
import json
import time

# Dify API 配置
DIFY_CONFIG = {
    'dataset_api_key': 'dataset-JLa32OwILQHkgPqYStTCW4sC',
    'base_url': 'http://10.10.172.5'
}

# 從上次測試得到的資料集 ID
TARGET_DATASET_ID = 'cb1eeadb-880a-4c54-aafc-0777487b5238'

class DifyDatasetChecker:
    """Dify 資料集檢查器"""
    
    def __init__(self):
        self.headers = {
            'Authorization': f'Bearer {DIFY_CONFIG["dataset_api_key"]}',
            'Content-Type': 'application/json'
        }
    
    def list_all_datasets(self):
        """列出所有資料集"""
        print("📚 列出所有資料集...")
        
        try:
            response = requests.get(
                f'{DIFY_CONFIG["base_url"]}/v1/datasets',
                headers=self.headers,
                timeout=30
            )
            
            print(f"📥 回應: HTTP {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                datasets = result.get('data', [])
                
                print(f"📄 找到 {len(datasets)} 個資料集:")
                
                for dataset in datasets:
                    dataset_id = dataset.get('id', 'N/A')
                    dataset_name = dataset.get('name', 'N/A')
                    created_at = dataset.get('created_at', 'N/A')
                    document_count = dataset.get('document_count', 0)
                    
                    print(f"  📚 {dataset_name}")
                    print(f"     ID: {dataset_id}")
                    print(f"     文件數: {document_count}")
                    print(f"     建立時間: {created_at}")
                    
                    if dataset_id == TARGET_DATASET_ID:
                        print(f"     🎯 >>> 這是我們的目標資料集！")
                    print("")
                
                return datasets
            else:
                print(f"❌ 列出資料集失敗: {response.text}")
                return []
                
        except Exception as e:
            print(f"❌ 列出資料集異常: {e}")
            return []
    
    def check_specific_dataset(self, dataset_id: str):
        """檢查特定資料集"""
        print(f"🔍 檢查資料集: {dataset_id}")
        
        try:
            response = requests.get(
                f'{DIFY_CONFIG["base_url"]}/v1/datasets/{dataset_id}',
                headers=self.headers,
                timeout=30
            )
            
            print(f"📥 回應: HTTP {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                print(f"✅ 資料集存在")
                print(f"📋 名稱: {result.get('name', 'N/A')}")
                print(f"📋 描述: {result.get('description', 'N/A')}")
                print(f"📋 文件數: {result.get('document_count', 0)}")
                print(f"📋 建立時間: {result.get('created_at', 'N/A')}")
                print(f"📋 更新時間: {result.get('updated_at', 'N/A')}")
                
                return True
            elif response.status_code == 404:
                print(f"❌ 資料集不存在")
                return False
            else:
                print(f"❌ 檢查失敗: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 檢查異常: {e}")
            return False
    
    def list_dataset_documents(self, dataset_id: str):
        """列出資料集中的文件"""
        print(f"📄 列出資料集 {dataset_id} 中的文件...")
        
        try:
            response = requests.get(
                f'{DIFY_CONFIG["base_url"]}/v1/datasets/{dataset_id}/documents',
                headers=self.headers,
                timeout=30
            )
            
            print(f"📥 回應: HTTP {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                documents = result.get('data', [])
                
                print(f"📄 找到 {len(documents)} 個文件:")
                
                for doc in documents:
                    doc_id = doc.get('id', 'N/A')
                    doc_name = doc.get('name', 'N/A')
                    status = doc.get('indexing_status', 'N/A')
                    word_count = doc.get('word_count', 0)
                    created_at = doc.get('created_at', 'N/A')
                    updated_at = doc.get('updated_at', 'N/A')
                    
                    print(f"  📄 {doc_name}")
                    print(f"     ID: {doc_id}")
                    print(f"     狀態: {status}")
                    print(f"     字數: {word_count}")
                    print(f"     建立時間: {created_at}")
                    print(f"     更新時間: {updated_at}")
                    print("")
                
                return documents
            else:
                print(f"❌ 列出文件失敗: {response.text}")
                return []
                
        except Exception as e:
            print(f"❌ 列出文件異常: {e}")
            return []
    
    def get_document_content(self, dataset_id: str, document_id: str):
        """獲取文件內容"""
        print(f"📖 獲取文件內容: {document_id}")
        
        try:
            response = requests.get(
                f'{DIFY_CONFIG["base_url"]}/v1/datasets/{dataset_id}/documents/{document_id}',
                headers=self.headers,
                timeout=30
            )
            
            print(f"📥 回應: HTTP {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                print(f"📄 文件詳情:")
                print(f"   名稱: {result.get('name', 'N/A')}")
                print(f"   狀態: {result.get('indexing_status', 'N/A')}")
                print(f"   字數: {result.get('word_count', 0)}")
                
                # 檢查是否有文件段落
                segments = result.get('segments', [])
                if segments:
                    print(f"   段落數: {len(segments)}")
                    print(f"   預覽前100字:")
                    for i, segment in enumerate(segments[:2]):
                        content = segment.get('content', '')
                        print(f"     段落{i+1}: {content[:100]}...")
                else:
                    print(f"   ⚠️ 沒有找到文件段落")
                
                return result
            else:
                print(f"❌ 獲取文件失敗: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ 獲取文件異常: {e}")
            return None

def main():
    """主檢查函數"""
    print("🔍 Dify 知識庫檢查工具")
    print("=" * 60)
    print(f"🎯 目標資料集 ID: {TARGET_DATASET_ID}")
    print(f"🔗 API 端點: {DIFY_CONFIG['base_url']}")
    print("=" * 60)
    
    checker = DifyDatasetChecker()
    
    # 1. 列出所有資料集
    print("\n🚀 步驟 1: 列出所有資料集")
    datasets = checker.list_all_datasets()
    
    # 2. 檢查目標資料集
    print(f"\n🚀 步驟 2: 檢查目標資料集")
    dataset_exists = checker.check_specific_dataset(TARGET_DATASET_ID)
    
    if dataset_exists:
        # 3. 列出資料集中的文件
        print(f"\n🚀 步驟 3: 列出資料集中的文件")
        documents = checker.list_dataset_documents(TARGET_DATASET_ID)
        
        # 4. 檢查文件內容
        if documents:
            print(f"\n🚀 步驟 4: 檢查第一個文件的內容")
            first_doc = documents[0]
            checker.get_document_content(TARGET_DATASET_ID, first_doc['id'])
    
    # 5. 總結
    print("\n" + "=" * 60)
    print("📊 檢查結果總結")
    print("=" * 60)
    
    if dataset_exists:
        print("✅ 目標資料集存在")
        print(f"🔗 直接連結: {DIFY_CONFIG['base_url']}/datasets/{TARGET_DATASET_ID}")
        print("\n💡 建議:")
        print("1. 確認您登入的是正確的 Dify 工作區")
        print("2. 嘗試重新整理瀏覽器頁面")
        print(f"3. 直接訪問: {DIFY_CONFIG['base_url']}/datasets")
        print("4. 搜尋資料集名稱: 測試上傳修正版_1757399730")
    else:
        print("❌ 目標資料集不存在")
        print("🔍 可能的原因:")
        print("- 資料集已被刪除")
        print("- API Token 權限不足")
        print("- 工作區不匹配")
        print("- 網路連線問題")
    
    print("\n✅ 檢查完成")

if __name__ == "__main__":
    main()