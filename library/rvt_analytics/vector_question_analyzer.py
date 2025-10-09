"""
Vector Question Analyzer - 向量化問題分析器

此模組提供：
- 基於向量聚類的問題分析
- 智能問題相似度分群
- 高級問題趨勢分析
- 向量化統計優化
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class VectorQuestionAnalyzer:
    """向量化問題分析器"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._vector_service = None
        self._clustering_service = None
        
    def _get_vector_service(self):
        """獲取向量化服務"""
        if self._vector_service is None:
            try:
                from library.rvt_analytics.chat_vector_service import get_chat_vector_service
                self._vector_service = get_chat_vector_service()
            except ImportError:
                self.logger.warning("向量化服務不可用")
        return self._vector_service
        
    def _get_clustering_service(self):
        """獲取聚類服務"""
        if self._clustering_service is None:
            try:
                from library.rvt_analytics.chat_clustering_service import get_clustering_service
                self._clustering_service = get_clustering_service()
            except ImportError:
                self.logger.warning("聚類服務不可用")
        return self._clustering_service
    
    def analyze_popular_questions_by_clusters(self, days: int = 30, 
                                            limit: int = 10) -> List[Dict]:
        """
        基於聚類分析熱門問題
        
        Args:
            days: 分析天數
            limit: 返回問題數量
            
        Returns:
            List[Dict]: 熱門問題列表，包含聚類信息
        """
        try:
            from django.db import connection
            from django.utils import timezone
            
            # 計算時間範圍
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)
            
            # 查詢向量化的用戶消息
            with connection.cursor() as cursor:
                cursor.execute('''
                    SELECT 
                        cme.cluster_id,
                        cm.content,
                        COUNT(*) as frequency,
                        AVG(cme.confidence_score) as avg_confidence,
                        STRING_AGG(DISTINCT cm.content, '|||') as all_examples
                    FROM chat_messages cm
                    JOIN chat_message_embeddings_1024 cme ON cm.id = cme.chat_message_id
                    WHERE cm.role = 'user' 
                        AND cm.created_at >= %s 
                        AND cm.created_at <= %s
                    GROUP BY cme.cluster_id, cm.content
                    ORDER BY cme.cluster_id, frequency DESC
                ''', [start_date, end_date])
                
                cluster_data = {}
                for cluster_id, content, freq, confidence, examples in cursor.fetchall():
                    if cluster_id not in cluster_data:
                        cluster_data[cluster_id] = {
                            'questions': [],
                            'total_frequency': 0,
                            'avg_confidence': 0.0,
                            'examples': set()
                        }
                    
                    cluster_data[cluster_id]['questions'].append({
                        'content': content,
                        'frequency': freq,
                        'confidence': confidence
                    })
                    cluster_data[cluster_id]['total_frequency'] += freq
                    cluster_data[cluster_id]['examples'].update(examples.split('|||') if examples else [content])
            
            # 生成問題分析結果
            popular_questions = []
            
            for cluster_id, data in cluster_data.items():
                # 特殊處理 NULL 聚類 - 分別統計每個問題
                if cluster_id is None:
                    # 對於 NULL 聚類，每個問題單獨統計
                    for question_item in data['questions']:
                        if question_item['frequency'] > 0:
                            popular_questions.append({
                                'cluster_id': None,
                                'pattern': self._generate_question_label(question_item['content']),
                                'question': question_item['content'],
                                'count': question_item['frequency'],  # 使用實際頻率，不是總和
                                'examples': [question_item['content']],
                                'avg_confidence': question_item['confidence'] or 0.0,
                                'is_vector_based': True,
                                'analysis_method': 'vector_clustering_individual',
                                'representative_frequency': question_item['frequency']
                            })
                elif data['total_frequency'] > 0:
                    # 正常聚類的處理邏輯
                    # 找到代表性問題（頻率最高的）
                    representative_question = max(data['questions'], key=lambda x: x['frequency'])
                    
                    # 計算平均信心度
                    avg_confidence = sum(q['confidence'] or 0 for q in data['questions']) / len(data['questions'])
                    
                    # 生成問題標籤
                    question_label = self._generate_question_label(representative_question['content'])
                    
                    # 獲取範例（去重並限制數量）
                    examples = list(data['examples'])[:5]
                    
                    popular_questions.append({
                        'cluster_id': cluster_id,
                        'pattern': question_label,
                        'question': representative_question['content'],
                        'count': data['total_frequency'],
                        'examples': examples,
                        'avg_confidence': round(avg_confidence, 3),
                        'is_vector_based': True,
                        'analysis_method': 'vector_clustering',
                        'representative_frequency': representative_question['frequency']
                    })
            
            # 按總頻率排序
            popular_questions.sort(key=lambda x: x['count'], reverse=True)
            
            self.logger.info(f"向量聚類分析完成，發現 {len(popular_questions)} 個問題群組")
            return popular_questions[:limit]
            
        except Exception as e:
            self.logger.error(f"向量聚類問題分析失敗: {str(e)}")
            return []
    
    def _generate_question_label(self, question: str) -> str:
        """為問題生成簡潔的標籤"""
        try:
            import re
            
            # 提取關鍵詞
            words = re.findall(r'[\u4e00-\u9fff\w]+', question)
            
            # 過濾停用詞
            stop_words = {'如何', '怎麼', '什麼', '為什麼', '怎樣', '哪裡', '是', '的', '了', '在', '有', '和'}
            keywords = [w for w in words if len(w) > 1 and w not in stop_words]
            
            # 生成標籤（取前3個關鍵詞）
            if keywords:
                return ' '.join(keywords[:3])
            else:
                return question[:20] + ('...' if len(question) > 20 else '')
                
        except Exception:
            return question[:20] + ('...' if len(question) > 20 else '')
    
    def get_question_similarity_groups(self, threshold: float = 0.8, 
                                     limit: int = 10) -> List[Dict]:
        """
        基於向量相似度分析問題組群
        
        Args:
            threshold: 相似度閾值
            limit: 返回組群數量
            
        Returns:
            List[Dict]: 相似問題組群
        """
        try:
            vector_service = self._get_vector_service()
            if not vector_service:
                return []
            
            # 獲取所有向量化的用戶消息
            from django.db import connection
            
            with connection.cursor() as cursor:
                cursor.execute('''
                    SELECT DISTINCT cm.content
                    FROM chat_messages cm
                    JOIN chat_message_embeddings_1024 cme ON cm.id = cme.chat_message_id
                    WHERE cm.role = 'user'
                    ORDER BY cm.created_at DESC
                    LIMIT 100  -- 限制數量以提高性能
                ''')
                
                questions = [row[0] for row in cursor.fetchall()]
            
            if not questions:
                return []
            
            # 使用向量相似度進行分組
            similarity_groups = []
            processed_questions = set()
            
            for base_question in questions:
                if base_question in processed_questions:
                    continue
                
                # 搜索相似問題
                try:
                    from library.rvt_analytics.chat_vector_service import search_similar_chat_messages
                    similar_questions = search_similar_chat_messages(
                        base_question, 
                        limit=10, 
                        threshold=threshold
                    )
                    
                    if len(similar_questions) > 1:  # 至少2個相似問題才組成群組
                        group_questions = [item['content'] for item in similar_questions]
                        
                        # 統計頻率
                        group_count = len(group_questions)
                        
                        similarity_groups.append({
                            'pattern': self._generate_question_label(base_question),
                            'question': base_question,
                            'count': group_count,
                            'examples': group_questions[:5],
                            'similarity_threshold': threshold,
                            'is_vector_based': True,
                            'analysis_method': 'vector_similarity',
                            'avg_similarity': sum(item.get('score', 0) for item in similar_questions) / len(similar_questions)
                        })
                        
                        # 標記已處理的問題
                        processed_questions.update(group_questions)
                        
                except Exception as e:
                    self.logger.warning(f"相似度搜索失敗 for '{base_question}': {e}")
                    continue
            
            # 按組群大小排序
            similarity_groups.sort(key=lambda x: x['count'], reverse=True)
            
            self.logger.info(f"相似度分析完成，發現 {len(similarity_groups)} 個相似問題組群")
            return similarity_groups[:limit]
            
        except Exception as e:
            self.logger.error(f"相似度問題分析失敗: {str(e)}")
            return []
    
    def get_enhanced_question_statistics(self, days: int = 30) -> Dict:
        """
        獲取增強的問題統計（結合聚類和相似度）
        
        Args:
            days: 分析天數
            
        Returns:
            Dict: 增強的統計結果
        """
        try:
            # 獲取聚類統計
            cluster_analysis = self.analyze_popular_questions_by_clusters(days=days, limit=15)
            
            # 獲取相似度統計  
            similarity_analysis = self.get_question_similarity_groups(threshold=0.7, limit=10)
            
            # 合併並去重
            all_questions = cluster_analysis.copy()
            
            # 添加相似度分析中的獨特問題
            cluster_patterns = {q['pattern'] for q in cluster_analysis}
            for sim_q in similarity_analysis:
                if sim_q['pattern'] not in cluster_patterns:
                    all_questions.append(sim_q)
            
            # 重新排序
            all_questions.sort(key=lambda x: x['count'], reverse=True)
            
            # 生成統計摘要
            total_vector_questions = len([q for q in all_questions if q.get('is_vector_based')])
            
            statistics = {
                'popular_questions': all_questions[:10],  # 取前10個
                'analysis_summary': {
                    'total_question_groups': len(all_questions),
                    'vector_based_groups': total_vector_questions,
                    'cluster_based_groups': len(cluster_analysis),
                    'similarity_based_groups': len(similarity_analysis),
                    'analysis_method': 'enhanced_vector_analysis',
                    'analysis_date': datetime.now().isoformat()
                },
                'method_comparison': {
                    'vector_clustering': len(cluster_analysis),
                    'vector_similarity': len(similarity_analysis),
                    'total_enhanced': len(all_questions)
                }
            }
            
            self.logger.info(f"增強問題統計完成，總計 {len(all_questions)} 個問題組群")
            return statistics
            
        except Exception as e:
            self.logger.error(f"增強問題統計失敗: {str(e)}")
            return {
                'popular_questions': [],
                'analysis_summary': {
                    'error': str(e),
                    'analysis_method': 'enhanced_vector_analysis_failed'
                }
            }


# 便利函數
def get_vector_question_analyzer():
    """獲取向量化問題分析器實例"""
    return VectorQuestionAnalyzer()


def analyze_questions_with_vectors(days: int = 30, limit: int = 10) -> List[Dict]:
    """
    使用向量化方法分析熱門問題的便利函數
    
    Args:
        days: 分析天數
        limit: 返回問題數量
        
    Returns:
        List[Dict]: 熱門問題列表
    """
    analyzer = get_vector_question_analyzer()
    return analyzer.analyze_popular_questions_by_clusters(days=days, limit=limit)


def get_enhanced_question_analysis(days: int = 30) -> Dict:
    """
    獲取增強問題分析的便利函數
    
    Args:
        days: 分析天數
        
    Returns:
        Dict: 增強的分析結果
    """
    analyzer = get_vector_question_analyzer()
    return analyzer.get_enhanced_question_statistics(days=days)