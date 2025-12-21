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

【意圖優先級規則 - 當問題包含「專案名稱 + FW 版本號」時】
- FW 版本號通常是類似 G200X6EC、Y1114B、HHB0YBC1、82CBW5QF 的格式
- 當問題同時包含專案名稱和 FW 版本號時：
  * 如果包含「統計」「通過率」「進度」「測了幾個」「狀況」「多少」→ 使用 query_project_test_summary_by_fw
  * 如果包含「測項結果」「測試項目」「哪些 Fail」「列出」「有哪些」→ 使用 query_project_fw_test_jobs
  * 不要誤認為 query_project_detail（此意圖不處理 FW 版本查詢）

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
用戶想了解某個特定專案的基本資訊（不含測試結果）時使用。
- 常見問法：
  - 「XX 專案的詳細資訊」「告訴我 XX 專案」
  - 「XX 專案是什麼」「查詢 XX 專案」「XX 專案的資訊」
  - 「介紹一下 XX 專案」
- 參數：project_name (專案名稱)
- 【重要區分】
  - 如果問題包含 FW 版本號（如 G200X6EC、Y1114B）→ 不要使用此意圖
  - 如果問題包含「統計」「測試」「通過率」「測項」「Fail」「Pass」→ 不要使用此意圖
  - 只有純粹詢問專案本身資訊時才使用此意圖

### 4. query_project_summary - 查詢專案基本摘要（僅限專案資訊）
【注意】此意圖僅用於查詢專案的基本資訊摘要，不涉及測試結果。
- 使用場景：用戶詢問專案概況、專案介紹、專案基本情況
- 常見問法：
  - 「XX 專案概況」「介紹 XX 專案」「XX 專案摘要」
- 參數：project_name (專案名稱)
- 【重要區分】
  - 如果問題包含 FW 版本號（如 G200X6EC、Y1114B）→ 使用 query_project_test_summary_by_fw
  - 如果問題包含「統計」「測試」「通過率」「測項」「Fail」「Pass」→ 使用測試相關意圖
  - 只有純粹詢問專案概況（不含 FW 版本、不含測試關鍵詞）才使用此意圖

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

### 8. query_project_test_summary_by_fw - 按 FW 版本查詢測試統計 (Phase 4 新增)
【高優先級】當問題同時包含「專案名稱」和「FW 版本號」時，優先使用此意圖或 query_project_fw_test_jobs。
用戶想了解專案特定 FW（韌體）版本的「測試統計數據」（如通過率、完成率、測試進度）時使用。
此意圖返回的是統計摘要，不包含每個測試項目的詳細結果。
- 常見問法：
  - 「XX 專案 FW YYY 測了幾個」「XX YYY 測試進度」
  - 「XX 的 YYY 版本通過率是多少」「XX YYY 通過率」
  - 「XX YYY 版本有多少測試通過？」「XX YYY 統計」
  - 「XX 專案韌體 YYY 的測試狀況」「XX YYY 測試狀況」
  - 「XX YYY 的完成率」「XX YYY 測試完成了多少」
  - 「XX 專案 YYY 的統計」「XX YYY 統計」
- 參數：
  - project_name (專案名稱，如 DEMETER、Channel、A400、Springsteen)
  - fw_version (FW 版本號，如 Y1114B、82CBW5QF、X0325A、G200X6EC)
- 【重要】此意圖用於查詢統計摘要
- 【識別規則】當問題包含「專案名稱 + FW 版本 + 統計/進度/狀況/通過率/測了幾個」時使用此意圖
- 【關鍵詞區分】
  - 統計類關鍵詞（使用此意圖）：「測了幾個」「通過率」「完成率」「統計」「進度」「狀況」「多少」
  - 詳細類關鍵詞（使用 query_project_fw_test_jobs）：「測項結果」「測試項目」「哪些測項」「哪些 Fail」「列出」「有哪些」
- 【區分】如果用戶沒有指定 FW 版本，請使用 query_project_test_summary
- 【注意】不要將此意圖誤認為 query_project_detail，query_project_detail 不處理 FW 版本

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
用戶想比較專案的 FW 版本，但沒有指定具體版本名稱，且只想比較【兩個】版本時使用。
系統會自動選擇最新的【兩個】版本進行比較。
- 常見問法：
  - 「XX 最新的 FW 比較」「XX 專案最新版本比較」（沒有指定數量 = 兩個）
  - 「比較 XX 最近兩個版本」「XX 的 FW 進度比較」
  - 「看一下 XX 最新版本差異」「XX 最新 FW 測試差異」
  - 「XX 專案 FW 更新比較」「比較 XX 最新韌體」
  - 「XX 版本演進比較」「XX 的 FW 變化」
- 參數：
  - project_name (專案名稱，如 DEMETER、Springsteen、Channel)
- 【重要】此意圖只用於比較【兩個】版本
- 【⚠️ 關鍵區分 ⚠️】
  - 如果用戶說「最新 3 個」「最近 3 個」「三個版本」「N 個版本」（N >= 3）→ 【必須】使用 compare_multiple_fw
  - 如果用戶說「最新」「最近」但【沒有指定數量】或說「兩個」→ 使用 compare_latest_fw
  - 數字關鍵字：3、三、4、四、5、五、多個 → 使用 compare_multiple_fw

### 11. list_fw_versions - 列出專案可比較的 FW 版本 (Phase 5.2 新增)
用戶想知道專案有哪些 FW 版本可以比較或查詢時使用。
- 常見問法：
  - 「XX 有哪些 FW 版本」「XX 專案的版本列表」
  - 「XX 的 FW 版本列表」「XX FW 版本」
  - 「列出 XX 的所有 FW」「XX 可以比較哪些版本」
  - 「XX 專案有幾個 FW」「查看 XX 的韌體版本」
  - 「XX 的 FW 版本有哪些」「顯示 XX 版本」
  - 「XX 有什麼版本可以查」「XX FW 清單」
  - 「XX 有那些 FW版本」「XX 有多少 FW」
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
- 【⚠️ 關鍵區分 ⚠️】
  - 如果用戶說「最新 3 個」「最近 3 個」「三個版本」「N 個版本」（N >= 3）→ 【必須】使用 compare_multiple_fw
  - 如果用戶說「最新兩個」「最近兩個」或沒有指定數量 → 使用 compare_latest_fw
  - 包含數字 3、三、4、四、5、五、6、六 或「多個」「幾個」「趨勢」→ 使用 compare_multiple_fw

### 13. query_fw_detail_summary - 查詢 FW 詳細統計 (Phase 6.2 新增)
用戶想了解專案特定 FW 版本的整體統計指標時使用。
此意圖提供：完成率、通過率、樣本使用率、執行率、失敗率等詳細統計。
- 常見問法：
  - 「XX 專案 FW YYY 的測試結果」「XX YYY 的測試結果」 ← 重要！
  - 「XX 專案 FW YYY 的詳細統計」「XX YYY 版本的統計資訊」
  - 「XX 專案 FW YYY 的完成率是多少」「XX YYY 進度如何」
  - 「XX 專案 FW YYY 使用了多少樣本」「XX YYY 樣本使用率」
  - 「XX 專案 FW YYY 的執行率」「XX YYY 失敗率多少」
  - 「XX 專案 FW YYY 測試概覽」「XX YYY 總覽」
  - 「XX 專案 FW YYY 的通過率」「XX YYY 測試進度」
- 參數：
  - project_name (專案名稱，如 Springsteen、DEMETER)
  - fw_version (FW 版本號，如 G200X6EC、Y1114B)
- 【重要】此意圖用於獲取整體統計指標，返回詳細統計表格（樣本數量、完成率指標、缺陷摘要）
- 【關鍵區分】
  - 「測試結果」→ 使用此意圖 query_fw_detail_summary（返回統計表格）
  - 「測試項目結果」「測項結果」→ 使用 query_project_fw_test_jobs（返回 Pass/Fail 清單）
  - 「統計」「完成率」「進度」「樣本」→ 使用此意圖 query_fw_detail_summary

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
  - 「XX 近一個月有哪些 FW」「XX 專案近一個月的 FW 版本」
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
  - date_range (選填，'this_month'、'last_month'、'this_week'、'last_week'、'recent'、'recent_month')
  - sub_version (選填，Sub Version 代碼如 AA、AB、AC、AD)
- 【date_range 關鍵字對應】- 【必須嚴格遵守】
  - 「本月」「這個月」→ date_range: "this_month"
  - 「上個月」「上月」→ date_range: "last_month"（特指上一個完整的月份）
  - 「近一個月」「最近一個月」「近30天」→ date_range: "recent_month"（從今天往回推30天）【重要：不是 last_month！】
  - 「最近」「近期」→ date_range: "recent"（最近30天）
  - 「本週」「這週」→ date_range: "this_week"
  - 「上週」→ date_range: "last_week"
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

### 27. query_supported_capacities - 查詢專案 FW 支援的容量 (Phase 14 新增)
用戶想知道某專案特定 FW 版本支援哪些儲存容量時使用。
這是查詢該專案 FW 版本的容量支援範圍（256GB/512GB/1024GB/2048GB/4096GB/8192GB）。
- 常見問法：
  - 「Springsteen FW PH10YC3H 支援哪些容量」「Springsteen 這版韌體有支援幾種容量」
  - 「DEMETER 的 Y1114B 有幾種容量」「TITAN 最新 FW 支援多大容量」
  - 「Channel 這個版本有支援 4TB 嗎」「XX FW 最大支援到多少容量」
  - 「Springsteen GD10YBJD 可以用 1TB 嗎」「XX 專案 FW YYY 有 2TB 版本嗎」
  - 「這個案子 PH10YC3H 有支援 512GB 和 1024GB 嗎」
- 參數：
  - project_name (專案名稱，必須)
  - fw_version (FW 版本，必須)
- 【重要區分】
  - 如果用戶問「XX 有哪些 sub version / 容量版本」→ 使用 list_sub_versions（查詢 Sub Version）
  - 如果用戶問「XX FW YYY 支援哪些容量」→ 使用 query_supported_capacities（查詢 FW 容量支援）
  - 如果用戶問「XX 1TB 版本的測試結果」→ 使用 query_project_test_by_capacity（按容量查測試）
  - 關鍵判斷：
    - 有專案名稱 + 有 FW 版本 + 問「支援/有哪些容量」→ query_supported_capacities
    - 有專案名稱 + 問「有哪些 sub version / 容量版本」→ list_sub_versions
    - 有專案名稱 + 有容量 + 問測試結果 → query_project_test_by_capacity

### 28. query_project_known_issues - 查詢專案 Known Issues (Phase 15 新增)
用戶想知道某個專案有哪些 Known Issues 時使用。
Known Issues 是指專案中已知的問題清單，包含 Issue ID、測項名稱、案例資訊、JIRA 連結等。
- 常見問法：
  - 「DEMETER 專案有哪些 Known Issues」「DEMETER 的已知問題」
  - 「Channel 有什麼 known issue」「列出 Springsteen 的 issues」
  - 「XX 專案有幾個 known issue」「查詢 XX 的問題清單」
  - 「XX 案子有哪些已知問題」「XX 的 known issues 列表」
  - 「XX 專案的 Issue 有哪些」「顯示 XX 的 known issue」
- 參數：
  - project_name (專案名稱，必須)
  - show_disabled (選填，是否顯示已停用的 Issues，預設 true)
- 【重要區分】
  - 如果用戶說「XX 有哪些 known issues」→ 使用 query_project_known_issues（查詢專案所有 Issues）
  - 如果用戶說「XX 的 YY 測項有哪些 issues」→ 使用 query_project_test_item_known_issues（按測項查詢）
  - 如果用戶說「XX 有多少個 known issues」→ 使用 count_project_known_issues（統計數量）

### 29. query_project_test_item_known_issues - 按 Test Item 查詢 Known Issues (Phase 15 新增)
用戶想知道某個專案特定測項（Test Item）有哪些 Known Issues 時使用。
- 常見問法：
  - 「DEMETER 的 Sequential Read 測項有哪些 known issues」
  - 「Channel 的 NVMe Compliance 有什麼已知問題」
  - 「XX 專案 Power Cycle 測項的 issues」
  - 「查詢 XX 的 Hot Plug 有哪些 known issue」
  - 「XX 案子的 Random Write 測試有什麼問題」
- 參數：
  - project_name (專案名稱，必須)
  - test_item (測試項目名稱，必須)
  - show_disabled (選填，是否顯示已停用的 Issues，預設 true)
- 【重要區分】
  - 有專案名稱 + 有測項名稱 + 問「有哪些 issues」→ query_project_test_item_known_issues
  - 有專案名稱 + 無測項名稱 + 問「有哪些 issues」→ query_project_known_issues

### 30. count_project_known_issues - 統計專案 Known Issues 數量 (Phase 15 新增)
用戶想知道某個專案有多少 Known Issues 時使用。
- 常見問法：
  - 「DEMETER 有幾個 Known Issues」「DEMETER 的 issues 數量」
  - 「Channel 有多少已知問題」「Springsteen 有多少 issue」
  - 「XX 專案總共有幾個 known issue」「統計 XX 的問題數量」
  - 「XX 案子有多少個 issues」「XX 的 known issues 有幾個」
- 參數：
  - project_name (專案名稱，必須)
  - show_disabled (選填，是否包含已停用的 Issues，預設 true)
- 【重要區分】
  - 如果用戶問「有幾個」「有多少」「數量」「統計」→ 使用 count_project_known_issues
  - 如果用戶問「有哪些」「列出」「是什麼」→ 使用 query_project_known_issues

### 31. rank_projects_by_known_issues - 排名專案 Known Issues 數量 (Phase 15 新增)
用戶想比較多個專案的 Known Issues 數量，看哪個專案問題最多/最少時使用。
- 常見問法：
  - 「哪個專案的 known issues 最多」「known issues 最多的案子」
  - 「比較各專案的 issue 數量」「專案問題排名」
  - 「哪些案子 issue 比較多」「排列各專案的已知問題數」
  - 「列出各專案 known issues 數量」「專案 issues 統計排名」
- 參數：
  - top_n (選填，返回前 N 個專案，預設 10)
  - customer (選填，限定特定客戶的專案)
- 【重要區分】
  - 如果用戶問「XX 專案有幾個 issues」→ 使用 count_project_known_issues（單一專案）
  - 如果用戶問「哪個專案 issues 最多」「排名」「比較」→ 使用 rank_projects_by_known_issues（跨專案比較）

### 32. query_known_issues_by_creator - 按建立者查詢 Known Issues (Phase 15 新增)
用戶想知道某人建立了哪些 Known Issues 時使用。
- 常見問法：
  - 「Ryder 建立了哪些 known issues」「ryder.lin 的 issues」
  - 「誰建立的 issues 最多」「Kevin 有建立哪些 known issue」
  - 「列出 XX 建立的問題」「查詢 YY 創建的 issues」
- 參數：
  - creator (建立者名稱，必須)
  - project_name (選填，限定特定專案)
- 【重要區分】
  - 如果用戶說「Ryder 負責哪些專案」→ 使用 query_projects_by_pl（專案負責人）
  - 如果用戶說「Ryder 建立了哪些 issues」→ 使用 query_known_issues_by_creator（Issues 建立者）

### 33. list_known_issues_creators - 列出 Known Issues 建立者清單 (Phase 15 新增)
用戶想知道有哪些人建立過 Known Issues 時使用。
- 常見問法：
  - 「誰有建立過 known issues」「issues 的建立者有哪些人」
  - 「列出建立過問題的人」「哪些人有建立 issue」
  - 「XX 專案的 issues 是誰建立的」「known issues 作者列表」
- 參數：
  - project_name (選填，限定特定專案)
- 【重要區分】
  - 如果用戶問「誰建立了哪些 issues」（想看詳細內容）→ 使用 query_known_issues_by_creator
  - 如果用戶問「有哪些人建立過 issues」（只要人員清單）→ 使用 list_known_issues_creators

### 34. query_known_issues_with_jira - 查詢有 JIRA 的 Known Issues (Phase 15 新增)
用戶想查詢有關聯 JIRA ticket 的 Known Issues 時使用。
- 常見問法：
  - 「DEMETER 有哪些 issues 有 JIRA」「有 JIRA 連結的 known issues」
  - 「XX 專案哪些 issues 有開 JIRA」「列出有 ticket 的 issues」
  - 「哪些問題有關聯 JIRA」「已建立 JIRA 的 issues」
- 參數：
  - project_name (選填，限定特定專案)
- 【重要區分】
  - 如果用戶問「有 JIRA 的 issues」→ 使用 query_known_issues_with_jira
  - 如果用戶問「沒有 JIRA 的 issues」→ 使用 query_known_issues_without_jira

### 35. query_known_issues_without_jira - 查詢沒有 JIRA 的 Known Issues (Phase 15 新增)
用戶想查詢尚未建立 JIRA ticket 的 Known Issues 時使用。
- 常見問法：
  - 「DEMETER 有哪些 issues 還沒開 JIRA」「沒有 JIRA 的 known issues」
  - 「XX 專案哪些問題還沒建 ticket」「缺少 JIRA 連結的 issues」
  - 「哪些 issues 需要開 JIRA」「尚未建立 JIRA 的問題」
- 參數：
  - project_name (選填，限定特定專案)
- 【重要區分】
  - 如果用戶問「沒有 JIRA 的 issues」「還沒開 JIRA」→ 使用 query_known_issues_without_jira
  - 如果用戶問「有 JIRA 的 issues」→ 使用 query_known_issues_with_jira

### 36. query_recent_known_issues - 查詢最近的 Known Issues (Phase 15 新增)
用戶想查詢最近新增的 Known Issues 時使用。
- 常見問法：
  - 「最近有哪些新的 known issues」「最新的 issues」
  - 「這週新增的問題」「今天有建立什麼 issue」
  - 「XX 專案最近有新的 issues 嗎」「近期的 known issues」
  - 「最近一週的 issues」「本月新增的問題」
- 參數：
  - project_name (選填，限定特定專案)
  - days (選填，最近幾天，預設 7)
  - date_range (選填，'today'、'this_week'、'this_month')
- 【重要區分】
  - 如果用戶問「最近」「最新」「這週」「今天」→ 使用 query_recent_known_issues
  - 如果用戶指定具體日期範圍 → 使用 query_known_issues_by_date_range

### 37. query_known_issues_by_date_range - 按日期範圍查詢 Known Issues (Phase 15 新增)
用戶想查詢特定日期範圍內建立的 Known Issues 時使用。
- 常見問法：
  - 「2025年1月的 known issues」「1月建立的問題」
  - 「XX 專案 2024年有多少 issues」「去年的 known issues」
  - 「2025/01/01 到 2025/01/31 的 issues」「上個月建立的問題」
- 參數：
  - project_name (選填，限定特定專案)
  - start_date (選填，開始日期，格式 YYYY-MM-DD)
  - end_date (選填，結束日期，格式 YYYY-MM-DD)
  - year (選填，年份)
  - month (選填，月份)
- 【重要區分】
  - 如果用戶指定具體日期範圍 → 使用 query_known_issues_by_date_range
  - 如果用戶問「最近」「最新」→ 使用 query_recent_known_issues

### 38. search_known_issues_by_keyword - 關鍵字搜尋 Known Issues (Phase 15 新增)
用戶想用關鍵字搜尋 Known Issues 時使用。
可搜尋 Issue ID、測項名稱、案例名稱、備註等欄位。
- 常見問法：
  - 「搜尋 known issues 中有 timeout 的」「找有 error 的 issues」
  - 「XX 專案有沒有跟 power 相關的 issue」「搜尋 NVMe 相關問題」
  - 「查詢包含 compliance 的 issues」「找 fail 相關的 known issue」
- 參數：
  - keyword (關鍵字，必須)
  - project_name (選填，限定特定專案)
  - search_fields (選填，搜尋欄位，預設 ['issue_id', 'test_item_name', 'case_name', 'note'])
- 【重要區分】
  - 如果用戶明確想搜尋關鍵字 → 使用 search_known_issues_by_keyword
  - 如果用戶問特定測項的 issues → 使用 query_project_test_item_known_issues

### 39. query_all_known_issues_by_test_item - 跨專案搜尋 Test Item 的 Known Issues (Phase 15 新增)
用戶想搜尋所有專案中某個 Test Item 相關的 Known Issues 時使用。
這是跨專案的搜尋，會列出所有專案中該測項相關的問題。
- 常見問法：
  - 「哪些專案的 Sequential Read 有 known issues」
  - 「所有專案的 NVMe Compliance issues」
  - 「跨專案查詢 Power Cycle 的問題」
  - 「各案子的 Hot Plug 測試有哪些 issues」
- 參數：
  - test_item (測試項目名稱，必須)
  - customer (選填，限定特定客戶的專案)
- 【重要區分】
  - 如果有專案名稱 + 測項名稱 → 使用 query_project_test_item_known_issues（單一專案）
  - 如果無專案名稱 + 測項名稱 → 使用 query_all_known_issues_by_test_item（跨專案搜尋）
  - 關鍵判斷：
    - 有專案名稱 + 測項名稱 → 單一專案查詢
    - 無專案名稱 + 測項名稱 + 問「哪些專案」→ 跨專案搜尋

### 40. query_project_fw_test_jobs - 查詢專案 FW 測試工作詳細結果 (Phase 16 新增)
用戶想查詢特定專案特定 FW 版本的「完整測試項目結果」（含 Test Category、Test Item、Capacity、Test Status 等）時使用。
這是查詢測試工作的完整詳細資訊，包括每個測試項目的執行狀態。
- 常見問法：
  - 「PM9M1 的 HHB0YBC1 測項結果」「PM9M1 HHB0YBC1 的測試項目結果」
  - 「查詢 XX 專案 FW YYY 的測項結果」「XX YYY 的測項狀態」
  - 「XX 專案 YYY 版本的測試項目」「列出 XX FW YYY 的所有測試」
  - 「XX 的 YYY 有哪些測試項目」「XX YYY 有哪些 Fail」
  - 「XX FW YYY 的測試工作結果」「XX YYY 的 test jobs」
  - 「Springsteen 的 GD10YBJD 測項結果」
  - 「DEMETER Y1114B 的測試項目結果」
  - 「列出 XX YYY 的測試結果」「XX YYY 哪些測試通過」
- 參數：
  - project_name (專案名稱，必須，可以是簡短名稱如 PM9M1、Springsteen)
  - fw_version (FW 版本，必須)
  - test_tool_key (選填，測試工具篩選)
- 【關鍵詞區分】
  - 詳細測項類關鍵詞（使用此意圖）：「測項結果」「測試項目結果」「哪些測項」「哪些 Fail」「哪些 Pass」「列出測試」「有哪些測試項目」
  - 統計結果類關鍵詞（使用 query_fw_detail_summary）：「測試結果」「完成率」「進度」「統計」「樣本使用率」「執行率」「測試概覽」
  - 【重要】「測試結果」→ query_fw_detail_summary（附件1格式：詳細統計表）
  - 【重要】「測試項目結果」「測項結果」→ query_project_fw_test_jobs（附件2格式：Pass/Fail清單）
- 【重要區分】
  - 如果用戶問「XX FW YYY 的測項結果」「XX YYY 有哪些 Fail」→ 使用此意圖（完整測試結果）
  - 如果用戶問「XX FW YYY 測了幾個」「XX YYY 通過率」→ 使用 query_project_test_summary_by_fw（統計摘要）
  - 如果用戶問「XX FW YYY 有哪些測試類別」→ 使用 query_project_fw_test_categories（類別列表）
  - 如果用戶問「XX FW YYY 有哪些測項」→ 使用 query_project_fw_all_test_items（測項列表）
- 【與其他意圖的差異】
  - query_project_fw_test_jobs: 返回測試工作的執行結果（Pass/Fail/Status）
  - query_project_fw_all_test_items: 返回測試項目列表（不含執行結果）
  - query_project_test_summary_by_fw: 返回統計摘要（通過率、完成率等）

### 41. compare_fw_test_jobs - 比較多個 FW 版本的測試項目結果差異 (Phase 17/18)
用戶想比較同一專案的多個 FW 版本的「測試項目結果差異」時使用。
支援 2-10 個 FW 版本同時比較。包括：狀態變化（Pass→Fail 或 Fail→Pass）、新增項目、移除項目。
- 常見問法：
  - 「比較 XX 專案 FW1 和 FW2 的測項結果」「對比 XX FW1 與 FW2 的測試項目差異」
  - 「比較 XX FW1 FW2 FW3 的測試結果」「對比 XX 三版 FW 的測試項目」
  - 「比較 springsteen 幾版 FW 的測試項目結果 GM10YCBM_Opal PH10YC3H_Pyrite_512Byte GD10YBSD_Opal」
  - 「XX FW1 和 FW2 和 FW3 的測試差異」「XX 版本 FW1 FW2 FW3 FW4 的比較」
  - 「比較 Springsteen PH10YC3H_Pyrite_4K 和 GD10YBJD 的測項結果」
  - 「XX 的 FW1 和 FW2 哪些測試變成 Fail」
  - 「XX FW1 vs FW2 測試結果差異」
  - 【🆕 使用 latest_count】「XX 最新 5 個 FW 版本測試項目結果比較」「XX 最近 3 個 FW 測項差異」
- 參數：
  - project_name (專案名稱，必須)
  - fw_versions (FW 版本陣列，包含 2-10 個版本) 或
  - latest_count (選填，自動取最近 N 個版本，如 2、3、5)
  - test_category (選填，篩選特定測試類別)
- 【關鍵詞識別】
  - 關鍵詞：「比較」「對比」「差異」「vs」「和...的」「與...的」+ 多個 FW 版本 + 「測項」「測試項目」「測試項目結果」
  - 【重要】必須同時出現：專案名稱 + (至少兩個 FW 版本 或 latest_count) + 比較/差異關鍵詞
- 【⚠️⚠️⚠️ 超級重要區分：「測試結果」vs「測試項目結果」⚠️⚠️⚠️】
  - compare_latest_fw / compare_multiple_fw：用於「測試結果比較」「FW 比較」「版本趨勢」→ 返回整體統計（通過率、熱力圖、趨勢圖）
  - compare_fw_test_jobs：用於「測試項目結果比較」「測項結果比較」「測項差異」→ 返回 Pass/Fail 狀態變化清單
  - 【關鍵字判斷】
    - 「測試結果」（不含「測試項目」或「測項」）→ compare_latest_fw / compare_multiple_fw
    - 「測試項目結果」「測項結果」「測項比較」「測項差異」→ compare_fw_test_jobs
  - 【範例】
    - 「Springsteen 最新 5 個 FW 版本測試結果比較」→ compare_multiple_fw（整體統計趨勢）
    - 「Springsteen 最新 5 個 FW 版本測試項目結果比較」→ compare_fw_test_jobs（Pass/Fail 清單）
- 【與其他意圖的差異】
  - compare_fw_test_jobs: 比較測試項目結果差異（Pass/Fail 狀態變化）
  - compare_latest_fw / compare_multiple_fw: 比較版本的統計數據（通過率、完成率變化、趨勢圖）
  - query_project_fw_test_jobs: 查詢單一版本的測試項目結果

### 42. unknown - 無法識別的意圖
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

# Phase 4: 按 FW 版本查詢測試統計（統計類查詢）
輸入：DEMETER 專案 FW Y1114B 測了幾個
輸出：{"intent": "query_project_test_summary_by_fw", "parameters": {"project_name": "DEMETER", "fw_version": "Y1114B"}, "confidence": 0.95}

輸入：Channel 的 82CBW5QF 版本通過率是多少
輸出：{"intent": "query_project_test_summary_by_fw", "parameters": {"project_name": "Channel", "fw_version": "82CBW5QF"}, "confidence": 0.93}

輸入：A400 專案 X0325A 的測試進度如何
輸出：{"intent": "query_project_test_summary_by_fw", "parameters": {"project_name": "A400", "fw_version": "X0325A"}, "confidence": 0.93}

輸入：想看一下 Frey3B 的 FWX0926C 測試狀況
輸出：{"intent": "query_project_test_summary_by_fw", "parameters": {"project_name": "Frey3B", "fw_version": "FWX0926C"}, "confidence": 0.90}

輸入：Bennington 專案韌體 Y1103C 有多少測試通過
輸出：{"intent": "query_project_test_summary_by_fw", "parameters": {"project_name": "Bennington", "fw_version": "Y1103C"}, "confidence": 0.90}

輸入：Springsteen 專案 G200X6EC 的統計
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

輸入：Springsteen 最新兩個 FW 版本比較
輸出：{"intent": "compare_latest_fw", "parameters": {"project_name": "Springsteen"}, "confidence": 0.96}

輸入：比較 DEMETER 最近兩個版本
輸出：{"intent": "compare_latest_fw", "parameters": {"project_name": "DEMETER"}, "confidence": 0.93}

輸入：DEMETER 最新兩個 FW 比較
輸出：{"intent": "compare_latest_fw", "parameters": {"project_name": "DEMETER"}, "confidence": 0.95}

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

輸入：pvf01 的 FW 版本列表
輸出：{"intent": "list_fw_versions", "parameters": {"project_name": "pvf01"}, "confidence": 0.95}

輸入：Springsteen 有那些 FW版本
輸出：{"intent": "list_fw_versions", "parameters": {"project_name": "Springsteen"}, "confidence": 0.95}

輸入：TITAN 的 FW 版本列表
輸出：{"intent": "list_fw_versions", "parameters": {"project_name": "TITAN"}, "confidence": 0.95}

輸入：Garuda FW 版本
輸出：{"intent": "list_fw_versions", "parameters": {"project_name": "Garuda"}, "confidence": 0.90}

輸入：比較 Springsteen 的 G200X6EC、G200X5DC、G200X4CB 三個版本
輸出：{"intent": "compare_multiple_fw", "parameters": {"project_name": "Springsteen", "fw_versions": ["G200X6EC", "G200X5DC", "G200X4CB"]}, "confidence": 0.95}

輸入：DEMETER 最近三個版本的趨勢
輸出：{"intent": "compare_multiple_fw", "parameters": {"project_name": "DEMETER", "latest_count": 3}, "confidence": 0.93}

輸入：Springsteen 最新 3 個 FW 版本比較
輸出：{"intent": "compare_multiple_fw", "parameters": {"project_name": "Springsteen", "latest_count": 3}, "confidence": 0.95}

輸入：Springsteen 最近三個 FW 比較
輸出：{"intent": "compare_multiple_fw", "parameters": {"project_name": "Springsteen", "latest_count": 3}, "confidence": 0.94}

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

# === 意圖 13 範例：query_fw_detail_summary（測試結果 = 統計表格）===
輸入：Springsteen 專案 G200X6EC 的測試結果
輸出：{"intent": "query_fw_detail_summary", "parameters": {"project_name": "Springsteen", "fw_version": "G200X6EC"}, "confidence": 0.95}

輸入：PM9M1 HHB0YBC1 的測試結果
輸出：{"intent": "query_fw_detail_summary", "parameters": {"project_name": "PM9M1", "fw_version": "HHB0YBC1"}, "confidence": 0.95}

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

輸入：PVF01 近一個月有那些 FW
輸出：{"intent": "list_fw_by_date_range", "parameters": {"project_name": "PVF01", "date_range": "recent_month"}, "confidence": 0.94}

輸入：Springsteen 最近一個月的 FW
輸出：{"intent": "list_fw_by_date_range", "parameters": {"project_name": "Springsteen", "date_range": "recent_month"}, "confidence": 0.94}

輸入：DEMETER 近30天有哪些 FW
輸出：{"intent": "list_fw_by_date_range", "parameters": {"project_name": "DEMETER", "date_range": "recent_month"}, "confidence": 0.93}

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

# Phase 14: 查詢專案 FW 支援的容量
輸入：Springsteen FW PH10YC3H 支援哪些容量
輸出：{"intent": "query_supported_capacities", "parameters": {"project_name": "Springsteen", "fw_version": "PH10YC3H"}, "confidence": 0.95}

輸入：DEMETER 的 Y1114B 有幾種容量
輸出：{"intent": "query_supported_capacities", "parameters": {"project_name": "DEMETER", "fw_version": "Y1114B"}, "confidence": 0.94}

輸入：TITAN 最新 FW 支援多大容量
輸出：{"intent": "query_supported_capacities", "parameters": {"project_name": "TITAN", "fw_version": "latest"}, "confidence": 0.93}

輸入：Channel GD10YBJD 可以用 4TB 嗎
輸出：{"intent": "query_supported_capacities", "parameters": {"project_name": "Channel", "fw_version": "GD10YBJD"}, "confidence": 0.92}

輸入：Springsteen 這版韌體有支援 512GB 和 1024GB 嗎
輸出：{"intent": "query_supported_capacities", "parameters": {"project_name": "Springsteen", "fw_version": "current"}, "confidence": 0.90}

輸入：XX 專案 FW YYY 最大支援到多少容量
輸出：{"intent": "query_supported_capacities", "parameters": {"project_name": "XX", "fw_version": "YYY"}, "confidence": 0.91}

# Phase 15: Known Issues 查詢
輸入：DEMETER 專案有哪些 Known Issues
輸出：{"intent": "query_project_known_issues", "parameters": {"project_name": "DEMETER"}, "confidence": 0.95}

輸入：Channel 有什麼 known issue
輸出：{"intent": "query_project_known_issues", "parameters": {"project_name": "Channel"}, "confidence": 0.93}

輸入：列出 Springsteen 的已知問題
輸出：{"intent": "query_project_known_issues", "parameters": {"project_name": "Springsteen"}, "confidence": 0.92}

輸入：XX 專案有幾個 known issue
輸出：{"intent": "query_project_known_issues", "parameters": {"project_name": "XX"}, "confidence": 0.90}

輸入：查詢 TITAN 的問題清單
輸出：{"intent": "query_project_known_issues", "parameters": {"project_name": "TITAN"}, "confidence": 0.92}

輸入：DEMETER 的 Sequential Read 測項有哪些 known issues
輸出：{"intent": "query_project_test_item_known_issues", "parameters": {"project_name": "DEMETER", "test_item": "Sequential Read"}, "confidence": 0.95}

輸入：Channel 的 NVMe Compliance 有什麼已知問題
輸出：{"intent": "query_project_test_item_known_issues", "parameters": {"project_name": "Channel", "test_item": "NVMe Compliance"}, "confidence": 0.93}

輸入：Springsteen 專案 Power Cycle 測項的 issues
輸出：{"intent": "query_project_test_item_known_issues", "parameters": {"project_name": "Springsteen", "test_item": "Power Cycle"}, "confidence": 0.92}

輸入：XX 案子的 Random Write 測試有什麼問題
輸出：{"intent": "query_project_test_item_known_issues", "parameters": {"project_name": "XX", "test_item": "Random Write"}, "confidence": 0.90}

輸入：DEMETER 有幾個 Known Issues
輸出：{"intent": "count_project_known_issues", "parameters": {"project_name": "DEMETER"}, "confidence": 0.95}

輸入：Channel 有多少已知問題
輸出：{"intent": "count_project_known_issues", "parameters": {"project_name": "Channel"}, "confidence": 0.93}

輸入：Springsteen 的 issues 數量
輸出：{"intent": "count_project_known_issues", "parameters": {"project_name": "Springsteen"}, "confidence": 0.92}

輸入：統計 XX 的問題數量
輸出：{"intent": "count_project_known_issues", "parameters": {"project_name": "XX"}, "confidence": 0.90}

輸入：哪個專案的 known issues 最多
輸出：{"intent": "rank_projects_by_known_issues", "parameters": {}, "confidence": 0.95}

輸入：比較各專案的 issue 數量
輸出：{"intent": "rank_projects_by_known_issues", "parameters": {}, "confidence": 0.93}

輸入：專案問題排名
輸出：{"intent": "rank_projects_by_known_issues", "parameters": {}, "confidence": 0.92}

輸入：WD 的案子哪個 issues 最多
輸出：{"intent": "rank_projects_by_known_issues", "parameters": {"customer": "WD"}, "confidence": 0.90}

輸入：Ryder 建立了哪些 known issues
輸出：{"intent": "query_known_issues_by_creator", "parameters": {"creator": "Ryder"}, "confidence": 0.95}

輸入：ryder.lin 的 issues
輸出：{"intent": "query_known_issues_by_creator", "parameters": {"creator": "ryder.lin"}, "confidence": 0.93}

輸入：Kevin 在 DEMETER 建立了哪些問題
輸出：{"intent": "query_known_issues_by_creator", "parameters": {"creator": "Kevin", "project_name": "DEMETER"}, "confidence": 0.92}

輸入：誰有建立過 known issues
輸出：{"intent": "list_known_issues_creators", "parameters": {}, "confidence": 0.95}

輸入：DEMETER 專案的 issues 是誰建立的
輸出：{"intent": "list_known_issues_creators", "parameters": {"project_name": "DEMETER"}, "confidence": 0.93}

輸入：有哪些人建立過問題
輸出：{"intent": "list_known_issues_creators", "parameters": {}, "confidence": 0.92}

輸入：DEMETER 有哪些 issues 有 JIRA
輸出：{"intent": "query_known_issues_with_jira", "parameters": {"project_name": "DEMETER"}, "confidence": 0.95}

輸入：有 JIRA 連結的 known issues
輸出：{"intent": "query_known_issues_with_jira", "parameters": {}, "confidence": 0.93}

輸入：哪些問題有關聯 JIRA
輸出：{"intent": "query_known_issues_with_jira", "parameters": {}, "confidence": 0.92}

輸入：DEMETER 有哪些 issues 還沒開 JIRA
輸出：{"intent": "query_known_issues_without_jira", "parameters": {"project_name": "DEMETER"}, "confidence": 0.95}

輸入：沒有 JIRA 的 known issues
輸出：{"intent": "query_known_issues_without_jira", "parameters": {}, "confidence": 0.93}

輸入：哪些 issues 需要開 JIRA
輸出：{"intent": "query_known_issues_without_jira", "parameters": {}, "confidence": 0.92}

輸入：最近有哪些新的 known issues
輸出：{"intent": "query_recent_known_issues", "parameters": {}, "confidence": 0.95}

輸入：DEMETER 專案最近有新的 issues 嗎
輸出：{"intent": "query_recent_known_issues", "parameters": {"project_name": "DEMETER"}, "confidence": 0.93}

輸入：這週新增的問題
輸出：{"intent": "query_recent_known_issues", "parameters": {"date_range": "this_week"}, "confidence": 0.92}

輸入：今天有建立什麼 issue
輸出：{"intent": "query_recent_known_issues", "parameters": {"date_range": "today"}, "confidence": 0.90}

輸入：2025年1月的 known issues
輸出：{"intent": "query_known_issues_by_date_range", "parameters": {"year": 2025, "month": 1}, "confidence": 0.95}

輸入：DEMETER 專案 2024年有多少 issues
輸出：{"intent": "query_known_issues_by_date_range", "parameters": {"project_name": "DEMETER", "year": 2024}, "confidence": 0.93}

輸入：上個月建立的問題
輸出：{"intent": "query_known_issues_by_date_range", "parameters": {"date_range": "last_month"}, "confidence": 0.92}

輸入：搜尋 known issues 中有 timeout 的
輸出：{"intent": "search_known_issues_by_keyword", "parameters": {"keyword": "timeout"}, "confidence": 0.95}

輸入：DEMETER 有沒有跟 power 相關的 issue
輸出：{"intent": "search_known_issues_by_keyword", "parameters": {"keyword": "power", "project_name": "DEMETER"}, "confidence": 0.93}

輸入：找有 error 的 issues
輸出：{"intent": "search_known_issues_by_keyword", "parameters": {"keyword": "error"}, "confidence": 0.92}

輸入：哪些專案的 Sequential Read 有 known issues
輸出：{"intent": "query_all_known_issues_by_test_item", "parameters": {"test_item": "Sequential Read"}, "confidence": 0.95}

輸入：所有專案的 NVMe Compliance issues
輸出：{"intent": "query_all_known_issues_by_test_item", "parameters": {"test_item": "NVMe Compliance"}, "confidence": 0.93}

輸入：各案子的 Hot Plug 測試有哪些 issues
輸出：{"intent": "query_all_known_issues_by_test_item", "parameters": {"test_item": "Hot Plug"}, "confidence": 0.92}

輸入：WD 的專案中 Power Cycle 有哪些 issues
輸出：{"intent": "query_all_known_issues_by_test_item", "parameters": {"test_item": "Power Cycle", "customer": "WD"}, "confidence": 0.90}

# Phase 16: 專案 FW 測試工作詳細結果查詢（詳細類查詢）
# === 意圖 40 範例：query_project_fw_test_jobs（測試項目結果 = Pass/Fail 清單）===
# 【重要】只有「測項結果」「測試項目結果」才使用此意圖，「測試結果」使用 query_fw_detail_summary
輸入：PM9M1 的 HHB0YBC1 測項結果
輸出：{"intent": "query_project_fw_test_jobs", "parameters": {"project_name": "PM9M1", "fw_version": "HHB0YBC1"}, "confidence": 0.95}

輸入：PM9M1 HHB0YBC1 的測試項目結果
輸出：{"intent": "query_project_fw_test_jobs", "parameters": {"project_name": "PM9M1", "fw_version": "HHB0YBC1"}, "confidence": 0.94}

輸入：Springsteen GD10YBJD 有哪些測項 Fail
輸出：{"intent": "query_project_fw_test_jobs", "parameters": {"project_name": "Springsteen", "fw_version": "GD10YBJD"}, "confidence": 0.93}

輸入：列出 DEMETER Y1114B 的測試項目結果
輸出：{"intent": "query_project_fw_test_jobs", "parameters": {"project_name": "DEMETER", "fw_version": "Y1114B"}, "confidence": 0.92}

輸入：列出 Channel FW 82CBW5QF 的所有測試項目
輸出：{"intent": "query_project_fw_test_jobs", "parameters": {"project_name": "Channel", "fw_version": "82CBW5QF"}, "confidence": 0.91}

輸入：XX 的 YYY 有哪些測試項目
輸出：{"intent": "query_project_fw_test_jobs", "parameters": {"project_name": "XX", "fw_version": "YYY"}, "confidence": 0.90}

輸入：A400 專案 X0325A 版本的測試項目結果
輸出：{"intent": "query_project_fw_test_jobs", "parameters": {"project_name": "A400", "fw_version": "X0325A"}, "confidence": 0.91}

# === 意圖 41 範例：compare_fw_test_jobs（比較多個 FW 版本的測試項目結果差異）===
# 2 版本比較
輸入：比較 Springsteen PH10YC3H_Pyrite_4K 和 GD10YBJD_Opal 的測項結果
輸出：{"intent": "compare_fw_test_jobs", "parameters": {"project_name": "Springsteen", "fw_versions": ["PH10YC3H_Pyrite_4K", "GD10YBJD_Opal"]}, "confidence": 0.95}

輸入：對比 PM9M1 HHB0YBC1 與 HHB0YBC2 測試項目差異
輸出：{"intent": "compare_fw_test_jobs", "parameters": {"project_name": "PM9M1", "fw_versions": ["HHB0YBC1", "HHB0YBC2"]}, "confidence": 0.94}

輸入：DEMETER Y1114B 和 Y1115A 的測試差異
輸出：{"intent": "compare_fw_test_jobs", "parameters": {"project_name": "DEMETER", "fw_versions": ["Y1114B", "Y1115A"]}, "confidence": 0.93}

# 3 版本比較
輸入：比較 springsteen 三版 FW GM10YCBM_Opal PH10YC3H_Pyrite_512Byte GD10YBSD_Opal 的測試結果
輸出：{"intent": "compare_fw_test_jobs", "parameters": {"project_name": "springsteen", "fw_versions": ["GM10YCBM_Opal", "PH10YC3H_Pyrite_512Byte", "GD10YBSD_Opal"]}, "confidence": 0.95}

輸入：PM9M1 HHB0YBC1 和 HHB0YBC2 和 HHB0YBC3 的測試項目比較
輸出：{"intent": "compare_fw_test_jobs", "parameters": {"project_name": "PM9M1", "fw_versions": ["HHB0YBC1", "HHB0YBC2", "HHB0YBC3"]}, "confidence": 0.94}

# 5 版本比較
輸入：比較 springsteen 幾版 FW 的測試項目結果 GM10YCBM_Opal PH10YC3H_Pyrite_512Byte GD10YBSD_Opal PH10YC3H_Pyrite_4K PH10YC3H_Opal_4K
輸出：{"intent": "compare_fw_test_jobs", "parameters": {"project_name": "springsteen", "fw_versions": ["GM10YCBM_Opal", "PH10YC3H_Pyrite_512Byte", "GD10YBSD_Opal", "PH10YC3H_Pyrite_4K", "PH10YC3H_Opal_4K"]}, "confidence": 0.95}

輸入：Channel 82CBW5QF 和 82CBW6QF 和 82CBW7QF 和 82CBW8QF 哪些測試變成 Fail
輸出：{"intent": "compare_fw_test_jobs", "parameters": {"project_name": "Channel", "fw_versions": ["82CBW5QF", "82CBW6QF", "82CBW7QF", "82CBW8QF"]}, "confidence": 0.93}

輸入：XX FW1 vs FW2 測試結果差異
輸出：{"intent": "compare_fw_test_jobs", "parameters": {"project_name": "XX", "fw_versions": ["FW1", "FW2"]}, "confidence": 0.91}

# 🆕 使用 latest_count 的 compare_fw_test_jobs（測試項目結果比較）
輸入：Springsteen 最新 5 個 FW 版本測試項目結果比較
輸出：{"intent": "compare_fw_test_jobs", "parameters": {"project_name": "Springsteen", "latest_count": 5}, "confidence": 0.95}

輸入：DEMETER 最近 3 個 FW 版本測項結果差異
輸出：{"intent": "compare_fw_test_jobs", "parameters": {"project_name": "DEMETER", "latest_count": 3}, "confidence": 0.94}

輸入：Channel 最新 4 個 FW 的測項比較
輸出：{"intent": "compare_fw_test_jobs", "parameters": {"project_name": "Channel", "latest_count": 4}, "confidence": 0.93}

輸入：Springsteen 最新五個 FW 測試項目比較
輸出：{"intent": "compare_fw_test_jobs", "parameters": {"project_name": "Springsteen", "latest_count": 5}, "confidence": 0.94}

# 🔥 超級重要區分：「測試結果」vs「測試項目結果」
# 「測試結果」→ compare_multiple_fw（整體統計趨勢）
輸入：Springsteen 最新 5 個 FW 版本測試結果比較
輸出：{"intent": "compare_multiple_fw", "parameters": {"project_name": "Springsteen", "latest_count": 5}, "confidence": 0.95}

輸入：DEMETER 最近三個版本測試結果趨勢
輸出：{"intent": "compare_multiple_fw", "parameters": {"project_name": "DEMETER", "latest_count": 3}, "confidence": 0.94}

輸入：Channel 最新 4 個 FW 的比較
輸出：{"intent": "compare_multiple_fw", "parameters": {"project_name": "Channel", "latest_count": 4}, "confidence": 0.93}

# 「測試項目結果」→ compare_fw_test_jobs（Pass/Fail 清單）
輸入：Springsteen 最新 5 個 FW 版本測試項目結果比較
輸出：{"intent": "compare_fw_test_jobs", "parameters": {"project_name": "Springsteen", "latest_count": 5}, "confidence": 0.95}

輸入：DEMETER 最近三個版本測項結果差異
輸出：{"intent": "compare_fw_test_jobs", "parameters": {"project_name": "DEMETER", "latest_count": 3}, "confidence": 0.94}

輸入：Channel 最新 4 個 FW 的測項比較
輸出：{"intent": "compare_fw_test_jobs", "parameters": {"project_name": "Channel", "latest_count": 4}, "confidence": 0.93}

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
                # FW 日期範圍查詢別名映射（新增）
                'list_project_firmware_by_date_range': 'list_fw_by_date_range',
                'list_fw_by_date': 'list_fw_by_date_range',
                'list_fw_by_month': 'list_fw_by_date_range',
                'list_fw_by_year': 'list_fw_by_date_range',
                'list_project_fw_by_date': 'list_fw_by_date_range',
                'list_project_fw_by_month': 'list_fw_by_date_range',
                'query_fw_by_date_range': 'list_fw_by_date_range',
                'query_project_fw_by_date': 'list_fw_by_date_range',
                'get_fw_by_date_range': 'list_fw_by_date_range',
                'fw_by_date_range': 'list_fw_by_date_range',
                # FW 統計相關的別名映射
                'query_project_fw_statistics': 'query_project_test_summary_by_fw',
                'query_fw_statistics': 'query_project_test_summary_by_fw',
                'query_project_fw_summary': 'query_project_test_summary_by_fw',
                'query_fw_test_summary': 'query_project_test_summary_by_fw',
                'query_project_statistics_by_firmware': 'query_project_test_summary_by_fw',
                'query_project_fw_test_jobs_count': 'query_project_test_summary_by_fw',
                # FW 版本列表別名映射（覆蓋所有可能的變體）
                'query_project_fw_list': 'list_fw_versions',
                'query_project_fw_versions': 'list_fw_versions',
                'query_fw_list': 'list_fw_versions',
                'query_fw_versions': 'list_fw_versions',
                'query_fw_version_list': 'list_fw_versions',
                'get_fw_versions': 'list_fw_versions',
                'get_project_fw_versions': 'list_fw_versions',
                'get_fw_list': 'list_fw_versions',
                'project_fw_versions': 'list_fw_versions',
                'project_fw_list': 'list_fw_versions',
                'fw_version_list': 'list_fw_versions',
                'fw_versions': 'list_fw_versions',
                # 新增更多 LLM 可能返回的變體
                'list_project_fw_versions': 'list_fw_versions',
                'list_project_fw': 'list_fw_versions',
                'list_fw_version': 'list_fw_versions',
                'get_fw_version_list': 'list_fw_versions',
                'show_fw_versions': 'list_fw_versions',
                'show_project_fw_versions': 'list_fw_versions',
            }
            
            if raw_intent in combined_intent_mapping:
                logger.info(f"映射組合意圖 '{raw_intent}' -> '{combined_intent_mapping[raw_intent]}'")
                raw_intent = combined_intent_mapping[raw_intent]
            
            # ★★★ 通用模式匹配：處理 LLM 可能返回的 FW 相關變體 ★★★
            if raw_intent not in [e.value for e in IntentType]:
                # 模式 1：FW + 日期範圍（優先檢查，因為更具體）
                fw_date_pattern = re.compile(r'(fw|firmware).*(date|month|year|range|time)', re.IGNORECASE)
                if fw_date_pattern.search(raw_intent):
                    logger.info(f"通用模式匹配：'{raw_intent}' 匹配 FW 日期範圍模式，映射到 'list_fw_by_date_range'")
                    raw_intent = 'list_fw_by_date_range'
                else:
                    # 模式 2：FW + 版本列表（不含日期關鍵字）
                    fw_list_pattern = re.compile(r'(fw|firmware).*(version|versions|list)', re.IGNORECASE)
                    if fw_list_pattern.search(raw_intent):
                        logger.info(f"通用模式匹配：'{raw_intent}' 匹配 FW 版本列表模式，映射到 'list_fw_versions'")
                        raw_intent = 'list_fw_versions'
            
            # ★★★ 語義修正 1：「測試結果」（不含「測試項目」）應該用 query_fw_detail_summary ★★★
            # 如果查詢包含「測試結果」但不含「測試項目」「測項」，應使用意圖 13 而非意圖 40
            if raw_intent == 'query_project_fw_test_jobs':
                if '測試結果' in original_query and '測試項目' not in original_query and '測項' not in original_query:
                    logger.info(f"語義修正：查詢為「測試結果」而非「測試項目結果」，修正 '{raw_intent}' -> 'query_fw_detail_summary'")
                    raw_intent = 'query_fw_detail_summary'
            
            # ★★★ 語義修正 2：檢查查詢是否包含「統計」但被誤判為 test_jobs ★★★
            stat_keywords = ['統計', '詳細統計', '通過率', '完成率', '進度', '狀況', '測了幾個', '多少', '樣本使用率', '執行率', '失敗率', '測試概覽']
            if raw_intent == 'query_project_fw_test_jobs' and any(sk in original_query for sk in stat_keywords):
                logger.info(f"語義修正：查詢包含統計關鍵字，修正 '{raw_intent}' -> 'query_fw_detail_summary'")
                raw_intent = 'query_fw_detail_summary'
            
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
            
            # 情況 4：查詢包含「比較」「對比」關鍵字但 Dify 返回的不是比較意圖
            # 例如：「比較 Springsteen GH10Y6NH 和 GH10Y6NH_512Byte 的測項結果」應該是 compare_fw_test_jobs
            compare_keywords = ['比較', '對比', '差異', '不同', '兩個版本', '兩版']
            is_compare_query = any(kw in original_query for kw in compare_keywords)
            if is_compare_query and intent_type != IntentType.COMPARE_FW_TEST_JOBS:
                # 檢查是否包含兩個 FW 版本（用「和」分隔）
                if ' 和 ' in original_query or '和' in original_query or ' vs ' in original_query.lower():
                    logger.info(f"查詢包含比較關鍵字且有兩個版本，但 Dify 返回 '{intent_type.value}'，嘗試 fallback")
                    should_use_fallback = True
            
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
        
        # 6.5. ★★★ Known Issues 全域查詢（不需要專案名稱）★★★
        known_issues_keywords = ['known issue', 'known issues', 'known-issue', 'known-issues',
                                 '已知問題', '已知issue', 'issue', 'issues', '問題清單']
        if any(kw in query_lower for kw in known_issues_keywords):
            # 檢查是否是排名/比較查詢
            rank_keywords = ['排名', '排行', 'rank', '最多', '最少', '比較', '統計']
            if any(rk in query_lower for rk in rank_keywords):
                return IntentResult(
                    intent=IntentType.RANK_PROJECTS_BY_KNOWN_ISSUES,
                    parameters={},
                    confidence=0.7,
                    raw_response="Fallback: rank projects by known issues"
                )
            
            # 檢查是否是按建立者查詢
            creator_keywords = ['誰建立', '誰創建', '建立者', '創建者', 'creator', 'created by', 'author']
            if any(ck in query_lower for ck in creator_keywords):
                return IntentResult(
                    intent=IntentType.LIST_KNOWN_ISSUES_CREATORS,
                    parameters={},
                    confidence=0.7,
                    raw_response="Fallback: list known issues creators"
                )
            
            # 檢查是否是 JIRA 相關查詢
            jira_keywords = ['jira', '沒有jira', '無jira', '有jira']
            if any(jk in query_lower for jk in jira_keywords):
                if '沒有' in query or '無' in query or 'without' in query_lower:
                    return IntentResult(
                        intent=IntentType.QUERY_KNOWN_ISSUES_WITHOUT_JIRA,
                        parameters={},
                        confidence=0.7,
                        raw_response="Fallback: known issues without JIRA"
                    )
                else:
                    return IntentResult(
                        intent=IntentType.QUERY_KNOWN_ISSUES_WITH_JIRA,
                        parameters={},
                        confidence=0.7,
                        raw_response="Fallback: known issues with JIRA"
                    )
            
            # 檢查是否是關鍵字搜尋
            search_keywords = ['搜尋', '搜索', 'search', '查找', '找']
            if any(sk in query_lower for sk in search_keywords):
                # 嘗試提取搜尋關鍵字
                return IntentResult(
                    intent=IntentType.SEARCH_KNOWN_ISSUES_BY_KEYWORD,
                    parameters={'keyword': query},  # 使用整個查詢作為關鍵字
                    confidence=0.6,
                    raw_response="Fallback: search known issues by keyword"
                )
            
            # 檢查是否是按測試項目查詢所有專案的 Known Issues
            test_item = self._detect_test_item_for_known_issues(query)
            if test_item:
                return IntentResult(
                    intent=IntentType.QUERY_ALL_KNOWN_ISSUES_BY_TEST_ITEM,
                    parameters={'test_item': test_item},
                    confidence=0.7,
                    raw_response=f"Fallback: all known issues by test item {test_item}"
                )
        
        # 7. 日期/月份查詢 (Phase 8)
        date_result = self._detect_date_query(query)
        if date_result:
            return date_result
        
        # 8. Sub Version 相關查詢 (Phase 9)
        project_name = self._detect_project_name(query)
        detected_sub_version = self._detect_sub_version(query)
        
        # ★ 重要：如果查詢包含「比較」關鍵字，先檢查是否有兩個 FW 版本
        # 避免 Sub Version 檢測干擾 FW 版本比較查詢
        compare_keywords = ['比較', '對比', '差異', 'compare', 'vs']
        has_compare = any(kw in query for kw in compare_keywords)
        
        if has_compare:
            fw_1, fw_2 = self._detect_two_fw_versions_for_compare(query)
            if fw_1 and fw_2 and project_name:
                # 跳過 Sub Version 處理，交給第 10 步的 FW 比較邏輯
                detected_sub_version = None
        
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
        
        # 9. ★★★ Phase 17/18: 優先檢測「比較 FW 版本測試項目結果」★★★
        # 必須在「最新 FW 版本比較」之前，因為兩者都包含「比較」和「fw」關鍵字
        # 區分點：「測試項目結果」vs「統計/通過率」
        # Phase 18: 支援多版本比較 (2-10 個版本)
        if project_name:
            compare_keywords = ['比較', '對比', '差異', 'compare', 'vs']
            test_job_keywords = ['測項', '測試項目', '測項結果', '測試項目結果', 'test job', 'test jobs', 'test item']
            stat_keywords = ['通過率', '完成率', '統計', '進度', 'pass rate', 'completion', '趨勢']
            
            has_compare = any(kw in query for kw in compare_keywords)
            has_test_job = any(kw in query.lower() for kw in test_job_keywords)
            has_stat = any(sk in query.lower() for sk in stat_keywords)
            
            # 如果包含「比較」+「測試項目」且不包含「統計」關鍵詞 → compare_fw_test_jobs
            if has_compare and has_test_job and not has_stat:
                fw_versions = self._detect_multi_fw_versions_for_compare(query)
                if len(fw_versions) >= 2:
                    return IntentResult(
                        intent=IntentType.COMPARE_FW_TEST_JOBS,
                        parameters={
                            'project_name': project_name,
                            'fw_versions': fw_versions
                        },
                        confidence=0.85,
                        raw_response=f"Fallback: compare FW test jobs for {project_name}: {' vs '.join(fw_versions)}"
                    )
        
        # 10. ★★★ 最新 FW 版本比較查詢 ★★★
        # 檢測「比較」+「最新」關鍵字組合
        compare_keywords = ['比較', '對比', 'compare', 'vs']
        latest_keywords = ['最新', '最近', '新版', 'latest', 'recent', '兩個', '兩版']
        fw_keywords = ['fw', 'firmware', '韌體', '版本']
        
        has_compare = any(kw in query_lower for kw in compare_keywords)
        has_latest = any(kw in query for kw in latest_keywords)
        has_fw = any(kw in query_lower for kw in fw_keywords)
        
        if project_name and has_compare and (has_latest or has_fw):
            return IntentResult(
                intent=IntentType.COMPARE_LATEST_FW,
                parameters={'project_name': project_name},
                confidence=0.7,
                raw_response=f"Fallback: compare latest FW versions for {project_name}"
            )
        
        # 10. 檢查是否是專案詳情或摘要查詢
        if project_name:
            # 檢查是否有測試類別或容量關鍵字
            detected_category = self._detect_test_category(query)
            detected_capacity = self._detect_capacity(query)
            
            # ★★★ Phase 17/18: 優先檢測「比較多個 FW 版本測項結果」★★★
            # 關鍵詞：「比較」「對比」「差異」+ 多個 FW 版本 + 「測項」「測試項目」
            # Phase 18: 支援 2-10 個版本
            compare_keywords = ['比較', '對比', '差異', 'compare', 'vs', '和', '與']
            test_job_keywords = ['測項', '測試項目', '測項結果', '測試項目結果', 'test job', 'test jobs', 'test item']
            
            has_compare = any(kw in query for kw in compare_keywords)
            has_test_job = any(kw in query.lower() for kw in test_job_keywords)
            
            if has_compare:
                fw_versions = self._detect_multi_fw_versions_for_compare(query)
                if len(fw_versions) >= 2:
                    # 確認是「比較測項結果」而非「比較版本統計」
                    # 「測項結果」「測試項目結果」→ compare_fw_test_jobs
                    # 「通過率」「完成率」「統計」「測試結果」→ compare_multiple_fw
                    stat_keywords = ['通過率', '完成率', '統計', '進度', 'pass rate', 'completion', '測試結果', '趨勢']
                    has_stat = any(sk in query.lower() for sk in stat_keywords)
                    
                    # 🆕 檢查是否包含「測試結果」但不含「測試項目」
                    has_test_result = '測試結果' in query
                    has_test_item = any(kw in query for kw in ['測試項目', '測項'])
                    
                    if has_test_job and not has_stat:
                        # 明確包含「測試項目」關鍵詞 → compare_fw_test_jobs
                        return IntentResult(
                            intent=IntentType.COMPARE_FW_TEST_JOBS,
                            parameters={
                                'project_name': project_name,
                                'fw_versions': fw_versions
                            },
                            confidence=0.8,
                            raw_response=f"Fallback: compare FW test jobs for {project_name}: {' vs '.join(fw_versions)}"
                        )
                    elif has_test_result and not has_test_item:
                        # 🆕 包含「測試結果」但不含「測試項目」→ compare_multiple_fw（整體統計）
                        return IntentResult(
                            intent=IntentType.COMPARE_MULTIPLE_FW,
                            parameters={
                                'project_name': project_name,
                                'fw_versions': fw_versions
                            },
                            confidence=0.8,
                            raw_response=f"Fallback: compare multiple FW (測試結果) for {project_name}: {' vs '.join(fw_versions)}"
                        )
                    elif not has_test_job:
                        # 🆕 沒有「測試項目」關鍵詞，預設為整體統計比較
                        return IntentResult(
                            intent=IntentType.COMPARE_MULTIPLE_FW,
                            parameters={
                                'project_name': project_name,
                                'fw_versions': fw_versions
                            },
                            confidence=0.75,
                            raw_response=f"Fallback: compare multiple FW (default) for {project_name}: {' vs '.join(fw_versions)}"
                        )
            
            # ★★★ 檢測 FW 版本 ★★★
            # FW 版本格式：通常是 CODE_Name_Capacity 或 簡短代碼
            # 例如：PH10YC3H_Pyrite_4K, GD10YBJD_Opal, Y1114B, X0325A, GM10YCBM_Opal 等
            detected_fw_version = self._detect_fw_version_for_fallback(query)
            
            # 如果有 FW 版本，優先處理 FW 相關查詢
            if detected_fw_version:
                # ★★★ 重要區分：「測試結果」vs「測試項目結果/測項結果」★★★
                # 「測試項目結果」「測項結果」→ query_project_fw_test_jobs（Pass/Fail 清單）
                test_item_detail_keywords = ['測項結果', '測試項目結果', '測試項目', '哪些測項', '哪些 fail', '哪些fail', '哪些 pass', '哪些pass']
                if any(dk in query.lower() for dk in test_item_detail_keywords):
                    return IntentResult(
                        intent=IntentType.QUERY_PROJECT_FW_TEST_JOBS,
                        parameters={'project_name': project_name, 'fw_version': detected_fw_version},
                        confidence=0.7,
                        raw_response=f"Fallback: FW test jobs query for {project_name} fw={detected_fw_version}"
                    )
                
                # 「測試結果」（不含「測試項目」）→ query_fw_detail_summary（統計表格）
                if '測試結果' in query and '測試項目' not in query and '測項' not in query:
                    return IntentResult(
                        intent=IntentType.QUERY_FW_DETAIL_SUMMARY,
                        parameters={'project_name': project_name, 'fw_version': detected_fw_version},
                        confidence=0.75,
                        raw_response=f"Fallback: FW detail summary (測試結果) for {project_name} fw={detected_fw_version}"
                    )
                
                # 統計類關鍵字 → query_fw_detail_summary
                stat_keywords = ['統計', '詳細統計', '通過率', '完成率', '進度', '狀況', '測了幾個', '多少', '樣本使用率', '執行率', '失敗率', '測試概覽']
                if any(sk in query for sk in stat_keywords):
                    return IntentResult(
                        intent=IntentType.QUERY_FW_DETAIL_SUMMARY,
                        parameters={'project_name': project_name, 'fw_version': detected_fw_version},
                        confidence=0.7,
                        raw_response=f"Fallback: FW detail summary query for {project_name} fw={detected_fw_version}"
                    )
                
                # 其他測試相關關鍵字 → query_fw_detail_summary
                if ('測試' in query or '結果' in query or '摘要' in query 
                    or 'pass' in query_lower or 'fail' in query_lower or '如何' in query):
                    return IntentResult(
                        intent=IntentType.QUERY_FW_DETAIL_SUMMARY,
                        parameters={'project_name': project_name, 'fw_version': detected_fw_version},
                        confidence=0.6,
                        raw_response=f"Fallback: FW detail summary query for {project_name} fw={detected_fw_version}"
                    )
            
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
            
            # ★★★ Phase 15: Known Issues 查詢 ★★★
            known_issues_keywords = ['known issue', 'known issues', 'known-issue', 'known-issues',
                                     '已知問題', '已知issue', 'issue', 'issues', '問題清單']
            if any(kw in query_lower for kw in known_issues_keywords):
                # 檢查是否有 Test Item 關鍵字
                test_item = self._detect_test_item_for_known_issues(query)
                
                if test_item:
                    # 按 Test Item 查詢專案 Known Issues
                    return IntentResult(
                        intent=IntentType.QUERY_PROJECT_TEST_ITEM_KNOWN_ISSUES,
                        parameters={'project_name': project_name, 'test_item': test_item},
                        confidence=0.7,
                        raw_response=f"Fallback: known issues by test item for {project_name}, test_item={test_item}"
                    )
                
                # 檢查是否是數量查詢
                if self._has_count_keywords(query):
                    return IntentResult(
                        intent=IntentType.COUNT_PROJECT_KNOWN_ISSUES,
                        parameters={'project_name': project_name},
                        confidence=0.7,
                        raw_response=f"Fallback: count known issues for {project_name}"
                    )
                
                # 一般專案 Known Issues 查詢
                return IntentResult(
                    intent=IntentType.QUERY_PROJECT_KNOWN_ISSUES,
                    parameters={'project_name': project_name},
                    confidence=0.7,
                    raw_response=f"Fallback: known issues query for {project_name}"
                )
            
            # ★★★ FW 版本列表查詢 ★★★
            # 關鍵詞：「有哪些 FW」「FW 版本」「版本列表」「幾個版本」
            fw_list_keywords = ['有哪些 fw', '有哪些fw', 'fw 版本', 'fw版本', '版本列表', 
                               '幾個版本', '哪些版本', '什麼版本', '版本有哪些', 
                               'firmware', 'list fw', 'fw list']
            if any(kw in query_lower for kw in fw_list_keywords):
                return IntentResult(
                    intent=IntentType.LIST_FW_VERSIONS,
                    parameters={'project_name': project_name},
                    confidence=0.75,
                    raw_response=f"Fallback: list FW versions for {project_name}"
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
        # 排除的關鍵字（不應被識別為專案名稱）
        excluded_keywords = {
            'GET', 'POST', 'API', 'SAF',
            # Known Issues 相關關鍵字
            'Known', 'Issue', 'Issues', 'JIRA', 'Jira',
            # 常見的非專案詞彙
            'Test', 'Tests', 'Result', 'Results', 'Summary',
            'Pass', 'Fail', 'Failed', 'Passed',
            'FW', 'Firmware', 'Version', 'Versions',
            'All', 'List', 'Count', 'Total', 'Query',
            # 中文關鍵字
            '比較', '對比', '差異', '幾版', '幾個', '測試', '結果', '項目',
        }
        
        # ★★★ 模式 0：比較查詢專用 ★★★
        # 格式：「比較 {project_name} ...」（支援小寫）
        compare_project_pattern = r'(?:比較|對比|差異)\s+([a-zA-Z][a-zA-Z0-9_-]*)'
        match = re.search(compare_project_pattern, query, re.IGNORECASE)
        if match:
            candidate = match.group(1)
            if candidate.upper() not in {k.upper() for k in excluded_keywords}:
                if candidate.upper() not in [c.upper() for c in KNOWN_CUSTOMERS]:
                    if candidate.upper() not in [c.upper() for c in KNOWN_CONTROLLERS]:
                        return candidate
        
        # 模式 1：檢測「專案」關鍵字前後的名稱
        # 格式：「{project_name} 專案」 或 「專案 {project_name}」
        project_patterns = [
            r'([a-zA-Z][a-zA-Z0-9_-]*)\s*專案',  # xxx 專案
            r'專案\s*([a-zA-Z][a-zA-Z0-9_-]*)',  # 專案 xxx
            r'([a-zA-Z][a-zA-Z0-9_-]*)\s+的\s+known\s+issue',  # xxx 的 known issue
            r'([a-zA-Z][a-zA-Z0-9_-]*)\s+的\s+issue',  # xxx 的 issue
            r'([a-zA-Z][a-zA-Z0-9_-]*)\s+的\s+已知問題',  # xxx 的 已知問題
            r'([a-zA-Z][a-zA-Z0-9_-]*)\s+known\s+issue',  # xxx known issue
            r'([a-zA-Z][a-zA-Z0-9_-]*)\s+issue',  # xxx issue（如果單獨出現）
            r'([a-zA-Z][a-zA-Z0-9_-]*)\s+有哪些',  # xxx 有哪些
        ]
        
        for pattern in project_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                candidate = match.group(1)
                if candidate and candidate not in excluded_keywords:
                    # 檢查是否是已知客戶或控制器
                    if candidate.upper() not in [c.upper() for c in KNOWN_CUSTOMERS]:
                        if candidate.upper() not in [c.upper() for c in KNOWN_CONTROLLERS]:
                            return candidate
        
        # 模式 2：大寫字母開頭的單詞（不是已知客戶或控制器）
        words = re.findall(r'\b([A-Z][a-zA-Z0-9]+)\b', query)
        
        for word in words:
            word_upper = word.upper()
            # 排除已知客戶和控制器
            if word_upper not in [c.upper() for c in KNOWN_CUSTOMERS]:
                if word_upper not in [c.upper() for c in KNOWN_CONTROLLERS]:
                    if word not in excluded_keywords:
                        return word
        
        return None
    
    def _detect_fw_version_for_fallback(self, query: str) -> Optional[str]:
        """
        檢測查詢中的 FW 版本（用於 fallback）
        
        FW 版本常見格式：
        1. CODE_Name_Capacity: PH10YC3H_Pyrite_4K, GD10YBJD_Opal
        2. 簡短代碼: Y1114B, X0325A, FWX0926C, 82CBW5QF
        3. 帶 FW 前綴: FW PH10YC3H_Pyrite_4K
        
        Args:
            query: 用戶查詢
            
        Returns:
            Optional[str]: 檢測到的 FW 版本，或 None
        """
        # 模式 1：完整 FW 格式 CODE_Name_Capacity (如 PH10YC3H_Pyrite_4K)
        # 格式：大寫字母+數字+字母_單詞_數字K/M
        full_fw_pattern = r'\b([A-Z]{2,}\d+[A-Z0-9]*_[A-Za-z]+(?:_[A-Za-z0-9]+)*)\b'
        full_matches = re.findall(full_fw_pattern, query)
        if full_matches:
            return full_matches[0]
        
        # 模式 2：帶 "FW" 關鍵字後面的版本號
        fw_keyword_pattern = r'(?:FW|fw|Fw)\s+([A-Za-z0-9_]+(?:_[A-Za-z0-9]+)*)'
        fw_keyword_matches = re.findall(fw_keyword_pattern, query)
        if fw_keyword_matches:
            return fw_keyword_matches[0]
        
        # 模式 3：簡短 FW 代碼（如 Y1114B, X0325A, 82CBW5QF）
        # 格式：字母+數字組合，至少5個字符
        short_fw_pattern = r'\b([A-Z]{1,2}\d{3,}[A-Z]{1,2}|\d{2}[A-Z]{3}[0-9A-Z]+|FW[A-Z]\d{4}[A-Z])\b'
        short_matches = re.findall(short_fw_pattern, query.upper())
        if short_matches:
            return short_matches[0]
        
        return None

    def _detect_multi_fw_versions_for_compare(self, query: str) -> list[str]:
        """
        檢測查詢中的多個 FW 版本（用於比較查詢）
        
        Phase 18: 支援 2-10 個 FW 版本的比較。
        專門用於處理「比較 FW1 和 FW2 和 FW3...」這類查詢。
        
        FW 版本常見格式：
        1. CODE_Name_Capacity: PH10YC3H_Pyrite_4K, GD10YBJD_Opal
        2. 簡短代碼: Y1114B, X0325A, GD10YBJD, HHB0YBC1
        
        Args:
            query: 用戶查詢
            
        Returns:
            list[str]: FW 版本列表（已去重，按出現順序），至少需要 2 個
        """
        all_matches = []
        
        # 模式 1：完整 FW 格式 CODE_Name_Capacity (如 PH10YC3H_Pyrite_4K)
        full_fw_pattern = r'\b([A-Z]{2,}\d+[A-Z0-9]*_[A-Za-z]+(?:_[A-Za-z0-9]+)*)\b'
        full_matches = re.findall(full_fw_pattern, query)
        all_matches.extend(full_matches)
        
        # 模式 2：更寬鬆的字母數字組合（如 HHB0YBC1, GD10YBJD）
        # 必須同時包含字母和數字，長度 >= 6
        flexible_pattern = r'\b([A-Z0-9]{6,})\b'
        flexible_matches = re.findall(flexible_pattern, query.upper())
        
        # 過濾掉純數字和專案名稱（通常是較短的或純字母的）
        project_name = self._detect_project_name(query)
        for match in flexible_matches:
            # 確保同時包含字母和數字（FW 版本特徵）
            has_letter = any(c.isalpha() for c in match)
            has_digit = any(c.isdigit() for c in match)
            # 排除專案名稱
            is_project = project_name and match.upper() == project_name.upper()
            
            if has_letter and has_digit and not is_project and match not in all_matches:
                all_matches.append(match)
        
        # 去重並保持順序
        seen = set()
        unique_versions = []
        for v in all_matches:
            if v and v not in seen:
                seen.add(v)
                unique_versions.append(v)
        
        return unique_versions
    
    def _detect_two_fw_versions_for_compare(self, query: str) -> tuple[Optional[str], Optional[str]]:
        """
        檢測查詢中的兩個 FW 版本（向後相容方法）
        
        Args:
            query: 用戶查詢
            
        Returns:
            tuple[Optional[str], Optional[str]]: (fw_version_1, fw_version_2)，找不到則返回 (None, None)
        """
        versions = self._detect_multi_fw_versions_for_compare(query)
        if len(versions) >= 2:
            return (versions[0], versions[1])
        return (None, None)

    def _has_count_keywords(self, query: str) -> bool:
        """檢查是否包含數量相關關鍵字"""
        count_keywords = ['多少', '幾個', '數量', 'count', '總共', '專案數']
        return any(kw in query.lower() for kw in count_keywords)
    
    def _has_project_keywords(self, query: str) -> bool:
        """檢查是否包含專案相關關鍵字"""
        project_keywords = ['專案', 'project', '有哪些', '列表', '列出']
        return any(kw in query.lower() for kw in project_keywords)
    
    def _detect_test_item_for_known_issues(self, query: str) -> Optional[str]:
        """
        從查詢中檢測 Test Item 名稱（用於 Known Issues 查詢）
        
        Args:
            query: 用戶查詢
            
        Returns:
            Optional[str]: 檢測到的 test_item，或 None
        """
        query_lower = query.lower()
        
        # 常見的 Test Item 關鍵字（按長度排序，優先匹配較長的）
        test_items = [
            # 完整名稱
            'crystaldiskmark', 'crystal disk mark', 'crystal-disk-mark',
            'smart', 's.m.a.r.t', 'smart data',
            'performance', 'perf', '效能',
            'compatibility', 'compat', '相容性',
            'compliance', 'comp', '合規',
            'stress', 'stress test', '壓力測試',
            'endurance', '耐久性',
            'power', 'power cycle', '電源',
            'temperature', 'temp', '溫度',
            'read', 'write', 'sequential', 'random',
            '4k', '4kb', '1m', '1mb', '512k', '512kb',
            # 其他常見測試項目
            'nvme', 'sata', 'pcie', 'usb',
            'trim', 'sanitize', 'format',
            'boot', 'firmware', 'fw', 'bios',
        ]
        
        for item in test_items:
            if item in query_lower:
                # 標準化返回值
                item_mapping = {
                    'crystal disk mark': 'CrystalDiskMark',
                    'crystal-disk-mark': 'CrystalDiskMark',
                    'crystaldiskmark': 'CrystalDiskMark',
                    's.m.a.r.t': 'SMART',
                    'smart data': 'SMART',
                    'smart': 'SMART',
                    'perf': 'Performance',
                    'performance': 'Performance',
                    '效能': 'Performance',
                    'compat': 'Compatibility',
                    'compatibility': 'Compatibility',
                    '相容性': 'Compatibility',
                    'comp': 'Compliance',
                    'compliance': 'Compliance',
                    '合規': 'Compliance',
                    'stress test': 'Stress',
                    '壓力測試': 'Stress',
                    'stress': 'Stress',
                    '耐久性': 'Endurance',
                    'endurance': 'Endurance',
                    'power cycle': 'Power Cycle',
                    '電源': 'Power Cycle',
                    'power': 'Power',
                    'temp': 'Temperature',
                    '溫度': 'Temperature',
                    'temperature': 'Temperature',
                }
                return item_mapping.get(item, item.upper())
        
        return None
    
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
