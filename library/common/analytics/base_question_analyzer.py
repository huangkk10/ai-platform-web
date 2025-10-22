"""
Base Question Analyzer - 共用問題分析器基礎類別

提供所有 Assistant 問題分析的共用邏輯。
各個 Assistant 繼承此類別並實作特定邏輯。

Usage:
    from library.common.analytics.base_question_analyzer import BaseQuestionAnalyzer
    
    class RVTQuestionAnalyzer(BaseQuestionAnalyzer):
        def get_assistant_type(self):
            return 'rvt_assistant'
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from collections import Counter

logger = logging.getLogger(__name__)


class BaseQuestionAnalyzer(ABC):
    """
    問題分析器基礎類別
    
    提供共用的問題分析邏輯
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
        """返回 system_type 過濾值"""
        return self.get_assistant_type()
    
    def get_question_categories(self) -> List[str]:
        """
        返回問題分類列表（子類別可覆寫以提供專屬分類）
        
        Returns:
            list: 問題分類名稱列表
        """
        return [
            '技術問題',
            '操作指南',
            '故障排除',
            '功能諮詢',
            '其他'
        ]
    
    # ==================== 共用分析方法 ====================
    
    def analyze_questions(self, days=30, user=None, mode='simple') -> Dict:
        """
        分析問題統計（共用邏輯）
        
        Args:
            days: 分析天數
            user: 特定用戶（可選）
            mode: 分析模式 ('simple' 或 'smart')
            
        Returns:
            dict: 問題分析結果
        """
        try:
            # 獲取用戶問題
            questions = self._get_user_questions(days, user)
            
            if not questions:
                return {
                    'total_questions': 0,
                    'message': '沒有找到相關問題數據',
                    'assistant_type': self.get_assistant_type()
                }
            
            # 基礎統計
            total_questions = len(questions)
            
            # 關鍵詞提取
            top_keywords = self._extract_top_keywords(questions)
            
            # 問題頻率統計
            popular_questions = self._analyze_popular_questions(questions, mode)
            
            # 分類統計（如果有分類資訊）
            category_distribution = self._analyze_category_distribution(questions)
            
            return {
                'analysis_period': f'{days} 天',
                'assistant_type': self.get_assistant_type(),
                'period': f'最近 {days} 天',
                'total_questions': total_questions,
                'top_keywords': top_keywords,
                'popular_questions': popular_questions,
                'category_distribution': category_distribution,
                'analysis_method': mode,
                'analyzed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"問題分析失敗: {str(e)}", exc_info=True)
            return {
                'error': f'問題分析失敗: {str(e)}',
                'assistant_type': self.get_assistant_type()
            }
    
    def _get_user_questions(self, days: int, user=None) -> List[Dict]:
        """獲取用戶問題（共用邏輯）"""
        try:
            from django.utils import timezone
            
            MessageModel = self.get_message_model()
            ConversationModel = self.get_conversation_model()
            
            start_date = timezone.now() - timedelta(days=days)
            system_type = self.get_system_type_filter()
            
            # 查詢對話
            sessions_query = ConversationModel.objects.filter(
                created_at__gte=start_date,
                system_type=system_type
            )
            
            if user:
                sessions_query = sessions_query.filter(user=user)
            
            conversation_ids = sessions_query.values_list('conversation_id', flat=True)
            
            # 查詢用戶問題（role='user'）
            questions_query = MessageModel.objects.filter(
                conversation_id__in=conversation_ids,
                role='user',
                created_at__gte=start_date
            ).order_by('-created_at')
            
            # 提取數據
            questions = []
            for msg in questions_query:
                data = {
                    'id': msg.id,
                    'content': msg.content,
                    'conversation_id': msg.conversation_id,
                    'created_at': msg.created_at
                }
                questions.append(data)
            
            return questions
            
        except Exception as e:
            self.logger.error(f"獲取用戶問題失敗: {str(e)}", exc_info=True)
            return []
    
    def _extract_top_keywords(self, questions: List[Dict], top_n=10) -> List[Dict]:
        """提取高頻關鍵詞（共用邏輯）"""
        try:
            import jieba
            from collections import Counter
            
            # 停用詞
            stop_words = {'的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', 
                         '一個', '上', '也', '很', '到', '說', '要', '去', '你', '會', '著', '沒有',
                         '看', '好', '自己', '這', '嗎', '？', '！', '。', '，', '、', '怎麼', '什麼',
                         '可以', '請問', '如何', '為什麼', '能', '想', '請', '謝謝', '幫忙'}
            
            # 提取所有問題的關鍵詞
            all_words = []
            for q in questions:
                content = q.get('content', '')
                if content:
                    words = jieba.cut(content)
                    # 過濾停用詞和短詞
                    filtered_words = [
                        w for w in words 
                        if w not in stop_words and len(w) > 1
                    ]
                    all_words.extend(filtered_words)
            
            # 統計詞頻
            word_counts = Counter(all_words)
            top_keywords = [
                {'keyword': word, 'count': count}
                for word, count in word_counts.most_common(top_n)
            ]
            
            return top_keywords
            
        except ImportError:
            self.logger.warning("jieba 未安裝，跳過關鍵詞提取")
            return []
        except Exception as e:
            self.logger.error(f"提取關鍵詞失敗: {str(e)}", exc_info=True)
            return []
    
    def _analyze_popular_questions(self, questions: List[Dict], mode='simple') -> List[Dict]:
        """分析熱門問題（共用邏輯）"""
        try:
            if mode == 'smart':
                # 智慧分析模式（如果有向量服務）
                return self._smart_analyze_popular_questions(questions)
            else:
                # 簡單頻率統計
                return self._simple_analyze_popular_questions(questions)
            
        except Exception as e:
            self.logger.error(f"分析熱門問題失敗: {str(e)}", exc_info=True)
            return []
    
    def _simple_analyze_popular_questions(self, questions: List[Dict], top_n=10) -> List[Dict]:
        """簡單頻率統計（共用邏輯）"""
        try:
            from collections import Counter
            
            # 統計問題頻率
            question_counts = Counter(q['content'] for q in questions if q.get('content'))
            
            # 取前 N 個高頻問題
            popular = [
                {
                    'question': question,
                    'count': count,
                    'pattern': question[:50] + '...' if len(question) > 50 else question
                }
                for question, count in question_counts.most_common(top_n)
            ]
            
            return popular
            
        except Exception as e:
            self.logger.error(f"簡單頻率統計失敗: {str(e)}", exc_info=True)
            return []
    
    def _smart_analyze_popular_questions(self, questions: List[Dict]) -> List[Dict]:
        """
        智慧分析熱門問題（使用向量聚類）
        
        子類別可以覆寫此方法以實作專屬的智慧分析邏輯
        """
        # 預設降級到簡單統計
        self.logger.info("智慧分析模式未實作，降級到簡單統計")
        return self._simple_analyze_popular_questions(questions)
    
    def _analyze_category_distribution(self, questions: List[Dict]) -> Dict[str, int]:
        """
        分析問題分類分布（共用邏輯）
        
        子類別可以覆寫此方法以實作專屬的分類邏輯
        """
        try:
            # 預設使用簡單分類（基於關鍵詞）
            categories = self.get_question_categories()
            distribution = {cat: 0 for cat in categories}
            
            # 關鍵詞映射（子類別可以覆寫）
            category_keywords = {
                '技術問題': ['錯誤', '失敗', '問題', 'error', 'bug', '不行'],
                '操作指南': ['如何', '怎麼', '步驟', '教學', '使用'],
                '故障排除': ['無法', '不能', '卡住', '異常', '修復'],
                '功能諮詢': ['功能', '支援', '可以', '能不能', '有沒有'],
            }
            
            for q in questions:
                content = q.get('content', '').lower()
                categorized = False
                
                for category, keywords in category_keywords.items():
                    if any(keyword in content for keyword in keywords):
                        distribution[category] += 1
                        categorized = True
                        break
                
                if not categorized and '其他' in distribution:
                    distribution['其他'] += 1
            
            return distribution
            
        except Exception as e:
            self.logger.error(f"分析分類分布失敗: {str(e)}", exc_info=True)
            return {}
