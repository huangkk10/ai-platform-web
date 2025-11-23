"""
Dify Benchmark ViewSets

提供 Dify 跑分系統的 RESTful API
"""

import logging
import json
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Avg, Count, Min, Max
from django.utils import timezone

from api.models import (
    DifyConfigVersion,
    DifyBenchmarkTestCase,
    DifyTestRun,
    DifyTestResult,
    DifyAnswerEvaluation
)

# 從 api.serializers (單一文件) 導入
from api.serializers import (
    DifyConfigVersionSerializer,
    DifyBenchmarkTestCaseSerializer,
    DifyTestRunSerializer,
    DifyTestResultSerializer,
    DifyAnswerEvaluationSerializer,
    DifyTestRunListSerializer,
    DifyBenchmarkTestCaseBulkImportSerializer
)

from library.dify_benchmark import DifyBatchTester

logger = logging.getLogger(__name__)


class DifyConfigVersionViewSet(viewsets.ModelViewSet):
    """
    Dify 配置版本 ViewSet
    
    功能：
    - 版本 CRUD 操作
    - 設定 baseline 版本
    - 執行批量測試
    - 版本效能統計
    
    API 端點：
    - GET    /api/dify-benchmark/versions/              列出所有版本
    - POST   /api/dify-benchmark/versions/              創建新版本
    - GET    /api/dify-benchmark/versions/:id/          獲取版本詳情
    - PUT    /api/dify-benchmark/versions/:id/          更新版本
    - PATCH  /api/dify-benchmark/versions/:id/          部分更新
    - DELETE /api/dify-benchmark/versions/:id/          刪除版本
    - POST   /api/dify-benchmark/versions/:id/set_baseline/       設定為基準版本
    - POST   /api/dify-benchmark/versions/:id/run_benchmark/      執行基準測試
    - GET    /api/dify-benchmark/versions/:id/statistics/         獲取版本統計
    - POST   /api/dify-benchmark/versions/batch_test/             批量測試多個版本
    """
    
    queryset = DifyConfigVersion.objects.all().order_by('-created_at')
    serializer_class = DifyConfigVersionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """自定義查詢集"""
        queryset = super().get_queryset()
        
        # 篩選啟用/停用
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # 篩選 baseline
        is_baseline = self.request.query_params.get('is_baseline')
        if is_baseline is not None:
            queryset = queryset.filter(is_baseline=is_baseline.lower() == 'true')
        
        # 搜尋版本名稱
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(version_name__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset
    
    def perform_create(self, serializer):
        """創建版本時設定創建者"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def set_baseline(self, request, pk=None):
        """
        設定為基準版本
        
        POST /api/dify-benchmark/versions/:id/set_baseline/
        
        將指定版本設定為基準版本，同時取消其他版本的 baseline 標記
        """
        version = self.get_object()
        
        # 取消所有其他版本的 baseline
        DifyConfigVersion.objects.filter(is_baseline=True).update(is_baseline=False)
        
        # 設定當前版本為 baseline
        version.is_baseline = True
        version.save()
        
        logger.info(f"版本 {version.version_name} 已設定為 baseline")
        
        return Response({
            'success': True,
            'message': f'版本 {version.version_name} 已設定為基準版本',
            'version': self.get_serializer(version).data
        })
    
    @action(detail=True, methods=['post'])
    def run_benchmark(self, request, pk=None):
        """
        執行基準測試
        
        POST /api/dify-benchmark/versions/:id/run_benchmark/
        
        Body:
        {
            "test_case_ids": [1, 2, 3],  // 可選，不提供則使用所有啟用案例
            "run_name": "快速測試",       // 可選
            "notes": "測試備註",          // 可選
            "use_ai_evaluator": false    // 可選，預設 false
        }
        
        Returns:
        {
            "success": true,
            "test_run_id": 123,
            "message": "測試已開始執行"
        }
        """
        version = self.get_object()
        
        # 解析請求參數
        test_case_ids = request.data.get('test_case_ids')
        run_name = request.data.get('run_name', f"{version.version_name} - 基準測試")
        notes = request.data.get('notes', '')
        use_ai_evaluator = request.data.get('use_ai_evaluator', False)
        
        try:
            # 執行批量測試（使用單一版本）
            tester = DifyBatchTester()
            
            result = tester.run_batch_test(
                version_ids=[version.id],
                test_case_ids=test_case_ids,
                batch_name=run_name,
                description=notes  # 修正：notes → description
                # 注意：use_ai_evaluator 參數暫時移除，DifyBatchTester 不支援
            )
            
            if result['success']:
                test_run_id = result['test_run_ids'][0] if result['test_run_ids'] else None
                
                return Response({
                    'success': True,
                    'test_run_id': test_run_id,
                    'batch_id': result['batch_id'],
                    'summary': result['summary'],
                    'message': '測試執行完成'
                })
            else:
                return Response({
                    'success': False,
                    'error': result.get('error', '測試執行失敗')
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            logger.error(f"執行基準測試失敗: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """
        獲取版本統計資料
        
        GET /api/dify-benchmark/versions/:id/statistics/
        
        Returns:
        {
            "version_id": 1,
            "version_name": "...",
            "total_test_runs": 10,
            "total_test_cases": 55,
            "average_score": 85.5,
            "average_pass_rate": 92.3,
            "best_score": 95.2,
            "worst_score": 78.3,
            "recent_runs": [...]
        }
        """
        version = self.get_object()
        
        # 統計所有測試記錄
        test_runs = DifyTestRun.objects.filter(version=version)
        
        stats = test_runs.aggregate(
            total_runs=Count('id'),
            avg_score=Avg('average_score'),
            avg_pass_rate=Avg('pass_rate')
        )
        
        # 最佳/最差分數
        best_run = test_runs.order_by('-average_score').first()
        worst_run = test_runs.order_by('average_score').first()
        
        # 最近 5 次測試
        recent_runs = test_runs.order_by('-created_at')[:5]
        
        return Response({
            'version_id': version.id,
            'version_name': version.version_name,
            'total_test_runs': stats['total_runs'] or 0,
            'average_score': round(stats['avg_score'] or 0, 2),
            'average_pass_rate': round(stats['avg_pass_rate'] or 0, 2),
            'best_score': round(best_run.average_score, 2) if best_run else 0,
            'worst_score': round(worst_run.average_score, 2) if worst_run else 0,
            'recent_runs': DifyTestRunSerializer(recent_runs, many=True).data
        })
    
    @action(detail=False, methods=['post'])
    def batch_test(self, request):
        """
        批量測試多個版本（支援多線程並行執行）
        
        POST /api/dify-benchmark/versions/batch_test/
        
        Body:
        {
            "version_ids": [1, 2, 3],       // 必填：版本 ID 列表
            "test_case_ids": [1, 2, 3],     // 可選：測試案例 ID（空則全部）
            "batch_name": "三版本對比",      // 可選：批次名稱
            "notes": "測試備註",            // 可選：備註
            "use_ai_evaluator": false,      // 可選：是否使用 AI 評分（預設 false）
            "use_parallel": true,           // 可選：是否並行執行（預設 true）
            "max_workers": 5                // 可選：最大並行線程數（預設 5）
        }
        
        效能提升：
        - 10 個測試：30 秒 → 6 秒（80% 提升）
        - 50 個測試：150 秒 → 30 秒（80% 提升）
        
        Returns:
        {
            "success": true,
            "batch_id": "batch_xxx",
            "test_run_ids": [123, 124, 125],
            "comparison": {...},
            "summary": {...}
        }
        """
        # 解析請求參數
        version_ids = request.data.get('version_ids')
        test_case_ids = request.data.get('test_case_ids')
        batch_name = request.data.get('batch_name')
        notes = request.data.get('notes', '')
        use_ai_evaluator = request.data.get('use_ai_evaluator', False)
        
        # 並行執行參數（新增）
        use_parallel = request.data.get('use_parallel', True)  # 預設啟用
        max_workers = request.data.get('max_workers', 5)       # 預設 5 個並行
        
        # 驗證參數
        if not version_ids or not isinstance(version_ids, list):
            return Response({
                'success': False,
                'error': 'version_ids 必須是版本 ID 列表'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # 執行批量測試（傳遞並行參數）
            tester = DifyBatchTester(
                use_ai_evaluator=use_ai_evaluator,
                use_parallel=use_parallel,
                max_workers=max_workers
            )
            
            result = tester.run_batch_test(
                version_ids=version_ids,
                test_case_ids=test_case_ids,
                batch_name=batch_name,
                description=notes  # 修正：notes → description
                # 注意：use_ai_evaluator 已在 tester 初始化時設定
            )
            
            if result['success']:
                return Response({
                    'success': True,
                    'batch_id': result['batch_id'],
                    'batch_name': result['batch_name'],
                    'test_run_ids': result['test_run_ids'],
                    'comparison': result['comparison'],
                    'summary': result['summary'],
                    'message': '批量測試執行完成'
                })
            else:
                return Response({
                    'success': False,
                    'error': result.get('error', '批量測試執行失敗')
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            logger.error(f"批量測試失敗: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DifyBenchmarkTestCaseViewSet(viewsets.ModelViewSet):
    """
    Dify 基準測試案例 ViewSet
    
    功能：
    - 測試案例 CRUD 操作
    - 批量導入案例（CSV/JSON）
    - 批量導出案例
    - 案例啟用/停用
    
    API 端點：
    - GET    /api/dify-benchmark/test-cases/              列出所有測試案例
    - POST   /api/dify-benchmark/test-cases/              創建測試案例
    - GET    /api/dify-benchmark/test-cases/:id/          獲取案例詳情
    - PUT    /api/dify-benchmark/test-cases/:id/          更新案例
    - PATCH  /api/dify-benchmark/test-cases/:id/          部分更新
    - DELETE /api/dify-benchmark/test-cases/:id/          刪除案例
    - POST   /api/dify-benchmark/test-cases/bulk_import/  批量導入案例
    - GET    /api/dify-benchmark/test-cases/bulk_export/  批量導出案例
    - PATCH  /api/dify-benchmark/test-cases/:id/toggle_active/  啟用/停用案例
    """
    
    queryset = DifyBenchmarkTestCase.objects.all().order_by('test_class_name', 'id')
    serializer_class = DifyBenchmarkTestCaseSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """自定義查詢集"""
        queryset = super().get_queryset()
        
        # 篩選測試類別
        test_class = self.request.query_params.get('test_class')
        if test_class:
            queryset = queryset.filter(test_class_name=test_class)
        
        # 篩選啟用/停用
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # 篩選難度
        difficulty = self.request.query_params.get('difficulty')
        if difficulty:
            queryset = queryset.filter(difficulty_level=difficulty)
        
        # 搜尋問題內容
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(question__icontains=search) |
                Q(expected_answer__icontains=search) |
                Q(answer_keywords__icontains=search)
            )
        
        return queryset
    
    @action(detail=False, methods=['post'])
    def bulk_import(self, request):
        """
        批量導入測試案例
        
        POST /api/dify-benchmark/test-cases/bulk_import/
        
        支援格式：JSON, CSV
        
        Body (JSON):
        {
            "format": "json",
            "data": [
                {
                    "test_class_name": "I3C",
                    "question": "什麼是 I3C？",
                    "expected_answer": "...",
                    "answer_keywords": ["I3C", "協議", "傳輸"],
                    "difficulty_level": "medium"
                }
            ],
            "overwrite_existing": false
        }
        
        Body (CSV File):
        {
            "format": "csv",
            "file": <file>,
            "overwrite_existing": false
        }
        """
        import csv
        import io
        import json
        
        serializer = DifyBenchmarkTestCaseBulkImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        format_type = serializer.validated_data['format']
        overwrite = serializer.validated_data.get('overwrite_existing', False)
        
        try:
            if format_type == 'json':
                # JSON 格式導入
                data = serializer.validated_data.get('data', [])
                
                imported_count = 0
                skipped_count = 0
                errors = []
                
                for item in data:
                    # 檢查是否已存在相同問題
                    existing = DifyBenchmarkTestCase.objects.filter(
                        question=item['question']
                    ).first()
                    
                    if existing and not overwrite:
                        skipped_count += 1
                        continue
                    
                    try:
                        if existing and overwrite:
                            # 更新現有案例
                            for key, value in item.items():
                                setattr(existing, key, value)
                            existing.save()
                        else:
                            # 創建新案例
                            DifyBenchmarkTestCase.objects.create(**item)
                        
                        imported_count += 1
                    except Exception as e:
                        errors.append(f"導入失敗: {item.get('question', 'Unknown')}: {str(e)}")
                
                return Response({
                    'success': True,
                    'imported': imported_count,
                    'skipped': skipped_count,
                    'errors': errors,
                    'message': f'成功導入 {imported_count} 個測試案例'
                })
            
            elif format_type == 'csv':
                # CSV 格式導入
                file = serializer.validated_data.get('file')
                if not file:
                    return Response({
                        'success': False,
                        'error': 'CSV 格式需要提供 file'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # 讀取 CSV
                decoded_file = file.read().decode('utf-8-sig')  # 支援 BOM
                csv_reader = csv.DictReader(io.StringIO(decoded_file))
                
                imported_count = 0
                skipped_count = 0
                errors = []
                
                for row in csv_reader:
                    # CSV 欄位映射
                    item = {
                        'test_class_name': row.get('test_class_name', ''),
                        'question': row.get('question', ''),
                        'expected_answer': row.get('expected_answer', ''),
                        'answer_keywords': json.loads(row.get('answer_keywords', '[]')),
                        'difficulty_level': row.get('difficulty_level', 'medium'),
                        'evaluation_criteria': row.get('evaluation_criteria', ''),
                        'notes': row.get('notes', ''),
                        'is_active': row.get('is_active', 'true').lower() == 'true'
                    }
                    
                    # 檢查是否已存在
                    existing = DifyBenchmarkTestCase.objects.filter(
                        question=item['question']
                    ).first()
                    
                    if existing and not overwrite:
                        skipped_count += 1
                        continue
                    
                    try:
                        if existing and overwrite:
                            for key, value in item.items():
                                setattr(existing, key, value)
                            existing.save()
                        else:
                            DifyBenchmarkTestCase.objects.create(**item)
                        
                        imported_count += 1
                    except Exception as e:
                        errors.append(f"導入失敗: {item.get('question', 'Unknown')}: {str(e)}")
                
                return Response({
                    'success': True,
                    'imported': imported_count,
                    'skipped': skipped_count,
                    'errors': errors,
                    'message': f'成功導入 {imported_count} 個測試案例'
                })
        
        except Exception as e:
            logger.error(f"批量導入失敗: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def bulk_export(self, request):
        """
        批量導出測試案例
        
        GET /api/dify-benchmark/test-cases/bulk_export/?format=json
        GET /api/dify-benchmark/test-cases/bulk_export/?format=csv
        
        Query Parameters:
        - format: json | csv (預設 json)
        - test_class: 測試類別篩選
        - is_active: true | false
        """
        import csv
        from django.http import HttpResponse
        
        format_type = request.query_params.get('format', 'json')
        queryset = self.filter_queryset(self.get_queryset())
        
        if format_type == 'csv':
            # CSV 匯出
            response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
            response['Content-Disposition'] = 'attachment; filename="dify_test_cases.csv"'
            
            # 添加 UTF-8 BOM（Excel 正確識別中文）
            response.write('\ufeff')
            
            writer = csv.writer(response)
            writer.writerow([
                'test_class_name', 'question', 'expected_answer', 'answer_keywords',
                'difficulty_level', 'evaluation_criteria', 'notes', 'is_active', 'order'
            ])
            
            for case in queryset:
                writer.writerow([
                    case.test_class_name,
                    case.question,
                    case.expected_answer,
                    json.dumps(case.answer_keywords, ensure_ascii=False),
                    case.difficulty_level,
                    case.evaluation_criteria or '',
                    case.notes or '',
                    case.is_active,
                    case.order
                ])
            
            return response
        
        else:
            # JSON 匯出
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                'success': True,
                'count': queryset.count(),
                'data': serializer.data
            })
    
    @action(detail=True, methods=['patch'])
    def toggle_active(self, request, pk=None):
        """
        啟用/停用測試案例
        
        PATCH /api/dify-benchmark/test-cases/:id/toggle_active/
        """
        test_case = self.get_object()
        test_case.is_active = not test_case.is_active
        test_case.save()
        
        return Response({
            'success': True,
            'is_active': test_case.is_active,
            'message': f"測試案例已{'啟用' if test_case.is_active else '停用'}"
        })


class DifyTestRunViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Dify 測試執行 ViewSet (唯讀)
    
    功能：
    - 查詢測試執行記錄
    - 查看測試結果詳情
    - 測試執行對比分析
    - 測試歷史查詢
    
    API 端點：
    - GET /api/dify-benchmark/test-runs/                    列出所有測試執行
    - GET /api/dify-benchmark/test-runs/:id/                獲取測試執行詳情
    - GET /api/dify-benchmark/test-runs/:id/results/        獲取測試結果列表
    - GET /api/dify-benchmark/test-runs/comparison/         對比多個測試執行
    - GET /api/dify-benchmark/test-runs/batch_history/      查詢批次歷史
    """
    
    queryset = DifyTestRun.objects.all().select_related('version').order_by('-created_at')
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        """根據 action 選擇序列化器"""
        if self.action == 'list':
            return DifyTestRunListSerializer
        return DifyTestRunSerializer
    
    def get_queryset(self):
        """自定義查詢集"""
        queryset = super().get_queryset()
        
        # 篩選版本
        version_id = self.request.query_params.get('version_id')
        if version_id:
            queryset = queryset.filter(version_id=version_id)
        
        # 篩選批次
        batch_id = self.request.query_params.get('batch_id')
        if batch_id:
            queryset = queryset.filter(batch_id=batch_id)
        
        # 篩選狀態
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # 日期範圍篩選
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        """
        獲取測試結果列表
        
        GET /api/dify-benchmark/test-runs/:id/results/
        
        Query Parameters:
        - passed: true | false (篩選通過/失敗的結果)
        - min_score: 最低分數
        - max_score: 最高分數
        """
        test_run = self.get_object()
        results = test_run.results.select_related('test_case').prefetch_related('evaluation')
        
        # 篩選通過/失敗
        passed = request.query_params.get('passed')
        if passed is not None:
            is_passed = passed.lower() == 'true'
            results = results.filter(evaluation__is_passed=is_passed)
        
        # 篩選分數範圍
        min_score = request.query_params.get('min_score')
        max_score = request.query_params.get('max_score')
        if min_score:
            results = results.filter(evaluation__score__gte=float(min_score))
        if max_score:
            results = results.filter(evaluation__score__lte=float(max_score))
        
        serializer = DifyTestResultSerializer(results, many=True)
        
        return Response({
            'test_run_id': test_run.id,
            'test_run_name': test_run.run_name,
            'total_results': results.count(),
            'results': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def comparison(self, request):
        """
        對比多個測試執行
        
        GET /api/dify-benchmark/test-runs/comparison/?test_run_ids=1,2,3
        GET /api/dify-benchmark/test-runs/comparison/?batch_id=batch_xxx
        
        Query Parameters:
        - test_run_ids: 測試執行 ID 列表（逗號分隔）
        - batch_id: 批次 ID（自動載入該批次的所有測試）
        
        Returns:
        {
            "test_runs": [...],
            "comparison": {
                "best_version": {...},
                "ranking": [...],
                "statistics": {...}
            }
        }
        """
        test_run_ids = request.query_params.get('test_run_ids')
        batch_id = request.query_params.get('batch_id')
        
        if not test_run_ids and not batch_id:
            return Response({
                'success': False,
                'error': '必須提供 test_run_ids 或 batch_id'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 獲取測試執行
        if batch_id:
            test_runs = DifyTestRun.objects.filter(batch_id=batch_id).select_related('version')
        else:
            ids = [int(id) for id in test_run_ids.split(',')]
            test_runs = DifyTestRun.objects.filter(id__in=ids).select_related('version')
        
        if not test_runs.exists():
            return Response({
                'success': False,
                'error': '找不到測試執行記錄'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # 生成對比報告
        comparison = self._generate_comparison_report(test_runs)
        
        serializer = DifyTestRunListSerializer(test_runs, many=True)
        
        return Response({
            'success': True,
            'test_runs': serializer.data,
            'comparison': comparison
        })
    
    @action(detail=False, methods=['get'])
    def batch_history(self, request):
        """
        查詢批次歷史
        
        GET /api/dify-benchmark/test-runs/batch_history/
        
        Returns:
        {
            "batches": [
                {
                    "batch_id": "batch_xxx",
                    "batch_name": "...",
                    "test_count": 3,
                    "created_at": "...",
                    "versions": [...]
                }
            ]
        }
        """
        # 按 batch_id 分組
        batches = DifyTestRun.objects.values('batch_id').annotate(
            test_count=Count('id'),
            first_created=Min('created_at')
        ).order_by('-first_created')
        
        batch_list = []
        for batch in batches:
            if not batch['batch_id']:
                continue
            
            # 獲取該批次的測試執行
            batch_runs = DifyTestRun.objects.filter(
                batch_id=batch['batch_id']
            ).select_related('version')
            
            batch_list.append({
                'batch_id': batch['batch_id'],
                'batch_name': batch_runs.first().run_name if batch_runs.exists() else '',
                'test_count': batch['test_count'],
                'created_at': batch['first_created'],
                'versions': [
                    {
                        'id': run.version.id,
                        'name': run.version.version_name,
                        'pass_rate': run.pass_rate,
                        'average_score': run.average_score
                    }
                    for run in batch_runs
                ]
            })
        
        return Response({
            'success': True,
            'total_batches': len(batch_list),
            'batches': batch_list
        })
    
    def _generate_comparison_report(self, test_runs):
        """生成對比報告"""
        from django.db.models import Min, Max, Avg
        
        # 排序（按通過率和平均分）
        ranked_runs = sorted(
            test_runs,
            key=lambda x: (x.pass_rate or 0, x.average_score or 0),
            reverse=True
        )
        
        # 最佳版本
        best_run = ranked_runs[0] if ranked_runs else None
        
        # 統計資料
        stats = test_runs.aggregate(
            min_pass_rate=Min('pass_rate'),
            max_pass_rate=Max('pass_rate'),
            avg_pass_rate=Avg('pass_rate'),
            min_score=Min('average_score'),
            max_score=Max('average_score'),
            avg_score=Avg('average_score')
        )
        
        # 版本排名
        ranking = [
            {
                'rank': idx + 1,
                'version_id': run.version.id,
                'version_name': run.version.version_name,
                'test_run_id': run.id,
                'pass_rate': round(run.pass_rate or 0, 2),
                'average_score': round(run.average_score or 0, 2),
                'total_cases': run.total_cases,
                'passed_cases': run.passed_cases
            }
            for idx, run in enumerate(ranked_runs)
        ]
        
        return {
            'best_version': {
                'version_id': best_run.version.id,
                'version_name': best_run.version.version_name,
                'pass_rate': round(best_run.pass_rate or 0, 2),
                'average_score': round(best_run.average_score or 0, 2)
            } if best_run else None,
            'ranking': ranking,
            'statistics': {
                'min_pass_rate': round(stats['min_pass_rate'] or 0, 2),
                'max_pass_rate': round(stats['max_pass_rate'] or 0, 2),
                'avg_pass_rate': round(stats['avg_pass_rate'] or 0, 2),
                'min_score': round(stats['min_score'] or 0, 2),
                'max_score': round(stats['max_score'] or 0, 2),
                'avg_score': round(stats['avg_score'] or 0, 2)
            }
        }
