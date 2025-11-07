#!/usr/bin/env python
"""
測試 Web Frontend Protocol Assistant Chat API
對比 Dify Studio 和 Web Frontend 的差異
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


def test_web_frontend_chat():
    """測試 Web Frontend Chat API"""
    
    print("=" * 80)
    print("🧪 測試 Web Frontend Protocol Assistant Chat API")
    print("=" * 80)
    
    # Web Frontend 使用的端點（容器內使用 ai-nginx 服務名）
    web_api_url = "http://ai-nginx/api/protocol-guide/chat/"
    
    print(f"\n📡 API 端點: {web_api_url}")
    
    # 模擬前端請求（需要認證）
    # 首先登入獲取 session
    login_url = "http://ai-nginx/api/auth/login/"
    login_data = {
        'username': 'admin',  # 使用你的測試帳號
        'password': 'admin'   # 使用你的測試密碼
    }
    
    session = requests.Session()
    
    print("\n🔐 嘗試登入...")
    try:
        login_response = session.post(login_url, json=login_data, timeout=10)
        
        if login_response.status_code == 200:
            print("✅ 登入成功")
        else:
            print(f"⚠️  登入失敗: {login_response.status_code}")
            print("   嘗試繼續測試（可能需要手動設置 Cookie）...")
    except Exception as e:
        print(f"⚠️  登入請求錯誤: {str(e)}")
        print("   嘗試繼續測試...")
    
    # 發送 Chat 請求
    chat_payload = {
        'message': 'crystaldiskmark 5 的內容有什麼',
        'conversation_id': '',
        'user_id': 1
    }
    
    print(f"\n💬 查詢: {chat_payload['message']}")
    print("\n⏳ 發送請求到 Web Frontend Chat API...")
    
    try:
        response = session.post(
            web_api_url,
            json=chat_payload,
            timeout=60
        )
        
        print(f"\n📊 HTTP 狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print("\n" + "=" * 80)
            print("✅ Web Frontend Chat API 回應成功")
            print("=" * 80)
            
            # 顯示完整的回應結構
            print(f"\n📋 回應結構:")
            print(f"  - success: {data.get('success')}")
            print(f"  - conversation_id: {data.get('conversation_id', 'N/A')}")
            print(f"  - message_id: {data.get('message_id', 'N/A')}")
            print(f"  - response_time: {data.get('response_time', 'N/A')}")
            
            # 顯示 AI 回答
            answer = data.get('answer', '')
            print(f"\n🤖 AI 回答 ({len(answer)} 字):")
            print("-" * 80)
            print(answer)
            print("-" * 80)
            
            # 檢查 metadata
            metadata = data.get('metadata', {})
            retriever_resources = metadata.get('retriever_resources', [])
            
            print(f"\n📚 檢索到的資源數量: {len(retriever_resources)}")
            
            if retriever_resources:
                print("\n✅ 檢索資源詳情:")
                for i, resource in enumerate(retriever_resources, 1):
                    print(f"\n  [{i}] {resource.get('document_name', 'Unknown')}")
                    print(f"      Score: {resource.get('score', 0):.4f}")
                    content_preview = resource.get('content', '')[:150]
                    print(f"      Content: {content_preview}...")
            else:
                print("\n❌ 沒有檢索到任何資源！")
            
            # 分析問題
            print("\n" + "=" * 80)
            print("🔍 問題分析")
            print("=" * 80)
            
            issues = []
            
            # 檢查 1: 答案是否表示找不到內容
            not_found_keywords = ['找不到', '無法找到', '沒有找到', '無法提供', '抱歉', '不確定']
            if any(keyword in answer for keyword in not_found_keywords):
                issues.append("❌ AI 回答表示找不到內容")
            else:
                print("✅ AI 回答看起來正常（未包含「找不到」字樣）")
            
            # 檢查 2: 是否有檢索資源
            if not retriever_resources:
                issues.append("❌ metadata 中沒有 retriever_resources（知識庫未使用）")
            else:
                print(f"✅ 檢索到 {len(retriever_resources)} 條知識庫資源")
            
            # 檢查 3: 檢索資源分數
            if retriever_resources:
                scores = [r.get('score', 0) for r in retriever_resources]
                avg_score = sum(scores) / len(scores)
                print(f"✅ 平均相似度分數: {avg_score:.4f}")
                
                if avg_score < 0.5:
                    issues.append(f"⚠️  平均分數偏低 ({avg_score:.4f})")
            
            # 檢查 4: 是否包含 CrystalDiskMark 5 內容
            if retriever_resources:
                has_crystaldiskmark = any(
                    'crystaldiskmark' in r.get('document_name', '').lower() or
                    'crystaldiskmark' in r.get('content', '').lower()
                    for r in retriever_resources
                )
                if has_crystaldiskmark:
                    print("✅ 檢索資源包含 CrystalDiskMark 相關內容")
                else:
                    issues.append("❌ 檢索資源不包含 CrystalDiskMark 內容")
            
            # 顯示問題摘要
            if issues:
                print("\n⚠️  發現問題:")
                for issue in issues:
                    print(f"  {issue}")
            else:
                print("\n🎉 一切正常！")
            
        elif response.status_code == 403:
            print("\n❌ 權限不足 (403)")
            print("   需要登入或檢查權限設定")
        elif response.status_code == 401:
            print("\n❌ 未認證 (401)")
            print("   需要登入")
        else:
            print(f"\n❌ 請求失敗: {response.status_code}")
            print("\n回應內容:")
            print(response.text)
            
    except requests.exceptions.Timeout:
        print("\n❌ 請求超時（60秒）")
    except Exception as e:
        print(f"\n❌ 錯誤: {str(e)}")
        import traceback
        traceback.print_exc()


def compare_with_dify_direct():
    """對比：直接調用 Dify API"""
    print("\n\n")
    print("=" * 80)
    print("🔬 對比：直接調用 Dify Chat API")
    print("=" * 80)
    
    from library.config.dify_config_manager import get_protocol_guide_config
    config = get_protocol_guide_config()
    
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
    
    print(f"\n📡 直接調用 Dify API: {config.api_url}")
    print(f"💬 查詢: {payload['query']}")
    
    try:
        response = requests.post(
            config.api_url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get('answer', '')
            retriever_resources = data.get('metadata', {}).get('retriever_resources', [])
            
            print(f"\n✅ Dify 直接調用成功")
            print(f"📚 檢索資源: {len(retriever_resources)} 條")
            print(f"🤖 回答長度: {len(answer)} 字")
            
            if retriever_resources:
                print("\n檢索資源:")
                for i, r in enumerate(retriever_resources, 1):
                    print(f"  [{i}] {r.get('document_name')} (Score: {r.get('score'):.4f})")
        else:
            print(f"❌ Dify 直接調用失敗: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Dify 直接調用錯誤: {str(e)}")


if __name__ == '__main__':
    # 測試 1: Web Frontend Chat API
    test_web_frontend_chat()
    
    # 測試 2: 直接調用 Dify（對比）
    compare_with_dify_direct()
    
    print("\n" + "=" * 80)
    print("測試完成")
    print("=" * 80)
