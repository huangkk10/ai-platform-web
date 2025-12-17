"""
SAF 意圖類型定義
================

定義 SAF 智能查詢系統支援的所有意圖類型。

作者：AI Platform Team
創建日期：2025-12-05
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List


class IntentType(Enum):
    """SAF 查詢意圖類型枚舉"""
    
    # 按客戶查詢專案
    QUERY_PROJECTS_BY_CUSTOMER = "query_projects_by_customer"
    
    # 按控制器查詢專案
    QUERY_PROJECTS_BY_CONTROLLER = "query_projects_by_controller"
    
    # 查詢專案詳細資訊
    QUERY_PROJECT_DETAIL = "query_project_detail"
    
    # 查詢專案測試摘要（舊版，保留向後相容）
    QUERY_PROJECT_SUMMARY = "query_project_summary"
    
    # 查詢專案測試結果摘要（新版 - 按類別和容量統計）
    QUERY_PROJECT_TEST_SUMMARY = "query_project_test_summary"
    
    # 查詢專案特定類別的測試結果
    QUERY_PROJECT_TEST_BY_CATEGORY = "query_project_test_by_category"
    
    # 查詢專案特定容量的測試結果
    QUERY_PROJECT_TEST_BY_CAPACITY = "query_project_test_by_capacity"
    
    # 🆕 Phase 4: 按 FW 版本查詢測試結果
    QUERY_PROJECT_TEST_SUMMARY_BY_FW = "query_project_test_summary_by_fw"
    
    # 🆕 Phase 5.1: 比較兩個指定的 FW 版本
    COMPARE_FW_VERSIONS = "compare_fw_versions"
    
    # 🆕 Phase 5.2: 智能版本選擇
    COMPARE_LATEST_FW = "compare_latest_fw"           # 自動比較最新兩版本
    LIST_FW_VERSIONS = "list_fw_versions"             # 列出可比較的 FW 版本
    
    # 🆕 Phase 5.4: 多版本趨勢分析
    COMPARE_MULTIPLE_FW = "compare_multiple_fw"       # 比較多個 FW 版本（3個或以上）
    
    # 🆕 Phase 6.2: 查詢 FW 詳細統計（使用 /firmware-summary API）
    QUERY_FW_DETAIL_SUMMARY = "query_fw_detail_summary"
    
    # 🆕 Phase 7: 按專案負責人 (PL) 查詢專案
    QUERY_PROJECTS_BY_PL = "query_projects_by_pl"
    
    # 🆕 Phase 7: 列出所有專案負責人 (PL)
    LIST_ALL_PLS = "list_all_pls"
    
    # 🆕 Phase 8: 按日期/月份查詢專案
    QUERY_PROJECTS_BY_DATE = "query_projects_by_date"     # 查詢指定日期的專案
    QUERY_PROJECTS_BY_MONTH = "query_projects_by_month"   # 查詢指定月份的專案
    
    # 🆕 Phase 9: Sub Version (容量版本) 查詢
    LIST_SUB_VERSIONS = "list_sub_versions"               # 列出專案所有 Sub Version
    LIST_FW_BY_SUB_VERSION = "list_fw_by_sub_version"     # 列出特定 Sub Version 的 FW 版本
    
    # 🆕 Phase 10: 跨專案測試類別搜尋
    QUERY_PROJECTS_BY_TEST_CATEGORY = "query_projects_by_test_category"  # 哪些案子有測試過 XX？
    
    # 🆕 Phase 11: 專案 FW 測試類別查詢
    QUERY_PROJECT_FW_TEST_CATEGORIES = "query_project_fw_test_categories"  # 專案 FW 有哪些測試類別？
    
    # 🆕 Phase 12: 專案 FW 測項查詢
    QUERY_PROJECT_FW_CATEGORY_TEST_ITEMS = "query_project_fw_category_test_items"  # 專案 FW 特定類別有哪些測項？
    QUERY_PROJECT_FW_ALL_TEST_ITEMS = "query_project_fw_all_test_items"  # 專案 FW 有哪些測項？
    
    # 🆕 Phase 13: 按日期範圍查詢專案 FW 版本
    LIST_FW_BY_DATE_RANGE = "list_fw_by_date_range"  # 專案在指定日期範圍內有哪些 FW？
    
    # 🆕 Phase 14: 查詢專案 FW 支援的容量
    QUERY_SUPPORTED_CAPACITIES = "query_supported_capacities"  # 專案 FW 支援哪些容量？
    
    # 🆕 Phase 15: Known Issues 查詢（基礎查詢）
    QUERY_PROJECT_KNOWN_ISSUES = "query_project_known_issues"  # 查詢專案的 Known Issues
    QUERY_PROJECT_TEST_ITEM_KNOWN_ISSUES = "query_project_test_item_known_issues"  # 按 Test Item 查詢
    
    # 🆕 Phase 15: Known Issues 統計分析
    COUNT_PROJECT_KNOWN_ISSUES = "count_project_known_issues"  # 統計專案 Known Issues 數量
    RANK_PROJECTS_BY_KNOWN_ISSUES = "rank_projects_by_known_issues"  # 按 Issues 數量排名專案
    
    # 🆕 Phase 15: Known Issues 按建立者查詢
    QUERY_KNOWN_ISSUES_BY_CREATOR = "query_known_issues_by_creator"  # 查詢特定人員建立的 Issues
    LIST_KNOWN_ISSUES_CREATORS = "list_known_issues_creators"  # 列出所有 Issue 建立者
    
    # 🆕 Phase 15: Known Issues JIRA 相關
    QUERY_KNOWN_ISSUES_WITH_JIRA = "query_known_issues_with_jira"  # 查詢有 JIRA 連結的 Issues
    QUERY_KNOWN_ISSUES_WITHOUT_JIRA = "query_known_issues_without_jira"  # 查詢沒有 JIRA 的 Issues
    
    # 🆕 Phase 15: Known Issues 時間相關
    QUERY_RECENT_KNOWN_ISSUES = "query_recent_known_issues"  # 查詢最近的 Known Issues
    QUERY_KNOWN_ISSUES_BY_DATE_RANGE = "query_known_issues_by_date_range"  # 按日期範圍查詢
    
    # 🆕 Phase 15: Known Issues 跨專案搜尋
    SEARCH_KNOWN_ISSUES_BY_KEYWORD = "search_known_issues_by_keyword"  # 按關鍵字搜尋 Issues
    QUERY_ALL_KNOWN_ISSUES_BY_TEST_ITEM = "query_all_known_issues_by_test_item"  # 跨專案按 Test Item 搜尋
    
    # 🆕 Phase 16: Test Jobs 查詢（專案 FW 測試工作結果）
    QUERY_PROJECT_FW_TEST_JOBS = "query_project_fw_test_jobs"  # 查詢專案 FW 的測試工作結果
    
    # 🆕 Phase 17: FW 版本測試項目比較
    COMPARE_FW_TEST_JOBS = "compare_fw_test_jobs"  # 比較兩個 FW 版本的測試項目結果差異
    
    # 統計專案數量
    COUNT_PROJECTS = "count_projects"
    
    # 列出所有客戶
    LIST_ALL_CUSTOMERS = "list_all_customers"
    
    # 列出所有控制器
    LIST_ALL_CONTROLLERS = "list_all_controllers"
    
    # 無法識別的意圖
    UNKNOWN = "unknown"
    
    @classmethod
    def from_string(cls, value: str) -> 'IntentType':
        """
        從字串轉換為 IntentType
        
        Args:
            value: 意圖類型字串
            
        Returns:
            IntentType: 對應的意圖類型，如果找不到則返回 UNKNOWN
        """
        try:
            return cls(value)
        except ValueError:
            return cls.UNKNOWN
    
    @classmethod
    def get_all_intents(cls) -> List[str]:
        """獲取所有意圖類型的字串值"""
        return [intent.value for intent in cls]
    
    def get_description(self) -> str:
        """獲取意圖類型的描述"""
        descriptions = {
            self.QUERY_PROJECTS_BY_CUSTOMER: "按客戶查詢專案",
            self.QUERY_PROJECTS_BY_CONTROLLER: "按控制器查詢專案",
            self.QUERY_PROJECT_DETAIL: "查詢專案詳細資訊",
            self.QUERY_PROJECT_SUMMARY: "查詢專案測試摘要（舊版）",
            self.QUERY_PROJECT_TEST_SUMMARY: "查詢專案測試結果摘要（按類別和容量）",
            self.QUERY_PROJECT_TEST_BY_CATEGORY: "查詢專案特定類別的測試結果",
            self.QUERY_PROJECT_TEST_BY_CAPACITY: "查詢專案特定容量的測試結果",
            self.QUERY_PROJECT_TEST_SUMMARY_BY_FW: "按 FW 版本查詢專案測試結果",
            self.COMPARE_FW_VERSIONS: "比較兩個指定的 FW 版本測試結果",
            self.COMPARE_LATEST_FW: "自動比較最新兩個 FW 版本",
            self.LIST_FW_VERSIONS: "列出專案可比較的 FW 版本",
            self.QUERY_FW_DETAIL_SUMMARY: "查詢 FW 詳細統計（完成率、樣本、執行率）",
            self.QUERY_PROJECTS_BY_PL: "按專案負責人 (PL) 查詢專案",
            self.LIST_SUB_VERSIONS: "列出專案所有 Sub Version（容量版本）",
            self.LIST_FW_BY_SUB_VERSION: "列出特定 Sub Version 的 FW 版本",
            self.QUERY_PROJECTS_BY_TEST_CATEGORY: "跨專案搜尋特定測試類別（哪些案子有測試過 XX）",
            self.QUERY_PROJECT_FW_TEST_CATEGORIES: "查詢專案 FW 的測試類別（有哪些 Category）",
            self.QUERY_PROJECT_FW_CATEGORY_TEST_ITEMS: "查詢專案 FW 特定類別的測項（有哪些 Test Items）",
            self.QUERY_PROJECT_FW_ALL_TEST_ITEMS: "查詢專案 FW 的所有測項（列出全部 Test Items）",
            self.LIST_FW_BY_DATE_RANGE: "按日期範圍查詢專案 FW 版本（專案這個月有哪些 FW）",
            self.QUERY_SUPPORTED_CAPACITIES: "查詢專案 FW 支援的容量（支援哪些 TB/GB）",
            # Phase 15: Known Issues 相關
            self.QUERY_PROJECT_KNOWN_ISSUES: "查詢專案的 Known Issues（已知問題）",
            self.QUERY_PROJECT_TEST_ITEM_KNOWN_ISSUES: "查詢專案特定測試項目的 Known Issues",
            self.COUNT_PROJECT_KNOWN_ISSUES: "統計專案 Known Issues 數量",
            self.RANK_PROJECTS_BY_KNOWN_ISSUES: "按 Known Issues 數量排名專案",
            self.QUERY_KNOWN_ISSUES_BY_CREATOR: "查詢特定人員建立的 Known Issues",
            self.LIST_KNOWN_ISSUES_CREATORS: "列出 Known Issues 建立者",
            self.QUERY_KNOWN_ISSUES_WITH_JIRA: "查詢有 JIRA 連結的 Known Issues",
            self.QUERY_KNOWN_ISSUES_WITHOUT_JIRA: "查詢沒有 JIRA 連結的 Known Issues",
            self.QUERY_RECENT_KNOWN_ISSUES: "查詢最近的 Known Issues",
            self.QUERY_KNOWN_ISSUES_BY_DATE_RANGE: "按日期範圍查詢 Known Issues",
            self.SEARCH_KNOWN_ISSUES_BY_KEYWORD: "按關鍵字搜尋 Known Issues",
            self.QUERY_ALL_KNOWN_ISSUES_BY_TEST_ITEM: "跨專案按 Test Item 搜尋 Known Issues",
            # Phase 16: Test Jobs 查詢
            self.QUERY_PROJECT_FW_TEST_JOBS: "查詢專案 FW 的測試工作結果（含 Test Category、Item、Status 等）",
            # Phase 17: FW 版本測試項目比較
            self.COMPARE_FW_TEST_JOBS: "比較兩個 FW 版本的測試項目結果差異",
            self.COUNT_PROJECTS: "統計專案數量",
            self.LIST_ALL_CUSTOMERS: "列出所有客戶",
            self.LIST_ALL_CONTROLLERS: "列出所有控制器",
            self.UNKNOWN: "無法識別的意圖"
        }
        return descriptions.get(self, "未知意圖")
    
    def get_required_parameters(self) -> List[str]:
        """獲取此意圖所需的參數列表"""
        required_params = {
            self.QUERY_PROJECTS_BY_CUSTOMER: ["customer"],
            self.QUERY_PROJECTS_BY_CONTROLLER: ["controller"],
            self.QUERY_PROJECT_DETAIL: ["project_name"],
            self.QUERY_PROJECT_SUMMARY: ["project_name"],
            self.QUERY_PROJECT_TEST_SUMMARY: ["project_name"],
            self.QUERY_PROJECT_TEST_BY_CATEGORY: ["project_name", "category"],
            self.QUERY_PROJECT_TEST_BY_CAPACITY: ["project_name", "capacity"],
            self.QUERY_PROJECT_TEST_SUMMARY_BY_FW: ["project_name", "fw_version"],
            self.COMPARE_FW_VERSIONS: ["project_name", "fw_version_1", "fw_version_2"],
            self.QUERY_FW_DETAIL_SUMMARY: ["project_name", "fw_version"],
            self.QUERY_PROJECTS_BY_PL: ["pl"],
            self.LIST_SUB_VERSIONS: ["project_name"],  # Phase 9: 列出 Sub Version
            self.LIST_FW_BY_SUB_VERSION: ["project_name", "sub_version"],  # Phase 9: 列出特定 Sub Version 的 FW
            self.QUERY_PROJECTS_BY_TEST_CATEGORY: ["test_category"],  # Phase 10: 跨專案測試類別搜尋
            self.QUERY_PROJECT_FW_TEST_CATEGORIES: ["project_name", "fw_version"],  # Phase 11: 專案 FW 測試類別
            self.QUERY_PROJECT_FW_CATEGORY_TEST_ITEMS: ["project_name", "fw_version", "category_name"],  # Phase 12: 專案 FW 類別測項
            self.QUERY_PROJECT_FW_ALL_TEST_ITEMS: ["project_name", "fw_version"],  # Phase 12: 專案 FW 全部測項
            self.LIST_FW_BY_DATE_RANGE: ["project_name"],  # Phase 13: 專案 FW 日期範圍查詢
            self.QUERY_SUPPORTED_CAPACITIES: ["project_name", "fw_version"],  # Phase 14: 專案 FW 支援容量
            # Phase 15: Known Issues 相關
            self.QUERY_PROJECT_KNOWN_ISSUES: ["project_name"],
            self.QUERY_PROJECT_TEST_ITEM_KNOWN_ISSUES: ["project_name", "test_item"],
            self.COUNT_PROJECT_KNOWN_ISSUES: ["project_name"],
            self.RANK_PROJECTS_BY_KNOWN_ISSUES: [],  # top_n 和 customer 是可選的
            self.QUERY_KNOWN_ISSUES_BY_CREATOR: ["creator"],
            self.LIST_KNOWN_ISSUES_CREATORS: [],  # project_name 是可選的
            self.QUERY_KNOWN_ISSUES_WITH_JIRA: [],  # project_name 是可選的
            self.QUERY_KNOWN_ISSUES_WITHOUT_JIRA: [],  # project_name 是可選的
            self.QUERY_RECENT_KNOWN_ISSUES: [],  # days, limit, project_name 都是可選的
            self.QUERY_KNOWN_ISSUES_BY_DATE_RANGE: ["start_date"],  # end_date 是可選的
            self.SEARCH_KNOWN_ISSUES_BY_KEYWORD: ["keyword"],
            self.QUERY_ALL_KNOWN_ISSUES_BY_TEST_ITEM: ["test_item"],
            # Phase 16: Test Jobs 查詢
            self.QUERY_PROJECT_FW_TEST_JOBS: ["project_name", "fw_version"],  # Phase 16: 專案 FW 測試工作結果
            # Phase 17: FW 版本測試項目比較
            self.COMPARE_FW_TEST_JOBS: ["project_name", "fw_version_1", "fw_version_2"],  # Phase 17: 比較兩個 FW 版本的測試項目
            self.COUNT_PROJECTS: [],  # customer 是可選的
            self.LIST_ALL_CUSTOMERS: [],
            self.LIST_ALL_CONTROLLERS: [],
            self.UNKNOWN: []
        }
        return required_params.get(self, [])
    
    def get_optional_parameters(self) -> List[str]:
        """獲取此意圖的可選參數列表"""
        optional_params = {
            self.QUERY_PROJECTS_BY_CUSTOMER: [],
            self.QUERY_PROJECTS_BY_CONTROLLER: [],
            self.QUERY_PROJECT_DETAIL: [],
            self.QUERY_PROJECT_SUMMARY: [],
            self.QUERY_PROJECT_TEST_SUMMARY: ["category", "capacity"],  # 可選：過濾特定類別或容量
            self.QUERY_PROJECT_TEST_BY_CATEGORY: ["capacity"],  # 可選：同時按容量過濾
            self.QUERY_PROJECT_TEST_BY_CAPACITY: ["category"],  # 可選：同時按類別過濾
            self.QUERY_PROJECT_TEST_SUMMARY_BY_FW: ["sub_version"],  # 可選：指定 SubVersion (容量版本)
            self.COMPARE_FW_VERSIONS: ["sub_version"],  # 可選：指定 SubVersion
            self.COMPARE_LATEST_FW: ["sub_version"],  # 可選：指定 SubVersion
            self.LIST_FW_VERSIONS: ["sub_version"],  # 可選：指定 SubVersion
            self.COMPARE_MULTIPLE_FW: ["sub_version"],  # 可選：指定 SubVersion (如 AA, AB, AC)
            self.QUERY_FW_DETAIL_SUMMARY: ["sub_version"],  # 可選：指定 SubVersion
            self.QUERY_PROJECTS_BY_PL: [],  # PL 查詢沒有可選參數
            self.LIST_SUB_VERSIONS: [],  # Phase 9: 無可選參數
            self.LIST_FW_BY_SUB_VERSION: ["include_stats"],  # Phase 9: 可選是否包含統計
            self.QUERY_PROJECTS_BY_TEST_CATEGORY: ["customer", "status_filter"],  # Phase 10: 可選客戶和狀態篩選
            self.QUERY_PROJECT_FW_TEST_CATEGORIES: ["capacity"],  # Phase 11: 可選容量過濾
            self.QUERY_PROJECT_FW_CATEGORY_TEST_ITEMS: ["capacity"],  # Phase 12: 可選容量過濾
            self.QUERY_PROJECT_FW_ALL_TEST_ITEMS: ["capacity"],  # Phase 12: 可選容量過濾
            self.LIST_FW_BY_DATE_RANGE: ["sub_version", "year", "month", "start_month", "end_month", "date_range"],  # Phase 13: 可選參數
            # Phase 15: Known Issues 相關
            self.QUERY_PROJECT_KNOWN_ISSUES: ["show_disabled"],
            self.QUERY_PROJECT_TEST_ITEM_KNOWN_ISSUES: ["show_disabled"],
            self.COUNT_PROJECT_KNOWN_ISSUES: [],
            self.RANK_PROJECTS_BY_KNOWN_ISSUES: ["top_n", "customer"],
            self.QUERY_KNOWN_ISSUES_BY_CREATOR: ["project_name"],
            self.LIST_KNOWN_ISSUES_CREATORS: ["project_name"],
            self.QUERY_KNOWN_ISSUES_WITH_JIRA: ["project_name"],
            self.QUERY_KNOWN_ISSUES_WITHOUT_JIRA: ["project_name"],
            self.QUERY_RECENT_KNOWN_ISSUES: ["days", "limit", "project_name"],
            self.QUERY_KNOWN_ISSUES_BY_DATE_RANGE: ["end_date", "project_name"],
            self.SEARCH_KNOWN_ISSUES_BY_KEYWORD: ["search_fields", "project_name"],
            self.QUERY_ALL_KNOWN_ISSUES_BY_TEST_ITEM: ["customer"],
            # Phase 16: Test Jobs 查詢
            self.QUERY_PROJECT_FW_TEST_JOBS: ["test_tool_key"],  # 可選：測試工具篩選
            # Phase 17: FW 版本測試項目比較
            self.COMPARE_FW_TEST_JOBS: ["test_category", "show_only_diff"],  # 可選：篩選類別、只顯示差異
            self.COUNT_PROJECTS: ["customer"],  # 可選：按客戶統計
            self.LIST_ALL_CUSTOMERS: [],
            self.LIST_ALL_CONTROLLERS: [],
            self.UNKNOWN: []
        }
        return optional_params.get(self, [])


@dataclass
class IntentResult:
    """
    意圖分析結果
    
    Attributes:
        intent: 識別到的意圖類型
        parameters: 提取的參數
        confidence: 信心度 (0.0 - 1.0)
        raw_response: LLM 原始回應（用於調試）
        error: 錯誤訊息（如果有）
    """
    intent: IntentType
    parameters: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    raw_response: Optional[str] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        """後初始化處理"""
        # 確保 intent 是 IntentType
        if isinstance(self.intent, str):
            self.intent = IntentType.from_string(self.intent)
        
        # 確保 confidence 在有效範圍內
        self.confidence = max(0.0, min(1.0, self.confidence))
    
    def is_valid(self) -> bool:
        """檢查意圖結果是否有效"""
        if self.error:
            return False
        if self.intent == IntentType.UNKNOWN:
            return False
        
        # 檢查必要參數
        required_params = self.intent.get_required_parameters()
        for param in required_params:
            if param not in self.parameters or not self.parameters[param]:
                return False
        
        return True
    
    def is_high_confidence(self, threshold: float = 0.7) -> bool:
        """檢查是否為高信心度結果"""
        return self.confidence >= threshold
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'intent': self.intent.value,
            'parameters': self.parameters,
            'confidence': self.confidence,
            'raw_response': self.raw_response,
            'error': self.error,
            'is_valid': self.is_valid()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IntentResult':
        """從字典創建 IntentResult"""
        return cls(
            intent=IntentType.from_string(data.get('intent', 'unknown')),
            parameters=data.get('parameters', {}),
            confidence=data.get('confidence', 0.0),
            raw_response=data.get('raw_response'),
            error=data.get('error')
        )
    
    @classmethod
    def create_unknown(cls, raw_response: str = None, error: str = None) -> 'IntentResult':
        """創建一個未知意圖的結果"""
        return cls(
            intent=IntentType.UNKNOWN,
            parameters={},
            confidence=0.0,
            raw_response=raw_response,
            error=error
        )
    
    @classmethod
    def create_error(cls, error: str, raw_response: str = None) -> 'IntentResult':
        """創建一個錯誤結果"""
        return cls(
            intent=IntentType.UNKNOWN,
            parameters={},
            confidence=0.0,
            raw_response=raw_response,
            error=error
        )


# 已知客戶名稱（用於意圖分析）
KNOWN_CUSTOMERS = [
    'WD', 'WDC', 'Western Digital',
    'Samsung',
    'Micron',
    'Transcend',
    'ADATA',
    'UMIS',
    'Biwin',
    'Kioxia',
    'SK Hynix',
    'Intel',
    'Toshiba',
    'SanDisk',
    'Kingston',
    'Crucial',
    'Patriot',
    'Lexar',
    'PNY',
    'Team Group',
]

# 已知控制器型號（用於意圖分析）
KNOWN_CONTROLLERS = [
    'SM2263', 'SM2263XT',
    'SM2264', 'SM2264XT',
    'SM2267', 'SM2267XT',
    'SM2269', 'SM2269XT',
    'SM2270',
    'SM2271',
]

# 已知專案負責人（用於意圖分析）
KNOWN_PLS = [
    # 常見格式：簡稱
    'Ryder', 'Jeffery', 'Wei-Zhen', 'Zhenyuan', 'Bruce',
    # 常見格式：email 前綴
    'ryder.lin', 'jeffery.kuo', 'bruce.zhang',
    # 完整名稱
    'Zhenyuan Peng',
]

# 已知測試類別（用於測試摘要查詢）
KNOWN_TEST_CATEGORIES = [
    # 完整名稱
    'Compliance', 'Functionality', 'Performance', 
    'Interoperability', 'Stress', 'Compatibility',
    # 縮寫
    'Comp', 'Func', 'Perf', 'Inter', 'Compat',
    # 中文
    '合規性', '功能測試', '效能測試', '互通性', '壓力測試', '相容性',
]

# 已知容量規格（用於測試摘要查詢）
KNOWN_CAPACITIES = [
    # 標準容量表示
    '256GB', '512GB', '1TB', '2TB', '4TB', '8TB',
    # 替代表示
    '256G', '512G', '1T', '2T', '4T', '8T',
    # 數字形式
    '256', '512', '1024', '2048',
]

# 意圖觸發詞對應表（用於降級的關鍵字匹配）
INTENT_KEYWORDS = {
    IntentType.QUERY_PROJECTS_BY_CUSTOMER: [
        '專案', 'project', '有哪些專案', '專案列表', '的專案'
    ],
    IntentType.QUERY_PROJECTS_BY_CONTROLLER: [
        '控制器', 'controller', '用在哪些專案', '哪些專案用'
    ],
    IntentType.QUERY_PROJECT_DETAIL: [
        '詳細資訊', '詳情', 'detail', '資訊', '專案資訊'
    ],
    IntentType.QUERY_PROJECT_SUMMARY: [
        '測試結果', '測試狀況', 'summary', '摘要', '測試摘要'
    ],
    IntentType.QUERY_PROJECT_TEST_SUMMARY: [
        '測試結果', '測試摘要', '測試統計', '測試狀態', '測試報告',
        'test summary', 'test result', '測試結果總覽',
        'pass', 'fail', '通過', '失敗', '測試狀況'
    ],
    IntentType.QUERY_PROJECT_TEST_BY_CATEGORY: [
        '類別測試', '分類測試', 'category', 
        'Compliance', 'Functionality', 'Performance', 
        'Interoperability', 'Stress', 'Compatibility',
        '合規', '功能', '效能', '互通', '壓力', '相容'
    ],
    IntentType.QUERY_PROJECT_TEST_BY_CAPACITY: [
        '容量', 'capacity', 
        '256GB', '512GB', '1TB', '2TB', '4TB',
        '256G', '512G', '1T', '2T', '4T'
    ],
    IntentType.COUNT_PROJECTS: [
        '多少', '幾個', '數量', 'count', '總共', '專案數'
    ],
    IntentType.LIST_ALL_CUSTOMERS: [
        '客戶', '有哪些客戶', '客戶列表', 'customer'
    ],
    IntentType.LIST_ALL_CONTROLLERS: [
        '有哪些控制器', '控制器列表', '控制器型號', '支援的控制器'
    ],
    IntentType.QUERY_PROJECTS_BY_PL: [
        '負責', '專案負責人', 'PL', 'project leader', '管理的專案',
        '誰負責', '負責人是', '的專案'
    ],
    # Phase 15: Known Issues 相關關鍵字
    IntentType.QUERY_PROJECT_KNOWN_ISSUES: [
        'known issue', 'known issues', '已知問題', 'issue', 'issues',
        '問題', '已知', '已知的問題', 'known'
    ],
    IntentType.QUERY_PROJECT_TEST_ITEM_KNOWN_ISSUES: [
        'known issue', '測試問題', 'test item issue', '測試項目問題',
        '的問題', '有什麼問題', '什麼issue'
    ],
    IntentType.COUNT_PROJECT_KNOWN_ISSUES: [
        '幾個known issue', '多少issue', '幾個問題', 'issue數量',
        '有幾個', '有多少', 'known issue數'
    ],
    IntentType.RANK_PROJECTS_BY_KNOWN_ISSUES: [
        '最多issue', 'issue排名', '問題最多', '哪個專案issue最多',
        '前幾名', 'top', '排名'
    ],
    IntentType.QUERY_KNOWN_ISSUES_BY_CREATOR: [
        '建立的', '建的', '誰建的', '建立者', 'created by',
        '誰建立', '建了哪些'
    ],
    IntentType.LIST_KNOWN_ISSUES_CREATORS: [
        '建立者', '誰建的', '建立者列表', '有哪些人建立',
        '都是誰建的', 'creators'
    ],
    IntentType.QUERY_KNOWN_ISSUES_WITH_JIRA: [
        '有jira', '已開jira', 'jira連結', '有關聯jira',
        '連結到jira', 'with jira'
    ],
    IntentType.QUERY_KNOWN_ISSUES_WITHOUT_JIRA: [
        '沒有jira', '未開jira', '缺少jira', '沒jira',
        '沒有開jira', 'without jira', '還沒開jira'
    ],
    IntentType.QUERY_RECENT_KNOWN_ISSUES: [
        '最近', '這週', '這個月', '新增的', 'recent',
        '最近一週', '最近幾天', '最新'
    ],
    IntentType.QUERY_KNOWN_ISSUES_BY_DATE_RANGE: [
        '日期', '時間範圍', '月份', 'date range',
        '幾月', '從...到', '期間'
    ],
    IntentType.SEARCH_KNOWN_ISSUES_BY_KEYWORD: [
        '搜尋', '包含', '關鍵字', '備註有', 'search',
        'keyword', '找出', '找'
    ],
    IntentType.QUERY_ALL_KNOWN_ISSUES_BY_TEST_ITEM: [
        '所有專案', '跨專案', '哪些專案有', '全部專案的',
        '所有的', 'all projects'
    ],
}
