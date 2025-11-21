"""Benchmark Scoring Engine"""
import math
from typing import List, Dict, Any

class ScoringEngine:
    WEIGHTS = {'precision': 0.35, 'recall': 0.30, 'f1': 0.20, 'ndcg': 0.05, 'speed': 0.10}
    SPEED_THRESHOLDS = {'excellent': 50, 'good': 150, 'acceptable': 300, 'poor': 500}
    
    @staticmethod
    def calculate_precision(returned_ids: List[int], expected_ids: List[int]) -> float:
        if not returned_ids:
            return 0.0
        expected_set = set(expected_ids)
        true_positives = sum(1 for doc_id in returned_ids if doc_id in expected_set)
        return true_positives / len(returned_ids)
    
    @staticmethod
    def calculate_recall(returned_ids: List[int], expected_ids: List[int]) -> float:
        if not expected_ids:
            return 0.0
        expected_set = set(expected_ids)
        returned_set = set(returned_ids)
        true_positives = len(expected_set & returned_set)
        return true_positives / len(expected_ids)
    
    @staticmethod
    def calculate_f1_score(precision: float, recall: float) -> float:
        if precision + recall == 0:
            return 0.0
        return 2 * (precision * recall) / (precision + recall)
    
    @staticmethod
    def calculate_ndcg(returned_ids: List[int], expected_ids: List[int], top_k: int = 10) -> float:
        if not returned_ids or not expected_ids:
            return 0.0
        expected_set = set(expected_ids)
        dcg = sum(1.0 / math.log2(i + 1) for i, doc_id in enumerate(returned_ids[:top_k], start=1) if doc_id in expected_set)
        num_relevant = min(len(expected_ids), top_k)
        idcg = sum(1.0 / math.log2(i + 1) for i in range(1, num_relevant + 1))
        return dcg / idcg if idcg > 0 else 0.0
    
    @staticmethod
    def calculate_speed_score(response_time: float) -> float:
        if response_time <= ScoringEngine.SPEED_THRESHOLDS['excellent']:
            return 100.0
        elif response_time <= ScoringEngine.SPEED_THRESHOLDS['good']:
            return 90.0
        elif response_time <= ScoringEngine.SPEED_THRESHOLDS['acceptable']:
            return 75.0
        elif response_time <= ScoringEngine.SPEED_THRESHOLDS['poor']:
            return 50.0
        else:
            max_time = 5000.0
            if response_time >= max_time:
                return 0.0
            score = 50.0 * (1 - (response_time - 500) / (max_time - 500))
            return max(0.0, score)
    
    @classmethod
    def calculate_overall_score(cls, precision: float, recall: float, f1: float, ndcg: float, speed_score: float) -> float:
        precision_pct = precision * 100
        recall_pct = recall * 100
        f1_pct = f1 * 100
        ndcg_pct = ndcg * 100
        overall = (precision_pct * cls.WEIGHTS['precision'] + recall_pct * cls.WEIGHTS['recall'] +
                  f1_pct * cls.WEIGHTS['f1'] + ndcg_pct * cls.WEIGHTS['ndcg'] + speed_score * cls.WEIGHTS['speed'])
        return round(overall, 2)
    
    @classmethod
    def calculate_all_metrics(cls, returned_ids: List[int], expected_ids: List[int], response_time: float, top_k: int = 10) -> Dict[str, Any]:
        precision = cls.calculate_precision(returned_ids, expected_ids)
        recall = cls.calculate_recall(returned_ids, expected_ids)
        f1 = cls.calculate_f1_score(precision, recall)
        ndcg = cls.calculate_ndcg(returned_ids, expected_ids, top_k)
        speed_score = cls.calculate_speed_score(response_time)
        overall_score = cls.calculate_overall_score(precision, recall, f1, ndcg, speed_score)
        expected_set = set(expected_ids)
        returned_set = set(returned_ids)
        true_positives = len(expected_set & returned_set)
        false_positives = len(returned_set - expected_set)
        false_negatives = len(expected_set - returned_set)
        return {
            'precision': round(precision, 4), 'recall': round(recall, 4), 'f1_score': round(f1, 4), 'ndcg': round(ndcg, 4),
            'precision_pct': round(precision * 100, 2), 'recall_pct': round(recall * 100, 2),
            'f1_score_pct': round(f1 * 100, 2), 'ndcg_pct': round(ndcg * 100, 2), 'speed_score': round(speed_score, 2),
            'overall_score': overall_score, 'true_positives': true_positives, 'false_positives': false_positives,
            'false_negatives': false_negatives, 'response_time_ms': round(response_time, 2),
            'returned_count': len(returned_ids), 'expected_count': len(expected_ids)
        }
