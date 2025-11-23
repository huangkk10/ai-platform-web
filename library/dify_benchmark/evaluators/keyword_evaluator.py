"""
Keyword Evaluator - 100% 關鍵字匹配評分

評分原則：
1. 完全基於關鍵字匹配（不使用 AI）
2. 匹配度 = (匹配的關鍵字數 / 總關鍵字數) * 100
3. 及格標準：60 分（即 60% 關鍵字匹配）
4. 大小寫不敏感
5. 支援中英文關鍵字
"""

import json
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class KeywordEvaluator:
    """
    100% 關鍵字匹配評分器
    
    使用方式：
        evaluator = KeywordEvaluator()
        result = evaluator.evaluate(
            question="什麼是 I3C?",
            expected_answer="I3C 是一種通訊協定...",
            actual_answer="I3C 是 MIPI 定義的新一代通訊協定...",
            keywords=["I3C", "MIPI", "通訊協定", "主從架構"]
        )
        
        # 返回：
        # {
        #     'score': 75,
        #     'is_passed': True,
        #     'matched_keywords': ['I3C', 'MIPI', '通訊協定'],
        #     'missing_keywords': ['主從架構'],
        #     'match_details': {...}
        # }
    """
    
    # 及格標準（可配置）
    PASSING_SCORE = 60
    
    def __init__(self, passing_score: int = None):
        """
        初始化評分器
        
        Args:
            passing_score: 自定義及格分數（預設 60）
        """
        self.passing_score = passing_score or self.PASSING_SCORE
    
    def evaluate(
        self,
        question: str,
        expected_answer: str,
        actual_answer: str,
        keywords: List[str]
    ) -> Dict[str, Any]:
        """
        執行關鍵字評分
        
        Args:
            question: 測試問題（用於日誌記錄）
            expected_answer: 預期答案（用於參考，不直接用於評分）
            actual_answer: Dify 實際回答
            keywords: 關鍵字列表（JSON 陣列）
        
        Returns:
            評分結果字典：
            {
                'score': int (0-100),
                'is_passed': bool,
                'matched_keywords': List[str],
                'missing_keywords': List[str],
                'match_details': Dict[str, bool]
            }
        """
        try:
            # 1. 驗證輸入
            if not actual_answer or not actual_answer.strip():
                logger.warning(f"實際回答為空: question={question[:50]}")
                return self._create_empty_result(keywords)
            
            if not keywords or len(keywords) == 0:
                logger.warning(f"關鍵字列表為空: question={question[:50]}")
                return {
                    'score': 100,  # 沒有關鍵字視為全部通過
                    'is_passed': True,
                    'matched_keywords': [],
                    'missing_keywords': [],
                    'match_details': {}
                }
            
            # 2. 正規化文本（轉小寫，移除空白）
            normalized_answer = actual_answer.lower().strip()
            
            # 3. 檢查每個關鍵字
            matched_keywords = []
            missing_keywords = []
            match_details = {}
            
            for keyword in keywords:
                if not keyword or not keyword.strip():
                    continue
                
                normalized_keyword = keyword.lower().strip()
                is_matched = normalized_keyword in normalized_answer
                
                match_details[keyword] = is_matched
                
                if is_matched:
                    matched_keywords.append(keyword)
                else:
                    missing_keywords.append(keyword)
            
            # 4. 計算分數
            total_keywords = len(keywords)
            matched_count = len(matched_keywords)
            
            if total_keywords > 0:
                score = int((matched_count / total_keywords) * 100)
            else:
                score = 100
            
            # 5. 判斷是否及格
            is_passed = score >= self.passing_score
            
            # 6. 記錄評分結果
            logger.info(
                f"關鍵字評分完成: "
                f"score={score}, "
                f"matched={matched_count}/{total_keywords}, "
                f"passed={'✅' if is_passed else '❌'}"
            )
            
            return {
                'score': score,
                'is_passed': is_passed,
                'matched_keywords': matched_keywords,
                'missing_keywords': missing_keywords,
                'match_details': match_details
            }
            
        except Exception as e:
            logger.error(f"關鍵字評分失敗: {str(e)}", exc_info=True)
            return self._create_error_result(keywords, str(e))
    
    def _create_empty_result(self, keywords: List[str]) -> Dict[str, Any]:
        """創建空回答的評分結果（0 分）"""
        return {
            'score': 0,
            'is_passed': False,
            'matched_keywords': [],
            'missing_keywords': keywords,
            'match_details': {kw: False for kw in keywords}
        }
    
    def _create_error_result(self, keywords: List[str], error_msg: str) -> Dict[str, Any]:
        """創建錯誤的評分結果（0 分）"""
        return {
            'score': 0,
            'is_passed': False,
            'matched_keywords': [],
            'missing_keywords': keywords,
            'match_details': {kw: False for kw in keywords},
            'error': error_msg
        }
    
    def batch_evaluate(
        self,
        test_cases: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        批量評分
        
        Args:
            test_cases: 測試案例列表，每個案例包含：
                {
                    'question': str,
                    'expected_answer': str,
                    'actual_answer': str,
                    'keywords': List[str]
                }
        
        Returns:
            評分結果列表
        """
        results = []
        
        for i, case in enumerate(test_cases, 1):
            try:
                result = self.evaluate(
                    question=case.get('question', ''),
                    expected_answer=case.get('expected_answer', ''),
                    actual_answer=case.get('actual_answer', ''),
                    keywords=case.get('keywords', [])
                )
                result['case_index'] = i
                results.append(result)
                
            except Exception as e:
                logger.error(f"批量評分失敗 (案例 {i}): {str(e)}")
                results.append({
                    'case_index': i,
                    'score': 0,
                    'is_passed': False,
                    'error': str(e)
                })
        
        return results
    
    def get_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        計算評分統計資料
        
        Args:
            results: 評分結果列表
        
        Returns:
            統計資料：
            {
                'total_cases': int,
                'passed_cases': int,
                'failed_cases': int,
                'pass_rate': float,
                'average_score': float,
                'score_distribution': Dict[str, int]
            }
        """
        if not results:
            return {
                'total_cases': 0,
                'passed_cases': 0,
                'failed_cases': 0,
                'pass_rate': 0.0,
                'average_score': 0.0,
                'score_distribution': {}
            }
        
        total_cases = len(results)
        passed_cases = sum(1 for r in results if r.get('is_passed', False))
        failed_cases = total_cases - passed_cases
        
        scores = [r.get('score', 0) for r in results]
        average_score = sum(scores) / total_cases if total_cases > 0 else 0
        pass_rate = (passed_cases / total_cases * 100) if total_cases > 0 else 0
        
        # 分數區間分布
        score_distribution = {
            '0-20': 0,
            '21-40': 0,
            '41-60': 0,
            '61-80': 0,
            '81-100': 0
        }
        
        for score in scores:
            if score <= 20:
                score_distribution['0-20'] += 1
            elif score <= 40:
                score_distribution['21-40'] += 1
            elif score <= 60:
                score_distribution['41-60'] += 1
            elif score <= 80:
                score_distribution['61-80'] += 1
            else:
                score_distribution['81-100'] += 1
        
        return {
            'total_cases': total_cases,
            'passed_cases': passed_cases,
            'failed_cases': failed_cases,
            'pass_rate': round(pass_rate, 2),
            'average_score': round(average_score, 2),
            'score_distribution': score_distribution
        }
