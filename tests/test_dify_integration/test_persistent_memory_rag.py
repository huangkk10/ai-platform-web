#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
永久記憶向量化 RAG 測試腳本
基於 test_vector_rag.py，增加持續對話和記憶功能
讓 AI 能夠記住之前的對話內容和學習到的知識
"""

import requests
import json
import sqlite3
import time
import os
import uuid
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
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
    'api_url': 'http://10.10.172.37/v1/chat-messages',
    'api_key': 'app-R5nTTZw6jSQX75sDvyUMxLgo',  # 應用 API Token
    'dataset_api_key': 'dataset-JLa32OwILQHkgPqYStTCW4sC',  # 知識庫 API Token
    'base_url': 'http://10.10.172.37'
}

# 向量化配置
VECTOR_CONFIG = {
    'model_name': 'all-MiniLM-L6-v2',
    'vector_dim': 384,
    'similarity_threshold': 0.7,
    'max_results': 5
}

# 記憶配置
MEMORY_CONFIG = {
    'memory_file': 'tests/test_dify_integration/memory_data.json',
    'conversation_file': 'tests/test_dify_integration/conversation_history.json',
    'max_conversation_length': 20,  # 最大對話輪數
    'max_memory_items': 100,  # 最大記憶項目數
    'memory_decay_days': 30  # 記憶衰減天數
}

class PersistentMemoryStore:
    """持久化記憶存儲系統"""
    
    def __init__(self):
        self.memory_file = MEMORY_CONFIG['memory_file']
        self.conversation_file = MEMORY_CONFIG['conversation_file']
        self.memory_data = self.load_memory()
        self.conversation_history = self.load_conversation_history()
    
    def load_memory(self) -> Dict:
        """載入記憶資料"""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"📚 載入 {len(data.get('knowledge_base', []))} 筆記憶資料")
                    return data
        except Exception as e:
            print(f"⚠️ 載入記憶資料失敗: {e}")
        
        return {
            'knowledge_base': [],  # 學習到的知識
            'user_preferences': {},  # 用戶偏好
            'learned_facts': [],  # 學習到的事實
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        }
    
    def save_memory(self):
        """保存記憶資料"""
        try:
            self.memory_data['last_updated'] = datetime.now().isoformat()
            os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
            
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(self.memory_data, f, ensure_ascii=False, indent=2)
            print(f"💾 記憶資料已保存到 {self.memory_file}")
        except Exception as e:
            print(f"❌ 保存記憶資料失敗: {e}")
    
    def load_conversation_history(self) -> List[Dict]:
        """載入對話歷史"""
        try:
            if os.path.exists(self.conversation_file):
                with open(self.conversation_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                    print(f"📝 載入 {len(history)} 筆對話記錄")
                    return history
        except Exception as e:
            print(f"⚠️ 載入對話歷史失敗: {e}")
        
        return []
    
    def save_conversation_history(self):
        """保存對話歷史"""
        try:
            # 限制對話歷史長度
            if len(self.conversation_history) > MEMORY_CONFIG['max_conversation_length']:
                self.conversation_history = self.conversation_history[-MEMORY_CONFIG['max_conversation_length']:]
            
            os.makedirs(os.path.dirname(self.conversation_file), exist_ok=True)
            
            with open(self.conversation_file, 'w', encoding='utf-8') as f:
                json.dump(self.conversation_history, f, ensure_ascii=False, indent=2)
            print(f"💾 對話歷史已保存到 {self.conversation_file}")
        except Exception as e:
            print(f"❌ 保存對話歷史失敗: {e}")
    
    def add_to_knowledge_base(self, question: str, answer: str, context: str = "", source: str = "vector_search"):
        """添加到知識庫"""
        knowledge_item = {
            'id': str(uuid.uuid4()),
            'question': question,
            'answer': answer,
            'context': context,
            'source': source,
            'timestamp': datetime.now().isoformat(),
            'access_count': 0
        }
        
        self.memory_data['knowledge_base'].append(knowledge_item)
        
        # 限制知識庫大小
        if len(self.memory_data['knowledge_base']) > MEMORY_CONFIG['max_memory_items']:
            # 移除最舊的項目
            self.memory_data['knowledge_base'] = self.memory_data['knowledge_base'][-MEMORY_CONFIG['max_memory_items']:]
        
        print(f"🧠 新知識已添加到記憶庫: {question[:50]}...")
    
    def add_conversation(self, conversation_id: str, question: str, answer: str, search_results: List = None):
        """添加對話記錄"""
        conversation_item = {
            'conversation_id': conversation_id,
            'question': question,
            'answer': answer,
            'search_results': search_results or [],
            'timestamp': datetime.now().isoformat()
        }
        
        self.conversation_history.append(conversation_item)
        print(f"📝 對話記錄已添加: {question[:30]}...")
    
    def search_knowledge_base(self, query: str, limit: int = 3) -> List[Dict]:
        """從知識庫搜尋相關知識"""
        relevant_knowledge = []
        query_lower = query.lower()
        
        for item in self.memory_data['knowledge_base']:
            # 簡單的關鍵字匹配
            question_lower = item['question'].lower()
            answer_lower = item['answer'].lower()
            
            if (any(word in question_lower for word in query_lower.split()) or
                any(word in answer_lower for word in query_lower.split())):
                
                item['access_count'] += 1  # 增加訪問次數
                relevant_knowledge.append(item)
        
        # 按訪問次數和時間排序
        relevant_knowledge.sort(key=lambda x: (x['access_count'], x['timestamp']), reverse=True)
        
        return relevant_knowledge[:limit]
    
    def get_recent_conversations(self, limit: int = 5) -> List[Dict]:
        """獲取最近的對話"""
        return self.conversation_history[-limit:] if self.conversation_history else []

class SimpleVectorStore:
    """簡化版向量資料庫"""
    
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
        
        similarities = []
        
        for i, vector in enumerate(self.vectors):
            # 簡化版餘弦相似度計算
            dot_product = sum(a * b for a, b in zip(query_vector, vector))
            norm1 = sum(a * a for a in query_vector) ** 0.5
            norm2 = sum(b * b for b in vector) ** 0.5
            
            if norm1 > 0 and norm2 > 0:
                similarity = dot_product / (norm1 * norm2)
                similarities.append((i, similarity))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        results = []
        
        for i, (idx, score) in enumerate(similarities[:top_k]):
            if score >= VECTOR_CONFIG['similarity_threshold']:
                results.append((self.texts[idx], self.metadata[idx], score))
        
        return results

class PersistentMemoryRAGTester:
    """具有永久記憶功能的 RAG 測試器"""
    
    def __init__(self):
        self.embedding_model = None
        self.vector_store = None
        self.memory_store = PersistentMemoryStore()
        self.current_conversation_id = None
        self.dataset_id = None  # Dify 知識庫 ID
        self.knowledge_base_enabled = False  # 知識庫是否啟用
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
            print("⚠️ 使用簡化版向量化")
    
    def setup_vector_store(self):
        """設置向量資料庫"""
        if CHROMADB_AVAILABLE:
            try:
                print("🔧 設置 ChromaDB 向量資料庫")
                self.chroma_client = chromadb.Client()
                self.collection = self.chroma_client.create_collection(
                    name="company_employees_persistent",
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
        """簡化版文字嵌入"""
        vector = [0.0] * 100
        vector[0] = len(text) / 100.0
        
        char_count = {}
        for char in text.lower():
            char_count[char] = char_count.get(char, 0) + 1
        
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
            conn = sqlite3.connect('tests/test_dify_integration/company.db')
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM employees")
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            conn.close()
            
            print(f"📋 載入 {len(rows)} 筆員工資料")
            
            texts = []
            metadata = []
            vectors = []
            
            for row in rows:
                employee_data = dict(zip(columns, row))
                
                text = f"""
                員工姓名: {employee_data['name']}
                部門: {employee_data['department']}
                職位: {employee_data['position']}
                薪資: {employee_data['salary']}
                入職日期: {employee_data['hire_date']}
                電子郵件: {employee_data['email']}
                """.strip()
                
                vector = self.get_embedding(text)
                
                texts.append(text)
                metadata.append(employee_data)
                vectors.append(vector)
                
                print(f"✅ 已向量化: {employee_data['name']} ({employee_data['department']})")
            
            # 存儲到向量資料庫
            if CHROMADB_AVAILABLE and hasattr(self, 'collection'):
                try:
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
    
    def create_dify_dataset(self) -> bool:
        """建立 Dify 知識庫資料集"""
        print("\n📚 建立 Dify 知識庫...")
        
        headers = {
            'Authorization': f'Bearer {DIFY_CONFIG["dataset_api_key"]}',
            'Content-Type': 'application/json'
        }
        
        dataset_data = {
            'name': f'員工資料庫_永久記憶_{int(time.time())}',
            'description': '具有永久記憶功能的員工資料庫，包含向量搜尋和對話歷史'
        }
        
        try:
            response = requests.post(
                f'{DIFY_CONFIG["base_url"]}/v1/datasets',
                headers=headers,
                json=dataset_data,
                timeout=30
            )
            
            print(f"📥 建立資料集回應: HTTP {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.dataset_id = result.get('id')
                print(f"✅ Dify 知識庫建立成功，ID: {self.dataset_id}")
                return True
            else:
                print(f"❌ 建立 Dify 知識庫失敗: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 建立 Dify 知識庫異常: {e}")
            return False
    
    def upload_to_dify_knowledge_base(self) -> bool:
        """上傳員工資料到 Dify 知識庫"""
        if not self.dataset_id:
            print("❌ 沒有資料集 ID，無法上傳")
            return False
        
        print(f"\n📄 上傳員工資料到 Dify 知識庫...")
        
        try:
            # 生成完整的員工資料檔案
            employees_content = self.generate_employees_content()
            
            # 建立臨時檔案
            temp_filename = f'tests/test_dify_integration/temp_employees_{int(time.time())}.txt'
            
            with open(temp_filename, 'w', encoding='utf-8') as f:
                f.write(employees_content)
            
            print(f"📝 員工資料檔案已生成: {temp_filename}")
            
            # 使用正確的檔案上傳 API
            headers = {
                'Authorization': f'Bearer {DIFY_CONFIG["dataset_api_key"]}'
                # 注意：檔案上傳不需要 Content-Type: application/json
            }
            
            # 上傳檔案
            with open(temp_filename, 'rb') as f:
                files = {
                    'file': (f'employees_data_{int(time.time())}.txt', f, 'text/plain')
                }
                
                data = {
                    'indexing_technique': 'high_quality',
                    'process_rule': json.dumps({
                        'mode': 'automatic',
                        'rules': {
                            'pre_processing_rules': [
                                {'id': 'remove_extra_spaces', 'enabled': True},
                                {'id': 'remove_urls_emails', 'enabled': False}
                            ],
                            'segmentation': {
                                'separator': '\n',
                                'max_tokens': 1000
                            }
                        }
                    }),
                    'duplicate_removal': 'true'
                }
                
                print(f"🚀 上傳檔案到資料集 {self.dataset_id}...")
                
                response = requests.post(
                    f'{DIFY_CONFIG["base_url"]}/v1/datasets/{self.dataset_id}/document/create_by_file',
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=60
                )
                
                print(f"📥 檔案上傳回應: HTTP {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    document_id = result.get('document', {}).get('id')
                    print(f"✅ 檔案上傳成功，文件 ID: {document_id}")
                    
                    # 清理臨時檔案
                    try:
                        os.remove(temp_filename)
                        print(f"🗑️ 臨時檔案已清理: {temp_filename}")
                    except:
                        pass
                    
                    # 等待文件處理完成
                    print("⏳ 等待文件索引建立...")
                    self.wait_for_document_processing(document_id)
                    
                    self.knowledge_base_enabled = True
                    print("🎉 Dify 知識庫上傳完成並已啟用")
                    return True
                else:
                    print(f"❌ 檔案上傳失敗: {response.text}")
                    return False
                employee_data = dict(zip(columns, row))
                
                # 構建員工文件內容
                document_content = f"""員工資料 - {employee_data['name']}

基本資訊：
- 姓名：{employee_data['name']}
- 員工編號：{employee_data['id']}
- 部門：{employee_data['department']}
- 職位：{employee_data['position']}
- 薪資：{employee_data['salary']:,} 元（月薪）
- 入職日期：{employee_data['hire_date']}
- 電子郵件：{employee_data['email']}

部門歸屬：{employee_data['department']}
職級層次：{employee_data['position']}
薪資水準：{employee_data['salary']:,} 元

聯繫資訊：
- Email: {employee_data['email']}
- 入職時間: {employee_data['hire_date']}
"""
                
                # 準備文件資料
                file_data = {
                    'name': f"{employee_data['name']}_profile.txt",
                    'text': document_content,
                    'indexing_technique': 'high_quality',  # 添加必需參數
                    'process_rule': {
                        'mode': 'automatic'
                    }
                }
                
                try:
                    # 上傳文件到資料集
                    response = requests.post(
                        f'{DIFY_CONFIG["base_url"]}/v1/datasets/{self.dataset_id}/document/create_by_text',
                        headers=headers,
                        json=file_data,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        success_count += 1
                        print(f"✅ 上傳員工 {employee_data['name']} 成功 ({success_count}/{len(rows)})")
                    else:
                        print(f"❌ 上傳員工 {employee_data['name']} 失敗: HTTP {response.status_code}")
                        print(f"   回應: {response.text}")
                    
                    # 避免請求過於頻繁
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"❌ 上傳員工 {employee_data['name']} 異常: {e}")
            
            print(f"\n📊 上傳結果: {success_count}/{len(rows)} 份文件成功")
            
            if success_count > 0:
                self.knowledge_base_enabled = True
                print("✅ Dify 知識庫已啟用")
                return True
            else:
                return False
                
        except Exception as e:
            print(f"❌ 上傳到 Dify 知識庫失敗: {e}")
            return False
    
    def generate_employees_content(self) -> str:
        """生成員工資料內容"""
        try:
            conn = sqlite3.connect('tests/test_dify_integration/company.db')
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM employees")
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            conn.close()
            
            content = "# 公司員工資料庫\n\n"
            content += "本文件包含公司所有員工的詳細資訊，包括姓名、部門、職位、薪資等。\n\n"
            
            # 按部門分組
            departments = {}
            for row in rows:
                employee_data = dict(zip(columns, row))
                dept = employee_data['department']
                if dept not in departments:
                    departments[dept] = []
                departments[dept].append(employee_data)
            
            for dept_name, employees in departments.items():
                content += f"## {dept_name}\n\n"
                
                for emp in employees:
                    content += f"### {emp['name']} (員工編號: {emp['id']})\n"
                    content += f"- **姓名**: {emp['name']}\n"
                    content += f"- **部門**: {emp['department']}\n"
                    content += f"- **職位**: {emp['position']}\n"
                    content += f"- **薪資**: {emp['salary']:,} 元（月薪）\n"
                    content += f"- **入職日期**: {emp['hire_date']}\n"
                    content += f"- **電子郵件**: {emp['email']}\n\n"
            
            # 添加統計資訊
            content += "## 統計資訊\n\n"
            content += f"- **總員工數**: {len(rows)} 人\n"
            
            for dept_name, employees in departments.items():
                avg_salary = sum(emp['salary'] for emp in employees) / len(employees)
                content += f"- **{dept_name}**: {len(employees)} 人，平均薪資 {avg_salary:,.0f} 元\n"
            
            return content
            
        except Exception as e:
            print(f"❌ 生成員工內容失敗: {e}")
            return "員工資料載入失敗"
    
    def wait_for_document_processing(self, document_id: str, max_wait: int = 60):
        """等待文件處理完成"""
        if not document_id:
            return
        
        headers = {
            'Authorization': f'Bearer {DIFY_CONFIG["dataset_api_key"]}',
            'Content-Type': 'application/json'
        }
        
        for i in range(max_wait):
            try:
                response = requests.get(
                    f'{DIFY_CONFIG["base_url"]}/v1/datasets/{self.dataset_id}/documents/{document_id}',
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    status = result.get('indexing_status', 'unknown')
                    
                    if status == 'completed':
                        print(f"✅ 文件處理完成 ({i+1}s)")
                        return
                    elif status == 'error':
                        print(f"❌ 文件處理失敗: {result.get('error', 'Unknown error')}")
                        return
                    
                    if i % 10 == 0:  # 每10秒顯示一次狀態
                        print(f"⏳ 文件處理中... 狀態: {status} ({i}s)")
                
                time.sleep(1)
                
            except Exception as e:
                if i % 10 == 0:
                    print(f"⚠️ 檢查處理狀態失敗: {e}")
                time.sleep(1)
        
        print(f"⚠️ 等待文件處理超時 ({max_wait}s)，但可能已完成")
    
    def query_dify_knowledge_base(self, question: str) -> dict:
        """直接查詢配置了知識庫的 Dify 應用"""
        if not self.knowledge_base_enabled:
            print("⚠️ Dify 知識庫未啟用，使用本地記憶")
            return None
        
        print(f"🔍 查詢 Dify 知識庫: {question}")
        
        headers = {
            'Authorization': f'Bearer {DIFY_CONFIG["api_key"]}',  # 使用應用 Token
            'Content-Type': 'application/json'
        }
        
        payload = {
            'inputs': {},
            'query': question,
            'response_mode': 'blocking',
            'user': 'persistent_memory_kb_test'
        }
        
        try:
            response = requests.post(
                DIFY_CONFIG['api_url'],
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get('answer', '')
                metadata = result.get('metadata', {})
                
                # 檢查是否使用了知識庫
                retrieval_sources = metadata.get('retrieval_sources', [])
                
                return {
                    'success': True,
                    'answer': answer,
                    'uses_knowledge_base': len(retrieval_sources) > 0,
                    'sources_count': len(retrieval_sources),
                    'sources': retrieval_sources
                }
            else:
                print(f"❌ Dify 知識庫查詢失敗: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Dify 知識庫查詢異常: {e}")
            return None
    
    def vector_search(self, query: str, top_k: int = 3) -> List[Tuple[str, Dict, float]]:
        """向量搜尋"""
        try:
            query_vector = self.get_embedding(query)
            
            if CHROMADB_AVAILABLE and hasattr(self, 'collection'):
                results = self.collection.query(
                    query_embeddings=[query_vector],
                    n_results=top_k
                )
                
                search_results = []
                for i in range(len(results['documents'][0])):
                    text = results['documents'][0][i]
                    metadata = results['metadatas'][0][i]
                    distance = results['distances'][0][i]
                    similarity = 1 - distance
                    search_results.append((text, metadata, similarity))
                
                return search_results
            else:
                return self.vector_store.search(query_vector, top_k)
        
        except Exception as e:
            print(f"❌ 向量搜尋失敗: {e}")
            return []
    
    def build_context_with_memory(self, question: str, search_results: List[Tuple[str, Dict, float]]) -> str:
        """構建包含記憶的上下文"""
        context_parts = []
        
        # 1. 加入相關的向量搜尋結果
        if search_results:
            context_parts.append("=== 員工資料庫搜尋結果 ===")
            for text, metadata, score in search_results:
                context_parts.append(f"相關員工: {metadata['name']} ({metadata['department']})")
                context_parts.append(text)
                context_parts.append("")
        
        # 2. 加入相關的歷史知識
        relevant_knowledge = self.memory_store.search_knowledge_base(question, limit=2)
        if relevant_knowledge:
            context_parts.append("=== 相關歷史知識 ===")
            for knowledge in relevant_knowledge:
                context_parts.append(f"問題: {knowledge['question']}")
                context_parts.append(f"回答: {knowledge['answer']}")
                context_parts.append("")
        
        # 3. 加入最近的對話歷史
        recent_conversations = self.memory_store.get_recent_conversations(limit=3)
        if recent_conversations:
            context_parts.append("=== 最近對話歷史 ===")
            for conv in recent_conversations:
                context_parts.append(f"問: {conv['question']}")
                context_parts.append(f"答: {conv['answer'][:100]}...")
                context_parts.append("")
        
        return "\n".join(context_parts)
    
    def call_dify_with_persistent_memory(self, question: str, context_data: str = "") -> dict:
        """調用 Dify API 並維持持續對話，優先使用知識庫"""
        
        # 優先嘗試使用 Dify 知識庫
        if self.knowledge_base_enabled:
            kb_result = self.query_dify_knowledge_base(question)
            if kb_result and kb_result['success'] and kb_result['uses_knowledge_base']:
                print(f"✅ 使用 Dify 知識庫回答 (找到 {kb_result['sources_count']} 個相關資源)")
                return {
                    'success': True,
                    'answer': kb_result['answer'],
                    'response_time': 1.0,  # 估計值
                    'source': 'dify_knowledge_base',
                    'uses_knowledge_base': True,
                    'sources_count': kb_result['sources_count']
                }
        
        # 如果知識庫沒有找到答案，使用本地向量搜尋 + 上下文
        print("🔄 使用本地向量搜尋 + 上下文模式")
        
        headers = {
            'Authorization': f'Bearer {DIFY_CONFIG["api_key"]}',
            'Content-Type': 'application/json'
        }
        
        # 如果沒有當前對話ID，創建一個新的
        if not self.current_conversation_id:
            self.current_conversation_id = str(uuid.uuid4())
            print(f"🆕 開始新對話: {self.current_conversation_id[:8]}...")
        
        # 使用修復過的上下文嵌入方法
        if context_data:
            enhanced_question = f"""基於以下資料回答問題：

{context_data}

問題：{question}

請根據上述資料詳細回答，如果資料中有相關資訊，請具體說明。"""
        else:
            enhanced_question = question
        
        payload = {
            'inputs': {},
            'query': enhanced_question,
            'response_mode': 'blocking',
            'user': 'persistent_memory_test'
        }
        
        try:
            print(f"🤖 調用 Dify AI (對話: {self.current_conversation_id[:8]}): {question[:50]}...")
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
                    'conversation_id': result.get('conversation_id', self.current_conversation_id),
                    'source': 'local_context',
                    'uses_knowledge_base': False
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}",
                    'response_time': elapsed,
                    'source': 'error'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'response_time': 0,
                'source': 'error'
            }
    
    def test_persistent_memory_queries(self):
        """測試永久記憶查詢"""
        print("\n" + "="*60)
        print("🧠 永久記憶 RAG 查詢測試")
        print("="*60)
        
        test_queries = [
            {
                'question': '技術部有哪些員工？請記住這個資訊。',
                'description': '建立基礎知識'
            },
            {
                'question': '剛才我問的技術部員工，他們的平均薪資是多少？',
                'description': '測試短期記憶'
            },
            {
                'question': '李美華是什麼職位？請記住她的資訊。',
                'description': '學習特定員工資訊'
            },
            {
                'question': '你還記得我之前問過技術部的事情嗎？',
                'description': '測試對話記憶'
            },
            {
                'question': '根據你學到的資訊，誰的薪資比較高？',
                'description': '測試知識整合'
            }
        ]
        
        results = []
        
        for i, query_info in enumerate(test_queries, 1):
            question = query_info['question']
            description = query_info['description']
            
            print(f"\n🔸 測試 {i}: {description}")
            print(f"❓ 問題: {question}")
            print("-" * 50)
            
            # 1. 向量搜尋
            search_start = time.time()
            search_results = self.vector_search(question, top_k=3)
            search_time = time.time() - search_start
            
            # 2. 構建包含記憶的上下文
            context_data = self.build_context_with_memory(question, search_results)
            
            if search_results or context_data.strip():
                print(f"🎯 搜尋結果: {len(search_results)} 個向量匹配 ({search_time:.2f}s)")
                print(f"🧠 記憶內容: {len(self.memory_store.search_knowledge_base(question))} 個相關記憶")
                
                # 3. 調用 AI
                ai_result = self.call_dify_with_persistent_memory(question, context_data)
                
                if ai_result['success']:
                    print(f"✅ AI 回答 ({ai_result['response_time']:.1f}s):")
                    print(f"📝 {ai_result['answer']}")
                    
                    # 4. 保存到記憶中
                    source_info = ai_result.get('source', 'unknown')
                    if ai_result.get('uses_knowledge_base', False):
                        source_info += f"_kb_sources_{ai_result.get('sources_count', 0)}"
                    
                    self.memory_store.add_to_knowledge_base(
                        question=question,
                        answer=ai_result['answer'],
                        context=context_data[:500],  # 限制上下文長度
                        source=source_info
                    )
                    
                    # 5. 保存對話記錄
                    search_summary = [{"name": meta['name'], "dept": meta['department']} 
                                    for _, meta, _ in search_results]
                    self.memory_store.add_conversation(
                        conversation_id=self.current_conversation_id,
                        question=question,
                        answer=ai_result['answer'],
                        search_results=search_summary
                    )
                    
                    results.append({
                        'question': question,
                        'description': description,
                        'search_time': search_time,
                        'search_results_count': len(search_results),
                        'memory_results_count': len(self.memory_store.search_knowledge_base(question)),
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
                        'ai_success': False,
                        'error': ai_result['error']
                    })
            
            time.sleep(1)  # 避免請求過於頻繁
        
        # 保存記憶和對話歷史
        self.memory_store.save_memory()
        self.memory_store.save_conversation_history()
        
        return results
    
    def test_memory_persistence(self):
        """測試記憶持久性"""
        print("\n" + "="*60)
        print("💾 記憶持久性測試")
        print("="*60)
        
        # 重新載入記憶
        old_memory_count = len(self.memory_store.memory_data['knowledge_base'])
        old_conversation_count = len(self.memory_store.conversation_history)
        
        # 創建新的記憶存儲實例（模擬重啟）
        print("🔄 模擬系統重啟，重新載入記憶...")
        new_memory_store = PersistentMemoryStore()
        
        new_memory_count = len(new_memory_store.memory_data['knowledge_base'])
        new_conversation_count = len(new_memory_store.conversation_history)
        
        print(f"📊 記憶保留情況:")
        print(f"   知識庫項目: {old_memory_count} → {new_memory_count}")
        print(f"   對話記錄: {old_conversation_count} → {new_conversation_count}")
        
        if new_memory_count >= old_memory_count and new_conversation_count >= old_conversation_count:
            print("✅ 記憶持久性測試通過")
            
            # 測試記憶搜尋
            test_query = "技術部"
            relevant_memories = new_memory_store.search_knowledge_base(test_query)
            print(f"🔍 搜尋「{test_query}」找到 {len(relevant_memories)} 個相關記憶")
            
            for memory in relevant_memories[:2]:
                print(f"   - {memory['question'][:40]}... (訪問次數: {memory['access_count']})")
        else:
            print("❌ 記憶持久性測試失敗")

def main():
    """主測試函數"""
    print("🚀 永久記憶向量化 RAG 測試系統")
    print("=" * 60)
    print(f"🔗 API 端點: {DIFY_CONFIG['api_url']}")
    print(f"🧠 嵌入模型: {VECTOR_CONFIG['model_name']}")
    print(f"💾 記憶存儲: {MEMORY_CONFIG['memory_file']}")
    print("=" * 60)
    
    # 檢查依賴
    print("\n🔍 檢查系統依賴:")
    print(f"📦 sentence-transformers: {'✅ 可用' if SENTENCE_TRANSFORMERS_AVAILABLE else '❌ 不可用'}")
    print(f"📦 chromadb: {'✅ 可用' if CHROMADB_AVAILABLE else '❌ 不可用'}")
    
    # 初始化測試器
    tester = PersistentMemoryRAGTester()
    
    # 1. 載入並向量化資料
    if not tester.load_and_vectorize_data():
        print("\n❌ 資料載入失敗，測試終止")
        return
    
    # 2. 初始化 Dify 知識庫（可選）
    print("\n🔧 Dify 知識庫初始化...")
    kb_setup_choice = input("是否建立 Dify 知識庫？(y/N): ").strip().lower()
    
    if kb_setup_choice in ['y', 'yes']:
        print("📚 開始建立 Dify 知識庫...")
        if tester.create_dify_dataset():
            print("⏳ 等待 5 秒後開始上傳資料...")
            time.sleep(5)
            if tester.upload_to_dify_knowledge_base():
                print("✅ Dify 知識庫建立完成")
                print("⏳ 等待 30 秒讓 Dify 建立索引...")
                time.sleep(30)
            else:
                print("⚠️ Dify 知識庫上傳失敗，將使用本地向量搜尋")
        else:
            print("⚠️ Dify 知識庫建立失敗，將使用本地向量搜尋")
    else:
        print("📍 跳過 Dify 知識庫建立，僅使用本地向量搜尋")
    
    # 3. 測試永久記憶查詢
    print(f"\n🧠 當前記憶狀態:")
    print(f"   知識庫項目: {len(tester.memory_store.memory_data['knowledge_base'])}")
    print(f"   對話記錄: {len(tester.memory_store.conversation_history)}")
    
    query_results = tester.test_persistent_memory_queries()
    
    # 3. 測試記憶持久性
    tester.test_memory_persistence()
    
    # 4. 總結報告
    print("\n" + "="*60)
    print("📊 永久記憶測試總結報告")
    print("="*60)
    
    if query_results:
        successful_queries = [r for r in query_results if r.get('ai_success', False)]
        print(f"✅ 成功查詢: {len(successful_queries)}/{len(query_results)}")
        
        if successful_queries:
            avg_search_time = sum(r['search_time'] for r in successful_queries) / len(successful_queries)
            avg_ai_time = sum(r['ai_response_time'] for r in successful_queries) / len(successful_queries)
            avg_total_time = sum(r['total_time'] for r in successful_queries) / len(successful_queries)
            
            total_memory_used = sum(r.get('memory_results_count', 0) for r in successful_queries)
            
            print(f"⏱️ 平均向量搜尋時間: {avg_search_time:.2f}s")
            print(f"⏱️ 平均 AI 回應時間: {avg_ai_time:.1f}s")
            print(f"⏱️ 平均總時間: {avg_total_time:.1f}s")
            print(f"🧠 總記憶使用次數: {total_memory_used}")
            
            # 知識庫使用統計
            if tester.knowledge_base_enabled:
                print(f"📚 Dify 知識庫狀態: ✅ 已啟用 (資料集 ID: {tester.dataset_id})")
            else:
                print(f"📚 Dify 知識庫狀態: ❌ 未啟用")
    
    final_memory_count = len(tester.memory_store.memory_data['knowledge_base'])
    final_conversation_count = len(tester.memory_store.conversation_history)
    
    print(f"\n💾 最終記憶狀態:")
    print(f"   知識庫項目: {final_memory_count}")
    print(f"   對話記錄: {final_conversation_count}")
    print(f"   記憶檔案: {MEMORY_CONFIG['memory_file']}")
    print(f"   對話檔案: {MEMORY_CONFIG['conversation_file']}")
    
    print("\n💡 增強版永久記憶特點:")
    print("🧠 AI 會記住學習到的知識和對話歷史")
    print("💾 記憶資料會保存在 JSON 檔案中")
    print("🔄 重啟後會自動載入之前的記憶")
    print("🔍 查詢時會結合歷史知識和新搜尋結果")
    print("📈 記憶會根據使用頻率進行排序")
    print("📚 支援 Dify 知識庫整合，實現真正的永久記憶")
    print("🎯 智能選擇最佳回答來源（知識庫優先，本地向量備用）")
    print("🔗 雙重保障：Dify 雲端知識 + 本地向量搜尋")
    
    print("\n✅ 永久記憶向量化 RAG 測試完成！")

if __name__ == "__main__":
    main()