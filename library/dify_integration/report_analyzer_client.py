#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Report Analyzer 專用聊天客戶端
提供針對 Report Analyzer 應用的專用功能和多格式處理
"""

import time
from typing import Dict, Any, List, Optional
from .chat_client import DifyChatClient
from .file_manager import DifyFileManager
from ..data_processing.file_utils import get_file_info, get_content_type_for_dify, get_default_analysis_query


class ReportAnalyzerClient(DifyChatClient):
    """Report Analyzer 專用聊天客戶端"""
    
    def __init__(self, api_url: str = None, api_key: str = None, base_url: str = None):
        """
        初始化 Report Analyzer 客戶端
        
        Args:
            api_url: Chat API 端點 URL
            api_key: API Key
            base_url: Dify 基礎 URL
        """
        # 如果沒有提供完整配置，使用 Report Analyzer 3 的默認配置
        if not (api_url and api_key):
            from ..config.dify_config_manager import get_report_analyzer_config
            config = get_report_analyzer_config()
            api_url = api_url or config.api_url
            api_key = api_key or config.api_key 
            base_url = base_url or config.base_url
        
        super().__init__(api_url, api_key, base_url)
        self.file_manager = DifyFileManager(self.config['base_url'], self.config['api_key'], self.session)
    
    def test_basic_chat_with_formats(self, query: str, conversation_id: str = "",
                                   user: str = "test_user", verbose: bool = True) -> Dict[str, Any]:
        """
        使用多種格式測試基本聊天功能
        
        Args:
            query: 查詢內容
            conversation_id: 對話 ID
            user: 用戶標識
            verbose: 是否顯示詳細日誌
            
        Returns:
            Dict: 聊天結果
        """
        if verbose:
            print(f"\n💬 測試基本聊天功能")
            print(f"查詢: {query}")
            print(f"⚠️ 注意：此應用需要特定變數，基本聊天可能無法工作")
        
        # 定義多種基本聊天格式
        chat_formats = [
            # 格式 1: 標準格式
            {
                "inputs": {},
                "query": query,
                "response_mode": "blocking",
                "conversation_id": conversation_id,
                "user": user
            },
            # 格式 2: 提供必需變數但使用空值
            {
                "inputs": {
                    "1752737089886": "",
                    "report": "",
                    "extension": ""
                },
                "query": query,
                "response_mode": "blocking",
                "conversation_id": "",
                "user": user
            },
            # 格式 3: 提供虛擬變數值
            {
                "inputs": {
                    "1752737089886": "test_session",
                    "report": "no_file",
                    "extension": "txt"
                },
                "query": query,
                "response_mode": "blocking",
                "conversation_id": "",
                "user": user
            }
        ]
        
        return self._try_multiple_formats(chat_formats, query, verbose)
    
    def analyze_file_with_formats(self, file_id: str, file_path: str, query: str, 
                                 conversation_id: str = "", user: str = "default_user",
                                 verbose: bool = True) -> Dict[str, Any]:
        """
        使用多種格式嘗試文件分析
        
        Args:
            file_id: 文件 ID
            file_path: 文件路徑
            query: 分析查詢
            conversation_id: 對話 ID
            user: 用戶標識
            verbose: 是否顯示詳細日誌
            
        Returns:
            Dict: 分析結果
        """
        file_info = get_file_info(file_path)
        content_type = get_content_type_for_dify(file_info['file_ext'])
        
        if verbose:
            print(f"\n💬📁 測試帶文件的聊天功能")
            print(f"文件 ID: {file_id}")
            print(f"查詢: {query}")
            print(f"文件類型: {content_type}")
        
        # 定義多種聊天格式
        chat_formats = [
            # 格式 1: 標準格式（object format）
            {
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
            },
            # 格式 2: 數組格式（array format）
            {
                "inputs": {
                    "1752737089886": file_id,
                    "report": [{
                        "transfer_method": "local_file",
                        "upload_file_id": file_id,
                        "type": content_type
                    }],
                    "extension": file_info['file_ext']
                },
                "query": query,
                "response_mode": "blocking",
                "conversation_id": conversation_id,
                "user": user
            },
            # 格式 3: 簡化格式（simple format）
            {
                "inputs": {
                    "1752737089886": file_id,
                    "report": file_id,
                    "extension": file_info['file_ext']
                },
                "query": query,
                "response_mode": "blocking",
                "conversation_id": conversation_id,
                "user": user
            },
            # 格式 4: 字符串格式（string format）
            {
                "inputs": {
                    "1752737089886": file_id,
                    "report": f"file_id:{file_id}",
                    "extension": file_info['file_ext']
                },
                "query": query,
                "response_mode": "blocking",
                "conversation_id": conversation_id,
                "user": user
            }
        ]
        
        return self._try_multiple_formats(chat_formats, query, verbose)
    
    def _try_multiple_formats(self, chat_formats: List[Dict], query: str, verbose: bool = True) -> Dict[str, Any]:
        """
        嘗試多種聊天格式
        
        Args:
            chat_formats: 聊天格式列表
            query: 查詢內容
            verbose: 是否顯示詳細日誌
            
        Returns:
            Dict: 聊天結果
        """
        headers = {
            "Authorization": f"Bearer {self.config['api_key']}",
            "Content-Type": "application/json"
        }
        
        for i, chat_data in enumerate(chat_formats, 1):
            if verbose:
                print(f"📤 嘗試格式 {i}")
            
            try:
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
                        if verbose:
                            print(f"✅ 使用格式 {i} 成功！")
                        
                        return {
                            'success': True,
                            'answer': response_data['answer'],
                            'conversation_id': response_data.get('conversation_id', ''),
                            'message_id': response_data.get('message_id', ''),
                            'metadata': response_data.get('metadata', {}),
                            'usage': response_data.get('usage', {}),
                            'format_used': i,
                            'response_time': elapsed,
                            'raw_response': response_data
                        }
                
                # 記錄失敗但繼續嘗試
                if verbose:
                    try:
                        error_data = response.json()
                        print(f"⚠️ 格式 {i} 失敗: {error_data.get('message', 'Unknown error')}")
                    except:
                        print(f"⚠️ 格式 {i} 失敗: {response.text[:100]}...")
                        
            except Exception as e:
                if verbose:
                    print(f"⚠️ 格式 {i} 異常: {str(e)}")
        
        return {
            'success': False,
            'error': '所有聊天格式都失敗',
            'response_time': 0
        }
    
    def upload_and_analyze(self, file_path: str, query: str = None, 
                          user: str = "default_user", wait_time: int = 2,
                          verbose: bool = True) -> Dict[str, Any]:
        """
        上傳文件並進行分析的完整流程
        
        Args:
            file_path: 文件路徑
            query: 分析查詢（可選，會根據文件類型自動生成）
            user: 用戶標識
            wait_time: 等待文件處理的時間（秒）
            verbose: 是否顯示詳細日誌
            
        Returns:
            Dict: 分析結果
        """
        if verbose:
            print(f"\n🔄 開始完整的文件上傳和分析流程")
            print(f"文件路徑: {file_path}")
        
        try:
            # 1. 上傳文件
            file_id = self.file_manager.upload_file(file_path, user, verbose=verbose)
            if not file_id:
                return {
                    'success': False,
                    'error': '文件上傳失敗'
                }
            
            # 2. 等待文件處理
            if wait_time > 0:
                if verbose:
                    print(f"⏳ 等待文件處理 {wait_time} 秒...")
                time.sleep(wait_time)
            
            # 3. 生成默認查詢（如果未提供）
            if not query:
                query = get_default_analysis_query(file_path)
                if verbose:
                    print(f"📝 使用默認查詢: {query}")
            
            # 4. 進行分析
            return self.analyze_file_with_formats(file_id, file_path, query, user=user, verbose=verbose)
            
        except Exception as e:
            return {
                'success': False,
                'error': f'上傳和分析流程錯誤: {str(e)}'
            }
    
    def batch_file_analysis(self, file_paths: List[str], queries: List[str] = None,
                          user: str = "default_user", wait_time: int = 2,
                          verbose: bool = True) -> Dict[str, Dict[str, Any]]:
        """
        批量文件分析
        
        Args:
            file_paths: 文件路徑列表
            queries: 查詢列表（可選，長度應與 file_paths 相同）
            user: 用戶標識
            wait_time: 等待文件處理的時間（秒）
            verbose: 是否顯示詳細日誌
            
        Returns:
            Dict[str, Dict[str, Any]]: 文件路徑到分析結果的映射
        """
        if verbose:
            print(f"\n📊 開始批量文件分析")
            print(f"文件數量: {len(file_paths)}")
        
        results = {}
        
        # 如果沒有提供查詢列表，生成默認查詢
        if not queries:
            queries = [None] * len(file_paths)
        elif len(queries) != len(file_paths):
            raise ValueError("查詢列表長度必須與文件路徑列表長度相同")
        
        for i, (file_path, query) in enumerate(zip(file_paths, queries), 1):
            if verbose:
                print(f"\n📤 處理文件 {i}/{len(file_paths)}: {file_path}")
            
            try:
                result = self.upload_and_analyze(
                    file_path, query, user, wait_time, verbose=False
                )
                results[file_path] = result
                
                if verbose:
                    if result['success']:
                        print(f"✅ 分析成功")
                    else:
                        print(f"❌ 分析失敗: {result.get('error', 'Unknown error')}")
                
                # 避免請求過於頻繁
                if i < len(file_paths):
                    time.sleep(1)
                    
            except Exception as e:
                results[file_path] = {
                    'success': False,
                    'error': str(e)
                }
                if verbose:
                    print(f"❌ 處理異常: {str(e)}")
        
        successful_analyses = sum(1 for result in results.values() if result.get('success', False))
        
        if verbose:
            print(f"\n📊 批量分析結果: {successful_analyses}/{len(file_paths)} 成功")
        
        return results
    
    def get_analysis_report(self, results: Dict[str, Dict[str, Any]], 
                          format_type: str = "summary") -> str:
        """
        生成分析報告
        
        Args:
            results: 分析結果字典
            format_type: 報告格式類型（"summary", "detailed", "json"）
            
        Returns:
            str: 格式化的分析報告
        """
        if format_type == "json":
            import json
            return json.dumps(results, indent=2, ensure_ascii=False)
        
        report_lines = []
        
        if format_type == "detailed":
            report_lines.append("📊 詳細分析報告")
            report_lines.append("=" * 50)
            
            for file_path, result in results.items():
                file_name = file_path.split('/')[-1]
                report_lines.append(f"\n📄 文件: {file_name}")
                report_lines.append("-" * 30)
                
                if result.get('success'):
                    answer = result.get('answer', '')
                    response_time = result.get('response_time', 0)
                    format_used = result.get('format_used', 'Unknown')
                    
                    report_lines.append(f"✅ 狀態: 成功")
                    report_lines.append(f"⏱️ 響應時間: {response_time:.2f}秒")
                    report_lines.append(f"🔧 使用格式: {format_used}")
                    report_lines.append(f"📝 分析結果:")
                    report_lines.append(answer)
                else:
                    error = result.get('error', 'Unknown error')
                    report_lines.append(f"❌ 狀態: 失敗")
                    report_lines.append(f"🚫 錯誤: {error}")
        
        else:  # summary format
            successful_count = sum(1 for result in results.values() if result.get('success', False))
            total_count = len(results)
            
            report_lines.append("📊 分析摘要報告")
            report_lines.append("=" * 30)
            report_lines.append(f"📈 成功率: {successful_count}/{total_count} ({successful_count/total_count*100:.1f}%)")
            
            if successful_count > 0:
                avg_response_time = sum(
                    result.get('response_time', 0) for result in results.values() 
                    if result.get('success', False)
                ) / successful_count
                report_lines.append(f"⏱️ 平均響應時間: {avg_response_time:.2f}秒")
            
            report_lines.append(f"\n📋 文件處理狀態:")
            for file_path, result in results.items():
                file_name = file_path.split('/')[-1]
                status = "✅" if result.get('success') else "❌"
                report_lines.append(f"  {status} {file_name}")
        
        return "\n".join(report_lines)
    
    def _try_multiple_formats(self, chat_formats: List[Dict], query: str, verbose: bool = True) -> Dict[str, Any]:
        """
        嘗試多種聊天格式
        
        Args:
            chat_formats: 聊天格式列表
            query: 查詢內容
            verbose: 是否顯示詳細日誌
            
        Returns:
            Dict: 聊天結果
        """
        headers = {
            "Authorization": f"Bearer {self.config['api_key']}",
            "Content-Type": "application/json"
        }

        last_error_msg = '所有聊天格式都失敗'
        last_status_code = None

        for i, chat_data in enumerate(chat_formats, 1):
            if verbose:
                print(f"📤 嘗試格式 {i}")
            
            try:
                start_time = time.time()
                
                response = self.session.post(
                    self.config['api_url'],
                    json=chat_data,
                    headers=headers,
                    timeout=self.config.get('timeout', 60)
                )
                
                elapsed = time.time() - start_time
                last_status_code = response.status_code
                
                if verbose:
                    print(f"📥 響應狀態: {response.status_code}")
                
                if response.status_code == 200:
                    response_data = response.json()
                    
                    if 'answer' in response_data:
                        if verbose:
                            print(f"✅ 使用格式 {i} 成功！")
                        
                        return {
                            'success': True,
                            'answer': response_data['answer'],
                            'conversation_id': response_data.get('conversation_id', ''),
                            'message_id': response_data.get('message_id', ''),
                            'metadata': response_data.get('metadata', {}),
                            'usage': response_data.get('usage', {}),
                            'format_used': i,
                            'response_time': elapsed,
                            'raw_response': response_data
                        }
                
                # 記錄失敗但繼續嘗試，保存最後一次的真實錯誤訊息
                try:
                    error_data = response.json()
                    dify_msg = error_data.get('message', 'Unknown error')
                    last_error_msg = f'Dify 錯誤 (HTTP {response.status_code}): {dify_msg}'
                    if verbose:
                        print(f"⚠️ 格式 {i} 失敗: {dify_msg}")
                except Exception:
                    last_error_msg = f'Dify 錯誤 (HTTP {response.status_code}): {response.text[:200]}'
                    if verbose:
                        print(f"⚠️ 格式 {i} 失敗: {response.text[:100]}...")
                        
            except Exception as e:
                last_error_msg = f'請求異常: {str(e)}'
                if verbose:
                    print(f"⚠️ 格式 {i} 異常: {str(e)}")
        
        return {
            'success': False,
            'error': last_error_msg,
            'dify_status_code': last_status_code,
            'response_time': 0
        }


# 便利函數
def create_report_analyzer_client(api_url: str = None, api_key: str = None, 
                                 base_url: str = None) -> ReportAnalyzerClient:
    """
    創建 Report Analyzer 客戶端
    
    Args:
        api_url: API URL
        api_key: API 密鑰
        base_url: 基礎 URL
        
    Returns:
        ReportAnalyzerClient: 客戶端實例
    """
    return ReportAnalyzerClient(api_url, api_key, base_url)


def quick_file_analysis(file_path: str, query: str = None, 
                       api_url: str = None, api_key: str = None, 
                       base_url: str = None, user: str = "quick_user",
                       verbose: bool = True) -> Dict[str, Any]:
    """
    快速文件分析
    
    Args:
        file_path: 文件路徑
        query: 分析查詢
        api_url: API URL
        api_key: API 密鑰
        base_url: 基礎 URL
        user: 用戶標識
        verbose: 是否顯示詳細日誌
        
    Returns:
        Dict: 分析結果
    """
    client = create_report_analyzer_client(api_url, api_key, base_url)
    return client.upload_and_analyze(file_path, query, user, verbose=verbose)