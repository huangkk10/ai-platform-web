#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dify 手動知識庫測試程式
適用於已手動配置知識庫的 Dify 應用
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
    'api_url': 'http://10.253.43.244/v1/chat-messages',
    'api_key': 'app-R5nTTZw6jSQX75sDvyUMxLgo',
    'base_url': 'http://10.253.43.244'
}

class DifyManualKnowledgeBaseTester:
    """Dify 手動知識庫測試器"""
    
    def __init__(self):
        self.employees_data = self.load_employee_data()
        self.conversation_id = None
    
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
    
    def generate_knowledge_base_content(self) -> str:
        """生成知識庫內容"""
        content = "# 公司員工資料庫\n\n"
        
        # 按部門分組
        departments = {}
        for emp in self.employees_data:
            dept = emp['department']
            if dept not in departments:
                departments[dept] = []
            departments[dept].append(emp)
        
        # 生成每個部門的內容
        for dept_name, employees in departments.items():
            content += f"## {dept_name}\n\n"
            
            for emp in employees:
                content += f"### {emp['name']}\n"
                content += f"- **員工編號**: {emp['id']}\n"
                content += f"- **姓名**: {emp['name']}\n"
                content += f"- **部門**: {emp['department']}\n"
                content += f"- **職位**: {emp['position']}\n"
                content += f"- **薪資**: {emp['salary']:,} 元（月薪）\n"
                content += f"- **入職日期**: {emp['hire_date']}\n"
                content += f"- **電子郵件**: {emp['email']}\n\n"
        
        # 添加統計資訊
        content += "## 統計資訊\n\n"
        content += f"- **總員工數**: {len(self.employees_data)} 人\n"
        
        for dept_name, employees in departments.items():
            avg_salary = sum(emp['salary'] for emp in employees) / len(employees)
            content += f"- **{dept_name}**: {len(employees)} 人，平均薪資 {avg_salary:,.0f} 元\n"
        
        return content
    
    def save_knowledge_base_file(self):
        """儲存知識庫檔案供手動上傳"""
        content = self.generate_knowledge_base_content()
        
        filename = 'tests/test_dify_integration/company_knowledge_base.md'
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 知識庫檔案已儲存: {filename}")
        print("📝 請手動執行以下步驟:")
        print("   1. 登入 Dify 平台")
        print("   2. 建立新的資料集")
        print(f"   3. 上傳檔案: {filename}")
        print("   4. 配置應用使用該資料集")
        print("   5. 回來運行測試查詢")
        
        return filename
    
    def query_with_knowledge_base(self, question: str) -> dict:
        """使用配置了知識庫的應用進行查詢"""
        print(f"\n❓ 查詢問題: {question}")
        
        headers = {
            'Authorization': f'Bearer {DIFY_CONFIG["api_key"]}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'inputs': {},
            'query': question,
            'response_mode': 'blocking',
            'user': 'manual_kb_test',
            'conversation_id': self.conversation_id or '',
            'files': []
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                DIFY_CONFIG['api_url'],
                headers=headers,
                json=payload,
                timeout=30
            )
            elapsed = time.time() - start_time
            
            print(f"📥 回應: HTTP {response.status_code} ({elapsed:.1f}s)")
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get('answer', '')
                metadata = result.get('metadata', {})
                self.conversation_id = result.get('conversation_id', self.conversation_id)
                
                print(f"✅ AI 回答:")
                print(answer)
                
                # 檢查是否使用了知識庫
                retrieval_sources = metadata.get('retrieval_sources', [])
                if retrieval_sources:
                    print(f"\n📚 使用的知識庫資源 ({len(retrieval_sources)} 個):")
                    for i, source in enumerate(retrieval_sources, 1):
                        print(f"   {i}. 文件: {source.get('document_name', 'N/A')}")
                        print(f"      相似度: {source.get('score', 'N/A')}")
                        print(f"      內容片段: {source.get('content', 'N/A')[:100]}...")
                        print()
                    
                    return {
                        'success': True,
                        'answer': answer,
                        'uses_knowledge_base': True,
                        'sources_count': len(retrieval_sources),
                        'response_time': elapsed
                    }
                else:
                    print("⚠️ 沒有使用知識庫資源")
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
    
    def analyze_answer_quality(self, question: str, answer: str, expected_info: List[str]) -> dict:
        """分析回答品質"""
        found_info = []
        
        for info in expected_info:
            if info in answer:
                found_info.append(info)
        
        accuracy = len(found_info) / len(expected_info) if expected_info else 0
        
        return {
            'expected_count': len(expected_info),
            'found_count': len(found_info),
            'found_info': found_info,
            'accuracy': accuracy
        }
    
    def test_comprehensive_queries(self):
        """執行綜合查詢測試"""
        print("\n" + "="*60)
        print("🧠 綜合知識庫查詢測試")
        print("="*60)
        
        test_cases = [
            {
                'question': '技術部有哪些員工？請列出他們的姓名和職位。',
                'expected_info': ['張小明', '李美華', '林志豪', '軟體工程師', '資深工程師', '技術主管'],
                'description': '部門員工查詢'
            },
            {
                'question': '李美華的薪資是多少？她在哪個部門工作？',
                'expected_info': ['李美華', '95000', '95,000', '技術部', '資深工程師'],
                'description': '特定員工資訊'
            },
            {
                'question': '哪個部門的員工人數最多？',
                'expected_info': ['技術部', '3'],
                'description': '部門統計查詢'
            },
            {
                'question': '薪資最高的員工是誰？薪資是多少？',
                'expected_info': ['林志豪', '120000', '120,000', '技術主管'],
                'description': '薪資排序查詢'
            },
            {
                'question': '人事部和財務部的員工總薪資各是多少？',
                'expected_info': ['人事部', '財務部', '150000', '150,000', '140000', '140,000'],
                'description': '部門薪資統計'
            },
            {
                'question': '入職時間最早的員工是誰？什麼時候入職的？',
                'expected_info': ['王大明', '2021-01-15'],
                'description': '時間序列查詢'
            }
        ]
        
        results = []
        knowledge_base_usage_count = 0
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n--- 測試 {i}/{len(test_cases)}: {test_case['description']} ---")
            
            result = self.query_with_knowledge_base(test_case['question'])
            
            if result['success']:
                # 分析回答品質
                quality = self.analyze_answer_quality(
                    test_case['question'],
                    result['answer'],
                    test_case['expected_info']
                )
                
                result.update(quality)
                
                if result['uses_knowledge_base']:
                    knowledge_base_usage_count += 1
                
                print(f"📊 回答品質: {quality['found_count']}/{quality['expected_count']} 項正確 ({quality['accuracy']:.1%})")
                
                if quality['found_info']:
                    print(f"✅ 正確資訊: {', '.join(quality['found_info'])}")
            
            results.append({
                'test_case': test_case,
                'result': result
            })
            
            # 避免請求過於頻繁
            time.sleep(1)
        
        # 統計結果
        print("\n" + "="*60)
        print("📊 測試結果統計")
        print("="*60)
        
        successful_queries = sum(1 for r in results if r['result']['success'])
        total_accuracy = sum(r['result'].get('accuracy', 0) for r in results if r['result']['success'])
        avg_accuracy = total_accuracy / successful_queries if successful_queries > 0 else 0
        
        print(f"成功查詢: {successful_queries}/{len(test_cases)}")
        print(f"使用知識庫: {knowledge_base_usage_count}/{len(test_cases)}")
        print(f"平均準確度: {avg_accuracy:.1%}")
        
        if knowledge_base_usage_count > 0:
            print("\n🎉 知識庫整合成功！")
            print("   AI 能夠從知識庫檢索相關資訊並回答問題")
        else:
            print("\n⚠️ 知識庫未正確配置")
            print("   請確認:")
            print("   1. 資料集已正確建立並上傳資料")
            print("   2. 應用已配置使用該資料集")
            print("   3. RAG 檢索功能已啟用")
        
        return results

def main():
    """主測試函數"""
    print("🚀 Dify 手動知識庫測試系統")
    print("=" * 60)
    print("🎯 目標：測試手動配置的知識庫功能")
    print("=" * 60)
    
    tester = DifyManualKnowledgeBaseTester()
    
    if not tester.employees_data:
        print("❌ 無法載入員工資料，測試終止")
        return
    
    # 1. 生成知識庫檔案
    print("\n📁 生成知識庫檔案...")
    filename = tester.save_knowledge_base_file()
    
    # 2. 等待用戶手動配置
    print("\n" + "="*60)
    input("⏳ 請按照上述步驟手動配置知識庫，完成後按 Enter 繼續...")
    
    # 3. 執行測試查詢
    results = tester.test_comprehensive_queries()
    
    # 4. 提供後續建議
    print("\n" + "="*60)
    print("💡 後續建議")
    print("="*60)
    
    knowledge_base_used = any(r['result'].get('uses_knowledge_base', False) for r in results)
    
    if knowledge_base_used:
        print("✅ 恭喜！真正的永久記憶知識庫已成功運作")
        print("   📚 AI 能夠自動檢索員工資料")
        print("   🧠 實現了真正的知識持久化")
        print("   🔄 可以擴展到更多企業資料")
    else:
        print("🔧 需要進一步配置:")
        print("   1. 檢查 Dify 應用的 RAG 設定")
        print("   2. 確認資料集正確關聯")
        print("   3. 驗證檔案上傳和索引狀態")

if __name__ == "__main__":
    main()