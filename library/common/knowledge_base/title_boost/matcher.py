"""
Title Matching Utilities
標題匹配工具（獨立模組）

提供查詢關鍵詞提取和標題匹配判定功能。
"""

import re
from typing import List, Set
import logging

logger = logging.getLogger(__name__)


class TitleMatcher:
    """
    標題匹配器（無狀態，可重複使用）
    
    主要功能：
    1. 提取查詢中的關鍵詞（移除停用詞）
    2. 判斷關鍵詞是否出現在標題中
    3. 計算匹配分數（匹配關鍵詞數量/總關鍵詞數量）
    """
    
    # 停用詞列表（請求性詞語、文檔級關鍵字）
    STOP_WORDS = {
        # 中文停用詞
        '請', '說明', '解釋', '告訴', '幫忙', '問', '教', '給',
        '如何', '怎麼', '怎樣', '什麼', '是', '的', '了', '嗎', '呢',
        '完整', '全部', '整個', '所有', '全文', '詳細',
        # 文檔級關鍵字
        'sop', 'SOP', '標準', '作業', '流程', '操作',
        # 英文停用詞
        'how', 'what', 'please', 'tell', 'explain', 'help'
    }
    
    def __init__(self, min_keyword_length: int = 2):
        """
        初始化 TitleMatcher
        
        Args:
            min_keyword_length: 最小關鍵詞長度（預設 2 字元）
        """
        self.min_keyword_length = min_keyword_length
    
    def extract_keywords(self, query: str) -> List[str]:
        """
        提取查詢中的關鍵詞
        
        處理策略：
        1. 使用正則表達式分詞（支援中英文）
        2. 移除停用詞
        3. 過濾短詞（< min_keyword_length）
        4. 正規化縮寫詞（小寫英文 → 大寫，如 iol → IOL）
        
        Args:
            query: 用戶查詢文本
            
        Returns:
            關鍵詞列表
            
        Examples:
            >>> matcher = TitleMatcher()
            >>> matcher.extract_keywords("如何完整測試 IOL SOP")
            ['測試', 'IOL']  # 移除 '如何', '完整', 'SOP'
            
            >>> matcher.extract_keywords("USB 3.0 連接測試")
            ['USB', '連接', '測試']
        """
        # 使用正則表達式分詞（支援中英文、數字、點號）
        words = re.findall(r'\w+(?:\.\w+)?', query)
        keywords = []
        
        for word in words:
            # 跳過停用詞
            if word.lower() in self.STOP_WORDS or word in self.STOP_WORDS:
                continue
            
            # 跳過短詞
            if len(word) < self.min_keyword_length:
                continue
            
            # 縮寫詞大寫正規化（純英文字母且長度 <= 5）
            if word.isalpha() and len(word) <= 5 and word.islower():
                keywords.append(word.upper())
            else:
                keywords.append(word)
        
        logger.debug(f"提取關鍵詞: '{query}' → {keywords}")
        return keywords
    
    def check_title_match(self, query: str, title: str) -> bool:
        """
        判斷查詢是否與標題匹配
        
        匹配規則：至少一個關鍵詞出現在標題中（忽略大小寫）
        
        Args:
            query: 用戶查詢
            title: 文檔標題
            
        Returns:
            True 表示匹配，False 表示不匹配
        
        Examples:
            >>> matcher = TitleMatcher()
            >>> matcher.check_title_match("IOL SOP", "IOL USB-IF 測試規範")
            True  # 'IOL' 匹配
            
            >>> matcher.check_title_match("random text", "IOL SOP")
            False  # 無匹配
        """
        keywords = self.extract_keywords(query)
        if not keywords:
            return False
        
        title_upper = title.upper()
        
        # 檢查任一關鍵詞是否在標題中
        for keyword in keywords:
            if keyword.upper() in title_upper:
                logger.debug(f"✅ Title 匹配: '{keyword}' in '{title}'")
                return True
        
        logger.debug(f"❌ Title 不匹配: {keywords} not in '{title}'")
        return False
    
    def calculate_match_score(self, query: str, title: str) -> float:
        """
        計算匹配分數（0.0 ~ 1.0）
        
        分數計算：匹配的關鍵詞數量 / 總關鍵詞數量
        
        Args:
            query: 用戶查詢
            title: 文檔標題
            
        Returns:
            匹配分數（0.0 表示無匹配，1.0 表示所有關鍵詞都匹配）
        
        Examples:
            >>> matcher = TitleMatcher()
            >>> matcher.calculate_match_score("IOL USB", "IOL USB-IF 測試")
            1.0  # 2/2 關鍵詞匹配
            
            >>> matcher.calculate_match_score("IOL USB SOP", "IOL 測試")
            0.33  # 1/3 關鍵詞匹配（只有 IOL）
        """
        keywords = self.extract_keywords(query)
        if not keywords:
            return 0.0
        
        title_upper = title.upper()
        matched_count = sum(1 for kw in keywords if kw.upper() in title_upper)
        
        score = matched_count / len(keywords)
        logger.debug(
            f"匹配分數: {matched_count}/{len(keywords)} = {score:.2f} "
            f"(query='{query}', title='{title}')"
        )
        return score
    
    def get_matched_keywords(self, query: str, title: str) -> List[str]:
        """
        獲取匹配的關鍵詞列表
        
        Args:
            query: 用戶查詢
            title: 文檔標題
            
        Returns:
            匹配的關鍵詞列表
        
        Examples:
            >>> matcher = TitleMatcher()
            >>> matcher.get_matched_keywords("IOL USB 測試", "IOL 規範")
            ['IOL']  # 只有 IOL 匹配
        """
        keywords = self.extract_keywords(query)
        title_upper = title.upper()
        
        matched = [kw for kw in keywords if kw.upper() in title_upper]
        return matched
