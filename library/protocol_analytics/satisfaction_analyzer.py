"""
Protocol Satisfaction Analyzer - Protocol Assistant 滿意度分析器

基於 BaseSatisfactionAnalyzer 的實現，專為 Protocol Assistant 設計。

主要功能：
1. 用戶滿意度統計（按讚/倒讚比率）
2. 回應時間分析（與滿意度的關聯）
3. 滿意度趨勢分析
4. 改進建議生成

Implementation Notes:
- 創建日期: 2025-11-07
- 繼承 BaseSatisfactionAnalyzer
- 實現 Protocol Assistant 特定需求
- 複用 Common Analytics 基礎設施

Usage:
    from library.protocol_analytics.satisfaction_analyzer import ProtocolSatisfactionAnalyzer
    
    analyzer = ProtocolSatisfactionAnalyzer()
    results = analyzer.analyze_user_satisfaction(user=None, days=30)
"""

import logging
from typing import Dict, Optional
from library.common.analytics.base_satisfaction_analyzer import BaseSatisfactionAnalyzer

logger = logging.getLogger(__name__)


class ProtocolSatisfactionAnalyzer(BaseSatisfactionAnalyzer):
    """
    Protocol Assistant 滿意度分析器
    
    繼承自 BaseSatisfactionAnalyzer，實現 Protocol Assistant 特定的滿意度分析
    """
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    # ==================== 實現抽象方法 ====================
    
    def get_assistant_type(self) -> str:
        """返回 Assistant 類型"""
        return 'protocol_assistant'
    
    def get_system_type_filter(self) -> str:
        """返回 system_type 過濾值（不含 _chat 後綴，會在查詢時自動添加）"""
        return 'protocol_assistant'
    
    def get_conversation_model(self):
        """返回對話模型"""
        from api.models import ConversationSession
        return ConversationSession
    
    def get_message_model(self):
        """返回消息模型"""
        from api.models import ChatMessage
        return ChatMessage
    
    # ==================== Protocol 專屬方法（可選） ====================
    
    def analyze_protocol_specific_satisfaction(self, days=30, user=None) -> Dict:
        """
        分析 Protocol 專屬的滿意度指標
        
        例如：Protocol 測試類型相關的滿意度差異
        
        Args:
            days: 統計天數
            user: 特定用戶（可選）
            
        Returns:
            dict: Protocol 專屬滿意度分析結果
        """
        try:
            # 示例：根據 Protocol 問題分類分析滿意度
            # 可以結合 question_classifier 進行更深入的分析
            
            return {
                'protocol_execution_satisfaction': 0.0,
                'troubleshooting_satisfaction': 0.0,
                'configuration_satisfaction': 0.0,
                # ... 其他 Protocol 專屬指標
            }
            
        except Exception as e:
            self.logger.error(f"Protocol 專屬滿意度分析失敗: {str(e)}", exc_info=True)
            return {}


# ==================== 便利函數 ====================

def analyze_user_satisfaction(user=None, days=30, conversation_id=None) -> Dict:
    """
    便利函數：分析 Protocol Assistant 用戶滿意度
    
    Args:
        user: Django User 實例（可選）
        days: 統計天數
        conversation_id: 特定對話 ID（可選）
        
    Returns:
        dict: 滿意度分析結果
    """
    analyzer = ProtocolSatisfactionAnalyzer()
    return analyzer.analyze_user_satisfaction(
        user=user,
        days=days,
        conversation_id=conversation_id
    )


def get_satisfaction_trends(days=30, interval='daily') -> Dict:
    """
    便利函數：獲取 Protocol Assistant 滿意度趨勢
    
    Args:
        days: 統計天數
        interval: 趨勢間隔 ('daily', 'weekly', 'monthly')
        
    Returns:
        dict: 滿意度趨勢數據
    """
    analyzer = ProtocolSatisfactionAnalyzer()
    return analyzer.get_satisfaction_trends(days=days, interval=interval)


__all__ = [
    'ProtocolSatisfactionAnalyzer',
    'analyze_user_satisfaction',
    'get_satisfaction_trends'
]
