"""
Base API Handler - 共用 API 處理器基礎類別

提供所有 Assistant Analytics API 的共用處理邏輯。
各個 Assistant 繼承此類別並實作特定邏輯。

Usage:
    from library.common.analytics.base_api_handler import BaseAPIHandler
    
    class RVTAnalyticsAPIHandler(BaseAPIHandler):
        def get_assistant_type(self):
            return 'rvt_assistant'
        
        def get_statistics_manager(self):
            from library.rvt_analytics.statistics_manager import StatisticsManager
            return StatisticsManager()
"""

import logging
from typing import Dict, Optional, Any
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseAPIHandler(ABC):
    """
    Analytics API 處理器基礎類別
    
    提供共用的 API 處理邏輯（overview, questions, satisfaction, feedback）
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    # ==================== 抽象方法（子類別必須實作） ====================
    
    @abstractmethod
    def get_assistant_type(self) -> str:
        """返回 Assistant 類型識別符"""
        pass
    
    @abstractmethod
    def get_statistics_manager(self):
        """
        返回統計管理器實例
        
        Returns:
            BaseStatisticsManager: 統計管理器
        """
        pass
    
    @abstractmethod
    def get_question_analyzer(self):
        """
        返回問題分析器實例
        
        Returns:
            BaseQuestionAnalyzer: 問題分析器
        """
        pass
    
    @abstractmethod
    def get_satisfaction_analyzer(self):
        """
        返回滿意度分析器實例
        
        Returns:
            BaseSatisfactionAnalyzer: 滿意度分析器
        """
        pass
    
    # ==================== 共用 API 處理方法 ====================
    
    def handle_analytics_overview_api(self, request) -> Dict:
        """
        處理分析概覽 API（共用邏輯）
        
        API 端點: GET /api/{assistant}-analytics/overview/
        參數:
            - days: 統計天數（預設 30）
            - user_id: 特定用戶 ID（可選）
            
        Returns:
            dict: API 回應
        """
        try:
            # 解析參數
            days = int(request.GET.get('days', 30))
            user_id = request.GET.get('user_id')
            
            # 獲取用戶對象（如果指定）
            user = None
            if user_id:
                try:
                    from django.contrib.auth import get_user_model
                    User = get_user_model()
                    user = User.objects.get(id=user_id)
                except Exception as e:
                    self.logger.warning(f"無法找到用戶 {user_id}: {e}")
            
            # 獲取統計數據
            stats_manager = self.get_statistics_manager()
            stats = stats_manager.get_comprehensive_stats(days=days, user=user)
            
            return {
                'success': True,
                'data': stats,
                'assistant_type': self.get_assistant_type()
            }
            
        except Exception as e:
            self.logger.error(f"概覽 API 處理失敗: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'assistant_type': self.get_assistant_type()
            }
    
    def handle_question_analysis_api(self, request) -> Dict:
        """
        處理問題分析 API（共用邏輯）
        
        API 端點: GET /api/{assistant}-analytics/questions/
        參數:
            - days: 統計天數（預設 7）
            - mode: 分析模式 ('simple' 或 'smart'，預設 'simple')
            - user_id: 特定用戶 ID（可選）
            
        Returns:
            dict: API 回應
        """
        try:
            # 解析參數
            days = int(request.GET.get('days', 7))
            mode = request.GET.get('mode', 'simple')
            user_id = request.GET.get('user_id')
            
            # 獲取用戶對象
            user = None
            if user_id:
                try:
                    from django.contrib.auth import get_user_model
                    User = get_user_model()
                    user = User.objects.get(id=user_id)
                except Exception as e:
                    self.logger.warning(f"無法找到用戶 {user_id}: {e}")
            
            # 獲取問題分析
            question_analyzer = self.get_question_analyzer()
            analysis = question_analyzer.analyze_questions(days=days, user=user, mode=mode)
            
            return {
                'success': True,
                'data': analysis,
                'assistant_type': self.get_assistant_type()
            }
            
        except Exception as e:
            self.logger.error(f"問題分析 API 處理失敗: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'assistant_type': self.get_assistant_type()
            }
    
    def handle_satisfaction_analysis_api(self, request) -> Dict:
        """
        處理滿意度分析 API（共用邏輯）
        
        API 端點: GET /api/{assistant}-analytics/satisfaction/
        參數:
            - days: 統計天數（預設 30）
            - detail: 是否返回詳細分析（預設 false）
            - user_id: 特定用戶 ID（可選）
            - conversation_id: 特定對話 ID（可選）
            
        Returns:
            dict: API 回應
        """
        try:
            # 解析參數
            days = int(request.GET.get('days', 30))
            detail = request.GET.get('detail', 'false').lower() == 'true'
            user_id = request.GET.get('user_id')
            conversation_id = request.GET.get('conversation_id')
            
            # 獲取用戶對象
            user = None
            if user_id:
                try:
                    from django.contrib.auth import get_user_model
                    User = get_user_model()
                    user = User.objects.get(id=user_id)
                except Exception as e:
                    self.logger.warning(f"無法找到用戶 {user_id}: {e}")
            
            # 獲取滿意度分析
            satisfaction_analyzer = self.get_satisfaction_analyzer()
            analysis = satisfaction_analyzer.analyze_user_satisfaction(
                user=user,
                days=days,
                conversation_id=conversation_id
            )
            
            return {
                'success': True,
                'data': analysis,
                'assistant_type': self.get_assistant_type()
            }
            
        except Exception as e:
            self.logger.error(f"滿意度分析 API 處理失敗: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'assistant_type': self.get_assistant_type()
            }
    
    def handle_message_feedback_api(self, request) -> Dict:
        """
        處理消息反饋 API（共用邏輯）
        
        API 端點: POST /api/{assistant}-analytics/feedback/
        請求 Body:
            - message_id: 消息 ID（必填）
            - is_helpful: 是否有幫助（true/false，必填）
            - feedback: 文字反饋（可選）
            
        Returns:
            dict: API 回應
        """
        try:
            import json
            
            # 解析請求
            if request.method != 'POST':
                return {
                    'success': False,
                    'error': '僅支援 POST 請求'
                }
            
            # 獲取請求數據
            try:
                data = json.loads(request.body.decode('utf-8'))
            except json.JSONDecodeError:
                return {
                    'success': False,
                    'error': '無效的 JSON 格式'
                }
            
            message_id = data.get('message_id')
            is_helpful = data.get('is_helpful')
            feedback = data.get('feedback', '')
            
            # 驗證必填欄位
            if message_id is None:
                return {
                    'success': False,
                    'error': '缺少 message_id 參數'
                }
            
            if is_helpful is None:
                return {
                    'success': False,
                    'error': '缺少 is_helpful 參數'
                }
            
            # 更新消息反饋
            result = self._update_message_feedback(message_id, is_helpful, feedback)
            
            if result['success']:
                return {
                    'success': True,
                    'message': '反饋已保存',
                    'data': result.get('data', {}),
                    'assistant_type': self.get_assistant_type()
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', '保存反饋失敗'),
                    'assistant_type': self.get_assistant_type()
                }
            
        except Exception as e:
            self.logger.error(f"反饋 API 處理失敗: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'assistant_type': self.get_assistant_type()
            }
    
    def _update_message_feedback(self, message_id: int, is_helpful: bool, feedback: str = '') -> Dict:
        """
        更新消息反饋（子類別可覆寫以實作專屬邏輯）
        
        Args:
            message_id: 消息 ID
            is_helpful: 是否有幫助
            feedback: 文字反饋
            
        Returns:
            dict: {'success': bool, 'error': str, 'data': dict}
        """
        try:
            # 獲取消息 Model（需要子類別提供）
            from django.apps import apps
            
            # 嘗試找到消息 Model
            try:
                MessageModel = apps.get_model('api', 'ChatMessage')
            except LookupError:
                return {
                    'success': False,
                    'error': 'ChatMessage Model 未找到'
                }
            
            # 查找消息
            try:
                message = MessageModel.objects.get(id=message_id)
            except MessageModel.DoesNotExist:
                return {
                    'success': False,
                    'error': f'找不到 ID 為 {message_id} 的消息'
                }
            
            # 更新反饋
            message.is_helpful = is_helpful
            if feedback:
                message.feedback = feedback
            message.save()
            
            self.logger.info(f"消息 {message_id} 反饋已更新: is_helpful={is_helpful}")
            
            return {
                'success': True,
                'data': {
                    'message_id': message_id,
                    'is_helpful': is_helpful,
                    'feedback': feedback
                }
            }
            
        except Exception as e:
            self.logger.error(f"更新消息反饋失敗: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
