"""
Benchmark System ViewSets

提供完整的 Benchmark 系統 REST API，包含：
- BenchmarkTestCaseViewSet: 測試案例管理
- BenchmarkTestRunViewSet: 測試執行管理
- BenchmarkTestResultViewSet: 測試結果查詢
- SearchAlgorithmVersionViewSet: 演算法版本管理
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta

from api.models import (
    BenchmarkTestCase,
    BenchmarkTestRun,
    BenchmarkTestResult,
    SearchAlgorithmVersion
)
from api.serializers import (
    BenchmarkTestCaseSerializer,
    BenchmarkTestRunSerializer,
    BenchmarkTestResultSerializer,
    SearchAlgorithmVersionSerializer
)


class BenchmarkTestCaseViewSet(viewsets.ModelViewSet):
    """
    測試案例管理 ViewSet
    
    提供功能：
    - CRUD 操作
    - 按類別、難度、題型篩選
    - 批量啟用/停用
    - 統計資訊
    """
    queryset = BenchmarkTestCase.objects.all().order_by('-created_at')
    serializer_class = BenchmarkTestCaseSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """支援多條件篩選"""
        queryset = super().get_queryset()
        
        # 類別篩選
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # 難度篩選
        difficulty = self.request.query_params.get('difficulty')
        if difficulty:
            queryset = queryset.filter(difficulty_level=difficulty)
        
        # 題型篩選
        question_type = self.request.query_params.get('question_type')
        if question_type:
            queryset = queryset.filter(question_type=question_type)
        
        # 知識源篩選
        source = self.request.query_params.get('source')
        if source:
            queryset = queryset.filter(source=source)
        
        # 啟用狀態篩選
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        測試案例統計資訊
        
        GET /api/benchmark/test-cases/statistics/
        """
        queryset = self.get_queryset()
        
        stats = {
            'total_count': queryset.count(),
            'active_count': queryset.filter(is_active=True).count(),
            'inactive_count': queryset.filter(is_active=False).count(),
            
            # 按類別統計
            'by_category': list(
                queryset.values('category')
                .annotate(count=Count('id'))
                .order_by('-count')
            ),
            
            # 按難度統計
            'by_difficulty': list(
                queryset.values('difficulty_level')
                .annotate(count=Count('id'))
                .order_by('difficulty_level')
            ),
            
            # 按題型統計
            'by_question_type': list(
                queryset.values('question_type')
                .annotate(count=Count('id'))
                .order_by('-count')
            ),
            
            # 按知識源統計
            'by_knowledge_source': list(
                queryset.values('source')
                .annotate(count=Count('id'))
                .order_by('-count')
            ),
        }
        
        return Response(stats)
    
    @action(detail=False, methods=['post'])
    def bulk_activate(self, request):
        """
        批量啟用測試案例
        
        POST /api/benchmark/test-cases/bulk_activate/
        Body: {
            "ids": [1, 2, 3, ...]
        }
        """
        ids = request.data.get('ids', [])
        if not ids:
            return Response(
                {'error': '請提供測試案例 ID 列表'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        updated = BenchmarkTestCase.objects.filter(id__in=ids).update(is_active=True)
        
        return Response({
            'success': True,
            'updated_count': updated,
            'message': f'已啟用 {updated} 個測試案例'
        })
    
    @action(detail=False, methods=['post'])
    def bulk_deactivate(self, request):
        """
        批量停用測試案例
        
        POST /api/benchmark/test-cases/bulk_deactivate/
        Body: {
            "ids": [1, 2, 3, ...]
        }
        """
        ids = request.data.get('ids', [])
        if not ids:
            return Response(
                {'error': '請提供測試案例 ID 列表'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        updated = BenchmarkTestCase.objects.filter(id__in=ids).update(is_active=False)
        
        return Response({
            'success': True,
            'updated_count': updated,
            'message': f'已停用 {updated} 個測試案例'
        })


class BenchmarkTestRunViewSet(viewsets.ModelViewSet):
    """
    測試執行管理 ViewSet
    
    提供功能：
    - 查詢測試執行記錄
    - 執行新測試
    - 停止執行中的測試
    - 查看詳細結果
    - 比較不同測試執行
    """
    queryset = BenchmarkTestRun.objects.all().order_by('-created_at')
    serializer_class = BenchmarkTestRunSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """支援篩選"""
        queryset = super().get_queryset()
        
        # 版本篩選
        version_id = self.request.query_params.get('version_id')
        if version_id:
            queryset = queryset.filter(version_id=version_id)
        
        # 狀態篩選
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # 執行類型篩選
        run_type = self.request.query_params.get('run_type')
        if run_type:
            queryset = queryset.filter(run_type=run_type)
        
        # 時間範圍篩選
        days = self.request.query_params.get('days')
        if days:
            try:
                days_int = int(days)
                start_date = timezone.now() - timedelta(days=days_int)
                queryset = queryset.filter(created_at__gte=start_date)
            except ValueError:
                pass
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        """
        獲取測試執行的所有結果
        
        GET /api/benchmark/test-runs/{id}/results/
        """
        test_run = self.get_object()
        results = test_run.results.all().order_by('test_case__id')
        
        # 支援結果篩選
        passed_only = request.query_params.get('passed_only')
        if passed_only == 'true':
            results = results.filter(is_passed=True)
        elif passed_only == 'false':
            results = results.filter(is_passed=False)
        
        serializer = BenchmarkTestResultSerializer(results, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def start_test(self, request):
        """
        啟動新的測試執行
        
        POST /api/benchmark/test-runs/start_test/
        Body: {
            "version_id": 1,
            "run_name": "測試名稱",
            "run_type": "manual",
            "category": "資源路徑",  // 可選
            "difficulty": "easy",    // 可選
            "question_type": "單一事實查詢",  // 可選
            "limit": 10,             // 可選，限制題數
            "notes": "備註"          // 可選
        }
        """
        from library.benchmark.test_runner import BenchmarkTestRunner
        
        # 驗證必要參數
        version_id = request.data.get('version_id')
        if not version_id:
            return Response(
                {'error': '請提供 version_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 驗證版本是否存在
        try:
            SearchAlgorithmVersion.objects.get(id=version_id)
        except SearchAlgorithmVersion.DoesNotExist:
            return Response(
                {'error': f'版本 ID {version_id} 不存在'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 獲取測試案例
        test_cases = BenchmarkTestCase.objects.filter(is_active=True)
        
        # 應用篩選條件
        category = request.data.get('category')
        if category:
            test_cases = test_cases.filter(category=category)
        
        difficulty = request.data.get('difficulty')
        if difficulty:
            test_cases = test_cases.filter(difficulty_level=difficulty)
        
        question_type = request.data.get('question_type')
        if question_type:
            test_cases = test_cases.filter(question_type=question_type)
        
        # 限制數量
        limit = request.data.get('limit')
        if limit:
            try:
                test_cases = test_cases[:int(limit)]
            except ValueError:
                pass
        
        test_cases = list(test_cases)
        
        if not test_cases:
            return Response(
                {'error': '沒有符合條件的測試案例'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 啟動測試
        try:
            runner = BenchmarkTestRunner(version_id=version_id, verbose=False)
            
            test_run = runner.run_batch_tests(
                test_cases=test_cases,
                run_name=request.data.get('run_name', f'API 測試 - {timezone.now().strftime("%Y-%m-%d %H:%M")}'),
                run_type=request.data.get('run_type', 'manual'),
                notes=request.data.get('notes', '')
            )
            
            serializer = self.get_serializer(test_run)
            return Response({
                'success': True,
                'test_run': serializer.data,
                'message': f'測試執行完成，ID: {test_run.id}'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': f'測試執行失敗: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def stop_test(self, request, pk=None):
        """
        停止執行中的測試
        
        POST /api/benchmark/test-runs/{id}/stop_test/
        """
        test_run = self.get_object()
        
        if test_run.status != 'running':
            return Response(
                {'error': f'測試狀態為 {test_run.status}，無法停止'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 更新狀態為已停止
        test_run.status = 'stopped'
        test_run.completed_at = timezone.now()
        test_run.save()
        
        return Response({
            'success': True,
            'message': f'測試 {test_run.id} 已停止'
        })
    
    @action(detail=False, methods=['post'])
    def compare(self, request):
        """
        比較兩個測試執行的結果
        
        POST /api/benchmark/test-runs/compare/
        Body: {
            "run_id_1": 1,
            "run_id_2": 2
        }
        """
        run_id_1 = request.data.get('run_id_1')
        run_id_2 = request.data.get('run_id_2')
        
        if not run_id_1 or not run_id_2:
            return Response(
                {'error': '請提供 run_id_1 和 run_id_2'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            run1 = BenchmarkTestRun.objects.get(id=run_id_1)
            run2 = BenchmarkTestRun.objects.get(id=run_id_2)
        except BenchmarkTestRun.DoesNotExist:
            return Response(
                {'error': '測試執行 ID 不存在'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        comparison = {
            'run_1': {
                'id': run1.id,
                'name': run1.run_name,
                'version': run1.version.version_name,
                'overall_score': run1.overall_score,
                'precision': run1.precision_pct,
                'recall': run1.recall_pct,
                'f1_score': run1.f1_score_pct,
                'ndcg': run1.ndcg_pct,
                'avg_time_ms': run1.avg_time_ms,
                'pass_rate': (run1.passed_test_cases / run1.total_test_cases * 100) if run1.total_test_cases > 0 else 0
            },
            'run_2': {
                'id': run2.id,
                'name': run2.run_name,
                'version': run2.version.version_name,
                'overall_score': run2.overall_score,
                'precision': run2.precision_pct,
                'recall': run2.recall_pct,
                'f1_score': run2.f1_score_pct,
                'ndcg': run2.ndcg_pct,
                'avg_time_ms': run2.avg_time_ms,
                'pass_rate': (run2.passed_test_cases / run2.total_test_cases * 100) if run2.total_test_cases > 0 else 0
            },
            'delta': {
                'overall_score': run2.overall_score - run1.overall_score,
                'precision': run2.precision_pct - run1.precision_pct,
                'recall': run2.recall_pct - run1.recall_pct,
                'f1_score': run2.f1_score_pct - run1.f1_score_pct,
                'ndcg': run2.ndcg_pct - run1.ndcg_pct,
                'avg_time_ms': run2.avg_time_ms - run1.avg_time_ms,
            }
        }
        
        return Response(comparison)


class BenchmarkTestResultViewSet(viewsets.ReadOnlyModelViewSet):
    """
    測試結果查詢 ViewSet（唯讀）
    
    提供功能：
    - 查詢測試結果
    - 按測試執行、測試案例、通過狀態篩選
    - 結果統計分析
    """
    queryset = BenchmarkTestResult.objects.all().order_by('-created_at')
    serializer_class = BenchmarkTestResultSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """支援篩選"""
        queryset = super().get_queryset()
        
        # 測試執行篩選
        test_run_id = self.request.query_params.get('test_run_id')
        if test_run_id:
            queryset = queryset.filter(test_run_id=test_run_id)
        
        # 測試案例篩選
        test_case_id = self.request.query_params.get('test_case_id')
        if test_case_id:
            queryset = queryset.filter(test_case_id=test_case_id)
        
        # 通過狀態篩選
        is_passed = self.request.query_params.get('is_passed')
        if is_passed is not None:
            queryset = queryset.filter(is_passed=is_passed.lower() == 'true')
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def failed_cases(self, request):
        """
        獲取所有失敗的測試案例
        
        GET /api/benchmark/test-results/failed_cases/
        """
        queryset = self.get_queryset().filter(is_passed=False)
        
        # 按測試案例分組統計失敗次數
        failed_stats = {}
        for result in queryset:
            case_id = result.test_case_id
            if case_id not in failed_stats:
                failed_stats[case_id] = {
                    'test_case_id': case_id,
                    'question': result.test_case.question,
                    'category': result.test_case.category,
                    'difficulty': result.test_case.difficulty_level,
                    'failed_count': 0,
                    'recent_failures': []
                }
            
            failed_stats[case_id]['failed_count'] += 1
            
            # 記錄最近 3 次失敗
            if len(failed_stats[case_id]['recent_failures']) < 3:
                failed_stats[case_id]['recent_failures'].append({
                    'test_run_id': result.test_run_id,
                    'test_run_name': result.test_run.run_name,
                    'precision': result.precision_score,
                    'recall': result.recall_score,
                    'created_at': result.created_at.isoformat()
                })
        
        return Response({
            'total_failed_results': queryset.count(),
            'unique_failed_cases': len(failed_stats),
            'failed_cases': list(failed_stats.values())
        })


class SearchAlgorithmVersionViewSet(viewsets.ModelViewSet):
    """
    搜尋演算法版本管理 ViewSet
    
    提供功能：
    - CRUD 操作
    - 設定基準版本
    - 版本比較
    - 版本統計
    """
    queryset = SearchAlgorithmVersion.objects.all().order_by('-created_at')
    serializer_class = SearchAlgorithmVersionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        """創建時自動設定 created_by"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def set_as_baseline(self, request, pk=None):
        """
        設定為基準版本
        
        POST /api/benchmark/versions/{id}/set_as_baseline/
        """
        version = self.get_object()
        
        # 取消其他版本的基準狀態
        SearchAlgorithmVersion.objects.filter(is_baseline=True).update(is_baseline=False)
        
        # 設定當前版本為基準
        version.is_baseline = True
        version.save()
        
        return Response({
            'success': True,
            'message': f'版本 {version.version_name} 已設定為基準版本'
        })
    
    @action(detail=True, methods=['get'])
    def test_history(self, request, pk=None):
        """
        獲取版本的測試歷史
        
        GET /api/benchmark/versions/{id}/test_history/
        """
        version = self.get_object()
        test_runs = version.test_runs.all().order_by('-created_at')
        
        serializer = BenchmarkTestRunSerializer(test_runs, many=True)
        return Response({
            'version': self.get_serializer(version).data,
            'test_runs': serializer.data,
            'total_runs': test_runs.count()
        })
    
    @action(detail=False, methods=['get'])
    def baseline(self, request):
        """
        獲取當前基準版本
        
        GET /api/benchmark/versions/baseline/
        """
        try:
            baseline = SearchAlgorithmVersion.objects.get(is_baseline=True)
            serializer = self.get_serializer(baseline)
            return Response(serializer.data)
        except SearchAlgorithmVersion.DoesNotExist:
            return Response(
                {'error': '尚未設定基準版本'},
                status=status.HTTP_404_NOT_FOUND
            )
