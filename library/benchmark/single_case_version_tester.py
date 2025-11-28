"""
單一測試案例版本比較測試器 (Single Case Version Tester)
=======================================================

用於對單一測試案例執行多個搜尋版本的比較測試。

使用場景：
- 快速測試單一問題在不同版本的表現
- 診斷特定問題的最佳搜尋策略
- 驗證關鍵字調整效果

時間優勢：
- 單問題 × 5 版本 = 20-30 秒
- 完整批量測試 = 40-50 分鐘
- 節省 99.2% 時間
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from decimal import Decimal

logger = logging.getLogger(__name__)


class SingleCaseVersionTester:
    """單一測試案例版本比較測試器"""
    
    def __init__(self, test_case_id: int, version_ids: Optional[List[int]] = None, verbose: bool = False):
        """
        初始化測試器
        
        Args:
            test_case_id: 測試案例 ID
            version_ids: 要測試的版本 ID 列表（None = 測試所有啟用版本）
            verbose: 是否輸出詳細日誌
        """
        self.test_case_id = test_case_id
        self.version_ids = version_ids
        self.verbose = verbose
        self.test_case = None
        self.versions = []
    
    def run_comparison(self) -> Dict[str, Any]:
        """
        執行版本比較測試
        
        Returns:
            Dict: 測試結果
                {
                    'success': bool,
                    'test_case': {...},
                    'results': [
                        {
                            'version_id': int,
                            'version_name': str,
                            'metrics': {
                                'precision': float,
                                'recall': float,
                                'f1_score': float
                            },
                            'response_time': float,
                            'status': 'success' | 'error',
                            'error_message': str (if error)
                        },
                        ...
                    ],
                    'summary': {
                        'total_versions': int,
                        'successful_tests': int,
                        'failed_tests': int,
                        'best_version': {...},
                        'avg_response_time': float,
                        'test_run_ids': [int, ...]
                    }
                }
        """
        try:
            print(f"\n{'='*80}")
            print(f"🚀 開始版本比較測試")
            print(f"{'='*80}")
            
            # 1. 準備測試案例和版本
            print(f"📋 準備測試案例 (ID: {self.test_case_id})...")
            self._prepare_test_case()
            
            print(f"📋 準備測試版本...")
            self._prepare_versions()
            
            if not self.test_case:
                print(f"❌ 錯誤: 找不到測試案例 ID: {self.test_case_id}")
                return {
                    'success': False,
                    'error': f'找不到測試案例 ID: {self.test_case_id}'
                }
            
            if not self.versions:
                print(f"❌ 錯誤: 沒有可用的測試版本")
                return {
                    'success': False,
                    'error': '沒有可用的測試版本'
                }
            
            print(f"✅ 測試案例: {self.test_case.question[:80]}...")
            print(f"✅ 共 {len(self.versions)} 個版本: {[v.version_name for v in self.versions]}")
            print(f"✅ 預期關鍵字: {self.test_case.expected_keywords}")
            print(f"✅ 難度等級: {self.test_case.difficulty_level}")
            
            self._log(f"開始測試問題: {self.test_case.question[:50]}...")
            self._log(f"測試 {len(self.versions)} 個版本")
            
            # 2. 執行每個版本的測試
            results = []
            test_run_ids = []
            start_time = datetime.now()
            
            for idx, version in enumerate(self.versions, 1):
                print(f"\n{'─'*80}")
                print(f"📊 進度: [{idx}/{len(self.versions)}]")
                print(f"{'─'*80}")
                self._log(f"[{idx}/{len(self.versions)}] 測試版本: {version.version_name}")
                
                try:
                    result = self._test_single_version(version)
                    results.append(result)
                    
                    if result.get('test_run_id'):
                        test_run_ids.append(result['test_run_id'])
                    
                    self._log(f"  ✅ 完成 - F1: {result['metrics']['f1_score']:.2%}")
                    
                except Exception as e:
                    error_msg = str(e)
                    print(f"❌ 版本 {version.version_name} 測試失敗!")
                    print(f"   錯誤訊息: {error_msg}")
                    import traceback
                    print(f"   完整堆疊:")
                    traceback.print_exc()
                    
                    self._log(f"  ❌ 失敗: {error_msg}", level='error')
                    results.append({
                        'version_id': version.id,
                        'version_name': version.version_name,
                        'status': 'error',
                        'error_message': error_msg,
                        'metrics': {
                            'precision': 0.0,
                            'recall': 0.0,
                            'f1_score': 0.0
                        },
                        'response_time': 0.0
                    })
            
            total_time = (datetime.now() - start_time).total_seconds()
            
            # 3. 生成摘要
            summary = self._generate_summary(results, total_time, test_run_ids)
            
            self._log(f"測試完成！總時間: {total_time:.2f} 秒")
            
            return {
                'success': True,
                'test_case': {
                    'id': self.test_case.id,
                    'question': self.test_case.question,
                    'difficulty_level': self.test_case.difficulty_level,
                    'expected_keywords': self.test_case.expected_keywords
                },
                'results': results,
                'summary': summary
            }
            
        except Exception as e:
            error_msg = f"版本比較測試失敗: {str(e)}"
            self._log(error_msg, level='error')
            return {
                'success': False,
                'error': error_msg
            }
    
    def _prepare_test_case(self):
        """準備測試案例"""
        from api.models import BenchmarkTestCase
        
        try:
            self.test_case = BenchmarkTestCase.objects.get(
                id=self.test_case_id,
                is_active=True
            )
        except BenchmarkTestCase.DoesNotExist:
            self._log(f"測試案例不存在或已停用: {self.test_case_id}", level='warning')
            self.test_case = None
    
    def _prepare_versions(self):
        """準備要測試的版本"""
        from api.models import SearchAlgorithmVersion
        
        if self.version_ids:
            # 測試指定的版本
            self.versions = list(
                SearchAlgorithmVersion.objects.filter(
                    id__in=self.version_ids,
                    is_active=True
                ).order_by('id')
            )
        else:
            # 測試所有啟用的版本
            self.versions = list(
                SearchAlgorithmVersion.objects.filter(
                    is_active=True
                ).order_by('id')
            )
    
    def _test_single_version(self, version) -> Dict[str, Any]:
        """
        測試單一版本
        
        Args:
            version: SearchAlgorithmVersion 實例
            
        Returns:
            Dict: 測試結果
        """
        from api.models import BenchmarkTestRun, BenchmarkTestResult
        from library.protocol_guide.search_service import ProtocolGuideSearchService
        from library.benchmark.search_strategies import get_strategy
        
        start_time = datetime.now()
        
        print(f"\n{'='*80}")
        print(f"🧪 開始測試版本：{version.version_name} (ID: {version.id})")
        print(f"{'='*80}")
        
        # 1. 獲取策略類型（優先使用 parameters 中的 strategy，其次使用 algorithm_type）
        strategy_type = version.parameters.get('strategy') or version.algorithm_type
        print(f"📋 策略類型: {strategy_type}")
        print(f"📋 algorithm_type: {version.algorithm_type}")
        print(f"📋 原始 parameters: {version.parameters}")
        
        if not strategy_type:
            raise ValueError(f"版本 {version.version_name} 缺少策略類型配置")
        
        # 2. 準備策略參數（移除 'strategy' 鍵，避免傳入策略類的 __init__）
        strategy_params = {k: v for k, v in version.parameters.items() if k != 'strategy'}
        print(f"📋 過濾後的策略參數: {strategy_params}")
        
        # 3. 獲取搜尋策略（⚠️ 策略類的 __init__ 只接受 search_service，其他參數傳給 execute()）
        print(f"🔧 正在初始化策略 {strategy_type}...")
        try:
            strategy = get_strategy(
                strategy_type,
                ProtocolGuideSearchService()
                # ⚠️ 不要在這裡傳入其他參數！
            )
            print(f"✅ 策略初始化成功: {type(strategy).__name__}")
        except Exception as e:
            print(f"❌ 策略初始化失敗: {str(e)}")
            raise
        
        # 4. 執行搜尋（⚠️ 參數傳給 execute() 而非 __init__）
        print(f"🔍 執行搜尋查詢: {self.test_case.question[:50]}...")
        print(f"🔍 搜尋參數: {strategy_params}")
        try:
            search_results = strategy.execute(
                query=self.test_case.question,
                limit=10,
                **strategy_params  # ⚠️ 參數在這裡傳入！
            )
            print(f"✅ 搜尋完成，找到 {len(search_results)} 個結果")
        except Exception as e:
            print(f"❌ 搜尋執行失敗: {str(e)}")
            raise
        
        # 5. 評估結果
        print(f"📊 開始評估搜尋結果...")
        try:
            metrics = self._evaluate_results(search_results)
            print(f"✅ 評估完成:")
            print(f"   - Precision: {metrics['precision']:.2%}")
            print(f"   - Recall: {metrics['recall']:.2%}")
            print(f"   - F1 Score: {metrics['f1_score']:.2%}")
        except Exception as e:
            print(f"❌ 評估失敗: {str(e)}")
            raise
        
        response_time = (datetime.now() - start_time).total_seconds()
        print(f"⏱️ 回應時間: {response_time:.2f} 秒")
        
        # 6. 儲存結果到資料庫
        print(f"💾 正在儲存測試結果到資料庫...")
        try:
            test_run = self._save_test_result(
                version=version,
                metrics=metrics,
                response_time=response_time,
                search_results=search_results
            )
            print(f"✅ 結果已儲存 (TestRun ID: {test_run.id})")
        except Exception as e:
            print(f"❌ 儲存失敗: {str(e)}")
            raise
        
        print(f"{'='*80}")
        print(f"✅ 版本 {version.version_name} 測試完成!")
        print(f"{'='*80}\n")
        
        return {
            'version_id': version.id,
            'version_name': version.version_name,
            'strategy_type': strategy_type,
            'metrics': {
                'precision': float(metrics['precision']),
                'recall': float(metrics['recall']),
                'f1_score': float(metrics['f1_score'])
            },
            'response_time': response_time,
            'matched_keywords': metrics.get('matched_keywords', []),
            'total_keywords': metrics.get('total_keywords', 0),
            'status': 'success',
            'test_run_id': test_run.id if test_run else None
        }
    
    def _evaluate_results(self, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        評估搜尋結果
        
        使用答案關鍵字進行評估，計算 P/R/F1
        
        Args:
            search_results: 搜尋結果列表
            
        Returns:
            Dict: 評估指標
                {
                    'precision': Decimal,
                    'recall': Decimal,
                    'f1_score': Decimal,
                    'matched_keywords': List[str],
                    'total_keywords': int
                }
        """
        if not search_results:
            return {
                'precision': Decimal('0'),
                'recall': Decimal('0'),
                'f1_score': Decimal('0'),
                'matched_keywords': [],
                'total_keywords': len(self.test_case.expected_keywords) if self.test_case.expected_keywords else 0
            }
        
        # 獲取答案關鍵字
        answer_keywords = self.test_case.expected_keywords or []
        if not answer_keywords:
            # 如果沒有關鍵字，無法評估
            return {
                'precision': Decimal('0'),
                'recall': Decimal('0'),
                'f1_score': Decimal('0'),
                'matched_keywords': [],
                'total_keywords': 0
            }
        
        # 提取搜尋結果的內容
        result_texts = []
        for result in search_results:
            text = ""
            if 'title' in result:
                text += result['title'] + " "
            if 'content' in result:
                text += result['content']
            result_texts.append(text)
        
        combined_text = " ".join(result_texts)
        
        # 計算匹配的關鍵字
        matched_keywords = []
        for keyword in answer_keywords:
            if keyword.lower() in combined_text.lower():
                matched_keywords.append(keyword)
        
        # 計算指標
        total_keywords = len(answer_keywords)
        matched_count = len(matched_keywords)
        
        # Recall = 匹配的關鍵字數 / 總關鍵字數
        recall = Decimal(matched_count) / Decimal(total_keywords) if total_keywords > 0 else Decimal('0')
        
        # Precision = 匹配的關鍵字數 / (搜尋結果數 × 總關鍵字數)
        # 這裡使用簡化版本：如果匹配到關鍵字，precision 就是 recall
        # 因為我們假設每個搜尋結果都是相關的
        precision = recall
        
        # F1 Score
        if precision + recall > 0:
            f1_score = (2 * precision * recall) / (precision + recall)
        else:
            f1_score = Decimal('0')
        
        return {
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'matched_keywords': matched_keywords,
            'total_keywords': total_keywords
        }
    
    def _save_test_result(
        self,
        version,
        metrics: Dict[str, Any],
        response_time: float,
        search_results: List[Dict[str, Any]]
    ):
        """
        儲存測試結果到資料庫
        
        Args:
            version: SearchAlgorithmVersion 實例
            metrics: 評估指標
            response_time: 回應時間（秒）
            search_results: 搜尋結果
            
        Returns:
            BenchmarkTestRun: 測試運行記錄
        """
        from api.models import BenchmarkTestRun, BenchmarkTestResult
        
        try:
            # ✅ 創建測試運行記錄（使用正確的欄位）
            test_run = BenchmarkTestRun.objects.create(
                version=version,  # ⚠️ 必填：關聯的版本
                run_name=f"單案例測試 - {self.test_case.question[:30]}...",
                run_type='single_case_comparison',  # ⚠️ 正確的欄位名稱
                total_test_cases=1,
                completed_test_cases=1,
                status='completed',
                # 指標數據
                avg_precision=metrics['precision'],
                avg_recall=metrics['recall'],
                avg_f1_score=metrics['f1_score'],
                overall_score=metrics['f1_score'],  # 單案例的 overall_score = f1_score
                avg_response_time=Decimal(str(response_time))
            )
            
            # ✅ 創建測試結果記錄（使用正確的欄位名稱）
            matched_keywords = metrics.get('matched_keywords', [])
            total_keywords = metrics.get('total_keywords', 0)
            
            BenchmarkTestResult.objects.create(
                test_run=test_run,
                test_case=self.test_case,
                search_query=self.test_case.question,  # ⚠️ 必填欄位
                returned_document_ids=[r.get('id', 0) for r in search_results[:10]],
                returned_document_scores=[float(r.get('score', 0)) for r in search_results[:10]],
                # 評分指標（使用正確的欄位名稱）
                precision_score=metrics['precision'],  # ⚠️ precision_score 不是 precision
                recall_score=metrics['recall'],        # ⚠️ recall_score 不是 recall
                f1_score=metrics['f1_score'],
                response_time=Decimal(str(response_time * 1000)),  # ⚠️ 單位是毫秒
                # 混淆矩陣（可選）
                true_positives=len(matched_keywords),
                false_negatives=total_keywords - len(matched_keywords),
                # 結果判定
                is_passed=metrics['f1_score'] > Decimal('0.5'),
                pass_reason=f"匹配 {len(matched_keywords)}/{total_keywords} 個關鍵字",
                # 詳細結果
                detailed_results={
                    'search_results': search_results[:5],  # 只儲存前 5 個結果
                    'matched_keywords': matched_keywords,
                    'total_keywords': total_keywords,
                    'version_name': version.version_name,
                    'strategy_type': version.parameters.get('strategy', version.algorithm_type)
                }
            )
            
            return test_run
            
        except Exception as e:
            self._log(f"儲存測試結果失敗: {str(e)}", level='error')
            return None
    
    def _generate_summary(
        self,
        results: List[Dict[str, Any]],
        total_time: float,
        test_run_ids: List[int]
    ) -> Dict[str, Any]:
        """
        生成測試摘要
        
        Args:
            results: 所有版本的測試結果
            total_time: 總執行時間（秒）
            test_run_ids: 測試運行 ID 列表
            
        Returns:
            Dict: 測試摘要
        """
        successful_results = [r for r in results if r.get('status') == 'success']
        failed_results = [r for r in results if r.get('status') == 'error']
        
        # 找出最佳版本（按 F1 Score 排序）
        best_version = None
        if successful_results:
            best_version = max(
                successful_results,
                key=lambda x: x['metrics']['f1_score']
            )
        
        # 計算平均回應時間
        avg_response_time = 0.0
        if successful_results:
            avg_response_time = sum(
                r['response_time'] for r in successful_results
            ) / len(successful_results)
        
        return {
            'total_versions': len(results),
            'successful_tests': len(successful_results),
            'failed_tests': len(failed_results),
            'best_version': best_version,
            'avg_response_time': round(avg_response_time, 2),
            'total_execution_time': round(total_time, 2),
            'test_run_ids': test_run_ids
        }
    
    def _log(self, message: str, level: str = 'info'):
        """輸出日誌"""
        if self.verbose:
            print(f"[SingleCaseVersionTester] {message}")
        
        log_func = getattr(logger, level, logger.info)
        log_func(f"[SingleCaseVersionTester] {message}")


# 便利函數

def test_single_case_all_versions(test_case_id: int, verbose: bool = False) -> Dict[str, Any]:
    """
    測試單一案例的所有版本
    
    Args:
        test_case_id: 測試案例 ID
        verbose: 是否輸出詳細日誌
        
    Returns:
        Dict: 測試結果
    """
    tester = SingleCaseVersionTester(test_case_id, version_ids=None, verbose=verbose)
    return tester.run_comparison()


def test_single_case_selected_versions(
    test_case_id: int,
    version_ids: List[int],
    verbose: bool = False
) -> Dict[str, Any]:
    """
    測試單一案例的指定版本
    
    Args:
        test_case_id: 測試案例 ID
        version_ids: 版本 ID 列表
        verbose: 是否輸出詳細日誌
        
    Returns:
        Dict: 測試結果
    """
    tester = SingleCaseVersionTester(test_case_id, version_ids=version_ids, verbose=verbose)
    return tester.run_comparison()
