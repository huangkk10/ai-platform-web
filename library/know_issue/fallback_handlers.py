"""
Know Issue 備用處理器

提供 Know Issue 功能的備用實現：
- 簡化版 ViewSet 管理
- 基本的 API 處理
- 緊急備用函數

當主要的 Know Issue library 不可用時使用
"""

import logging
import json
from typing import Dict, Any, Optional
from rest_framework import status
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class FallbackKnowIssueProcessor:
    """備用 Know Issue 處理器"""
    
    def __init__(self):
        self.logger = logger
    
    def simple_process_images(self, request) -> Dict[int, Dict[str, Any]]:
        """簡化的圖片處理"""
        try:
            uploaded_images = {}
            for i in range(1, 6):  # image1 到 image5
                image_field = f'image{i}'
                if image_field in request.FILES:
                    image_file = request.FILES[image_field]
                    uploaded_images[i] = {
                        'data': image_file.read(),
                        'filename': image_file.name,
                        'content_type': image_file.content_type
                    }
            return uploaded_images
        except Exception as e:
            self.logger.error(f"備用圖片處理失敗: {e}")
            return {}
    
    def simple_save_images(self, instance, uploaded_images: Dict[int, Dict[str, Any]]) -> bool:
        """簡化的圖片保存"""
        try:
            for image_index, image_data in uploaded_images.items():
                if hasattr(instance, 'set_image_data'):
                    instance.set_image_data(
                        image_index,
                        image_data['data'],
                        image_data['filename'],
                        image_data['content_type']
                    )
            return True
        except Exception as e:
            self.logger.error(f"備用圖片保存失敗: {e}")
            return False


def fallback_know_issue_create(request, serializer) -> Response:
    """
    備用的 Know Issue 創建處理
    
    Args:
        request: HTTP 請求
        serializer: 序列化器
        
    Returns:
        Response: DRF 回應
    """
    try:
        processor = FallbackKnowIssueProcessor()
        
        # 處理圖片上傳
        uploaded_images = processor.simple_process_images(request)
        
        # 驗證序列化器
        if serializer.is_valid():
            # 保存實例
            instance = serializer.save(updated_by=request.user)
            
            # 處理圖片（如果有）
            if uploaded_images:
                processor.simple_save_images(instance, uploaded_images)
                instance.save()
            
            # 簡單回應
            return Response({
                'id': instance.id,
                'message': 'Know Issue 創建成功（備用模式）',
                'note': '使用備用處理器，某些功能可能受限'
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'error': '資料驗證失敗',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"備用 Know Issue 創建失敗: {e}")
        return Response({
            'error': f'Know Issue 創建失敗: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def fallback_know_issue_update(request, instance, serializer) -> Response:
    """
    備用的 Know Issue 更新處理
    
    Args:
        request: HTTP 請求
        instance: Know Issue 實例
        serializer: 序列化器
        
    Returns:
        Response: DRF 回應
    """
    try:
        processor = FallbackKnowIssueProcessor()
        
        # 處理圖片上傳
        uploaded_images = processor.simple_process_images(request)
        
        # 驗證序列化器
        if serializer.is_valid():
            # 保存實例
            updated_instance = serializer.save(updated_by=request.user)
            
            # 處理圖片（如果有）
            if uploaded_images:
                processor.simple_save_images(updated_instance, uploaded_images)
                updated_instance.save()
            
            # 簡單回應
            return Response({
                'id': updated_instance.id,
                'message': 'Know Issue 更新成功（備用模式）',
                'note': '使用備用處理器，某些功能可能受限'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': '資料驗證失敗',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"備用 Know Issue 更新失敗: {e}")
        return Response({
            'error': f'Know Issue 更新失敗: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def fallback_dify_know_issue_search(request) -> Response:
    """
    備用的 Dify Know Issue 搜索 API
    
    Args:
        request: HTTP 請求
        
    Returns:
        Response: DRF 回應
    """
    try:
        # 解析請求數據
        data = json.loads(request.body) if request.body else {}
        query = data.get('query', '')
        
        logger.info(f"備用 Know Issue 搜索: {query}")
        
        # 驗證必要參數
        if not query:
            return Response({
                'error_code': 2001,
                'error_msg': 'Query parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 備用搜索 - 返回空結果但符合格式
        response_data = {
            'records': [],
            'message': '使用備用搜索服務，結果可能不完整',
            'note': 'Know Issue 主搜索服務不可用'
        }
        
        logger.info("備用 Know Issue 搜索完成")
        return Response(response_data, status=status.HTTP_200_OK)
        
    except json.JSONDecodeError:
        return Response({
            'error_code': 1001,
            'error_msg': 'Invalid JSON format'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"備用 Dify Know Issue 搜索錯誤: {str(e)}")
        return Response({
            'error_code': 2001,
            'error_msg': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def fallback_know_issue_queryset_filter(base_queryset, query_params):
    """
    備用的查詢過濾
    
    Args:
        base_queryset: 基礎查詢集
        query_params: 查詢參數
        
    Returns:
        QuerySet: 過濾後的查詢集
    """
    try:
        from django.db import models
        
        queryset = base_queryset
        
        # 簡化的過濾邏輯
        search = query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                models.Q(project__icontains=search) |
                models.Q(error_message__icontains=search)
            )
        
        project = query_params.get('project', None)
        if project:
            queryset = queryset.filter(project__icontains=project)
            
        status_param = query_params.get('status', None)
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        return queryset.order_by('-updated_at')
        
    except Exception as e:
        logger.error(f"備用查詢過濾失敗: {e}")
        return base_queryset