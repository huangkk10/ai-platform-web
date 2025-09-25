#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化版向量化 RAG 測試腳本
僅使用內建函式庫，無需額外依賴
"""

import requests
import json
import sqlite3
import time
import math
from typing import List, Dict, Any, Tuple

# Dify API 配置
DIFY_CONFIG = {
    'api_url': 'http://10.10.172.37/v1/chat-messages',
    'api_key': 'app-R5nTTZw6jSQX75sDvyUMxLgo',
    'base_url': 'http://10.10.172.37'
}

class SimpleVectorizer:
    """簡化版文字向量化器"""
    
    @staticmethod
    def text_to_vector(text: str, dim: int = 100) -> List[float]:
        """將文字轉換為簡化向量"""
        vector = [0.0] * dim
        
        # 1. 文字基本特徵
        vector[0] = len(text) / 100.0  # 文字長度
        vector[1] = text.count(' ') / len(text) if text else 0  # 空格比例
        vector[2] = sum(1 for c in text if c.isdigit()) / len(text) if text else 0  # 數字比例
        
        # 2. 字元頻率特徵（使用常見中文字和英文字母）
        common_chars = '一二三四五六七八九十員工部門薪資職位技術業務abcdefghijklmnopqrstuvwxyz0123456789'
        
        for i, char in enumerate(common_chars[:dim-10]):
            if char in text.lower():
                vector[i + 3] = text.lower().count(char) / len(text)
        
        # 3. 關鍵詞特徵
        keywords = ['技術', '業務', '工程師', '經理', '薪資', '部門', '員工', '職位']
        for i, keyword in enumerate(keywords):
            if i + 90 < dim:
                vector[i + 90] = text.count(keyword) / len(text) if text else 0
        
        return vector
    
    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """計算餘弦相似度"""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)

class SimpleVectorDB:
    """簡化版向量資料庫"""
    
    def __init__(self):
        self.vectors = []
        self.texts = []
        self.metadata = []
    
    def add(self, text: str, metadata: Dict, vector: List[float] = None):
        """添加文件到向量資料庫"""
        if vector is None:
            vector = SimpleVectorizer.text_to_vector(text)
        
        self.vectors.append(vector)
        self.texts.append(text)
        self.metadata.append(metadata)
    
    def search(self, query: str, top_k: int = 5, threshold: float = 0.1) -> List[Tuple[str, Dict, float]]:
        """搜尋相似文件"""
        if not self.vectors:
            return []
        
        query_vector = SimpleVectorizer.text_to_vector(query)
        similarities = []
        
        for i, vector in enumerate(self.vectors):
            similarity = SimpleVectorizer.cosine_similarity(query_vector, vector)
            if similarity >= threshold:
                similarities.append((i, similarity))
        
        # 按相似度排序
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for i, (idx, score) in enumerate(similarities[:top_k]):
            results.append((self.texts[idx], self.metadata[idx], score))
        
        return results

class SimpleRAGTester:
    """簡化版 RAG 測試器"""
    
    def __init__(self):
        self.vector_db = SimpleVectorDB()
        self.loaded = False
    
    def load_data(self) -> bool:
        """載入並向量化資料"""
        print("📊 載入員工資料並建立向量索引...")
        
        try:
            conn = sqlite3.connect('tests/test_dify_integration/company.db')
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM employees")
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            conn.close()
            
            print(f"📋 載入 {len(rows)} 筆員工資料")
            
            for row in rows:
                employee = dict(zip(columns, row))
                
                # 構建搜尋用文字
                text = f"""
                姓名: {employee['name']}
                部門: {employee['department']}
                職位: {employee['position']}
                薪資: {employee['salary']}
                入職日期: {employee['hire_date']}
                郵箱: {employee['email']}
                """.strip()
                
                # 添加到向量資料庫
                self.vector_db.add(text, employee)
                print(f"✅ 已索引: {employee['name']} - {employee['department']}")
            
            self.loaded = True
            print(f"🎯 向量索引建立完成，共 {len(rows)} 筆資料")
            return True
            
        except Exception as e:
            print(f"❌ 資料載入失敗: {e}")
            return False
    
    def call_dify_ai(self, question: str, context: str = "") -> Dict:
        """調用 Dify AI"""
        headers = {
            'Authorization': f'Bearer {DIFY_CONFIG["api_key"]}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'inputs': {'context': context} if context else {},
            'query': question,
            'response_mode': 'blocking',
            'user': 'simple_rag_test'
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                DIFY_CONFIG['api_url'],
                headers=headers,
                json=payload,
                timeout=30
            )
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'answer': result.get('answer', ''),
                    'response_time': elapsed
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
    
    def test_queries(self):
        """測試查詢"""
        if not self.loaded:
            print("❌ 請先載入資料")
            return
        
        print("\n" + "="*50)
        print("🔍 開始測試向量搜尋查詢")
        print("="*50)
        
        test_cases = [
            {
                'question': '技術部有哪些員工？',
                'description': '部門查詢測試'
            },
            {
                'question': '薪資最高的員工是誰？',
                'description': '薪資查詢測試'
            },
            {
                'question': '有哪些工程師？',
                'description': '職位查詢測試'
            },
            {
                'question': '李美華的基本資訊',
                'description': '個人資訊查詢'
            },
            {
                'question': '2022年入職的員工',
                'description': '時間查詢測試'
            }
        ]
        
        results = []
        
        for i, test_case in enumerate(test_cases, 1):
            question = test_case['question']
            description = test_case['description']
            
            print(f"\n🔸 測試 {i}: {description}")
            print(f"❓ 問題: {question}")
            print("-" * 40)
            
            # 1. 向量搜尋
            search_start = time.time()
            search_results = self.vector_db.search(question, top_k=3, threshold=0.05)
            search_time = time.time() - search_start
            
            if search_results:
                print(f"🎯 找到 {len(search_results)} 個相關結果 ({search_time:.3f}s)")
                
                # 顯示搜尋結果
                context_parts = []
                for j, (text, metadata, score) in enumerate(search_results, 1):
                    print(f"   {j}. {metadata['name']} ({metadata['department']}) - 相似度: {score:.3f}")
                    context_parts.append(text)
                
                # 構建上下文
                context = "\n---\n".join(context_parts)
                
                # 2. 調用 AI
                ai_result = self.call_dify_ai(question, context)
                
                if ai_result['success']:
                    print(f"✅ AI 回答 ({ai_result['response_time']:.1f}s):")
                    print(f"📝 {ai_result['answer']}")
                    
                    results.append({
                        'question': question,
                        'description': description,
                        'search_time': search_time,
                        'search_count': len(search_results),
                        'ai_time': ai_result['response_time'],
                        'success': True
                    })
                else:
                    print(f"❌ AI 調用失敗: {ai_result['error']}")
                    results.append({
                        'question': question,
                        'description': description,
                        'search_time': search_time,
                        'search_count': len(search_results),
                        'success': False,
                        'error': ai_result['error']
                    })
            else:
                print("❌ 未找到相關資料")
                results.append({
                    'question': question,
                    'description': description,
                    'search_time': search_time,
                    'search_count': 0,
                    'success': False,
                    'error': '無相關結果'
                })
            
            time.sleep(0.5)  # 避免請求過快
        
        return results
    
    def test_comparison(self):
        """比較測試：向量搜尋 vs 全量資料"""
        print("\n" + "="*50)
        print("⚖️ 效能比較測試")
        print("="*50)
        
        question = "技術部的員工薪資情況如何？"
        print(f"🔸 測試問題: {question}")
        
        # 方法1：向量搜尋
        print("\n🔹 方法1: 向量搜尋")
        vector_start = time.time()
        search_results = self.vector_db.search(question, top_k=10)
        
        if search_results:
            context_parts = [text for text, _, _ in search_results]
            context = "\n---\n".join(context_parts)
            ai_result1 = self.call_dify_ai(question, context)
            vector_total = time.time() - vector_start
            
            print(f"✅ 找到 {len(search_results)} 個結果")
            if ai_result1['success']:
                print(f"📝 AI 回答: {ai_result1['answer'][:100]}...")
                print(f"⏱️ 總耗時: {vector_total:.1f}s")
        
        # 方法2：全量資料
        print("\n🔹 方法2: 全量資料查詢")
        full_start = time.time()
        
        try:
            conn = sqlite3.connect('tests/test_dify_integration/company.db')
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM employees WHERE department = '技術部'")
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            conn.close()
            
            employees = [dict(zip(columns, row)) for row in rows]
            full_context = json.dumps(employees, ensure_ascii=False, indent=2)
            
            ai_result2 = self.call_dify_ai(question, full_context)
            full_total = time.time() - full_start
            
            print(f"✅ 直接查詢 {len(employees)} 筆資料")
            if ai_result2['success']:
                print(f"📝 AI 回答: {ai_result2['answer'][:100]}...")
                print(f"⏱️ 總耗時: {full_total:.1f}s")
            
            # 比較結果
            print("\n🔸 比較結果:")
            print(f"📊 向量搜尋: {vector_total:.1f}s")
            print(f"📊 全量查詢: {full_total:.1f}s")
            
            if vector_total < full_total:
                print("🏆 向量搜尋更快")
            else:
                print("🏆 全量查詢更快")
                
        except Exception as e:
            print(f"❌ 全量查詢失敗: {e}")

def main():
    """主程式"""
    print("🚀 簡化版向量 RAG 測試系統")
    print("=" * 50)
    print(f"🔗 API: {DIFY_CONFIG['api_url']}")
    print(f"💾 資料庫: tests/test_dify_integration/company.db")
    print("🧠 向量化: 內建簡化算法")
    print("=" * 50)
    
    # 測試 API 連接
    print("\n🔍 測試 Dify API 連接...")
    tester = SimpleRAGTester()
    test_result = tester.call_dify_ai("Hello, this is a connection test.")
    
    if test_result['success']:
        print("✅ API 連接正常")
    else:
        print(f"❌ API 連接失敗: {test_result['error']}")
        return
    
    # 載入資料
    if not tester.load_data():
        return
    
    # 執行查詢測試
    query_results = tester.test_queries()
    
    # 執行比較測試
    tester.test_comparison()
    
    # 總結報告
    print("\n" + "="*50)
    print("📊 測試總結")
    print("="*50)
    
    if query_results:
        successful = [r for r in query_results if r.get('success', False)]
        print(f"✅ 成功查詢: {len(successful)}/{len(query_results)}")
        
        if successful:
            avg_search = sum(r['search_time'] for r in successful) / len(successful)
            avg_ai = sum(r['ai_time'] for r in successful) / len(successful)
            print(f"⏱️ 平均搜尋時間: {avg_search:.3f}s")
            print(f"⏱️ 平均 AI 時間: {avg_ai:.1f}s")
    
    print("\n💡 系統特點:")
    print("✨ 無需額外依賴，使用內建函式庫")
    print("🔍 基於字元頻率和關鍵詞的簡化向量化")
    print("⚡ 快速部署，適合基本測試需求")
    print("🔧 如需更好效果，請安裝 sentence-transformers")
    
    print("\n✅ 測試完成！")

if __name__ == "__main__":
    main()