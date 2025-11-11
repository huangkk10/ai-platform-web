"""
不確定回答檢測器（Uncertainty Detector）

檢測 AI 回答是否表達不確定，
用於決定是否需要降級到下一階段搜尋或降級模式。

Author: AI Platform Team
Date: 2025-11-11
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# ===== 不確定關鍵字列表 =====

UNCERTAINTY_KEYWORDS = [
    # 明確否定
    '不清楚', '不知道', '不了解', '不確定',
    '沒有相關資料', '沒有找到', '沒有資訊', '找不到',
    '沒有提供', '沒有提及', '沒有說明',
    
    # 委婉表達
    '抱歉', '很遺憾', '無法回答', '無法提供',
    '資訊不足', '資料不足', '缺乏資訊',
    '無法確認', '難以回答', '難以確定',
    
    # 英文（如果 Dify 可能返回英文）
    "i don't know", 'not sure', 'unclear', 'uncertain',
    'no information', 'cannot find', 'unable to answer',
    'sorry', 'unfortunately', 'not available',
    
    # 模糊回答（已移除「可能」避免誤判免責聲明）
    '也許', '不太確定', '我猜',
    '大概', '似乎', '或許',
]

# 最短回答長度閾值（過短可能是無法回答）
MIN_RESPONSE_LENGTH = 20


def is_uncertain_response(ai_response: str, strict_mode: bool = False) -> tuple[bool, str | None]:
    """
    檢測 AI 回答是否表達不確定
    
    Args:
        ai_response: AI 的回答內容
        strict_mode: 嚴格模式（更保守地判斷不確定）
                     True: 只檢測明確的不確定關鍵字
                     False: 同時考慮回答長度
        
    Returns:
        tuple[bool, str | None]:
            - bool: True 表示回答不確定，False 表示回答明確
            - str | None: 匹配到的不確定關鍵字，如果沒有則為 None
    
    Examples:
        >>> is_uncertain_response("抱歉，我不清楚這個問題。")
        (True, "不清楚")
        
        >>> is_uncertain_response("根據文檔，Cup 是一個測試項目...")
        (False, None)
    """
    if not ai_response or not ai_response.strip():
        logger.warning("⚠️ 不確定檢測: 空回答")
        return True, None
    
    # 轉小寫比較
    response_lower = ai_response.lower()
    
    # 檢查是否含有不確定關鍵字
    for keyword in UNCERTAINTY_KEYWORDS:
        if keyword.lower() in response_lower:
            logger.info(f"🔍 不確定檢測: 找到關鍵字 '{keyword}'")
            return True, keyword
    
    # 非嚴格模式：檢查回答長度
    if not strict_mode:
        response_length = len(ai_response.strip())
        if response_length < MIN_RESPONSE_LENGTH:
            logger.info(f"🔍 不確定檢測: 回答過短 ({response_length} 字元 < {MIN_RESPONSE_LENGTH})")
            return True, None
    
    logger.debug("🔍 不確定檢測: 回答明確")
    return False, None


def format_fallback_response(documents: List[Dict[str, Any]], max_documents: int = 3) -> str:
    """
    格式化降級模式的回應
    
    當 AI 無法回答時，直接返回參考資料
    
    Args:
        documents: 搜尋結果文檔列表
                   每個文檔應包含: title, document_id, similarity, content
        max_documents: 最多顯示的文檔數
        
    Returns:
        str: 格式化後的降級模式回應
    """
    if not documents:
        return (
            "抱歉，我目前沒有找到相關資料。\n\n"
            "💡 **建議**：\n"
            "- 請嘗試調整問題的關鍵字\n"
            "- 或者查看知識庫中的其他相關文檔"
        )
    
    # 限制文檔數量
    documents = documents[:max_documents]
    
    response = "抱歉，我目前沒有足夠的資訊來完整回答您的問題。\n\n"
    response += "📚 **以下是可能相關的參考資料**：\n\n"
    
    for i, doc in enumerate(documents, 1):
        title = doc.get('title', '未命名文檔')
        document_id = doc.get('document_id', 'unknown')
        similarity = doc.get('similarity', 0.0)
        content = doc.get('content', '')
        
        response += f"### {i}. 📄 {title}\n\n"
        response += f"**來源**：`{document_id}`\n"
        
        # 顯示相似度（如果有）
        if similarity > 0:
            response += f"**相似度**：{similarity:.0%}\n"
        
        response += "\n"
        
        # 顯示內容摘要（前 500 字元）
        if content:
            content_preview = content[:500]
            if len(content) > 500:
                content_preview += "..."
            
            response += f"**內容摘要**：\n```\n{content_preview}\n```\n\n"
        
        response += "---\n\n"
    
    response += "💡 **提示**：您可以進一步查看上述文檔的完整內容，或重新調整問題。"
    
    return response


def get_uncertainty_keywords_count() -> int:
    """
    獲取不確定關鍵字總數
    
    Returns:
        int: 關鍵字總數
    """
    return len(UNCERTAINTY_KEYWORDS)


# ===== 測試函數 =====

def test_uncertainty_detection():
    """
    測試不確定檢測功能
    """
    test_cases = [
        # (回答內容, 預期結果, 描述)
        ("抱歉，我不清楚這個問題。", True, "明確表達不清楚"),
        ("很遺憾，我沒有找到相關資料。", True, "沒有找到資料"),
        ("我不確定這個答案是否正確。", True, "表達不確定"),
        ("根據 Cup 文檔，測試流程包括以下步驟...", False, "明確回答"),
        ("Cup 是一個測試項目，主要用於驗證杯子的顏色和圖案。詳細步驟如下：...", False, "完整回答"),
        ("是", True, "過短回答（嚴格模式 False）"),
        ("OK", True, "過短回答"),
        ("Based on the documentation, the process includes...", False, "英文明確回答"),
        ("I don't know the answer.", True, "英文不確定"),
    ]
    
    print("\n===== 不確定回答檢測測試 =====\n")
    
    passed = 0
    failed = 0
    
    for response, expected_result, description in test_cases:
        result, keyword = is_uncertain_response(response, strict_mode=False)
        
        status = "✅" if result == expected_result else "❌"
        
        if result == expected_result:
            passed += 1
            print(f"{status} {description}")
            print(f"   回答: '{response[:50]}...' (長度: {len(response)})")
            print(f"   → 不確定: {result}")
            if keyword:
                print(f"   → 匹配關鍵字: '{keyword}'")
        else:
            failed += 1
            print(f"{status} {description}")
            print(f"   回答: '{response[:50]}...'")
            print(f"   → 預期: {expected_result}, 實際: {result}")
        
        print()
    
    print(f"\n測試結果: {passed} 通過, {failed} 失敗")
    print(f"關鍵字總數: {get_uncertainty_keywords_count()}\n")
    
    # 測試降級模式格式化
    print("\n===== 測試降級模式格式化 =====\n")
    
    test_documents = [
        {
            'title': 'Cup 測試指南',
            'document_id': 'protocol_guide_20',
            'similarity': 0.86,
            'content': 'Cup 是一個測試項目，主要用於驗證杯子的顏色和圖案...'
        },
        {
            'title': '新舊各個版本主板',
            'document_id': 'protocol_guide_21',
            'similarity': 0.82,
            'content': '主板測試流程包括以下步驟...'
        }
    ]
    
    fallback_response = format_fallback_response(test_documents)
    print(fallback_response)
    
    return passed, failed


if __name__ == '__main__':
    # 運行測試
    test_uncertainty_detection()
