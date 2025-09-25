#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dify Know Issue Chat 應用測試腳本 (修正版)
測試與 Dify 平台中配置了外部知識庫的 Chat 應用整合
"""

import requests
import json
import time

# Dify API 配置
DIFY_CONFIG = {
    'api_url': 'http://10.10.172.37/v1/chat-messages',
    'api_key': 'app-Sql11xracJ71PtZThNJ4ZQQW',
    'base_url': 'http://10.10.172.37'
}

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

def call_dify_chunwei(question: str, context_data: str = "", conversation_id: str = "") -> dict:
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
        'user': 'know_issue_test_user'
    }
    
    # 如果有對話 ID，加入以維持對話上下文
    if conversation_id:
        payload['conversation_id'] = conversation_id
    
    try:
        print(f"🤖 調用 Dify: {question[:50]}...")
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

def main():
    """主測試函數"""
    print("🚀 Dify Know Issue Chat 應用整合測試 (修正版)")
    print("=" * 70)
    print(f"🔗 Chat API 端點: {DIFY_CONFIG['api_url']}")
    print(f"🔑 Chat API Key: {DIFY_CONFIG['api_key'][:20]}...")
    print("=" * 70)
    print("📝 說明: dataset-j89ytSyDedYS4sDly2Jnqz0a 是外部知識庫的 ID")
    print("📝 該 ID 用於 Dify 調用我們的外部知識庫 API (Django)")
    print("📝 測試重點: Chat API 是否正確使用外部知識庫")
    print("=" * 70)
    
    # 1. 測試 Chat API 連接
    if not test_dify_chat_api():
        print("\n❌ Dify Chat API 連接失敗，請檢查配置")
        return
    
    # 2. 測試 Know Issue 相關查詢
    print("\n" + "="*70)
    print("📚 Know Issue 外部知識庫整合測試")
    print("="*70)
    
    know_issue_questions = [
        "請幫我查詢技術部的員工資料",
        "誰會 Python 開發？",
        "張小明是做什麼的？",
        "請列出更新人員是 Eric_huang 的 Know Issue",
        "技術部有哪些員工？",
        "請查詢會 React 的工程師"
    ]
    
    results = []
    conversation_id = ""
    
    for i, question in enumerate(know_issue_questions, 1):
        print(f"\n🔸 測試 {i}: {question}")
        print("-" * 60)
        
        result = call_dify_chunwei(question, "", conversation_id)
        results.append(result)
        
        if result['success']:
            print(f"✅ 成功 ({result['response_time']:.1f}s)")
            
            # 檢查是否使用了外部知識庫
            answer = result['answer']
            metadata = result.get('metadata', {})
            
            # 檢查回答是否包含具體資訊（表示使用了知識庫）
            knowledge_indicators = ['張小明', '技術部', 'Python', 'Eric_huang', '員工', 'React', '工程師', '開發']
            has_specific_info = any(keyword in answer for keyword in knowledge_indicators)
            
            if has_specific_info:
                print("🎯 ✅ 回應包含具體知識庫資訊")
            else:
                print("⚠️  回應似乎沒有使用外部知識庫")
            
            print(f"📝 回應: {answer[:300]}...")
            if len(answer) > 300:
                print("     ... (已截斷)")
            
            # 檢查 metadata 中的檢索資源
            if metadata.get('retriever_resources'):
                print(f"🔍 使用了 {len(metadata['retriever_resources'])} 個檢索資源")
                for resource in metadata['retriever_resources']:
                    print(f"   📄 來源: {resource.get('document_name', 'Unknown')}")
            
            # 保持對話上下文
            if result['conversation_id']:
                conversation_id = result['conversation_id']
                
        else:
            print(f"❌ 失敗: {result['error']}")
        
        time.sleep(2)  # 避免請求過於頻繁
    
    # 3. 總結報告
    print("\n" + "="*70)
    print("📊 測試總結報告")
    print("="*70)
    
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
            knowledge_indicators = ['張小明', '技術部', 'Python', 'Eric_huang', '員工', 'React', '工程師', '開發']
            kb_usage = 0
            metadata_usage = 0
            
            for r in successful_results:
                # 檢查回答內容
                if any(keyword in r['answer'] for keyword in knowledge_indicators):
                    kb_usage += 1
                
                # 檢查 metadata
                if r.get('metadata', {}).get('retriever_resources'):
                    metadata_usage += 1
            
            print(f"📚 知識庫使用分析:")
            print(f"   🎯 內容分析: {kb_usage}/{success_count} 次包含具體資訊")
            print(f"   📊 Metadata: {metadata_usage}/{success_count} 次有檢索資源")
            
            if kb_usage > 0 or metadata_usage > 0:
                print("✅ Know Issue 外部知識庫整合成功！")
                if metadata_usage == 0:
                    print("💡 提示: 雖然有具體回答，但 metadata 沒有檢索資源，可能是 LLM 的背景知識")
            else:
                print("⚠️  警告: 沒有檢測到外部知識庫使用")
                print("💡 請檢查 Dify Chat 應用是否正確配置了 Know Issue 外部知識庫")
                print("💡 確認知識庫開關是否已開啟，Score 閾值是否設置合理")
    
    print("\n✅ Know Issue Chat 應用測試完成！")
    print("💡 說明: dataset-j89ytSyDedYS4sDly2Jnqz0a 是外部知識庫 ID")
    print("💡 該 ID 供 Dify 調用我們架設的 Django 外部知識庫 API")
    print("💡 Django API 端點: http://10.10.173.12/api/dify/knowledge")

if __name__ == "__main__":
    main()