#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dify 文件管理器
提供文件上傳、管理等功能
"""

import os
import requests
import time
from typing import Optional, Dict, Any
from ..data_processing.file_utils import get_file_info, validate_file_for_upload


class DifyFileManager:
    """Dify 文件管理器"""
    
    def __init__(self, base_url: str, api_key: str, session: requests.Session = None):
        """
        初始化文件管理器
        
        Args:
            base_url: Dify 基礎 URL
            api_key: API 密鑰
            session: 可選的 requests session
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = session or requests.Session()
        
        # 設置默認 headers
        self.default_headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
    
    def upload_file(self, file_path: str, user: str = "default_user", 
                   max_size_mb: int = 100, verbose: bool = True) -> Optional[str]:
        """
        上傳文件到 Dify
        
        Args:
            file_path: 文件路徑
            user: 用戶標識
            max_size_mb: 最大文件大小（MB）
            verbose: 是否顯示詳細日誌
            
        Returns:
            Optional[str]: 成功時返回文件 ID，失敗時返回 None
            
        Raises:
            FileNotFoundError: 當文件不存在時
            ValueError: 當文件驗證失敗時
        """
        # 驗證文件
        is_valid, error_msg = validate_file_for_upload(file_path, max_size_mb)
        if not is_valid:
            if verbose:
                print(f"❌ 文件驗證失敗: {error_msg}")
            raise ValueError(error_msg)
        
        file_info = get_file_info(file_path)
        upload_url = f"{self.base_url}/v1/files/upload"
        
        if verbose:
            print(f"📁 準備上傳文件")
            print(f"文件名: {file_info['file_name']}")
            print(f"文件大小: {file_info['file_size'] / 1024:.1f} KB")
            print(f"MIME 類型: {file_info['mime_type']}")
            print(f"上傳到: {upload_url}")
        
        try:
            # 文件上傳時只使用 Authorization header，不設置 Content-Type
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }
            
            with open(file_path, 'rb') as f:
                files = {
                    'file': (file_info['file_name'], f, file_info['mime_type'])
                }
                
                data = {
                    'user': user
                }
                
                if verbose:
                    print(f"📤 上傳到: {upload_url}")
                
                response = requests.post(  # 直接使用 requests.post 而不是 self.session
                    upload_url,
                    files=files,
                    data=data,
                    headers=headers,
                    timeout=60
                )
                
                if verbose:
                    print(f"📥 上傳響應狀態: {response.status_code}")
                
                if response.status_code == 201:
                    upload_data = response.json()
                    file_id = upload_data.get('id')
                    
                    if verbose:
                        print(f"✅ 文件上傳成功！")
                        print(f"文件 ID: {file_id}")
                    
                    return file_id
                else:
                    if verbose:
                        print(f"❌ 文件上傳失敗: HTTP {response.status_code}")
                        try:
                            error_data = response.json()
                            print(f"錯誤詳情: {error_data}")
                        except:
                            print(f"錯誤文本: {response.text[:200]}...")
                    return None
                    
        except Exception as e:
            if verbose:
                print(f"❌ 文件上傳時發生錯誤: {str(e)}")
            raise
    
    def upload_multiple_files(self, file_paths: list, user: str = "default_user", 
                             max_size_mb: int = 100, verbose: bool = True) -> Dict[str, Optional[str]]:
        """
        批量上傳多個文件
        
        Args:
            file_paths: 文件路徑列表
            user: 用戶標識
            max_size_mb: 最大文件大小（MB）
            verbose: 是否顯示詳細日誌
            
        Returns:
            Dict[str, Optional[str]]: 文件路徑到文件ID的映射
        """
        results = {}
        
        if verbose:
            print(f"📁 開始批量上傳 {len(file_paths)} 個文件")
        
        for i, file_path in enumerate(file_paths, 1):
            if verbose:
                print(f"\n📤 上傳文件 {i}/{len(file_paths)}: {os.path.basename(file_path)}")
            
            try:
                file_id = self.upload_file(file_path, user, max_size_mb, verbose=False)
                results[file_path] = file_id
                
                if verbose:
                    if file_id:
                        print(f"✅ 上傳成功: {file_id}")
                    else:
                        print(f"❌ 上傳失敗")
                
                # 避免請求過於頻繁
                if i < len(file_paths):
                    time.sleep(0.5)
                    
            except Exception as e:
                results[file_path] = None
                if verbose:
                    print(f"❌ 上傳異常: {str(e)}")
        
        successful_uploads = sum(1 for file_id in results.values() if file_id)
        
        if verbose:
            print(f"\n📊 批量上傳結果: {successful_uploads}/{len(file_paths)} 成功")
        
        return results
    
    def get_file_info_for_chat(self, file_path: str) -> Dict[str, Any]:
        """
        獲取用於聊天的文件信息
        
        Args:
            file_path: 文件路徑
            
        Returns:
            Dict: 適合聊天使用的文件信息
        """
        file_info = get_file_info(file_path)
        
        return {
            'file_name': file_info['file_name'],
            'file_ext': file_info['file_ext'],
            'content_type': 'image' if file_info['is_image'] else 'document',
            'is_image': file_info['is_image'],
            'mime_type': file_info['mime_type']
        }
    
    def prepare_file_for_analysis(self, file_path: str, user: str = "default_user",
                                 wait_time: int = 2, verbose: bool = True) -> Optional[str]:
        """
        準備文件進行分析（上傳 + 等待處理）
        
        Args:
            file_path: 文件路徑
            user: 用戶標識
            wait_time: 等待文件處理的時間（秒）
            verbose: 是否顯示詳細日誌
            
        Returns:
            Optional[str]: 文件 ID 或 None
        """
        # 上傳文件
        file_id = self.upload_file(file_path, user, verbose=verbose)
        
        if not file_id:
            return None
        
        # 等待文件處理
        if verbose and wait_time > 0:
            print(f"⏳ 等待文件處理 {wait_time} 秒...")
        
        if wait_time > 0:
            time.sleep(wait_time)
        
        return file_id