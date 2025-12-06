"""
SAF Query Handlers 模組
=======================

提供各種查詢處理器，根據不同的意圖類型執行對應的 SAF API 調用。

處理器列表：
- BaseHandler: 處理器基類
- CustomerHandler: 按客戶查詢專案
- ControllerHandler: 按控制器查詢專案
- ProjectDetailHandler: 查詢專案詳細資訊
- ProjectSummaryHandler: 查詢專案測試摘要（舊版）
- TestSummaryHandler: 查詢專案測試結果統計（Phase 3 新增）
- TestSummaryByFWHandler: 按 FW 版本查詢測試結果（Phase 4 新增）
- StatisticsHandler: 統計查詢（數量、客戶列表、控制器列表）

作者：AI Platform Team
創建日期：2025-12-05
更新日期：2025-12-24（Phase 3: 添加 TestSummaryHandler）
更新日期：2025-12-26（Phase 4: 添加 TestSummaryByFWHandler）
"""

from .base_handler import BaseHandler, QueryResult, QueryStatus
from .customer_handler import CustomerHandler
from .controller_handler import ControllerHandler
from .project_detail_handler import ProjectDetailHandler
from .project_summary_handler import ProjectSummaryHandler
from .test_summary_handler import TestSummaryHandler
from .test_summary_by_fw_handler import TestSummaryByFWHandler
from .statistics_handler import StatisticsHandler

__all__ = [
    'BaseHandler',
    'QueryResult',
    'QueryStatus',
    'CustomerHandler',
    'ControllerHandler',
    'ProjectDetailHandler',
    'ProjectSummaryHandler',
    'TestSummaryHandler',
    'TestSummaryByFWHandler',
    'StatisticsHandler',
]
