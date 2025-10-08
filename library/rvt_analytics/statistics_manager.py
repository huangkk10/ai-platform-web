"""
Statistics Manager - RVT Analytics 統計管理器

此模組負責：
- 整合各種統計數據
- 生成綜合分析報告
- 提供數據導出功能
- 管理統計數據快取
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class StatisticsManager:
    """統計管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def get_comprehensive_stats(self, days=30, user=None) -> Dict:
        """
        獲取綜合統計數據
        
        Args:
            days: 統計天數
            user: 特定用戶（可選）
            
        Returns:
            dict: 綜合統計結果
        """
        try:
            # 獲取各項統計
            overview_stats = self._get_overview_stats(days, user)
            question_stats = self._get_question_stats(days, user)
            satisfaction_stats = self._get_satisfaction_stats(days, user)
            performance_stats = self._get_performance_stats(days, user)
            trend_stats = self._get_trend_stats(days, user)
            
            return {
                'generated_at': datetime.now().isoformat(),
                'period': f'{days} 天',
                'user_filter': user.username if user else 'all',
                'overview': overview_stats,
                'question_analysis': question_stats,
                'satisfaction_analysis': satisfaction_stats,
                'performance_metrics': performance_stats,
                'trends': trend_stats
            }
            
        except Exception as e:
            self.logger.error(f"獲取綜合統計失敗: {str(e)}")
            return {
                'error': f'統計生成失敗: {str(e)}',
                'generated_at': datetime.now().isoformat()
            }
    
    def _get_overview_stats(self, days: int, user=None) -> Dict:
        """獲取概覽統計"""
        try:
            from django.utils import timezone
            from api.models import ConversationSession, ChatMessage
            
            # 基礎查詢
            start_date = timezone.now() - timedelta(days=days)
            
            # 會話統計
            sessions_query = ConversationSession.objects.filter(created_at__gte=start_date)
            if user:
                sessions_query = sessions_query.filter(user=user)
            
            total_sessions = sessions_query.count()
            active_sessions = sessions_query.filter(is_active=True).count()
            guest_sessions = sessions_query.filter(is_guest_session=True).count()
            
            # 消息統計
            messages_query = ChatMessage.objects.filter(created_at__gte=start_date)
            if user:
                user_session_ids = sessions_query.values_list('id', flat=True)
                messages_query = messages_query.filter(conversation_id__in=user_session_ids)
            
            total_messages = messages_query.count()
            user_messages = messages_query.filter(role='user').count()
            assistant_messages = messages_query.filter(role='assistant').count()
            
            # 計算平均值
            avg_messages_per_session = total_messages / total_sessions if total_sessions > 0 else 0
            
            return {
                'total_conversations': total_sessions,
                'active_conversations': active_sessions,
                'guest_conversations': guest_sessions,
                'registered_user_conversations': total_sessions - guest_sessions,
                'total_messages': total_messages,
                'user_messages': user_messages,
                'assistant_messages': assistant_messages,
                'avg_messages_per_conversation': round(avg_messages_per_session, 2)
            }
            
        except Exception as e:
            self.logger.error(f"獲取概覽統計失敗: {str(e)}")
            return {'error': str(e)}
    
    def _get_question_stats(self, days: int, user=None) -> Dict:
        """獲取問題統計"""
        try:
            from .question_classifier import QuestionClassifier, classify_question
            from .message_feedback import get_message_feedback_stats
            from django.utils import timezone
            from api.models import ChatMessage, ConversationSession
            
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
                    'top_questions': []
                }
            
            # 問題分類統計
            classifier = QuestionClassifier()
            category_counts = {}
            classified_questions = []
            
            for question in user_messages:
                classification = classify_question(question)
                category = classification['category']
                
                if category not in category_counts:
                    category_counts[category] = 0
                category_counts[category] += 1
                
                classified_questions.append((question, category))
            
            # 獲取分類統計
            category_stats = classifier.get_category_stats(classified_questions)
            
            # 找出熱門問題（使用相似度歸併）
            popular_questions = self._get_popular_questions(user_messages, top_n=10)
            
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
        """獲取滿意度統計"""
        try:
            from .satisfaction_analyzer import analyze_user_satisfaction
            
            satisfaction_result = analyze_user_satisfaction(
                user=user,
                days=days
            )
            
            return satisfaction_result
            
        except Exception as e:
            self.logger.error(f"獲取滿意度統計失敗: {str(e)}")
            return {'error': str(e)}
    
    def _get_performance_stats(self, days: int, user=None) -> Dict:
        """獲取效能統計"""
        try:
            from django.utils import timezone
            from api.models import ChatMessage, ConversationSession
            
            start_date = timezone.now() - timedelta(days=days)
            
            # 查詢 AI 回覆消息
            messages_query = ChatMessage.objects.filter(
                role='assistant',
                created_at__gte=start_date
            )
            
            if user:
                user_sessions = ConversationSession.objects.filter(user=user)
                messages_query = messages_query.filter(
                    conversation_id__in=user_sessions.values_list('id', flat=True)
                )
            
            messages = messages_query.exclude(response_time__isnull=True)
            
            if not messages.exists():
                return {
                    'total_responses': 0,
                    'avg_response_time': None,
                    'response_time_distribution': {}
                }
            
            # 回應時間統計
            response_times = list(messages.values_list('response_time', flat=True))
            
            avg_response_time = sum(response_times) / len(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            
            # 回應時間分布
            time_distribution = {
                'fast (< 3s)': len([t for t in response_times if t < 3]),
                'medium (3-10s)': len([t for t in response_times if 3 <= t <= 10]),
                'slow (> 10s)': len([t for t in response_times if t > 10])
            }
            
            # Token 使用統計
            token_stats = self._calculate_token_stats(messages)
            
            return {
                'total_responses': len(response_times),
                'avg_response_time': round(avg_response_time, 2),
                'min_response_time': round(min_response_time, 2),
                'max_response_time': round(max_response_time, 2),
                'response_time_distribution': time_distribution,
                'token_statistics': token_stats
            }
            
        except Exception as e:
            self.logger.error(f"獲取效能統計失敗: {str(e)}")
            return {'error': str(e)}
    
    def _get_trend_stats(self, days: int, user=None) -> Dict:
        """獲取趨勢統計"""
        try:
            from django.utils import timezone
            from api.models import ConversationSession, ChatMessage
            from collections import defaultdict
            
            start_date = timezone.now() - timedelta(days=days)
            
            # 按日期統計會話數量
            sessions_query = ConversationSession.objects.filter(created_at__gte=start_date)
            if user:
                sessions_query = sessions_query.filter(user=user)
            
            daily_sessions = defaultdict(int)
            daily_messages = defaultdict(int)
            
            # 統計每日會話
            for session in sessions_query:
                date_key = session.created_at.date().isoformat()
                daily_sessions[date_key] += 1
            
            # 統計每日消息
            messages_query = ChatMessage.objects.filter(created_at__gte=start_date)
            if user:
                user_session_ids = sessions_query.values_list('id', flat=True)
                messages_query = messages_query.filter(conversation_id__in=user_session_ids)
            
            for message in messages_query:
                date_key = message.created_at.date().isoformat()
                daily_messages[date_key] += 1
            
            return {
                'daily_conversations': dict(daily_sessions),
                'daily_messages': dict(daily_messages),
                'trend_summary': self._analyze_usage_trend(daily_sessions, daily_messages)
            }
            
        except Exception as e:
            self.logger.error(f"獲取趨勢統計失敗: {str(e)}")
            return {'error': str(e)}
    
    def _get_popular_questions(self, questions: List[str], top_n: int = 10) -> List[Dict]:
        """獲取熱門問題（使用簡化的相似度歸併）"""
        try:
            from collections import Counter
            import re
            
            # 簡化版本：提取關鍵詞並統計
            keyword_questions = {}
            
            for question in questions:
                # 提取主要詞彙
                words = re.findall(r'\w+', question.lower())
                # 過濾常見詞彙
                filtered_words = [w for w in words if len(w) > 2 and w not in ['如何', '怎麼', '什麼', '為什麼']]
                
                if filtered_words:
                    # 使用前2個關鍵詞作為問題特徵
                    key = ' '.join(sorted(filtered_words[:2]))
                    if key not in keyword_questions:
                        keyword_questions[key] = []
                    keyword_questions[key].append(question)
            
            # 統計並排序
            popular_questions = []
            for key, question_list in keyword_questions.items():
                if len(question_list) >= 2:  # 至少出現2次才算熱門
                    popular_questions.append({
                        'pattern': key,
                        'count': len(question_list),
                        'examples': question_list[:3]  # 最多顯示3個例子
                    })
            
            # 按出現次數排序
            popular_questions.sort(key=lambda x: x['count'], reverse=True)
            
            return popular_questions[:top_n]
            
        except Exception as e:
            self.logger.error(f"獲取熱門問題失敗: {str(e)}")
            return []
    
    def _calculate_token_stats(self, messages) -> Dict:
        """計算 Token 使用統計"""
        try:
            token_usages = []
            
            for message in messages:
                if message.token_usage:
                    if isinstance(message.token_usage, dict):
                        total_tokens = message.token_usage.get('total_tokens', 0)
                        if total_tokens > 0:
                            token_usages.append(total_tokens)
            
            if not token_usages:
                return {'total_tokens': 0, 'avg_tokens_per_response': 0}
            
            total_tokens = sum(token_usages)
            avg_tokens = total_tokens / len(token_usages)
            
            return {
                'total_tokens_used': total_tokens,
                'avg_tokens_per_response': round(avg_tokens, 2),
                'max_tokens_in_response': max(token_usages),
                'min_tokens_in_response': min(token_usages)
            }
            
        except Exception as e:
            self.logger.error(f"計算 Token 統計失敗: {str(e)}")
            return {'error': str(e)}
    
    def _analyze_usage_trend(self, daily_sessions: Dict, daily_messages: Dict) -> Dict:
        """分析使用趨勢"""
        try:
            if len(daily_sessions) < 2:
                return {'trend': 'insufficient_data'}
            
            # 計算增長率
            dates = sorted(daily_sessions.keys())
            session_values = [daily_sessions.get(date, 0) for date in dates]
            
            # 簡單趨勢分析
            first_half_avg = sum(session_values[:len(session_values)//2]) / (len(session_values)//2)
            second_half_avg = sum(session_values[len(session_values)//2:]) / (len(session_values) - len(session_values)//2)
            
            growth_rate = ((second_half_avg - first_half_avg) / first_half_avg * 100) if first_half_avg > 0 else 0
            
            trend_direction = 'increasing' if growth_rate > 5 else 'decreasing' if growth_rate < -5 else 'stable'
            
            return {
                'trend_direction': trend_direction,
                'growth_rate_percent': round(growth_rate, 2),
                'avg_daily_sessions_first_half': round(first_half_avg, 2),
                'avg_daily_sessions_second_half': round(second_half_avg, 2)
            }
            
        except Exception as e:
            self.logger.error(f"分析使用趨勢失敗: {str(e)}")
            return {'error': str(e)}

# 便利函數
def get_rvt_analytics_stats(days=30, user=None) -> Dict:
    """獲取 RVT Analytics 統計數據便利函數"""
    manager = StatisticsManager()
    return manager.get_comprehensive_stats(days, user)

def generate_analytics_report(days=30, user=None, format='json') -> Dict:
    """生成分析報告便利函數"""
    stats = get_rvt_analytics_stats(days, user)
    
    if format == 'json':
        return stats
    elif format == 'summary':
        return _generate_summary_report(stats)
    else:
        return {'error': f'Unsupported format: {format}'}

def _generate_summary_report(stats: Dict) -> Dict:
    """生成摘要報告"""
    try:
        overview = stats.get('overview', {})
        satisfaction = stats.get('satisfaction_analysis', {}).get('basic_stats', {})
        
        summary = {
            'period': stats.get('period', 'unknown'),
            'key_metrics': {
                'total_conversations': overview.get('total_conversations', 0),
                'total_messages': overview.get('total_messages', 0),
                'satisfaction_rate': satisfaction.get('satisfaction_rate'),
                'feedback_rate': satisfaction.get('feedback_rate')
            },
            'highlights': []
        }
        
        # 生成重點摘要
        if satisfaction.get('satisfaction_rate', 0) > 0.8:
            summary['highlights'].append('用戶滿意度高於 80%')
        
        if overview.get('avg_messages_per_conversation', 0) > 5:
            summary['highlights'].append('用戶互動積極，平均對話長度較長')
        
        return summary
        
    except Exception as e:
        logger.error(f"生成摘要報告失敗: {str(e)}")
        return {'error': str(e)}