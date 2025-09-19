#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dify Chat Client 模組
提供 Dify Chat API 的封裝和基本功能
"""

import requests
import json
import time
from typing import Dict, Optional, Any
from ..config.dify_config import get_chat_config
from ..data_processing.file_utils import get_file_info, get_content_type_for_dify, get_default_analysis_query


class DifyChatClient:
    """Dify Chat API 客戶端"""
    
    def __init__(self, api_url: str = None, api_key: str = None, base_url: str = None):
        """
        初始化 Dify Chat 客戶端
        
        Args:
            api_url: Chat API 端點 URL
            api_key: API Key
            base_url: Dify 基礎 URL
        """
        # 使用提供的配置或從配置檔案獲取
        if api_url and api_key:
            self.config = {
                'api_url': api_url,
                'api_key': api_key,
                'base_url': base_url or api_url.split('/v1')[0]
            }
        else:
            self.config = get_chat_config()
        
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.config["api_key"]}',
            'Content-Type': 'application/json'
        })
    
    def test_connection(self, verbose: bool = True) -> bool:
        """
        測試 Dify Chat API 連接
        
        Args:
            verbose: 是否顯示詳細日誌
            
        Returns:
            bool: 連接是否成功
        """
        if verbose:
            print("🔍 測試 Dify Chat API 連接...")
        
        # 簡單的測試請求
        payload = {
            'inputs': {},
            'query': 'Hello, can you respond to this test message?',
            'response_mode': 'blocking',
            'user': 'test_user'
        }
        
        try:
            response = self.session.post(
                self.config['api_url'],
                json=payload,
                timeout=30
            )
            
            if verbose:
                print(f"📊 HTTP 狀態碼: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if verbose:
                    print("✅ Dify Chat API 連接成功")
                    print(f"📝 回應: {result.get('answer', 'No answer')[:100]}...")
                return True
            else:
                if verbose:
                    print(f"❌ API 請求失敗: {response.status_code}")
                    print(f"錯誤詳情: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            if verbose:
                print(f"❌ 網路連接錯誤: {e}")
            return False
        except Exception as e:
            if verbose:
                print(f"❌ 未知錯誤: {e}")
            return False
    
    def chat(self, question: str, conversation_id: str = "", user: str = "default_user", 
             inputs: Dict[str, Any] = None, verbose: bool = True) -> Dict[str, Any]:
        """
        調用 Dify Chat 應用
        
        Args:
            question: 問題內容
            conversation_id: 對話 ID（用於保持上下文）
            user: 用戶標識
            inputs: 額外的輸入參數
            verbose: 是否顯示詳細日誌
            
        Returns:
            Dict: 包含回應結果的字典
        """
        # 構建請求載荷
        payload = {
            'inputs': inputs or {},
            'query': question,
            'response_mode': 'blocking',
            'user': user
        }
        
        # 如果有對話 ID，加入以維持對話上下文
        if conversation_id:
            payload['conversation_id'] = conversation_id
        
        try:
            if verbose:
                print(f"🤖 調用 Dify Chat: {question[:50]}...")
            
            start_time = time.time()
            
            response = self.session.post(
                self.config['api_url'],
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
                    'metadata': result.get('metadata', {}),
                    'usage': result.get('usage', {}),
                    'raw_response': result
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}",
                    'response_time': elapsed,
                    'status_code': response.status_code
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'response_time': 0
            }
    
    def chat_with_file(self, query: str, file_id: str, file_path: str, 
                       conversation_id: str = "", user: str = "default_user",
                       verbose: bool = True) -> Dict[str, Any]:
        """
        使用文件進行聊天
        
        Args:
            query: 查詢內容
            file_id: 文件 ID
            file_path: 文件路徑（用於獲取文件信息）
            conversation_id: 對話 ID
            user: 用戶標識
            verbose: 是否顯示詳細日誌
            
        Returns:
            Dict: 聊天結果
        """
        if verbose:
            print(f"💬📁 使用文件進行聊天")
            print(f"文件 ID: {file_id}")
            print(f"查詢: {query}")
        
        try:
            file_info = get_file_info(file_path)
            content_type = get_content_type_for_dify(file_info['file_ext'])
            
            # 構建聊天數據
            chat_data = {
                "inputs": {
                    "1752737089886": file_id,
                    "report": {
                        "transfer_method": "local_file",
                        "upload_file_id": file_id,
                        "type": content_type
                    },
                    "extension": file_info['file_ext']
                },
                "query": query,
                "response_mode": "blocking",
                "conversation_id": conversation_id,
                "user": user
            }
            
            if verbose:
                print(f"📤 發送文件聊天請求")
                print(f"文件類型: {content_type}")
            
            headers = {
                "Authorization": f"Bearer {self.config['api_key']}",
                "Content-Type": "application/json"
            }
            
            start_time = time.time()
            
            response = self.session.post(
                self.config['api_url'],
                json=chat_data,
                headers=headers,
                timeout=self.config.get('timeout', 60)
            )
            
            elapsed = time.time() - start_time
            
            if verbose:
                print(f"📥 響應狀態: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                
                if 'answer' in response_data:
                    answer = response_data['answer']
                    if verbose:
                        print(f"✅ 文件聊天成功！")
                    
                    return {
                        'success': True,
                        'answer': answer,
                        'conversation_id': response_data.get('conversation_id', ''),
                        'message_id': response_data.get('message_id', ''),
                        'metadata': response_data.get('metadata', {}),
                        'usage': response_data.get('usage', {}),
                        'response_time': elapsed,
                        'raw_response': response_data
                    }
                else:
                    return {
                        'success': False,
                        'error': '響應中沒有 answer 字段',
                        'response_time': elapsed,
                        'raw_response': response_data
                    }
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', f'HTTP {response.status_code}')
                except:
                    error_msg = f"HTTP {response.status_code}: {response.text[:200]}..."
                
                return {
                    'success': False,
                    'error': error_msg,
                    'status_code': response.status_code,
                    'response_time': elapsed
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'response_time': 0
            }
    
    def chat_stream(self, question: str, conversation_id: str = "", user: str = "default_user",
                   inputs: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        調用 Dify Chat 應用（流式回應）
        
        Args:
            question: 問題內容
            conversation_id: 對話 ID
            user: 用戶標識
            inputs: 額外的輸入參數
            
        Returns:
            Dict: 包含流式回應結果的字典
        """
        payload = {
            'inputs': inputs or {},
            'query': question,
            'response_mode': 'streaming',
            'user': user
        }
        
        if conversation_id:
            payload['conversation_id'] = conversation_id
        
        try:
            start_time = time.time()
            
            response = self.session.post(
                self.config['api_url'],
                json=payload,
                timeout=60,
                stream=True
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'stream': response.iter_lines(),
                    'response_time': time.time() - start_time
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}",
                    'response_time': time.time() - start_time
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'response_time': 0
            }
    
    def get_conversations(self, user: str = "default_user", limit: int = 20) -> Dict[str, Any]:
        """
        獲取用戶的對話列表
        
        Args:
            user: 用戶標識
            limit: 最大返回數量
            
        Returns:
            Dict: 對話列表結果
        """
        try:
            # 注意: 這個 API 端點可能需要根據實際 Dify 版本調整
            conversations_url = f"{self.config['base_url']}/v1/conversations"
            
            params = {
                'user': user,
                'limit': limit
            }
            
            response = self.session.get(conversations_url, params=params, timeout=30)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'conversations': response.json()
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_conversation_messages(self, conversation_id: str, user: str = "default_user") -> Dict[str, Any]:
        """
        獲取對話的訊息歷史
        
        Args:
            conversation_id: 對話 ID
            user: 用戶標識
            
        Returns:
            Dict: 訊息歷史結果
        """
        try:
            messages_url = f"{self.config['base_url']}/v1/conversations/{conversation_id}/messages"
            
            params = {'user': user}
            
            response = self.session.get(messages_url, params=params, timeout=30)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'messages': response.json()
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


# 便利函數
def create_chat_client(api_url: str = None, api_key: str = None, base_url: str = None) -> DifyChatClient:
    """
    創建 Dify Chat 客戶端實例
    
    Args:
        api_url: Chat API 端點 URL
        api_key: API Key
        base_url: Dify 基礎 URL
        
    Returns:
        DifyChatClient: Chat 客戶端實例
    """
    return DifyChatClient(api_url, api_key, base_url)


def quick_chat(question: str, api_url: str = None, api_key: str = None, 
               user: str = "quick_user", verbose: bool = True) -> Dict[str, Any]:
    """
    快速聊天功能（不保持上下文）
    
    Args:
        question: 問題內容
        api_url: Chat API 端點 URL
        api_key: API Key
        user: 用戶標識
        verbose: 是否顯示詳細日誌
        
    Returns:
        Dict: 聊天結果
    """
    client = create_chat_client(api_url, api_key)
    return client.chat(question, user=user, verbose=verbose)