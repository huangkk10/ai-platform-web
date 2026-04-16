#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dify 知識庫上傳測試腳本 - 修正版
專門測試檔案上傳到 Dify 知識庫功能，解決嵌入模型問題
"""

import requests
import json
import sqlite3
import time
import os

# Dify API 配置
DIFY_CONFIG = {
    'dataset_api_key': 'dataset-JLa32OwILQHkgPqYStTCW4sC',  # 知識庫 API Token
    'base_url': 'http://10.253.43.244'
}

class DifyUploadTesterV2:
    """Dify 知識庫上傳測試器 V2 - 修正嵌入模型問題"""
    
    def __init__(self):
        self.dataset_id = None
    
    def create_dataset(self) -> bool:
        """建立測試用資料集"""
        print("📚 建立 Dify 測試資料集...")
        
        headers = {
            'Authorization': f'Bearer {DIFY_CONFIG["dataset_api_key"]}',
            'Content-Type': 'application/json'
        }
        
        dataset_data = {
            'name': f'測試上傳修正版_{int(time.time())}',
            'description': '測試檔案上傳功能的修正版資料集，解決嵌入模型問題'
        }
        
        try:
            response = requests.post(
                f'{DIFY_CONFIG["base_url"]}/v1/datasets',
                headers=headers,
                json=dataset_data,
                timeout=30
            )
            
            print(f"📥 建立資料集回應: HTTP {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.dataset_id = result.get('id')
                print(f"✅ 資料集建立成功")
                print(f"📋 資料集 ID: {self.dataset_id}")
                print(f"📋 資料集名稱: {result.get('name', 'N/A')}")
                return True
            else:
                print(f"❌ 建立資料集失敗: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 建立資料集異常: {e}")
            return False
    
    def generate_simple_content(self) -> str:
        """生成簡化的測試內容"""
        try:
            # 從資料庫載入員工資料
            conn = sqlite3.connect('tests/test_dify_integration/company.db')
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM employees LIMIT 3")  # 只取前3個員工
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            conn.close()
            
            # 生成簡化的知識庫內容
            content = "# 員工資料測試\n\n"
            
            for row in rows:
                employee_data = dict(zip(columns, row))
                content += f"員工姓名: {employee_data['name']}\n"
                content += f"部門: {employee_data['department']}\n"
                content += f"職位: {employee_data['position']}\n"
                content += f"薪資: {employee_data['salary']} 元\n\n"
            
            print(f"📄 生成簡化內容長度: {len(content)} 字元")
            return content
            
        except Exception as e:
            print(f"❌ 生成測試內容失敗: {e}")
            return "測試內容：張小明，技術部，軟體工程師，75000元"
    
    def try_upload_methods(self) -> bool:
        """嘗試多種上傳方法"""
        if not self.dataset_id:
            print("❌ 沒有資料集 ID，無法上傳")
            return False
        
        content = self.generate_simple_content()
        headers = {
            'Authorization': f'Bearer {DIFY_CONFIG["dataset_api_key"]}',
            'Content-Type': 'application/json'
        }
        
        # 方法1: 經濟模式
        print("\n🔄 方法1: 使用經濟模式上傳...")
        success = self.try_upload_with_params(headers, content, {
            'name': f'employees_economy_{int(time.time())}.txt',
            'text': content,
            'indexing_technique': 'economy',
            'process_rule': {'mode': 'automatic'}
        })
        
        if success:
            return True
        
        # 方法2: 不指定索引技術
        print("\n🔄 方法2: 不指定索引技術...")
        success = self.try_upload_with_params(headers, content, {
            'name': f'employees_auto_{int(time.time())}.txt',
            'text': content,
            'process_rule': {'mode': 'automatic'}
        })
        
        if success:
            return True
        
        # 方法3: 最簡化參數
        print("\n🔄 方法3: 最簡化參數...")
        success = self.try_upload_with_params(headers, content, {
            'name': f'employees_simple_{int(time.time())}.txt',
            'text': content[:200] + "..."  # 縮短內容
        })
        
        return success
    
    def try_upload_with_params(self, headers: dict, content: str, data: dict) -> bool:
        """嘗試使用特定參數上傳"""
        try:
            print(f"📤 上傳參數: {list(data.keys())}")
            
            response = requests.post(
                f'{DIFY_CONFIG["base_url"]}/v1/datasets/{self.dataset_id}/document/create_by_text',
                headers=headers,
                json=data,
                timeout=60
            )
            
            print(f"📥 回應: HTTP {response.status_code}")
            
            if response.status_code in [200, 201]:
                result = response.json()
                document_id = result.get('document', {}).get('id')
                document_name = result.get('document', {}).get('name', 'N/A')
                
                print(f"✅ 上傳成功！")
                print(f"📋 文件 ID: {document_id}")
                print(f"📋 文件名稱: {document_name}")
                
                # 簡單等待處理
                if document_id:
                    print("⏳ 等待處理...")
                    time.sleep(5)
                    self.check_document_status(document_id)
                
                return True
            else:
                print(f"❌ 上傳失敗: {response.text}")
                
                # 解析錯誤
                try:
                    error_data = response.json()
                    error_code = error_data.get('code', 'unknown')
                    error_message = error_data.get('message', 'No message')
                    print(f"🔍 錯誤: {error_code} - {error_message}")
                except:
                    pass
                
                return False
                
        except Exception as e:
            print(f"❌ 上傳異常: {e}")
            return False
    
    def check_document_status(self, document_id: str):
        """檢查文件狀態"""
        headers = {
            'Authorization': f'Bearer {DIFY_CONFIG["dataset_api_key"]}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(
                f'{DIFY_CONFIG["base_url"]}/v1/datasets/{self.dataset_id}/documents/{document_id}',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                status = result.get('indexing_status', 'unknown')
                word_count = result.get('word_count', 0)
                
                print(f"📊 文件狀態: {status}")
                if word_count > 0:
                    print(f"📊 處理字數: {word_count}")
                
                if status == 'completed':
                    print("✅ 處理完成")
                elif status == 'error':
                    error_msg = result.get('error', 'Unknown error')
                    print(f"❌ 處理失敗: {error_msg}")
                
        except Exception as e:
            print(f"⚠️ 檢查狀態失敗: {e}")
    
    def list_documents(self):
        """列出資料集中的文件"""
        if not self.dataset_id:
            print("❌ 沒有資料集 ID")
            return
        
        print(f"\n📋 檢查資料集 {self.dataset_id} 中的文件...")
        
        headers = {
            'Authorization': f'Bearer {DIFY_CONFIG["dataset_api_key"]}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(
                f'{DIFY_CONFIG["base_url"]}/v1/datasets/{self.dataset_id}/documents',
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                documents = result.get('data', [])
                
                print(f"📄 找到 {len(documents)} 個文件:")
                
                for doc in documents:
                    doc_name = doc.get('name', 'N/A')
                    status = doc.get('indexing_status', 'N/A')
                    word_count = doc.get('word_count', 0)
                    
                    print(f"  📄 {doc_name}")
                    print(f"     狀態: {status}, 字數: {word_count}")
                
                return len(documents) > 0
            else:
                print(f"❌ 列出文件失敗: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 列出文件異常: {e}")
            return False

def main():
    """主測試函數"""
    print("🧪 Dify 知識庫上傳測試 V2 - 修正版")
    print("=" * 60)
    print(f"🔗 API 端點: {DIFY_CONFIG['base_url']}")
    print(f"🔑 使用 Dataset API Token")
    print("🎯 目標: 解決嵌入模型問題，成功上傳到知識庫")
    print("=" * 60)
    
    # 初始化測試器
    tester = DifyUploadTesterV2()
    
    # 測試流程
    success = False
    
    # 1. 建立資料集
    print("\n🚀 步驟 1: 建立測試資料集")
    if not tester.create_dataset():
        print("❌ 建立資料集失敗，測試終止")
        return
    
    # 等待一下
    print("\n⏳ 等待 3 秒...")
    time.sleep(3)
    
    # 2. 嘗試多種上傳方法
    print("\n🚀 步驟 2: 嘗試多種上傳方法")
    success = tester.try_upload_methods()
    
    # 3. 檢查上傳結果
    print("\n🚀 步驟 3: 檢查上傳結果")
    has_documents = tester.list_documents()
    
    # 4. 測試結果
    print("\n" + "=" * 60)
    print("📊 測試結果總結")
    print("=" * 60)
    
    if success and has_documents:
        print("✅ 知識庫上傳測試成功！")
        print(f"📚 資料集 ID: {tester.dataset_id}")
        print("💡 員工資料已成功上傳到 Dify 知識庫")
        
        print("\n🔍 驗證步驟:")
        print("1. 登入 Dify 平台")
        print("2. 進入「知識庫」頁面")
        print(f"3. 找到資料集: 測試上傳修正版_{tester.dataset_id}")
        print("4. 確認員工資料檔案已上傳並處理完成")
        print("5. 在應用中配置該知識庫")
        print("6. 測試查詢員工資訊")
        
        print("\n🎉 恭喜！Dify 知識庫上傳功能正常！")
    else:
        print("❌ 知識庫上傳測試失敗")
        print("🔍 可能的問題:")
        print("- 嵌入模型未啟用或配置錯誤")
        print("- API Token 權限不足")
        print("- Dify 服務配置問題")
        print("- 網路連線問題")
        
        print("\n💡 建議:")
        print("1. 檢查 Dify 管理介面的模型設定")
        print("2. 確認向量化模型是否正常運行")
        print("3. 檢查知識庫相關配置")
    
    print("\n✅ 測試完成")

if __name__ == "__main__":
    main()