#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dify chunwei 應用測試腳本
測試與 Dify 平台中 chunwei 應用的整合
"""

import requests
import json
import sqlite3
import time

# Dify API 配置
DIFY_CONFIG = {
    'api_url': 'http://10.10.172.5/v1/chat-messages',
    'api_key': 'app-R5nTTZw6jSQX75sDvyUMxLgo',
    'base_url': 'http://10.10.172.5'
}

def test_dify_api_connection():
    """測試 Dify API 連接"""
    print("🔍 測試 Dify API 連接...")
    
    headers = {
        'Authorization': f'Bearer {DIFY_CONFIG["api_key"]}',
        'Content-Type': 'application/json'
    }
    
    # 簡單的測試請求
    payload = {
        'inputs': {},
        'query': 'Hello, can you respond to this test message?',
        'response_mode': 'blocking',
        'user': 'test_user'
    }
    
    try:
        response = requests.post(
            DIFY_CONFIG['api_url'],
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"📊 HTTP 狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Dify API 連接成功")
            print(f"📝 回應: {result.get('answer', 'No answer')[:100]}...")
            return True
        else:
            print(f"❌ API 請求失敗: {response.status_code}")
            print(f"錯誤詳情: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 網路連接錯誤: {e}")
        return False
    except Exception as e:
        print(f"❌ 未知錯誤: {e}")
        return False

def call_dify_chunwei(question: str, context_data: str = "") -> dict:
    """調用 Dify chunwei 應用"""
    
    headers = {
        'Authorization': f'Bearer {DIFY_CONFIG["api_key"]}',
        'Content-Type': 'application/json'
    }
    
    # 構建請求載荷
    payload = {
        'inputs': {
            'context': context_data
        } if context_data else {},
        'query': question,
        'response_mode': 'blocking',
        'user': 'rag_test_user'
    }
    
    try:
        print(f"🤖 調用 Dify chunwei: {question[:50]}...")
        start_time = time.time()
        
        response = requests.post(
            DIFY_CONFIG['api_url'],
            headers=headers,
            json=payload,
            timeout=60
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            return {
                'success': True,
                'answer': result.get('answer', ''),
                'response_time': elapsed,
                'message_id': result.get('message_id', ''),
                'conversation_id': result.get('conversation_id', '')
            }
        else:
            return {
                'success': False,
                'error': f"HTTP {response.status_code}: {response.text}",
                'response_time': elapsed
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'response_time': 0
        }

def test_basic_questions():
    """測試基本問題"""
    print("\n" + "="*60)
    print("📋 基本問題測試")
    print("="*60)
    
    test_questions = [
        "Hello, what can you help me with?",
        "What is artificial intelligence?",
        "Can you explain machine learning in simple terms?",
        "你好，你能用中文回答嗎？",
        "請介紹一下自己"
    ]
    
    results = []
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n🔸 測試 {i}: {question}")
        print("-" * 40)
        
        result = call_dify_chunwei(question)
        results.append(result)
        
        if result['success']:
            print(f"✅ 成功 ({result['response_time']:.1f}s)")
            print(f"📝 回應: {result['answer'][:200]}...")
            if len(result['answer']) > 200:
                print("     ... (回應已截斷)")
        else:
            print(f"❌ 失敗: {result['error']}")
    
    return results

def test_employee_data_analysis():
    """測試員工資料分析"""
    print("\n" + "="*60)
    print("👥 員工資料分析測試")
    print("="*60)
    
    # 從資料庫獲取員工資料
    try:
        conn = sqlite3.connect('tests/test_dify_integration/company.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM employees WHERE department = '技術部'")
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        employees = [dict(zip(columns, row)) for row in rows]
        conn.close()
        
        print(f"📊 檢索到 {len(employees)} 筆技術部員工資料")
        
    except Exception as e:
        print(f"❌ 資料庫錯誤: {e}")
        return None
    
    # 準備上下文資料
    context_data = json.dumps(employees, ensure_ascii=False, indent=2)
    
    # 測試問題
    analysis_questions = [
        "Based on the employee data provided, what is the average salary in the Technical Department?",
        "Who is the highest paid employee and what is their position?",
        "Can you analyze the salary distribution and provide insights?",
        "根據提供的員工資料，請分析技術部的薪資結構",
        "請計算平均薪資並提供薪資分析報告"
    ]
    
    results = []
    
    for i, question in enumerate(analysis_questions, 1):
        print(f"\n🔹 分析測試 {i}: {question}")
        print("-" * 50)
        
        result = call_dify_chunwei(question, context_data)
        results.append(result)
        
        if result['success']:
            print(f"✅ 成功 ({result['response_time']:.1f}s)")
            print(f"📊 分析結果:")
            print(result['answer'])
        else:
            print(f"❌ 失敗: {result['error']}")
        
        # 等待一下避免請求過於頻繁
        time.sleep(1)
    
    return results

def compare_with_deepseek():
    """與 DeepSeek 直接調用比較"""
    print("\n" + "="*60)
    print("⚖️ Dify vs DeepSeek 比較測試")
    print("="*60)
    
    test_question = "What is the sum of 100 + 200? Please explain your calculation."
    
    print(f"📝 測試問題: {test_question}")
    
    # 1. Dify chunwei 回應
    print("\n🔸 Dify chunwei 回應:")
    print("-" * 30)
    dify_result = call_dify_chunwei(test_question)
    
    if dify_result['success']:
        print(f"✅ Dify ({dify_result['response_time']:.1f}s): {dify_result['answer']}")
    else:
        print(f"❌ Dify 失敗: {dify_result['error']}")
    
    # 2. DeepSeek SSH 回應 (簡化版)
    print("\n🔸 DeepSeek SSH 回應:")
    print("-" * 30)
    
    try:
        import paramiko
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect('10.10.172.5', username='svd', password='1234', timeout=10)
        
        escaped_prompt = test_question.replace('"', '\\"')
        command = f'echo "{escaped_prompt}" | ollama run deepseek-r1:14b'
        
        start_time = time.time()
        stdin, stdout, stderr = ssh.exec_command(command, timeout=60)
        response = stdout.read().decode('utf-8', errors='replace')
        elapsed = time.time() - start_time
        
        ssh.close()
        
        if response.strip() and '�' not in response:
            print(f"✅ DeepSeek ({elapsed:.1f}s): {response[:200]}...")
        else:
            print("❌ DeepSeek 回應有問題或編碼錯誤")
    
    except Exception as e:
        print(f"❌ DeepSeek SSH 錯誤: {e}")

def main():
    """主測試函數"""
    print("🚀 Dify chunwei 應用整合測試")
    print("=" * 60)
    print(f"🔗 API 端點: {DIFY_CONFIG['api_url']}")
    print(f"🔑 API Key: {DIFY_CONFIG['api_key'][:20]}...")
    print("=" * 60)
    
    # 1. 測試連接
    if not test_dify_api_connection():
        print("\n❌ Dify API 連接失敗，請檢查配置")
        return
    
    # 2. 基本問題測試
    basic_results = test_basic_questions()
    
    # 3. 員工資料分析測試
    analysis_results = test_employee_data_analysis()
    
    # 4. 與 DeepSeek 比較
    compare_with_deepseek()
    
    # 5. 總結報告
    print("\n" + "="*60)
    print("📊 測試總結報告")
    print("="*60)
    
    if basic_results:
        success_count = sum(1 for r in basic_results if r['success'])
        print(f"📋 基本測試: {success_count}/{len(basic_results)} 成功")
        
        if success_count > 0:
            avg_time = sum(r['response_time'] for r in basic_results if r['success']) / success_count
            print(f"⏱️ 平均回應時間: {avg_time:.1f} 秒")
    
    if analysis_results:
        analysis_success = sum(1 for r in analysis_results if r['success'])
        print(f"👥 資料分析測試: {analysis_success}/{len(analysis_results)} 成功")
    
    print("\n✅ 測試完成！")
    print("💡 您現在可以將 Dify chunwei 整合到 simple_rag_test.py 中")

if __name__ == "__main__":
    main()