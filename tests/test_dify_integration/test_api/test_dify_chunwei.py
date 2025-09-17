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
    'dataset_api_url': 'http://10.10.172.5/v1/datasets/j89ytSyDedYS4sDly2Jnqz0a/retrieve',
    'api_key': 'app-Sql11xracJ71PtZThNJ4ZQQW',
    'dataset_key': 'dataset-j89ytSyDedYS4sDly2Jnqz0a',
    'base_url': 'http://10.10.172.5'
}

def test_dify_dataset_api():
    """測試 Dify Dataset API 連接"""
    print("🔍 測試 Dify Dataset API 連接...")
    
    headers = {
        'Authorization': f'Bearer {DIFY_CONFIG["dataset_key"]}',
        'Content-Type': 'application/json'
    }
    
    # 首先檢查 dataset 是否存在
    dataset_id = DIFY_CONFIG['dataset_api_url'].split('/')[-2]
    print(f"🔑 檢查 Dataset ID: {dataset_id}")
    
    # Dataset retrieval 測試請求 - 使用正確的格式
    payload = {
        'query': 'Python',
        'retrieval_model': {
            'search_method': 'semantic_search',
            'reranking_enable': False,
            'top_k': 3,
            'score_threshold_enabled': False
        }
    }
    
    try:
        response = requests.post(
            DIFY_CONFIG['dataset_api_url'],
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"📊 HTTP 狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Dify Dataset API 連接成功")
            print(f"📝 檢索結果數量: {len(result.get('records', []))}")
            if result.get('records'):
                print(f"📄 第一筆結果: {result['records'][0].get('content', 'No content')[:100]}...")
            return True
        elif response.status_code == 404:
            print("❌ Dataset 不存在或 API 路徑錯誤")
            print("💡 可能的問題:")
            print("   1. Dataset ID 不正確")
            print("   2. Dataset 已被刪除")
            print("   3. API Key 沒有訪問權限")
            print("   4. Dify API 路徑已變更")
            print(f"🔗 嘗試訪問的 URL: {DIFY_CONFIG['dataset_api_url']}")
            return False
        elif response.status_code == 401:
            print("❌ API Key 認證失敗")
            print("💡 請檢查 Dataset API Key 是否正確")
            return False
        elif response.status_code == 403:
            print("❌ 沒有訪問權限")
            print("💡 API Key 可能沒有該 Dataset 的訪問權限")
            return False
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

def test_dify_chat_api():
    """測試 Dify Chat API 連接"""
    print("🔍 測試 Dify Chat API 連接...")
    
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
            timeout=60
        )
        
        print(f"📊 HTTP 狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Dify Chat API 連接成功")
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

def test_dify_api_connection():
    """測試 Dify API 連接"""
    print("🔍 測試 Dify API 連接...")
    
    # 先測試 Chat API
    chat_success = test_dify_chat_api()
    
    # 再測試 Dataset API
    dataset_success = test_dify_dataset_api()
    
    # 如果 Dataset API 失敗，嘗試其他可能的端點
    if not dataset_success:
        print("\n🔧 嘗試其他可能的 Dataset API 端點...")
        alternative_endpoints = [
            f"{DIFY_CONFIG['base_url']}/v1/datasets/{DIFY_CONFIG['dataset_key'].split('-')[1]}/retrieve",
            f"{DIFY_CONFIG['base_url']}/v1/knowledge-retrieval",
            f"{DIFY_CONFIG['base_url']}/v1/datasets/retrieval"
        ]
        
        for endpoint in alternative_endpoints:
            print(f"🔗 嘗試: {endpoint}")
            success = test_alternative_dataset_endpoint(endpoint)
            if success:
                print(f"✅ 找到可用的端點: {endpoint}")
                # 更新配置
                DIFY_CONFIG['dataset_api_url'] = endpoint
                dataset_success = True
                break
    
    return chat_success or dataset_success

def test_alternative_dataset_endpoint(endpoint_url):
    """測試替代的 Dataset API 端點"""
    headers = {
        'Authorization': f'Bearer {DIFY_CONFIG["dataset_key"]}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'query': 'test',
        'retrieval_model': {
            'search_method': 'semantic_search',
            'top_k': 1
        }
    }
    
    try:
        response = requests.post(endpoint_url, headers=headers, json=payload, timeout=10)
        return response.status_code == 200
    except:
        return False

def call_dify_dataset_retrieval(query: str, top_k: int = 3, score_threshold: float = 0.5) -> dict:
    """調用 Dify Dataset 檢索 API"""
    
    headers = {
        'Authorization': f'Bearer {DIFY_CONFIG["dataset_key"]}',
        'Content-Type': 'application/json'
    }
    
    # 構建請求載荷 - 使用正確的格式
    payload = {
        'query': query,
        'retrieval_model': {
            'search_method': 'semantic_search',
            'reranking_enable': False,
            'top_k': top_k,
            'score_threshold_enabled': True,
            'score_threshold': score_threshold
        }
    }
    
    try:
        print(f"🔍 Dataset 檢索: {query[:50]}...")
        start_time = time.time()
        
        response = requests.post(
            DIFY_CONFIG['dataset_api_url'],
            headers=headers,
            json=payload,
            timeout=60
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            return {
                'success': True,
                'records': result.get('records', []),
                'response_time': elapsed,
                'query': query
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

def test_dataset_retrieval():
    """測試 Dataset 檢索功能"""
    print("\n" + "="*60)
    print("📚 Dataset 檢索測試")
    print("="*60)
    
    test_queries = [
        "Python 開發工程師",
        "技術部",
        "資料工程師",
        "員工資料",
        "薪資分析"
    ]
    
    results = []
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔸 檢索測試 {i}: {query}")
        print("-" * 40)
        
        result = call_dify_dataset_retrieval(query, top_k=3, score_threshold=0.5)
        results.append(result)
        
        if result['success']:
            print(f"✅ 成功 ({result['response_time']:.1f}s)")
            print(f"📊 檢索到 {len(result['records'])} 筆記錄")
            
            for j, record in enumerate(result['records'][:2], 1):  # 顯示前2筆
                print(f"  📄 記錄 {j} (分數: {record.get('score', 'N/A')}):")
                print(f"     {record.get('content', 'No content')[:100]}...")
                
        else:
            print(f"❌ 失敗: {result['error']}")
        
        time.sleep(1)  # 避免請求過於頻繁
    
    return results

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
    print(f"🔗 Chat API 端點: {DIFY_CONFIG['api_url']}")
    print(f"🔗 Dataset API 端點: {DIFY_CONFIG['dataset_api_url']}")
    print(f"🔑 Chat API Key: {DIFY_CONFIG['api_key'][:20]}...")
    print(f"🔑 Dataset API Key: {DIFY_CONFIG['dataset_key'][:20]}...")
    print("=" * 60)
    
    # 1. 測試 API 連接
    if not test_dify_api_connection():
        print("\n❌ Dify API 連接失敗")
        print("\n🔧 診斷建議:")
        print("1. 檢查 Dify 服務是否正常運行")
        print("2. 驗證 API Key 是否正確和有效")
        print("3. 確認 Dataset ID 是否存在")
        print("4. 檢查網路連接")
        print("\n💡 解決步驟:")
        print("1. 登入 Dify 控制台檢查 Dataset 狀態")
        print("2. 重新生成 API Key")
        print("3. 確認 Dataset 是否已發布")
        return
    
    # 2. Dataset 檢索測試
    retrieval_results = test_dataset_retrieval()
    
    # 3. 基本問題測試（如果有 Chat API）
    basic_results = None
    if DIFY_CONFIG['api_key'].startswith('app-'):
        basic_results = test_basic_questions()
    else:
        print("\n" + "="*60)
        print("⚠️  Chat API 測試（需要 Chat API key）")
        print("="*60)
        print("當前使用的是 Dataset API key，無法測試 Chat 功能")
        print("如需測試 Chat 功能，請提供 app- 開頭的 API key")
    
    # 4. 總結報告
    print("\n" + "="*60)
    print("📊 測試總結報告")
    print("="*60)
    
    if retrieval_results:
        success_count = sum(1 for r in retrieval_results if r['success'])
        print(f"📚 Dataset 檢索測試: {success_count}/{len(retrieval_results)} 成功")
        
        if success_count > 0:
            avg_time = sum(r['response_time'] for r in retrieval_results if r['success']) / success_count
            print(f"⏱️ 平均檢索時間: {avg_time:.1f} 秒")
            
            total_records = sum(len(r['records']) for r in retrieval_results if r['success'])
            print(f"📄 總檢索記錄數: {total_records}")
        else:
            print("❌ 所有 Dataset 檢索測試都失敗了")
            print("💡 建議檢查 Dataset 配置和內容")
    
    if basic_results:
        chat_success_count = sum(1 for r in basic_results if r['success'])
        print(f"💬 Chat API 測試: {chat_success_count}/{len(basic_results)} 成功")
    
    if retrieval_results and any(r['success'] for r in retrieval_results):
        print("\n✅ Dataset API 測試完成！")
        print("💡 Dataset API 可用於知識檢索和 RAG 應用")
    elif basic_results and any(r['success'] for r in basic_results):
        print("\n✅ Chat API 測試完成！")
        print("💡 Chat API 可用於對話功能")
    else:
        print("\n❌ 所有測試都失敗了")
        print("💡 請檢查 Dify 配置和 API 狀態")

if __name__ == "__main__":
    main()