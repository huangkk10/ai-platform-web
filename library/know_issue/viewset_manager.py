"""
Know Issue ViewSet Manager - ViewSet 管理器
==========================================

統一管理 Know Issue ViewSet 相關的邏輯：
- 權限管理
- 查詢過濾
- 創建和更新處理
"""

import logging
from typing import Dict, Any, List
from rest_framework import status
from rest_framework.response import Response
from django.db import models
from .processors import KnowIssueProcessor

logger = logging.getLogger(__name__)


class KnowIssueViewSetManager:
    """Know Issue ViewSet 管理器 - 統一管理所有 ViewSet 相關邏輯"""
    
    def __init__(self):
        self.logger = logger
        self.processor = KnowIssueProcessor()
        
    def get_permissions_for_action(self, action: str, user) -> List:
        """
        根據操作類型決定權限
        
        Args:
            action: 操作類型
            user: 用戶對象
            
        Returns:
            List: 權限列表
        """
        try:
            from rest_framework import permissions
            
            # Know Issue 允許所有登入用戶訪問
            return [permissions.IsAuthenticated()]
            
        except Exception as e:
            self.logger.error(f"權限檢查失敗: {e}")
            return []
    
    def get_filtered_queryset(self, base_queryset, query_params: Dict[str, Any]):
        """
        根據查詢參數過濾資料
        
        Args:
            base_queryset: 基礎查詢集
            query_params: 查詢參數
            
        Returns:
            QuerySet: 過濾後的查詢集
        """
        try:
            queryset = base_queryset
            
            # 根據專案過濾
            project = query_params.get('project', None)
            if project:
                queryset = queryset.filter(project__icontains=project)
                
            # 根據狀態過濾
            status_param = query_params.get('status', None)
            if status_param:
                queryset = queryset.filter(status=status_param)
                
            # 根據問題類型過濾
            issue_type = query_params.get('issue_type', None)
            if issue_type:
                queryset = queryset.filter(issue_type=issue_type)
                
            # 根據關鍵字搜尋
            search = query_params.get('search', None)
            if search:
                queryset = queryset.filter(
                    models.Q(issue_id__icontains=search) |
                    models.Q(project__icontains=search) |
                    models.Q(error_message__icontains=search) |
                    models.Q(supplement__icontains=search)
                )
                
            self.logger.info(f"Know Issue 查詢過濾完成，結果數量: {queryset.count()}")
            return queryset.order_by('-updated_at')
            
        except Exception as e:
            self.logger.error(f"查詢過濾失敗: {e}")
            return base_queryset
    
    def handle_create(self, request, serializer) -> Response:
        """
        處理 Know Issue 創建
        
        Args:
            request: HTTP 請求
            serializer: 序列化器
            
        Returns:
            Response: DRF 回應
        """
        try:
            # 驗證資料
            is_valid, error_message = self.processor.validate_know_issue_data(request.data)
            if not is_valid:
                return Response(
                    {'error': error_message}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 處理圖片上傳
            uploaded_images = self.processor.process_image_uploads(request)
            
            # 驗證序列化器
            if not serializer.is_valid():
                return Response(
                    {'error': '資料驗證失敗', 'details': serializer.errors}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 保存實例，設置更新人員
            instance = serializer.save(updated_by=request.user)
            
            # 處理上傳的圖片
            if uploaded_images:
                success = self.processor.save_images_to_instance(instance, uploaded_images)
                if success:
                    instance.save()  # 再次保存以處理圖片
            
            # 格式化回應
            response_data = self.processor.format_know_issue_response(instance, 'create')
            
            self.logger.info(f"Know Issue 創建成功: {instance.id}")
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            self.logger.error(f"Know Issue 創建失敗: {str(e)}")
            return Response(
                {'error': f'創建失敗: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def handle_update(self, request, instance, serializer) -> Response:
        """
        處理 Know Issue 更新
        
        Args:
            request: HTTP 請求
            instance: Know Issue 實例
            serializer: 序列化器
            
        Returns:
            Response: DRF 回應
        """
        try:
            # 處理圖片上傳
            uploaded_images = self.processor.process_image_uploads(request)
            
            # 驗證序列化器
            if not serializer.is_valid():
                return Response(
                    {'error': '資料驗證失敗', 'details': serializer.errors}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 保存實例，設置更新人員
            updated_instance = serializer.save(updated_by=request.user)
            
            # 處理上傳的圖片
            if uploaded_images:
                success = self.processor.save_images_to_instance(updated_instance, uploaded_images)
                if success:
                    updated_instance.save()  # 再次保存以處理圖片
            
            # 格式化回應
            response_data = self.processor.format_know_issue_response(updated_instance, 'update')
            
            self.logger.info(f"Know Issue 更新成功: {updated_instance.id}")
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            self.logger.error(f"Know Issue 更新失敗: {str(e)}")
            return Response(
                {'error': f'更新失敗: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def perform_create(self, serializer, user):
        """執行創建操作"""
        try:
            return serializer.save(updated_by=user)
        except Exception as e:
            self.logger.error(f"Know Issue 執行創建失敗: {e}")
            raise
    
    def perform_update(self, serializer, user):
        """執行更新操作"""
        try:
            return serializer.save(updated_by=user)
        except Exception as e:
            self.logger.error(f"Know Issue 執行更新失敗: {e}")
            raise