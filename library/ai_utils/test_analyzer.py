#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試結果分析器模組
提供測試結果統計、分析和報告生成功能
"""

import json
import time
from typing import List, Dict, Any, Optional, Union
from collections import defaultdict, Counter
import statistics


class TestAnalyzer:
    """測試結果分析器"""
    
    def __init__(self):
        self.results = []
        self.metadata = {}
    
    def add_results(self, results: Union[List[Dict], Dict], test_name: str = None):
        """
        添加測試結果
        
        Args:
            results: 測試結果（可以是列表或單個結果）
            test_name: 測試名稱
        """
        if isinstance(results, dict):
            results = [results]
        
        for result in results:
            enhanced_result = {
                'test_name': test_name or 'Unknown Test',
                'timestamp': time.time(),
                **result
            }
            self.results.append(enhanced_result)
    
    def get_success_rate(self, test_name: str = None) -> float:
        """
        計算成功率
        
        Args:
            test_name: 測試名稱（如果指定，只計算該測試的成功率）
            
        Returns:
            float: 成功率（0-1）
        """
        filtered_results = self._filter_results(test_name)
        if not filtered_results:
            return 0.0
        
        success_count = sum(1 for r in filtered_results if r.get('success', False))
        return success_count / len(filtered_results)
    
    def get_average_response_time(self, test_name: str = None, successful_only: bool = True) -> float:
        """
        計算平均回應時間
        
        Args:
            test_name: 測試名稱
            successful_only: 是否只計算成功的請求
            
        Returns:
            float: 平均回應時間（秒）
        """
        filtered_results = self._filter_results(test_name)
        
        if successful_only:
            response_times = [r.get('response_time', 0) for r in filtered_results 
                            if r.get('success', False) and r.get('response_time', 0) > 0]
        else:
            response_times = [r.get('response_time', 0) for r in filtered_results 
                            if r.get('response_time', 0) > 0]
        
        return statistics.mean(response_times) if response_times else 0.0
    
    def get_response_time_stats(self, test_name: str = None) -> Dict[str, float]:
        """
        獲取回應時間統計
        
        Args:
            test_name: 測試名稱
            
        Returns:
            Dict: 包含最小值、最大值、平均值、中位數的統計
        """
        filtered_results = self._filter_results(test_name)
        response_times = [r.get('response_time', 0) for r in filtered_results 
                        if r.get('success', False) and r.get('response_time', 0) > 0]
        
        if not response_times:
            return {
                'min': 0.0, 'max': 0.0, 'mean': 0.0, 
                'median': 0.0, 'std_dev': 0.0
            }
        
        return {
            'min': min(response_times),
            'max': max(response_times),
            'mean': statistics.mean(response_times),
            'median': statistics.median(response_times),
            'std_dev': statistics.stdev(response_times) if len(response_times) > 1 else 0.0
        }
    
    def get_error_analysis(self, test_name: str = None) -> Dict[str, Any]:
        """
        分析錯誤模式
        
        Args:
            test_name: 測試名稱
            
        Returns:
            Dict: 錯誤分析結果
        """
        filtered_results = self._filter_results(test_name)
        failed_results = [r for r in filtered_results if not r.get('success', False)]
        
        if not failed_results:
            return {
                'total_failures': 0,
                'error_types': {},
                'common_errors': []
            }
        
        # 統計錯誤類型
        error_counter = Counter()
        status_code_counter = Counter()
        
        for result in failed_results:
            error = result.get('error', 'Unknown Error')
            error_counter[error] += 1
            
            # 統計 HTTP 狀態碼
            if 'HTTP' in error:
                try:
                    status_code = error.split('HTTP ')[1].split(':')[0]
                    status_code_counter[status_code] += 1
                except:
                    pass
        
        return {
            'total_failures': len(failed_results),
            'failure_rate': len(failed_results) / len(filtered_results),
            'error_types': dict(error_counter),
            'status_codes': dict(status_code_counter),
            'common_errors': error_counter.most_common(5)
        }
    
    def get_knowledge_usage_analysis(self, test_name: str = None) -> Dict[str, Any]:
        """
        分析知識庫使用情況
        
        Args:
            test_name: 測試名稱
            
        Returns:
            Dict: 知識庫使用分析結果
        """
        filtered_results = self._filter_results(test_name)
        knowledge_results = [r for r in filtered_results if 'knowledge_used' in r]
        
        if not knowledge_results:
            return {
                'total_tests': 0,
                'knowledge_usage_rate': 0.0,
                'keyword_stats': {}
            }
        
        knowledge_used_count = sum(1 for r in knowledge_results if r.get('knowledge_used', False))
        
        # 統計關鍵詞使用
        all_keywords = []
        for result in knowledge_results:
            matched_keywords = result.get('matched_keywords', [])
            all_keywords.extend(matched_keywords)
        
        keyword_counter = Counter(all_keywords)
        
        return {
            'total_tests': len(knowledge_results),
            'knowledge_usage_rate': knowledge_used_count / len(knowledge_results),
            'knowledge_used_count': knowledge_used_count,
            'keyword_stats': dict(keyword_counter),
            'most_matched_keywords': keyword_counter.most_common(10)
        }
    
    def get_conversation_analysis(self, test_name: str = None) -> Dict[str, Any]:
        """
        分析對話相關指標
        
        Args:
            test_name: 測試名稱
            
        Returns:
            Dict: 對話分析結果
        """
        filtered_results = self._filter_results(test_name)
        conversation_results = [r for r in filtered_results if 'conversation_id' in r]
        
        if not conversation_results:
            return {
                'total_conversations': 0,
                'context_maintained_rate': 0.0
            }
        
        # 統計對話 ID
        conversation_ids = [r.get('conversation_id', '') for r in conversation_results 
                          if r.get('conversation_id')]
        unique_conversations = len(set(conversation_ids))
        
        # 統計上下文維持情況
        context_maintained = sum(1 for r in conversation_results 
                               if r.get('conversation_id') and r.get('success', False))
        
        return {
            'total_conversations': len(conversation_results),
            'unique_conversations': unique_conversations,
            'context_maintained_rate': context_maintained / len(conversation_results) if conversation_results else 0.0,
            'average_turns_per_conversation': len(conversation_results) / unique_conversations if unique_conversations > 0 else 0
        }
    
    def generate_summary_report(self, test_name: str = None) -> Dict[str, Any]:
        """
        生成綜合測試報告
        
        Args:
            test_name: 測試名稱
            
        Returns:
            Dict: 綜合報告
        """
        filtered_results = self._filter_results(test_name)
        
        if not filtered_results:
            return {
                'test_name': test_name or 'All Tests',
                'total_tests': 0,
                'message': 'No test results available'
            }
        
        # 基本統計
        total_tests = len(filtered_results)
        successful_tests = sum(1 for r in filtered_results if r.get('success', False))
        success_rate = successful_tests / total_tests
        
        # 時間分析
        response_time_stats = self.get_response_time_stats(test_name)
        
        # 錯誤分析
        error_analysis = self.get_error_analysis(test_name)
        
        # 知識庫分析
        knowledge_analysis = self.get_knowledge_usage_analysis(test_name)
        
        # 對話分析
        conversation_analysis = self.get_conversation_analysis(test_name)
        
        # 測試類型分布
        test_types = Counter(r.get('test_name', 'Unknown') for r in filtered_results)
        
        return {
            'test_name': test_name or 'All Tests',
            'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'basic_stats': {
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'failed_tests': total_tests - successful_tests,
                'success_rate': success_rate
            },
            'performance_stats': response_time_stats,
            'error_analysis': error_analysis,
            'knowledge_analysis': knowledge_analysis,
            'conversation_analysis': conversation_analysis,
            'test_distribution': dict(test_types)
        }
    
    def print_summary_report(self, test_name: str = None, detailed: bool = True):
        """
        打印測試總結報告
        
        Args:
            test_name: 測試名稱
            detailed: 是否顯示詳細信息
        """
        report = self.generate_summary_report(test_name)
        
        print("\n" + "="*60)
        print(f"📊 測試總結報告 - {report['test_name']}")
        print("="*60)
        print(f"🕒 生成時間: {report['generated_at']}")
        
        # 基本統計
        basic = report['basic_stats']
        print(f"\n📈 基本統計:")
        print(f"  總測試數: {basic['total_tests']}")
        print(f"  成功數: {basic['successful_tests']}")
        print(f"  失敗數: {basic['failed_tests']}")
        print(f"  成功率: {basic['success_rate']:.1%}")
        
        # 效能統計
        if detailed:
            perf = report['performance_stats']
            if perf['mean'] > 0:
                print(f"\n⏱️ 效能統計:")
                print(f"  平均回應時間: {perf['mean']:.2f}s")
                print(f"  最快回應: {perf['min']:.2f}s")
                print(f"  最慢回應: {perf['max']:.2f}s")
                print(f"  中位數: {perf['median']:.2f}s")
                if perf['std_dev'] > 0:
                    print(f"  標準差: {perf['std_dev']:.2f}s")
        
        # 錯誤分析
        error = report['error_analysis']
        if error['total_failures'] > 0:
            print(f"\n❌ 錯誤分析:")
            print(f"  失敗總數: {error['total_failures']}")
            print(f"  失敗率: {error['failure_rate']:.1%}")
            
            if detailed and error['common_errors']:
                print(f"  常見錯誤:")
                for error_msg, count in error['common_errors'][:3]:
                    print(f"    • {error_msg}: {count} 次")
        
        # 知識庫分析
        knowledge = report['knowledge_analysis']
        if knowledge['total_tests'] > 0:
            print(f"\n📚 知識庫使用:")
            print(f"  知識庫使用率: {knowledge['knowledge_usage_rate']:.1%}")
            
            if detailed and knowledge['most_matched_keywords']:
                print(f"  常用關鍵詞:")
                for keyword, count in knowledge['most_matched_keywords'][:5]:
                    print(f"    • {keyword}: {count} 次")
        
        # 對話分析
        conv = report['conversation_analysis']
        if conv['total_conversations'] > 0:
            print(f"\n💬 對話分析:")
            print(f"  對話數: {conv['unique_conversations']}")
            print(f"  上下文維持率: {conv['context_maintained_rate']:.1%}")
            if conv['average_turns_per_conversation'] > 0:
                print(f"  平均對話輪數: {conv['average_turns_per_conversation']:.1f}")
        
        print("\n" + "="*60)
    
    def export_to_json(self, filename: str, test_name: str = None):
        """
        導出測試結果為 JSON 文件
        
        Args:
            filename: 文件名
            test_name: 測試名稱
        """
        report = self.generate_summary_report(test_name)
        filtered_results = self._filter_results(test_name)
        
        export_data = {
            'summary': report,
            'detailed_results': filtered_results,
            'export_time': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        print(f"📁 測試結果已導出到: {filename}")
    
    def _filter_results(self, test_name: str = None) -> List[Dict]:
        """過濾指定測試名稱的結果"""
        if test_name is None:
            return self.results
        return [r for r in self.results if r.get('test_name') == test_name]
    
    def clear_results(self):
        """清空所有測試結果"""
        self.results.clear()
        self.metadata.clear()
    
    def get_test_names(self) -> List[str]:
        """獲取所有測試名稱"""
        return list(set(r.get('test_name', 'Unknown') for r in self.results))


# 便利函數
def analyze_results(results: Union[List[Dict], Dict], test_name: str = None, 
                   print_report: bool = True, detailed: bool = True) -> TestAnalyzer:
    """
    快速分析測試結果
    
    Args:
        results: 測試結果
        test_name: 測試名稱
        print_report: 是否打印報告
        detailed: 是否顯示詳細信息
        
    Returns:
        TestAnalyzer: 分析器實例
    """
    analyzer = TestAnalyzer()
    analyzer.add_results(results, test_name)
    
    if print_report:
        analyzer.print_summary_report(test_name, detailed)
    
    return analyzer


def quick_stats(results: List[Dict]) -> Dict[str, Any]:
    """
    快速統計測試結果
    
    Args:
        results: 測試結果列表
        
    Returns:
        Dict: 基本統計信息
    """
    if not results:
        return {'total': 0, 'success': 0, 'failure': 0, 'success_rate': 0.0}
    
    total = len(results)
    success = sum(1 for r in results if r.get('success', False))
    failure = total - success
    success_rate = success / total
    
    return {
        'total': total,
        'success': success,
        'failure': failure,
        'success_rate': success_rate
    }