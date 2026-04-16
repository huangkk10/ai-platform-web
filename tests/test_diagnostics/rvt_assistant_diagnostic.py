#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RVT Assistant 診斷工具
分析 RVT Assistant 聊天功能的 API 問題
"""

import requests
import json
import time
import sys
import os
from pathlib import Path

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from config.config_loader import get_ai_pc_ip
    from tests.test_config import get_rvt_guide_test_config
    CONFIG_AVAILABLE = True
    print("✅ 配置系統載入成功")
except ImportError as e:
    CONFIG_AVAILABLE = False
    print(f"⚠️  配置系統載入失敗: {e}")


class RVTAssistantDiagnostic:
    """RVT Assistant 診斷器"""
    
    def __init__(self):
        if CONFIG_AVAILABLE:
            self.config = get_rvt_guide_test_config()
            self.ai_pc_ip = get_ai_pc_ip()
        else:
            self.ai_pc_ip = "10.253.43.244"
            self.config = {
                'api_url': f'http://{self.ai_pc_ip}/v1/chat-messages',
                'api_key': 'app-Lp4mlfIWHqMWPHTlzF9ywT4F',
                'base_url': f'http://{self.ai_pc_ip}'
            }
        
        print(f"🔧 使用配置:")
        print(f"   AI PC IP: {self.ai_pc_ip}")
        print(f"   API URL: {self.config['api_url']}")
        print(f"   API Key: {self.config['api_key'][:15]}...")
    
    def test_basic_connectivity(self):
        """測試基本連通性"""
        print("\n" + "="*60)
        print("🌐 測試基本連通性")
        print("="*60)
        
        # 測試基本 HTTP 連接
        try:
            print(f"🔍 測試基本連接: {self.config['base_url']}")
            response = requests.get(self.config['base_url'], timeout=10)
            print(f"✅ 基本連接成功: HTTP {response.status_code}")
            return True
        except Exception as e:
            print(f"❌ 基本連接失敗: {e}")
            return False
    
    def test_api_endpoint_availability(self):
        """測試 API 端點可用性"""
        print("\n" + "="*60)
        print("🔗 測試 API 端點可用性")
        print("="*60)
        
        headers = {
            'Authorization': f'Bearer {self.config["api_key"]}',
            'Content-Type': 'application/json'
        }
        
        # 測試 OPTIONS 請求
        try:
            print(f"🔍 測試 OPTIONS: {self.config['api_url']}")
            response = requests.options(self.config['api_url'], headers=headers, timeout=15)
            print(f"📡 OPTIONS 回應: HTTP {response.status_code}")
            
            if response.status_code in [200, 204, 405]:
                print("✅ API 端點可達")
                return True
            else:
                print("❌ API 端點不可達")
                return False
                
        except Exception as e:
            print(f"❌ API 端點測試失敗: {e}")
            return False
    
    def test_rvt_chat_simple(self):
        """測試簡單的 RVT 聊天請求"""
        print("\n" + "="*60)
        print("💬 測試 RVT Chat API")
        print("="*60)
        
        headers = {
            'Authorization': f'Bearer {self.config["api_key"]}',
            'Content-Type': 'application/json'
        }
        
        # 簡單測試問題
        test_questions = [
            "Hello, 這是一個連通性測試。",
            "RVT是什麼？",
            "Jenkins有哪些階段？"
        ]
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n📤 測試問題 {i}: {question}")
            
            payload = {
                'inputs': {},
                'query': question,
                'response_mode': 'blocking',
                'user': f'diagnostic_test_{int(time.time())}'
            }
            
            try:
                start_time = time.time()
                response = requests.post(
                    self.config['api_url'],
                    headers=headers,
                    json=payload,
                    timeout=60  # RVT 可能需要更長時間
                )
                elapsed = time.time() - start_time
                
                print(f"📥 回應狀態: HTTP {response.status_code}")
                print(f"⏱️  響應時間: {elapsed:.2f}s")
                
                if response.status_code == 200:
                    try:
                        result = response.json()
                        answer = result.get('answer', '')
                        conversation_id = result.get('conversation_id', '')
                        
                        print(f"✅ RVT Assistant 回應成功!")
                        print(f"🆔 Conversation ID: {conversation_id}")
                        print(f"🤖 AI 回應: {answer[:200]}{'...' if len(answer) > 200 else ''}")
                        
                        # 檢查回應質量
                        if len(answer.strip()) < 10:
                            print("⚠️  回應內容過短，可能有問題")
                        elif "抱歉" in answer or "無法" in answer or "不知道" in answer:
                            print("⚠️  AI 可能無法找到相關資訊")
                        else:
                            print("✅ 回應質量良好")
                        
                        return True, result
                        
                    except json.JSONDecodeError:
                        print("❌ 回應不是有效的 JSON 格式")
                        print(f"原始回應: {response.text[:500]}")
                        return False, None
                        
                else:
                    print(f"❌ API 請求失敗")
                    try:
                        error_detail = response.json()
                        print(f"錯誤詳情: {json.dumps(error_detail, ensure_ascii=False, indent=2)}")
                    except:
                        print(f"錯誤回應: {response.text[:500]}")
                    return False, None
                    
            except requests.exceptions.Timeout:
                print(f"⏰ 請求超時 (>{60}s)")
                return False, None
            except Exception as e:
                print(f"❌ 請求異常: {e}")
                return False, None
        
        return False, None
    
    def test_rvt_knowledge_base(self):
        """測試 RVT 知識庫相關問題"""
        print("\n" + "="*60)
        print("📚 測試 RVT 知識庫")
        print("="*60)
        
        # 測試 RVT 相關的具體問題
        rvt_questions = [
            "Jenkins 在 RVT 測試中的角色是什麼？",
            "RVT 測試流程有哪些階段？",
            "Ansible 在 RVT 中如何配置？",
            "UART 配置相關問題",
            "MDT 環境準備步驟"
        ]
        
        headers = {
            'Authorization': f'Bearer {self.config["api_key"]}',
            'Content-Type': 'application/json'
        }
        
        successful_responses = 0
        total_questions = len(rvt_questions)
        
        for i, question in enumerate(rvt_questions, 1):
            print(f"\n📋 RVT 問題 {i}/{total_questions}: {question}")
            
            payload = {
                'inputs': {},
                'query': question,
                'response_mode': 'blocking',
                'user': f'rvt_knowledge_test_{int(time.time())}'
            }
            
            try:
                start_time = time.time()
                response = requests.post(
                    self.config['api_url'],
                    headers=headers,
                    json=payload,
                    timeout=90
                )
                elapsed = time.time() - start_time
                
                print(f"   狀態: HTTP {response.status_code} ({elapsed:.1f}s)")
                
                if response.status_code == 200:
                    result = response.json()
                    answer = result.get('answer', '')
                    
                    # 分析回應質量
                    if len(answer.strip()) > 50:
                        if any(keyword in answer for keyword in ['Jenkins', 'RVT', 'Ansible', 'UART', 'MDT', '測試', '階段', '配置']):
                            print(f"   ✅ 找到相關 RVT 資訊")
                            successful_responses += 1
                        else:
                            print(f"   ⚠️  回應不包含 RVT 相關內容")
                    else:
                        print(f"   ❌ 回應過短或空白")
                        
                    print(f"   📄 回應: {answer[:150]}...")
                else:
                    print(f"   ❌ 請求失敗")
                    
            except Exception as e:
                print(f"   ❌ 請求異常: {e}")
                
            # 避免請求過於頻繁
            if i < total_questions:
                time.sleep(2)
        
        print(f"\n📊 知識庫測試結果: {successful_responses}/{total_questions} 個問題成功獲得相關回應")
        return successful_responses / total_questions if total_questions > 0 else 0
    
    def diagnose_api_issues(self):
        """診斷 API 問題"""
        print("\n" + "="*60)
        print("🔍 API 問題診斷")
        print("="*60)
        
        issues = []
        suggestions = []
        
        # 檢查 API Key 格式
        if not self.config['api_key'].startswith('app-'):
            issues.append("❌ API Key 格式不正確（應以 'app-' 開頭）")
            suggestions.append("確認 RVT Guide 應用的 API Key 是否正確")
        
        # 檢查 URL 格式
        if not self.config['api_url'].endswith('/v1/chat-messages'):
            issues.append("❌ API URL 格式可能不正確")
            suggestions.append("確認 API URL 應為 '/v1/chat-messages'")
        
        # 測試網路連通性
        try:
            response = requests.get(self.config['base_url'], timeout=5)
            if response.status_code >= 500:
                issues.append("❌ 服務器內部錯誤")
                suggestions.append("檢查 Dify 服務器狀態")
        except:
            issues.append("❌ 無法連接到服務器")
            suggestions.append("檢查網路連接和服務器可用性")
        
        # 打印診斷結果
        if issues:
            print("發現的問題:")
            for issue in issues:
                print(f"  {issue}")
        
        if suggestions:
            print("\n建議的解決方案:")
            for suggestion in suggestions:
                print(f"  💡 {suggestion}")
        
        if not issues:
            print("✅ 未發現明顯的配置問題")
        
        return issues, suggestions


def main():
    """主診斷函數"""
    print("🔧 RVT Assistant API 診斷工具")
    print("=" * 70)
    
    diagnostic = RVTAssistantDiagnostic()
    
    # 執行診斷步驟
    steps = [
        ("基本連通性測試", diagnostic.test_basic_connectivity),
        ("API 端點可用性測試", diagnostic.test_api_endpoint_availability),
        ("RVT Chat API 測試", diagnostic.test_rvt_chat_simple),
        ("RVT 知識庫測試", diagnostic.test_rvt_knowledge_base),
    ]
    
    results = {}
    
    for step_name, step_func in steps:
        print(f"\n🚀 執行: {step_name}")
        try:
            if step_name == "RVT 知識庫測試":
                results[step_name] = step_func()
            else:
                results[step_name] = step_func()
        except Exception as e:
            print(f"❌ {step_name} 執行失敗: {e}")
            results[step_name] = False
    
    # 診斷 API 問題
    diagnostic.diagnose_api_issues()
    
    # 總結報告
    print("\n" + "="*70)
    print("📊 診斷總結報告")
    print("="*70)
    
    for step_name, result in results.items():
        if isinstance(result, bool):
            status = "✅ 通過" if result else "❌ 失敗"
        elif isinstance(result, float):
            status = f"📊 成功率 {result:.1%}"
        else:
            status = f"📄 結果: {result}"
        
        print(f"{step_name:<25}: {status}")
    
    # 提供具體建議
    print("\n🔍 問題分析:")
    basic_ok = results.get("基本連通性測試", False)
    api_ok = results.get("API 端點可用性測試", False)
    chat_ok = results.get("RVT Chat API 測試", False)
    knowledge_rate = results.get("RVT 知識庫測試", 0)
    
    if not basic_ok:
        print("❌ 基本網路連接失敗")
        print("   💡 檢查網路連接和 IP 地址設定")
    elif not api_ok:
        print("❌ API 端點無法訪問")
        print("   💡 檢查 Dify 服務是否正常運行")
    elif not chat_ok:
        print("❌ Chat API 無法正常工作")
        print("   💡 檢查 API Key 和應用配置")
    elif knowledge_rate < 0.5:
        print("⚠️  RVT Assistant 可以回應，但找不到相關知識")
        print("   💡 這可能是知識庫配置問題:")
        print("      - 檢查 RVT Guide 應用是否有外部知識庫")
        print("      - 確認知識庫中有 RVT 相關文檔")
        print("      - 檢查知識庫向量化是否完成")
        print("      - 考慮重新上傳或索引 RVT 知識文檔")
    else:
        print("✅ RVT Assistant API 工作正常")
        print(f"📈 知識庫命中率: {knowledge_rate:.1%}")
    
    print("\n🌐 Web 前端相關檢查:")
    print("   1. 檢查瀏覽器開發者工具的網路標籤")
    print("   2. 查看是否有 JavaScript 錯誤")
    print("   3. 確認前端使用的 API 端點配置正確")
    print(f"   4. 前端應該調用: {diagnostic.config['api_url']}")
    
    print("\n✅ 診斷完成")


if __name__ == "__main__":
    main()