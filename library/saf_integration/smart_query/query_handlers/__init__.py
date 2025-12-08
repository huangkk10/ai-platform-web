"""
SAF Query Handlers 模組
=======================

提供各種查詢處理器，根據不同的意圖類型執行對應的 SAF API 調用。

處理器列表：
- BaseHandler: 處理器基類
- CustomerHandler: 按客戶查詢專案
- ControllerHandler: 按控制器查詢專案
- PLHandler: 按專案負責人查詢專案（Phase 7 新增）
- ProjectDetailHandler: 查詢專案詳細資訊
- ProjectSummaryHandler: 查詢專案測試摘要（舊版）
- TestSummaryHandler: 查詢專案測試結果統計（Phase 3 新增）
- TestSummaryByFWHandler: 按 FW 版本查詢測試結果（Phase 4 新增）
- CompareFWVersionsHandler: 比較兩個 FW 版本測試結果（Phase 5.1 新增）
- CompareLatestFWHandler: 自動比較最新兩個 FW 版本（Phase 5.2.1 新增）
- ListFWVersionsHandler: 列出專案可比較的 FW 版本（Phase 5.2.2 新增）
- CompareMultipleFWHandler: 比較多個 FW 版本趨勢（Phase 5.4 新增）
- FWDetailSummaryHandler: FW 詳細統計（完成率、樣本、執行率）（Phase 6.2 新增）
- StatisticsHandler: 統計查詢（數量、客戶列表、控制器列表）

作者：AI Platform Team
創建日期：2025-12-05
更新日期：2025-12-24（Phase 3: 添加 TestSummaryHandler）
更新日期：2025-12-26（Phase 4: 添加 TestSummaryByFWHandler）
更新日期：2025-12-07（Phase 5.1: 添加 CompareFWVersionsHandler）
更新日期：2025-12-07（Phase 5.2: 添加 CompareLatestFWHandler, ListFWVersionsHandler）
更新日期：2025-12-07（Phase 6.2: 添加 FWDetailSummaryHandler）
更新日期：2025-12-08（Phase 5.4: 添加 CompareMultipleFWHandler）
更新日期：2025-12-08（Phase 7: 添加 PLHandler）
"""

from .base_handler import BaseHandler, QueryResult, QueryStatus
from .customer_handler import CustomerHandler
from .controller_handler import ControllerHandler
from .pl_handler import PLHandler
from .project_detail_handler import ProjectDetailHandler
from .project_summary_handler import ProjectSummaryHandler
from .test_summary_handler import TestSummaryHandler
from .test_summary_by_fw_handler import TestSummaryByFWHandler
from .compare_fw_versions_handler import CompareFWVersionsHandler
from .compare_latest_fw_handler import CompareLatestFWHandler
from .list_fw_versions_handler import ListFWVersionsHandler
from .compare_multiple_fw_handler import CompareMultipleFWHandler
from .fw_detail_summary_handler import FWDetailSummaryHandler
from .statistics_handler import StatisticsHandler

__all__ = [
    'BaseHandler',
    'QueryResult',
    'QueryStatus',
    'CustomerHandler',
    'ControllerHandler',
    'PLHandler',
    'ProjectDetailHandler',
    'ProjectSummaryHandler',
    'TestSummaryHandler',
    'TestSummaryByFWHandler',
    'CompareFWVersionsHandler',
    'CompareLatestFWHandler',
    'ListFWVersionsHandler',
    'CompareMultipleFWHandler',
    'FWDetailSummaryHandler',
    'StatisticsHandler',
]

