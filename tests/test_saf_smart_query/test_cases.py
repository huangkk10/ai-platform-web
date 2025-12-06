"""
SAF Smart Query 測試案例定義
============================

定義所有測試案例，方便管理和維護。
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class TestCase:
    """測試案例"""
    name: str                          # 測試名稱
    query: str                         # 用戶問題
    expected_intent: str               # 預期意圖
    expected_params: Dict[str, Any]    # 預期參數（部分匹配）
    min_confidence: float = 0.5        # 最低信心度
    should_succeed: bool = True        # 是否應該成功
    description: str = ""              # 測試說明


# ============================================================
# 1. 按客戶查詢專案
# ============================================================
CUSTOMER_QUERY_TESTS = [
    TestCase(
        name="客戶查詢_WD",
        query="WD 有哪些專案？",
        expected_intent="query_projects_by_customer",
        expected_params={"customer": "WD"},
        min_confidence=0.8,
        description="標準客戶查詢"
    ),
    TestCase(
        name="客戶查詢_Samsung",
        query="Samsung 的專案有哪些？",
        expected_intent="query_projects_by_customer",
        expected_params={"customer": "Samsung"},
        min_confidence=0.8,
        description="不同客戶名稱"
    ),
    TestCase(
        name="客戶查詢_WDC",
        query="WDC 有什麼專案",
        expected_intent="query_projects_by_customer",
        expected_params={"customer": "WDC"},  # WDC 在資料庫中是獨立客戶
        min_confidence=0.7,
        description="WDC 客戶查詢（獨立客戶）"
    ),
    TestCase(
        name="客戶查詢_列出格式",
        query="列出 Micron 的所有專案",
        expected_intent="query_projects_by_customer",
        expected_params={"customer": "Micron"},
        min_confidence=0.7,
        description="不同問法"
    ),
    TestCase(
        name="客戶查詢_口語化",
        query="我想看看 ADATA 在做什麼專案",
        expected_intent="query_projects_by_customer",
        expected_params={"customer": "ADATA"},
        min_confidence=0.6,
        description="口語化問法"
    ),
]

# ============================================================
# 2. 按控制器查詢專案
# ============================================================
CONTROLLER_QUERY_TESTS = [
    TestCase(
        name="控制器查詢_SM2264",
        query="SM2264 控制器用在哪些專案？",
        expected_intent="query_projects_by_controller",
        expected_params={"controller": "SM2264"},
        min_confidence=0.8,
        description="標準控制器查詢"
    ),
    TestCase(
        name="控制器查詢_SM2269",
        query="哪些專案使用 SM2269？",
        expected_intent="query_projects_by_controller",
        expected_params={"controller": "SM2269"},
        min_confidence=0.7,
        description="不同問法"
    ),
    TestCase(
        name="控制器查詢_XT系列",
        query="SM2264XT 有哪些專案在用",
        expected_intent="query_projects_by_controller",
        expected_params={"controller": "SM2264XT"},
        min_confidence=0.7,
        description="XT 系列控制器"
    ),
]

# ============================================================
# 3. 專案詳情查詢
# ============================================================
PROJECT_DETAIL_TESTS = [
    TestCase(
        name="專案詳情_DEMETER",
        query="DEMETER 專案的詳細資訊",
        expected_intent="query_project_detail",
        expected_params={"project_name": "DEMETER"},
        min_confidence=0.8,
        description="標準專案詳情查詢"
    ),
    TestCase(
        name="專案詳情_口語化",
        query="請告訴我 Garuda 專案的情況",
        expected_intent="query_project_detail",
        expected_params={"project_name": "Garuda"},
        min_confidence=0.7,
        description="口語化問法"
    ),
    TestCase(
        name="專案詳情_簡短",
        query="查詢 Taurian 專案",
        expected_intent="query_project_detail",
        expected_params={"project_name": "Taurian"},
        min_confidence=0.6,
        description="簡短問法"
    ),
]

# ============================================================
# 4. 專案測試摘要查詢 (基本)
# ============================================================
PROJECT_SUMMARY_TESTS = [
    TestCase(
        name="測試摘要_DEMETER",
        query="DEMETER 的測試結果如何？",
        expected_intent="query_project_test_summary",
        expected_params={"project_name": "DEMETER"},
        min_confidence=0.7,
        description="測試結果查詢"
    ),
    TestCase(
        name="測試摘要_測試狀況",
        query="Garuda 專案測試狀況",
        expected_intent="query_project_test_summary",
        expected_params={"project_name": "Garuda"},
        min_confidence=0.6,
        description="測試狀況查詢"
    ),
    TestCase(
        name="測試摘要_多少通過",
        query="KC600 有多少測試通過？",
        expected_intent="query_project_test_summary",
        expected_params={"project_name": "KC600"},
        min_confidence=0.7,
        description="通過數量查詢"
    ),
    TestCase(
        name="測試摘要_失敗數量",
        query="TITAN 有多少測試失敗？",
        expected_intent="query_project_test_summary",
        expected_params={"project_name": "TITAN"},
        min_confidence=0.7,
        description="失敗數量查詢"
    ),
    TestCase(
        name="測試摘要_測試進度",
        query="NV3 專案的測試進度如何",
        expected_intent="query_project_test_summary",
        expected_params={"project_name": "NV3"},
        min_confidence=0.6,
        description="測試進度查詢"
    ),
    TestCase(
        name="測試摘要_口語化",
        query="想了解一下 Thor 測試跑得怎麼樣",
        expected_intent="query_project_test_summary",
        expected_params={"project_name": "Thor"},
        min_confidence=0.5,
        description="口語化測試查詢"
    ),
]

# ============================================================
# 4.1 按類別查詢專案測試 (Phase 3 新增)
# ============================================================
TEST_BY_CATEGORY_TESTS = [
    TestCase(
        name="類別測試_Compliance",
        query="TITAN 的 Compliance 測試結果",
        expected_intent="query_project_test_by_category",
        expected_params={"project_name": "TITAN", "category": "Compliance"},
        min_confidence=0.7,
        description="Compliance 類別測試查詢"
    ),
    TestCase(
        name="類別測試_Performance",
        query="DEMETER 專案的效能測試如何？",
        expected_intent="query_project_test_by_category",
        expected_params={"project_name": "DEMETER", "category": "Performance"},
        min_confidence=0.7,
        description="Performance 類別測試查詢"
    ),
    TestCase(
        name="類別測試_Interoperability",
        query="APOLLO 的相容性測試結果",
        expected_intent="query_project_test_by_category",
        expected_params={"project_name": "APOLLO", "category": "Compatibility"},
        min_confidence=0.6,
        description="相容性測試查詢（中文'相容性'對應 Compatibility）"
    ),
    TestCase(
        name="類別測試_Stress",
        query="Garuda 專案壓力測試跑了多少",
        expected_intent="query_project_test_by_category",
        expected_params={"project_name": "Garuda", "category": "Stress"},
        min_confidence=0.6,
        description="Stress 類別測試查詢"
    ),
    TestCase(
        name="類別測試_Functional",
        query="PHOENIX 的功能測試結果如何",
        expected_intent="query_project_test_by_category",
        expected_params={"project_name": "PHOENIX", "category": "Functionality"},
        min_confidence=0.6,
        description="功能測試查詢（中文'功能測試'對應 Functionality）"
    ),
    TestCase(
        name="類別測試_Interop_英文",
        query="VULCAN 專案的 Interoperability 測試狀況",
        expected_intent="query_project_test_by_category",
        expected_params={"project_name": "VULCAN", "category": "Interoperability"},
        min_confidence=0.6,
        description="Interoperability 英文關鍵字查詢"
    ),
    TestCase(
        name="類別測試_中文口語化",
        query="TITAN 的相容測試做得如何？",
        expected_intent="query_project_test_by_category",
        expected_params={"project_name": "TITAN", "category": "Compatibility"},
        min_confidence=0.5,
        description="中文口語化相容測試查詢"
    ),
    TestCase(
        name="類別測試_所有分類",
        query="DEMETER 的 Compliance 項目通過了幾個？",
        expected_intent="query_project_test_by_category",
        expected_params={"project_name": "DEMETER", "category": "Compliance"},
        min_confidence=0.6,
        description="帶數量詢問的類別查詢"
    ),
]

# ============================================================
# 4.2 按容量查詢專案測試 (Phase 3 新增)
# ============================================================
TEST_BY_CAPACITY_TESTS = [
    TestCase(
        name="容量測試_1TB",
        query="NV3 1TB 的測試狀況",
        expected_intent="query_project_test_by_capacity",
        expected_params={"project_name": "NV3", "capacity": "1TB"},
        min_confidence=0.7,
        description="1TB 容量測試查詢"
    ),
    TestCase(
        name="容量測試_512GB",
        query="TITAN 512GB 測試結果",
        expected_intent="query_project_test_by_capacity",
        expected_params={"project_name": "TITAN", "capacity": "512GB"},
        min_confidence=0.7,
        description="512GB 容量測試查詢"
    ),
    TestCase(
        name="容量測試_2TB",
        query="DEMETER 2TB 版本測試如何？",
        expected_intent="query_project_test_by_capacity",
        expected_params={"project_name": "DEMETER", "capacity": "2TB"},
        min_confidence=0.7,
        description="2TB 容量測試查詢"
    ),
    TestCase(
        name="容量測試_256GB",
        query="Garuda 專案 256GB 的測試進度",
        expected_intent="query_project_test_by_capacity",
        expected_params={"project_name": "Garuda", "capacity": "256GB"},
        min_confidence=0.6,
        description="256GB 容量測試查詢"
    ),
    TestCase(
        name="容量測試_4TB",
        query="PHOENIX 4TB 測試結果如何",
        expected_intent="query_project_test_by_capacity",
        expected_params={"project_name": "PHOENIX", "capacity": "4TB"},
        min_confidence=0.6,
        description="4TB 容量測試查詢"
    ),
    TestCase(
        name="容量測試_128GB",
        query="VULCAN 128GB 的測試狀況",
        expected_intent="query_project_test_by_capacity",
        expected_params={"project_name": "VULCAN", "capacity": "128GB"},
        min_confidence=0.6,
        description="128GB 容量測試查詢"
    ),
    TestCase(
        name="容量測試_口語化",
        query="想看 TITAN 一T版本的測試",
        expected_intent="query_project_test_by_capacity",
        expected_params={"project_name": "TITAN", "capacity": "1TB"},
        min_confidence=0.5,
        description="口語化容量查詢（一T = 1TB）"
    ),
    TestCase(
        name="容量測試_多少通過",
        query="APOLLO 2TB 有多少測試通過？",
        expected_intent="query_project_test_by_capacity",
        expected_params={"project_name": "APOLLO", "capacity": "2TB"},
        min_confidence=0.6,
        description="帶數量詢問的容量查詢"
    ),
]

# ============================================================
# 4.3 按 FW 版本查詢專案測試 (Phase 4 新增)
# ============================================================
TEST_BY_FW_VERSION_TESTS = [
    TestCase(
        name="FW版本測試_標準格式",
        query="DEMETER 專案 FW Y1114B 的測試結果",
        expected_intent="query_project_test_summary_by_fw",
        expected_params={"project_name": "DEMETER", "fw_version": "Y1114B"},
        min_confidence=0.7,
        description="標準 FW 版本測試查詢"
    ),
    TestCase(
        name="FW版本測試_Channel",
        query="Channel 的 82CBW5QF 版本測試狀況",
        expected_intent="query_project_test_summary_by_fw",
        expected_params={"project_name": "Channel", "fw_version": "82CBW5QF"},
        min_confidence=0.7,
        description="Channel 專案的 FW 版本查詢"
    ),
    TestCase(
        name="FW版本測試_A400",
        query="A400 專案 X0325A 的測試結果如何",
        expected_intent="query_project_test_summary_by_fw",
        expected_params={"project_name": "A400", "fw_version": "X0325A"},
        min_confidence=0.7,
        description="A400 專案的 FW 版本查詢"
    ),
    TestCase(
        name="FW版本測試_Frey3B",
        query="想看一下 Frey3B 的 FWX0926C 測試結果",
        expected_intent="query_project_test_summary_by_fw",
        expected_params={"project_name": "Frey3B", "fw_version": "FWX0926C"},
        min_confidence=0.6,
        description="Frey3B 專案的 FW 版本查詢（口語化）"
    ),
    TestCase(
        name="FW版本測試_通過數量",
        query="Bennington 專案韌體 Y1103C 有多少測試通過",
        expected_intent="query_project_test_summary_by_fw",
        expected_params={"project_name": "Bennington", "fw_version": "Y1103C"},
        min_confidence=0.6,
        description="帶數量詢問的 FW 版本查詢"
    ),
    TestCase(
        name="FW版本測試_韌體版本",
        query="Garuda 韌體版本 22Z4VBL3 測試情況",
        expected_intent="query_project_test_summary_by_fw",
        expected_params={"project_name": "Garuda", "fw_version": "22Z4VBL3"},
        min_confidence=0.6,
        description="使用「韌體版本」關鍵字"
    ),
    TestCase(
        name="FW版本測試_firmware",
        query="Hydro firmware FDC_Y1121A_7b80259 的測試結果",
        expected_intent="query_project_test_summary_by_fw",
        expected_params={"project_name": "Hydro", "fw_version": "FDC_Y1121A_7b80259"},
        min_confidence=0.6,
        description="使用英文 firmware 關鍵字"
    ),
    TestCase(
        name="FW版本測試_版本號",
        query="KC600 版本 S4800122 測試報告",
        expected_intent="query_project_test_summary_by_fw",
        expected_params={"project_name": "KC600", "fw_version": "S4800122"},
        min_confidence=0.6,
        description="使用「版本」關鍵字"
    ),
    TestCase(
        name="FW版本測試_Springsteen",
        query="Springsteen 專案 G200X6EC 的測試結果",
        expected_intent="query_project_test_summary_by_fw",
        expected_params={"project_name": "Springsteen", "fw_version": "G200X6EC"},
        min_confidence=0.7,
        description="Springsteen 專案的 FW 版本查詢（真實資料）"
    ),
]

# ============================================================
# 4.4 比較兩個 FW 版本測試 (Phase 5 新增)
# ============================================================
COMPARE_FW_VERSIONS_TESTS = [
    TestCase(
        name="FW版本比較_標準格式",
        query="DEMETER 專案的 Y1114B 和 Y1114A 比較",
        expected_intent="compare_fw_versions",
        expected_params={
            "project_name": "DEMETER", 
            "fw_version_1": "Y1114B", 
            "fw_version_2": "Y1114A"
        },
        min_confidence=0.7,
        description="標準 FW 版本比較"
    ),
    TestCase(
        name="FW版本比較_完整句子",
        query="比較 Channel 專案 FW 82CBW5QF 和 82F1W7DA 的測試結果",
        expected_intent="compare_fw_versions",
        expected_params={
            "project_name": "Channel", 
            "fw_version_1": "82CBW5QF", 
            "fw_version_2": "82F1W7DA"
        },
        min_confidence=0.7,
        description="完整描述的版本比較（使用真實 FW）"
    ),
    TestCase(
        name="FW版本比較_差異查詢",
        query="A400 的 X0325A 版本跟 W0207A 版本差異",
        expected_intent="compare_fw_versions",
        expected_params={
            "project_name": "A400", 
            "fw_version_1": "X0325A", 
            "fw_version_2": "W0207A"
        },
        min_confidence=0.6,
        description="使用「差異」關鍵字（使用真實 FW）"
    ),
    TestCase(
        name="FW版本比較_VS格式",
        query="DEMETER FW Y1114B vs Y1114A",
        expected_intent="compare_fw_versions",
        expected_params={
            "project_name": "DEMETER", 
            "fw_version_1": "Y1114B", 
            "fw_version_2": "Y1114A"
        },
        min_confidence=0.6,
        description="使用 vs 格式"
    ),
    TestCase(
        name="FW版本比較_優劣查詢",
        query="Frey3B 的 FWX0926C 和 FWX0509DE 哪個測試結果比較好",
        expected_intent="compare_fw_versions",
        expected_params={
            "project_name": "Frey3B", 
            "fw_version_1": "FWX0926C", 
            "fw_version_2": "FWX0509DE"
        },
        min_confidence=0.6,
        description="詢問哪個版本較好（使用真實 FW）"
    ),
    TestCase(
        name="FW版本比較_對比格式",
        query="對比 Bennington 專案韌體 Y1103C 和 Y0418A",
        expected_intent="compare_fw_versions",
        expected_params={
            "project_name": "Bennington", 
            "fw_version_1": "Y1103C", 
            "fw_version_2": "Y0418A"
        },
        min_confidence=0.6,
        description="使用「對比」關鍵字（使用真實 FW）"
    ),
]

# ============================================================
# 5. 統計專案數量
# ============================================================
COUNT_PROJECTS_TESTS = [
    TestCase(
        name="數量統計_總數",
        query="總共有多少專案？",
        expected_intent="count_projects",
        expected_params={},
        min_confidence=0.8,
        description="總數查詢"
    ),
    TestCase(
        name="數量統計_客戶專案數",
        query="Samsung 有幾個專案？",
        expected_intent="count_projects",
        expected_params={"customer": "Samsung"},
        min_confidence=0.8,
        description="特定客戶數量"
    ),
    TestCase(
        name="數量統計_口語化",
        query="WD 目前有多少個進行中的專案",
        expected_intent="count_projects",
        expected_params={"customer": "WD"},
        min_confidence=0.5,  # 口語化問法可能降低信心度
        description="口語化數量查詢"
    ),
    TestCase(
        name="數量統計_專案數量",
        query="專案數量是多少",
        expected_intent="count_projects",
        expected_params={},
        min_confidence=0.7,
        description="簡短數量查詢"
    ),
]

# ============================================================
# 6. 列出所有客戶
# ============================================================
LIST_CUSTOMERS_TESTS = [
    TestCase(
        name="客戶列表_標準",
        query="有哪些客戶？",
        expected_intent="list_all_customers",
        expected_params={},
        min_confidence=0.8,
        description="標準客戶列表查詢"
    ),
    TestCase(
        name="客戶列表_列出",
        query="列出所有客戶",
        expected_intent="list_all_customers",
        expected_params={},
        min_confidence=0.7,
        description="列出格式"
    ),
    TestCase(
        name="客戶列表_全部",
        query="目前有哪些客戶在合作",
        expected_intent="list_all_customers",
        expected_params={},
        min_confidence=0.6,
        description="口語化問法"
    ),
]

# ============================================================
# 7. 列出所有控制器
# ============================================================
LIST_CONTROLLERS_TESTS = [
    TestCase(
        name="控制器列表_標準",
        query="有哪些控制器？",
        expected_intent="list_all_controllers",
        expected_params={},
        min_confidence=0.8,
        description="標準控制器列表查詢"
    ),
    TestCase(
        name="控制器列表_列出",
        query="列出所有控制器型號",
        expected_intent="list_all_controllers",
        expected_params={},
        min_confidence=0.7,
        description="列出格式"
    ),
    TestCase(
        name="控制器列表_支援",
        query="系統支援哪些控制器",
        expected_intent="list_all_controllers",
        expected_params={},
        min_confidence=0.6,
        description="支援格式問法"
    ),
]

# ============================================================
# 8. 未知意圖（邊界測試）
# ============================================================
UNKNOWN_INTENT_TESTS = [
    TestCase(
        name="未知意圖_天氣",
        query="今天天氣如何？",
        expected_intent="unknown",
        expected_params={},
        min_confidence=0.0,
        should_succeed=False,  # API 返回 success=false 是正確的
        description="完全無關的問題"
    ),
    TestCase(
        name="未知意圖_問候",
        query="你好",
        expected_intent="unknown",
        expected_params={},
        min_confidence=0.0,
        should_succeed=False,  # API 返回 success=false 是正確的
        description="簡單問候"
    ),
    TestCase(
        name="未知意圖_模糊",
        query="幫我查一下",
        expected_intent="unknown",
        expected_params={},
        min_confidence=0.0,
        should_succeed=False,  # API 返回 success=false 是正確的
        description="模糊不清的請求"
    ),
]

# ============================================================
# 9. 邊界情況測試
# ============================================================
EDGE_CASE_TESTS = [
    TestCase(
        name="邊界_空白查詢",
        query="   ",
        expected_intent="unknown",
        expected_params={},
        should_succeed=False,
        description="空白查詢應該失敗"
    ),
    TestCase(
        name="邊界_超長查詢",
        query="我想要查詢一下關於 WD 這個客戶的所有專案資訊，包括他們使用的控制器型號、NAND 類型、負責人等等，" * 3,
        expected_intent="query_projects_by_customer",
        expected_params={"customer": "WD"},
        min_confidence=0.5,
        description="超長查詢"
    ),
    TestCase(
        name="邊界_混合中英文",
        query="Show me WD's projects 列表",
        expected_intent="query_projects_by_customer",
        expected_params={"customer": "WD"},
        min_confidence=0.5,
        description="中英文混合"
    ),
    TestCase(
        name="邊界_特殊字符",
        query="WD 的專案？！@#",
        expected_intent="query_projects_by_customer",
        expected_params={"customer": "WD"},
        min_confidence=0.5,
        description="包含特殊字符"
    ),
]

# ============================================================
# 所有測試套件
# ============================================================
ALL_TEST_SUITES = [
    ("1. 按客戶查詢專案", CUSTOMER_QUERY_TESTS),
    ("2. 按控制器查詢專案", CONTROLLER_QUERY_TESTS),
    ("3. 專案詳情查詢", PROJECT_DETAIL_TESTS),
    ("4. 專案測試摘要（基本）", PROJECT_SUMMARY_TESTS),
    ("4.1 按類別查詢測試（Phase 3）", TEST_BY_CATEGORY_TESTS),
    ("4.2 按容量查詢測試（Phase 3）", TEST_BY_CAPACITY_TESTS),
    ("4.3 按 FW 版本查詢測試（Phase 4）", TEST_BY_FW_VERSION_TESTS),
    ("4.4 FW 版本比較測試（Phase 5）", COMPARE_FW_VERSIONS_TESTS),
    ("5. 統計專案數量", COUNT_PROJECTS_TESTS),
    ("6. 列出所有客戶", LIST_CUSTOMERS_TESTS),
    ("7. 列出所有控制器", LIST_CONTROLLERS_TESTS),
    ("8. 未知意圖", UNKNOWN_INTENT_TESTS),
    ("9. 邊界情況", EDGE_CASE_TESTS),
]
