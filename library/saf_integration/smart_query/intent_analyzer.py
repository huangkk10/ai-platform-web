"""
SAF 意圖分析器
=============

使用 Dify Chat API 分析用戶查詢的意圖，輸出結構化的意圖識別結果。

功能：
1. 分析用戶問題的意圖
2. 提取相關參數（客戶名稱、控制器型號、專案名稱等）
3. 返回信心度評分
4. 提供降級的關鍵字匹配方案

作者：AI Platform Team
創建日期：2025-12-05
"""

import json
import logging
import re
import requests
from typing import Optional, Dict, Any

from .intent_types import (
    IntentType, 
    IntentResult, 
    KNOWN_CUSTOMERS, 
    KNOWN_CONTROLLERS,
    KNOWN_TEST_CATEGORIES,
    KNOWN_CAPACITIES,
    INTENT_KEYWORDS
)

logger = logging.getLogger(__name__)


# ============================================================
# 意圖分析 Prompt（完全在程式碼中管理，可版本控制）
# ============================================================
INTENT_ANALYSIS_PROMPT = """
你是一個意圖分析器，專門分析用戶關於 SAF 專案管理系統的問題。

【重要規則】
1. 你必須**只輸出 JSON 格式**，不要輸出任何其他文字、解釋或標記
2. 仔細理解用戶問題的**語義意圖**，不要只看關鍵字
3. 即使語句結構不同，只要意思相同就應該識別為相同意圖

## 可用的意圖類型

### 1. query_projects_by_customer - 按客戶查詢專案
用戶想知道某個客戶有哪些專案時使用。
- 常見問法：
  - 「XX 有哪些專案」「列出 XX 的專案」「XX 的專案有哪些」
  - 「XX 的專案列表」「顯示 XX 的專案」「查詢 XX 的專案」
  - 「XX 目前有什麼專案」「XX 正在進行的專案」
- 參數：customer (客戶名稱)

### 2. query_projects_by_controller - 按控制器查詢專案
用戶想知道某個控制器型號被哪些專案使用時使用。
- 常見問法：
  - 「SM2264 用在哪些專案」「哪些專案用 SM2264」
  - 「SM2264 被哪些專案使用」「哪些專案使用 SM2264」
  - 「那些專案使用 SM2264」「什麼專案用 SM2264 控制器」
  - 「SM2264 的專案」「用 SM2264 的專案有哪些」
  - 「列出使用 SM2264 的專案」「查詢 SM2264 相關專案」
- 參數：controller (控制器型號，如 SM2264、SM2269XT)

### 3. query_project_detail - 查詢專案詳細資訊
用戶想了解某個特定專案的詳細資訊時使用。
- 常見問法：
  - 「XX 專案的詳細資訊」「告訴我 XX 專案」
  - 「XX 專案是什麼」「查詢 XX 專案」「XX 專案的資訊」
  - 「介紹一下 XX 專案」「XX 專案的狀況」
- 參數：project_name (專案名稱)

### 4. query_project_summary - 查詢專案基本摘要（僅限專案資訊）
【注意】此意圖僅用於查詢專案的基本資訊摘要，不涉及測試結果。
- 使用場景：用戶詢問專案概況、專案介紹、專案基本情況
- 常見問法：
  - 「XX 專案概況」「介紹 XX 專案」「XX 專案摘要」
- 參數：project_name (專案名稱)
- 【重要】如果問題涉及「測試」、「Pass」、「Fail」、「通過」、「失敗」等字眼，應使用 query_project_test_summary

### 5. query_project_test_summary - 查詢專案測試結果統計（推薦使用）
【預設使用】任何與「測試結果」相關的查詢都應使用此意圖。
用戶想了解專案測試結果、測試狀況、測試進度、Pass/Fail 統計時使用。
- 常見問法：
  - 「XX 的測試結果」「XX 測試狀況」「XX 的測試進度」
  - 「XX 有多少測試通過」「XX 有多少測試失敗」
  - 「XX 的 Pass/Fail 統計」「XX 專案測試報告」
  - 「XX 測試結果如何」「XX 測試狀態」「XX 測試怎麼樣」
  - 「查看 XX 專案的測試結果」「XX 測試結果總覽」
  - 「想了解 XX 測試跑得怎麼樣」
  - 「What's the test status of XX?」「XX test results」
- 參數：project_name (專案名稱)
- 【重要】只要問題包含「測試結果」、「測試狀況」、「測試進度」等，就應優先使用此意圖

### 6. query_project_test_by_category - 按類別查詢測試結果
用戶想了解某個專案在特定測試類別的結果時使用。
- 常見問法：
  - 「XX 專案的 Compliance 測試結果」「XX 的功能測試」
  - 「XX 專案 Performance 測試怎麼樣」「XX 的效能測試結果」
  - 「XX 的 Interoperability 測試」「XX 互通性測試狀況」
  - 「XX 專案 Stress 測試結果」「XX 的壓力測試」
  - 「XX 的相容性測試」「XX 的 Compatibility 測試」
- 參數：project_name (專案名稱), category (測試類別)
- 【類別對應】中文 → 英文：
  - 功能測試 → Functionality
  - 效能測試 → Performance
  - 壓力測試 → Stress
  - 相容性測試/相容測試 → Compatibility
  - 互通性測試 → Interoperability
  - 合規測試 → Compliance

### 7. query_project_test_by_capacity - 按容量查詢測試結果
用戶想了解某個專案在特定容量規格的測試結果時使用。
- 常見問法：
  - 「XX 專案 1TB 的測試結果」「XX 的 512GB 測試」
  - 「XX 專案 2TB 版本測試怎麼樣」「XX 256GB 測試狀況」
  - 「查看 XX 的 4TB 測試結果」「XX 128GB 測試」
  - 「想看 XX 一T版本的測試」（一T = 1TB）
- 參數：project_name (專案名稱), capacity (容量規格: 128GB/256GB/512GB/1TB/2TB/4TB/8TB)
- 【口語對應】一T/1T → 1TB, 二T/2T → 2TB, 半T → 512GB

### 8. query_project_test_summary_by_fw - 按 FW 版本查詢測試結果 (Phase 4 新增)
用戶想了解專案特定 FW（韌體）版本的測試結果時使用。
- 常見問法：
  - 「XX 專案 FW YYY 的測試結果」
  - 「XX 的 YYY 版本測試狀況」
  - 「查看 XX 專案 FW YYY 的 Pass/Fail」
  - 「XX YYY 版本有多少測試通過？」
  - 「XX 專案韌體 YYY 的測試進度」
  - 「想看 XX 的 FW YYY 測試結果」
- 參數：
  - project_name (專案名稱，如 DEMETER、Channel、A400)
  - fw_version (FW 版本號，如 Y1114B、82CBW5QF、X0325A、FWX0926C)
- 【重要】此意圖用於指定 FW 版本的查詢
- 【區分】如果用戶沒有指定 FW 版本，請使用 query_project_test_summary

### 9. compare_fw_versions - 比較兩個指定的 FW 版本 (Phase 5.1)
用戶想比較同一專案中兩個不同 FW 版本的測試結果時使用。
- 常見問法：
  - 「XX 專案的 YYY 和 ZZZ 比較」
  - 「比較 XX 專案 FW YYY 和 ZZZ 的測試結果」
  - 「XX 的 YYY 版本跟 ZZZ 版本差異」
  - 「XX 專案 FW YYY vs ZZZ」
  - 「XX 的 YYY 和 ZZZ 哪個測試結果比較好」
  - 「對比 XX 專案韌體 YYY 和 ZZZ」
- 參數：
  - project_name (專案名稱，如 DEMETER、Channel、A400)
  - fw_version_1 (第一個 FW 版本號)
  - fw_version_2 (第二個 FW 版本號)
- 【重要】必須提供兩個 FW 版本才能進行比較
- 【區分】如果只有一個 FW 版本，請使用 query_project_test_summary_by_fw

### 10. compare_latest_fw - 自動比較最新兩個 FW 版本 (Phase 5.2 新增)
用戶想比較專案的 FW 版本，但沒有指定具體版本名稱時使用。
系統會自動選擇最新/最活躍的兩個版本進行比較。
- 常見問法：
  - 「XX 最新的 FW 比較」「XX 專案最新版本比較」
  - 「比較 XX 最近兩個版本」「XX 的 FW 進度比較」
  - 「看一下 XX 最新版本差異」「XX 最新 FW 測試差異」
  - 「XX 專案 FW 更新比較」「比較 XX 最新韌體」
  - 「XX 版本演進比較」「XX 的 FW 變化」
- 參數：
  - project_name (專案名稱，如 DEMETER、Springsteen、Channel)
- 【重要】此意圖用於用戶沒有指定具體 FW 版本時
- 【區分】
  - 如果用戶指定了兩個具體 FW 版本 → 使用 compare_fw_versions
  - 如果用戶說「最新」「最近」「版本比較」但沒有版本號 → 使用 compare_latest_fw

### 11. list_fw_versions - 列出專案可比較的 FW 版本 (Phase 5.2 新增)
用戶想知道專案有哪些 FW 版本可以比較或查詢時使用。
- 常見問法：
  - 「XX 有哪些 FW 版本」「XX 專案的版本列表」
  - 「列出 XX 的所有 FW」「XX 可以比較哪些版本」
  - 「XX 專案有幾個 FW」「查看 XX 的韌體版本」
  - 「XX 的 FW 版本有哪些」「顯示 XX 版本」
  - 「XX 有什麼版本可以查」「XX FW 清單」
- 參數：
  - project_name (專案名稱，如 DEMETER、Springsteen、Channel)
- 【重要】此意圖用於查詢版本列表，不是比較
- 【區分】
  - 如果用戶問「有哪些版本」「版本列表」「幾個版本」 → 使用 list_fw_versions
  - 如果用戶問「比較」但沒指定版本 → 使用 compare_latest_fw

### 12. compare_multiple_fw - 比較多個 FW 版本趨勢 (Phase 5.4 新增)
用戶想比較專案的三個或更多 FW 版本的趨勢變化時使用。
- 常見問法：
  - 「XX 專案的 A、B、C 三個版本比較」「比較 XX 的多個 FW 版本」
  - 「XX 最近三個版本的趨勢」「XX 最近 5 個 FW 版本的比較」
  - 「XX 專案 FW A、B、C、D 的測試趨勢」「分析 XX 最近幾版的變化」
  - 「看一下 XX 版本演進趨勢」「XX 專案 FW 趨勢分析」
  - 「XX 的 V1、V2、V3 版本比較」「XX 多版本對比」
  - 「比較 XX 的 FW 版本 A, B 和 C」「XX 版本趨勢圖」
  - 「XX AA 版本最近三個 FW 比較」「XX 512GB 版本趨勢」
- 參數：
  - project_name (專案名稱，如 Springsteen、DEMETER、Channel)
  - fw_versions (選填，FW 版本列表，如 ["A", "B", "C"]，至少 3 個)
  - latest_count (選填，自動取最近 N 個版本，如 3、5)
  - sub_version (選填，SubVersion/容量版本代碼，如 AA、AB、AC、AD)
- 【SubVersion 說明】：
  - AA = 512GB 版本
  - AB = 1024GB 版本
  - AC = 2048GB 版本
  - AD = 4096GB 版本
  - 用戶可能直接說「AA」「AB」或「512GB」「1024GB」等
- 【重要】此意圖用於 3 個或更多版本的趨勢比較
- 【區分】
  - 如果用戶指定了兩個具體 FW 版本 → 使用 compare_fw_versions
  - 如果用戶說「最新兩個」「最近兩個」→ 使用 compare_latest_fw
  - 如果用戶說「三個版本」「多個版本」「最近幾個」「趨勢」→ 使用 compare_multiple_fw

### 13. query_fw_detail_summary - 查詢 FW 詳細統計 (Phase 6.2 新增)
用戶想了解專案特定 FW 版本的整體統計指標時使用。
此意圖提供：完成率、通過率、樣本使用率、執行率、失敗率等詳細統計。
- 常見問法：
  - 「XX 專案 FW YYY 的詳細統計」「XX YYY 版本的統計資訊」
  - 「XX 專案 FW YYY 的完成率是多少」「XX YYY 進度如何」
  - 「XX 專案 FW YYY 使用了多少樣本」「XX YYY 樣本使用率」
  - 「XX 專案 FW YYY 的執行率」「XX YYY 失敗率多少」
  - 「XX 專案 FW YYY 測試概覽」「XX YYY 總覽」
  - 「XX 專案 FW YYY 的通過率」「XX YYY 測試進度」
- 參數：
  - project_name (專案名稱，如 Springsteen、DEMETER)
  - fw_version (FW 版本號，如 G200X6EC、Y1114B)
- 【重要】此意圖用於獲取整體統計指標，而非按類別或容量的 Pass/Fail 明細
- 【區分】
  - 如果用戶問「測試結果」「Pass/Fail」「哪些通過/失敗」→ 使用 query_project_test_summary_by_fw
  - 如果用戶問「統計」「完成率」「進度」「樣本」「使用率」「執行率」→ 使用 query_fw_detail_summary

### 14. query_projects_by_pl - 按專案負責人查詢專案 (Phase 7 新增)
用戶想知道某位專案負責人（PL / Project Leader）負責哪些專案時使用。
- 常見問法：
  - 「Ryder 負責哪些專案」「ryder.lin 的專案」
  - 「Jeffery 管理的專案有哪些」「查詢 PL 是 Wei-Zhen 的專案」
  - 「哪些專案是 bruce.zhang 負責的」「列出 Zhenyuan 的專案」
  - 「XX 的專案有哪些」（當 XX 是人名時）
  - 「專案負責人是 XX 的專案」「誰負責 XX 專案」
- 參數：pl (專案負責人名稱)
- 【重要區分】
  - 如果名稱是公司名（WD, Samsung）→ 使用 query_projects_by_customer
  - 如果名稱是人名（Ryder, Jeffery, ryder.lin）→ 使用 query_projects_by_pl
- 已知 PL 名稱：Ryder, ryder.lin, Jeffery, jeffery.kuo, bruce.zhang, Wei-Zhen, Zhenyuan

### 15. count_projects - 統計專案數量
用戶想知道專案數量時使用。
- 常見問法：
  - 「有多少專案」「幾個專案」「專案數量」「總共多少專案」
  - 「XX 有多少專案」「XX 有幾個專案」「XX 專案數」
  - 「統計專案數量」「專案總數」
- 參數：customer (可選，若指定特定客戶)

### 16. list_all_customers - 列出所有客戶
用戶想知道系統中有哪些客戶時使用。
- 常見問法：
  - 「有哪些客戶」「客戶列表」「列出所有客戶」
  - 「系統裡有什麼客戶」「支援哪些客戶」「客戶有誰」
- 參數：無

### 17. list_all_controllers - 列出所有控制器
用戶想知道系統中有哪些控制器型號時使用。
- 常見問法：
  - 「有哪些控制器」「控制器列表」「列出所有控制器」
  - 「支援哪些控制器型號」「可以查詢哪些控制器」
- 參數：無

### 18. query_projects_by_month - 按月份查詢專案 (Phase 8 新增)
用戶想知道特定月份有哪些專案轉入/建立時使用。
- 常見問法：
  - 「2025年12月有哪些專案」「2025/12 的案子」「12月有幾個專案」
  - 「本月有哪些轉案」「這個月新增的專案」「當月的專案」
  - 「上個月轉進的案子」「上月的專案」
  - 「幾月轉進的案子」「12月建立的專案」
- 參數：
  - year (選填，年份，如 2025，不填則為當年)
  - month (月份，1-12)
  - date_range (選填，'this_month' 或 'last_month')
- 【區分】
  - 如果指定具體月份 → 使用 query_projects_by_month
  - 如果只指定年份不指定月份 → 使用 query_projects_by_date

### 19. query_projects_by_date - 按年份/日期範圍查詢專案 (Phase 8 新增)
用戶想知道特定年份或日期範圍內有哪些專案時使用。
- 常見問法：
  - 「今年有哪些專案」「2025年的專案」「今年轉進幾個案子」
  - 「2024年建立的專案」「去年的案子」
- 參數：
  - year (年份，如 2025)
  - date_range (選填，'this_year' 表示今年)
- 【區分】
  - 如果只指定年份 → 使用 query_projects_by_date
  - 如果指定具體月份 → 使用 query_projects_by_month

### 20. list_sub_versions - 列出專案所有 Sub Version (Phase 9 新增)
用戶想知道某專案有哪些容量版本（Sub Version）時使用。
Sub Version 是指專案的不同容量變體，如 AA=512GB, AB=1024GB, AC=2048GB, AD=4096GB。
- 常見問法：
  - 「Springsteen 有哪幾版 sub version」「Springsteen 有哪些容量版本」
  - 「DEMETER 的 sub version 有哪些」「Channel 有幾個容量版本」
  - 「XX 專案有哪些版本（AA/AB/AC/AD）」「列出 XX 的 SubVersion」
  - 「XX 有哪些 sub version」「XX 的容量版本」
- 參數：
  - project_name (專案名稱，如 Springsteen、DEMETER)
- 【區分】
  - 如果用戶問「有哪些 FW 版本」→ 使用 list_fw_versions
  - 如果用戶問「有哪些 sub version / 容量版本 / AA/AB/AC/AD」→ 使用 list_sub_versions

### 21. list_fw_by_sub_version - 列出特定 Sub Version 的 FW 版本 (Phase 9 新增)
用戶想知道某專案特定容量版本下有哪些 FW 時使用。
- 常見問法：
  - 「Springsteen AC 有哪些 FW」「Springsteen 2048GB 版本的 FW」
  - 「DEMETER AA 有幾個 FW」「Channel AB 版本的韌體列表」
  - 「XX 專案 AC 版本有哪些韌體版本」「列出 XX AA 的 FW」
  - 「XX 512GB 有哪些 FW 版本」「XX 1TB 版本的韌體」
- 參數：
  - project_name (專案名稱)
  - sub_version (Sub Version 代碼，如 AA、AB、AC、AD，或容量如 512GB、1024GB)
- 【SubVersion 與容量對應】：
  - AA = 512GB
  - AB = 1024GB / 1TB
  - AC = 2048GB / 2TB
  - AD = 4096GB / 4TB
- 【重要】
  - 用戶可能直接說 AA/AB/AC/AD，也可能說 512GB/1024GB/2048GB/4096GB
  - 需要正確識別並提取 sub_version 參數

### 22. query_projects_by_test_category - 跨專案測試類別搜尋 (Phase 10 新增)
用戶想知道哪些專案有執行過特定測試類別時使用。
這是跨專案的搜尋功能，會搜尋所有專案並返回包含該測試類別的專案列表。
- 常見問法：
  - 「哪些案子有測試過 PCIe CV5」「哪些專案做過 Performance 測試」
  - 「有做過 NVMe 測試的專案有哪些」「哪些專案測過 OAKGATE」
  - 「找出所有測試過 MANDi 的專案」「有跑過 CrystalDiskMark 的案子」
  - 「哪些產品有做過 Compatibility 測試」「哪些專案完成了 USB4 認證」
  - 「列出有 SATA 測試的案子」「哪些專案有 Functionality 測試」
  - 「有 Performance 測試的專案」「做過效能測試的案子」
- 參數：
  - test_category (測試類別名稱，如 PCIe、NVMe、Performance、OAKGATE、MANDi)
  - customer (選填，限定特定客戶)
  - status_filter (選填，'pass' 只找有通過的、'fail' 只找有失敗的、'all' 全部)
- 【重要區分】
  - 如果用戶說「XX 專案的 Performance 測試結果」→ 使用 query_project_test_by_category（單一專案）
  - 如果用戶說「哪些案子有做過 Performance 測試」→ 使用 query_projects_by_test_category（跨專案搜尋）
  - 關鍵判斷：是否有指定「專案名稱」
    - 有專案名稱 → 單一專案查詢
    - 無專案名稱，問「哪些專案」→ 跨專案搜尋
- 【測試類別對應】：
  - PCIe / PCIe CV5 → PCIe
  - NVMe / NVMe Validation → NVMe_Validation_Tool
  - 效能 / Performance → Performance
  - 功能 / Functionality → Functionality
  - 相容性 / Compatibility → Compatibility

### 23. query_project_fw_test_categories - 專案 FW 測試類別查詢 (Phase 11 新增)
用戶想知道某個專案的特定 FW 版本有哪些測試類別時使用。
這是單一專案內的查詢，返回該 FW 版本下的所有測試類別列表及統計。
- 常見問法：
  - 「DEMETER 的 Y1114B FW 有哪些測試類別」
  - 「XX 專案 512GB 版本有哪些 Category」
  - 「這個案子 1024GB 的 FW 有什麼測試」
  - 「Project Alpha 的 FW v2.1 包含哪些測試類別」
  - 「XX 專案這個 FW 做了哪些測試」
  - 「某案子某版本的測試類別清單」
- 參數：
  - project_name (專案名稱，必須)
  - fw_version (FW 版本，必須，可以是版本號如 Y1114B，或容量如 512GB)
- 【重要區分】
  - 如果用戶說「DEMETER 的測試結果」→ 使用 query_project_test_summary（查詢測試結果）
  - 如果用戶說「DEMETER 的 Y1114B 有哪些測試類別」→ 使用 query_project_fw_test_categories（查詢類別清單）
  - 如果用戶說「哪些案子有做過 Performance」→ 使用 query_projects_by_test_category（跨專案搜尋）
  - 關鍵判斷：
    - 有專案名稱 + 有 FW 版本 + 問「有哪些類別」→ query_project_fw_test_categories
    - 有專案名稱 + 無 FW 版本 → query_project_test_summary
    - 無專案名稱 + 問「哪些專案」→ query_projects_by_test_category

### 24. query_project_fw_category_test_items - 專案 FW 類別測項查詢 (Phase 12 新增)
用戶想知道某個專案特定 FW 版本的特定測試類別有哪些測試項目（Test Items）時使用。
這是查詢單一類別內的詳細測試項目列表。
- 常見問法：
  - 「Springsteen GD10YBJD_Opal Functionality 類別有哪些測項」
  - 「DEMETER 的 Y1114B 的 NVMe_Validation_Tool 有什麼測試項目」
  - 「XX 專案 512GB 版本 Performance 類別有哪些測項」
  - 「這個案子 1024GB 的 MANDi 測試包含哪些項目」
  - 「XX 專案 FW YYY 的 Reliability 測試有哪些測項」
  - 「某案子某版本的 Protocol 類別測試項目清單」
- 參數：
  - project_name (專案名稱，必須)
  - fw_version (FW 版本，必須，如 GD10YBJD_Opal、Y1114B)
  - category_name (測試類別名稱，必須，如 Functionality、Performance、MANDi、Protocol)
- 【重要區分】
  - 如果用戶說「XX FW YYY 有哪些測試類別」→ 使用 query_project_fw_test_categories（查詢類別清單）
  - 如果用戶說「XX FW YYY 的 Functionality 類別有哪些測項」→ 使用 query_project_fw_category_test_items（查詢特定類別的測項）
  - 如果用戶說「XX FW YYY 有哪些測項」（沒有指定類別）→ 使用 query_project_fw_all_test_items（查詢全部測項）
  - 關鍵判斷：
    - 有專案名稱 + 有 FW 版本 + 有類別名稱 + 問「有哪些測項」→ query_project_fw_category_test_items
    - 有專案名稱 + 有 FW 版本 + 無類別名稱 + 問「有哪些測項」→ query_project_fw_all_test_items
    - 有專案名稱 + 有 FW 版本 + 問「有哪些類別」→ query_project_fw_test_categories

### 25. query_project_fw_all_test_items - 專案 FW 全部測項查詢 (Phase 12 新增)
用戶想知道某個專案特定 FW 版本的所有測試項目（Test Items）時使用。
這是查詢該 FW 版本下所有類別的全部測試項目，按類別分組顯示。
- 常見問法：
  - 「Springsteen GD10YBJD_Opal 有哪些測項」
  - 「DEMETER 的 Y1114B 有哪些測試項目」
  - 「XX 專案 512GB 版本的全部測項」
  - 「這個案子 1024GB 有什麼測試項目」
  - 「XX 專案 FW YYY 總共有哪些測試項目」
  - 「列出某案子某版本的所有測項」
- 參數：
  - project_name (專案名稱，必須)
  - fw_version (FW 版本，必須，如 GD10YBJD_Opal、Y1114B)
- 【重要區分】
  - 如果用戶說「XX FW YYY 有哪些測試類別」→ 使用 query_project_fw_test_categories（查詢類別清單）
  - 如果用戶說「XX FW YYY 有哪些測項」（沒有指定類別）→ 使用 query_project_fw_all_test_items（查詢全部測項）
  - 如果用戶說「XX FW YYY 的 Functionality 類別有哪些測項」→ 使用 query_project_fw_category_test_items（查詢特定類別的測項）
  - 關鍵判斷：
    - 問「有哪些測項」或「有哪些測試項目」且沒有指定類別 → query_project_fw_all_test_items
    - 問「有哪些測項」或「有哪些測試項目」且有指定類別 → query_project_fw_category_test_items
    - 問「有哪些類別」或「有什麼測試」→ query_project_fw_test_categories

### 26. list_fw_by_date_range - 按日期範圍查詢專案 FW 版本 (Phase 13 新增)
用戶想知道某專案在特定日期範圍內有哪些 FW 版本時使用。
這是查詢專案在指定時間段內發布的 FW 版本列表。
- 常見問法：
  - 「Springsteen 12月有哪些 FW」「Springsteen 這個月有幾個 FW 版本」
  - 「DEMETER 本月的 FW」「DEMETER 上個月有哪些韌體版本」
  - 「XX 專案 2025年1月的 FW 版本」「XX 今年有哪些 FW」
  - 「Springsteen 最近有哪些 FW」「DEMETER 近期的韌體」
  - 「XX 專案 10月到12月的 FW」「XX 上半年的 FW 版本」
  - 「這個月 XX 有發布什麼 FW」「上週 XX 有新的 FW 嗎」
  - 「Springsteen AC 2025年有哪些 FW」「DEMETER AA 本月的 FW」（同時指定 Sub Version 和日期）
  - 「Channel AB 12月的韌體版本」「XX 專案 AC 版本今年的 FW」
- 參數：
  - project_name (專案名稱，必須)
  - year (選填，年份，如 2025)
  - month (選填，月份，1-12)
  - start_month (選填，開始月份，用於範圍查詢)
  - end_month (選填，結束月份，用於範圍查詢)
  - date_range (選填，'this_month'、'last_month'、'this_week'、'last_week'、'recent')
  - sub_version (選填，Sub Version 代碼如 AA、AB、AC、AD)
- 【重要區分】
  - 如果用戶問「XX 有哪些 FW 版本」（無日期）→ 使用 list_fw_versions（列出所有 FW）
  - 如果用戶問「XX 12月有哪些 FW」或「XX 本月的 FW」→ 使用 list_fw_by_date_range（按日期過濾）
  - 如果用戶問「12月有哪些專案」（無專案名稱）→ 使用 query_projects_by_month（查詢專案）
  - 如果用戶問「XX AC 2025年有哪些 FW」→ 使用 list_fw_by_date_range（同時帶 sub_version 和 year）
  - 關鍵判斷：
    - 有專案名稱 + 有日期/月份/年份 + 問「有哪些 FW」→ list_fw_by_date_range
    - 有專案名稱 + 無日期 + 問「有哪些 FW」→ list_fw_versions
    - 無專案名稱 + 有月份 + 問「有哪些專案」→ query_projects_by_month
    - 有專案名稱 + 有 Sub Version + 有日期/年份 → list_fw_by_date_range（帶 sub_version）

### 27. unknown - 無法識別的意圖
當問題與 SAF 專案管理系統無關時使用。

## 已知資訊

客戶名稱：WD, WDC, Western Digital, Samsung, Micron, Transcend, ADATA, UMIS, Biwin, Kioxia, SK Hynix
控制器型號：SM2263, SM2264, SM2267, SM2269, SM2264XT, SM2269XT, SM2508
測試類別：PCIe, NVMe, Performance, OAKGATE, MANDi, Functionality, Compatibility, USB4, SATA, CrystalDiskMark
容量規格：128GB, 256GB, 512GB, 1TB, 2TB, 4TB, 8TB
專案負責人 (PL)：Ryder, ryder.lin, Jeffery, jeffery.kuo, bruce.zhang, Wei-Zhen, Zhenyuan
Sub Version 代碼：AA (512GB), AB (1024GB/1TB), AC (2048GB/2TB), AD (4096GB/4TB)

## 輸出格式

{"intent": "意圖ID", "parameters": {}, "confidence": 0.0-1.0}

## 範例（注意各種不同的問法都應該正確識別）

輸入：WD 有哪些專案？
輸出：{"intent": "query_projects_by_customer", "parameters": {"customer": "WD"}, "confidence": 0.95}

輸入：列出 Samsung 的專案
輸出：{"intent": "query_projects_by_customer", "parameters": {"customer": "Samsung"}, "confidence": 0.93}

輸入：SM2264 控制器用在哪些專案？
輸出：{"intent": "query_projects_by_controller", "parameters": {"controller": "SM2264"}, "confidence": 0.95}

輸入：哪些專案使用 SM2269XT
輸出：{"intent": "query_projects_by_controller", "parameters": {"controller": "SM2269XT"}, "confidence": 0.93}

輸入：那些專案使用 SM2508
輸出：{"intent": "query_projects_by_controller", "parameters": {"controller": "SM2508"}, "confidence": 0.92}

輸入：SM2267 的專案有哪些
輸出：{"intent": "query_projects_by_controller", "parameters": {"controller": "SM2267"}, "confidence": 0.90}

輸入：用 SM2264 的專案
輸出：{"intent": "query_projects_by_controller", "parameters": {"controller": "SM2264"}, "confidence": 0.88}

輸入：總共有多少專案？
輸出：{"intent": "count_projects", "parameters": {}, "confidence": 0.95}

輸入：Samsung 有幾個專案？
輸出：{"intent": "count_projects", "parameters": {"customer": "Samsung"}, "confidence": 0.93}

輸入：WD 專案數量
輸出：{"intent": "count_projects", "parameters": {"customer": "WD"}, "confidence": 0.90}

輸入：DEMETER 專案的詳細資訊
輸出：{"intent": "query_project_detail", "parameters": {"project_name": "DEMETER"}, "confidence": 0.92}

輸入：查詢 APOLLO 專案
輸出：{"intent": "query_project_detail", "parameters": {"project_name": "APOLLO"}, "confidence": 0.88}

輸入：DEMETER 的測試結果如何？
輸出：{"intent": "query_project_test_summary", "parameters": {"project_name": "DEMETER"}, "confidence": 0.95}

輸入：Garuda 專案測試狀況如何
輸出：{"intent": "query_project_test_summary", "parameters": {"project_name": "Garuda"}, "confidence": 0.95}

輸入：PHOENIX 專案的測試進度
輸出：{"intent": "query_project_test_summary", "parameters": {"project_name": "PHOENIX"}, "confidence": 0.93}

輸入：想了解一下 VULCAN 測試跑得怎麼樣
輸出：{"intent": "query_project_test_summary", "parameters": {"project_name": "VULCAN"}, "confidence": 0.92}

輸入：What's the test status of DEMETER?
輸出：{"intent": "query_project_test_summary", "parameters": {"project_name": "DEMETER"}, "confidence": 0.93}

輸入：TITAN 的測試結果
輸出：{"intent": "query_project_test_summary", "parameters": {"project_name": "TITAN"}, "confidence": 0.95}

輸入：APOLLO 專案的測試結果統計
輸出：{"intent": "query_project_test_summary", "parameters": {"project_name": "APOLLO"}, "confidence": 0.95}

輸入：查看 DEMETER 的測試報告
輸出：{"intent": "query_project_test_summary", "parameters": {"project_name": "DEMETER"}, "confidence": 0.93}

輸入：TITAN 有多少測試通過
輸出：{"intent": "query_project_test_summary", "parameters": {"project_name": "TITAN"}, "confidence": 0.92}

輸入：APOLLO 專案的 Compliance 測試結果
輸出：{"intent": "query_project_test_by_category", "parameters": {"project_name": "APOLLO", "category": "Compliance"}, "confidence": 0.95}

輸入：DEMETER 的 Performance 測試怎麼樣
輸出：{"intent": "query_project_test_by_category", "parameters": {"project_name": "DEMETER", "category": "Performance"}, "confidence": 0.93}

輸入：TITAN 的功能測試結果
輸出：{"intent": "query_project_test_by_category", "parameters": {"project_name": "TITAN", "category": "Functionality"}, "confidence": 0.90}

輸入：APOLLO 專案 1TB 的測試結果
輸出：{"intent": "query_project_test_by_capacity", "parameters": {"project_name": "APOLLO", "capacity": "1TB"}, "confidence": 0.95}

輸入：DEMETER 的 512GB 測試狀況
輸出：{"intent": "query_project_test_by_capacity", "parameters": {"project_name": "DEMETER", "capacity": "512GB"}, "confidence": 0.93}

輸入：查看 TITAN 2TB 版本的測試
輸出：{"intent": "query_project_test_by_capacity", "parameters": {"project_name": "TITAN", "capacity": "2TB"}, "confidence": 0.92}

輸入：VULCAN 128GB 的測試狀況
輸出：{"intent": "query_project_test_by_capacity", "parameters": {"project_name": "VULCAN", "capacity": "128GB"}, "confidence": 0.93}

輸入：APOLLO 的相容性測試結果
輸出：{"intent": "query_project_test_by_category", "parameters": {"project_name": "APOLLO", "category": "Compatibility"}, "confidence": 0.93}

輸入：TITAN 的相容測試做得如何？
輸出：{"intent": "query_project_test_by_category", "parameters": {"project_name": "TITAN", "category": "Compatibility"}, "confidence": 0.93}

輸入：PHOENIX 的功能測試結果如何
輸出：{"intent": "query_project_test_by_category", "parameters": {"project_name": "PHOENIX", "category": "Functionality"}, "confidence": 0.93}

輸入：DEMETER 專案 FW Y1114B 的測試結果
輸出：{"intent": "query_project_test_summary_by_fw", "parameters": {"project_name": "DEMETER", "fw_version": "Y1114B"}, "confidence": 0.95}

輸入：Channel 的 82CBW5QF 版本測試狀況
輸出：{"intent": "query_project_test_summary_by_fw", "parameters": {"project_name": "Channel", "fw_version": "82CBW5QF"}, "confidence": 0.93}

輸入：A400 專案 X0325A 的測試結果如何
輸出：{"intent": "query_project_test_summary_by_fw", "parameters": {"project_name": "A400", "fw_version": "X0325A"}, "confidence": 0.93}

輸入：想看一下 Frey3B 的 FWX0926C 測試結果
輸出：{"intent": "query_project_test_summary_by_fw", "parameters": {"project_name": "Frey3B", "fw_version": "FWX0926C"}, "confidence": 0.90}

輸入：Bennington 專案韌體 Y1103C 有多少測試通過
輸出：{"intent": "query_project_test_summary_by_fw", "parameters": {"project_name": "Bennington", "fw_version": "Y1103C"}, "confidence": 0.90}

輸入：Springsteen 專案 G200X6EC 的測試結果
輸出：{"intent": "query_project_test_summary_by_fw", "parameters": {"project_name": "Springsteen", "fw_version": "G200X6EC"}, "confidence": 0.92}

輸入：DEMETER 專案的 Y1114B 和 Y1114A 比較
輸出：{"intent": "compare_fw_versions", "parameters": {"project_name": "DEMETER", "fw_version_1": "Y1114B", "fw_version_2": "Y1114A"}, "confidence": 0.95}

輸入：比較 Channel 專案 FW 82CBW5QF 和 82CBW4QE 的測試結果
輸出：{"intent": "compare_fw_versions", "parameters": {"project_name": "Channel", "fw_version_1": "82CBW5QF", "fw_version_2": "82CBW4QE"}, "confidence": 0.95}

輸入：A400 的 X0325A 版本跟 X0324B 版本差異
輸出：{"intent": "compare_fw_versions", "parameters": {"project_name": "A400", "fw_version_1": "X0325A", "fw_version_2": "X0324B"}, "confidence": 0.93}

輸入：DEMETER FW Y1114B vs Y1114A
輸出：{"intent": "compare_fw_versions", "parameters": {"project_name": "DEMETER", "fw_version_1": "Y1114B", "fw_version_2": "Y1114A"}, "confidence": 0.92}

輸入：Frey3B 的 FWX0926C 和 FWX0925B 哪個測試結果比較好
輸出：{"intent": "compare_fw_versions", "parameters": {"project_name": "Frey3B", "fw_version_1": "FWX0926C", "fw_version_2": "FWX0925B"}, "confidence": 0.90}

輸入：對比 Bennington 專案韌體 Y1103C 和 Y1102B
輸出：{"intent": "compare_fw_versions", "parameters": {"project_name": "Bennington", "fw_version_1": "Y1103C", "fw_version_2": "Y1102B"}, "confidence": 0.90}

輸入：Springsteen 最新的 FW 比較
輸出：{"intent": "compare_latest_fw", "parameters": {"project_name": "Springsteen"}, "confidence": 0.95}

輸入：比較 DEMETER 最近兩個版本
輸出：{"intent": "compare_latest_fw", "parameters": {"project_name": "DEMETER"}, "confidence": 0.93}

輸入：Channel 的 FW 進度比較
輸出：{"intent": "compare_latest_fw", "parameters": {"project_name": "Channel"}, "confidence": 0.90}

輸入：看一下 A400 最新版本差異
輸出：{"intent": "compare_latest_fw", "parameters": {"project_name": "A400"}, "confidence": 0.92}

輸入：Bennington 專案 FW 更新比較
輸出：{"intent": "compare_latest_fw", "parameters": {"project_name": "Bennington"}, "confidence": 0.90}

輸入：Springsteen 版本演進比較
輸出：{"intent": "compare_latest_fw", "parameters": {"project_name": "Springsteen"}, "confidence": 0.88}

輸入：DEMETER 有哪些 FW 版本
輸出：{"intent": "list_fw_versions", "parameters": {"project_name": "DEMETER"}, "confidence": 0.95}

輸入：列出 Springsteen 的所有 FW
輸出：{"intent": "list_fw_versions", "parameters": {"project_name": "Springsteen"}, "confidence": 0.93}

輸入：Channel 可以比較哪些版本
輸出：{"intent": "list_fw_versions", "parameters": {"project_name": "Channel"}, "confidence": 0.90}

輸入：A400 專案有幾個 FW
輸出：{"intent": "list_fw_versions", "parameters": {"project_name": "A400"}, "confidence": 0.92}

輸入：查看 Bennington 的韌體版本
輸出：{"intent": "list_fw_versions", "parameters": {"project_name": "Bennington"}, "confidence": 0.90}

輸入：Frey3B 的 FW 版本有哪些
輸出：{"intent": "list_fw_versions", "parameters": {"project_name": "Frey3B"}, "confidence": 0.92}

輸入：顯示 TITAN 版本
輸出：{"intent": "list_fw_versions", "parameters": {"project_name": "TITAN"}, "confidence": 0.88}

輸入：比較 Springsteen 的 G200X6EC、G200X5DC、G200X4CB 三個版本
輸出：{"intent": "compare_multiple_fw", "parameters": {"project_name": "Springsteen", "fw_versions": ["G200X6EC", "G200X5DC", "G200X4CB"]}, "confidence": 0.95}

輸入：DEMETER 最近三個版本的趨勢
輸出：{"intent": "compare_multiple_fw", "parameters": {"project_name": "DEMETER", "latest_count": 3}, "confidence": 0.93}

輸入：Channel 專案 FW A、B、C、D 的測試趨勢
輸出：{"intent": "compare_multiple_fw", "parameters": {"project_name": "Channel", "fw_versions": ["A", "B", "C", "D"]}, "confidence": 0.95}

輸入：分析 A400 最近 5 個版本的變化
輸出：{"intent": "compare_multiple_fw", "parameters": {"project_name": "A400", "latest_count": 5}, "confidence": 0.92}

輸入：Springsteen AA 版本最近三個 FW 趨勢
輸出：{"intent": "compare_multiple_fw", "parameters": {"project_name": "Springsteen", "latest_count": 3, "sub_version": "AA"}, "confidence": 0.94}

輸入：Springsteen AA 的 G200X8CA、G200X82B、G200X5HB 比較
輸出：{"intent": "compare_multiple_fw", "parameters": {"project_name": "Springsteen", "fw_versions": ["G200X8CA", "G200X82B", "G200X5HB"], "sub_version": "AA"}, "confidence": 0.95}

輸入：Channel AB 1024GB 版本最近三個 FW 比較
輸出：{"intent": "compare_multiple_fw", "parameters": {"project_name": "Channel", "latest_count": 3, "sub_version": "AB"}, "confidence": 0.93}

輸入：Springsteen 512GB 版本 FW 趨勢
輸出：{"intent": "compare_multiple_fw", "parameters": {"project_name": "Springsteen", "latest_count": 3, "sub_version": "AA"}, "confidence": 0.92}

輸入：看一下 Frey3B 版本演進趨勢
輸出：{"intent": "compare_multiple_fw", "parameters": {"project_name": "Frey3B", "latest_count": 3}, "confidence": 0.90}

輸入：Bennington 專案 FW 趨勢分析
輸出：{"intent": "compare_multiple_fw", "parameters": {"project_name": "Bennington", "latest_count": 3}, "confidence": 0.90}

輸入：TITAN 多版本對比
輸出：{"intent": "compare_multiple_fw", "parameters": {"project_name": "TITAN", "latest_count": 3}, "confidence": 0.88}

輸入：比較 VULCAN 的 V1、V2、V3 版本
輸出：{"intent": "compare_multiple_fw", "parameters": {"project_name": "VULCAN", "fw_versions": ["V1", "V2", "V3"]}, "confidence": 0.92}

輸入：Springsteen 專案 G200X6EC 的詳細統計
輸出：{"intent": "query_fw_detail_summary", "parameters": {"project_name": "Springsteen", "fw_version": "G200X6EC"}, "confidence": 0.95}

輸入：DEMETER FW Y1114B 的完成率是多少
輸出：{"intent": "query_fw_detail_summary", "parameters": {"project_name": "DEMETER", "fw_version": "Y1114B"}, "confidence": 0.93}

輸入：Channel 的 82CBW5QF 版本進度如何
輸出：{"intent": "query_fw_detail_summary", "parameters": {"project_name": "Channel", "fw_version": "82CBW5QF"}, "confidence": 0.90}

輸入：A400 專案 X0325A 使用了多少樣本
輸出：{"intent": "query_fw_detail_summary", "parameters": {"project_name": "A400", "fw_version": "X0325A"}, "confidence": 0.92}

輸入：Frey3B 的 FWX0926C 樣本使用率
輸出：{"intent": "query_fw_detail_summary", "parameters": {"project_name": "Frey3B", "fw_version": "FWX0926C"}, "confidence": 0.90}

輸入：Bennington 專案韌體 Y1103C 的執行率
輸出：{"intent": "query_fw_detail_summary", "parameters": {"project_name": "Bennington", "fw_version": "Y1103C"}, "confidence": 0.90}

輸入：Springsteen G200X6EC 測試概覽
輸出：{"intent": "query_fw_detail_summary", "parameters": {"project_name": "Springsteen", "fw_version": "G200X6EC"}, "confidence": 0.92}

輸入：DEMETER Y1114B 的通過率
輸出：{"intent": "query_fw_detail_summary", "parameters": {"project_name": "DEMETER", "fw_version": "Y1114B"}, "confidence": 0.90}

輸入：Channel 82CBW5QF 失敗率多少
輸出：{"intent": "query_fw_detail_summary", "parameters": {"project_name": "Channel", "fw_version": "82CBW5QF"}, "confidence": 0.90}

輸入：Ryder 負責哪些專案？
輸出：{"intent": "query_projects_by_pl", "parameters": {"pl": "Ryder"}, "confidence": 0.95}

輸入：ryder.lin 的專案
輸出：{"intent": "query_projects_by_pl", "parameters": {"pl": "ryder.lin"}, "confidence": 0.93}

輸入：Jeffery 管理的專案有哪些
輸出：{"intent": "query_projects_by_pl", "parameters": {"pl": "Jeffery"}, "confidence": 0.93}

輸入：查詢 PL 是 Wei-Zhen 的專案
輸出：{"intent": "query_projects_by_pl", "parameters": {"pl": "Wei-Zhen"}, "confidence": 0.92}

輸入：哪些專案是 bruce.zhang 負責的
輸出：{"intent": "query_projects_by_pl", "parameters": {"pl": "bruce.zhang"}, "confidence": 0.90}

輸入：列出 Zhenyuan 的專案
輸出：{"intent": "query_projects_by_pl", "parameters": {"pl": "Zhenyuan"}, "confidence": 0.92}

輸入：專案負責人是 jeffery.kuo 的專案
輸出：{"intent": "query_projects_by_pl", "parameters": {"pl": "jeffery.kuo"}, "confidence": 0.90}

輸入：2025年12月有哪些專案？
輸出：{"intent": "query_projects_by_month", "parameters": {"year": 2025, "month": 12}, "confidence": 0.95}

輸入：本月有哪些轉案
輸出：{"intent": "query_projects_by_month", "parameters": {"date_range": "this_month"}, "confidence": 0.93}

輸入：上個月轉進的案子
輸出：{"intent": "query_projects_by_month", "parameters": {"date_range": "last_month"}, "confidence": 0.93}

輸入：12月有幾個專案
輸出：{"intent": "query_projects_by_month", "parameters": {"month": 12}, "confidence": 0.90}

輸入：今年有哪些專案
輸出：{"intent": "query_projects_by_date", "parameters": {"date_range": "this_year"}, "confidence": 0.93}

輸入：2024年的專案
輸出：{"intent": "query_projects_by_date", "parameters": {"year": 2024}, "confidence": 0.92}

輸入：有哪些客戶
輸出：{"intent": "list_all_customers", "parameters": {}, "confidence": 0.95}

輸入：控制器列表
輸出：{"intent": "list_all_controllers", "parameters": {}, "confidence": 0.95}

輸入：Springsteen 有哪幾版 sub version
輸出：{"intent": "list_sub_versions", "parameters": {"project_name": "Springsteen"}, "confidence": 0.95}

輸入：DEMETER 的 sub version 有哪些
輸出：{"intent": "list_sub_versions", "parameters": {"project_name": "DEMETER"}, "confidence": 0.93}

輸入：Channel 有哪些容量版本
輸出：{"intent": "list_sub_versions", "parameters": {"project_name": "Channel"}, "confidence": 0.92}

輸入：A400 有幾個 SubVersion
輸出：{"intent": "list_sub_versions", "parameters": {"project_name": "A400"}, "confidence": 0.90}

輸入：springsteen AC 有哪些 FW
輸出：{"intent": "list_fw_by_sub_version", "parameters": {"project_name": "Springsteen", "sub_version": "AC"}, "confidence": 0.95}

輸入：DEMETER AA 有幾個 FW
輸出：{"intent": "list_fw_by_sub_version", "parameters": {"project_name": "DEMETER", "sub_version": "AA"}, "confidence": 0.93}

輸入：Channel 2048GB 版本的 FW
輸出：{"intent": "list_fw_by_sub_version", "parameters": {"project_name": "Channel", "sub_version": "AC"}, "confidence": 0.92}

輸入：Frey3B AB 版本有哪些韌體
輸出：{"intent": "list_fw_by_sub_version", "parameters": {"project_name": "Frey3B", "sub_version": "AB"}, "confidence": 0.92}

輸入：A400 512GB 有哪些 FW 版本
輸出：{"intent": "list_fw_by_sub_version", "parameters": {"project_name": "A400", "sub_version": "AA"}, "confidence": 0.90}

輸入：Springsteen 1TB 版本的韌體列表
輸出：{"intent": "list_fw_by_sub_version", "parameters": {"project_name": "Springsteen", "sub_version": "AB"}, "confidence": 0.90}

輸入：哪些案子有測試過 Performance
輸出：{"intent": "query_projects_by_test_category", "parameters": {"test_category": "Performance"}, "confidence": 0.95}

輸入：有做過 NVMe 測試的專案有哪些
輸出：{"intent": "query_projects_by_test_category", "parameters": {"test_category": "NVMe"}, "confidence": 0.93}

輸入：哪些專案做過 PCIe CV5 測試
輸出：{"intent": "query_projects_by_test_category", "parameters": {"test_category": "PCIe"}, "confidence": 0.92}

輸入：找出所有測試過 OAKGATE 的專案
輸出：{"intent": "query_projects_by_test_category", "parameters": {"test_category": "OAKGATE"}, "confidence": 0.93}

輸入：有跑過 MANDi 的案子
輸出：{"intent": "query_projects_by_test_category", "parameters": {"test_category": "MANDi"}, "confidence": 0.90}

輸入：哪些專案完成了 USB4 認證
輸出：{"intent": "query_projects_by_test_category", "parameters": {"test_category": "USB4"}, "confidence": 0.92}

輸入：列出有 Compatibility 測試的案子
輸出：{"intent": "query_projects_by_test_category", "parameters": {"test_category": "Compatibility"}, "confidence": 0.93}

輸入：WD 有哪些案子做過 Performance 測試
輸出：{"intent": "query_projects_by_test_category", "parameters": {"test_category": "Performance", "customer": "WD"}, "confidence": 0.93}

輸入：有 CrystalDiskMark 測試的專案
輸出：{"intent": "query_projects_by_test_category", "parameters": {"test_category": "CrystalDiskMark"}, "confidence": 0.90}

輸入：哪些專案的效能測試有 Pass
輸出：{"intent": "query_projects_by_test_category", "parameters": {"test_category": "Performance", "status_filter": "pass"}, "confidence": 0.90}

輸入：DEMETER 的 Y1114B FW 有哪些測試類別
輸出：{"intent": "query_project_fw_test_categories", "parameters": {"project_name": "DEMETER", "fw_version": "Y1114B"}, "confidence": 0.95}

輸入：這個案子 512GB 版本有哪些 Category
輸出：{"intent": "query_project_fw_test_categories", "parameters": {"project_name": "這個案子", "fw_version": "512GB"}, "confidence": 0.93}

輸入：Springsteen 的 128GB FW 有做哪些測試類別
輸出：{"intent": "query_project_fw_test_categories", "parameters": {"project_name": "Springsteen", "fw_version": "128GB"}, "confidence": 0.92}

輸入：Project Alpha 的 FW v2.1 包含哪些測試類別
輸出：{"intent": "query_project_fw_test_categories", "parameters": {"project_name": "Project Alpha", "fw_version": "FW v2.1"}, "confidence": 0.93}

輸入：Channel 的 FWY0512A 有哪些 Category
輸出：{"intent": "query_project_fw_test_categories", "parameters": {"project_name": "Channel", "fw_version": "FWY0512A"}, "confidence": 0.94}

輸入：這個專案 1024GB 的 FW 有什麼測試
輸出：{"intent": "query_project_fw_test_categories", "parameters": {"project_name": "這個專案", "fw_version": "1024GB"}, "confidence": 0.90}

輸入：A400 專案 AB 版本有哪些測試類別
輸出：{"intent": "query_project_fw_test_categories", "parameters": {"project_name": "A400", "fw_version": "AB"}, "confidence": 0.92}

輸入：WD DEMETER 的 AC 版本做了哪些測試
輸出：{"intent": "query_project_fw_test_categories", "parameters": {"project_name": "DEMETER", "fw_version": "AC"}, "confidence": 0.91}

輸入：Springsteen GD10YBJD_Opal Functionality 類別有哪些測項
輸出：{"intent": "query_project_fw_category_test_items", "parameters": {"project_name": "Springsteen", "fw_version": "GD10YBJD_Opal", "category_name": "Functionality"}, "confidence": 0.95}

輸入：DEMETER 的 Y1114B 的 NVMe_Validation_Tool 有什麼測試項目
輸出：{"intent": "query_project_fw_category_test_items", "parameters": {"project_name": "DEMETER", "fw_version": "Y1114B", "category_name": "NVMe_Validation_Tool"}, "confidence": 0.94}

輸入：Channel 專案 FW 82CBW5QF 的 Performance 類別有哪些測項
輸出：{"intent": "query_project_fw_category_test_items", "parameters": {"project_name": "Channel", "fw_version": "82CBW5QF", "category_name": "Performance"}, "confidence": 0.93}

輸入：這個案子 512GB 版本 MANDi 測試包含哪些項目
輸出：{"intent": "query_project_fw_category_test_items", "parameters": {"project_name": "這個案子", "fw_version": "512GB", "category_name": "MANDi"}, "confidence": 0.92}

輸入：A400 專案 X0325A 的 Reliability 測試有哪些測項
輸出：{"intent": "query_project_fw_category_test_items", "parameters": {"project_name": "A400", "fw_version": "X0325A", "category_name": "Reliability"}, "confidence": 0.93}

輸入：Springsteen GD10YBJD_Opal 有哪些測項
輸出：{"intent": "query_project_fw_all_test_items", "parameters": {"project_name": "Springsteen", "fw_version": "GD10YBJD_Opal"}, "confidence": 0.95}

輸入：DEMETER 的 Y1114B 有哪些測試項目
輸出：{"intent": "query_project_fw_all_test_items", "parameters": {"project_name": "DEMETER", "fw_version": "Y1114B"}, "confidence": 0.94}

輸入：Channel 專案 FW 82CBW5QF 全部測項有哪些
輸出：{"intent": "query_project_fw_all_test_items", "parameters": {"project_name": "Channel", "fw_version": "82CBW5QF"}, "confidence": 0.93}

輸入：這個案子 1024GB 有什麼測試項目
輸出：{"intent": "query_project_fw_all_test_items", "parameters": {"project_name": "這個案子", "fw_version": "1024GB"}, "confidence": 0.92}

輸入：A400 專案 X0325A 總共有哪些測試項目
輸出：{"intent": "query_project_fw_all_test_items", "parameters": {"project_name": "A400", "fw_version": "X0325A"}, "confidence": 0.93}

輸入：列出 Frey3B 的 FWX0926C 所有測項
輸出：{"intent": "query_project_fw_all_test_items", "parameters": {"project_name": "Frey3B", "fw_version": "FWX0926C"}, "confidence": 0.92}

輸入：Springsteen 12月有哪些 FW
輸出：{"intent": "list_fw_by_date_range", "parameters": {"project_name": "Springsteen", "month": 12}, "confidence": 0.95}

輸入：DEMETER 本月的 FW
輸出：{"intent": "list_fw_by_date_range", "parameters": {"project_name": "DEMETER", "date_range": "this_month"}, "confidence": 0.94}

輸入：Channel 上個月有哪些 FW 版本
輸出：{"intent": "list_fw_by_date_range", "parameters": {"project_name": "Channel", "date_range": "last_month"}, "confidence": 0.93}

輸入：Springsteen 2025年1月的 FW 版本
輸出：{"intent": "list_fw_by_date_range", "parameters": {"project_name": "Springsteen", "year": 2025, "month": 1}, "confidence": 0.94}

輸入：DEMETER 這個月有幾個 FW
輸出：{"intent": "list_fw_by_date_range", "parameters": {"project_name": "DEMETER", "date_range": "this_month"}, "confidence": 0.93}

輸入：Channel 最近有哪些 FW
輸出：{"intent": "list_fw_by_date_range", "parameters": {"project_name": "Channel", "date_range": "recent"}, "confidence": 0.92}

輸入：Springsteen 10月到12月的 FW
輸出：{"intent": "list_fw_by_date_range", "parameters": {"project_name": "Springsteen", "year": 2025, "start_month": 10, "end_month": 12}, "confidence": 0.93}

輸入：DEMETER 這週有新的 FW 嗎
輸出：{"intent": "list_fw_by_date_range", "parameters": {"project_name": "DEMETER", "date_range": "this_week"}, "confidence": 0.91}

輸入：Channel 上週發布了什麼 FW
輸出：{"intent": "list_fw_by_date_range", "parameters": {"project_name": "Channel", "date_range": "last_week"}, "confidence": 0.90}

輸入：Springsteen 今年有哪些 FW
輸出：{"intent": "list_fw_by_date_range", "parameters": {"project_name": "Springsteen", "year": 2025}, "confidence": 0.92}

輸入：Springsteen AC 2025年有哪些 FW
輸出：{"intent": "list_fw_by_date_range", "parameters": {"project_name": "Springsteen", "sub_version": "AC", "year": 2025}, "confidence": 0.95}

輸入：DEMETER AA 本月的 FW
輸出：{"intent": "list_fw_by_date_range", "parameters": {"project_name": "DEMETER", "sub_version": "AA", "date_range": "this_month"}, "confidence": 0.94}

輸入：Channel AB 12月的韌體版本
輸出：{"intent": "list_fw_by_date_range", "parameters": {"project_name": "Channel", "sub_version": "AB", "month": 12}, "confidence": 0.93}

輸入：Springsteen 的 AC 版本今年有哪些 FW
輸出：{"intent": "list_fw_by_date_range", "parameters": {"project_name": "Springsteen", "sub_version": "AC", "year": 2025}, "confidence": 0.94}

輸入：DEMETER AD 上個月有幾個 FW
輸出：{"intent": "list_fw_by_date_range", "parameters": {"project_name": "DEMETER", "sub_version": "AD", "date_range": "last_month"}, "confidence": 0.93}

輸入：Channel 2TB 版本 2025年的 FW
輸出：{"intent": "list_fw_by_date_range", "parameters": {"project_name": "Channel", "sub_version": "AC", "year": 2025}, "confidence": 0.92}

輸入：今天天氣如何？
輸出：{"intent": "unknown", "parameters": {}, "confidence": 0.10}

輸入：幫我寫程式
輸出：{"intent": "unknown", "parameters": {}, "confidence": 0.10}

---

現在分析以下問題：
"""


class SAFIntentAnalyzer:
    """
    SAF 意圖分析器
    
    使用 Dify 的 SAF_Intent_Analyzer App 進行意圖分析。
    Prompt 完全由程式碼控制，方便版本管理。
    """
    
    def __init__(self, api_key: str = None, timeout: int = None):
        """
        初始化意圖分析器
        
        Args:
            api_key: Dify API Key（可選，使用配置管理器的預設值）
            timeout: 請求超時時間（可選）
        """
        # 延遲導入避免循環依賴
        from library.config.dify_config_manager import get_saf_intent_analyzer_config
        
        config = get_saf_intent_analyzer_config()
        
        self.api_key = api_key or config.api_key
        self.api_url = config.api_url
        self.timeout = timeout or config.timeout
        
        logger.info(f"SAFIntentAnalyzer 初始化完成: api_url={self.api_url}")
    
    def analyze(self, query: str, user_id: str = "saf-smart-query") -> IntentResult:
        """
        分析用戶問題的意圖
        
        Args:
            query: 用戶的問題（如「WD 有哪些專案？」）
            user_id: 用戶識別碼
            
        Returns:
            IntentResult: 包含 intent, parameters, confidence
        """
        if not query or not query.strip():
            return IntentResult.create_error("查詢內容不能為空")
        
        try:
            # 組合完整的 prompt
            full_query = f"{INTENT_ANALYSIS_PROMPT}\n{query}"
            
            # 調用 Dify Chat API
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "inputs": {},
                    "query": full_query,
                    "response_mode": "blocking",
                    "conversation_id": "",  # 每次都是新對話
                    "user": user_id
                },
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                logger.error(f"Dify API 錯誤: {response.status_code} - {response.text[:200]}")
                return self._fallback_analysis(query)
            
            data = response.json()
            answer = data.get('answer', '')
            
            logger.info(f"意圖分析原始回應: {answer[:200]}...")
            
            return self._parse_intent_response(answer, query)
            
        except requests.Timeout:
            logger.error("Dify API 請求超時")
            return self._fallback_analysis(query)
        except requests.ConnectionError as e:
            logger.error(f"Dify API 連線錯誤: {str(e)}")
            return self._fallback_analysis(query)
        except Exception as e:
            logger.error(f"意圖分析錯誤: {str(e)}")
            return self._fallback_analysis(query)
    
    def _parse_intent_response(self, answer: str, original_query: str) -> IntentResult:
        """
        解析 LLM 返回的 JSON
        
        Args:
            answer: LLM 回應
            original_query: 原始查詢
            
        Returns:
            IntentResult: 解析後的意圖結果
        """
        try:
            # 清理可能的 markdown 標記
            clean_answer = self._clean_json_response(answer)
            
            # 解析 JSON
            intent_data = json.loads(clean_answer)
            
            # 獲取原始意圖字串
            raw_intent = intent_data.get('intent', 'unknown')
            
            # 處理 Dify 可能返回的組合意圖（映射到我們支援的 Intent）
            combined_intent_mapping = {
                'list_fw_by_sub_version_and_year': 'list_fw_by_date_range',
                'list_fw_by_sub_version_and_month': 'list_fw_by_date_range',
                'list_fw_by_sub_version_and_date': 'list_fw_by_date_range',
                'query_fw_by_sub_version_and_year': 'list_fw_by_date_range',
            }
            
            if raw_intent in combined_intent_mapping:
                logger.info(f"映射組合意圖 '{raw_intent}' -> '{combined_intent_mapping[raw_intent]}'")
                raw_intent = combined_intent_mapping[raw_intent]
            
            # 創建 IntentResult
            intent_type = IntentType.from_string(raw_intent)
            parameters = intent_data.get('parameters', {})
            
            # 檢測意圖是否與查詢明顯不匹配
            should_use_fallback = False
            
            # 情況 1：Dify 返回 unknown
            if intent_type == IntentType.UNKNOWN:
                logger.info("Dify 返回 unknown，嘗試 fallback 分析")
                should_use_fallback = True
            
            # 情況 2：查詢中包含特定客戶名，但 Dify 返回了 list_all_customers（列出所有客戶）
            # 例如：「Samsung 有幾個案子」應該是 count_projects(customer=Samsung)，不是 list_all_customers
            elif intent_type == IntentType.LIST_ALL_CUSTOMERS:
                detected_customer = self._detect_customer(original_query)
                if detected_customer:
                    logger.info(f"查詢包含特定客戶 '{detected_customer}'，但 Dify 返回 list_all_customers，嘗試 fallback")
                    should_use_fallback = True
            
            # 情況 3：查詢中包含特定客戶名，但返回的意圖沒有 customer 參數
            elif intent_type in [IntentType.COUNT_PROJECTS, IntentType.QUERY_PROJECTS_BY_CUSTOMER]:
                detected_customer = self._detect_customer(original_query)
                if detected_customer and not parameters.get('customer'):
                    logger.info(f"查詢包含特定客戶 '{detected_customer}'，但參數中缺少 customer，補充參數")
                    parameters['customer'] = detected_customer
            
            # 如果需要使用 fallback
            if should_use_fallback:
                fallback_result = self._fallback_analysis(original_query)
                # 只有當 fallback 識別出有效意圖時才使用
                if fallback_result.intent != IntentType.UNKNOWN:
                    logger.info(f"Fallback 識別成功: {fallback_result.intent}, 參數: {fallback_result.parameters}")
                    return fallback_result
            
            return IntentResult(
                intent=intent_type,
                parameters=parameters,
                confidence=float(intent_data.get('confidence', 0.5)),
                raw_response=answer
            )
            
        except json.JSONDecodeError as e:
            logger.warning(f"JSON 解析失敗: {e}, 嘗試提取: {answer[:100]}...")
            return self._extract_json_from_text(answer, original_query)
    
    def _clean_json_response(self, answer: str) -> str:
        """
        清理 JSON 回應中的 markdown 標記
        
        Args:
            answer: 原始回應
            
        Returns:
            str: 清理後的 JSON 字串
        """
        clean_answer = answer.strip()
        
        # 移除 markdown 代碼塊標記
        if clean_answer.startswith("```json"):
            clean_answer = clean_answer[7:]
        if clean_answer.startswith("```"):
            clean_answer = clean_answer[3:]
        if clean_answer.endswith("```"):
            clean_answer = clean_answer[:-3]
        
        return clean_answer.strip()
    
    def _extract_json_from_text(self, text: str, original_query: str) -> IntentResult:
        """
        從文字中提取 JSON（處理 LLM 可能添加的額外文字）
        
        Args:
            text: 包含 JSON 的文字
            original_query: 原始查詢
            
        Returns:
            IntentResult: 提取的意圖結果
        """
        # 嘗試找到包含 "intent" 的 JSON 部分
        json_pattern = r'\{[^{}]*"intent"[^{}]*\}'
        matches = re.findall(json_pattern, text)
        
        for match in matches:
            try:
                intent_data = json.loads(match)
                if 'intent' in intent_data:
                    intent_type = IntentType.from_string(intent_data.get('intent', 'unknown'))
                    return IntentResult(
                        intent=intent_type,
                        parameters=intent_data.get('parameters', {}),
                        confidence=float(intent_data.get('confidence', 0.5)),
                        raw_response=text
                    )
            except (json.JSONDecodeError, ValueError):
                continue
        
        # 完全無法解析，使用降級方案
        logger.warning("無法從回應中提取 JSON，使用降級方案")
        return self._fallback_analysis(original_query)
    
    def _fallback_analysis(self, query: str) -> IntentResult:
        """
        降級處理：使用簡單的關鍵字匹配
        當 LLM 調用失敗時的備用方案
        
        Args:
            query: 用戶查詢
            
        Returns:
            IntentResult: 基於關鍵字匹配的意圖結果
        """
        query_lower = query.lower()
        
        # 1. 檢查客戶關鍵字
        detected_customer = self._detect_customer(query)
        if detected_customer:
            # 檢查是數量查詢還是列表查詢
            if self._has_count_keywords(query):
                return IntentResult(
                    intent=IntentType.COUNT_PROJECTS,
                    parameters={'customer': detected_customer},
                    confidence=0.6,
                    raw_response=f"Fallback: detected customer={detected_customer}, count query"
                )
            elif self._has_project_keywords(query):
                return IntentResult(
                    intent=IntentType.QUERY_PROJECTS_BY_CUSTOMER,
                    parameters={'customer': detected_customer},
                    confidence=0.6,
                    raw_response=f"Fallback: detected customer={detected_customer}"
                )
        
        # 2. 檢查控制器關鍵字
        detected_controller = self._detect_controller(query)
        if detected_controller:
            return IntentResult(
                intent=IntentType.QUERY_PROJECTS_BY_CONTROLLER,
                parameters={'controller': detected_controller},
                confidence=0.6,
                raw_response=f"Fallback: detected controller={detected_controller}"
            )
        
        # 3. 通用數量查詢（無特定客戶）
        if self._has_count_keywords(query):
            return IntentResult(
                intent=IntentType.COUNT_PROJECTS,
                parameters={},
                confidence=0.6,
                raw_response="Fallback: count query without customer"
            )
        
        # 4. 客戶列表查詢
        if '客戶' in query and ('有哪些' in query or '列表' in query or '全部' in query):
            return IntentResult(
                intent=IntentType.LIST_ALL_CUSTOMERS,
                parameters={},
                confidence=0.6,
                raw_response="Fallback: list customers query"
            )
        
        # 5. 控制器列表查詢
        if '控制器' in query and ('有哪些' in query or '列表' in query or '全部' in query):
            return IntentResult(
                intent=IntentType.LIST_ALL_CONTROLLERS,
                parameters={},
                confidence=0.6,
                raw_response="Fallback: list controllers query"
            )
        
        # 6. PL（專案負責人）列表查詢
        query_lower = query.lower()
        pl_keywords = ['pl', 'pm', '負責人', '專案負責人', 'project leader', 'project manager']
        list_keywords = ['有哪些', '有那些', '列表', '全部', '所有', '多少']
        
        if any(pk in query_lower for pk in pl_keywords) and any(lk in query for lk in list_keywords):
            return IntentResult(
                intent=IntentType.LIST_ALL_PLS,
                parameters={},
                confidence=0.6,
                raw_response="Fallback: list pls query"
            )
        
        # 7. 日期/月份查詢 (Phase 8)
        date_result = self._detect_date_query(query)
        if date_result:
            return date_result
        
        # 8. Sub Version 相關查詢 (Phase 9)
        project_name = self._detect_project_name(query)
        detected_sub_version = self._detect_sub_version(query)
        
        if project_name and detected_sub_version:
            # 查詢特定 Sub Version 的 FW 列表
            return IntentResult(
                intent=IntentType.LIST_FW_BY_SUB_VERSION,
                parameters={
                    'project_name': project_name,
                    'sub_version': detected_sub_version
                },
                confidence=0.6,
                raw_response=f"Fallback: list FW by sub version for {project_name} {detected_sub_version}"
            )
        
        if project_name and self._has_sub_version_keywords(query):
            # 列出專案所有 Sub Version
            return IntentResult(
                intent=IntentType.LIST_SUB_VERSIONS,
                parameters={'project_name': project_name},
                confidence=0.6,
                raw_response=f"Fallback: list sub versions for {project_name}"
            )
        
        # 9. 檢查是否是專案詳情或摘要查詢
        if project_name:
            # 檢查是否有測試類別或容量關鍵字
            detected_category = self._detect_test_category(query)
            detected_capacity = self._detect_capacity(query)
            
            if detected_category:
                # 按類別查詢測試結果
                params = {'project_name': project_name, 'category': detected_category}
                if detected_capacity:
                    params['capacity'] = detected_capacity
                return IntentResult(
                    intent=IntentType.QUERY_PROJECT_TEST_BY_CATEGORY,
                    parameters=params,
                    confidence=0.6,
                    raw_response=f"Fallback: test by category query for {project_name}"
                )
            
            if detected_capacity:
                # 按容量查詢測試結果
                return IntentResult(
                    intent=IntentType.QUERY_PROJECT_TEST_BY_CAPACITY,
                    parameters={'project_name': project_name, 'capacity': detected_capacity},
                    confidence=0.6,
                    raw_response=f"Fallback: test by capacity query for {project_name}"
                )
            
            # 一般測試查詢
            if '測試' in query or '結果' in query or '摘要' in query or 'pass' in query_lower or 'fail' in query_lower:
                return IntentResult(
                    intent=IntentType.QUERY_PROJECT_TEST_SUMMARY,
                    parameters={'project_name': project_name},
                    confidence=0.5,
                    raw_response=f"Fallback: project test summary query for {project_name}"
                )
            else:
                return IntentResult(
                    intent=IntentType.QUERY_PROJECT_DETAIL,
                    parameters={'project_name': project_name},
                    confidence=0.5,
                    raw_response=f"Fallback: project detail query for {project_name}"
                )
        
        # 無法識別
        return IntentResult(
            intent=IntentType.UNKNOWN,
            parameters={},
            confidence=0.3,
            raw_response=f"Fallback: unknown intent for query: {query}"
        )
    
    def _detect_customer(self, query: str) -> Optional[str]:
        """
        檢測查詢中的客戶名稱
        
        Args:
            query: 用戶查詢
            
        Returns:
            Optional[str]: 檢測到的客戶名稱，或 None
        """
        query_upper = query.upper()
        
        # 按優先順序檢查（較長的名稱優先）
        sorted_customers = sorted(KNOWN_CUSTOMERS, key=len, reverse=True)
        
        for customer in sorted_customers:
            if customer.upper() in query_upper:
                # 標準化返回值
                customer_mapping = {
                    'WDC': 'WD',
                    'WESTERN DIGITAL': 'WD',
                }
                return customer_mapping.get(customer.upper(), customer)
        
        return None
    
    def _detect_controller(self, query: str) -> Optional[str]:
        """
        檢測查詢中的控制器型號
        
        Args:
            query: 用戶查詢
            
        Returns:
            Optional[str]: 檢測到的控制器型號，或 None
        """
        query_upper = query.upper()
        
        for controller in KNOWN_CONTROLLERS:
            if controller.upper() in query_upper:
                return controller.upper()
        
        # 嘗試匹配部分型號（如 2264）
        partial_pattern = r'(\d{4})'
        matches = re.findall(partial_pattern, query)
        for match in matches:
            full_model = f"SM{match}"
            if full_model in [c.upper() for c in KNOWN_CONTROLLERS]:
                return full_model
        
        return None
    
    def _detect_project_name(self, query: str) -> Optional[str]:
        """
        檢測查詢中的專案名稱（啟發式方法）
        
        Args:
            query: 用戶查詢
            
        Returns:
            Optional[str]: 檢測到的專案名稱，或 None
        """
        # 常見專案名稱模式
        # 1. 大寫字母開頭的單詞（不是已知客戶或控制器）
        words = re.findall(r'\b([A-Z][a-zA-Z0-9]+)\b', query)
        
        for word in words:
            word_upper = word.upper()
            # 排除已知客戶和控制器
            if word_upper not in [c.upper() for c in KNOWN_CUSTOMERS]:
                if word_upper not in [c.upper() for c in KNOWN_CONTROLLERS]:
                    if word not in ['GET', 'POST', 'API', 'SAF']:
                        return word
        
        return None
    
    def _has_count_keywords(self, query: str) -> bool:
        """檢查是否包含數量相關關鍵字"""
        count_keywords = ['多少', '幾個', '數量', 'count', '總共', '專案數']
        return any(kw in query.lower() for kw in count_keywords)
    
    def _has_project_keywords(self, query: str) -> bool:
        """檢查是否包含專案相關關鍵字"""
        project_keywords = ['專案', 'project', '有哪些', '列表', '列出']
        return any(kw in query.lower() for kw in project_keywords)
    
    def _detect_test_category(self, query: str) -> Optional[str]:
        """
        檢測查詢中的測試類別
        
        Args:
            query: 用戶查詢
            
        Returns:
            Optional[str]: 檢測到的測試類別（標準化名稱），或 None
        """
        query_lower = query.lower()
        
        # 類別名稱映射（包含中英文和縮寫）
        category_mapping = {
            'compliance': 'Compliance',
            'comp': 'Compliance',
            '合規': 'Compliance',
            '合規性': 'Compliance',
            'functionality': 'Functionality',
            'func': 'Functionality',
            '功能': 'Functionality',
            '功能測試': 'Functionality',
            'performance': 'Performance',
            'perf': 'Performance',
            '效能': 'Performance',
            '效能測試': 'Performance',
            'interoperability': 'Interoperability',
            'inter': 'Interoperability',
            '互通': 'Interoperability',
            '互通性': 'Interoperability',
            'stress': 'Stress',
            '壓力': 'Stress',
            '壓力測試': 'Stress',
            'compatibility': 'Compatibility',
            'compat': 'Compatibility',
            '相容': 'Compatibility',
            '相容性': 'Compatibility',
        }
        
        for keyword, standard_name in category_mapping.items():
            if keyword in query_lower:
                return standard_name
        
        return None
    
    def _detect_capacity(self, query: str) -> Optional[str]:
        """
        檢測查詢中的容量規格
        
        Args:
            query: 用戶查詢
            
        Returns:
            Optional[str]: 檢測到的容量（標準化格式），或 None
        """
        query_upper = query.upper()
        
        # 容量映射（標準化為 GB/TB 格式）
        capacity_mapping = {
            '256GB': '256GB',
            '256G': '256GB',
            '512GB': '512GB',
            '512G': '512GB',
            '1TB': '1TB',
            '1T': '1TB',
            '2TB': '2TB',
            '2T': '2TB',
            '4TB': '4TB',
            '4T': '4TB',
            '8TB': '8TB',
            '8T': '8TB',
        }
        
        for keyword, standard_capacity in capacity_mapping.items():
            if keyword in query_upper:
                return standard_capacity
        
        return None

    def _detect_sub_version(self, query: str) -> Optional[str]:
        """
        檢測查詢中的 Sub Version（容量版本）(Phase 9)
        
        支援格式：
        - 直接代碼：AA, AB, AC, AD
        - 容量描述：512GB, 1024GB, 2048GB, 4096GB, 1TB, 2TB, 4TB
        
        Args:
            query: 用戶查詢
            
        Returns:
            Optional[str]: 檢測到的 Sub Version 代碼（AA/AB/AC/AD），或 None
        """
        query_upper = query.upper()
        
        # 直接匹配 Sub Version 代碼（確保是獨立的詞）
        for sv in ['AA', 'AB', 'AC', 'AD']:
            # 使用正則確保是獨立的詞（避免匹配到 AAAA 這種）
            if re.search(rf'\b{sv}\b', query_upper):
                return sv
        
        # 容量到 Sub Version 的映射
        capacity_to_sv = {
            '512GB': 'AA', '512G': 'AA',
            '1024GB': 'AB', '1024G': 'AB', '1TB': 'AB', '1T': 'AB',
            '2048GB': 'AC', '2048G': 'AC', '2TB': 'AC', '2T': 'AC',
            '4096GB': 'AD', '4096G': 'AD', '4TB': 'AD', '4T': 'AD',
        }
        
        for capacity, sv in capacity_to_sv.items():
            if capacity in query_upper:
                return sv
        
        return None
    
    def _has_sub_version_keywords(self, query: str) -> bool:
        """
        檢查查詢是否包含 Sub Version 相關關鍵字 (Phase 9)
        
        Args:
            query: 用戶查詢
            
        Returns:
            bool: 是否包含 Sub Version 相關關鍵字
        """
        query_lower = query.lower()
        sv_keywords = [
            'sub version', 'subversion', 'sub_version', 'sv',
            '容量版本', '版本 aa', '版本 ab', '版本 ac', '版本 ad',
            'aa版', 'ab版', 'ac版', 'ad版',
        ]
        return any(kw in query_lower for kw in sv_keywords)
    
    def _parse_date_parameters_for_fw(self, query: str) -> Optional[Dict[str, Any]]:
        """
        解析 FW 日期查詢的日期參數 (Phase 13)
        
        Args:
            query: 用戶查詢
            
        Returns:
            Optional[Dict]: 日期參數字典，如果無法解析則返回 None
        """
        from datetime import datetime
        
        parameters = {}
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        # 1. 檢測「本月」「這個月」
        if '本月' in query or '這個月' in query or '當月' in query:
            parameters['date_range'] = 'this_month'
        
        # 2. 檢測「上月」「上個月」
        elif '上月' in query or '上個月' in query:
            parameters['date_range'] = 'last_month'
        
        # 3. 檢測「今年」（需要沒有月份）
        elif '今年' in query:
            parameters['date_range'] = 'this_year'
            parameters['year'] = current_year
        
        # 4. 檢測「YYYY年」（只有年份）
        else:
            # 嘗試匹配 "YYYY年MM月" 格式
            year_month_pattern = r'(\d{4})\s*年\s*(\d{1,2})\s*月'
            match = re.search(year_month_pattern, query)
            if match:
                parameters['year'] = int(match.group(1))
                parameters['month'] = int(match.group(2))
            else:
                # 嘗試匹配 "YYYY年" 格式（只有年份）
                year_pattern = r'(\d{4})\s*年'
                match = re.search(year_pattern, query)
                if match:
                    parameters['year'] = int(match.group(1))
                else:
                    # 嘗試匹配 "MM月" 格式（只有月份，假設當年）
                    month_pattern = r'(\d{1,2})\s*月'
                    match = re.search(month_pattern, query)
                    if match:
                        parameters['year'] = current_year
                        parameters['month'] = int(match.group(1))
        
        # 驗證月份有效性
        if 'month' in parameters:
            if not (1 <= parameters['month'] <= 12):
                return None
        
        return parameters if parameters else None

    def _detect_date_query(self, query: str) -> Optional[IntentResult]:
        """
        檢測日期/月份相關查詢 (Phase 8, 擴展 Phase 13)
        
        支援的查詢格式：
        - 「2025年12月有哪些專案」「2025/12 的案子」
        - 「本月有哪些轉案」「這個月新增的專案」
        - 「上個月轉進的案子」「上月的專案」
        - 「今年的專案」「2025年有幾個案子」
        - 「12月有哪些專案」「幾月轉進的」
        
        Phase 13 擴展（FW 日期查詢）：
        - 「Springsteen 12月有哪些 FW」
        - 「Springsteen AC 2025年有哪些 FW」
        - 「DEMETER 本月的 FW」
        
        Args:
            query: 用戶查詢
            
        Returns:
            Optional[IntentResult]: 如果是日期查詢，返回 IntentResult；否則 None
        """
        from datetime import datetime
        
        # 日期相關關鍵字
        date_keywords = [
            '月', '年', '日期', '本月', '這個月', '上月', '上個月', '今年', 
            '幾月', '月份', '轉案', '轉進', '新增', '建立'
        ]
        
        # FW 相關關鍵字
        fw_keywords = ['fw', 'firmware', '韌體', '版本']
        
        # 專案相關關鍵字（需要同時出現）
        project_keywords = ['專案', '案子', '項目', 'project', '有哪些', '有那些', '多少', '幾個']
        
        query_lower = query.lower()
        
        # 檢查是否同時包含日期關鍵字和專案關鍵字
        has_date_keyword = any(kw in query for kw in date_keywords)
        has_project_keyword = any(kw in query_lower for kw in project_keywords)
        has_fw_keyword = any(kw in query_lower for kw in fw_keywords)
        
        # 檢測專案名稱和 Sub Version
        detected_project = self._detect_project_name(query)
        detected_sub_version = self._detect_sub_version(query)
        
        # 如果有專案名稱 + 日期關鍵字 + FW 關鍵字 → 這是 FW 日期查詢
        if detected_project and has_date_keyword and has_fw_keyword:
            # 解析日期參數
            date_params = self._parse_date_parameters_for_fw(query)
            
            if date_params:
                parameters = {
                    'project_name': detected_project,
                    **date_params
                }
                
                # 如果有 Sub Version，加入參數
                if detected_sub_version:
                    parameters['sub_version'] = detected_sub_version
                
                return IntentResult(
                    intent=IntentType.LIST_FW_BY_DATE_RANGE,
                    parameters=parameters,
                    confidence=0.7,
                    raw_response=f"Fallback: detected FW date query with params={parameters}"
                )
        
        # 原有邏輯：專案日期查詢
        if not (has_date_keyword and has_project_keyword):
            return None
        
        # 解析日期參數
        parameters = {}
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        # 1. 檢測「本月」「這個月」
        if '本月' in query or '這個月' in query or '當月' in query:
            parameters['date_range'] = 'this_month'
            parameters['year'] = current_year
            parameters['month'] = current_month
        
        # 2. 檢測「上月」「上個月」
        elif '上月' in query or '上個月' in query:
            parameters['date_range'] = 'last_month'
            if current_month == 1:
                parameters['year'] = current_year - 1
                parameters['month'] = 12
            else:
                parameters['year'] = current_year
                parameters['month'] = current_month - 1
        
        # 3. 檢測「今年」
        elif '今年' in query and '月' not in query:
            parameters['date_range'] = 'this_year'
            parameters['year'] = current_year
        
        # 4. 檢測具體年月 (例如: 2025年12月, 2025/12, 2025-12)
        else:
            # 嘗試匹配 "YYYY年MM月" 格式
            year_month_pattern = r'(\d{4})\s*年?\s*(\d{1,2})\s*月'
            match = re.search(year_month_pattern, query)
            if match:
                parameters['year'] = int(match.group(1))
                parameters['month'] = int(match.group(2))
            else:
                # 嘗試匹配 "YYYY年" 格式（只有年份）
                year_pattern = r'(\d{4})\s*年'
                match = re.search(year_pattern, query)
                if match:
                    year = int(match.group(1))
                    parameters['year'] = year
                    parameters['date_range'] = 'this_year'
                else:
                    # 嘗試匹配 "MM月" 格式（只有月份，假設當年）
                    month_pattern = r'(\d{1,2})\s*月'
                    match = re.search(month_pattern, query)
                    if match:
                        parameters['year'] = current_year
                        parameters['month'] = int(match.group(1))
        
        # 如果成功解析出日期參數
        if parameters:
            # 驗證月份有效性
            if 'month' in parameters:
                if not (1 <= parameters['month'] <= 12):
                    return None
            
            # 決定意圖類型
            if 'month' in parameters:
                intent_type = IntentType.QUERY_PROJECTS_BY_MONTH
            else:
                intent_type = IntentType.QUERY_PROJECTS_BY_DATE
            
            return IntentResult(
                intent=intent_type,
                parameters=parameters,
                confidence=0.65,
                raw_response=f"Fallback: detected date query with params={parameters}"
            )
        
        return None


# ============================================================
# 便利函數
# ============================================================

def analyze_intent(query: str, user_id: str = "saf-smart-query") -> IntentResult:
    """
    分析用戶查詢意圖的便利函數
    
    Args:
        query: 用戶查詢
        user_id: 用戶 ID
        
    Returns:
        IntentResult: 意圖分析結果
    """
    analyzer = SAFIntentAnalyzer()
    return analyzer.analyze(query, user_id)


# ============================================================
# 測試用 main 函數
# ============================================================
if __name__ == "__main__":
    # 測試案例
    test_queries = [
        "WD 有哪些專案？",
        "Samsung 有幾個專案？",
        "SM2264 控制器用在哪些專案？",
        "有哪些客戶？",
        "DEMETER 專案的詳細資訊",
        "DEMETER 的測試結果如何？",
        "有哪些控制器？",
        "今天天氣如何？"
    ]
    
    analyzer = SAFIntentAnalyzer()
    
    print("=" * 60)
    print("SAF 意圖分析器測試")
    print("=" * 60)
    
    for query in test_queries:
        result = analyzer.analyze(query)
        print(f"\n問題: {query}")
        print(f"意圖: {result.intent.value}")
        print(f"參數: {result.parameters}")
        print(f"信心度: {result.confidence:.2f}")
        print(f"有效: {result.is_valid()}")
        print("-" * 40)
