"""
Protocol Statistics Manager - 基於 Common Analytics 基礎設施的統計管理器

此版本繼承自 BaseStatisticsManager，複用共用邏輯。

主要功能：
1. 總覽統計（對話數、消息數、用戶數、滿意度等）- 基類提供
2. 用戶統計（活躍用戶、新用戶、流失分析）- 基類提供  
3. 效能統計（回應時間、tokens 使用量）- 基類提供
4. 趨勢分析（時間序列趨勢）- 基類提供
5. 問題分類統計 - Protocol 專屬
6. 滿意度分析 - 複用 Common

Implementation Notes:
- 創建日期: 2025-10-23
- 基於 RVT Analytics 範本
- 繼承 BaseStatisticsManager
- 實現 Protocol Assistant 特定需求

Usage:
    from library.protocol_analytics.statistics_manager import ProtocolStatisticsManager
    
    manager = ProtocolStatisticsManager()
    stats = manager.get_comprehensive_stats(days=30)
"""

import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
from library.common.analytics.base_statistics_manager import BaseStatisticsManager

logger = logging.getLogger(__name__)


class ProtocolStatisticsManager(BaseStatisticsManager):
    """
    Protocol Analytics 統計管理器
    
    繼承自 BaseStatisticsManager，實現 Protocol Assistant 特定的統計需求
    """
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    # ==================== 實現抽象方法 ====================
    
    def get_assistant_type(self) -> str:
        """返回 Assistant 類型"""
        return 'protocol_assistant'
    
    def get_conversation_model(self):
        """返回對話模型"""
        from api.models import ConversationSession
        return ConversationSession
    
    def get_message_model(self):
        """返回消息模型"""
        from api.models import ChatMessage
        return ChatMessage
    
    # ==================== 覆寫統計方法以包含額外分析 ====================
    
    def get_comprehensive_stats(self, days=30, user=None) -> Dict:
        """
        獲取綜合統計數據（覆寫以添加問題和滿意度分析）
        
        Args:
            days: 統計天數
            user: 特定用戶（可選）
            
        Returns:
            dict: 綜合統計結果
        """
        try:
            # 調用基類的統計方法
            base_stats = super().get_comprehensive_stats(days, user)
            
            # 添加 Protocol 特定的統計
            question_stats = self._get_question_stats(days, user)
            satisfaction_stats = self._get_satisfaction_stats(days, user)
            
            # 合併結果
            base_stats['question_analysis'] = question_stats
            base_stats['satisfaction_analysis'] = satisfaction_stats
            
            return base_stats
            
        except Exception as e:
            self.logger.error(f"獲取綜合統計失敗: {str(e)}", exc_info=True)
            return {
                'error': f'統計生成失敗: {str(e)}',
                'generated_at': datetime.now().isoformat()
            }
    
    def _get_question_stats(self, days: int, user=None) -> Dict:
        """獲取問題統計（Protocol 特定邏輯）"""
        try:
            from .question_classifier import ProtocolQuestionClassifier, classify_protocol_question
            from django.utils import timezone
            from api.models import ChatMessage, ConversationSession
            from collections import Counter
            
            # 獲取用戶消息
            start_date = timezone.now() - timedelta(days=days)
            messages_query = ChatMessage.objects.filter(
                role='user',
                created_at__gte=start_date
            )
            
            if user:
                user_sessions = ConversationSession.objects.filter(user=user)
                messages_query = messages_query.filter(
                    conversation_id__in=user_sessions.values_list('id', flat=True)
                )
            
            user_messages = list(messages_query.values_list('content', flat=True))
            
            if not user_messages:
                return {
                    'total_questions': 0,
                    'category_distribution': {},
                    'top_questions': [],
                    'popular_questions': []
                }
            
            # 問題分類統計
            classifier = ProtocolQuestionClassifier()
            category_counts = {}
            classified_questions = []
            
            for question in user_messages:
                classification = classify_protocol_question(question)
                category = classification['category']
                
                if category not in category_counts:
                    category_counts[category] = 0
                category_counts[category] += 1
                
                classified_questions.append((question, category))
            
            # 獲取分類統計
            category_stats = classifier.get_category_stats(classified_questions)
            
            # 計算熱門問題（問題頻率統計）
            question_counter = Counter(user_messages)
            popular_questions = [
                {
                    'question': question,
                    'count': count,
                    'percentage': round((count / len(user_messages)) * 100, 2)
                }
                for question, count in question_counter.most_common(20)
            ]
            
            return {
                'total_questions': len(user_messages),
                'category_distribution': category_counts,
                'category_percentages': category_stats.get('category_percentages', {}),
                'top_categories': category_stats.get('top_categories', []),
                'popular_questions': popular_questions
            }
            
        except Exception as e:
            self.logger.error(f"獲取問題統計失敗: {str(e)}")
            return {'error': str(e)}
    
    def _get_satisfaction_stats(self, days: int, user=None) -> Dict:
        """獲取滿意度統計（複用 RVT 分析器）"""
        try:
            # 複用 RVT Analytics 的 satisfaction_analyzer
            from library.rvt_analytics.satisfaction_analyzer import analyze_user_satisfaction
            
            satisfaction_result = analyze_user_satisfaction(
                user=user,
                days=days,
                assistant_type='protocol_assistant'
            )
            
            return satisfaction_result
            
        except Exception as e:
            self.logger.error(f"獲取滿意度統計失敗: {str(e)}")
            return {'error': str(e)}
    
    # ==================== Protocol 專屬方法（如果需要） ====================
    
    def get_protocol_specific_metrics(self, days=30, user=None) -> Dict:
        """
        獲取 Protocol 專屬的統計指標
        
        例如：Protocol 測試相關的特定統計
        """
        try:
            # 示例：Protocol 專屬的統計邏輯
            # 可以統計與 Protocol 測試相關的特定欄位
            
            return {
                'protocol_test_count': 0,
                'protocol_error_rate': 0,
                # ... 其他 Protocol 專屬指標
            }
            
        except Exception as e:
            self.logger.error(f"獲取 Protocol 專屬指標失敗: {str(e)}", exc_info=True)
            return {}


# ==================== 便利函數 ====================

def get_protocol_analytics_stats(days=30, user=None) -> Dict:
    """
    便利函數：獲取 Protocol Analytics 統計數據
    
    Args:
        days: 統計天數
        user: 特定用戶（可選）
        
    Returns:
        dict: 統計結果
    """
    manager = ProtocolStatisticsManager()
    return manager.get_comprehensive_stats(days, user)


__all__ = [
    'ProtocolStatisticsManager',
    'get_protocol_analytics_stats',
]
