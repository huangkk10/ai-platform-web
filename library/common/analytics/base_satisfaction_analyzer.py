"""
Base Satisfaction Analyzer - 共用滿意度分析器基礎類別

提供所有 Assistant 滿意度分析的共用邏輯。
各個 Assistant 繼承此類別並實作特定邏輯。

Usage:
    from library.common.analytics.base_satisfaction_analyzer import BaseSatisfactionAnalyzer
    
    class RVTSatisfactionAnalyzer(BaseSatisfactionAnalyzer):
        def get_assistant_type(self):
            return 'rvt_assistant'
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseSatisfactionAnalyzer(ABC):
    """
    滿意度分析器基礎類別
    
    提供共用的滿意度分析邏輯
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    # ==================== 抽象方法（子類別必須實作） ====================
    
    @abstractmethod
    def get_assistant_type(self) -> str:
        """返回 Assistant 類型識別符"""
        pass
    
    @abstractmethod
    def get_message_model(self):
        """返回消息 Model 類別"""
        pass
    
    @abstractmethod
    def get_conversation_model(self):
        """返回對話 Model 類別"""
        pass
    
    # ==================== 可選覆寫方法 ====================
    
    def get_system_type_filter(self) -> str:
        """返回 system_type 過濾值（預設使用 get_assistant_type）"""
        return self.get_assistant_type()
    
    # ==================== 共用分析方法 ====================
    
    def analyze_user_satisfaction(self, user=None, days=30, conversation_id=None) -> Dict:
        """
        分析用戶滿意度（共用邏輯）
        
        Args:
            user: 特定用戶（可選）
            days: 分析天數
            conversation_id: 特定對話（可選）
            
        Returns:
            dict: 滿意度分析結果
        """
        try:
            # 獲取消息數據
            messages_data = self._get_messages_data(user, days, conversation_id)
            
            if not messages_data:
                return {
                    'total_messages': 0,
                    'satisfaction_score': None,
                    'message': '沒有找到相關消息數據',
                    'assistant_type': self.get_assistant_type()
                }
            
            # 基礎統計
            basic_stats = self._calculate_basic_stats(messages_data)
            
            # 回應時間與滿意度關係
            response_time_analysis = self._analyze_response_time_satisfaction(messages_data)
            
            # 生成建議
            recommendations = self._generate_recommendations(basic_stats, response_time_analysis)
            
            return {
                'analysis_period': f'{days} 天',
                'assistant_type': self.get_assistant_type(),
                'basic_stats': basic_stats,
                'response_time_analysis': response_time_analysis,
                'recommendations': recommendations,
                'analyzed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"滿意度分析失敗: {str(e)}", exc_info=True)
            return {
                'error': f'滿意度分析失敗: {str(e)}',
                'assistant_type': self.get_assistant_type()
            }
    
    def _get_messages_data(self, user=None, days=30, conversation_id=None) -> List[Dict]:
        """獲取消息數據（共用邏輯）"""
        try:
            from django.utils import timezone
            
            MessageModel = self.get_message_model()
            ConversationModel = self.get_conversation_model()
            
            start_date = timezone.now() - timedelta(days=days)
            system_type = self.get_system_type_filter()
            
            # 建立查詢
            if conversation_id:
                # 查詢特定對話
                messages_query = MessageModel.objects.filter(
                    conversation_id=conversation_id,
                    role='assistant'
                )
            else:
                # 查詢時間範圍內的對話
                sessions_query = ConversationModel.objects.filter(
                    created_at__gte=start_date,
                    system_type=system_type
                )
                
                if user:
                    sessions_query = sessions_query.filter(user=user)
                
                conversation_ids = sessions_query.values_list('conversation_id', flat=True)
                messages_query = MessageModel.objects.filter(
                    conversation_id__in=conversation_ids,
                    role='assistant',
                    created_at__gte=start_date
                )
            
            # 提取數據
            messages_data = []
            for msg in messages_query:
                data = {
                    'id': msg.id,
                    'conversation_id': msg.conversation_id,
                    'content': msg.content,
                    'created_at': msg.created_at,
                    'is_helpful': getattr(msg, 'is_helpful', None),
                    'feedback': getattr(msg, 'feedback', None),
                    'response_time': getattr(msg, 'response_time', None)
                }
                messages_data.append(data)
            
            return messages_data
            
        except Exception as e:
            self.logger.error(f"獲取消息數據失敗: {str(e)}", exc_info=True)
            return []
    
    def _calculate_basic_stats(self, messages_data: List[Dict]) -> Dict:
        """計算基礎滿意度統計（共用邏輯）"""
        try:
            total_messages = len(messages_data)
            
            if total_messages == 0:
                return {
                    'total_messages': 0,
                    'helpful_count': 0,
                    'unhelpful_count': 0,
                    'unrated_count': 0,
                    'satisfaction_rate': 0,
                    'feedback_rate': 0
                }
            
            # 統計反饋
            helpful_count = sum(1 for msg in messages_data if msg.get('is_helpful') == True)
            unhelpful_count = sum(1 for msg in messages_data if msg.get('is_helpful') == False)
            unrated_count = total_messages - helpful_count - unhelpful_count
            
            # 計算比率
            feedback_count = helpful_count + unhelpful_count
            feedback_rate = feedback_count / total_messages if total_messages > 0 else 0
            satisfaction_rate = helpful_count / feedback_count if feedback_count > 0 else 0
            
            return {
                'total_messages': total_messages,
                'helpful_count': helpful_count,
                'unhelpful_count': unhelpful_count,
                'unrated_count': unrated_count,
                'feedback_count': feedback_count,
                'satisfaction_rate': round(satisfaction_rate, 4),
                'feedback_rate': round(feedback_rate, 4)
            }
            
        except Exception as e:
            self.logger.error(f"計算基礎統計失敗: {str(e)}", exc_info=True)
            return {
                'total_messages': len(messages_data),
                'error': str(e)
            }
    
    def _analyze_response_time_satisfaction(self, messages_data: List[Dict]) -> Dict:
        """分析回應時間與滿意度關係（共用邏輯）"""
        try:
            # 過濾有回應時間和反饋的消息
            messages_with_time_and_feedback = [
                msg for msg in messages_data 
                if msg.get('response_time') is not None 
                and msg.get('is_helpful') is not None
            ]
            
            if not messages_with_time_and_feedback:
                return {
                    'fast': {'total_messages': 0, 'satisfaction_rate': 0},
                    'medium': {'total_messages': 0, 'satisfaction_rate': 0},
                    'slow': {'total_messages': 0, 'satisfaction_rate': 0}
                }
            
            # 分類消息（快速 < 3s, 中等 3-10s, 較慢 > 10s）
            fast_messages = [msg for msg in messages_with_time_and_feedback if msg['response_time'] < 3]
            medium_messages = [msg for msg in messages_with_time_and_feedback if 3 <= msg['response_time'] < 10]
            slow_messages = [msg for msg in messages_with_time_and_feedback if msg['response_time'] >= 10]
            
            # 計算各類別滿意度
            def calc_satisfaction(messages):
                if not messages:
                    return {'total_messages': 0, 'satisfaction_rate': 0, 'helpful_count': 0}
                total = len(messages)
                helpful = sum(1 for msg in messages if msg['is_helpful'] == True)
                return {
                    'total_messages': total,
                    'helpful_count': helpful,
                    'satisfaction_rate': round(helpful / total, 4) if total > 0 else 0
                }
            
            return {
                'fast': calc_satisfaction(fast_messages),
                'medium': calc_satisfaction(medium_messages),
                'slow': calc_satisfaction(slow_messages),
                'total_analyzed': len(messages_with_time_and_feedback)
            }
            
        except Exception as e:
            self.logger.error(f"分析回應時間滿意度失敗: {str(e)}", exc_info=True)
            return {
                'error': str(e)
            }
    
    def _generate_recommendations(self, basic_stats: Dict, response_time_analysis: Dict) -> List[str]:
        """生成改進建議（共用邏輯，子類別可覆寫以添加專屬建議）"""
        recommendations = []
        
        try:
            # 基於滿意度率的建議
            satisfaction_rate = basic_stats.get('satisfaction_rate', 0)
            feedback_rate = basic_stats.get('feedback_rate', 0)
            
            if satisfaction_rate < 0.6:
                recommendations.append(f"整體滿意度較低 ({satisfaction_rate*100:.1f}%)，建議檢視負面反饋並改進回答品質")
            elif satisfaction_rate < 0.8:
                recommendations.append(f"滿意度中等 ({satisfaction_rate*100:.1f}%)，仍有改進空間")
            else:
                recommendations.append(f"滿意度良好 ({satisfaction_rate*100:.1f}%)，請保持當前服務品質")
            
            if feedback_rate < 0.3:
                recommendations.append(f"用戶反饋率較低 ({feedback_rate*100:.1f}%)，建議鼓勵用戶提供反饋")
            
            # 基於回應時間的建議
            if 'fast' in response_time_analysis and 'slow' in response_time_analysis:
                fast_sat = response_time_analysis['fast'].get('satisfaction_rate', 0)
                slow_sat = response_time_analysis['slow'].get('satisfaction_rate', 0)
                
                if fast_sat > slow_sat + 0.1:  # 快速回應滿意度明顯更高
                    recommendations.append("快速回應的滿意度較高，建議優化回應速度")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"生成建議失敗: {str(e)}", exc_info=True)
            return ["建議生成失敗"]
