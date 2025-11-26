"""
Title Boost Processor
標題加分處理器（裝飾器模式）

不修改原有搜尋邏輯，在結果上包裹一層加分處理。
"""

from typing import List, Dict, Any
from .matcher import TitleMatcher
import logging

logger = logging.getLogger(__name__)


class TitleBoostProcessor:
    """
    Title Boost 處理器
    
    設計模式：裝飾器模式
    - 不修改原有搜尋邏輯
    - 在結果上包裹一層加分處理
    - 可選啟用/停用
    
    處理流程：
    1. 接收向量搜尋的原始結果
    2. 遍歷每個結果，檢查標題匹配
    3. 如果匹配，在 final_score 上加分
    4. 限制最高分為 1.0
    5. 重新排序結果
    6. 記錄加分資訊到 metadata
    """
    
    def __init__(
        self, 
        title_match_bonus: float = 0.15, 
        min_keyword_length: int = 2,
        enable_progressive_bonus: bool = False
    ):
        """
        初始化 TitleBoostProcessor
        
        Args:
            title_match_bonus: Title 匹配加分（0.0 ~ 1.0）
            min_keyword_length: 最小關鍵詞長度
            enable_progressive_bonus: 是否啟用漸進式加分（根據匹配程度）
        """
        self.title_match_bonus = title_match_bonus
        self.matcher = TitleMatcher(min_keyword_length=min_keyword_length)
        self.enable_progressive_bonus = enable_progressive_bonus
    
    def apply_title_boost(
        self,
        query: str,
        vector_results: List[Dict[str, Any]],
        title_field: str = 'title'
    ) -> List[Dict[str, Any]]:
        """
        對向量搜尋結果應用 Title Boost
        
        ⚠️ 不修改原始 title_score 和 content_score
        ⚠️ 只調整 final_score（加分後重新排序）
        
        Args:
            query: 用戶查詢
            vector_results: 向量搜尋原始結果
            title_field: 標題欄位名稱（預設 'title'）
            
        Returns:
            加分後的結果列表（排序可能改變）
        
        Examples:
            >>> processor = TitleBoostProcessor(title_match_bonus=0.15)
            >>> results = [
            ...     {'final_score': 0.80, 'title': 'IOL 測試指南'},
            ...     {'final_score': 0.85, 'title': '其他指南'}
            ... ]
            >>> boosted = processor.apply_title_boost("IOL SOP", results)
            >>> boosted[0]['final_score']
            0.95  # 0.80 + 0.15 (Title Boost)
            >>> boosted[0]['title_boost_applied']
            True
        """
        if not vector_results:
            logger.info("向量結果為空，跳過 Title Boost")
            return vector_results
        
        boosted_results = []
        boost_count = 0
        total_boost_value = 0.0
        
        for result in vector_results:
            # 深拷貝結果（避免修改原始資料）
            boosted_result = result.copy()
            
            # 獲取標題
            title = boosted_result.get(title_field, '')
            if not title:
                logger.warning(f"結果缺少標題欄位: {title_field}")
                boosted_results.append(boosted_result)
                continue
            
            # 檢查 Title 匹配
            is_match = self.matcher.check_title_match(query, title)
            
            if is_match:
                # 計算加分值
                if self.enable_progressive_bonus:
                    # 漸進式加分：根據匹配程度調整
                    match_score = self.matcher.calculate_match_score(query, title)
                    actual_bonus = self.title_match_bonus * match_score
                else:
                    # 固定加分
                    actual_bonus = self.title_match_bonus
                
                # 計算加分後的分數（支援 final_score 或 score 欄位）
                original_score = boosted_result.get('final_score') or boosted_result.get('score', 0.0)
                boosted_score = min(original_score + actual_bonus, 1.0)
                
                # 更新分數
                boosted_result['final_score'] = boosted_score
                boosted_result['similarity_score'] = boosted_score  # 向後兼容
                
                # 記錄加分資訊
                boosted_result['title_boost_applied'] = True
                boosted_result['title_boost_value'] = actual_bonus
                boosted_result['original_score'] = original_score
                
                # 可選：記錄匹配的關鍵詞
                matched_keywords = self.matcher.get_matched_keywords(query, title)
                boosted_result['matched_keywords'] = matched_keywords
                
                boost_count += 1
                total_boost_value += actual_bonus
                
                logger.debug(
                    f"✨ Title Boost 應用: '{title[:40]}...' "
                    f"({original_score:.3f} → {boosted_score:.3f}, "
                    f"bonus={actual_bonus:.3f})"
                )
            else:
                # 無匹配，保持原分數
                boosted_result['title_boost_applied'] = False
            
            boosted_results.append(boosted_result)
        
        # 重新排序（按加分後的 final_score）
        boosted_results.sort(key=lambda x: x.get('final_score', 0.0), reverse=True)
        
        # 統計資訊
        if boost_count > 0:
            avg_boost = total_boost_value / boost_count
            logger.info(
                f"📊 Title Boost 完成: {boost_count}/{len(vector_results)} 結果獲得加分 "
                f"(平均加分: {avg_boost:.3f})"
            )
        else:
            logger.info(f"📊 Title Boost 完成: 無結果匹配（0/{len(vector_results)}）")
        
        return boosted_results
    
    def get_boost_statistics(self, boosted_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        獲取 Title Boost 統計資訊
        
        Args:
            boosted_results: 已應用 Title Boost 的結果
            
        Returns:
            統計資訊字典
        """
        total_count = len(boosted_results)
        boosted_count = sum(1 for r in boosted_results if r.get('title_boost_applied', False))
        
        if boosted_count > 0:
            total_boost_value = sum(
                r.get('title_boost_value', 0.0) 
                for r in boosted_results 
                if r.get('title_boost_applied', False)
            )
            avg_boost = total_boost_value / boosted_count
            
            # 找出最大加分
            max_boosted = max(
                (r for r in boosted_results if r.get('title_boost_applied', False)),
                key=lambda x: x.get('title_boost_value', 0.0),
                default=None
            )
        else:
            avg_boost = 0.0
            max_boosted = None
        
        return {
            'total_results': total_count,
            'boosted_count': boosted_count,
            'boost_ratio': boosted_count / total_count if total_count > 0 else 0.0,
            'average_boost': avg_boost,
            'max_boost': max_boosted.get('title_boost_value', 0.0) if max_boosted else 0.0,
            'max_boosted_title': max_boosted.get('title', '') if max_boosted else ''
        }
