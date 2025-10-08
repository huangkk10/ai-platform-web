"""
Question Classifier - RVT Assistant 問題智能分類器

此模組負責：
- 自動分類用戶問題類型
- 識別相似問題並歸併
- 提供問題趨勢分析
- 支持規則式和AI輔助分類
"""

import logging
import re
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class QuestionClassifier:
    """問題分類器"""
    
    # 預定義問題分類規則
    CATEGORY_RULES = {
        'hardware': {
            'keywords': ['Samsung', 'ULINK', 'SSD', 'device', 'hardware', '硬體', '設備', '裝置'],
            'patterns': [
                r'Samsung.*(?:問題|error|fail)',
                r'ULINK.*(?:連接|connection|issue)',
                r'SSD.*(?:測試|test|performance)'
            ],
            'description': '硬體相關問題'
        },
        'jenkins': {
            'keywords': ['Jenkins', 'pipeline', 'stage', 'build', 'job', '流水線', '建置'],
            'patterns': [
                r'Jenkins.*(?:失敗|fail|error)',
                r'pipeline.*(?:問題|issue|stuck)',
                r'build.*(?:失敗|timeout)'
            ],
            'description': 'Jenkins 流水線問題'
        },
        'testing': {
            'keywords': ['測試', 'test', 'fail', 'error', 'bug', 'issue', 'problem', '問題', '錯誤'],
            'patterns': [
                r'測試.*(?:失敗|錯誤|問題)',
                r'test.*(?:fail|error|issue)',
                r'.*(?:無法|不能).*測試'
            ],
            'description': '測試執行問題'
        },
        'ansible': {
            'keywords': ['Ansible', 'playbook', 'deploy', 'automation', '自動化', '部署'],
            'patterns': [
                r'Ansible.*(?:執行|run|fail)',
                r'playbook.*(?:問題|error)',
                r'deploy.*(?:失敗|timeout)'
            ],
            'description': 'Ansible 自動化問題'
        },
        'mdt': {
            'keywords': ['MDT', 'deployment', 'image', 'WinPE', '部署', '映像'],
            'patterns': [
                r'MDT.*(?:部署|deploy|fail)',
                r'WinPE.*(?:問題|boot|issue)',
                r'deployment.*(?:失敗|timeout)'
            ],
            'description': 'MDT 部署問題'
        },
        'network': {
            'keywords': ['network', 'connection', 'IP', 'ping', '網路', '連接', '連線'],
            'patterns': [
                r'(?:網路|network).*(?:問題|issue|fail)',
                r'(?:連接|connection).*(?:失敗|timeout)',
                r'ping.*(?:不通|fail)'
            ],
            'description': '網路連接問題'
        },
        'configuration': {
            'keywords': ['config', 'setting', 'parameter', '配置', '設定', '參數'],
            'patterns': [
                r'(?:配置|config).*(?:問題|錯誤|issue)',
                r'(?:參數|parameter).*(?:設定|setting)',
                r'setting.*(?:問題|incorrect)'
            ],
            'description': '配置設定問題'
        },
        'troubleshooting': {
            'keywords': ['troubleshoot', 'debug', 'solve', 'fix', '排除', '解決', '修復'],
            'patterns': [
                r'(?:如何|how to).*(?:解決|solve|fix)',
                r'(?:排除|troubleshoot).*問題',
                r'.*(?:修復|repair|fix)'
            ],
            'description': '故障排除指導'
        },
        'performance': {
            'keywords': ['performance', 'speed', 'slow', 'timeout', '效能', '速度', '緩慢'],
            'patterns': [
                r'(?:效能|performance).*(?:問題|issue)',
                r'(?:速度|speed).*(?:慢|slow)',
                r'.*timeout.*'
            ],
            'description': '效能相關問題'
        }
    }
    
    def __init__(self, use_ai_classification=False):
        """
        初始化問題分類器
        
        Args:
            use_ai_classification (bool): 是否使用 AI 輔助分類
        """
        self.use_ai_classification = use_ai_classification
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def classify_question(self, question_text: str) -> Dict:
        """
        分類問題
        
        Args:
            question_text (str): 問題文本
            
        Returns:
            dict: 分類結果
        """
        try:
            # 基礎規則分類
            rule_result = self._rule_based_classify(question_text)
            
            # 如果啟用 AI 分類且規則分類信心度不高，嘗試 AI 分類
            ai_result = None
            if self.use_ai_classification and rule_result['confidence'] < 0.7:
                ai_result = self._ai_based_classify(question_text)
            
            # 合併結果
            final_result = self._merge_classification_results(rule_result, ai_result)
            
            self.logger.debug(
                f"問題分類完成: '{question_text[:50]}...' -> "
                f"category={final_result['category']}, "
                f"confidence={final_result['confidence']}"
            )
            
            return final_result
            
        except Exception as e:
            self.logger.error(f"問題分類失敗: {str(e)}")
            return {
                'category': 'unknown',
                'confidence': 0.0,
                'method': 'error',
                'error': str(e)
            }
    
    def _rule_based_classify(self, question_text: str) -> Dict:
        """基於規則的分類"""
        question_lower = question_text.lower()
        scores = {}
        
        for category, rules in self.CATEGORY_RULES.items():
            score = 0
            matched_keywords = []
            matched_patterns = []
            
            # 關鍵字匹配
            for keyword in rules['keywords']:
                if keyword.lower() in question_lower:
                    score += 1
                    matched_keywords.append(keyword)
            
            # 正則表達式匹配
            for pattern in rules['patterns']:
                if re.search(pattern, question_text, re.IGNORECASE):
                    score += 2  # 模式匹配權重更高
                    matched_patterns.append(pattern)
            
            if score > 0:
                scores[category] = {
                    'score': score,
                    'matched_keywords': matched_keywords,
                    'matched_patterns': matched_patterns
                }
        
        if not scores:
            return {
                'category': 'general',
                'confidence': 0.1,
                'method': 'rule_based',
                'details': {'reason': 'no_matching_rules'}
            }
        
        # 找出最高分的類別
        best_category = max(scores.keys(), key=lambda k: scores[k]['score'])
        best_score = scores[best_category]['score']
        
        # 計算信心度（簡化版本）
        total_possible_score = len(self.CATEGORY_RULES[best_category]['keywords']) + \
                             len(self.CATEGORY_RULES[best_category]['patterns']) * 2
        confidence = min(best_score / total_possible_score, 0.9)  # 最高信心度 0.9
        
        return {
            'category': best_category,
            'confidence': confidence,
            'method': 'rule_based',
            'details': scores[best_category]
        }
    
    def _ai_based_classify(self, question_text: str) -> Optional[Dict]:
        """基於 AI 的分類（需要 embedding 服務支援）"""
        try:
            # 這裡可以整合 embedding 服務進行語義分類
            # 暫時返回 None，表示 AI 分類不可用
            return None
            
        except Exception as e:
            self.logger.error(f"AI 分類失敗: {str(e)}")
            return None
    
    def _merge_classification_results(self, rule_result: Dict, ai_result: Optional[Dict]) -> Dict:
        """合併規則分類和 AI 分類結果"""
        if ai_result is None:
            return rule_result
        
        # 如果 AI 分類信心度更高，使用 AI 結果
        if ai_result['confidence'] > rule_result['confidence']:
            ai_result['fallback_method'] = rule_result['method']
            return ai_result
        
        # 否則使用規則分類結果，但記錄 AI 分類作為參考
        rule_result['ai_suggestion'] = ai_result
        return rule_result
    
    def find_similar_questions(self, question_text: str, existing_questions: List[str], 
                             similarity_threshold: float = 0.7) -> List[Tuple[str, float]]:
        """
        查找相似問題
        
        Args:
            question_text (str): 當前問題
            existing_questions (List[str]): 已存在的問題列表
            similarity_threshold (float): 相似度閾值
            
        Returns:
            List[Tuple[str, float]]: 相似問題和相似度分數列表
        """
        similar_questions = []
        
        try:
            # 簡化版本：基於關鍵字重疊度計算相似度
            current_words = set(re.findall(r'\w+', question_text.lower()))
            
            for existing_question in existing_questions:
                existing_words = set(re.findall(r'\w+', existing_question.lower()))
                
                # 計算 Jaccard 相似度
                intersection = current_words.intersection(existing_words)
                union = current_words.union(existing_words)
                
                if len(union) > 0:
                    similarity = len(intersection) / len(union)
                    
                    if similarity >= similarity_threshold:
                        similar_questions.append((existing_question, similarity))
            
            # 按相似度排序
            similar_questions.sort(key=lambda x: x[1], reverse=True)
            
        except Exception as e:
            self.logger.error(f"查找相似問題失敗: {str(e)}")
        
        return similar_questions
    
    def get_category_stats(self, questions_with_categories: List[Tuple[str, str]]) -> Dict:
        """
        獲取分類統計
        
        Args:
            questions_with_categories: [(question, category), ...]
            
        Returns:
            dict: 統計結果
        """
        try:
            from collections import Counter
            
            categories = [category for _, category in questions_with_categories]
            category_counts = Counter(categories)
            
            total_questions = len(questions_with_categories)
            
            stats = {
                'total_questions': total_questions,
                'category_distribution': dict(category_counts),
                'category_percentages': {},
                'top_categories': []
            }
            
            # 計算百分比
            for category, count in category_counts.items():
                percentage = (count / total_questions) * 100 if total_questions > 0 else 0
                stats['category_percentages'][category] = round(percentage, 2)
            
            # 取前 5 大類別
            stats['top_categories'] = category_counts.most_common(5)
            
            return stats
            
        except Exception as e:
            self.logger.error(f"獲取分類統計失敗: {str(e)}")
            return {'error': str(e)}

# 便利函數
def classify_question(question_text: str, use_ai_classification: bool = False) -> Dict:
    """問題分類便利函數"""
    classifier = QuestionClassifier(use_ai_classification=use_ai_classification)
    return classifier.classify_question(question_text)

def get_question_categories() -> Dict:
    """獲取所有問題分類"""
    return {
        category: rules['description'] 
        for category, rules in QuestionClassifier.CATEGORY_RULES.items()
    }

def find_similar_questions(question_text: str, existing_questions: List[str], 
                          similarity_threshold: float = 0.7) -> List[Tuple[str, float]]:
    """查找相似問題便利函數"""
    classifier = QuestionClassifier()
    return classifier.find_similar_questions(question_text, existing_questions, similarity_threshold)