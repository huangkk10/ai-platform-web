"""
Chat Clustering Service - 聊天消息聚類分析服務

此模組負責：
- 對聊天消息向量進行智能聚類
- 自動發現問題類型和模式
- 提供動態分類建議
- 支持聚類優化和調整
"""

import logging
import numpy as np
from typing import List, Dict, Optional, Any, Tuple
from django.db import connection, transaction
from collections import Counter, defaultdict
import json
import math

logger = logging.getLogger(__name__)

class ChatClusteringService:
    """聊天消息聚類分析服務"""
    
    def __init__(self, min_cluster_size: int = 3, max_clusters: int = 20):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.min_cluster_size = min_cluster_size
        self.max_clusters = max_clusters
    
    def get_vector_data(self, user_role: str = 'user', 
                       min_message_length: int = 5) -> List[Dict]:
        """
        獲取向量數據用於聚類
        
        Args:
            user_role: 用戶角色過濾
            min_message_length: 最小消息長度過濾
            
        Returns:
            向量數據列表
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        id,
                        chat_message_id,
                        conversation_id,
                        text_content,
                        embedding,
                        message_length,
                        question_keywords,
                        language_detected,
                        created_at
                    FROM chat_message_embeddings_1024
                    WHERE user_role = %s
                    AND message_length >= %s
                    AND embedding IS NOT NULL
                    ORDER BY created_at DESC
                """, [user_role, min_message_length])
                
                columns = [col[0] for col in cursor.description]
                results = []
                
                for row in cursor.fetchall():
                    data = dict(zip(columns, row))
                    # 轉換向量數據
                    if data['embedding']:
                        # PostgreSQL vector 類型轉換為 Python list
                        embedding_str = data['embedding'].replace('[', '').replace(']', '')
                        data['embedding'] = [float(x) for x in embedding_str.split(',')]
                    results.append(data)
                
                self.logger.info(f"獲取向量數據: {len(results)} 筆記錄")
                return results
                
        except Exception as e:
            self.logger.error(f"獲取向量數據失敗: {str(e)}")
            return []
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        計算餘弦相似度
        
        Args:
            vec1, vec2: 向量
            
        Returns:
            相似度分數 (0-1)
        """
        try:
            # 轉換為 numpy 數組
            a = np.array(vec1)
            b = np.array(vec2)
            
            # 計算餘弦相似度
            dot_product = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            
            if norm_a == 0 or norm_b == 0:
                return 0.0
            
            similarity = dot_product / (norm_a * norm_b)
            return max(0.0, min(1.0, similarity))  # 確保在 0-1 範圍
            
        except Exception as e:
            self.logger.error(f"計算相似度失敗: {str(e)}")
            return 0.0
    
    def simple_kmeans_clustering(self, vector_data: List[Dict], 
                                k: Optional[int] = None,
                                max_iterations: int = 100) -> Dict:
        """
        簡化版 K-means 聚類
        
        Args:
            vector_data: 向量數據
            k: 聚類數量（None 則自動決定）
            max_iterations: 最大迭代次數
            
        Returns:
            聚類結果
        """
        try:
            if not vector_data:
                return {'clusters': {}, 'centroids': {}, 'stats': {}}
            
            # 提取向量
            embeddings = [data['embedding'] for data in vector_data]
            n_samples = len(embeddings)
            
            # 自動決定 k 值
            if k is None:
                k = min(self.max_clusters, max(2, int(math.sqrt(n_samples / 2))))
            
            self.logger.info(f"開始 K-means 聚類: 樣本數={n_samples}, k={k}")
            
            # 初始化質心（隨機選擇）
            np.random.seed(42)  # 固定隨機種子以確保結果可重現
            centroids = [embeddings[i] for i in np.random.choice(n_samples, k, replace=False)]
            
            clusters = {}
            
            for iteration in range(max_iterations):
                # 分配每個點到最近的質心
                new_clusters = defaultdict(list)
                
                for idx, embedding in enumerate(embeddings):
                    # 計算到各質心的距離
                    distances = [
                        1 - self.cosine_similarity(embedding, centroid)
                        for centroid in centroids
                    ]
                    
                    # 找到最近的質心
                    closest_centroid = distances.index(min(distances))
                    new_clusters[closest_centroid].append(idx)
                
                # 更新質心
                new_centroids = []
                converged = True
                
                for cluster_id in range(k):
                    if cluster_id in new_clusters and len(new_clusters[cluster_id]) > 0:
                        # 計算新質心（平均向量）
                        cluster_vectors = [embeddings[idx] for idx in new_clusters[cluster_id]]
                        new_centroid = np.mean(cluster_vectors, axis=0).tolist()
                        
                        # 檢查是否收斂
                        if (len(centroids) > cluster_id and 
                            self.cosine_similarity(new_centroid, centroids[cluster_id]) < 0.99):
                            converged = False
                        
                        new_centroids.append(new_centroid)
                    else:
                        # 空聚類，保持原質心
                        if len(centroids) > cluster_id:
                            new_centroids.append(centroids[cluster_id])
                        else:
                            new_centroids.append(embeddings[0])  # 預設值
                
                centroids = new_centroids
                clusters = dict(new_clusters)
                
                if converged:
                    self.logger.info(f"K-means 收斂於第 {iteration + 1} 次迭代")
                    break
            
            # 生成聚類統計
            stats = self._calculate_cluster_stats(vector_data, clusters, centroids)
            
            return {
                'clusters': clusters,
                'centroids': centroids,
                'stats': stats,
                'algorithm': 'k-means',
                'k': k,
                'iterations': iteration + 1
            }
            
        except Exception as e:
            self.logger.error(f"K-means 聚類失敗: {str(e)}")
            return {'error': str(e)}
    
    def density_based_clustering(self, vector_data: List[Dict], 
                               eps: float = 0.3, 
                               min_samples: int = 3) -> Dict:
        """
        基於密度的聚類（簡化版 DBSCAN）
        
        Args:
            vector_data: 向量數據
            eps: 鄰域半徑
            min_samples: 最小樣本數
            
        Returns:
            聚類結果
        """
        try:
            if not vector_data:
                return {'clusters': {}, 'noise': [], 'stats': {}}
            
            embeddings = [data['embedding'] for data in vector_data]
            n_samples = len(embeddings)
            
            self.logger.info(f"開始密度聚類: 樣本數={n_samples}, eps={eps}, min_samples={min_samples}")
            
            # 計算距離矩陣
            distances = np.zeros((n_samples, n_samples))
            for i in range(n_samples):
                for j in range(i + 1, n_samples):
                    sim = self.cosine_similarity(embeddings[i], embeddings[j])
                    distance = 1 - sim
                    distances[i][j] = distance
                    distances[j][i] = distance
            
            # DBSCAN 演算法
            visited = [False] * n_samples
            clusters = {}
            noise = []
            cluster_id = 0
            
            for i in range(n_samples):
                if visited[i]:
                    continue
                
                visited[i] = True
                
                # 找到鄰域
                neighbors = [j for j in range(n_samples) if distances[i][j] <= eps]
                
                if len(neighbors) < min_samples:
                    # 噪點
                    noise.append(i)
                else:
                    # 開始新聚類
                    clusters[cluster_id] = []
                    self._expand_cluster(i, neighbors, distances, eps, min_samples, 
                                       visited, clusters[cluster_id], noise)
                    cluster_id += 1
            
            # 生成統計
            stats = {
                'n_clusters': len(clusters),
                'n_noise': len(noise),
                'cluster_sizes': {cid: len(points) for cid, points in clusters.items()},
                'total_points': n_samples
            }
            
            return {
                'clusters': clusters,
                'noise': noise,
                'stats': stats,
                'algorithm': 'dbscan',
                'eps': eps,
                'min_samples': min_samples
            }
            
        except Exception as e:
            self.logger.error(f"密度聚類失敗: {str(e)}")
            return {'error': str(e)}
    
    def _expand_cluster(self, point, neighbors, distances, eps, min_samples,
                       visited, cluster, noise):
        """擴展聚類（DBSCAN 輔助函數）"""
        cluster.append(point)
        
        i = 0
        while i < len(neighbors):
            neighbor = neighbors[i]
            
            if not visited[neighbor]:
                visited[neighbor] = True
                
                # 找到鄰域
                neighbor_neighbors = [j for j in range(len(distances)) 
                                    if distances[neighbor][j] <= eps]
                
                if len(neighbor_neighbors) >= min_samples:
                    # 合併鄰域
                    for nn in neighbor_neighbors:
                        if nn not in neighbors:
                            neighbors.append(nn)
            
            # 如果不在任何聚類中，加入當前聚類
            if neighbor not in cluster and neighbor not in noise:
                cluster.append(neighbor)
            
            i += 1
    
    def _calculate_cluster_stats(self, vector_data: List[Dict], 
                               clusters: Dict, centroids: List) -> Dict:
        """計算聚類統計資訊"""
        try:
            stats = {
                'n_clusters': len(clusters),
                'cluster_sizes': {},
                'cluster_keywords': {},
                'cluster_examples': {},
                'quality_metrics': {}
            }
            
            for cluster_id, point_indices in clusters.items():
                cluster_size = len(point_indices)
                stats['cluster_sizes'][cluster_id] = cluster_size
                
                # 收集聚類中的關鍵字
                all_keywords = []
                examples = []
                
                for idx in point_indices:
                    if idx < len(vector_data):
                        data = vector_data[idx]
                        if data.get('question_keywords'):
                            all_keywords.extend(data['question_keywords'])
                        
                        # 收集代表性例子
                        if len(examples) < 3:
                            examples.append({
                                'text': data['text_content'][:100] + '...',
                                'length': data['message_length']
                            })
                
                # 統計關鍵字頻率
                keyword_counts = Counter(all_keywords)
                stats['cluster_keywords'][cluster_id] = dict(keyword_counts.most_common(10))
                stats['cluster_examples'][cluster_id] = examples
                
                # 計算聚類內部相似度
                if cluster_size > 1 and cluster_id < len(centroids):
                    similarities = []
                    centroid = centroids[cluster_id]
                    
                    for idx in point_indices:
                        if idx < len(vector_data):
                            embedding = vector_data[idx]['embedding']
                            sim = self.cosine_similarity(embedding, centroid)
                            similarities.append(sim)
                    
                    if similarities:
                        stats['quality_metrics'][cluster_id] = {
                            'avg_similarity': np.mean(similarities),
                            'min_similarity': np.min(similarities),
                            'max_similarity': np.max(similarities)
                        }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"計算聚類統計失敗: {str(e)}")
            return {'error': str(e)}
    
    def update_cluster_assignments(self, clustering_result: Dict) -> bool:
        """
        更新資料庫中的聚類分配
        
        Args:
            clustering_result: 聚類結果
            
        Returns:
            是否成功
        """
        try:
            if 'error' in clustering_result:
                self.logger.error("聚類結果包含錯誤，無法更新")
                return False
            
            clusters = clustering_result.get('clusters', {})
            
            with transaction.atomic():
                # 首先清除現有聚類分配
                with connection.cursor() as cursor:
                    cursor.execute("""
                        UPDATE chat_message_embeddings_1024 
                        SET cluster_id = NULL, confidence_score = 0.0, updated_at = NOW()
                    """)
                
                # 更新新的聚類分配
                updated_count = 0
                
                for cluster_id, point_indices in clusters.items():
                    # 計算聚類信心分數
                    cluster_stats = clustering_result.get('stats', {})
                    quality_metrics = cluster_stats.get('quality_metrics', {})
                    confidence = 0.5  # 預設信心分數
                    
                    if cluster_id in quality_metrics:
                        avg_similarity = quality_metrics[cluster_id].get('avg_similarity', 0.5)
                        confidence = min(0.9, max(0.1, avg_similarity))
                    
                    # 獲取對應的向量數據
                    vector_data = self.get_vector_data()
                    
                    for idx in point_indices:
                        if idx < len(vector_data):
                            embedding_id = vector_data[idx]['id']
                            
                            with connection.cursor() as cursor:
                                cursor.execute("""
                                    UPDATE chat_message_embeddings_1024 
                                    SET cluster_id = %s, confidence_score = %s, updated_at = NOW()
                                    WHERE id = %s
                                """, [cluster_id, confidence, embedding_id])
                                
                            updated_count += 1
                
                self.logger.info(f"聚類分配更新完成: 更新了 {updated_count} 筆記錄")
                return True
                
        except Exception as e:
            self.logger.error(f"更新聚類分配失敗: {str(e)}")
            return False
    
    def auto_categorize_clusters(self, clustering_result: Dict) -> Dict:
        """
        基於聚類結果自動生成類別名稱
        
        Args:
            clustering_result: 聚類結果
            
        Returns:
            類別分配建議
        """
        try:
            categories = {}
            stats = clustering_result.get('stats', {})
            cluster_keywords = stats.get('cluster_keywords', {})
            
            # 預定義的類別映射規則
            category_rules = {
                'hardware': ['Samsung', 'ULINK', 'SSD', 'device', 'hardware', '硬體', '設備'],
                'jenkins': ['Jenkins', 'pipeline', 'stage', 'build', 'job', '流水線'],
                'testing': ['測試', 'test', 'fail', 'error', 'bug', '問題', '錯誤'],
                'ansible': ['Ansible', 'playbook', 'deploy', 'automation', '自動化'],
                'network': ['network', 'connection', 'IP', 'ping', '網路', '連接'],
                'performance': ['performance', 'speed', 'slow', 'timeout', '效能', '速度'],
                'configuration': ['config', 'setting', 'parameter', '配置', '設定'],
                'troubleshooting': ['troubleshoot', 'debug', 'solve', 'fix', '排除', '解決']
            }
            
            for cluster_id, keywords in cluster_keywords.items():
                best_category = 'general'
                best_score = 0
                
                for category, rule_keywords in category_rules.items():
                    score = 0
                    for keyword in keywords.keys():
                        if keyword.lower() in [rk.lower() for rk in rule_keywords]:
                            score += keywords[keyword]
                    
                    if score > best_score:
                        best_score = score
                        best_category = category
                
                categories[cluster_id] = {
                    'category': best_category,
                    'confidence': min(0.9, best_score / 10.0),  # 標準化分數
                    'keywords': list(keywords.keys())[:5]  # 前5個關鍵字
                }
            
            return categories
            
        except Exception as e:
            self.logger.error(f"自動分類失敗: {str(e)}")
            return {}
    
    def perform_clustering_analysis(self, algorithm: str = 'kmeans') -> Dict:
        """
        執行完整的聚類分析
        
        Args:
            algorithm: 聚類算法 ('kmeans' 或 'dbscan')
            
        Returns:
            完整的聚類分析結果
        """
        try:
            self.logger.info(f"開始聚類分析: algorithm={algorithm}")
            
            # 獲取向量數據
            vector_data = self.get_vector_data()
            if not vector_data:
                return {'error': '沒有可用的向量數據'}
            
            # 執行聚類
            if algorithm.lower() == 'kmeans':
                clustering_result = self.simple_kmeans_clustering(vector_data)
            elif algorithm.lower() == 'dbscan':
                clustering_result = self.density_based_clustering(vector_data)
            else:
                return {'error': f'不支援的聚類算法: {algorithm}'}
            
            if 'error' in clustering_result:
                return clustering_result
            
            # 自動分類
            categories = self.auto_categorize_clusters(clustering_result)
            
            # 更新資料庫
            update_success = self.update_cluster_assignments(clustering_result)
            
            # 完整結果
            result = {
                'clustering_result': clustering_result,
                'category_suggestions': categories,
                'database_updated': update_success,
                'analysis_summary': {
                    'total_messages': len(vector_data),
                    'n_clusters': clustering_result.get('stats', {}).get('n_clusters', 0),
                    'algorithm_used': algorithm,
                    'categories_generated': len(categories)
                }
            }
            
            self.logger.info(f"聚類分析完成: {result['analysis_summary']}")
            return result
            
        except Exception as e:
            self.logger.error(f"聚類分析失敗: {str(e)}")
            return {'error': str(e)}

# 便利函數
def get_clustering_service(min_cluster_size: int = 3) -> ChatClusteringService:
    """獲取聚類服務實例"""
    return ChatClusteringService(min_cluster_size=min_cluster_size)

def perform_auto_clustering(algorithm: str = 'kmeans') -> Dict:
    """執行自動聚類便利函數"""
    service = get_clustering_service()
    return service.perform_clustering_analysis(algorithm)

def get_cluster_categories() -> Dict:
    """獲取當前聚類類別便利函數"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT cluster_id, predicted_category, COUNT(*) as count,
                       AVG(confidence_score) as avg_confidence
                FROM chat_message_embeddings_1024
                WHERE cluster_id IS NOT NULL
                GROUP BY cluster_id, predicted_category
                ORDER BY cluster_id, count DESC
            """)
            
            results = {}
            for row in cursor.fetchall():
                cluster_id, category, count, avg_confidence = row
                if cluster_id not in results:
                    results[cluster_id] = []
                results[cluster_id].append({
                    'category': category,
                    'count': count,
                    'confidence': float(avg_confidence) if avg_confidence else 0.0
                })
            
            return results
            
    except Exception as e:
        logger.error(f"獲取聚類類別失敗: {str(e)}")
        return {}