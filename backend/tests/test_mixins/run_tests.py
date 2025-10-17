"""
運行 Mixin 單元測試

執行所有 Mixin 相關的單元測試
"""
import sys
import os

# 添加 backend 到 Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))

# 設置 Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')

import django
django.setup()

import pytest

if __name__ == '__main__':
    # 運行所有 Mixin 測試
    exit_code = pytest.main([
        os.path.dirname(__file__),
        '-v',
        '--tb=short',
        '--color=yes',
        '-ra'
    ])
    
    sys.exit(exit_code)
