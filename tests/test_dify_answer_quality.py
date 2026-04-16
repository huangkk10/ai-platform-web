#!/usr/bin/env python3
"""
Dify AI 回答品質測試
====================

測試目標：
1. 向 Dify API 發送 10 次相同問題
2. 統計 AI 回答品質
3. 記錄所有回應內容供分析
4. 檢查是否使用了外部知識庫

使用方法：
    python tests/test_dify_answer_quality.py

輸出：
    - 詳細的測試結果
    - JSON 格式的完整記錄（可用於後續分析）
"""

import requests
import json
import time
from datetime import datetime
from pathlib import Path


class DifyAnswerQualityTest:
    """Dify 回答品質測試類"""
    
    def __init__(self):
        self.api_url = "http://10.253.43.244/v1/chat-messages"
        self.api_key = "app-MgZZOhADkEmdUrj2DtQLJ23G"  # Protocol Guide API Key
        self.test_query = "crystaldiskmark 如何放測"
        self.results = []
        
    def send_request(self, test_number, use_conversation_id=False, conversation_id=None):
        """
        發送單次測試請求
        
        Args:
            test_number: 測試編號
            use_conversation_id: 是否使用 conversation_id
            conversation_id: 對話 ID
            
        Returns:
            dict: 測試結果
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "inputs": {},
            "query": self.test_query,
            "response_mode": "blocking",
            "user": "test_user_quality_check",
            "retrieval_model": {
                "search_method": "semantic_search",
                "reranking_enable": False,
                "reranking_mode": None,
                "top_k": 3,
                "score_threshold_enabled": False
            }
        }
        
        # 如果需要使用 conversation_id
        if use_conversation_id and conversation_id:
            payload["conversation_id"] = conversation_id
        
        print(f"\n{'='*60}")
        print(f"測試 #{test_number}")
        print(f"{'='*60}")
        print(f"📤 發送請求: {self.test_query}")
        if conversation_id:
            print(f"🔗 Conversation ID: {conversation_id}")
        
        start_time = time.time()
        
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                return self._analyze_response(test_number, data, elapsed_time, conversation_id)
            else:
                print(f"❌ 請求失敗: {response.status_code}")
                return {
                    "test_number": test_number,
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            print(f"❌ 請求異常: {str(e)}")
            return {
                "test_number": test_number,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _analyze_response(self, test_number, data, elapsed_time, conversation_id):
        """分析 Dify 回應"""
        answer = data.get("answer", "")
        metadata = data.get("metadata", {})
        retriever_resources = metadata.get("retriever_resources", [])
        new_conversation_id = data.get("conversation_id", "")
        message_id = data.get("message_id", "")
        
        # 分析回答品質
        answer_length = len(answer)
        has_resources = len(retriever_resources) > 0
        resource_count = len(retriever_resources)
        
        # 判斷回答品質（基於長度和是否使用知識庫）
        quality_score = self._calculate_quality_score(
            answer, 
            answer_length, 
            has_resources,
            retriever_resources
        )
        
        # 檢查是否是"找不到資料"的回答
        negative_keywords = [
            "無法找到", "找不到", "未找到", "沒有找到",
            "無法在資料庫", "資料庫中無", "目前無法"
        ]
        is_negative_answer = any(keyword in answer for keyword in negative_keywords)
        
        # 輸出結果
        print(f"⏱️  回應時間: {elapsed_time:.2f}s")
        print(f"📏 回答長度: {answer_length} 字元")
        print(f"🔍 知識庫使用: {'✅ 是' if has_resources else '❌ 否'} ({resource_count} 條)")
        
        if has_resources:
            print(f"📚 引用文檔:")
            for i, resource in enumerate(retriever_resources, 1):
                doc_name = resource.get("document_name", "Unknown")
                score = resource.get("score", 0)
                print(f"   {i}. {doc_name} (分數: {score:.4f})")
        
        print(f"🎯 品質評分: {quality_score}/10")
        
        if is_negative_answer and has_resources:
            print(f"⚠️  警告: AI 說找不到資料，但實際有 {resource_count} 條知識庫結果！")
        
        # 顯示回答預覽
        answer_preview = answer[:150] + "..." if len(answer) > 150 else answer
        print(f"💬 回答預覽:\n{answer_preview}\n")
        
        # 構建結果
        result = {
            "test_number": test_number,
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "query": self.test_query,
            "conversation_id": new_conversation_id or conversation_id,
            "message_id": message_id,
            "response_time": round(elapsed_time, 2),
            "answer": {
                "content": answer,
                "length": answer_length,
                "preview": answer_preview
            },
            "knowledge_base": {
                "used": has_resources,
                "resource_count": resource_count,
                "resources": [
                    {
                        "document_name": r.get("document_name", ""),
                        "score": r.get("score", 0),
                        "position": r.get("position", 0)
                    }
                    for r in retriever_resources
                ]
            },
            "quality_analysis": {
                "score": quality_score,
                "is_negative_answer": is_negative_answer,
                "has_contradiction": is_negative_answer and has_resources,
                "is_high_quality": quality_score >= 7 and has_resources and not is_negative_answer
            }
        }
        
        return result
    
    def _calculate_quality_score(self, answer, length, has_resources, resources):
        """
        計算回答品質評分 (0-10)
        
        評分標準：
        - 基礎分: 5 分
        - 使用知識庫: +2 分
        - 回答長度 > 500 字: +2 分
        - 回答長度 200-500 字: +1 分
        - 知識庫分數 > 0.8: +1 分
        - 包含「找不到」等負面詞: -3 分
        """
        score = 5  # 基礎分
        
        # 使用知識庫
        if has_resources:
            score += 2
        else:
            score -= 2
        
        # 回答長度
        if length > 500:
            score += 2
        elif length > 200:
            score += 1
        elif length < 100:
            score -= 1
        
        # 知識庫分數
        if resources:
            max_score = max([r.get("score", 0) for r in resources])
            if max_score > 0.8:
                score += 1
        
        # 負面關鍵字
        negative_keywords = [
            "無法找到", "找不到", "未找到", "沒有找到",
            "無法在資料庫", "資料庫中無", "目前無法"
        ]
        if any(keyword in answer for keyword in negative_keywords):
            score -= 3
        
        return max(0, min(10, score))  # 限制在 0-10 範圍
    
    def run_tests(self, num_tests=10, use_conversation=True):
        """
        執行多次測試
        
        Args:
            num_tests: 測試次數
            use_conversation: 是否使用對話模式（所有請求共用一個 conversation_id）
        """
        print(f"\n🚀 開始 Dify AI 回答品質測試")
        print(f"📊 測試次數: {num_tests}")
        print(f"🔗 對話模式: {'啟用' if use_conversation else '停用'}")
        print(f"❓ 測試問題: {self.test_query}")
        print(f"🌐 API 端點: {self.api_url}")
        
        conversation_id = None
        
        for i in range(1, num_tests + 1):
            result = self.send_request(
                test_number=i,
                use_conversation_id=use_conversation and conversation_id is not None,
                conversation_id=conversation_id
            )
            
            self.results.append(result)
            
            # 如果是對話模式，儲存 conversation_id
            if use_conversation and result.get("success"):
                conversation_id = result.get("conversation_id")
            
            # 避免請求過快
            if i < num_tests:
                time.sleep(1)
        
        # 統計和分析
        self._print_summary()
        self._save_results()
    
    def _print_summary(self):
        """輸出測試摘要"""
        print(f"\n{'='*60}")
        print(f"📊 測試摘要")
        print(f"{'='*60}")
        
        successful_tests = [r for r in self.results if r.get("success")]
        total_tests = len(self.results)
        
        if not successful_tests:
            print("❌ 所有測試都失敗了")
            return
        
        # 基本統計
        print(f"\n✅ 成功測試: {len(successful_tests)}/{total_tests}")
        
        # 知識庫使用統計
        kb_used_count = sum(1 for r in successful_tests if r.get("knowledge_base", {}).get("used"))
        print(f"📚 使用知識庫: {kb_used_count}/{len(successful_tests)} ({kb_used_count/len(successful_tests)*100:.1f}%)")
        
        # 回答長度統計
        lengths = [r["answer"]["length"] for r in successful_tests]
        avg_length = sum(lengths) / len(lengths)
        print(f"📏 平均回答長度: {avg_length:.0f} 字元")
        print(f"   最短: {min(lengths)} 字元")
        print(f"   最長: {max(lengths)} 字元")
        
        # 品質評分統計
        scores = [r["quality_analysis"]["score"] for r in successful_tests]
        avg_score = sum(scores) / len(scores)
        high_quality_count = sum(1 for r in successful_tests if r["quality_analysis"]["is_high_quality"])
        
        print(f"\n🎯 品質評分:")
        print(f"   平均分數: {avg_score:.1f}/10")
        print(f"   最低分數: {min(scores)}/10")
        print(f"   最高分數: {max(scores)}/10")
        print(f"   高品質回答: {high_quality_count}/{len(successful_tests)} ({high_quality_count/len(successful_tests)*100:.1f}%)")
        
        # 矛盾情況統計
        contradictions = sum(1 for r in successful_tests if r["quality_analysis"]["has_contradiction"])
        if contradictions > 0:
            print(f"\n⚠️  發現 {contradictions} 次矛盾（AI 說找不到但實際有知識庫結果）")
        
        # 回應時間統計
        times = [r["response_time"] for r in successful_tests]
        avg_time = sum(times) / len(times)
        print(f"\n⏱️  平均回應時間: {avg_time:.2f}s")
        print(f"   最快: {min(times):.2f}s")
        print(f"   最慢: {max(times):.2f}s")
        
        # 品質分佈
        print(f"\n📈 品質分佈:")
        score_ranges = [
            ("優秀 (8-10分)", 8, 10),
            ("良好 (6-7分)", 6, 7),
            ("中等 (4-5分)", 4, 5),
            ("較差 (0-3分)", 0, 3)
        ]
        for label, min_score, max_score in score_ranges:
            count = sum(1 for s in scores if min_score <= s <= max_score)
            percentage = count / len(scores) * 100
            print(f"   {label}: {count}/{len(scores)} ({percentage:.1f}%)")
    
    def _save_results(self):
        """儲存測試結果到檔案"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"dify_quality_test_{timestamp}.json"
        
        # 創建測試結果目錄
        output_dir = Path(__file__).parent / "test_results"
        output_dir.mkdir(exist_ok=True)
        
        filepath = output_dir / filename
        
        # 準備完整報告
        report = {
            "test_info": {
                "timestamp": datetime.now().isoformat(),
                "query": self.test_query,
                "api_url": self.api_url,
                "total_tests": len(self.results)
            },
            "summary": self._generate_summary(),
            "detailed_results": self.results
        }
        
        # 儲存為 JSON
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 測試結果已儲存: {filepath}")
        
        # 同時儲存一份最新的
        latest_filepath = output_dir / "latest_quality_test.json"
        with open(latest_filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"💾 最新結果副本: {latest_filepath}")
    
    def _generate_summary(self):
        """生成統計摘要"""
        successful_tests = [r for r in self.results if r.get("success")]
        
        if not successful_tests:
            return {"error": "所有測試都失敗"}
        
        kb_used_count = sum(1 for r in successful_tests if r.get("knowledge_base", {}).get("used"))
        lengths = [r["answer"]["length"] for r in successful_tests]
        scores = [r["quality_analysis"]["score"] for r in successful_tests]
        times = [r["response_time"] for r in successful_tests]
        high_quality_count = sum(1 for r in successful_tests if r["quality_analysis"]["is_high_quality"])
        contradictions = sum(1 for r in successful_tests if r["quality_analysis"]["has_contradiction"])
        
        return {
            "total_tests": len(self.results),
            "successful_tests": len(successful_tests),
            "knowledge_base_usage": {
                "count": kb_used_count,
                "percentage": round(kb_used_count / len(successful_tests) * 100, 1)
            },
            "answer_length": {
                "average": round(sum(lengths) / len(lengths), 0),
                "min": min(lengths),
                "max": max(lengths)
            },
            "quality_score": {
                "average": round(sum(scores) / len(scores), 1),
                "min": min(scores),
                "max": max(scores),
                "high_quality_count": high_quality_count,
                "high_quality_percentage": round(high_quality_count / len(successful_tests) * 100, 1)
            },
            "response_time": {
                "average": round(sum(times) / len(times), 2),
                "min": round(min(times), 2),
                "max": round(max(times), 2)
            },
            "contradictions": contradictions
        }


def main():
    """主函數"""
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║         Dify AI 回答品質測試工具                          ║
    ║         Protocol Assistant - CrystalDiskMark 測試         ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    # 創建測試實例
    tester = DifyAnswerQualityTest()
    
    # 執行測試
    # use_conversation=True: 所有請求使用同一個 conversation_id（模擬連續對話）
    # use_conversation=False: 每次都是新對話
    tester.run_tests(num_tests=10, use_conversation=False)
    
    print("\n✅ 測試完成！")
    print("📁 詳細結果已儲存至 tests/test_results/ 目錄")


if __name__ == "__main__":
    main()
