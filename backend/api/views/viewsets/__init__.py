"""
ViewSets Package
重構後的 ViewSet 模組，按業務領域拆分

包含的模組：
- user_viewsets: 用戶和檔案管理
- project_viewsets: 專案和任務管理  
- knowledge_viewsets: 知識庫管理
- ocr_viewsets: OCR 測試管理
- content_viewsets: 內容和圖片管理
- monitoring_views: 系統監控 API
"""

# 用戶相關
from .user_viewsets import UserViewSet, UserProfileViewSet

# 專案相關
from .project_viewsets import ProjectViewSet, TaskViewSet

# 知識庫相關
from .knowledge_viewsets import (
    KnowIssueViewSet,
    RVTGuideViewSet,
    ProtocolGuideViewSet
)

# Protocol Assistant
from .protocol_assistant_viewset import ProtocolAssistantViewSet

# OCR 相關
from .ocr_viewsets import (
    TestClassViewSet,
    OCRTestClassViewSet,
    OCRStorageBenchmarkViewSet
)

# 內容管理
from .content_viewsets import ContentImageViewSet

# Threshold 設定管理
from .threshold_viewsets import SearchThresholdViewSet

# 系統監控
from .monitoring_views import (
    system_logs,
    simple_system_status,
    basic_system_status
)

__all__ = [
    # User
    'UserViewSet',
    'UserProfileViewSet',
    # Project
    'ProjectViewSet',
    'TaskViewSet',
    # Knowledge
    'KnowIssueViewSet',
    'RVTGuideViewSet',
    'ProtocolGuideViewSet',
    # Protocol Assistant
    'ProtocolAssistantViewSet',
    # OCR
    'TestClassViewSet',
    'OCRTestClassViewSet',
    'OCRStorageBenchmarkViewSet',
    # Content
    'ContentImageViewSet',
    # Threshold
    'SearchThresholdViewSet',
    # Monitoring
    'system_logs',
    'simple_system_status',
    'basic_system_status',
]
