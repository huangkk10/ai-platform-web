"""
Satisfaction Analyzer - RVT Assistant 滿意度分析器

此模組負責：
- 分析用戶滿意度趨勢
- 識別高/低滿意度問題類型
- 計算整體滿意度指標
- 提供改進建議
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SatisfactionAnalyzer:
    """滿意度分析器"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def analyze_user_satisfaction(self, user=None, days=30, conversation_id=None) -> Dict:
        """
        分析用戶滿意度
        
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
                    'message': '沒有找到相關消息數據'
                }
            
            # 基礎統計
            basic_stats = self._calculate_basic_stats(messages_data)
            
            # 滿意度趨勢
            satisfaction_trends = self._calculate_satisfaction_trends(messages_data, days)
            
            # 問題類型滿意度
            category_satisfaction = self._analyze_category_satisfaction(messages_data)
            
            # 回應時間與滿意度關係
            response_time_analysis = self._analyze_response_time_satisfaction(messages_data)
            
            # 生成建議
            recommendations = self._generate_recommendations(basic_stats, category_satisfaction)
            
            return {
                'analysis_period': f'{days} 天',
                'basic_stats': basic_stats,
                'satisfaction_trends': satisfaction_trends,
                'category_satisfaction': category_satisfaction,
                'response_time_analysis': response_time_analysis,
                'recommendations': recommendations,
                'analyzed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"滿意度分析失敗: {str(e)}")
            return {
                'error': f'滿意度分析失敗: {str(e)}'
            }
    
    def _get_messages_data(self, user=None, days=30, conversation_id=None) -> List[Dict]:
        """獲取消息數據"""
        try:
            from django.utils import timezone
            from api.models import ChatMessage, ConversationSession
            
            # 基礎查詢 - 只分析 AI 回覆
            queryset = ChatMessage.objects.filter(role='assistant')
            
            # 時間過濾
            if days:
                start_date = timezone.now() - timedelta(days=days)
                queryset = queryset.filter(created_at__gte=start_date)
            
            # 對話過濾
            if conversation_id:
                queryset = queryset.filter(conversation_id=conversation_id)
            
            # 用戶過濾
            if user:
                user_sessions = ConversationSession.objects.filter(user=user)
                queryset = queryset.filter(conversation_id__in=user_sessions.values_list('id', flat=True))
            
            # 提取數據
            messages_data = []
            for message in queryset.select_related('conversation'):
                try:
                    # 嘗試獲取對應的用戶問題
                    user_message = ChatMessage.objects.filter(
                        conversation_id=message.conversation_id,
                        role='user',
                        sequence_number=message.sequence_number - 1
                    ).first()
                    
                    message_data = {
                        'id': message.id,
                        'message_id': message.message_id,
                        'conversation_id': message.conversation_id,
                        'content': message.content,
                        'is_helpful': message.is_helpful,
                        'response_time': message.response_time,
                        'confidence_score': message.confidence_score,
                        'created_at': message.created_at,
                        'sequence_number': message.sequence_number,
                        'user_question': user_message.content if user_message else None
                    }
                    
                    messages_data.append(message_data)
                    
                except Exception as e:
                    self.logger.warning(f"處理消息 {message.id} 時出錯: {str(e)}")
                    continue
            
            return messages_data
            
        except Exception as e:
            self.logger.error(f"獲取消息數據失敗: {str(e)}")
            return []
    
    def _calculate_basic_stats(self, messages_data: List[Dict]) -> Dict:
        """計算基礎統計數據"""
        total_messages = len(messages_data)
        if total_messages == 0:
            return {'total_messages': 0}
        
        # 反饋統計
        helpful_count = sum(1 for msg in messages_data if msg['is_helpful'] is True)
        unhelpful_count = sum(1 for msg in messages_data if msg['is_helpful'] is False)
        unrated_count = sum(1 for msg in messages_data if msg['is_helpful'] is None)
        
        # 滿意度計算
        rated_count = helpful_count + unhelpful_count
        satisfaction_rate = (helpful_count / rated_count) if rated_count > 0 else None
        feedback_rate = (rated_count / total_messages) if total_messages > 0 else 0
        
        # 回應時間統計
        response_times = [msg['response_time'] for msg in messages_data if msg['response_time'] is not None]
        avg_response_time = sum(response_times) / len(response_times) if response_times else None
        
        # 信心分數統計
        confidence_scores = [msg['confidence_score'] for msg in messages_data if msg['confidence_score'] is not None]
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else None
        
        return {
            'total_messages': total_messages,
            'helpful_count': helpful_count,
            'unhelpful_count': unhelpful_count,
            'unrated_count': unrated_count,
            'satisfaction_rate': round(satisfaction_rate, 3) if satisfaction_rate is not None else None,
            'feedback_rate': round(feedback_rate, 3),
            'avg_response_time': round(avg_response_time, 2) if avg_response_time is not None else None,
            'avg_confidence_score': round(avg_confidence, 3) if avg_confidence is not None else None
        }
    
    def _calculate_satisfaction_trends(self, messages_data: List[Dict], days: int) -> Dict:
        """計算滿意度趨勢"""
        try:
            from collections import defaultdict
            
            # 按日期分組
            daily_stats = defaultdict(lambda: {'helpful': 0, 'unhelpful': 0, 'total': 0})
            
            for message in messages_data:
                date_key = message['created_at'].date().isoformat()
                daily_stats[date_key]['total'] += 1
                
                if message['is_helpful'] is True:
                    daily_stats[date_key]['helpful'] += 1
                elif message['is_helpful'] is False:
                    daily_stats[date_key]['unhelpful'] += 1
            
            # 計算每日滿意度
            daily_satisfaction = {}
            for date, stats in daily_stats.items():
                rated = stats['helpful'] + stats['unhelpful']
                if rated > 0:
                    satisfaction_rate = stats['helpful'] / rated
                    daily_satisfaction[date] = {
                        'satisfaction_rate': round(satisfaction_rate, 3),
                        'total_messages': stats['total'],
                        'rated_messages': rated
                    }
            
            return {
                'daily_satisfaction': daily_satisfaction,
                'trend_summary': self._analyze_trend(daily_satisfaction)
            }
            
        except Exception as e:
            self.logger.error(f"計算滿意度趨勢失敗: {str(e)}")
            return {'error': str(e)}
    
    def _analyze_category_satisfaction(self, messages_data: List[Dict]) -> Dict:
        """分析各問題類型的滿意度"""
        try:
            from .question_classifier import classify_question
            from collections import defaultdict
            
            category_stats = defaultdict(lambda: {'helpful': 0, 'unhelpful': 0, 'total': 0})
            
            for message in messages_data:
                # 對用戶問題進行分類
                if message['user_question']:
                    classification = classify_question(message['user_question'])
                    category = classification['category']
                else:
                    category = 'unknown'
                
                category_stats[category]['total'] += 1
                
                if message['is_helpful'] is True:
                    category_stats[category]['helpful'] += 1
                elif message['is_helpful'] is False:
                    category_stats[category]['unhelpful'] += 1
            
            # 計算各類別滿意度
            category_satisfaction = {}
            for category, stats in category_stats.items():
                rated = stats['helpful'] + stats['unhelpful']
                if rated > 0:
                    satisfaction_rate = stats['helpful'] / rated
                    category_satisfaction[category] = {
                        'satisfaction_rate': round(satisfaction_rate, 3),
                        'total_messages': stats['total'],
                        'helpful_count': stats['helpful'],
                        'unhelpful_count': stats['unhelpful'],
                        'feedback_rate': round(rated / stats['total'], 3)
                    }
            
            # 排序
            sorted_categories = sorted(
                category_satisfaction.items(),
                key=lambda x: x[1]['satisfaction_rate'],
                reverse=True
            )
            
            return {
                'category_satisfaction': dict(sorted_categories),
                'best_categories': sorted_categories[:3],
                'worst_categories': sorted_categories[-3:] if len(sorted_categories) >= 3 else []
            }
            
        except Exception as e:
            self.logger.error(f"分析分類滿意度失敗: {str(e)}")
            return {'error': str(e)}
    
    def _analyze_response_time_satisfaction(self, messages_data: List[Dict]) -> Dict:
        """分析回應時間與滿意度的關係"""
        try:
            # 將回應時間分組
            time_buckets = {
                'fast': {'range': '< 3秒', 'helpful': 0, 'unhelpful': 0},
                'medium': {'range': '3-10秒', 'helpful': 0, 'unhelpful': 0},
                'slow': {'range': '> 10秒', 'helpful': 0, 'unhelpful': 0}
            }
            
            for message in messages_data:
                if message['response_time'] is None or message['is_helpful'] is None:
                    continue
                
                response_time = message['response_time']
                is_helpful = message['is_helpful']
                
                if response_time < 3:
                    bucket = 'fast'
                elif response_time <= 10:
                    bucket = 'medium'
                else:
                    bucket = 'slow'
                
                if is_helpful:
                    time_buckets[bucket]['helpful'] += 1
                else:
                    time_buckets[bucket]['unhelpful'] += 1
            
            # 計算各時間段滿意度
            for bucket, data in time_buckets.items():
                total = data['helpful'] + data['unhelpful']
                if total > 0:
                    data['satisfaction_rate'] = round(data['helpful'] / total, 3)
                    data['total_messages'] = total
                else:
                    data['satisfaction_rate'] = None
                    data['total_messages'] = 0
            
            return time_buckets
            
        except Exception as e:
            self.logger.error(f"分析回應時間滿意度失敗: {str(e)}")
            return {'error': str(e)}
    
    def _analyze_trend(self, daily_satisfaction: Dict) -> Dict:
        """分析趨勢"""
        if len(daily_satisfaction) < 2:
            return {'trend': 'insufficient_data'}
        
        # 簡單趨勢分析
        dates = sorted(daily_satisfaction.keys())
        satisfaction_values = [daily_satisfaction[date]['satisfaction_rate'] for date in dates]
        
        # 計算趨勢
        first_half = satisfaction_values[:len(satisfaction_values)//2]
        second_half = satisfaction_values[len(satisfaction_values)//2:]
        
        avg_first = sum(first_half) / len(first_half)
        avg_second = sum(second_half) / len(second_half)
        
        trend = 'improving' if avg_second > avg_first else 'declining' if avg_second < avg_first else 'stable'
        
        return {
            'trend': trend,
            'avg_satisfaction_first_half': round(avg_first, 3),
            'avg_satisfaction_second_half': round(avg_second, 3),
            'change': round(avg_second - avg_first, 3)
        }
    
    def _generate_recommendations(self, basic_stats: Dict, category_satisfaction: Dict) -> List[str]:
        """生成改進建議"""
        recommendations = []
        
        try:
            # 基於整體滿意度的建議
            satisfaction_rate = basic_stats.get('satisfaction_rate')
            if satisfaction_rate is not None:
                if satisfaction_rate < 0.6:
                    recommendations.append("整體滿意度偏低，建議檢查回答品質和相關性")
                elif satisfaction_rate > 0.8:
                    recommendations.append("整體滿意度良好，繼續保持現有服務品質")
            
            # 基於反饋率的建議
            feedback_rate = basic_stats.get('feedback_rate', 0)
            if feedback_rate < 0.3:
                recommendations.append("用戶反饋率較低，可考慮增加反饋提醒或簡化反饋流程")
            
            # 基於回應時間的建議
            avg_response_time = basic_stats.get('avg_response_time')
            if avg_response_time and avg_response_time > 10:
                recommendations.append("平均回應時間較長，建議優化處理效率")
            
            # 基於問題類型的建議
            category_data = category_satisfaction.get('category_satisfaction', {})
            if category_data:
                worst_categories = sorted(
                    category_data.items(),
                    key=lambda x: x[1]['satisfaction_rate']
                )[:2]
                
                for category, stats in worst_categories:
                    if stats['satisfaction_rate'] < 0.5:
                        recommendations.append(f"'{category}' 類問題滿意度較低，建議加強相關知識庫內容")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"生成建議失敗: {str(e)}")
            return ["建議生成失敗，請檢查系統狀態"]

# 便利函數
def analyze_user_satisfaction(user=None, days=30, conversation_id=None) -> Dict:
    """滿意度分析便利函數"""
    analyzer = SatisfactionAnalyzer()
    return analyzer.analyze_user_satisfaction(user, days, conversation_id)

def get_satisfaction_trends(days=7) -> Dict:
    """獲取滿意度趨勢便利函數"""
    analyzer = SatisfactionAnalyzer()
    result = analyzer.analyze_user_satisfaction(days=days)
    return result.get('satisfaction_trends', {})