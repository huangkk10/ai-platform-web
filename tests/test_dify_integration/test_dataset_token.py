#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dify 知識庫 API 測試程式 - 使用 Dataset Token
現在可以自動管理知識庫了！
"""

import requests
import json
import sqlite3
import time
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

# Dify API 配置
DIFY_CONFIG = {
    # 聊天應用 API (用於查詢)
    'chat_api_url': 'http://10.10.172.37/v1/chat-messages',
    'chat_api_key': 'app-R5nTTZw6jSQX75sDvyUMxLgo',
    
    # 知識庫 API (用於管理資料集)
    'dataset_api_key': 'dataset-JLa32OwILQHkgPqYStTCW4sC',
    'base_url': 'http://10.10.172.37'
}

class DifyFullKnowledgeBaseTester:
    """完整的 Dify 知識庫測試器 - 使用 Dataset Token"""
    
    def __init__(self):
        self.employees_data = self.load_employee_data()
        self.dataset_id = None
        self.document_ids = []
        
        # 不同 API 的請求頭
        self.dataset_headers = {
            'Authorization': f'Bearer {DIFY_CONFIG["dataset_api_key"]}',
            'Content-Type': 'application/json'
        }
        
        self.chat_headers = {
            'Authorization': f'Bearer {DIFY_CONFIG["chat_api_key"]}',
            'Content-Type': 'application/json'
        }
    
    def load_employee_data(self):
        """載入員工資料"""
        try:
            conn = sqlite3.connect('tests/test_dify_integration/company.db')
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM employees")
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            conn.close()
            
            employees = []
            for row in rows:
                employee = dict(zip(columns, row))
                employees.append(employee)
            
            print(f"📊 載入 {len(employees)} 位員工資料")
            return employees
        except Exception as e:
            print(f"❌ 載入資料失敗: {e}")
            return []
    
    def create_dataset(self) -> bool:
        """使用 Dataset API 建立資料集"""
        print("\n📚 使用 Dataset API 建立資料集...")
        
        dataset_data = {
            'name': f'員工資料庫_完整版_{int(time.time())}',
            'description': '使用 Dataset API 建立的完整員工資料庫，支援自動管理和查詢'
        }
        
        try:
            response = requests.post(
                f'{DIFY_CONFIG["base_url"]}/v1/datasets',
                headers=self.dataset_headers,
                json=dataset_data,
                timeout=30
            )
            
            print(f"📥 建立資料集回應: HTTP {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.dataset_id = result.get('id')
                print(f"✅ 資料集建立成功！")
                print(f"   📋 資料集 ID: {self.dataset_id}")
                print(f"   📝 資料集名稱: {result.get('name')}")
                return True
            else:
                print(f"❌ 建立資料集失敗: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 建立資料集異常: {e}")
            return False
    
    def upload_employee_documents(self) -> bool:
        """上傳員工文件到知識庫"""
        if not self.dataset_id:
            print("❌ 沒有資料集 ID，無法上傳文件")
            return False
        
        print(f"\n📄 上傳 {len(self.employees_data)} 份員工文件到知識庫...")
        
        success_count = 0
        
        for i, employee in enumerate(self.employees_data, 1):
            # 構建詳細的員工文件內容
            document_content = f"""# {employee['name']} - 員工檔案

## 基本資訊
- **員工編號**: {employee['id']}
- **姓名**: {employee['name']}
- **部門**: {employee['department']}
- **職位**: {employee['position']}
- **薪資**: {employee['salary']:,} 元（月薪）
- **入職日期**: {employee['hire_date']}
- **電子郵件**: {employee['email']}

## 詳細描述
{employee['name']} 是 {employee['department']} 的 {employee['position']}，
員工編號為 {employee['id']}，月薪 {employee['salary']:,} 元。
於 {employee['hire_date']} 入職，聯絡信箱為 {employee['email']}。

## 部門資訊
所屬部門：{employee['department']}
職位層級：{employee['position']}
薪資水準：{employee['salary']:,} 元

## 聯絡方式
Email: {employee['email']}
入職時間: {employee['hire_date']}
"""
            
            document_data = {
                'text': document_content,
                'metadata': {
                    'employee_id': str(employee['id']),
                    'name': employee['name'],
                    'department': employee['department'],
                    'position': employee['position'],
                    'salary': str(employee['salary']),
                    'hire_date': employee['hire_date'],
                    'source': 'employee_database'
                }
            }
            
            try:
                response = requests.post(
                    f'{DIFY_CONFIG["base_url"]}/v1/datasets/{self.dataset_id}/documents',
                    headers=self.dataset_headers,
                    json=document_data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    doc_id = result.get('id')
                    self.document_ids.append(doc_id)
                    success_count += 1
                    print(f"✅ {employee['name']} 上傳成功 ({i}/{len(self.employees_data)}) - Doc ID: {doc_id}")
                else:
                    print(f"❌ {employee['name']} 上傳失敗: HTTP {response.status_code}")
                    print(f"   回應: {response.text}")
                
                # 避免請求過於頻繁
                time.sleep(0.3)
                
            except Exception as e:
                print(f"❌ 上傳 {employee['name']} 異常: {e}")
        
        print(f"\n📊 上傳結果: {success_count}/{len(self.employees_data)} 份文件成功")
        return success_count == len(self.employees_data)
    
    def wait_for_indexing(self):
        """等待知識庫索引建立完成"""
        print("\n⏳ 等待知識庫索引建立...")
        
        for i in range(6):  # 等待最多 60 秒
            time.sleep(10)
            
            try:
                # 檢查資料集狀態
                response = requests.get(
                    f'{DIFY_CONFIG["base_url"]}/v1/datasets/{self.dataset_id}',
                    headers=self.dataset_headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    doc_count = result.get('document_count', 0)
                    print(f"   索引進度: {doc_count} 文件已索引 ({(i+1)*10}s)")
                    
                    if doc_count >= len(self.employees_data):
                        print("✅ 索引建立完成！")
                        return True
                else:
                    print(f"   檢查狀態失敗: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"   檢查索引狀態異常: {e}")
        
        print("⚠️ 索引可能還在建立中，繼續測試...")
        return False
    
    def query_with_dataset(self, question: str) -> dict:
        """使用配置了知識庫的應用進行查詢"""
        print(f"\n❓ 查詢問題: {question}")
        
        payload = {
            'inputs': {},
            'query': question,
            'response_mode': 'blocking',
            'user': 'dataset_test',
            'conversation_id': '',
            'files': []
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                DIFY_CONFIG['chat_api_url'],
                headers=self.chat_headers,
                json=payload,
                timeout=30
            )
            elapsed = time.time() - start_time
            
            print(f"📥 回應: HTTP {response.status_code} ({elapsed:.1f}s)")
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get('answer', '')
                metadata = result.get('metadata', {})
                
                print(f"✅ AI 回答:")
                print(answer)
                
                # 檢查是否使用了知識庫
                retrieval_sources = metadata.get('retrieval_sources', [])
                if retrieval_sources:
                    print(f"\n📚 知識庫檢索結果 ({len(retrieval_sources)} 個來源):")
                    for i, source in enumerate(retrieval_sources, 1):
                        print(f"   {i}. 相似度: {source.get('score', 'N/A')}")
                        print(f"      文件片段: {source.get('content', 'N/A')[:100]}...")
                        print()
                    
                    return {
                        'success': True,
                        'answer': answer,
                        'uses_knowledge_base': True,
                        'sources_count': len(retrieval_sources),
                        'response_time': elapsed
                    }
                else:
                    print("⚠️ 沒有檢索到知識庫資源")
                    return {
                        'success': True,
                        'answer': answer,
                        'uses_knowledge_base': False,
                        'sources_count': 0,
                        'response_time': elapsed
                    }
            else:
                print(f"❌ 查詢失敗: {response.text}")
                return {'success': False, 'error': response.text}
                
        except Exception as e:
            print(f"❌ 查詢異常: {e}")
            return {'success': False, 'error': str(e)}
    
    def run_comprehensive_test(self):
        """執行完整的知識庫測試"""
        print("\n" + "="*60)
        print("🧠 完整知識庫功能測試")
        print("="*60)
        
        test_questions = [
            "技術部有哪些員工？請列出姓名和職位。",
            "李美華的詳細資訊是什麼？包括薪資和入職時間。",
            "薪資最高的員工是誰？多少錢？",
            "2022年入職的員工有哪些？",
            "技術部的平均薪資是多少？",
            "人資部和財務部哪個部門薪資較高？",
            "入職最早和最晚的員工分別是誰？",
            "email 地址包含 'li' 的員工是誰？"
        ]
        
        results = []
        kb_usage_count = 0
        total_response_time = 0
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n--- 測試 {i}/{len(test_questions)} ---")
            
            result = self.query_with_dataset(question)
            results.append({
                'question': question,
                'result': result
            })
            
            if result.get('success') and result.get('uses_knowledge_base'):
                kb_usage_count += 1
            
            if result.get('response_time'):
                total_response_time += result['response_time']
            
            # 避免請求過於頻繁
            time.sleep(1)
        
        # 統計結果
        print("\n" + "="*60)
        print("📊 完整測試結果統計")
        print("="*60)
        
        successful_queries = sum(1 for r in results if r['result'].get('success'))
        avg_response_time = total_response_time / len(test_questions) if test_questions else 0
        
        print(f"✅ 成功查詢: {successful_queries}/{len(test_questions)}")
        print(f"📚 使用知識庫: {kb_usage_count}/{len(test_questions)}")
        print(f"⏱️ 平均回應時間: {avg_response_time:.1f}s")
        
        if kb_usage_count >= len(test_questions) * 0.7:  # 70% 以上使用知識庫
            print("\n🎉 知識庫整合大成功！")
            print("   📋 AI 能自動檢索員工資料")
            print("   🧠 實現了真正的永久記憶")
            print("   🚀 可以用於生產環境")
        elif kb_usage_count > 0:
            print("\n👍 知識庫部分成功")
            print("   ⚠️ 可能需要調整應用配置")
            print("   🔧 或等待更長時間讓索引完成")
        else:
            print("\n❌ 知識庫整合失敗")
            print("   🔍 請檢查應用是否配置使用資料集")
            print("   ⏰ 或需要等待索引建立完成")
        
        return results
    
    def list_datasets_info(self):
        """列出資料集資訊"""
        print("\n📋 列出所有資料集...")
        
        try:
            response = requests.get(
                f'{DIFY_CONFIG["base_url"]}/v1/datasets',
                headers=self.dataset_headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                datasets = result.get('data', [])
                
                print(f"📚 找到 {len(datasets)} 個資料集:")
                for dataset in datasets:
                    print(f"   - {dataset['name']} (ID: {dataset['id']})")
                    print(f"     文件數: {dataset.get('document_count', 0)}")
                    print(f"     建立時間: {dataset.get('created_at', 'N/A')}")
                    print()
                
                return datasets
            else:
                print(f"❌ 列出資料集失敗: HTTP {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ 列出資料集異常: {e}")
            return []
    
    def cleanup_test_dataset(self):
        """清理測試資料集"""
        if not self.dataset_id:
            return
        
        print(f"\n🧹 清理測試資料集...")
        
        try:
            response = requests.delete(
                f'{DIFY_CONFIG["base_url"]}/v1/datasets/{self.dataset_id}',
                headers=self.dataset_headers,
                timeout=30
            )
            
            if response.status_code == 200:
                print("✅ 測試資料集清理完成")
            else:
                print(f"⚠️ 清理失敗: HTTP {response.status_code}")
                print(f"   可能需要手動清理資料集 ID: {self.dataset_id}")
                
        except Exception as e:
            print(f"❌ 清理異常: {e}")

def main():
    """主測試函數"""
    print("🚀 Dify 完整知識庫 API 測試系統")
    print("=" * 60)
    print("🎯 目標：使用 Dataset Token 實現完整自動化")
    print("🔑 Dataset Token: dataset-JLa32OwILQHkgPqYStTCW4sC")
    print("=" * 60)
    
    tester = DifyFullKnowledgeBaseTester()
    
    if not tester.employees_data:
        print("❌ 無法載入員工資料，測試終止")
        return
    
    try:
        # 1. 列出現有資料集
        tester.list_datasets_info()
        
        # 2. 建立新資料集
        if not tester.create_dataset():
            print("❌ 無法建立資料集，測試終止")
            return
        
        # 3. 上傳員工文件
        if not tester.upload_employee_documents():
            print("❌ 文件上傳不完整，繼續測試...")
        
        # 4. 等待索引建立
        tester.wait_for_indexing()
        
        # 5. 執行完整測試
        results = tester.run_comprehensive_test()
        
        # 6. 顯示最終結果
        print("\n" + "="*60)
        print("🎉 測試完成！Dataset Token 功能驗證")
        print("="*60)
        print(f"📋 資料集 ID: {tester.dataset_id}")
        print(f"📄 上傳文件數: {len(tester.document_ids)}")
        
        kb_usage = sum(1 for r in results if r['result'].get('uses_knowledge_base'))
        print(f"📚 知識庫使用率: {kb_usage}/{len(results)} ({kb_usage/len(results)*100:.1f}%)")
        
    except KeyboardInterrupt:
        print("\n⚠️ 測試被中斷")
    finally:
        # 詢問是否清理
        cleanup = input("\n是否清理測試資料集？(y/N): ").strip().lower()
        if cleanup in ['y', 'yes']:
            tester.cleanup_test_dataset()
        else:
            print(f"💾 資料集保留，ID: {tester.dataset_id}")
            print("   您可以在 Dify 平台查看或手動管理")

if __name__ == "__main__":
    main()