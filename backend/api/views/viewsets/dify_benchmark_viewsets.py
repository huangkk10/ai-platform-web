"""
Dify Benchmark ViewSets

提供 Dify 跑分系統的 RESTful API
"""

import logging
import json
import threading  # ✅ 新增：用於背景執行測試
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Avg, Count, Min, Max
from django.utils import timezone

# Import custom renderer for SSE
from api.renderers import ServerSentEventRenderer

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
    pagination_class = None  # 禁用分頁，返回所有版本
    
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
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def set_baseline(self, request, pk=None):
        """
        設定為基準版本（增強版 - 支援動態版本）
        
        POST /api/dify-benchmark/versions/:id/set_baseline/
        
        功能：
        1. 清除所有版本的 is_baseline 標記
        2. 設定選定版本為 Baseline
        3. 記錄操作日誌
        4. 如果是動態版本，刷新 Threshold 快取
        
        權限：僅管理員
        """
        from django.db import transaction
        from library.dify_integration.dynamic_threshold_loader import DynamicThresholdLoader
        
        version = self.get_object()
        
        with transaction.atomic():
            # 取消所有其他版本的 baseline
            DifyConfigVersion.objects.filter(is_baseline=True).update(is_baseline=False)
            
            # 設定當前版本為 baseline
            version.is_baseline = True
            version.save()
            
            # 🆕 如果是動態版本，刷新 Threshold 快取
            is_dynamic = DynamicThresholdLoader.is_dynamic_version(version.rag_settings)
            if is_dynamic:
                try:
                    from library.common.threshold_manager import get_threshold_manager
                    manager = get_threshold_manager()
                    manager.clear_cache()
                    logger.info(f"🔄 動態版本 {version.version_name} 設為 Baseline，已刷新快取")
                except Exception as e:
                    logger.error(f"刷新快取失敗: {str(e)}")
            
            # 記錄操作日誌
            logger.info(
                f"✅ 版本切換: {version.version_name} (ID: {version.id}) "
                f"已設為 Baseline，動態版本: {is_dynamic}，操作者: {request.user.username}"
            )
        
        return Response({
            'success': True,
            'message': f'版本 {version.version_name} 已設定為 Baseline',
            'version_id': version.id,
            'version_name': version.version_name,
            'is_dynamic': is_dynamic,
            'timestamp': timezone.now().isoformat(),
        })
    
    @action(detail=False, methods=['get'])
    def get_baseline(self, request):
        """
        獲取當前 Baseline 版本
        
        GET /api/dify-benchmark/versions/get_baseline/
        
        回應：
        {
            "version_id": 1,
            "version_name": "Dify 二階搜尋 v1.2.1",
            "version_code": "dify-two-tier-v1.2.1",
            "is_dynamic": true,
            "rag_settings": {...},  // 如果是動態版本，返回動態載入後的配置
            "description": "..."
        }
        """
        from library.dify_integration.dynamic_threshold_loader import DynamicThresholdLoader
        
        baseline = DifyConfigVersion.objects.filter(
            is_baseline=True, 
            is_active=True
        ).first()
        
        if not baseline:
            return Response({
                'success': False,
                'error': '找不到 Baseline 版本',
                'message': '請在版本管理中設定一個 Baseline 版本'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # 🆕 如果是動態版本，載入最新配置
        is_dynamic = DynamicThresholdLoader.is_dynamic_version(baseline.rag_settings)
        if is_dynamic:
            try:
                rag_settings = DynamicThresholdLoader.load_full_rag_settings(baseline.rag_settings)
                logger.info(f"🔄 Baseline 版本 {baseline.version_name} 使用動態配置")
            except Exception as e:
                logger.error(f"動態載入失敗，使用靜態配置: {str(e)}")
                rag_settings = baseline.rag_settings
        else:
            rag_settings = baseline.rag_settings
        
        serializer = self.get_serializer(baseline)
        data = serializer.data
        data['is_dynamic'] = is_dynamic
        data['rag_settings'] = rag_settings  # 返回動態載入後的配置
        
        return Response({
            'success': True,
            'baseline': data  # ✅ 包裝在 baseline 欄位中
        }, status=status.HTTP_200_OK)
    
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
            'best_score': round(best_run.average_score or 0, 2) if best_run else 0,
            'worst_score': round(worst_run.average_score or 0, 2) if worst_run else 0,
            'recent_runs': DifyTestRunSerializer(recent_runs, many=True).data
        })
    
    @action(detail=False, methods=['post'], permission_classes=[])
    def batch_test(self, request):
        """
        批量測試多個版本（背景執行，立即返回）
        
        POST /api/dify-benchmark/versions/batch_test/
        
        Body:
        {
            "batch_id": "batch_xxx",        // 必填：批次 ID（前端生成）
            "version_ids": [1, 2, 3],       // 必填：版本 ID 列表
            "test_case_ids": [1, 2, 3],     // 可選：測試案例 ID（空則全部）
            "batch_name": "三版本對比",      // 可選：批次名稱
            "notes": "測試備註",            // 可選：備註
            "use_ai_evaluator": false,      // 可選：是否使用 AI 評分（預設 false）
            "use_parallel": true,           // 可選：是否並行執行（預設 true）
            "max_workers": 5                // 可選：最大並行線程數（預設 5）
        }
        
        Returns (立即返回，不等待測試完成):
        {
            "success": true,
            "batch_id": "batch_xxx",
            "message": "批量測試已啟動，請透過 SSE 追蹤進度"
        }
        """
        # 解析請求參數
        batch_id = request.data.get('batch_id')  # ✅ 前端傳來的 batch_id
        version_ids = request.data.get('version_ids')
        test_case_ids = request.data.get('test_case_ids')
        batch_name = request.data.get('batch_name')
        notes = request.data.get('notes', '')
        use_ai_evaluator = request.data.get('use_ai_evaluator', False)
        
        # 並行執行參數
        use_parallel = request.data.get('use_parallel', True)
        max_workers = request.data.get('max_workers', 5)
        
        # 驗證參數
        if not batch_id:
            return Response({
                'success': False,
                'error': 'batch_id 必填'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not version_ids or not isinstance(version_ids, list):
            return Response({
                'success': False,
                'error': 'version_ids 必須是版本 ID 列表'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"📥 收到批次測試請求: batch_id={batch_id}, version_ids={version_ids}")
        
        # ✅ 定義背景執行函數
        def run_test_in_background():
            """在背景線程中執行測試"""
            try:
                logger.info(f"🚀 [背景執行] 開始批次測試: batch_id={batch_id}")
                
                tester = DifyBatchTester(
                    use_ai_evaluator=use_ai_evaluator,
                    use_parallel=use_parallel,
                    max_workers=max_workers
                )
                
                result = tester.run_batch_test(
                    version_ids=version_ids,
                    test_case_ids=test_case_ids,
                    batch_name=batch_name,
                    description=notes,
                    batch_id=batch_id
                )
                
                logger.info(f"✅ [背景執行] 批次測試完成: batch_id={batch_id}")
                
            except Exception as e:
                logger.error(f"❌ [背景執行] 批次測試失敗: batch_id={batch_id}, error={str(e)}")
                import traceback
                logger.error(traceback.format_exc())
        
        # ✅ 啟動背景線程
        thread = threading.Thread(target=run_test_in_background, daemon=True)
        thread.start()
        
        logger.info(f"✅ 批次測試已在背景啟動: batch_id={batch_id}, thread={thread.name}")
        
        # ✅ 立即返回（不等待測試完成）
        return Response({
            'success': True,
            'batch_id': batch_id,
            'message': '批量測試已啟動，請透過 SSE 追蹤進度'
        })
    
    @action(detail=False, methods=['get'], permission_classes=[], 
            renderer_classes=[ServerSentEventRenderer])
    def batch_test_progress(self, request):
        """
        獲取批量測試進度（Server-Sent Events 串流）
        
        GET /api/dify-benchmark/versions/batch_test_progress/?batch_id=xxx
        
        使用 Server-Sent Events (SSE) 推送即時進度更新。
        前端使用 EventSource API 連接此端點。
        
        ⚠️ 注意：此端點不需要認證（因為 EventSource API 無法傳遞認證資訊）
        安全性由 batch_id 的隨機性保證（類似 UUID）
        
        更新頻率：每 0.5 秒
        
        SSE 事件格式：
        data: {
            "batch_id": "batch_xxx",
            "status": "running",
            "progress": 45.5,
            "completed_tests": 5,
            "total_tests": 11,
            "current_version": "Dify 二階搜尋 v1.1",
            "current_test_case": "MIPI D-PHY 基本參數查詢",
            "estimated_remaining_time": 30,
            "versions": [...]
        }
        
        Returns:
            StreamingHttpResponse with SSE events
        """
        from django.http import StreamingHttpResponse
        from library.dify_benchmark.progress_tracker import progress_tracker
        import time
        
        batch_id = request.query_params.get('batch_id')
        if not batch_id:
            return Response({
                'success': False,
                'error': 'batch_id 參數為必填'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        def event_stream():
            """SSE 事件串流生成器"""
            try:
                # ✅ 立即發送初始連接確認事件（觸發 EventSource onopen）
                logger.info(f"SSE 連接已建立: batch_id={batch_id}")
                
                # ⚠️ 重要：先發送一個 data 事件來觸發 EventSource onopen
                # 註解（`: ...`）不會觸發 onopen，只有 `data:` 事件才會！
                initial_data = progress_tracker.get_progress(batch_id)
                if initial_data:
                    initial_sse = {
                        'batch_id': initial_data['batch_id'],
                        'batch_name': initial_data['batch_name'],
                        'status': initial_data['status'],
                        'progress': 0.0,
                        'completed_tests': initial_data['completed_tests'],
                        'total_tests': initial_data['total_tests'],
                        'message': 'SSE connection established'
                    }
                    yield f'data: {json.dumps(initial_sse)}\n\n'
                    logger.info(f"✅ 已發送初始 SSE 事件，觸發 onopen: batch_id={batch_id}")
                
                while True:
                    # 獲取進度資料
                    progress_data = progress_tracker.get_progress(batch_id)
                    
                    if not progress_data:
                        # ✅ 檢查批次是否已完成（從資料庫查詢）
                        try:
                            from api.models import DifyTestRun
                            
                            # 查詢該批次的所有測試執行記錄
                            test_runs = DifyTestRun.objects.filter(
                                batch_id=batch_id
                            ).order_by('-created_at')
                            
                            if test_runs.exists():
                                # 檢查所有測試是否都已完成（completed_at 不為 None）
                                all_completed = all(tr.completed_at is not None for tr in test_runs)
                                
                                if all_completed:
                                    # 批次已完成，計算統計資料
                                    total_tests = test_runs.count()
                                    avg_score = sum(tr.average_score or 0 for tr in test_runs) / total_tests
                                    avg_pass_rate = sum(tr.pass_rate or 0 for tr in test_runs) / total_tests
                                    
                                    # 建構版本資料
                                    versions_data = []
                                    for tr in test_runs:
                                        versions_data.append({
                                            'version_id': tr.version.id,
                                            'version_name': tr.version.version_name,
                                            'test_run_id': tr.id,
                                            'status': 'completed',
                                            'progress': 100.0,
                                            'passed_tests': tr.passed_cases,
                                            'failed_tests': tr.failed_cases,
                                            'total_tests': tr.total_test_cases,
                                            'average_score': round(tr.average_score or 0, 2),
                                            'pass_rate': round(tr.pass_rate or 0, 2)
                                        })
                                    
                                    final_data = {
                                        'batch_id': batch_id,
                                        'status': 'completed',
                                        'progress': 100.0,
                                        'completed_tests': total_tests,
                                        'total_tests': total_tests,
                                        'average_score': round(avg_score, 2),
                                        'pass_rate': round(avg_pass_rate, 2),
                                        'message': '測試已完成（從資料庫恢復）',
                                        'versions': versions_data
                                    }
                                    yield f'data: {json.dumps(final_data)}\n\n'
                                    logger.info(f"✅ 從資料庫恢復完成狀態: batch_id={batch_id}, 版本數={total_tests}")
                                    break
                                else:
                                    # 批次還在執行中，但記憶體丟失
                                    logger.warning(f"⚠️ 批次正在執行但記憶體丟失: batch_id={batch_id}")
                                    yield f'data: {json.dumps({"error": "Progress lost due to server restart"})}\n\n'
                                    break
                            else:
                                # 批次確實不存在
                                logger.warning(f"⚠️ 批次不存在於內存和資料庫: batch_id={batch_id}")
                                yield f'data: {json.dumps({"error": "Batch not found"})}\n\n'
                                break
                        
                        except Exception as e:
                            logger.error(f"❌ 資料庫查詢異常: {str(e)}", exc_info=True)
                            yield f'data: {json.dumps({"error": f"Database query failed: {str(e)}"})}\n\n'
                            break
                    
                    # 計算整體進度百分比
                    if progress_data['total_tests'] > 0:
                        progress_percentage = (
                            progress_data['completed_tests'] / progress_data['total_tests'] * 100
                        )
                        # ✅ 防止進度超過 100% (避免重複計數)
                        progress_percentage = min(progress_percentage, 100.0)
                    else:
                        progress_percentage = 0
                    
                    # ✅ 防止 completed_tests 超過 total_tests (避免重複計數)
                    completed_tests = min(progress_data['completed_tests'], progress_data['total_tests'])
                    
                    # 構建 SSE 資料
                    sse_data = {
                        'batch_id': progress_data['batch_id'],
                        'batch_name': progress_data['batch_name'],
                        'status': progress_data['status'],
                        'progress': round(progress_percentage, 2),
                        'completed_tests': completed_tests,  # ✅ 使用修正後的值
                        'total_tests': progress_data['total_tests'],
                        'failed_tests': progress_data['failed_tests'],
                        'current_version': progress_data['current_version_name'],
                        'current_test_case': progress_data['current_test_case'],
                        'estimated_remaining_time': progress_data['estimated_remaining_time'],
                        'start_time': progress_data['start_time'],
                        'last_update': progress_data['last_update'],
                        'versions': [
                            {
                                'version_id': v_data['version_id'],
                                'version_name': v_data['version_name'],
                                'total_tests': v_data['total_tests'],
                                'completed_tests': min(v_data['completed_tests'], v_data['total_tests']),  # ✅ 防止超過 total
                                'failed_tests': v_data['failed_tests'],
                                'status': v_data['status'],
                                'progress': round(
                                    min(  # ✅ 防止進度超過 100%
                                        (v_data['completed_tests'] / v_data['total_tests'] * 100)
                                        if v_data['total_tests'] > 0 else 0,
                                        100.0
                                    ),
                                    2
                                ),
                                'average_score': v_data.get('average_score'),
                                'pass_rate': v_data.get('pass_rate')
                            }
                            for v_data in progress_data['versions'].values()
                        ]
                    }
                    
                    # 發送 SSE 事件
                    yield f'data: {json.dumps(sse_data)}\n\n'
                    
                    # 如果測試完成，發送最後一次更新後結束
                    if progress_data['status'] in ['completed', 'error']:
                        logger.info(f"批次測試完成，關閉 SSE 連接: {batch_id}")
                        break
                    
                    # 等待 0.5 秒後再次查詢
                    time.sleep(0.5)
            
            except GeneratorExit:
                logger.info(f"客戶端關閉 SSE 連接: {batch_id}")
            except Exception as e:
                logger.error(f"SSE 串流錯誤: {str(e)}", exc_info=True)
                yield f'data: {json.dumps({"error": str(e)})}\n\n'
        
        # 創建 StreamingHttpResponse
        response = StreamingHttpResponse(
            event_stream(),
            content_type='text/event-stream'
        )
        
        # SSE 必要的 HTTP 標頭
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'  # 禁用 Nginx 緩衝
        
        return response


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
    pagination_class = None  # 禁用分頁，返回所有測試案例
    
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
