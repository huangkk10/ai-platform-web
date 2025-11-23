"""
Dify Batch Tester - 多版本對比測試器

用途：
1. 執行多個 Dify 版本的對比測試
2. 使用相同的測試案例對所有版本進行測試
3. 生成對比報告
4. 協調多個 DifyTestRunner

架構：
DifyBatchTester (orchestrator)
  ├── DifyTestRunner (version 1) → Test Results
  ├── DifyTestRunner (version 2) → Test Results
  └── DifyTestRunner (version N) → Test Results
    → Comparison Report
"""

import logging
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from django.db import transaction

from api.models import (
    DifyConfigVersion,
    DifyBenchmarkTestCase,
    DifyTestRun
)
from .dify_test_runner import DifyTestRunner

logger = logging.getLogger(__name__)


class DifyBatchTester:
    """
    多版本批量測試器
    
    負責協調多個 Dify 版本的測試執行和結果對比
    
    使用方式：
        tester = DifyBatchTester()
        
        results = tester.run_batch_test(
            version_ids=[1, 2, 3],
            test_case_ids=[1, 2, 3, 4, 5],
            batch_name="三階段搜尋對比測試"
        )
        
        # 返回：
        # {
        #     'batch_id': 'batch_xxx',
        #     'total_versions': 3,
        #     'total_cases': 5,
        #     'test_runs': [...],
        #     'comparison': {...}
        # }
    """
    
    def __init__(self, use_ai_evaluator: bool = False):
        """
        初始化批量測試器
        
        Args:
            use_ai_evaluator: 是否使用 AI 評分（預設 False）
        """
        self.use_ai_evaluator = use_ai_evaluator
        
        logger.info(
            f"DifyBatchTester 初始化完成: "
            f"evaluator={'AI' if use_ai_evaluator else 'Keyword'}"
        )
    
    def run_batch_test(
        self,
        version_ids: List[int],
        test_case_ids: Optional[List[int]] = None,
        batch_name: str = None,
        description: str = None
    ) -> Dict[str, Any]:
        """
        執行批量對比測試
        
        Args:
            version_ids: Dify 版本 ID 列表
            test_case_ids: 測試案例 ID 列表（可選，預設使用所有案例）
            batch_name: 批次名稱（可選）
            description: 批次描述（可選）
        
        Returns:
            測試結果字典：
            {
                'batch_id': str,
                'batch_name': str,
                'total_versions': int,
                'total_cases': int,
                'test_runs': List[Dict],
                'comparison': Dict
            }
        """
        try:
            # 1. 生成 Batch ID
            batch_id = self._generate_batch_id()
            
            # 2. 生成預設名稱
            if not batch_name:
                batch_name = f"批量測試 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            # 3. 載入版本
            versions = self._load_versions(version_ids)
            
            # 4. 載入測試案例
            test_cases = self._load_test_cases(test_case_ids)
            
            logger.info(
                f"開始批量測試: "
                f"batch_id={batch_id}, "
                f"versions={len(versions)}, "
                f"test_cases={len(test_cases)}"
            )
            
            # 5. 執行所有版本的測試
            test_runs = []
            
            for version in versions:
                try:
                    logger.info(f"測試版本: {version.version_name}")
                    
                    # 創建 Test Runner
                    runner = DifyTestRunner(
                        version=version,
                        use_ai_evaluator=self.use_ai_evaluator
                    )
                    
                    # 執行測試
                    test_run = runner.run_batch_tests(
                        test_cases=test_cases,
                        run_name=f"{batch_name} - {version.version_name}",
                        batch_id=batch_id,
                        description=description
                    )
                    
                    # 獲取測試摘要
                    summary = runner.get_test_summary(test_run)
                    test_runs.append(summary)
                    
                    logger.info(
                        f"版本測試完成: "
                        f"version={version.version_name}, "
                        f"pass_rate={summary['pass_rate']:.2f}%"
                    )
                    
                except Exception as e:
                    logger.error(f"版本測試失敗: {version.version_name}, 錯誤: {str(e)}", exc_info=True)
            
            # 6. 生成對比報告
            comparison = self._generate_comparison_report(test_runs)
            
            # 7. 返回結果
            result = {
                'batch_id': batch_id,
                'batch_name': batch_name,
                'total_versions': len(versions),
                'total_cases': len(test_cases),
                'test_runs': test_runs,
                'comparison': comparison,
                'completed_at': datetime.now().isoformat()
            }
            
            logger.info(
                f"批量測試完成: "
                f"batch_id={batch_id}, "
                f"versions={len(versions)}, "
                f"best_version={comparison.get('best_version', 'N/A')}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"批量測試失敗: {str(e)}", exc_info=True)
            raise
    
    def _generate_batch_id(self) -> str:
        """生成唯一的 Batch ID"""
        return f"batch_{uuid.uuid4().hex[:12]}"
    
    def _load_versions(self, version_ids: List[int]) -> List[DifyConfigVersion]:
        """載入 Dify 版本"""
        if not version_ids:
            raise ValueError("版本 ID 列表不能為空")
        
        versions = DifyConfigVersion.objects.filter(id__in=version_ids)
        
        if versions.count() != len(version_ids):
            found_ids = [v.id for v in versions]
            missing_ids = set(version_ids) - set(found_ids)
            raise ValueError(f"找不到以下版本 ID: {missing_ids}")
        
        return list(versions)
    
    def _load_test_cases(
        self,
        test_case_ids: Optional[List[int]] = None
    ) -> List[DifyBenchmarkTestCase]:
        """載入測試案例"""
        if test_case_ids:
            # 載入指定的測試案例
            test_cases = DifyBenchmarkTestCase.objects.filter(
                id__in=test_case_ids,
                is_active=True
            )
            
            if test_cases.count() != len(test_case_ids):
                found_ids = [tc.id for tc in test_cases]
                missing_ids = set(test_case_ids) - set(found_ids)
                raise ValueError(f"找不到以下測試案例 ID: {missing_ids}")
        else:
            # 載入所有啟用的測試案例
            test_cases = DifyBenchmarkTestCase.objects.filter(is_active=True)
        
        if not test_cases.exists():
            raise ValueError("沒有可用的測試案例")
        
        return list(test_cases)
    
    def _generate_comparison_report(
        self,
        test_runs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        生成版本對比報告
        
        Returns:
            {
                'best_version': str,
                'best_pass_rate': float,
                'best_average_score': float,
                'version_ranking': List[Dict],
                'statistics': Dict
            }
        """
        if not test_runs:
            return {}
        
        # 1. 按通過率排序
        sorted_by_pass_rate = sorted(
            test_runs,
            key=lambda x: x['pass_rate'],
            reverse=True
        )
        
        # 2. 按平均分數排序
        sorted_by_score = sorted(
            test_runs,
            key=lambda x: x['average_score'],
            reverse=True
        )
        
        # 3. 最佳版本（通過率優先）
        best_version = sorted_by_pass_rate[0]
        
        # 4. 版本排名（綜合評分）
        version_ranking = []
        for i, run in enumerate(sorted_by_pass_rate, 1):
            version_ranking.append({
                'rank': i,
                'version_name': run['version_name'],
                'pass_rate': run['pass_rate'],
                'average_score': run['average_score'],
                'passed_cases': run['passed_cases'],
                'failed_cases': run['failed_cases']
            })
        
        # 5. 統計資料
        total_runs = len(test_runs)
        avg_pass_rate = sum(r['pass_rate'] for r in test_runs) / total_runs
        avg_score = sum(r['average_score'] for r in test_runs) / total_runs
        
        statistics = {
            'total_versions_tested': total_runs,
            'average_pass_rate': round(avg_pass_rate, 2),
            'average_score': round(avg_score, 2),
            'pass_rate_range': {
                'min': sorted_by_pass_rate[-1]['pass_rate'],
                'max': sorted_by_pass_rate[0]['pass_rate']
            },
            'score_range': {
                'min': sorted_by_score[-1]['average_score'],
                'max': sorted_by_score[0]['average_score']
            }
        }
        
        return {
            'best_version': best_version['version_name'],
            'best_pass_rate': best_version['pass_rate'],
            'best_average_score': best_version['average_score'],
            'version_ranking': version_ranking,
            'statistics': statistics
        }
    
    def get_batch_history(
        self,
        batch_id: str
    ) -> Dict[str, Any]:
        """
        獲取批次測試歷史記錄
        
        Args:
            batch_id: 批次 ID
        
        Returns:
            歷史記錄字典
        """
        test_runs = DifyTestRun.objects.filter(batch_id=batch_id)
        
        if not test_runs.exists():
            return {
                'error': f'找不到批次 ID: {batch_id}'
            }
        
        runs_data = []
        for run in test_runs:
            runs_data.append({
                'run_id': run.id,
                'version_name': run.version.version_name,
                'total_cases': run.total_cases,
                'passed_cases': run.passed_cases,
                'failed_cases': run.failed_cases,
                'pass_rate': run.pass_rate,
                'average_score': run.average_score,
                'started_at': run.started_at.isoformat() if run.started_at else None,
                'completed_at': run.completed_at.isoformat() if run.completed_at else None
            })
        
        return {
            'batch_id': batch_id,
            'total_runs': len(runs_data),
            'runs': runs_data
        }
