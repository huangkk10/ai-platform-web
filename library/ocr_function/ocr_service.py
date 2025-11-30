#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OCR Function 服務模組
=====================

提供便捷的 OCR 圖片文字辨識功能，供其他模組調用。

使用範例：
    from library.ocr_function import ocr_image, ocr_image_from_base64
    
    # 方式 1：從檔案路徑辨識
    result = ocr_image('/path/to/image.jpg')
    if result['success']:
        print(result['text'])
    
    # 方式 2：從 Base64 辨識
    result = ocr_image_from_base64(base64_string, 'image.png')
    if result['success']:
        print(result['text'])
    
    # 方式 3：從 bytes 辨識
    result = ocr_image_from_bytes(image_bytes, 'image.jpg')
"""

import os
import base64
import requests
import logging
from typing import Optional, Dict, Any, Union

from library.config.dify_config_manager import get_ocr_function_config

logger = logging.getLogger(__name__)


class OCRService:
    """OCR 服務類別"""
    
    def __init__(self, user_id: str = 'ocr_service'):
        """
        初始化 OCR 服務
        
        Args:
            user_id: 用於 Dify API 的使用者識別碼
        """
        self.config = get_ocr_function_config()
        self.user_id = user_id
        self.upload_url = self.config.api_url.replace('/chat-messages', '/files/upload')
    
    def _get_mime_type(self, filename: str) -> str:
        """根據檔案名稱取得 MIME 類型"""
        ext = os.path.splitext(filename)[1].lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.webp': 'image/webp'
        }
        return mime_types.get(ext, 'image/jpeg')
    
    def _upload_image(self, image_data: bytes, filename: str) -> Optional[str]:
        """
        上傳圖片到 Dify
        
        Args:
            image_data: 圖片二進位資料
            filename: 檔案名稱
            
        Returns:
            上傳成功返回 file_id，失敗返回 None
        """
        try:
            headers = {'Authorization': f'Bearer {self.config.api_key}'}
            mime_type = self._get_mime_type(filename)
            
            files = {'file': (filename, image_data, mime_type)}
            response = requests.post(
                self.upload_url,
                headers=headers,
                files=files,
                data={'user': self.user_id},
                timeout=30
            )
            
            if response.status_code == 201:
                return response.json().get('id')
            else:
                logger.error(f"圖片上傳失敗: HTTP {response.status_code}, {response.text[:200]}")
                return None
                
        except Exception as e:
            logger.error(f"圖片上傳異常: {e}")
            return None
    
    def _send_ocr_request(
        self, 
        upload_file_id: str, 
        query: str = '請辨識這張圖片中的所有文字內容'
    ) -> Dict[str, Any]:
        """
        發送 OCR 請求
        
        Args:
            upload_file_id: 已上傳的檔案 ID
            query: 查詢提示詞
            
        Returns:
            包含 success, text, raw_response 等欄位的字典
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.config.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'inputs': {
                    'report': {
                        'type': 'image',
                        'transfer_method': 'local_file',
                        'upload_file_id': upload_file_id
                    }
                },
                'query': query,
                'response_mode': 'blocking',
                'user': self.user_id
            }
            
            response = requests.post(
                self.config.api_url,
                headers=headers,
                json=payload,
                timeout=self.config.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'text': data.get('answer', ''),
                    'conversation_id': data.get('conversation_id'),
                    'message_id': data.get('message_id'),
                    'metadata': data.get('metadata', {}),
                    'raw_response': data
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text[:300]}",
                    'text': None
                }
                
        except requests.Timeout:
            return {
                'success': False,
                'error': f"請求超時 (>{self.config.timeout}秒)",
                'text': None
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'text': None
            }
    
    def ocr_from_file(
        self, 
        file_path: str, 
        query: str = '請辨識這張圖片中的所有文字內容'
    ) -> Dict[str, Any]:
        """
        從檔案路徑進行 OCR 辨識
        
        Args:
            file_path: 圖片檔案路徑
            query: 查詢提示詞（可自訂）
            
        Returns:
            {
                'success': bool,
                'text': str or None,      # OCR 辨識結果
                'error': str or None,     # 錯誤訊息
                'conversation_id': str,
                'message_id': str,
                'metadata': dict
            }
        """
        if not os.path.exists(file_path):
            return {
                'success': False,
                'error': f"檔案不存在: {file_path}",
                'text': None
            }
        
        try:
            with open(file_path, 'rb') as f:
                image_data = f.read()
            
            filename = os.path.basename(file_path)
            return self.ocr_from_bytes(image_data, filename, query)
            
        except Exception as e:
            return {
                'success': False,
                'error': f"讀取檔案失敗: {e}",
                'text': None
            }
    
    def ocr_from_bytes(
        self, 
        image_data: bytes, 
        filename: str = 'image.jpg',
        query: str = '請辨識這張圖片中的所有文字內容'
    ) -> Dict[str, Any]:
        """
        從 bytes 資料進行 OCR 辨識
        
        Args:
            image_data: 圖片二進位資料
            filename: 檔案名稱（用於判斷 MIME 類型）
            query: 查詢提示詞
            
        Returns:
            OCR 結果字典
        """
        # 上傳圖片
        upload_file_id = self._upload_image(image_data, filename)
        if not upload_file_id:
            return {
                'success': False,
                'error': '圖片上傳失敗',
                'text': None
            }
        
        # 發送 OCR 請求
        return self._send_ocr_request(upload_file_id, query)
    
    def ocr_from_base64(
        self, 
        base64_string: str, 
        filename: str = 'image.jpg',
        query: str = '請辨識這張圖片中的所有文字內容'
    ) -> Dict[str, Any]:
        """
        從 Base64 字串進行 OCR 辨識
        
        Args:
            base64_string: Base64 編碼的圖片字串
            filename: 檔案名稱
            query: 查詢提示詞
            
        Returns:
            OCR 結果字典
        """
        try:
            # 移除可能的 data URL 前綴
            if ',' in base64_string:
                base64_string = base64_string.split(',')[1]
            
            image_data = base64.b64decode(base64_string)
            return self.ocr_from_bytes(image_data, filename, query)
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Base64 解碼失敗: {e}",
                'text': None
            }


# 建立預設服務實例
_default_service = None

def _get_default_service() -> OCRService:
    """取得預設服務實例（延遲初始化）"""
    global _default_service
    if _default_service is None:
        _default_service = OCRService()
    return _default_service


# ============================================================
# 便利函數（推薦使用）
# ============================================================

def ocr_image(file_path: str, query: str = '請辨識這張圖片中的所有文字內容') -> Dict[str, Any]:
    """
    從檔案路徑進行 OCR 辨識（便利函數）
    
    Args:
        file_path: 圖片檔案路徑
        query: 查詢提示詞
        
    Returns:
        {
            'success': bool,
            'text': str or None,
            'error': str or None,
            ...
        }
    
    Example:
        result = ocr_image('/path/to/image.jpg')
        if result['success']:
            print(result['text'])
    """
    return _get_default_service().ocr_from_file(file_path, query)


def ocr_image_from_bytes(
    image_data: bytes, 
    filename: str = 'image.jpg',
    query: str = '請辨識這張圖片中的所有文字內容'
) -> Dict[str, Any]:
    """
    從 bytes 資料進行 OCR 辨識（便利函數）
    
    Args:
        image_data: 圖片二進位資料
        filename: 檔案名稱
        query: 查詢提示詞
        
    Returns:
        OCR 結果字典
    """
    return _get_default_service().ocr_from_bytes(image_data, filename, query)


def ocr_image_from_base64(
    base64_string: str, 
    filename: str = 'image.jpg',
    query: str = '請辨識這張圖片中的所有文字內容'
) -> Dict[str, Any]:
    """
    從 Base64 字串進行 OCR 辨識（便利函數）
    
    Args:
        base64_string: Base64 編碼的圖片
        filename: 檔案名稱
        query: 查詢提示詞
        
    Returns:
        OCR 結果字典
    """
    return _get_default_service().ocr_from_base64(base64_string, filename, query)
