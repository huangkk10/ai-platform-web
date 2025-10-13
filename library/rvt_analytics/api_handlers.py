"""
API Handlers - RVT Analytics API 處理器

此模組負責：
- 處理反饋評分 API 請求
- 處理分析統計 API 請求
- 統一錯誤處理和回應格式
- API 認證和權限控制
"""

import logging
import json
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.utils import timezone
from datetime import timedelta
from collections import Counter

logger = logging.getLogger(__name__)

def get_smart_analysis(days=7):
    """
    智慧分析模式：自動判斷是否需要獨立顯示高頻問題
    
    Args:
        days: 分析天數
        
    Returns:
        Dict: 智慧選擇的分析結果
    """
    try:
        # 先獲取原始頻率和聚類結果
        freq_analysis = get_raw_frequency_analysis(days)
        from .statistics_manager import get_rvt_analytics_stats
        cluster_stats = get_rvt_analytics_stats(days=days)
        cluster_analysis = cluster_stats.get('question_analysis', {})
        
        # 檢查是否有高頻問題被聚類掩蓋
        freq_top = freq_analysis.get('popular_questions', [])[:10]
        cluster_top = cluster_analysis.get('popular_questions', [])[:10]
        
        # 計算差異度
        major_discrepancies = []
        for freq_q in freq_top:
            freq_count = freq_q['count']
            freq_pattern = freq_q['pattern'].lower()
            
            # 在聚類結果中尋找對應問題
            found_in_cluster = False
            for cluster_q in cluster_top:
                cluster_examples = [str(ex).lower() for ex in cluster_q.get('examples', [])]
                if any(freq_pattern in ex or ex in freq_pattern for ex in cluster_examples):
                    cluster_count = cluster_q['count']
                    if freq_count > cluster_count * 2:  # 如果頻率差異超過2倍
                        major_discrepancies.append({
                            'original_question': freq_q['pattern'],
                            'original_count': freq_count,
                            'cluster_pattern': cluster_q['pattern'],
                            'cluster_count': cluster_count,
                            'severity': freq_count / max(cluster_count, 1)
                        })
                    found_in_cluster = True
                    break
        
        # 決策邏輯
        if len(major_discrepancies) >= 2:  # 如果有2個以上嚴重差異
            result = freq_analysis.copy()
            result['analysis_method'] = 'smart_frequency'
            result['reason'] = f'檢測到{len(major_discrepancies)}個高頻問題被聚類掩蓋，使用頻率模式'
            result['discrepancies'] = major_discrepancies
            return result
        else:
            result = cluster_analysis.copy()
            result['analysis_method'] = 'smart_clustered'
            result['reason'] = '未發現重大聚類問題，使用聚類模式'
            return result
            
    except Exception as e:
        # 出錯時回退到頻率模式
        return get_raw_frequency_analysis(days)

def get_raw_frequency_analysis(days=7):
    """
    獲取原始問題頻率分析（不經過聚類）
    
    Args:
        days: 分析天數
        
    Returns:
        Dict: 包含熱門問題的原始頻率統計
    """
    try:
        from api.models import ChatMessage
        
        # 獲取指定天數內的用戶問題
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        recent_messages = ChatMessage.objects.filter(
            role='user',
            created_at__gte=start_date
        )
        
        # 統計問題頻率
        question_counts = Counter(recent_messages.values_list('content', flat=True))
        
        # 生成熱門問題列表
        popular_questions = []
        for i, (question, count) in enumerate(question_counts.most_common(20)):
            popular_questions.append({
                'rank': i + 1,
                'question': question,
                'pattern': question,  # 在頻率模式下，問題就是模式
                'count': count,
                'is_vector_based': False,  # 標記為非向量分析
                'analysis_mode': 'frequency',  # 分析模式標記
                'examples': [question]  # 例子就是問題本身
            })
        
        # 統計總問題數和分類
        total_questions = recent_messages.count()
        
        # 簡單的關鍵詞分類
        category_distribution = {}
        for question, count in question_counts.items():
            if 'ucc' in question.lower():
                category = 'UCC相關'
            elif 'rvt' in question.lower():
                category = 'RVT相關'
            elif 'hello' in question.lower() or 'hi' in question.lower():
                category = '問候語'
            elif any(keyword in question.lower() for keyword in ['error', 'fail', 'exception']):
                category = '錯誤問題'
            else:
                category = '其他'
                
            category_distribution[category] = category_distribution.get(category, 0) + count
        
        return {
            'total_questions': total_questions,
            'popular_questions': popular_questions,
            'category_distribution': category_distribution,
            'analysis_method': 'raw_frequency',
            'is_vector_enhanced': False,
            'period': f'最近{days}天'
        }
        
    except Exception as e:
        logger.error(f"Raw frequency analysis error: {str(e)}")
        return {
            'total_questions': 0,
            'popular_questions': [],
            'category_distribution': {},
            'error': str(e)
        }

class RVTAnalyticsAPIHandler:
    """RVT Analytics API 處理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @staticmethod
    def handle_message_feedback_api(request):
        """
        處理消息反饋 API
        POST /api/rvt-analytics/feedback/
        
        Expected payload:
        {
            "message_id": "uuid-string",
            "is_helpful": true/false
        }
        """
        try:
            if request.method != 'POST':
                return JsonResponse({
                    'success': False,
                    'error': 'Only POST method allowed'
                }, status=405)
            
            # 解析請求數據
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid JSON format'
                }, status=400)
            
            message_id = data.get('message_id')
            is_helpful = data.get('is_helpful')
            
            # 參數驗證
            if not message_id:
                return JsonResponse({
                    'success': False,
                    'error': 'message_id is required'
                }, status=400)
            
            if is_helpful is None:
                return JsonResponse({
                    'success': False,
                    'error': 'is_helpful is required (true/false)'
                }, status=400)
            
            if not isinstance(is_helpful, bool):
                return JsonResponse({
                    'success': False,
                    'error': 'is_helpful must be boolean (true/false)'
                }, status=400)
            
            # 獲取用戶信息
            user = None
            guest_identifier = None
            
            if request.user.is_authenticated:
                user = request.user
            else:
                # 對於訪客，使用 session key 作為識別碼
                guest_identifier = request.session.session_key
                if not guest_identifier:
                    # 如果沒有 session，創建一個
                    request.session.create()
                    guest_identifier = request.session.session_key
            
            # 記錄反饋
            from .message_feedback import record_message_feedback
            result = record_message_feedback(
                message_id=message_id,
                is_helpful=is_helpful,
                user=user,
                guest_identifier=guest_identifier
            )
            
            if result['success']:
                return JsonResponse({
                    'success': True,
                    'message': '反饋已記錄',
                    'data': {
                        'message_id': result['message_id'],
                        'is_helpful': result['is_helpful'],
                        'user_type': 'registered' if user else 'guest',
                        'updated_at': result['updated_at']
                    }
                }, status=200)
            else:
                return JsonResponse({
                    'success': False,
                    'error': result['error']
                }, status=400)
                
        except Exception as e:
            logger.error(f"Message feedback API error: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': f'服務器錯誤: {str(e)}'
            }, status=500)
    
    @staticmethod
    def handle_analytics_overview_api(request):
        """
        處理分析概覽 API
        GET /api/rvt-analytics/overview/
        
        Query parameters:
        - days: 統計天數 (default: 30)
        - user_id: 特定用戶ID (admin only)
        """
        try:
            if request.method != 'GET':
                return JsonResponse({
                    'success': False,
                    'error': 'Only GET method allowed'
                }, status=405)
            
            # 獲取查詢參數
            days = int(request.GET.get('days', 30))
            user_id = request.GET.get('user_id')
            
            # 參數驗證
            if days < 1 or days > 365:
                return JsonResponse({
                    'success': False,
                    'error': 'days must be between 1 and 365'
                }, status=400)
            
            # 權限檢查
            target_user = None
            if user_id:
                if not request.user.is_staff:
                    return JsonResponse({
                        'success': False,
                        'error': '無權限查看其他用戶數據'
                    }, status=403)
                
                try:
                    from django.contrib.auth.models import User
                    target_user = User.objects.get(id=user_id)
                except User.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': '用戶不存在'
                    }, status=404)
            elif not request.user.is_staff:
                # 非管理員只能查看自己的數據
                target_user = request.user if request.user.is_authenticated else None
            
            # 獲取統計數據
            from .statistics_manager import get_rvt_analytics_stats
            stats = get_rvt_analytics_stats(days=days, user=target_user)
            
            return JsonResponse({
                'success': True,
                'data': stats
            }, status=200)
            
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid days parameter'
            }, status=400)
        except Exception as e:
            logger.error(f"Analytics overview API error: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': f'服務器錯誤: {str(e)}'
            }, status=500)
    
    @staticmethod
    def handle_question_analysis_api(request):
        """
        處理問題分析 API
        GET /api/rvt-analytics/questions/
        
        Query parameters:
        - days: 統計天數 (default: 7)
        - category: 問題分類過濾
        - mode: 分析模式 (clustered/frequency) - 新增參數
        """
        try:
            if request.method != 'GET':
                return JsonResponse({
                    'success': False,
                    'error': 'Only GET method allowed'
                }, status=405)
            
            days = int(request.GET.get('days', 7))
            category_filter = request.GET.get('category')
            analysis_mode = request.GET.get('mode', 'clustered')  # 新增模式參數
            
            # 權限檢查
            if not request.user.is_staff:
                return JsonResponse({
                    'success': False,
                    'error': '此功能僅限管理員使用'
                }, status=403)
            
            # 根據模式選擇不同的分析方法
            if analysis_mode == 'frequency':
                # 使用原始頻率分析
                question_analysis = get_raw_frequency_analysis(days=days)
            elif analysis_mode == 'smart':
                # 使用智慧分析（自動選擇最佳模式）
                question_analysis = get_smart_analysis(days=days)
            else:
                # 使用聚類分析（默認）
                from .statistics_manager import get_rvt_analytics_stats
                stats = get_rvt_analytics_stats(days=days)
                question_analysis = stats.get('question_analysis', {})
            
            # 如果有分類過濾
            if category_filter and 'category_distribution' in question_analysis:
                filtered_data = {
                    k: v for k, v in question_analysis['category_distribution'].items()
                    if category_filter.lower() in k.lower()
                }
                question_analysis['filtered_category_distribution'] = filtered_data
            
            return JsonResponse({
                'success': True,
                'data': question_analysis
            }, status=200)
            
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid days parameter'
            }, status=400)
        except Exception as e:
            logger.error(f"Question analysis API error: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': f'服務器錯誤: {str(e)}'
            }, status=500)
    
    @staticmethod
    def handle_satisfaction_analysis_api(request):
        """
        處理滿意度分析 API
        GET /api/rvt-analytics/satisfaction/
        
        Query parameters:
        - days: 統計天數 (default: 30)
        - detail: 是否包含詳細分析 (true/false)
        """
        try:
            if request.method != 'GET':
                return JsonResponse({
                    'success': False,
                    'error': 'Only GET method allowed'
                }, status=405)
            
            days = int(request.GET.get('days', 30))
            include_detail = request.GET.get('detail', 'false').lower() == 'true'
            
            # 權限檢查
            if not request.user.is_staff:
                return JsonResponse({
                    'success': False,
                    'error': '此功能僅限管理員使用'
                }, status=403)
            
            # 獲取滿意度分析
            from .satisfaction_analyzer import analyze_user_satisfaction
            satisfaction_data = analyze_user_satisfaction(days=days)
            
            # 如果不需要詳細信息，只返回基礎統計
            if not include_detail:
                basic_stats = satisfaction_data.get('basic_stats', {})
                return JsonResponse({
                    'success': True,
                    'data': {
                        'basic_stats': basic_stats,
                        'analysis_period': satisfaction_data.get('analysis_period')
                    }
                }, status=200)
            
            return JsonResponse({
                'success': True,
                'data': satisfaction_data
            }, status=200)
            
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid days parameter'
            }, status=400)
        except Exception as e:
            logger.error(f"Satisfaction analysis API error: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': f'服務器錯誤: {str(e)}'
            }, status=500)

# 便利函數
def handle_feedback_api(request):
    """處理反饋 API 便利函數"""
    return RVTAnalyticsAPIHandler.handle_message_feedback_api(request)

def handle_analytics_api(request):
    """處理分析 API 便利函數"""
    # 根據 URL 路徑決定調用哪個處理器
    path = request.path
    
    if 'overview' in path:
        return RVTAnalyticsAPIHandler.handle_analytics_overview_api(request)
    elif 'questions' in path:
        return RVTAnalyticsAPIHandler.handle_question_analysis_api(request)
    elif 'satisfaction' in path:
        return RVTAnalyticsAPIHandler.handle_satisfaction_analysis_api(request)
    else:
        return JsonResponse({
            'success': False,
            'error': 'Unknown analytics endpoint'
        }, status=404)

# DRF 視圖函數裝飾器版本
@api_view(['POST'])
@permission_classes([])  # 允許訪客使用反饋功能
def message_feedback_api_view(request):
    """消息反饋 API 視圖"""
    return handle_feedback_api(request)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analytics_overview_api_view(request):
    """分析概覽 API 視圖"""
    return RVTAnalyticsAPIHandler.handle_analytics_overview_api(request)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def question_analysis_api_view(request):
    """問題分析 API 視圖"""
    return RVTAnalyticsAPIHandler.handle_question_analysis_api(request)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def satisfaction_analysis_api_view(request):
    """滿意度分析 API 視圖"""
    return RVTAnalyticsAPIHandler.handle_satisfaction_analysis_api(request)