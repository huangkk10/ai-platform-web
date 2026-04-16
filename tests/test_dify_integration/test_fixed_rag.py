#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修復版永久記憶 RAG 測試腳本
解決上下文傳遞問題
"""

import requests
import json
import sqlite3
import time
import os
import uuid
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional

# Dify API 配置
DIFY_CONFIG = {
    'api_url': 'http://10.253.43.244/v1/chat-messages',
    'api_key': 'app-R5nTTZw6jSQX75sDvyUMxLgo',
    'base_url': 'http://10.253.43.244'
}

class FixedRAGTester:
    """修復版 RAG 測試器"""
    
    def __init__(self):
        self.employees_data = self.load_employee_data()
    
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
    
    def call_dify_fixed(self, question: str, employee_context: str = "") -> dict:
        """修復版 Dify API 調用"""
        headers = {
            'Authorization': f'Bearer {DIFY_CONFIG["api_key"]}',
            'Content-Type': 'application/json'
        }
        
        # 方法1: 將上下文直接嵌入問題中
        if employee_context:
            enhanced_question = f"""
基於以下員工資料回答問題：

{employee_context}

問題：{question}

請根據上述資料回答，如果資料中有相關資訊，請詳細說明。
"""
        else:
            enhanced_question = question
        
        # 嘗試多種參數組合
        payload_options = [
            # 選項1: 使用 inputs.context
            {
                'inputs': {'context': employee_context} if employee_context else {},
                'query': question,
                'response_mode': 'blocking',
                'user': 'fixed_test'
            },
            # 選項2: 將上下文嵌入問題
            {
                'inputs': {},
                'query': enhanced_question,
                'response_mode': 'blocking',
                'user': 'fixed_test'
            },
            # 選項3: 使用 inputs.data
            {
                'inputs': {'data': employee_context} if employee_context else {},
                'query': question,
                'response_mode': 'blocking',
                'user': 'fixed_test'
            }
        ]
        
        for i, payload in enumerate(payload_options, 1):
            print(f"\n🔄 嘗試方法 {i}...")
            
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
                    
                    # 檢查答案品質
                    if self.is_good_answer(answer, employee_context):
                        print(f"✅ 方法 {i} 成功！")
                        return {
                            'success': True,
                            'answer': answer,
                            'response_time': elapsed,
                            'method': i
                        }
                    else:
                        print(f"⚠️ 方法 {i} 回答品質不佳")
                        print(f"回答片段: {answer[:100]}...")
                else:
                    print(f"❌ 方法 {i} HTTP 錯誤: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ 方法 {i} 異常: {e}")
        
        return {
            'success': False,
            'error': '所有方法都失敗',
            'response_time': 0
        }
    
    def is_good_answer(self, answer: str, context: str) -> bool:
        """檢查答案品質"""
        if not context:
            return True
        
        # 檢查是否包含員工姓名
        employee_names = [emp['name'] for emp in self.employees_data]
        found_names = [name for name in employee_names if name in answer]
        
        # 檢查是否拒絕回答
        refuse_phrases = ['无法回答', '无法提供', '属于公司的内部信息', '不便对外公开']
        is_refusing = any(phrase in answer for phrase in refuse_phrases)
        
        return len(found_names) > 0 and not is_refusing
    
    def test_technical_department(self):
        """測試技術部查詢"""
        print("\n" + "="*60)
        print("🔍 測試技術部員工查詢")
        print("="*60)
        
        # 獲取技術部員工
        tech_employees = [emp for emp in self.employees_data if emp['department'] == '技術部']
        
        if not tech_employees:
            print("❌ 沒有找到技術部員工")
            return
        
        print(f"📊 技術部員工清單:")
        for emp in tech_employees:
            print(f"   - {emp['name']}: {emp['position']}, 薪資: {emp['salary']:,}")
        
        # 構建上下文
        context = "技術部員工資訊：\n"
        for emp in tech_employees:
            context += f"- {emp['name']}，職位：{emp['position']}，薪資：{emp['salary']:,} 元\n"
        
        question = "技術部有哪些員工？請列出他們的姓名、職位和薪資。"
        
        print(f"\n❓ 問題: {question}")
        print(f"📝 上下文: {context}")
        
        result = self.call_dify_fixed(question, context)
        
        if result['success']:
            print(f"\n✅ AI 回答 (方法 {result['method']}):")
            print(result['answer'])
            
            # 分析回答
            employee_names = [emp['name'] for emp in tech_employees]
            found_names = [name for name in employee_names if name in result['answer']]
            
            print(f"\n📊 回答分析:")
            print(f"   期望員工數: {len(tech_employees)}")
            print(f"   提及員工數: {len(found_names)}")
            print(f"   提及的員工: {found_names}")
            
            if len(found_names) == len(tech_employees):
                print("🎉 完美！AI 正確使用了所有員工資料")
            elif len(found_names) > 0:
                print("👍 不錯！AI 使用了部分員工資料")
            else:
                print("😞 失敗！AI 沒有使用員工資料")
        else:
            print(f"\n❌ 所有方法都失敗: {result['error']}")
    
    def test_specific_employee(self):
        """測試特定員工查詢"""
        print("\n" + "="*60)
        print("🔍 測試特定員工查詢")
        print("="*60)
        
        # 選擇李美華
        target_employee = None
        for emp in self.employees_data:
            if emp['name'] == '李美華':
                target_employee = emp
                break
        
        if not target_employee:
            print("❌ 沒有找到李美華的資料")
            return
        
        print(f"📊 李美華資料:")
        print(f"   姓名: {target_employee['name']}")
        print(f"   部門: {target_employee['department']}")
        print(f"   職位: {target_employee['position']}")
        print(f"   薪資: {target_employee['salary']:,}")
        print(f"   入職日期: {target_employee['hire_date']}")
        
        context = f"""
員工資料：
姓名：{target_employee['name']}
部門：{target_employee['department']}
職位：{target_employee['position']}
薪資：{target_employee['salary']:,} 元
入職日期：{target_employee['hire_date']}
電子郵件：{target_employee['email']}
"""
        
        question = "李美華是什麼職位？她的薪資是多少？"
        
        print(f"\n❓ 問題: {question}")
        
        result = self.call_dify_fixed(question, context)
        
        if result['success']:
            print(f"\n✅ AI 回答 (方法 {result['method']}):")
            print(result['answer'])
            
            # 檢查回答準確性
            correct_info = []
            if target_employee['position'] in result['answer']:
                correct_info.append("職位")
            if str(target_employee['salary']) in result['answer']:
                correct_info.append("薪資")
            
            print(f"\n📊 回答準確性:")
            print(f"   正確資訊: {correct_info}")
            
            if len(correct_info) == 2:
                print("🎉 完全正確！")
            elif len(correct_info) == 1:
                print("👍 部分正確")
            else:
                print("😞 回答不準確")
        else:
            print(f"\n❌ 查詢失敗: {result['error']}")

def main():
    """主測試函數"""
    print("🚀 修復版永久記憶 RAG 測試系統")
    print("=" * 60)
    print("🎯 目標：修復上下文傳遞問題")
    print("=" * 60)
    
    tester = FixedRAGTester()
    
    if not tester.employees_data:
        print("❌ 無法載入員工資料，測試終止")
        return
    
    # 1. 測試技術部查詢
    tester.test_technical_department()
    
    # 2. 測試特定員工查詢
    tester.test_specific_employee()
    
    print("\n" + "="*60)
    print("📊 修復測試完成")
    print("="*60)
    print("如果仍然失敗，可能需要:")
    print("1. 檢查 Dify 應用的 prompt 設定")
    print("2. 確認 API 金鑰權限")
    print("3. 聯繫 Dify 管理員確認應用配置")

if __name__ == "__main__":
    main()