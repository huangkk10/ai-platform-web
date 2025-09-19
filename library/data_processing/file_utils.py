#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件處理工具模組
提供文件信息獲取、MIME類型映射等工具函數
"""

import os
from typing import Dict, Tuple


def get_file_info(file_path: str) -> Dict[str, any]:
    """
    獲取文件基本信息
    
    Args:
        file_path: 文件路徑
        
    Returns:
        Dict: 包含文件名、擴展名、MIME類型、是否為圖片等信息
        
    Raises:
        FileNotFoundError: 當文件不存在時
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    file_name = os.path.basename(file_path)
    file_ext = os.path.splitext(file_path)[1].lower().lstrip('.')
    mime_type = get_mime_type(file_ext)
    is_image = is_image_file(file_ext)
    
    return {
        'file_name': file_name,
        'file_ext': file_ext,
        'mime_type': mime_type,
        'is_image': is_image,
        'file_size': os.path.getsize(file_path),
        'file_path': file_path
    }


def get_mime_type(file_ext: str) -> str:
    """
    根據文件擴展名獲取 MIME 類型
    
    Args:
        file_ext: 文件擴展名（不含點號）
        
    Returns:
        str: MIME 類型
    """
    # MIME 類型映射表
    mime_types = {
        # 文本文件
        'txt': 'text/plain',
        'log': 'text/plain',
        'md': 'text/markdown',
        'csv': 'text/csv',
        'tsv': 'text/tab-separated-values',
        
        # 數據格式
        'json': 'application/json',
        'xml': 'application/xml',
        'yaml': 'application/x-yaml',
        'yml': 'application/x-yaml',
        
        # 圖片格式
        'png': 'image/png',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'gif': 'image/gif',
        'bmp': 'image/bmp',
        'webp': 'image/webp',
        'svg': 'image/svg+xml',
        'ico': 'image/x-icon',
        
        # 文檔格式
        'pdf': 'application/pdf',
        'doc': 'application/msword',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'xls': 'application/vnd.ms-excel',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'ppt': 'application/vnd.ms-powerpoint',
        'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        
        # 壓縮格式
        'zip': 'application/zip',
        'rar': 'application/x-rar-compressed',
        '7z': 'application/x-7z-compressed',
        'tar': 'application/x-tar',
        'gz': 'application/gzip',
        
        # 程式碼文件
        'py': 'text/x-python',
        'js': 'text/javascript',
        'html': 'text/html',
        'css': 'text/css',
        'java': 'text/x-java-source',
        'cpp': 'text/x-c++src',
        'c': 'text/x-csrc',
        'php': 'text/x-php',
        'rb': 'text/x-ruby',
        'go': 'text/x-go',
        'rs': 'text/x-rust',
        'ts': 'text/typescript'
    }
    
    return mime_types.get(file_ext.lower(), 'application/octet-stream')


def is_image_file(file_ext: str) -> bool:
    """
    判斷是否為圖片文件
    
    Args:
        file_ext: 文件擴展名（不含點號）
        
    Returns:
        bool: 是否為圖片文件
    """
    image_extensions = [
        'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'svg', 'ico',
        'tiff', 'tif', 'psd', 'raw', 'heic', 'avif'
    ]
    return file_ext.lower() in image_extensions


def is_document_file(file_ext: str) -> bool:
    """
    判斷是否為文檔文件
    
    Args:
        file_ext: 文件擴展名（不含點號）
        
    Returns:
        bool: 是否為文檔文件
    """
    document_extensions = [
        'txt', 'md', 'doc', 'docx', 'pdf', 'rtf', 'odt',
        'xls', 'xlsx', 'ppt', 'pptx', 'csv', 'tsv'
    ]
    return file_ext.lower() in document_extensions


def get_content_type_for_dify(file_ext: str) -> str:
    """
    根據文件擴展名返回適合 Dify 的內容類型
    
    Args:
        file_ext: 文件擴展名（不含點號）
        
    Returns:
        str: "image" 或 "document"
    """
    return "image" if is_image_file(file_ext) else "document"


def get_default_analysis_query(file_path: str) -> str:
    """
    根據文件類型生成默認的分析查詢
    
    Args:
        file_path: 文件路徑
        
    Returns:
        str: 適合該文件類型的分析查詢
    """
    file_info = get_file_info(file_path)
    
    if file_info['is_image']:
        return "請分析這張圖片的內容，描述你看到的信息"
    elif file_info['file_ext'] in ['log', 'txt']:
        return "請分析這個日誌/文本文件的內容，並提供摘要和關鍵信息"
    elif file_info['file_ext'] == 'csv':
        return "請分析這個 CSV 文件的數據結構和內容摘要"
    elif file_info['file_ext'] == 'json':
        return "請分析這個 JSON 文件的結構和內容"
    elif file_info['file_ext'] == 'pdf':
        return "請提取並分析這個 PDF 文件的主要內容"
    else:
        return "請分析這個文件的內容，並提供摘要"


def validate_file_for_upload(file_path: str, max_size_mb: int = 100) -> Tuple[bool, str]:
    """
    驗證文件是否適合上傳
    
    Args:
        file_path: 文件路徑
        max_size_mb: 最大文件大小（MB）
        
    Returns:
        Tuple[bool, str]: (是否有效, 錯誤信息或空字符串)
    """
    if not os.path.exists(file_path):
        return False, f"文件不存在: {file_path}"
    
    if not os.path.isfile(file_path):
        return False, f"路徑不是文件: {file_path}"
    
    file_size = os.path.getsize(file_path)
    max_size_bytes = max_size_mb * 1024 * 1024
    
    if file_size > max_size_bytes:
        return False, f"文件太大: {file_size / (1024 * 1024):.1f}MB (最大: {max_size_mb}MB)"
    
    if file_size == 0:
        return False, "文件為空"
    
    return True, ""


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小顯示
    
    Args:
        size_bytes: 文件大小（字節）
        
    Returns:
        str: 格式化的文件大小字符串
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def get_supported_file_extensions() -> Dict[str, list]:
    """
    獲取支援的文件擴展名列表
    
    Returns:
        Dict: 按類型分組的支援文件擴展名
    """
    return {
        'images': ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'svg', 'ico'],
        'documents': ['txt', 'md', 'doc', 'docx', 'pdf', 'rtf', 'odt'],
        'data': ['csv', 'tsv', 'json', 'xml', 'yaml', 'yml'],
        'code': ['py', 'js', 'html', 'css', 'java', 'cpp', 'c', 'php', 'rb', 'go', 'ts'],
        'logs': ['log', 'out', 'err'],
        'archives': ['zip', 'rar', '7z', 'tar', 'gz']
    }