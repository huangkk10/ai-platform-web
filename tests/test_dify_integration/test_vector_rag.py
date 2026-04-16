#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向量化 RAG 測試腳本
將 company.db 資料轉換為向量資料，並測試基於向量搜尋的 AI 問答功能
"""

import requests
import json
import sqlite3
import time
import os
import numpy as np
from typing import List, Dict, Any, Tuple
import hashlib

# 嘗試導入向量化相關套件
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("⚠️ sentence-transformers 未安裝，將使用簡化版向量化")

try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("⚠️ chromadb 未安裝，將使用內建向量搜尋")

# Dify API 配置
DIFY_CONFIG = {
    'api_url': 'http://10.253.43.244/v1/chat-messages',
    'api_key': 'app-R5nTTZw6jSQX75sDvyUMxLgo',
    'base_url': 'http://10.253.43.244'
}

# 向量化配置
VECTOR_CONFIG = {
    'model_name': 'all-MiniLM-L6-v2',  # 輕量化的向量模型
    'vector_dim': 384,  # 向量維度
    'similarity_threshold': 0.7,  # 相似度閾值
    'max_results': 5  # 最大搜尋結果數
}

class SimpleVectorStore:
    """簡化版向量資料庫（當 ChromaDB 不可用時使用）"""
    
    def __init__(self):
        self.vectors = []
        self.metadata = []
        self.texts = []
    
    def add_vectors(self, vectors: List[List[float]], texts: List[str], metadata: List[Dict]):
        """添加向量資料"""
        self.vectors.extend(vectors)
        self.texts.extend(texts)
        self.metadata.extend(metadata)
    
    def search(self, query_vector: List[float], top_k: int = 5) -> List[Tuple[str, Dict, float]]:
        """搜尋相似向量"""
        if not self.vectors:
            return []
        
        # 計算餘弦相似度
        query_vector = np.array(query_vector)
        similarities = []
        
        for i, vector in enumerate(self.vectors):
            vector = np.array(vector)
            similarity = np.dot(query_vector, vector) / (np.linalg.norm(query_vector) * np.linalg.norm(vector))
            similarities.append((i, similarity))
        
        # 排序並返回前 k 個結果
        similarities.sort(key=lambda x: x[1], reverse=True)
        results = []
        
        for i, (idx, score) in enumerate(similarities[:top_k]):
            if score >= VECTOR_CONFIG['similarity_threshold']:
                results.append((self.texts[idx], self.metadata[idx], score))
        
        return results

class VectorRAGTester:
    """向量化 RAG 測試器"""
    
    def __init__(self):
        self.embedding_model = None
        self.vector_store = None
        self.setup_embedding_model()
        self.setup_vector_store()
    
    def setup_embedding_model(self):
        """設置嵌入模型"""
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                print(f"🔧 載入嵌入模型: {VECTOR_CONFIG['model_name']}")
                self.embedding_model = SentenceTransformer(VECTOR_CONFIG['model_name'])
                print("✅ 嵌入模型載入成功")
            except Exception as e:
                print(f"❌ 嵌入模型載入失敗: {e}")
                self.embedding_model = None
        else:
            print("⚠️ 使用簡化版向量化（基於文字長度和字元頻率）")
    
    def setup_vector_store(self):
        """設置向量資料庫"""
        if CHROMADB_AVAILABLE:
            try:
                print("🔧 設置 ChromaDB 向量資料庫")
                self.chroma_client = chromadb.Client()
                self.collection = self.chroma_client.create_collection(
                    name="company_employees",
                    metadata={"hnsw:space": "cosine"}
                )
                print("✅ ChromaDB 向量資料庫設置成功")
            except Exception as e:
                print(f"❌ ChromaDB 設置失敗: {e}")
                self.vector_store = SimpleVectorStore()
        else:
            print("🔧 使用簡化版向量資料庫")
            self.vector_store = SimpleVectorStore()
    
    def simple_embedding(self, text: str) -> List[float]:
        """簡化版文字嵌入（當無法使用 SentenceTransformers 時）"""
        # 基於字元頻率和位置的簡單向量化
        vector = [0.0] * 100  # 簡化為 100 維
        
        # 文字長度特徵
        vector[0] = len(text) / 100.0
        
        # 字元頻率特徵
        char_count = {}
        for char in text.lower():
            char_count[char] = char_count.get(char, 0) + 1
        
        # 將常見字元映射到向量維度
        common_chars = 'abcdefghijklmnopqrstuvwxyz0123456789一二三四五六七八九十'
        for i, char in enumerate(common_chars[:99]):
            if char in char_count:
                vector[i + 1] = char_count[char] / len(text)
        
        return vector
    
    def get_embedding(self, text: str) -> List[float]:
        """獲取文字嵌入向量"""
        if self.embedding_model:
            try:
                embedding = self.embedding_model.encode(text)
                return embedding.tolist()
            except Exception as e:
                print(f"⚠️ 嵌入生成失敗，使用簡化版: {e}")
                return self.simple_embedding(text)
        else:
            return self.simple_embedding(text)
    
    def load_and_vectorize_data(self):
        """載入並向量化資料庫資料"""
        print("\n" + "="*60)
        print("📊 載入並向量化員工資料")
        print("="*60)
        
        try:
            # 連接資料庫
            conn = sqlite3.connect('tests/test_dify_integration/company.db')
            cursor = conn.cursor()
            
            # 獲取所有員工資料
            cursor.execute("SELECT * FROM employees")
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            conn.close()
            
            print(f"📋 載入 {len(rows)} 筆員工資料")
            
            # 轉換為文字並向量化
            texts = []
            metadata = []
            vectors = []
            
            for row in rows:
                # 將員工資料轉換為可搜尋的文字
                employee_data = dict(zip(columns, row))
                
                # 構建描述性文字
                text = f"""
                員工姓名: {employee_data['name']}
                部門: {employee_data['department']}
                職位: {employee_data['position']}
                薪資: {employee_data['salary']}
                入職日期: {employee_data['hire_date']}
                電子郵件: {employee_data['email']}
                """.strip()
                
                # 生成向量
                vector = self.get_embedding(text)
                
                texts.append(text)
                metadata.append(employee_data)
                vectors.append(vector)
                
                print(f"✅ 已向量化: {employee_data['name']} ({employee_data['department']})")
            
            # 存儲到向量資料庫
            if CHROMADB_AVAILABLE and hasattr(self, 'collection'):
                try:
                    # 生成唯一 ID
                    ids = [f"emp_{i}" for i in range(len(texts))]
                    
                    self.collection.add(
                        embeddings=vectors,
                        documents=texts,
                        metadatas=metadata,
                        ids=ids
                    )
                    print("✅ 資料已存儲到 ChromaDB")
                except Exception as e:
                    print(f"⚠️ ChromaDB 存儲失敗，使用簡化版: {e}")
                    self.vector_store = SimpleVectorStore()
                    self.vector_store.add_vectors(vectors, texts, metadata)
            else:
                self.vector_store.add_vectors(vectors, texts, metadata)
                print("✅ 資料已存儲到簡化版向量資料庫")
            
            print(f"🎯 向量化完成，總共處理 {len(texts)} 筆資料")
            return True
            
        except Exception as e:
            print(f"❌ 資料載入失敗: {e}")
            return False
    
    def vector_search(self, query: str, top_k: int = 3) -> List[Tuple[str, Dict, float]]:
        """向量搜尋"""
        try:
            # 將查詢轉換為向量
            query_vector = self.get_embedding(query)
            
            if CHROMADB_AVAILABLE and hasattr(self, 'collection'):
                # 使用 ChromaDB 搜尋
                results = self.collection.query(
                    query_embeddings=[query_vector],
                    n_results=top_k
                )
                
                search_results = []
                for i in range(len(results['documents'][0])):
                    text = results['documents'][0][i]
                    metadata = results['metadatas'][0][i]
                    distance = results['distances'][0][i]
                    similarity = 1 - distance  # 轉換為相似度分數
                    search_results.append((text, metadata, similarity))
                
                return search_results
            else:
                # 使用簡化版搜尋
                return self.vector_store.search(query_vector, top_k)
        
        except Exception as e:
            print(f"❌ 向量搜尋失敗: {e}")
            return []
    
    def call_dify_with_context(self, question: str, context_data: str = "") -> dict:
        """調用 Dify API 並傳入上下文"""
        headers = {
            'Authorization': f'Bearer {DIFY_CONFIG["api_key"]}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'inputs': {
                'context': context_data
            } if context_data else {},
            'query': question,
            'response_mode': 'blocking',
            'user': 'vector_rag_test'
        }
        
        try:
            print(f"🤖 調用 Dify AI: {question[:50]}...")
            start_time = time.time()
            
            response = requests.post(
                DIFY_CONFIG['api_url'],
                headers=headers,
                json=payload,
                timeout=60
            )
            
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'answer': result.get('answer', ''),
                    'response_time': elapsed,
                    'message_id': result.get('message_id', ''),
                    'conversation_id': result.get('conversation_id', '')
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}",
                    'response_time': elapsed
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'response_time': 0
            }
    
    def test_vector_rag_queries(self):
        """測試向量化 RAG 查詢"""
        print("\n" + "="*60)
        print("🔍 向量化 RAG 查詢測試")
        print("="*60)
        
        test_queries = [
            {
                'question': '技術部有哪些員工？他們的薪資如何？',
                'description': '部門篩選查詢'
            },
            {
                'question': '薪資最高的員工是誰？',
                'description': '薪資排序查詢'
            },
            {
                'question': '有哪些軟體工程師？',
                'description': '職位篩選查詢'
            },
            {
                'question': '2022年入職的員工有哪些？',
                'description': '時間篩選查詢'
            },
            {
                'question': '李美華的詳細資訊',
                'description': '特定員工查詢'
            }
        ]
        
        results = []
        
        for i, query_info in enumerate(test_queries, 1):
            question = query_info['question']
            description = query_info['description']
            
            print(f"\n🔸 測試 {i}: {description}")
            print(f"❓ 問題: {question}")
            print("-" * 50)
            
            # 1. 向量搜尋相關資料
            search_start = time.time()
            search_results = self.vector_search(question, top_k=3)
            search_time = time.time() - search_start
            
            if search_results:
                print(f"🎯 找到 {len(search_results)} 個相關結果 ({search_time:.2f}s)")
                
                # 構建上下文
                context_texts = []
                for text, metadata, score in search_results:
                    print(f"   - {metadata['name']} ({metadata['department']}) 相似度: {score:.3f}")
                    context_texts.append(text)
                
                context_data = "\n".join(context_texts)
                
                # 2. 使用搜尋結果作為上下文調用 AI
                ai_result = self.call_dify_with_context(question, context_data)
                
                if ai_result['success']:
                    print(f"✅ AI 回答 ({ai_result['response_time']:.1f}s):")
                    print(f"📝 {ai_result['answer']}")
                    
                    results.append({
                        'question': question,
                        'description': description,
                        'search_time': search_time,
                        'search_results_count': len(search_results),
                        'ai_success': True,
                        'ai_response_time': ai_result['response_time'],
                        'total_time': search_time + ai_result['response_time']
                    })
                else:
                    print(f"❌ AI 調用失敗: {ai_result['error']}")
                    results.append({
                        'question': question,
                        'description': description,
                        'search_time': search_time,
                        'search_results_count': len(search_results),
                        'ai_success': False,
                        'error': ai_result['error']
                    })
            else:
                print("❌ 未找到相關資料")
                results.append({
                    'question': question,
                    'description': description,
                    'search_time': search_time,
                    'search_results_count': 0,
                    'ai_success': False,
                    'error': '未找到相關資料'
                })
            
            time.sleep(1)  # 避免請求過於頻繁
        
        return results
    
    def compare_vector_vs_traditional_rag(self):
        """比較向量化 RAG 與傳統 RAG"""
        print("\n" + "="*60)
        print("⚖️ 向量化 RAG vs 傳統 RAG 比較")
        print("="*60)
        
        test_question = "技術部的平均薪資是多少？"
        print(f"🔸 測試問題: {test_question}")
        
        # 1. 向量化 RAG 方法
        print("\n🔹 向量化 RAG 方法:")
        print("-" * 30)
        
        vector_start = time.time()
        search_results = self.vector_search(test_question, top_k=5)
        
        if search_results:
            context_texts = [text for text, _, _ in search_results]
            context_data = "\n".join(context_texts)
            vector_ai_result = self.call_dify_with_context(test_question, context_data)
            vector_total_time = time.time() - vector_start
            
            print(f"✅ 向量搜尋找到 {len(search_results)} 個結果")
            if vector_ai_result['success']:
                print(f"📝 AI 回答: {vector_ai_result['answer'][:150]}...")
                print(f"⏱️ 總耗時: {vector_total_time:.1f}s")
        
        # 2. 傳統 RAG 方法（直接傳入所有資料）
        print("\n🔹 傳統 RAG 方法:")
        print("-" * 30)
        
        traditional_start = time.time()
        
        # 獲取所有員工資料
        try:
            conn = sqlite3.connect('tests/test_dify_integration/company.db')
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM employees WHERE department = '技術部'")
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            conn.close()
            
            employees = [dict(zip(columns, row)) for row in rows]
            traditional_context = json.dumps(employees, ensure_ascii=False, indent=2)
            
            traditional_ai_result = self.call_dify_with_context(test_question, traditional_context)
            traditional_total_time = time.time() - traditional_start
            
            print(f"✅ 直接查詢找到 {len(employees)} 筆資料")
            if traditional_ai_result['success']:
                print(f"📝 AI 回答: {traditional_ai_result['answer'][:150]}...")
                print(f"⏱️ 總耗時: {traditional_total_time:.1f}s")
        
        except Exception as e:
            print(f"❌ 傳統方法失敗: {e}")
        
        # 3. 比較結果
        print("\n🔸 比較總結:")
        print("-" * 30)
        if 'vector_total_time' in locals() and 'traditional_total_time' in locals():
            print(f"📊 向量化 RAG: {vector_total_time:.1f}s")
            print(f"📊 傳統 RAG: {traditional_total_time:.1f}s")
            if vector_total_time < traditional_total_time:
                print("🏆 向量化 RAG 更快")
            else:
                print("🏆 傳統 RAG 更快")

def main():
    """主測試函數"""
    print("🚀 向量化 RAG 測試系統")
    print("=" * 60)
    print(f"🔗 API 端點: {DIFY_CONFIG['api_url']}")
    print(f"🧠 嵌入模型: {VECTOR_CONFIG['model_name']}")
    print(f"📏 向量維度: {VECTOR_CONFIG['vector_dim']}")
    print("=" * 60)
    
    # 檢查依賴
    print("\n🔍 檢查系統依賴:")
    print(f"📦 sentence-transformers: {'✅ 可用' if SENTENCE_TRANSFORMERS_AVAILABLE else '❌ 不可用'}")
    print(f"📦 chromadb: {'✅ 可用' if CHROMADB_AVAILABLE else '❌ 不可用'}")
    
    # 初始化測試器
    tester = VectorRAGTester()
    
    # 1. 載入並向量化資料
    if not tester.load_and_vectorize_data():
        print("\n❌ 資料載入失敗，測試終止")
        return
    
    # 2. 測試向量化 RAG 查詢
    query_results = tester.test_vector_rag_queries()
    
    # 3. 比較不同方法
    tester.compare_vector_vs_traditional_rag()
    
    # 4. 總結報告
    print("\n" + "="*60)
    print("📊 測試總結報告")
    print("="*60)
    
    if query_results:
        successful_queries = [r for r in query_results if r.get('ai_success', False)]
        print(f"✅ 成功查詢: {len(successful_queries)}/{len(query_results)}")
        
        if successful_queries:
            avg_search_time = sum(r['search_time'] for r in successful_queries) / len(successful_queries)
            avg_ai_time = sum(r['ai_response_time'] for r in successful_queries) / len(successful_queries)
            avg_total_time = sum(r['total_time'] for r in successful_queries) / len(successful_queries)
            
            print(f"⏱️ 平均向量搜尋時間: {avg_search_time:.2f}s")
            print(f"⏱️ 平均 AI 回應時間: {avg_ai_time:.1f}s")
            print(f"⏱️ 平均總時間: {avg_total_time:.1f}s")
    
    print("\n💡 建議:")
    if not SENTENCE_TRANSFORMERS_AVAILABLE:
        print("🔧 安裝 sentence-transformers 以獲得更好的向量化效果:")
        print("   pip install sentence-transformers")
    
    if not CHROMADB_AVAILABLE:
        print("🔧 安裝 chromadb 以獲得更好的向量資料庫效能:")
        print("   pip install chromadb")
    
    print("\n✅ 向量化 RAG 測試完成！")

if __name__ == "__main__":
    main()