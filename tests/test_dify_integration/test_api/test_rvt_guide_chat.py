#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 RVT_GUIDE 聊天功能
使用配置中的設定進行基本聊天測試
"""

import sys
import os
import requests
import json
import time
from datetime import datetime

# 添加項目根目錄到 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from library.config.dify_app_configs import get_rvt_guide_config


class RVTGuideChatTest:
    """RVT Guide 聊天測試器"""
    
    def __init__(self):
        """初始化"""
        self.config = get_rvt_guide_config()
        self.session = requests.Session()
        self.conversation_id = ""
        
        print(f"🔧 初始化 RVT Guide 聊天測試")
        print(f"工作室: {self.config['workspace']}")
        print(f"應用名稱: {self.config['app_name']}")
        print(f"API URL: {self.config['api_url']}")
        print(f"Base URL: {self.config['base_url']}")
        print(f"API Key: {self.config['api_key'][:12]}...")
        print(f"功能: {', '.join(self.config['features'])}")
        print(f"描述: {self.config['description']}")
    
    def test_basic_chat(self, query):
        """測試基本聊天功能"""
        print(f"\n💬 測試基本聊天功能")
        print(f"查詢: {query}")
        
        try:
            headers = {
                "Authorization": f"Bearer {self.config['api_key']}",
                "Content-Type": "application/json"
            }
            
            # RVT Guide 聊天格式
            chat_data = {
                "inputs": {},
                "query": query,
                "response_mode": "blocking",
                "conversation_id": self.conversation_id if self.conversation_id else "",
                "user": "test_user"
            }
            
            print(f"📤 發送聊天請求: {self.config['api_url']}")
            
            response = self.session.post(
                self.config['api_url'],
                json=chat_data,
                headers=headers,
                timeout=self.config['timeout']
            )
            
            print(f"📥 響應狀態: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                
                # 更新會話 ID
                if 'conversation_id' in response_data:
                    self.conversation_id = response_data['conversation_id']
                    print(f"🔄 會話 ID: {self.conversation_id}")
                
                if 'answer' in response_data:
                    answer = response_data['answer']
                    print(f"✅ 聊天成功！")
                    print(f"🤖 AI 回答:")
                    print("="*50)
                    print(answer)
                    print("="*50)
                    return answer
                else:
                    print(f"⚠️ 響應中沒有 answer 字段")
                    print(f"響應內容: {response_data}")
                    return None
            else:
                try:
                    error_data = response.json()
                    print(f"❌ 聊天失敗: {error_data.get('message', 'Unknown error')}")
                    print(f"錯誤詳情: {error_data}")
                except:
                    print(f"❌ 聊天失敗: {response.text[:200]}...")
                return None
                
        except Exception as e:
            print(f"❌ 聊天測試時發生錯誤: {str(e)}")
            return None
    
    def test_rvt_specific_questions(self):
        """測試 RVT 相關的特定問題"""
        print(f"\n🔍 測試 RVT 相關的特定問題")
        
        rvt_questions = [
            "什麼是 RVT？",
            "RVT 的主要功能有哪些？",
            "如何進行 RVT 測試？",
            "RVT 測試的流程是什麼？",
            "RVT 常見問題有哪些？",
            "如何解決 RVT 測試中的問題？",
            "RVT 測試需要注意什麼事項？",
            "RVT 工具的使用方法",
        ]
        
        results = []
        for i, question in enumerate(rvt_questions, 1):
            print(f"\n📝 問題 {i}: {question}")
            result = self.test_basic_chat(question)
            results.append({
                'question': question,
                'answer': result,
                'success': result is not None
            })
            
            # 短暫延遲避免請求過於頻繁
            if i < len(rvt_questions):
                time.sleep(1)
        
        return results
    
    def test_conversation_flow(self):
        """測試對話流程（多輪對話）"""
        print(f"\n💬🔄 測試對話流程（多輪對話）")
        
        conversation_steps = [
            "你好，我想了解 RVT 測試",
            "能詳細說明 RVT 測試的步驟嗎？",
            "如果測試失敗了該怎麼辦？",
            "有什麼最佳實踐建議嗎？",
            "謝謝你的幫助"
        ]
        
        conversation_results = []
        
        for i, step in enumerate(conversation_steps, 1):
            print(f"\n🗣️ 對話步驟 {i}: {step}")
            result = self.test_basic_chat(step)
            conversation_results.append({
                'step': i,
                'query': step,
                'answer': result,
                'success': result is not None,
                'conversation_id': self.conversation_id
            })
            
            # 短暫延遲避免請求過於頻繁
            if i < len(conversation_steps):
                time.sleep(1)
        
        return conversation_results
    
    def test_configuration_validation(self):
        """測試配置驗證"""
        print(f"\n🔧 測試配置驗證")
        
        try:
            from library.config.dify_app_configs import validate_rvt_guide_config
            
            is_valid = validate_rvt_guide_config()
            print(f"✅ 配置驗證成功: {is_valid}")
            return True
            
        except Exception as e:
            print(f"❌ 配置驗證失敗: {str(e)}")
            return False
    
    def test_client_creation(self):
        """測試客戶端創建"""
        print(f"\n🤖 測試客戶端創建")
        
        try:
            from library.config.dify_app_configs import create_rvt_guide_chat_client
            
            client = create_rvt_guide_chat_client()
            print(f"✅ 客戶端創建成功: {type(client)}")
            return client
            
        except Exception as e:
            print(f"❌ 客戶端創建失敗: {str(e)}")
            return None
    
    def save_test_results(self, results, filename_suffix=""):
        """保存測試結果到 JSON 文件"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"rvt_guide_test_results_{timestamp}{filename_suffix}.json"
            filepath = os.path.join(os.path.dirname(__file__), filename)
            
            test_summary = {
                'timestamp': timestamp,
                'config': {
                    'workspace': self.config['workspace'],
                    'app_name': self.config['app_name'],
                    'api_url': self.config['api_url'],
                    'features': self.config['features']
                },
                'results': results
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(test_summary, f, ensure_ascii=False, indent=2)
            
            print(f"📄 測試結果已保存到: {filename}")
            return filepath
            
        except Exception as e:
            print(f"❌ 保存測試結果失敗: {str(e)}")
            return None
    
    def run_complete_test(self):
        """運行完整測試"""
        print(f"\n{'='*60}")
        print(f"🧪 開始 RVT Guide 完整聊天測試")
        print(f"{'='*60}")
        print(f"時間: {datetime.now()}")
        
        all_results = {
            'basic_test': {},
            'rvt_specific_tests': [],
            'conversation_flow': [],
            'config_validation': False,
            'client_creation': False
        }
        
        # 測試 1: 配置驗證
        print(f"\n🧪 測試 1: 配置驗證")
        all_results['config_validation'] = self.test_configuration_validation()
        
        # 測試 2: 客戶端創建
        print(f"\n🧪 測試 2: 客戶端創建")
        client = self.test_client_creation()
        all_results['client_creation'] = client is not None
        
        # 測試 3: 基本聊天
        print(f"\n🧪 測試 3: 基本聊天功能")
        basic_result = self.test_basic_chat("你好，我是測試用戶，請介紹一下你的功能")
        all_results['basic_test'] = {
            'query': "你好，我是測試用戶，請介紹一下你的功能",
            'answer': basic_result,
            'success': basic_result is not None
        }
        
        # 測試 4: RVT 特定問題
        print(f"\n🧪 測試 4: RVT 特定問題")
        all_results['rvt_specific_tests'] = self.test_rvt_specific_questions()
        
        # 測試 5: 對話流程
        print(f"\n🧪 測試 5: 對話流程測試")
        # 重置對話 ID 開始新對話
        self.conversation_id = ""
        all_results['conversation_flow'] = self.test_conversation_flow()
        
        # 測試總結
        print(f"\n{'='*60}")
        print(f"🎯 測試總結")
        print(f"{'='*60}")
        
        print(f"✅ 配置驗證：{'成功' if all_results['config_validation'] else '失敗'}")
        print(f"✅ 客戶端創建：{'成功' if all_results['client_creation'] else '失敗'}")
        print(f"✅ 基本聊天：{'成功' if all_results['basic_test']['success'] else '失敗'}")
        
        rvt_success_count = sum(1 for test in all_results['rvt_specific_tests'] if test['success'])
        rvt_total_count = len(all_results['rvt_specific_tests'])
        print(f"✅ RVT 特定問題：{rvt_success_count}/{rvt_total_count} 成功")
        
        conv_success_count = sum(1 for step in all_results['conversation_flow'] if step['success'])
        conv_total_count = len(all_results['conversation_flow'])
        print(f"✅ 對話流程：{conv_success_count}/{conv_total_count} 步驟成功")
        
        # 保存測試結果
        result_file = self.save_test_results(all_results)
        
        # 總體評估
        total_tests = 5
        passed_tests = sum([
            all_results['config_validation'],
            all_results['client_creation'],
            all_results['basic_test']['success'],
            rvt_success_count >= rvt_total_count * 0.7,  # 70% RVT 問題成功
            conv_success_count >= conv_total_count * 0.7   # 70% 對話步驟成功
        ])
        
        print(f"\n📊 總體評估：{passed_tests}/{total_tests} 項測試通過")
        
        if passed_tests >= 4:
            print(f"🎉 RVT Guide 工作正常！")
        elif passed_tests >= 2:
            print(f"⚠️ RVT Guide 部分功能正常，需要檢查配置")
        else:
            print(f"❌ RVT Guide 存在嚴重問題，需要修復")
        
        print(f"\n測試完成！")
        if result_file:
            print(f"詳細結果請查看: {result_file}")
        
        return all_results


def main():
    """主程式"""
    print("🧪 RVT Guide 聊天功能測試")
    print("="*60)
    
    # 初始化測試器
    tester = RVTGuideChatTest()
    
    # 運行完整測試
    results = tester.run_complete_test()
    
    # 快速功能演示（如果基本聊天可用）
    if results['basic_test']['success']:
        print(f"\n{'='*60}")
        print(f"🎮 快速功能演示")
        print(f"{'='*60}")
        
        demo_questions = [
            "RVT 測試的主要步驟有哪些？",
            "如何排查 RVT 測試問題？"
        ]
        
        for question in demo_questions:
            print(f"\n❓ 示例問題: {question}")
            answer = tester.test_basic_chat(question)
            if not answer:
                print("⚠️ 演示問題失敗")


if __name__ == "__main__":
    main()