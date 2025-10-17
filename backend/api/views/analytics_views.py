"""
Analytics API Views
管理所有分析相關的 API 端點

包含的 API：
- 對話管理: conversation_list, conversation_detail, record_conversation, 
             update_conversation_session, conversation_stats
- RVT Analytics: rvt_analytics_feedback, rvt_analytics_overview, 
                 rvt_analytics_questions, rvt_analytics_satisfaction
- 聊天向量化與聚類: chat_vector_search, chat_clustering_analysis, 
                    chat_clustering_stats, vectorize_chat_message, 
                    intelligent_question_classify
"""

import json
import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

# 設置日誌
logger = logging.getLogger(__name__)


# ============= 檢查 Library 可用性 =============

# Conversation Management Library
CONVERSATION_MANAGEMENT_AVAILABLE = False
ConversationAPIHandler = None

try:
    from library.conversation_management import (
        CONVERSATION_MANAGEMENT_AVAILABLE,
        ConversationAPIHandler
    )
except ImportError as e:
    logger.warning(f"⚠️  Conversation Management Library 無法載入: {str(e)}")


# RVT Analytics Library
RVT_ANALYTICS_AVAILABLE = False
RVTAnalyticsAPIHandler = None
handle_feedback_api = None

try:
    from library.rvt_analytics import (
        RVT_ANALYTICS_AVAILABLE,
        RVTAnalyticsAPIHandler,
        handle_feedback_api
    )
except ImportError as e:
    logger.warning(f"⚠️  RVT Analytics Library 無法載入: {str(e)}")


# Chat Vector Services
CHAT_VECTOR_SERVICES_AVAILABLE = False
search_similar_chat_messages = None
perform_auto_clustering = None
get_cluster_categories = None
get_chat_vector_service = None
generate_message_vector = None

try:
    from library.rvt_analytics.vector_services import (
        search_similar_chat_messages,
        perform_auto_clustering,
        get_cluster_categories,
        get_chat_vector_service,
        generate_message_vector
    )
    CHAT_VECTOR_SERVICES_AVAILABLE = True
except ImportError as e:
    logger.warning(f"⚠️  Chat Vector Services 無法載入: {str(e)}")


# ============= 對話管理 API =============

@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])  # 支援訪客
def conversation_list(request):
    """
    對話列表 API - 使用 Conversation Management Library
    GET /api/conversations/
    
    支援查詢參數:
    - page: 頁碼 (預設 1)
    - page_size: 每頁大小 (預設 20, 最大 100)
    - chat_type: 聊天類型篩選 (可選)
    """
    try:
        if CONVERSATION_MANAGEMENT_AVAILABLE and ConversationAPIHandler:
            return ConversationAPIHandler.handle_conversation_list_api(request)
        else:
            return Response({
                'success': False,
                'error': 'Conversation Management Library not available'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
    except Exception as e:
        logger.error(f"Conversation list API error: {str(e)}")
        return Response({
            'success': False,
            'error': f'對話列表獲取失敗: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])  # 支援訪客
def conversation_detail(request, conversation_id):
    """
    對話詳情 API - 使用 Conversation Management Library
    GET /api/conversations/{id}/
    
    支援查詢參數:
    - page: 頁碼 (預設 1)
    - page_size: 每頁大小 (預設 50, 最大 100)
    """
    try:
        if CONVERSATION_MANAGEMENT_AVAILABLE and ConversationAPIHandler:
            return ConversationAPIHandler.handle_conversation_detail_api(request, conversation_id)
        else:
            return Response({
                'success': False,
                'error': 'Conversation Management Library not available'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
    except Exception as e:
        logger.error(f"Conversation detail API error: {str(e)}")
        return Response({
            'success': False,
            'error': f'對話詳情獲取失敗: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])  # 支援訪客
def record_conversation(request):
    """
    記錄對話 API - 使用 Conversation Management Library
    POST /api/conversations/record/
    
    預期 payload:
    {
        "session_id": "dify_conv_12345",
        "user_message": "用戶問題",
        "assistant_message": "AI回覆",
        "response_time": 2.3,
        "token_usage": {"total_tokens": 150},
        "metadata": {}
    }
    """
    try:
        if CONVERSATION_MANAGEMENT_AVAILABLE and ConversationAPIHandler:
            return ConversationAPIHandler.handle_record_conversation_api(request)
        else:
            return Response({
                'success': False,
                'error': 'Conversation Management Library not available'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
    except Exception as e:
        logger.error(f"Record conversation API error: {str(e)}")
        return Response({
            'success': False,
            'error': f'對話記錄失敗: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['PATCH'])
@permission_classes([AllowAny])  # 支援訪客
def update_conversation_session(request, session_id):
    """
    更新會話 API - 使用 Conversation Management Library
    PATCH /api/conversations/sessions/{session_id}/
    
    預期 payload:
    {
        "title": "新標題"
    }
    """
    try:
        if CONVERSATION_MANAGEMENT_AVAILABLE and ConversationAPIHandler:
            return ConversationAPIHandler.handle_update_session_api(request, session_id)
        else:
            return Response({
                'success': False,
                'error': 'Conversation Management Library not available'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
    except Exception as e:
        logger.error(f"Update conversation session API error: {str(e)}")
        return Response({
            'success': False,
            'error': f'會話更新失敗: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])  # 支援訪客
def conversation_stats(request):
    """
    對話統計 API - 使用 Conversation Management Library
    GET /api/conversations/stats/
    """
    try:
        if CONVERSATION_MANAGEMENT_AVAILABLE and ConversationAPIHandler:
            return ConversationAPIHandler.handle_conversation_stats_api(request)
        else:
            return Response({
                'success': False,
                'error': 'Conversation Management Library not available'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
    except Exception as e:
        logger.error(f"Conversation stats API error: {str(e)}")
        return Response({
            'success': False,
            'error': f'對話統計獲取失敗: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============= RVT Analytics API =============

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])  # 支援訪客使用反饋功能
def rvt_analytics_feedback(request):
    """
    RVT Assistant 消息反饋 API - 使用 RVT Analytics Library
    POST /api/rvt-analytics/feedback/
    
    預期 payload:
    {
        "message_id": "uuid-string",
        "is_helpful": true/false
    }
    """
    try:
        if RVT_ANALYTICS_AVAILABLE and handle_feedback_api:
            return handle_feedback_api(request)
        else:
            # 使用備用實現
            logger.warning("RVT Analytics Library 不可用，使用備用反饋處理")
            try:
                data = json.loads(request.body)
                message_id = data.get('message_id')
                is_helpful = data.get('is_helpful')
                
                if message_id is None or is_helpful is None:
                    return JsonResponse({
                        'success': False,
                        'error': 'message_id 和 is_helpful 是必需的'
                    }, status=400)
                
                # 簡化的備用處理：直接更新資料庫
                from api.models import ChatMessage
                
                message = ChatMessage.objects.filter(id=message_id).first()
                if not message:
                    return JsonResponse({
                        'success': False,
                        'error': '消息不存在'
                    }, status=404)
                
                message.is_helpful = is_helpful
                message.save()
                
                return JsonResponse({
                    'success': True,
                    'fallback': True,
                    'data': {
                        'message_id': str(message_id),
                        'is_helpful': is_helpful
                    }
                }, status=200)
                
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'備用反饋處理失敗: {str(e)}'
                }, status=500)
            
    except Exception as e:
        logger.error(f"RVT Analytics feedback API error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'反饋提交失敗: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def rvt_analytics_overview(request):
    """
    RVT Analytics 概覽 API - 使用 RVT Analytics Library
    GET /api/rvt-analytics/overview/
    
    Query parameters:
    - days: 統計天數 (default: 30)
    - user_id: 特定用戶ID (admin only)
    """
    try:
        if RVT_ANALYTICS_AVAILABLE and RVTAnalyticsAPIHandler:
            return RVTAnalyticsAPIHandler.handle_analytics_overview_api(request)
        else:
            # 備用實現
            logger.warning("RVT Analytics Library 不可用，使用備用概覽實現")
            try:
                days = int(request.GET.get('days', 30))
                user_id = request.GET.get('user_id')
                
                # 權限檢查
                if user_id and not request.user.is_staff:
                    return JsonResponse({
                        'success': False,
                        'error': '無權限查看其他用戶數據'
                    }, status=403)
                
                # 簡化的統計
                from django.utils import timezone
                from datetime import timedelta
                from api.models import ConversationSession, ChatMessage
                
                start_date = timezone.now() - timedelta(days=days)
                
                # 基本統計
                total_conversations = ConversationSession.objects.filter(
                    created_at__gte=start_date
                ).count()
                
                total_messages = ChatMessage.objects.filter(
                    created_at__gte=start_date,
                    role='assistant'
                ).count()
                
                helpful_count = ChatMessage.objects.filter(
                    created_at__gte=start_date,
                    role='assistant',
                    is_helpful=True
                ).count()
                
                return JsonResponse({
                    'success': True,
                    'fallback': True,
                    'data': {
                        'period': f'{days} 天',
                        'overview': {
                            'total_conversations': total_conversations,
                            'total_messages': total_messages,
                            'helpful_messages': helpful_count
                        }
                    }
                }, status=200)
                
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'備用概覽處理失敗: {str(e)}'
                }, status=500)
            
    except Exception as e:
        logger.error(f"RVT Analytics overview API error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'概覽獲取失敗: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def rvt_analytics_questions(request):
    """
    RVT Analytics 問題分析 API - 使用 RVT Analytics Library
    GET /api/rvt-analytics/questions/
    
    Query parameters:
    - days: 統計天數 (default: 7)
    - category: 問題分類過濾
    """
    try:
        if RVT_ANALYTICS_AVAILABLE and RVTAnalyticsAPIHandler:
            return RVTAnalyticsAPIHandler.handle_question_analysis_api(request)
        else:
            # 備用實現
            logger.warning("RVT Analytics Library 不可用，使用備用問題分析實現")
            try:
                days = int(request.GET.get('days', 7))
                
                # 簡化的問題分析
                from django.utils import timezone
                from datetime import timedelta
                from api.models import ChatMessage
                from collections import Counter
                
                start_date = timezone.now() - timedelta(days=days)
                
                user_messages = ChatMessage.objects.filter(
                    role='user',
                    created_at__gte=start_date
                ).values_list('content', flat=True)
                
                # 簡單的關鍵字統計
                keywords = []
                for message in user_messages:
                    words = message.lower().split()
                    keywords.extend([w for w in words if len(w) > 3])
                
                keyword_counts = Counter(keywords).most_common(10)
                
                return JsonResponse({
                    'success': True,
                    'fallback': True,
                    'data': {
                        'total_questions': len(user_messages),
                        'top_keywords': keyword_counts,
                        'period': f'{days} 天'
                    }
                }, status=200)
                
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'備用問題分析失敗: {str(e)}'
                }, status=500)
            
    except Exception as e:
        logger.error(f"RVT Analytics questions API error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'問題分析失敗: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def rvt_analytics_satisfaction(request):
    """
    RVT Analytics 滿意度分析 API - 使用 RVT Analytics Library
    GET /api/rvt-analytics/satisfaction/
    
    Query parameters:
    - days: 統計天數 (default: 30)
    - detail: 是否包含詳細分析 (true/false)
    """
    try:
        if RVT_ANALYTICS_AVAILABLE and RVTAnalyticsAPIHandler:
            return RVTAnalyticsAPIHandler.handle_satisfaction_analysis_api(request)
        else:
            # 備用實現
            logger.warning("RVT Analytics Library 不可用，使用備用滿意度分析實現")
            try:
                days = int(request.GET.get('days', 30))
                
                # 簡化的滿意度分析
                from django.utils import timezone
                from datetime import timedelta
                from api.models import ChatMessage
                
                start_date = timezone.now() - timedelta(days=days)
                
                assistant_messages = ChatMessage.objects.filter(
                    role='assistant',
                    created_at__gte=start_date
                )
                
                total_messages = assistant_messages.count()
                helpful_messages = assistant_messages.filter(is_helpful=True).count()
                unhelpful_messages = assistant_messages.filter(is_helpful=False).count()
                
                satisfaction_rate = None
                if helpful_messages + unhelpful_messages > 0:
                    satisfaction_rate = helpful_messages / (helpful_messages + unhelpful_messages)
                
                return JsonResponse({
                    'success': True,
                    'fallback': True,
                    'data': {
                        'basic_stats': {
                            'total_messages': total_messages,
                            'helpful_count': helpful_messages,
                            'unhelpful_count': unhelpful_messages,
                            'satisfaction_rate': round(satisfaction_rate, 3) if satisfaction_rate else None
                        },
                        'analysis_period': f'{days} 天'
                    }
                }, status=200)
                
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'備用滿意度分析失敗: {str(e)}'
                }, status=500)
            
    except Exception as e:
        logger.error(f"RVT Analytics satisfaction API error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'滿意度分析失敗: {str(e)}'
        }, status=500)


# ============= 聊天向量化和聚類 API =============

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat_vector_search(request):
    """
    聊天消息向量相似度搜索 API
    POST /api/chat/vector-search/
    """
    try:
        if not CHAT_VECTOR_SERVICES_AVAILABLE:
            return JsonResponse({
                'success': False,
                'error': '聊天向量化服務不可用'
            }, status=503)
        
        data = json.loads(request.body)
        query = data.get('query', '').strip()
        limit = min(int(data.get('limit', 10)), 50)  # 最大限制50
        threshold = float(data.get('threshold', 0.7))
        
        if not query:
            return JsonResponse({
                'success': False,
                'error': '查詢文本不能為空'
            }, status=400)
        
        # 執行向量搜索
        results = search_similar_chat_messages(query, limit, threshold)
        
        return JsonResponse({
            'success': True,
            'data': {
                'query': query,
                'results': results,
                'total_found': len(results),
                'search_params': {
                    'limit': limit,
                    'threshold': threshold
                }
            }
        }, status=200)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': '無效的 JSON 數據'
        }, status=400)
    except Exception as e:
        logger.error(f"Chat vector search API error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'向量搜索失敗: {str(e)}'
        }, status=500)


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat_clustering_analysis(request):
    """
    聊天消息聚類分析 API
    POST /api/chat/clustering-analysis/
    """
    try:
        if not CHAT_VECTOR_SERVICES_AVAILABLE:
            return JsonResponse({
                'success': False,
                'error': '聊天聚類服務不可用'
            }, status=503)
        
        data = json.loads(request.body)
        algorithm = data.get('algorithm', 'kmeans').lower()
        
        if algorithm not in ['kmeans', 'dbscan']:
            return JsonResponse({
                'success': False,
                'error': f'不支援的聚類算法: {algorithm}'
            }, status=400)
        
        # 執行聚類分析
        results = perform_auto_clustering(algorithm)
        
        if 'error' in results:
            return JsonResponse({
                'success': False,
                'error': results['error']
            }, status=500)
        
        return JsonResponse({
            'success': True,
            'data': results
        }, status=200)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': '無效的 JSON 數據'
        }, status=400)
    except Exception as e:
        logger.error(f"Chat clustering analysis API error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'聚類分析失敗: {str(e)}'
        }, status=500)


@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chat_clustering_stats(request):
    """
    獲取聊天聚類統計 API
    GET /api/chat/clustering-stats/
    """
    try:
        if not CHAT_VECTOR_SERVICES_AVAILABLE:
            return JsonResponse({
                'success': False,
                'error': '聊天聚類服務不可用'
            }, status=503)
        
        # 獲取聚類統計
        cluster_categories = get_cluster_categories()
        
        # 獲取向量服務統計
        vector_service = get_chat_vector_service()
        embedding_stats = vector_service.get_embedding_stats()
        
        return JsonResponse({
            'success': True,
            'data': {
                'cluster_categories': cluster_categories,
                'embedding_stats': embedding_stats
            }
        }, status=200)
        
    except Exception as e:
        logger.error(f"Chat clustering stats API error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'獲取聚類統計失敗: {str(e)}'
        }, status=500)


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def vectorize_chat_message(request):
    """
    對單個聊天消息進行向量化 API
    POST /api/chat/vectorize-message/
    """
    try:
        if not CHAT_VECTOR_SERVICES_AVAILABLE:
            return JsonResponse({
                'success': False,
                'error': '聊天向量化服務不可用'
            }, status=503)
        
        data = json.loads(request.body)
        chat_message_id = data.get('chat_message_id')
        content = data.get('content', '').strip()
        conversation_id = data.get('conversation_id')
        
        if not chat_message_id:
            return JsonResponse({
                'success': False,
                'error': 'chat_message_id 是必需的'
            }, status=400)
        
        if not content:
            return JsonResponse({
                'success': False,
                'error': '消息內容不能為空'
            }, status=400)
        
        # 生成向量
        success = generate_message_vector(chat_message_id, content, conversation_id)
        
        if success:
            # 嘗試分類
            from library.rvt_analytics.question_classifier import classify_question
            classification = classify_question(
                content, 
                chat_message_id=chat_message_id, 
                use_vector_classification=True
            )
            
            return JsonResponse({
                'success': True,
                'data': {
                    'chat_message_id': chat_message_id,
                    'vectorized': True,
                    'classification': classification
                }
            }, status=200)
        else:
            return JsonResponse({
                'success': False,
                'error': '向量化處理失敗'
            }, status=500)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': '無效的 JSON 數據'
        }, status=400)
    except Exception as e:
        logger.error(f"Vectorize chat message API error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'向量化失敗: {str(e)}'
        }, status=500)


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def intelligent_question_classify(request):
    """
    智能問題分類 API（整合向量聚類）
    POST /api/chat/intelligent-classify/
    """
    try:
        data = json.loads(request.body)
        question_text = data.get('question', '').strip()
        chat_message_id = data.get('chat_message_id')
        use_vector_classification = data.get('use_vector_classification', True)
        use_ai_classification = data.get('use_ai_classification', False)
        
        if not question_text:
            return JsonResponse({
                'success': False,
                'error': '問題文本不能為空'
            }, status=400)
        
        # 執行智能分類
        from library.rvt_analytics.question_classifier import classify_question
        
        classification_result = classify_question(
            question_text=question_text,
            chat_message_id=chat_message_id,
            use_vector_classification=use_vector_classification,
            use_ai_classification=use_ai_classification
        )
        
        # 如果啟用向量分類，也提供相似問題
        similar_questions = []
        if use_vector_classification and CHAT_VECTOR_SERVICES_AVAILABLE:
            similar_questions = search_similar_chat_messages(
                question_text, 
                limit=5, 
                threshold=0.6
            )
        
        return JsonResponse({
            'success': True,
            'data': {
                'classification': classification_result,
                'similar_questions': similar_questions
            }
        }, status=200)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': '無效的 JSON 數據'
        }, status=400)
    except Exception as e:
        logger.error(f"Intelligent question classify API error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'智能分類失敗: {str(e)}'
        }, status=500)
