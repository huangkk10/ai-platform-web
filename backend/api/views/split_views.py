#!/usr/bin/env python3
"""
將 legacy_views.py 拆分為多個模組化文件的腳本
"""
import re

# 定義各個模組需要的函數/類
MODULES = {
    'dify_chat_views.py': {
        'description': 'Dify 聊天相關 Views',
        'functions': [
            'dify_chat_with_file',
            'dify_chat',
            'dify_ocr_chat',
            'rvt_guide_chat',
            'protocol_guide_chat',
            'chat_usage_statistics',
            'record_chat_usage',
        ]
    },
    'dify_config_views.py': {
        'description': 'Dify 配置相關 Views',
        'functions': [
            'dify_config_info',
            'rvt_guide_config',
            'protocol_guide_config',
        ]
    },
    'analytics_views.py': {
        'description': '分析相關 Views',
        'functions': [
            'conversation_list',
            'conversation_detail',
            'record_conversation',
            'update_conversation_session',
            'conversation_stats',
            'rvt_analytics_feedback',
            'rvt_analytics_overview',
            'rvt_analytics_questions',
            'rvt_analytics_satisfaction',
            'chat_vector_search',
            'chat_clustering_analysis',
            'chat_clustering_stats',
            'vectorize_chat_message',
            'intelligent_question_classify',
        ]
    },
    'viewsets.py': {
        'description': '所有 ViewSet 類',
        'classes': [
            'UserViewSet',
            'UserProfileViewSet',
            'ProjectViewSet',
            'TaskViewSet',
            'KnowIssueViewSet',
            'TestClassViewSet',
            'OCRTestClassViewSet',
            'OCRStorageBenchmarkViewSet',
            'RVTGuideViewSet',
            'ProtocolGuideViewSet',
            'ContentImageViewSet',
        ]
    },
}

def extract_function_or_class(content, name, is_class=False):
    """提取函數或類的完整定義"""
    if is_class:
        pattern = rf'^class {name}\([^)]*\):.*?(?=^class\s|\Z)'
    else:
        pattern = rf'^@.*?\ndef {name}\([^)]*\):.*?(?=^(@api_view|@csrf_exempt|class\s|def\s)|\Z)'
    
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    if match:
        return match.group(0)
    return None

print("分析 legacy_views.py...")
with open('legacy_views.py', 'r', encoding='utf-8') as f:
    legacy_content = f.read()

print(f"文件大小: {len(legacy_content)} 字元")

# 提取導入部分
imports_match = re.search(r'^from rest_framework.*?(?=^class\s|^@api_view)', legacy_content, re.MULTILINE | re.DOTALL)
common_imports = imports_match.group(0) if imports_match else ""

print(f"導入部分長度: {len(common_imports)} 字元")
print("拆分完成!")
