#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dify Chat 測試工具模組
提供批量測試、對話上下文測試和知識庫整合測試功能
"""

import time
import json
from typing import List, Dict, Any, Optional, Callable
from .chat_client import DifyChatClient, create_chat_client


class DifyChatTester:
    """Dify Chat 測試器"""
    
    def __init__(self, chat_client: DifyChatClient = None, delay_between_requests: float = 2.0):
        """
        初始化測試器
        
        Args:
            chat_client: Dify Chat 客戶端（如果不提供會創建默認的）
            delay_between_requests: 請求之間的延遲時間（秒）
        """
        self.client = chat_client or create_chat_client()
        self.delay = delay_between_requests
    
    def batch_test(self, questions: List[str], test_name: str = "批量測試", 
                   user: str = "batch_test_user", maintain_context: bool = False,
                   verbose: bool = True) -> List[Dict[str, Any]]:
        """
        批量測試問題列表
        
        Args:
            questions: 問題列表
            test_name: 測試名稱
            user: 用戶標識
            maintain_context: 是否維持對話上下文
            verbose: 是否顯示詳細日誌
            
        Returns:
            List[Dict]: 測試結果列表
        """
        if verbose:
            print(f"\n{'='*60}")
            print(f"🔍 {test_name}")
            print(f"{'='*60}")
        
        results = []
        conversation_id = ""
        
        for i, question in enumerate(questions, 1):
            if verbose:
                print(f"\n🔸 測試 {i}: {question}")
                print("-" * 50)
            
            # 如果不維持上下文，每次都使用新的對話
            current_conversation_id = conversation_id if maintain_context else ""
            
            result = self.client.chat(question, current_conversation_id, user, verbose=verbose)
            results.append({
                'question': question,
                'test_index': i,
                **result
            })
            
            if result['success']:
                if verbose:
                    print(f"✅ 成功 ({result['response_time']:.1f}s)")
                    answer = result['answer']
                    if len(answer) > 300:
                        print(f"📝 回應: {answer[:300]}...")
                        print("     ... (回應已截斷)")
                    else:
                        print(f"📝 回應: {answer}")
                
                # 保持對話上下文
                if maintain_context and result['conversation_id']:
                    conversation_id = result['conversation_id']
                
                # 如果有 metadata，顯示相關資訊
                if verbose and result.get('metadata'):
                    print(f"📊 Metadata: {json.dumps(result['metadata'], ensure_ascii=False, indent=2)}")
            else:
                if verbose:
                    print(f"❌ 失敗: {result['error']}")
            
            # 延遲以避免請求過於頻繁
            if i < len(questions):
                time.sleep(self.delay)
        
        return results
    
    def context_test(self, conversation_flow: List[str], test_name: str = "對話上下文測試",
                    user: str = "context_test_user", verbose: bool = True) -> List[Dict[str, Any]]:
        """
        測試對話上下文保持
        
        Args:
            conversation_flow: 對話流程（問題列表）
            test_name: 測試名稱
            user: 用戶標識
            verbose: 是否顯示詳細日誌
            
        Returns:
            List[Dict]: 測試結果列表
        """
        if verbose:
            print(f"\n{'='*60}")
            print(f"💬 {test_name}")
            print(f"{'='*60}")
        
        results = []
        conversation_id = ""
        
        for i, question in enumerate(conversation_flow, 1):
            if verbose:
                print(f"\n🔸 對話 {i}: {question}")
                print("-" * 40)
            
            result = self.client.chat(question, conversation_id, user, verbose=False)
            results.append({
                'question': question,
                'conversation_step': i,
                **result
            })
            
            if result['success']:
                if verbose:
                    print(f"✅ 成功 ({result['response_time']:.1f}s)")
                    print(f"📝 回應: {result['answer']}")
                
                # 更新對話 ID
                if result['conversation_id']:
                    conversation_id = result['conversation_id']
                    if verbose:
                        print(f"🔗 對話ID: {conversation_id}")
            else:
                if verbose:
                    print(f"❌ 失敗: {result['error']}")
            
            time.sleep(self.delay)
        
        return results
    
    def knowledge_integration_test(self, knowledge_questions: List[str], 
                                 knowledge_keywords: List[str] = None,
                                 test_name: str = "知識庫整合測試",
                                 user: str = "knowledge_test_user",
                                 verbose: bool = True) -> List[Dict[str, Any]]:
        """
        測試知識庫整合效果
        
        Args:
            knowledge_questions: 知識庫相關問題列表
            knowledge_keywords: 期望在回應中出現的關鍵詞
            test_name: 測試名稱
            user: 用戶標識
            verbose: 是否顯示詳細日誌
            
        Returns:
            List[Dict]: 測試結果列表
        """
        if verbose:
            print(f"\n{'='*60}")
            print(f"📚 {test_name}")
            print(f"{'='*60}")
        
        # 默認關鍵詞
        if knowledge_keywords is None:
            knowledge_keywords = ['python', '工程師', '技術部', '員工', 'know issue', '問題']
        
        results = []
        
        for i, question in enumerate(knowledge_questions, 1):
            if verbose:
                print(f"\n🔸 知識庫測試 {i}: {question}")
                print("-" * 50)
            
            result = self.client.chat(question, user=user, verbose=False)
            
            # 分析知識庫使用情況
            knowledge_used = False
            matched_keywords = []
            
            if result['success']:
                answer_lower = result['answer'].lower()
                matched_keywords = [
                    keyword for keyword in knowledge_keywords 
                    if keyword.lower() in answer_lower
                ]
                knowledge_used = len(matched_keywords) > 0
            
            enhanced_result = {
                'question': question,
                'test_index': i,
                'knowledge_used': knowledge_used,
                'matched_keywords': matched_keywords,
                **result
            }
            
            results.append(enhanced_result)
            
            if result['success']:
                if verbose:
                    print(f"✅ 成功 ({result['response_time']:.1f}s)")
                    print(f"📝 回應長度: {len(result['answer'])} 字符")
                    
                    if knowledge_used:
                        print(f"🎯 ✅ 回應使用了知識庫資訊（關鍵詞: {', '.join(matched_keywords)}）")
                    else:
                        print("⚠️  回應似乎沒有使用知識庫資訊")
                    
                    answer = result['answer']
                    if len(answer) > 200:
                        print(f"📄 完整回應: {answer[:200]}...")
                        print("     ... (回應已截斷)")
                    else:
                        print(f"📄 完整回應: {answer}")
            else:
                if verbose:
                    print(f"❌ 失敗: {result['error']}")
            
            time.sleep(self.delay)
        
        return results
    
    def custom_test(self, test_function: Callable, test_data: Any, 
                   test_name: str = "自定義測試", verbose: bool = True) -> Any:
        """
        執行自定義測試函數
        
        Args:
            test_function: 測試函數
            test_data: 測試數據
            test_name: 測試名稱
            verbose: 是否顯示詳細日誌
            
        Returns:
            Any: 測試結果
        """
        if verbose:
            print(f"\n{'='*60}")
            print(f"🔧 {test_name}")
            print(f"{'='*60}")
        
        try:
            start_time = time.time()
            result = test_function(self.client, test_data)
            elapsed = time.time() - start_time
            
            if verbose:
                print(f"✅ 自定義測試完成 ({elapsed:.1f}s)")
            
            return {
                'success': True,
                'result': result,
                'execution_time': elapsed
            }
        except Exception as e:
            if verbose:
                print(f"❌ 自定義測試失敗: {e}")
            
            return {
                'success': False,
                'error': str(e),
                'execution_time': 0
            }


class TestSuiteBuilder:
    """測試套件建構器"""
    
    def __init__(self):
        self.test_cases = []
    
    def add_batch_test(self, questions: List[str], name: str = "批量測試", 
                      maintain_context: bool = False) -> 'TestSuiteBuilder':
        """添加批量測試案例"""
        self.test_cases.append({
            'type': 'batch',
            'name': name,
            'questions': questions,
            'maintain_context': maintain_context
        })
        return self
    
    def add_context_test(self, conversation_flow: List[str], 
                        name: str = "對話上下文測試") -> 'TestSuiteBuilder':
        """添加上下文測試案例"""
        self.test_cases.append({
            'type': 'context',
            'name': name,
            'conversation_flow': conversation_flow
        })
        return self
    
    def add_knowledge_test(self, knowledge_questions: List[str], 
                          keywords: List[str] = None,
                          name: str = "知識庫整合測試") -> 'TestSuiteBuilder':
        """添加知識庫測試案例"""
        self.test_cases.append({
            'type': 'knowledge',
            'name': name,
            'knowledge_questions': knowledge_questions,
            'keywords': keywords
        })
        return self
    
    def run_all(self, tester: DifyChatTester = None, verbose: bool = True) -> Dict[str, List[Dict[str, Any]]]:
        """執行所有測試案例"""
        if tester is None:
            tester = DifyChatTester()
        
        all_results = {}
        
        for test_case in self.test_cases:
            test_type = test_case['type']
            test_name = test_case['name']
            
            if test_type == 'batch':
                results = tester.batch_test(
                    test_case['questions'], 
                    test_name,
                    maintain_context=test_case['maintain_context'],
                    verbose=verbose
                )
            elif test_type == 'context':
                results = tester.context_test(
                    test_case['conversation_flow'],
                    test_name,
                    verbose=verbose
                )
            elif test_type == 'knowledge':
                results = tester.knowledge_integration_test(
                    test_case['knowledge_questions'],
                    test_case.get('keywords'),
                    test_name,
                    verbose=verbose
                )
            else:
                if verbose:
                    print(f"⚠️  未知測試類型: {test_type}")
                continue
            
            all_results[test_name] = results
        
        return all_results


# 便利函數
def quick_batch_test(questions: List[str], api_url: str = None, api_key: str = None,
                    test_name: str = "快速批量測試", verbose: bool = True) -> List[Dict[str, Any]]:
    """
    快速批量測試功能
    
    Args:
        questions: 問題列表
        api_url: Chat API 端點 URL
        api_key: API Key
        test_name: 測試名稱
        verbose: 是否顯示詳細日誌
        
    Returns:
        List[Dict]: 測試結果列表
    """
    client = create_chat_client(api_url, api_key)
    tester = DifyChatTester(client)
    return tester.batch_test(questions, test_name, verbose=verbose)


def quick_context_test(conversation_flow: List[str], api_url: str = None, api_key: str = None,
                      test_name: str = "快速上下文測試", verbose: bool = True) -> List[Dict[str, Any]]:
    """
    快速對話上下文測試
    
    Args:
        conversation_flow: 對話流程
        api_url: Chat API 端點 URL
        api_key: API Key
        test_name: 測試名稱
        verbose: 是否顯示詳細日誌
        
    Returns:
        List[Dict]: 測試結果列表
    """
    client = create_chat_client(api_url, api_key)
    tester = DifyChatTester(client)
    return tester.context_test(conversation_flow, test_name, verbose=verbose)