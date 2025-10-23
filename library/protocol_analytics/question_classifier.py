"""
Protocol Question Classifier - Protocol Assistant 問題智能分類器

此模組負責：
- 自動分類用戶關於 Protocol 測試的問題類型
- 識別相似問題並歸併
- 提供問題趨勢分析
- 基於規則的分類（可擴展至 AI 輔助）

Protocol 特定分類：
- Protocol 測試執行
- Known Issue 查詢
- 測試配置問題
- Protocol 規範諮詢
- 故障排除
"""

import logging
import re
from typing import List, Dict, Optional, Tuple
from collections import Counter

logger = logging.getLogger(__name__)


class ProtocolQuestionClassifier:
    """Protocol 問題分類器"""
    
    # Protocol 特定問題分類規則
    CATEGORY_RULES = {
        'protocol_execution': {
            'keywords': ['測試', 'test', '執行', 'run', 'execute', '運行', 'protocol'],
            'patterns': [
                r'protocol.*(?:測試|test|執行)',
                r'(?:執行|run).*protocol',
                r'如何.*(?:測試|test).*protocol'
            ],
            'description': 'Protocol 測試執行'
        },
        'known_issue': {
            'keywords': ['know issue', 'known issue', '已知問題', 'bug', 'error', '錯誤', 'issue'],
            'patterns': [
                r'know[n]?\s*issue',
                r'已知.*(?:問題|錯誤)',
                r'(?:查詢|search|find).*issue'
            ],
            'description': 'Known Issue 查詢'
        },
        'configuration': {
            'keywords': ['配置', 'config', 'setting', '設定', 'parameter', '參數'],
            'patterns': [
                r'(?:配置|config).*(?:問題|錯誤|issue)',
                r'(?:參數|parameter|setting).*(?:如何|怎麼)',
                r'setting.*protocol'
            ],
            'description': '測試配置問題'
        },
        'specification': {
            'keywords': ['規範', 'spec', 'specification', 'standard', '標準', '要求'],
            'patterns': [
                r'protocol.*(?:規範|spec|標準)',
                r'(?:規範|specification).*要求',
                r'什麼是.*protocol'
            ],
            'description': 'Protocol 規範諮詢'
        },
        'troubleshooting': {
            'keywords': ['troubleshoot', '排除', '解決', 'fix', 'solve', '修復', 'debug'],
            'patterns': [
                r'(?:如何|怎麼).*(?:解決|solve|fix)',
                r'(?:排除|troubleshoot).*問題',
                r'.*(?:修復|repair|debug)'
            ],
            'description': '故障排除'
        },
        'test_result': {
            'keywords': ['結果', 'result', 'report', '報告', 'log', '日誌'],
            'patterns': [
                r'(?:測試|test).*(?:結果|result)',
                r'(?:報告|report|log).*(?:查看|view)',
                r'result.*analysis'
            ],
            'description': '測試結果分析'
        },
        'environment': {
            'keywords': ['環境', 'environment', 'setup', '建置', '安裝', 'install'],
            'patterns': [
                r'(?:環境|environment).*(?:問題|issue)',
                r'(?:建置|setup|install).*環境',
                r'environment.*configuration'
            ],
            'description': '測試環境問題'
        },
        'general_inquiry': {
            'keywords': ['是什麼', '什麼是', 'what is', 'how to', '如何', '怎麼'],
            'patterns': [
                r'(?:是什麼|什麼是|what is)',
                r'(?:如何|怎麼|how to)',
                r'can.*(?:tell|explain)'
            ],
            'description': '一般諮詢'
        }
    }
    
    def __init__(self):
        """初始化 Protocol 問題分類器"""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def classify_question(self, question_text: str) -> Dict:
        """
        分類問題（基於規則）
        
        Args:
            question_text (str): 問題文本
            
        Returns:
            dict: 分類結果
                {
                    'category': str,
                    'confidence': float,
                    'matched_keywords': List[str],
                    'description': str
                }
        """
        try:
            # 規則式分類
            best_category = 'general_inquiry'
            best_score = 0
            matched_keywords = []
            
            question_lower = question_text.lower()
            
            for category, rules in self.CATEGORY_RULES.items():
                score = 0
                category_keywords = []
                
                # 關鍵字匹配
                for keyword in rules['keywords']:
                    if keyword.lower() in question_lower:
                        score += 1
                        category_keywords.append(keyword)
                
                # 正則匹配（權重更高）
                for pattern in rules['patterns']:
                    if re.search(pattern, question_text, re.IGNORECASE):
                        score += 2
                
                if score > best_score:
                    best_score = score
                    best_category = category
                    matched_keywords = category_keywords
            
            # 計算信心度
            confidence = min(best_score / 5.0, 1.0)  # 最高 5 分
            
            return {
                'category': best_category,
                'confidence': round(confidence, 2),
                'matched_keywords': matched_keywords,
                'description': self.CATEGORY_RULES[best_category]['description']
            }
            
        except Exception as e:
            self.logger.error(f"問題分類失敗: {str(e)}")
            return {
                'category': 'unknown',
                'confidence': 0.0,
                'matched_keywords': [],
                'description': '未知類別'
            }
    
    def classify_batch(self, questions: List[str]) -> List[Dict]:
        """
        批量分類問題
        
        Args:
            questions (List[str]): 問題列表
            
        Returns:
            List[Dict]: 分類結果列表
        """
        return [self.classify_question(q) for q in questions]
    
    def get_category_stats(self, classified_questions: List[Tuple[str, str]]) -> Dict:
        """
        獲取分類統計
        
        Args:
            classified_questions: [(question, category), ...]
            
        Returns:
            dict: 統計結果
        """
        try:
            if not classified_questions:
                return {
                    'total': 0,
                    'category_counts': {},
                    'category_percentages': {},
                    'top_categories': []
                }
            
            # 統計每個分類的數量
            categories = [cat for _, cat in classified_questions]
            category_counts = dict(Counter(categories))
            
            total = len(categories)
            
            # 計算百分比
            category_percentages = {
                cat: round((count / total) * 100, 2)
                for cat, count in category_counts.items()
            }
            
            # 取前 5 名
            top_categories = sorted(
                category_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            top_categories_with_desc = [
                {
                    'category': cat,
                    'count': count,
                    'percentage': category_percentages[cat],
                    'description': self.CATEGORY_RULES.get(cat, {}).get('description', '未知')
                }
                for cat, count in top_categories
            ]
            
            return {
                'total': total,
                'category_counts': category_counts,
                'category_percentages': category_percentages,
                'top_categories': top_categories_with_desc
            }
            
        except Exception as e:
            self.logger.error(f"統計分類失敗: {str(e)}")
            return {'error': str(e)}
    
    def get_category_description(self, category: str) -> str:
        """獲取分類描述"""
        return self.CATEGORY_RULES.get(category, {}).get('description', '未知類別')
    
    def get_all_categories(self) -> List[Dict]:
        """獲取所有分類及其描述"""
        return [
            {
                'category': cat,
                'description': rules['description'],
                'keyword_count': len(rules['keywords'])
            }
            for cat, rules in self.CATEGORY_RULES.items()
        ]


# ==================== 便利函數 ====================

def classify_protocol_question(question_text: str) -> Dict:
    """
    便利函數：分類單個問題
    
    Args:
        question_text (str): 問題文本
        
    Returns:
        dict: 分類結果
    """
    classifier = ProtocolQuestionClassifier()
    return classifier.classify_question(question_text)


def get_protocol_categories() -> List[Dict]:
    """
    便利函數：獲取所有 Protocol 問題分類
    
    Returns:
        List[Dict]: 分類列表
    """
    classifier = ProtocolQuestionClassifier()
    return classifier.get_all_categories()


__all__ = [
    'ProtocolQuestionClassifier',
    'classify_protocol_question',
    'get_protocol_categories',
]
