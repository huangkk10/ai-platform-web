#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Platform API 連通性測試
測試各種 API 端點是否正常工作
"""

import requests
import json
import time
import sys
import os
from urllib.parse import urlparse

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from tests.test_config import get_dify_test_config, get_ai_pc_ip
    from config.config_loader import get_ai_pc_ip_with_env, get_config
    CONFIG_AVAILABLE = True
    print("✅ 配置系統載入成功")
except ImportError as e:
    CONFIG_AVAILABLE = False
    print(f"⚠️  配置系統載入失敗: {e}")
    print("⚠️  使用備用配置")
    def get_ai_pc_ip():
        return "10.253.43.244"
    def get_dify_test_config():
        return {
            'api_url': 'http://10.253.43.244/v1/chat-messages',
            'api_key': 'app-Sql11xracJ71PtZThNJ4ZQQW',
            'base_url': 'http://10.253.43.244'
        }


def test_basic_connectivity():
    """測試基本網路連通性"""
    print("🌐 測試基本網路連通性")
    print("=" * 50)
    
    ai_pc_ip = get_ai_pc_ip()
    print(f"📡 目標 IP: {ai_pc_ip}")
    
    # 測試基本 HTTP 連接
    test_urls = [
        f"http://{ai_pc_ip}",
        f"http://{ai_pc_ip}/health",
        f"http://{ai_pc_ip}/v1",
    ]
    
    for url in test_urls:
        try:
            print(f"\n🔍 測試: {url}")
            start_time = time.time()
            response = requests.get(url, timeout=10)
            elapsed = time.time() - start_time
            
            print(f"✅ 回應: HTTP {response.status_code} ({elapsed:.2f}s)")
            if response.status_code == 200:
                print(f"📄 內容長度: {len(response.text)} 字元")
            elif response.status_code in [404, 405]:
                print("ℹ️  端點存在但方法不支持（正常）")
            else:
                print(f"⚠️  狀態碼: {response.status_code}")
                
        except requests.exceptions.ConnectTimeout:
            print("❌ 連接超時")
        except requests.exceptions.ConnectionError as e:
            print(f"❌ 連接錯誤: {e}")
        except requests.exceptions.Timeout:
            print("❌ 請求超時")
        except Exception as e:
            print(f"❌ 未知錯誤: {e}")


def test_dify_api_endpoints():
    """測試 Dify API 端點"""
    print("\n🤖 測試 Dify API 端點")
    print("=" * 50)
    
    config = get_dify_test_config()
    ai_pc_ip = get_ai_pc_ip()
    
    print(f"🔧 使用配置:")
    print(f"   IP: {ai_pc_ip}")
    print(f"   API URL: {config['api_url']}")
    print(f"   Base URL: {config['base_url']}")
    print(f"   API Key: {config['api_key'][:15]}...")
    
    # 測試各種 Dify 端點
    test_endpoints = [
        {
            'name': 'Chat Messages API',
            'url': config['api_url'],
            'method': 'POST',
            'headers': {
                'Authorization': f'Bearer {config["api_key"]}',
                'Content-Type': 'application/json'
            },
            'data': {
                'inputs': {},
                'query': '你好，這是連通性測試',
                'response_mode': 'blocking',
                'user': 'connectivity_test'
            }
        },
        {
            'name': 'Base URL Check',
            'url': config['base_url'],
            'method': 'GET',
            'headers': {}
        },
        {
            'name': 'API Root',
            'url': f"{config['base_url']}/v1",
            'method': 'GET',
            'headers': {}
        }
    ]
    
    for endpoint in test_endpoints:
        try:
            print(f"\n🔍 測試: {endpoint['name']}")
            print(f"   URL: {endpoint['url']}")
            print(f"   方法: {endpoint['method']}")
            
            start_time = time.time()
            
            if endpoint['method'] == 'POST':
                response = requests.post(
                    endpoint['url'],
                    headers=endpoint['headers'],
                    json=endpoint['data'],
                    timeout=30
                )
            else:
                response = requests.get(
                    endpoint['url'],
                    headers=endpoint['headers'],
                    timeout=10
                )
            
            elapsed = time.time() - start_time
            
            print(f"✅ 回應: HTTP {response.status_code} ({elapsed:.2f}s)")
            
            if response.status_code == 200:
                try:
                    json_response = response.json()
                    print(f"📊 JSON 回應: {json.dumps(json_response, ensure_ascii=False, indent=2)[:200]}...")
                except:
                    print(f"📄 文字回應: {response.text[:200]}...")
            elif response.status_code == 401:
                print("🔐 認證錯誤 - API Key 可能無效")
            elif response.status_code == 404:
                print("🔍 端點不存在")
            elif response.status_code == 422:
                print("📝 請求格式錯誤")
            else:
                print(f"⚠️  HTTP {response.status_code}: {response.text[:100]}")
                
        except requests.exceptions.ConnectTimeout:
            print("❌ 連接超時")
        except requests.exceptions.ConnectionError as e:
            print(f"❌ 連接錯誤: {e}")
        except requests.exceptions.Timeout:
            print("❌ 請求超時")
        except Exception as e:
            print(f"❌ 未知錯誤: {e}")


def test_local_api_endpoints():
    """測試本地 Django API 端點"""
    print("\n🐍 測試本地 Django API 端點")
    print("=" * 50)
    
    local_endpoints = [
        'http://localhost:8000/api/',
        'http://localhost:8000/api/dify/knowledge/retrieval/',
        'http://localhost:8000/api/auth/user/',
        'http://10.10.172.127/api/',  # 從 AI 指令中看到的本地 IP
        'http://10.10.172.127/api/dify/knowledge/retrieval/',
    ]
    
    for url in local_endpoints:
        try:
            print(f"\n🔍 測試本地端點: {url}")
            start_time = time.time()
            
            # 對於需要認證的端點，先嘗試不帶認證的請求
            response = requests.get(url, timeout=5)
            elapsed = time.time() - start_time
            
            print(f"📡 回應: HTTP {response.status_code} ({elapsed:.2f}s)")
            
            if response.status_code == 200:
                print("✅ 端點可訪問")
            elif response.status_code == 403:
                print("🔐 需要認證（正常）")
            elif response.status_code == 404:
                print("🔍 端點不存在")
            elif response.status_code == 405:
                print("📝 方法不支持（可能需要 POST）")
            else:
                print(f"⚠️  狀態: {response.status_code}")
                
        except requests.exceptions.ConnectTimeout:
            print("❌ 連接超時")
        except requests.exceptions.ConnectionError:
            print("❌ 連接失敗（服務可能未運行）")
        except requests.exceptions.Timeout:
            print("❌ 請求超時")
        except Exception as e:
            print(f"❌ 錯誤: {e}")


def test_docker_services():
    """測試 Docker 服務狀態"""
    print("\n🐳 檢查 Docker 服務狀態")
    print("=" * 50)
    
    try:
        import subprocess
        result = subprocess.run(['docker', 'compose', 'ps'], 
                              capture_output=True, text=True, 
                              cwd='/home/user/codes/ai-platform-web')
        
        if result.returncode == 0:
            print("✅ Docker Compose 服務狀態:")
            lines = result.stdout.strip().split('\n')
            for line in lines[1:]:  # 跳過標題行
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 6:
                        service_name = parts[0]
                        status = ' '.join(parts[4:])
                        print(f"   📦 {service_name}: {status}")
        else:
            print(f"❌ 無法獲取 Docker 狀態: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Docker 檢查錯誤: {e}")


def main():
    """主測試函數"""
    print("🚀 AI Platform API 連通性測試")
    print("=" * 60)
    
    if CONFIG_AVAILABLE:
        print("✅ 配置系統可用")
    else:
        print("⚠️  配置系統不可用，使用預設值")
    
    # 1. Docker 服務檢查
    test_docker_services()
    
    # 2. 基本連通性測試
    test_basic_connectivity()
    
    # 3. Dify API 測試
    test_dify_api_endpoints()
    
    # 4. 本地 API 測試
    test_local_api_endpoints()
    
    print("\n" + "=" * 60)
    print("📊 連通性測試完成")
    print("=" * 60)
    print("📋 診斷建議:")
    print("   1. 如果遠端 AI 服務無法連接，檢查網路和防火牆")
    print("   2. 如果 API Key 認證失敗，聯繫管理員更新金鑰") 
    print("   3. 如果本地服務無法連接，檢查 Docker 容器狀態")
    print("   4. 確認所有必要的服務都在運行中")


if __name__ == "__main__":
    main()