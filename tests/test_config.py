#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試配置輔助工具
為測試文件提供統一的配置管理
"""

import os
import sys
from pathlib import Path

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from config.config_loader import get_ai_pc_ip_with_env
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    def get_ai_pc_ip_with_env():
        return os.getenv('AI_PC_IP', '10.10.172.5')


def get_dify_test_config():
    """
    獲取 Dify 測試配置
    
    Returns:
        dict: 測試配置
    """
    ai_pc_ip = get_ai_pc_ip_with_env()
    
    return {
        'api_url': f'http://{ai_pc_ip}/v1/chat-messages',
        'api_key': os.getenv('DIFY_API_KEY', 'app-Sql11xracJ71PtZThNJ4ZQQW'),  # 預設使用 Protocol
        'base_url': f'http://{ai_pc_ip}',
        'timeout': int(os.getenv('DIFY_TIMEOUT', '60')),
        'dataset_api_url': f'http://{ai_pc_ip}/v1/datasets',
        'chat_api_url': f'http://{ai_pc_ip}/v1/chat-messages',
    }


def get_report_analyzer_test_config():
    """
    獲取 Report Analyzer 測試配置
    
    Returns:
        dict: 測試配置
    """
    ai_pc_ip = get_ai_pc_ip_with_env()
    
    return {
        'api_url': f'http://{ai_pc_ip}/v1/chat-messages',
        'api_key': os.getenv('DIFY_REPORT_ANALYZER_API_KEY', 'app-DmCCl8KwXhhjND0WbEf0ULlR'),
        'base_url': f'http://{ai_pc_ip}',
        'timeout': int(os.getenv('DIFY_TIMEOUT', '120')),
    }


def get_rvt_guide_test_config():
    """
    獲取 RVT Guide 測試配置
    
    Returns:
        dict: 測試配置
    """
    ai_pc_ip = get_ai_pc_ip_with_env()
    
    return {
        'api_url': f'http://{ai_pc_ip}/v1/chat-messages',
        'api_key': os.getenv('DIFY_RVT_GUIDE_API_KEY', 'app-Lp4mlfIWHqMWPHTlzF9ywT4F'),
        'base_url': f'http://{ai_pc_ip}',
        'timeout': int(os.getenv('DIFY_TIMEOUT', '60')),
    }


def get_ai_pc_ip():
    """
    獲取 AI PC IP 地址的便利函數（用於測試）
    
    Returns:
        str: IP 地址
    """
    return get_ai_pc_ip_with_env()


def get_dataset_api_config():
    """
    獲取 Dataset API 配置
    
    Returns:
        dict: Dataset API 配置
    """
    ai_pc_ip = get_ai_pc_ip_with_env()
    
    return {
        'base_url': f'http://{ai_pc_ip}',
        'dataset_api_url': f'http://{ai_pc_ip}/v1/datasets',
        'api_key': os.getenv('DIFY_DATASET_API_KEY', 'dataset-aPo8HCQTrg1VvCZsNzwPGT0H'),
        'timeout': int(os.getenv('DIFY_TIMEOUT', '60')),
    }


def print_config_info():
    """打印當前配置信息"""
    print("=== 測試配置信息 ===")
    print(f"AI PC IP: {get_ai_pc_ip()}")
    print(f"配置載入器可用: {'✅' if CONFIG_AVAILABLE else '❌'}")
    print(f"Dify 測試配置: {get_dify_test_config()}")
    print("==================")


if __name__ == "__main__":
    print_config_info()