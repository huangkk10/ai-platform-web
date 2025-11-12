#!/usr/bin/env python
"""
測試 Dify Chat API 是否正確使用知識庫結果
"""
import os
import sys
import django
import requests
import json

# 設定 Django 環境
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from library.config.dify_config_manager import get_protocol_guide_config


def test_dify_chat():
    """測試 Dify Chat API"""
    
    print("=" * 80)
    print("🧪 測試 Dify Protocol Assistant Chat API")
    print("=" * 80)
    
    # 獲取配置
    config = get_protocol_guide_config()
    
    print(f"\n📡 API 端點: {config.api_url}")
    print(f"🔑 API Key: {config.api_key[:20]}...")
    print(f"🏢 應用名稱: {config.app_name}")
    
    # 準備請求
    headers = {
        'Authorization': f'Bearer {config.api_key}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'inputs': {},
        'query': 'crystaldiskmark 5 的內容有什麼',
        'response_mode': 'blocking',
        'user': 'test-user',
        'conversation_id': ''
    }
    
    print(f"\n💬 查詢: {payload['query']}")
    print("\n⏳ 發送請求到 Dify...")
    
    try:
        response = requests.post(
            config.api_url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            print("\n" + "=" * 80)
            print("✅ Dify 回應成功")
            print("=" * 80)
            
            # 顯示回應內容
            answer = data.get('answer', '')
            print(f"\n🤖 AI 回答:\n{answer}")
            
            # 檢查是否有 metadata.retriever_resources
            metadata = data.get('metadata', {})
            retriever_resources = metadata.get('retriever_resources', [])
            
            print(f"\n📚 檢索到的資源數量: {len(retriever_resources)}")
            
            if retriever_resources:
                print("\n檢索資源詳情:")
                for i, resource in enumerate(retriever_resources, 1):
                    print(f"\n  [{i}] {resource.get('document_name', 'Unknown')}")
                    print(f"      Score: {resource.get('score', 0)}")
                    print(f"      Content: {resource.get('content', '')[:100]}...")
            else:
                print("\n⚠️  警告：沒有檢索到任何資源！")
                print("    可能原因：")
                print("    1. Dify APP 的 Score Threshold 設定太高")
                print("    2. 知識庫未正確配置")
                print("    3. 外部知識庫 API 沒有返回結果")
            
            # 檢查答案是否包含「找不到」相關字眼
            if any(keyword in answer for keyword in ['找不到', '無法找到', '沒有找到', '無法提供']):
                print("\n⚠️  警告：AI 回答表示找不到內容！")
                print("    建議檢查：")
                print("    1. Dify 工作室 → Protocol Assistant APP")
                print("    2. 知識庫設定 → Score Threshold（降低至 0.5 或關閉）")
                print("    3. 知識庫設定 → 關閉 Rerank（重排序）")
            else:
                print("\n✅ AI 成功使用了知識庫內容！")
        else:
            print(f"\n❌ 請求失敗: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"\n❌ 錯誤: {str(e)}")


if __name__ == '__main__':
    test_dify_chat()
