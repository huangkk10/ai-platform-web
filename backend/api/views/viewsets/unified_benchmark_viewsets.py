"""
統一 Benchmark 測試案例 ViewSet
整合 Protocol 和 VSA 測試案例管理
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count, Avg
from django.utils import timezone

from api.models import UnifiedBenchmarkTestCase
from api.serializers import UnifiedBenchmarkTestCaseSerializer


class UnifiedBenchmarkTestCaseViewSet(viewsets.ModelViewSet):
    """統一的 Benchmark 測試案例 ViewSet"""
    queryset = UnifiedBenchmarkTestCase.objects.all()
    serializer_class = UnifiedBenchmarkTestCaseSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        根據查詢參數篩選測試案例
        支援的參數:
        - test_type: 測試類型 (protocol, vsa, hybrid)
        - difficulty_level: 難度 (easy, medium, hard)
        - is_active: 是否啟用
        - category: 類別
        - test_class_name: 測試類別名稱
        - search: 搜尋關鍵字（問題內容）
        """
        queryset = super().get_queryset()
        
        # 測試類型篩選
        test_type = self.request.query_params.get('test_type', None)
        if test_type:
            queryset = queryset.filter(test_type=test_type)
        
        # 難度篩選
        difficulty = self.request.query_params.get('difficulty_level', None)
        if difficulty:
            queryset = queryset.filter(difficulty_level=difficulty)
        
        # 啟用狀態篩選
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_bool)
        
        # 類別篩選
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)
        
        # 測試類別名稱篩選
        test_class_name = self.request.query_params.get('test_class_name', None)
        if test_class_name:
            queryset = queryset.filter(test_class_name=test_class_name)
        
        # 搜尋功能
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(question__icontains=search) |
                Q(test_class_name__icontains=search) |
                Q(category__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        """創建測試案例時自動設定創建者"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        獲取測試案例統計資料
        支援參數: test_type（可選，用於篩選特定類型）
        """
        test_type = request.query_params.get('test_type', None)
        queryset = self.get_queryset()
        
        if test_type:
            queryset = queryset.filter(test_type=test_type)
        
        # 基本統計
        total_count = queryset.count()
        active_count = queryset.filter(is_active=True).count()
        inactive_count = queryset.filter(is_active=False).count()
        
        # 難度分布
        difficulty_stats = queryset.values('difficulty_level').annotate(count=Count('id'))
        difficulty_dict = {
            'easy': 0,
            'medium': 0,
            'hard': 0,
        }
        for stat in difficulty_stats:
            difficulty_dict[stat['difficulty_level']] = stat['count']
        
        # 測試類型分布
        type_stats = queryset.values('test_type').annotate(count=Count('id'))
        type_dict = {
            'protocol': 0,
            'vsa': 0,
            'hybrid': 0,
        }
        for stat in type_stats:
            type_dict[stat['test_type']] = stat['count']
        
        # 類別分布（Top 10）
        category_stats = queryset.values('category').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # 測試類別名稱分布（Top 10）
        test_class_stats = queryset.values('test_class_name').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # 平均執行次數和分數
        avg_stats = queryset.aggregate(
            avg_runs=Avg('total_runs'),
            avg_score=Avg('avg_score')
        )
        
        stats = {
            'total': total_count,
            'active': active_count,
            'inactive': inactive_count,
            'by_difficulty': difficulty_dict,
            'by_type': type_dict,
            'by_category': list(category_stats),
            'by_test_class': list(test_class_stats),
            'average_runs': round(avg_stats['avg_runs'] or 0, 2),
            'average_score': round(float(avg_stats['avg_score'] or 0), 2),
        }
        
        return Response(stats)
    
    @action(detail=False, methods=['post'])
    def bulk_import(self, request):
        """批量匯入測試案例"""
        test_type = request.data.get('test_type', 'protocol')
        test_cases = request.data.get('test_cases', [])
        overwrite = request.data.get('overwrite_existing', False)
        
        if not test_cases:
            return Response(
                {'error': '沒有提供測試案例資料'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created_count = 0
        updated_count = 0
        error_count = 0
        errors = []
        
        for case_data in test_cases:
            try:
                # 檢查是否已存在
                question = case_data.get('question')
                existing_case = UnifiedBenchmarkTestCase.objects.filter(
                    test_type=test_type,
                    question=question
                ).first()
                
                if existing_case and overwrite:
                    # 更新現有案例
                    for key, value in case_data.items():
                        setattr(existing_case, key, value)
                    existing_case.test_type = test_type
                    existing_case.save()
                    updated_count += 1
                elif not existing_case:
                    # 創建新案例
                    case_data['test_type'] = test_type
                    case_data['created_by'] = request.user
                    UnifiedBenchmarkTestCase.objects.create(**case_data)
                    created_count += 1
                
            except Exception as e:
                error_count += 1
                errors.append({
                    'question': case_data.get('question', 'Unknown'),
                    'error': str(e)
                })
        
        return Response({
            'success': True,
            'created': created_count,
            'updated': updated_count,
            'errors': error_count,
            'error_details': errors[:10]  # 最多返回 10 個錯誤
        })
    
    @action(detail=False, methods=['get'])
    def bulk_export(self, request):
        """批量匯出測試案例"""
        test_type = request.query_params.get('test_type', None)
        queryset = self.get_queryset()
        
        if test_type:
            queryset = queryset.filter(test_type=test_type)
        
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'test_cases': serializer.data,
            'total_count': queryset.count(),
            'export_time': timezone.now().isoformat()
        })
    
    @action(detail=True, methods=['patch'])
    def toggle_active(self, request, pk=None):
        """切換測試案例的啟用狀態"""
        test_case = self.get_object()
        test_case.is_active = not test_case.is_active
        test_case.save()
        
        serializer = self.get_serializer(test_case)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """獲取所有類別列表"""
        test_type = request.query_params.get('test_type', None)
        queryset = self.get_queryset()
        
        if test_type:
            queryset = queryset.filter(test_type=test_type)
        
        categories = queryset.values_list('category', flat=True).distinct()
        categories = [c for c in categories if c]  # 過濾空值
        
        return Response(sorted(categories))
    
    @action(detail=False, methods=['get'])
    def test_classes(self, request):
        """獲取所有測試類別列表"""
        test_type = request.query_params.get('test_type', None)
        queryset = self.get_queryset()
        
        if test_type:
            queryset = queryset.filter(test_type=test_type)
        
        test_classes = queryset.values_list('test_class_name', flat=True).distinct()
        test_classes = [tc for tc in test_classes if tc]  # 過濾空值
        
        return Response(sorted(test_classes))
