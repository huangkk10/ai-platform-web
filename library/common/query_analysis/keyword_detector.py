"""
全文關鍵字檢測器（Full Document Keyword Detector）

檢測用戶查詢是否包含要求完整文檔的關鍵字，
用於智能路由決策（模式 A vs 模式 B）。

Author: AI Platform Team
Date: 2025-11-11
"""

import logging

logger = logging.getLogger(__name__)

# ===== 全文關鍵字列表 =====

FULL_DOCUMENT_KEYWORDS = [
    # 完整性要求
    '完整', '全部', '全文', '完整內容', '完整文檔',
    '取得完整內容', '取得全部內容', '完整說明', '完整流程',
    '完整資料', '完整資訊', '完整文件',
    
    # 步驟相關
    '所有步驟', '全部步驟', '完整步驟', '詳細步驟',
    '所有流程', '全部流程', '完整流程', '詳細流程',
    '每個步驟', '每一步驟',
    
    # 詳細性要求
    '詳細', '詳細內容', '詳細說明', '詳細資訊',
    '完整資訊', '全部資訊', '所有資訊',
    '詳盡', '詳盡說明', '詳盡內容',
    
    # 顯示相關
    '顯示完整', '顯示全部', '顯示所有',
    '查看完整', '查看全部', '查看所有',
    
    # SOP 和標準作業流程相關（🆕 新增）
    'SOP', 'sop', '標準作業流程', '操作流程', '作業流程',
    '標準流程', '工作流程', '執行流程',
    
    # 教學和手冊相關（🆕 新增）
    '教學', '指南', '手冊', '使用手冊', '操作手冊',
    '指導', '說明書', '操作指南', '使用指南',
    'tutorial', 'guide', 'manual', 'handbook',
    
    # 英文（如果用戶可能使用英文）
    'full', 'complete', 'entire', 'whole',
    'all steps', 'full document', 'complete document',
    'detailed', 'full content', 'complete content',
    'show all', 'show complete', 'view all',
]


def contains_full_document_keywords(user_query: str) -> tuple[bool, str | None]:
    """
    檢測用戶問題是否包含全文關鍵字
    
    Args:
        user_query: 用戶查詢字串
        
    Returns:
        tuple[bool, str | None]: 
            - bool: True 表示包含全文關鍵字，False 表示不包含
            - str | None: 匹配到的關鍵字，如果沒有匹配則為 None
    
    Examples:
        >>> contains_full_document_keywords("Cup顏色完整內容")
        (True, "完整內容")
        
        >>> contains_full_document_keywords("Cup顏色全文")
        (True, "全文")
        
        >>> contains_full_document_keywords("Cup顏色")
        (False, None)
    """
    if not user_query or not user_query.strip():
        return False, None
    
    # 轉小寫比較（支援英文）
    query_lower = user_query.lower()
    
    # 檢查是否含有全文關鍵字
    for keyword in FULL_DOCUMENT_KEYWORDS:
        if keyword.lower() in query_lower:
            logger.debug(f"🔍 全文關鍵字檢測: 找到關鍵字 '{keyword}' in '{user_query}'")
            return True, keyword
    
    logger.debug(f"🔍 全文關鍵字檢測: 未找到關鍵字 in '{user_query}'")
    return False, None


def get_full_document_keywords_count() -> int:
    """
    獲取全文關鍵字總數
    
    Returns:
        int: 關鍵字總數
    """
    return len(FULL_DOCUMENT_KEYWORDS)


def add_custom_keyword(keyword: str) -> None:
    """
    動態添加自定義關鍵字（運行時）
    
    Args:
        keyword: 要添加的關鍵字
        
    Note:
        此函數僅在運行時有效，重啟後會重置
        如需永久添加，請修改 FULL_DOCUMENT_KEYWORDS 列表
    """
    if keyword and keyword not in FULL_DOCUMENT_KEYWORDS:
        FULL_DOCUMENT_KEYWORDS.append(keyword)
        logger.info(f"✅ 已添加自定義全文關鍵字: '{keyword}'")


# ===== 測試函數 =====

def test_keyword_detection():
    """
    測試關鍵字檢測功能
    
    用於驗證檢測邏輯的正確性
    """
    test_cases = [
        ("Cup顏色完整內容", True, "完整內容"),
        ("Cup顏色全文", True, "全文"),
        ("所有步驟怎麼做", True, "所有步驟"),
        ("取得完整內容", True, "取得完整內容"),
        ("詳細說明Cup流程", True, "詳細說明"),
        ("show complete document", True, "complete"),
        ("Cup顏色是什麼", False, None),
        ("如何測試Cup", False, None),
        ("Cup的用途", False, None),
    ]
    
    print("\n===== 全文關鍵字檢測測試 =====\n")
    
    passed = 0
    failed = 0
    
    for query, expected_result, expected_keyword in test_cases:
        result, keyword = contains_full_document_keywords(query)
        
        status = "✅" if result == expected_result else "❌"
        
        if result == expected_result:
            passed += 1
            print(f"{status} 問題: '{query}'")
            print(f"   → 包含全文關鍵字: {result}")
            if keyword:
                print(f"   → 匹配關鍵字: '{keyword}'")
            print(f"   → 搜尋策略: {'模式A（直接全文）' if result else '模式B（兩階段）'}")
        else:
            failed += 1
            print(f"{status} 問題: '{query}'")
            print(f"   → 預期: {expected_result}, 實際: {result}")
            print(f"   → 預期關鍵字: '{expected_keyword}', 實際: '{keyword}'")
        
        print()
    
    print(f"\n測試結果: {passed} 通過, {failed} 失敗")
    print(f"關鍵字總數: {get_full_document_keywords_count()}\n")
    
    return passed, failed


if __name__ == '__main__':
    # 運行測試
    test_keyword_detection()
