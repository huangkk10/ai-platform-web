"""
AI OCR 查詢集管理器

提供 OCRStorageBenchmark 查詢邏輯的統一實現，
包括基本查詢、高級過濾、搜尋等功能。

此模組將 views.py 中的備用查詢邏輯重構為可重用的類。
"""

import logging
from datetime import datetime
from django.db import models
from django.db.models import Q

logger = logging.getLogger(__name__)


class OCRStorageBenchmarkQueryManager:
    """OCR Storage Benchmark 查詢管理器"""
    
    def __init__(self):
        """初始化查詢管理器"""
        self.logger = logger
        
    def get_filtered_queryset(self, base_queryset, query_params):
        """
        對 OCRStorageBenchmark 查詢集進行過濾和搜尋
        
        Args:
            base_queryset: 基礎查詢集
            query_params: Django request.query_params 對象
            
        Returns:
            經過過濾的查詢集
        """
        try:
            # 優化查詢性能
            queryset = base_queryset.select_related('test_class', 'uploaded_by')
            
            # 應用各種過濾器
            queryset = self._apply_basic_filters(queryset, query_params)
            queryset = self._apply_score_filters(queryset, query_params)
            queryset = self._apply_date_filters(queryset, query_params)
            queryset = self._apply_search_filters(queryset, query_params)
            
            # 排序
            return queryset.order_by('-test_datetime', '-created_at')
            
        except Exception as e:
            self.logger.error(f"OCR Storage Benchmark 查詢過濾失敗: {str(e)}")
            # 返回基礎查詢集，避免完全失敗
            return base_queryset.order_by('-test_datetime', '-created_at')
    
    def _apply_basic_filters(self, queryset, query_params):
        """應用基本過濾器"""
        # 專案名稱過濾
        project_name = query_params.get('project_name', None)
        if project_name:
            queryset = queryset.filter(project_name__icontains=project_name)
        
        # 裝置型號過濾
        device_model = query_params.get('device_model', None)
        if device_model:
            queryset = queryset.filter(device_model__icontains=device_model)
        
        # 韌體版本過濾
        firmware_version = query_params.get('firmware_version', None)
        if firmware_version:
            queryset = queryset.filter(firmware_version__icontains=firmware_version)
        
        # 測試類別過濾
        test_class_id = query_params.get('test_class', None)
        if test_class_id:
            try:
                queryset = queryset.filter(test_class_id=int(test_class_id))
            except (ValueError, TypeError):
                self.logger.warning(f"無效的測試類別 ID: {test_class_id}")
        
        return queryset
    
    def _apply_score_filters(self, queryset, query_params):
        """應用分數範圍過濾器"""
        # 最小分數過濾
        min_score = query_params.get('min_score', None)
        if min_score:
            try:
                min_score_val = int(min_score)
                queryset = queryset.filter(benchmark_score__gte=min_score_val)
            except (ValueError, TypeError):
                self.logger.warning(f"無效的最小分數: {min_score}")
        
        # 最大分數過濾
        max_score = query_params.get('max_score', None)
        if max_score:
            try:
                max_score_val = int(max_score)
                queryset = queryset.filter(benchmark_score__lte=max_score_val)
            except (ValueError, TypeError):
                self.logger.warning(f"無效的最大分數: {max_score}")
        
        return queryset
    
    def _apply_date_filters(self, queryset, query_params):
        """應用日期範圍過濾器"""
        # 開始日期過濾
        start_date = query_params.get('start_date', None)
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                queryset = queryset.filter(test_datetime__gte=start_datetime)
            except (ValueError, TypeError) as e:
                self.logger.warning(f"無效的開始日期: {start_date}, 錯誤: {str(e)}")
        
        # 結束日期過濾
        end_date = query_params.get('end_date', None)
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                queryset = queryset.filter(test_datetime__lte=end_datetime)
            except (ValueError, TypeError) as e:
                self.logger.warning(f"無效的結束日期: {end_date}, 錯誤: {str(e)}")
        
        return queryset
    
    def _apply_search_filters(self, queryset, query_params):
        """應用搜尋過濾器"""
        search = query_params.get('search', None)
        if search:
            # 支援多欄位搜尋
            search_q = Q(project_name__icontains=search) | \
                      Q(device_model__icontains=search) | \
                      Q(firmware_version__icontains=search) | \
                      Q(ocr_raw_text__icontains=search)
            
            queryset = queryset.filter(search_q)
        
        return queryset
    
    def get_statistics_data(self, queryset):
        """
        獲取查詢集的統計數據
        
        Args:
            queryset: 要統計的查詢集
            
        Returns:
            包含統計數據的字典
        """
        try:
            from django.db.models import Count, Avg, Max, Min
            
            # 基本統計
            total_records = queryset.count()
            
            # 測試類別分佈
            test_class_stats = queryset.values('test_class__name').annotate(count=Count('id'))
            
            # 分數統計
            score_stats = queryset.aggregate(
                avg_score=Avg('benchmark_score'),
                max_score=Max('benchmark_score'),
                min_score=Min('benchmark_score')
            )
            
            # 韌體版本分佈
            firmware_stats = queryset.values('firmware_version').annotate(count=Count('id'))
            
            # 專案分佈
            project_stats = queryset.values('project_name').annotate(count=Count('id'))
            
            # 裝置型號分佈 (前10名)
            device_stats = queryset.values('device_model').annotate(count=Count('id')).order_by('-count')[:10]
            
            return {
                'total_records': total_records,
                'test_class_distribution': list(test_class_stats),
                'score_statistics': score_stats,
                'firmware_distribution': list(firmware_stats),
                'project_distribution': list(project_stats),
                'top_devices': list(device_stats)
            }
            
        except Exception as e:
            self.logger.error(f"統計數據獲取失敗: {str(e)}")
            return {
                'error': f'統計數據獲取失敗: {str(e)}'
            }


# 便利函數，用於快速創建查詢管理器
def create_ocr_queryset_manager():
    """創建 OCR Storage Benchmark 查詢管理器實例"""
    return OCRStorageBenchmarkQueryManager()


# 備用函數，用於直接處理查詢集過濾
def fallback_ocr_storage_benchmark_queryset_filter(base_queryset, query_params):
    """
    備用的 OCR Storage Benchmark 查詢集過濾函數
    
    當 OCRStorageBenchmarkQueryManager 不可用時使用
    
    Args:
        base_queryset: 基礎查詢集
        query_params: 查詢參數
        
    Returns:
        過濾後的查詢集
    """
    try:
        manager = create_ocr_queryset_manager()
        return manager.get_filtered_queryset(base_queryset, query_params)
    except Exception as e:
        logger.error(f"備用查詢集過濾失敗: {str(e)}")
        # 最簡單的備用實現
        search = query_params.get('search', None)
        if search:
            base_queryset = base_queryset.filter(
                Q(project_name__icontains=search) |
                Q(device_model__icontains=search)
            )
        return base_queryset.order_by('-test_datetime', '-created_at')