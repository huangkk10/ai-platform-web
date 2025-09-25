#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化版 Dify Chat API 測試
專注於測試 Chat 功能
"""

import requests
import json
import time

# Dify Chat API 配置
DIFY_CONFIG = {
    'api_url': 'http://10.10.172.37/v1/chat-messages',
    'api_key': 'app-Sql11xracJ71PtZThNJ4ZQQW',
    'base_url': 'http://10.10.172.37'
}

def call_dify_chat(question: str, conversation_id: str = "", user: str = "test_user") -> dict:
    """調用 Dify Chat API"""
    
    headers = {
        'Authorization': f'Bearer {DIFY_CONFIG["api_key"]}',
        'Content-Type': 'application/json'
    }
    
    # 構建請求載荷
    payload = {
        'inputs': {},
        'query': question,
        'response_mode': 'blocking',
        'user': user
    }
    
    # 如果有對話 ID，加入以維持對話上下文
    if conversation_id:
        payload['conversation_id'] = conversation_id
    
    try:
        print(f"🤖 Chat 問題: {question}")
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
                'conversation_id': result.get('conversation_id', ''),
                'metadata': result.get('metadata', {})
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

def test_chat_functionality():
    """測試 Chat 功能"""
    print("🚀 Dify Chat API 測試")
    print("=" * 50)
    
    # 測試問題
    test_questions = [
        "你好，你是誰？",
        "請幫我查詢技術部的員工資料",
        "誰會 Python 開發？",
        "張小明是做什麼的？",
        "請列出所有員工的技能"
    ]
    
    results = []
    conversation_id = ""
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n🔸 測試 {i}: {question}")
        print("-" * 40)
        
        result = call_dify_chat(question, conversation_id)
        results.append(result)
        
        if result['success']:
            print(f"✅ 成功 ({result['response_time']:.1f}s)")
            print(f"📝 回應: {result['answer'][:200]}...")
            if len(result['answer']) > 200:
                print("     ... (已截斷)")
            
            # 保持對話上下文
            if result['conversation_id']:
                conversation_id = result['conversation_id']
            
            # 檢查是否有檢索資源（知識庫）
            metadata = result.get('metadata', {})
            if metadata.get('retriever_resources'):
                print(f"🔍 使用了 {len(metadata['retriever_resources'])} 個知識庫資源")
                
        else:
            print(f"❌ 失敗: {result['error']}")
        
        time.sleep(2)  # 避免請求過於頻繁
    
    return results

def main():
    """主測試函數"""
    print("🚀 Dify Know Issue Chat 應用測試")
    print("=" * 60)
    print(f"🔗 API 端點: {DIFY_CONFIG['api_url']}")
    print(f"🔑 API Key: {DIFY_CONFIG['api_key'][:20]}...")
    print("=" * 60)
    
    # 執行測試
    results = test_chat_functionality()
    
    # 總結報告
    print("\n" + "="*60)
    print("📊 測試總結報告")
    print("="*60)
    
    if results:
        success_count = sum(1 for r in results if r['success'])
        total_tests = len(results)
        
        print(f"📊 總體測試結果: {success_count}/{total_tests} 成功")
        print(f"📈 成功率: {(success_count/total_tests)*100:.1f}%")
        
        if success_count > 0:
            successful_results = [r for r in results if r['success']]
            avg_time = sum(r['response_time'] for r in successful_results) / len(successful_results)
            print(f"⏱️ 平均回應時間: {avg_time:.1f} 秒")
            
            # 檢查知識庫使用情況
            kb_usage = 0
            for r in successful_results:
                if r.get('metadata', {}).get('retriever_resources'):
                    kb_usage += 1
            
            if kb_usage > 0:
                print(f"📚 知識庫使用: {kb_usage}/{success_count} 次使用了知識庫")
            else:
                print("⚠️  警告: 沒有檢測到知識庫使用")
    
    print("\n✅ Chat API 測試完成！")
    print("💡 如果知識庫沒有被使用，請檢查 Dify 應用配置")

if __name__ == "__main__":
    main()