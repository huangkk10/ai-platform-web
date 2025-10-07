"""
AI OCR 統計功能管理器

統一管理所有 OCR 相關的統計資料生成和分析：
- OCRStorageBenchmark 統計分析
- 測試類別分布統計
- 效能指標統計
- 裝置型號分析

減少 ViewSet 中的統計邏輯複雜度，提供可重用的統計組件
"""

import logging
from django.db.models import Count, Avg, Max, Min
from rest_framework import status
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class OCRStatisticsManager:
    """OCR 統計資料管理器"""
    
    def __init__(self):
        self.logger = logger
        
    def get_ocr_storage_benchmark_statistics(self, queryset):
        """
        獲取 OCR Storage Benchmark 統計資料
        
        Args:
            queryset: OCRStorageBenchmark 查詢集
            
        Returns:
            Response: 包含統計資料的 DRF Response
        """
        try:
            # 基本統計
            total_records = queryset.count()
            
            # 按測試類別統計
            test_class_stats = queryset.values('test_class__name').annotate(count=Count('id'))
            
            # 分數統計
            score_stats = queryset.aggregate(
                avg_score=Avg('benchmark_score'),
                max_score=Max('benchmark_score'),
                min_score=Min('benchmark_score')
            )
            
            # 按韌體版本統計
            firmware_stats = queryset.values('firmware_version').annotate(count=Count('id'))
            
            # 按專案名稱統計
            project_stats = queryset.values('project_name').annotate(count=Count('id'))
            
            # 按裝置型號統計 (前10名)
            device_stats = queryset.values('device_model').annotate(count=Count('id')).order_by('-count')[:10]
            
            # 效能等級分析
            performance_grade_stats = self._analyze_performance_grades(queryset)
            
            # 時間趨勢分析（按月統計）
            time_trend_stats = self._analyze_time_trends(queryset)
            
            self.logger.info(f"OCR Storage Benchmark 統計資料生成成功: {total_records} 記錄")
            
            return Response({
                'success': True,
                'total_records': total_records,
                'test_class_distribution': list(test_class_stats),
                'score_statistics': score_stats,
                'firmware_distribution': list(firmware_stats),
                'project_distribution': list(project_stats),
                'top_devices': list(device_stats),
                'performance_grades': performance_grade_stats,
                'time_trends': time_trend_stats,
                'generated_at': self._get_current_timestamp()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            self.logger.error(f"OCR Storage Benchmark 統計資料獲取失敗: {str(e)}")
            return Response({
                'success': False,
                'error': f'統計資料獲取失敗: {str(e)}',
                'error_type': 'statistics_generation_error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _analyze_performance_grades(self, queryset):
        """分析效能等級分布"""
        try:
            # 根據基準分數分類效能等級
            excellent_count = queryset.filter(benchmark_score__gte=8000).count()
            good_count = queryset.filter(benchmark_score__gte=6000, benchmark_score__lt=8000).count()
            average_count = queryset.filter(benchmark_score__gte=4000, benchmark_score__lt=6000).count()
            poor_count = queryset.filter(benchmark_score__lt=4000).count()
            
            return {
                'excellent': {'count': excellent_count, 'label': '優秀 (≥8000分)'},
                'good': {'count': good_count, 'label': '良好 (6000-7999分)'},
                'average': {'count': average_count, 'label': '普通 (4000-5999分)'},
                'poor': {'count': poor_count, 'label': '待改善 (<4000分)'}
            }
        except Exception as e:
            self.logger.error(f"效能等級分析失敗: {str(e)}")
            return {}
    
    def _analyze_time_trends(self, queryset):
        """分析時間趨勢"""
        try:
            from django.db.models import TruncMonth
            from django.utils import timezone
            import datetime
            
            # 最近 6 個月的趨勢分析
            six_months_ago = timezone.now() - datetime.timedelta(days=180)
            
            monthly_stats = queryset.filter(
                test_datetime__gte=six_months_ago
            ).annotate(
                month=TruncMonth('test_datetime')
            ).values('month').annotate(
                count=Count('id'),
                avg_score=Avg('benchmark_score')
            ).order_by('month')
            
            # 格式化結果
            formatted_trends = []
            for stat in monthly_stats:
                if stat['month']:  # 確保 month 不是 None
                    formatted_trends.append({
                        'month': stat['month'].strftime('%Y-%m'),
                        'count': stat['count'],
                        'average_score': round(stat['avg_score'], 2) if stat['avg_score'] else 0
                    })
            
            return formatted_trends
            
        except Exception as e:
            self.logger.error(f"時間趨勢分析失敗: {str(e)}")
            return []
    
    def _get_current_timestamp(self):
        """獲取當前時間戳"""
        try:
            from django.utils import timezone
            return timezone.now().isoformat()
        except Exception:
            import datetime
            return datetime.datetime.now().isoformat()
    
    def get_basic_statistics(self, queryset):
        """
        獲取基本統計資料（簡化版）
        
        Args:
            queryset: OCRStorageBenchmark 查詢集
            
        Returns:
            dict: 基本統計資料
        """
        try:
            total_records = queryset.count()
            
            if total_records == 0:
                return {
                    'total_records': 0,
                    'message': '沒有找到任何記錄'
                }
            
            # 基本分數統計
            score_stats = queryset.aggregate(
                avg_score=Avg('benchmark_score'),
                max_score=Max('benchmark_score'),
                min_score=Min('benchmark_score')
            )
            
            # 最新 5 筆記錄
            latest_records = list(queryset.order_by('-test_datetime', '-created_at')[:5].values(
                'project_name', 'device_model', 'benchmark_score', 'test_datetime'
            ))
            
            return {
                'total_records': total_records,
                'score_statistics': score_stats,
                'latest_records': latest_records,
                'status': 'success'
            }
            
        except Exception as e:
            self.logger.error(f"基本統計資料獲取失敗: {str(e)}")
            return {
                'error': f'基本統計資料獲取失敗: {str(e)}',
                'status': 'error'
            }


class OCRStatisticsFallbackManager:
    """OCR 統計功能備用管理器"""
    
    @staticmethod
    def get_fallback_statistics(queryset):
        """
        備用統計實現 - 當主要統計管理器不可用時使用
        
        Args:
            queryset: OCRStorageBenchmark 查詢集
            
        Returns:
            Response: 包含基本統計資料的 DRF Response
        """
        try:
            logger.warning("使用 OCR 統計備用實現")
            
            total_records = queryset.count()
            
            # 最基本的統計
            if total_records > 0:
                # 使用 Python 聚合（避免複雜查詢）
                scores = list(queryset.values_list('benchmark_score', flat=True))
                avg_score = sum(scores) / len(scores) if scores else 0
                max_score = max(scores) if scores else 0
                min_score = min(scores) if scores else 0
            else:
                avg_score = max_score = min_score = 0
            
            return Response({
                'success': True,
                'total_records': total_records,
                'basic_statistics': {
                    'avg_score': round(avg_score, 2),
                    'max_score': max_score,
                    'min_score': min_score
                },
                'note': '使用備用統計實現，功能受限',
                'fallback': True
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"OCR 統計備用實現失敗: {str(e)}")
            return Response({
                'success': False,
                'error': f'統計資料獲取失敗: {str(e)}',
                'fallback': True
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# 便利函數
def create_ocr_statistics_manager():
    """創建 OCR 統計管理器"""
    try:
        return OCRStatisticsManager()
    except Exception as e:
        logger.warning(f"無法創建 OCR 統計管理器: {e}")
        return None


def get_fallback_ocr_statistics(queryset):
    """獲取備用 OCR 統計資料"""
    return OCRStatisticsFallbackManager.get_fallback_statistics(queryset)


# 對外接口函數
def handle_ocr_storage_benchmark_statistics(queryset):
    """
    處理 OCR Storage Benchmark 統計請求
    
    統一的統計處理接口，包含備用機制
    """
    try:
        # 優先使用主要統計管理器
        manager = create_ocr_statistics_manager()
        if manager:
            return manager.get_ocr_storage_benchmark_statistics(queryset)
        else:
            # 使用備用實現
            logger.warning("OCR 統計管理器不可用，使用備用實現")
            return get_fallback_ocr_statistics(queryset)
            
    except Exception as e:
        logger.error(f"OCR 統計處理失敗: {str(e)}")
        return get_fallback_ocr_statistics(queryset)