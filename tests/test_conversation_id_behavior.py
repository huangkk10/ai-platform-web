#!/usr/bin/env python3
"""
測試 Dify conversation_id 行為
目的：驗證使用相同 conversation_id 連續請求時的成功率和回應品質

測試方法：
1. 發送 10 次相同的問題
2. 每次都使用前一次返回的 conversation_id
3. 記錄每次的結果（成功/失敗、回應長度）
4. 統計成功率和失敗模式
"""

import os
import sys
import json
import time
import requests
from datetime import datetime

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Django 設置
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
import django
django.setup()

from library.config.dify_config_manager import get_protocol_guide_config

# 導入知識庫檢查功能
from library.protocol_guide.search_service import ProtocolGuideSearchService

# 測試配置
TEST_QUESTION = "crystaldiskmark 如何放測"
TEST_ROUNDS = 10
REQUEST_DELAY = 2  # 每次請求間隔（秒）

def check_knowledge_base(question):
    """
    檢查知識庫是否有相關資料
    
    Args:
        question: 問題內容
    
    Returns:
        dict: 包含 found, count, results 等資訊
    """
    try:
        search_service = ProtocolGuideSearchService()
        results = search_service.search_knowledge(
            query=question,
            use_vector=True,
            use_keyword=False,
            top_k=3
        )
        
        formatted_results = []
        if results:
            for item in results:
                formatted_results.append({
                    'similarity': item.get('score', 0),
                    'title': item.get('title', 'N/A'),
                    'id': item.get('id', 0)
                })
        
        return {
            'found': len(formatted_results) > 0,
            'count': len(formatted_results),
            'results': formatted_results
        }
    except Exception as e:
        return {
            'found': False,
            'count': 0,
            'results': [],
            'error': str(e)
        }

def send_dify_request(question, conversation_id=None, user_id="test_user"):
    """
    發送 Dify API 請求
    
    Args:
        question: 問題內容
        conversation_id: 對話ID（可選）
        user_id: 用戶ID
    
    Returns:
        dict: 包含 success, answer, conversation_id, error 等資訊
    """
    config = get_protocol_guide_config()
    
    # 準備請求 payload
    payload = {
        "inputs": {},
        "query": question,
        "response_mode": "blocking",
        "user": user_id
    }
    
    # 如果有 conversation_id，加入請求
    if conversation_id:
        payload["conversation_id"] = conversation_id
    
    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        print(f"📤 發送請求 - conversation_id: {conversation_id or 'None (新對話)'}")
        
        response = requests.post(
            config.api_url,
            json=payload,
            headers=headers,
            timeout=config.timeout
        )
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get('answer', '')
            new_conversation_id = data.get('conversation_id', '')
            
            return {
                'success': True,
                'answer': answer,
                'answer_length': len(answer),
                'conversation_id': new_conversation_id,
                'status_code': 200,
                'error': None
            }
        else:
            error_msg = f"HTTP {response.status_code}"
            try:
                error_data = response.json()
                error_msg = error_data.get('message', error_msg)
            except:
                pass
            
            return {
                'success': False,
                'answer': None,
                'answer_length': 0,
                'conversation_id': None,
                'status_code': response.status_code,
                'error': error_msg
            }
    
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'answer': None,
            'answer_length': 0,
            'conversation_id': None,
            'status_code': None,
            'error': 'Request timeout'
        }
    except Exception as e:
        return {
            'success': False,
            'answer': None,
            'answer_length': 0,
            'conversation_id': None,
            'status_code': None,
            'error': str(e)
        }

def analyze_answer_quality(answer):
    """
    分析回答品質
    
    Returns:
        str: 'good' (詳細回答) 或 'poor' (簡短/不知道)
    """
    if not answer:
        return 'no_answer'
    
    # 檢查是否為「不知道」類型的回答
    poor_indicators = [
        '抱歉',
        '不清楚',
        '不知道',
        '無法',
        '沒有',
        'sorry',
        "don't know",
        "can't"
    ]
    
    answer_lower = answer.lower()
    if any(indicator in answer_lower for indicator in poor_indicators):
        return 'poor'
    
    # 根據長度判斷
    if len(answer) < 200:
        return 'poor'
    else:
        return 'good'

def run_test():
    """執行測試"""
    print("=" * 80)
    print("🧪 開始測試 Dify conversation_id 行為")
    print("=" * 80)
    print(f"測試問題: {TEST_QUESTION}")
    print(f"測試次數: {TEST_ROUNDS}")
    print(f"請求間隔: {REQUEST_DELAY} 秒")
    print("=" * 80)
    print()
    
    results = []
    current_conversation_id = None
    
    # 在測試開始前檢查知識庫
    print("\n" + "=" * 80)
    print("📚 檢查知識庫是否有相關資料")
    print("=" * 80)
    kb_check = check_knowledge_base(TEST_QUESTION)
    print(f"✅ 知識庫檢查結果:")
    print(f"   - 找到資料: {'是' if kb_check['found'] else '否'}")
    print(f"   - 資料數量: {kb_check['count']} 條")
    if kb_check['count'] > 0:
        for i, result in enumerate(kb_check['results'], 1):
            print(f"   - 結果 {i}: 相似度 {result.get('similarity', 0):.2%}, 標題: {result.get('title', 'N/A')[:50]}...")
    print("=" * 80)
    
    for round_num in range(1, TEST_ROUNDS + 1):
        print(f"\n{'='*80}")
        print(f"📝 第 {round_num}/{TEST_ROUNDS} 次請求")
        print(f"{'='*80}")
        
        start_time = time.time()
        
        # 發送請求
        # ✅ 修正：使用固定的 user_id，因為 conversation_id 是綁定到特定用戶的
        result = send_dify_request(
            TEST_QUESTION,
            conversation_id=current_conversation_id,
            user_id="test_user_fixed"  # 固定 user_id，模擬同一個用戶的連續對話
        )
        
        elapsed_time = time.time() - start_time
        result['round'] = round_num
        result['elapsed_time'] = elapsed_time
        result['used_conversation_id'] = current_conversation_id
        
        # 分析回答品質
        if result['success']:
            result['quality'] = analyze_answer_quality(result['answer'])
            current_conversation_id = result['conversation_id']
            
            print(f"✅ 成功")
            print(f"   - 狀態碼: {result['status_code']}")
            print(f"   - 回應時間: {elapsed_time:.2f} 秒")
            print(f"   - 回答長度: {result['answer_length']} 字元")
            print(f"   - 回答品質: {result['quality']}")
            
            # ✅ 如果回答品質差，檢查知識庫
            if result['quality'] == 'poor':
                print(f"   ⚠️ 檢測到低品質回答，重新檢查知識庫...")
                kb_recheck = check_knowledge_base(TEST_QUESTION)
                print(f"   - 知識庫資料: {kb_recheck['count']} 條")
                if kb_recheck['count'] > 0:
                    print(f"   - 💡 知識庫有資料，但 AI 說「不知道」！（LLM 隨機性問題）")
                else:
                    print(f"   - ⚠️ 知識庫確實沒有資料")
                result['kb_available'] = kb_recheck['count'] > 0
            
            print(f"   - 新 conversation_id: {result['conversation_id'][:20]}...")
            print(f"   - 回答預覽: {result['answer'][:100]}...")
        else:
            result['quality'] = 'failed'
            
            print(f"❌ 失敗")
            print(f"   - 狀態碼: {result['status_code']}")
            print(f"   - 錯誤訊息: {result['error']}")
            
            # 如果是 404 錯誤，清除 conversation_id（模擬自動重試）
            if result['status_code'] == 404:
                print(f"   ⚠️ 檢測到 404 錯誤，清除 conversation_id 並重試...")
                current_conversation_id = None
                
                # 重試
                time.sleep(1)
                retry_result = send_dify_request(
                    TEST_QUESTION,
                    conversation_id=None,
                    user_id="test_user_fixed"  # ✅ 修正：重試時也使用相同的 user_id
                )
                
                if retry_result['success']:
                    print(f"   ✅ 重試成功")
                    print(f"   - 回答長度: {retry_result['answer_length']} 字元")
                    retry_result['quality'] = analyze_answer_quality(retry_result['answer'])
                    print(f"   - 回答品質: {retry_result['quality']}")
                    current_conversation_id = retry_result['conversation_id']
                    
                    # 記錄重試結果
                    result['retry_success'] = True
                    result['retry_quality'] = retry_result['quality']
                    result['retry_answer_length'] = retry_result['answer_length']
                else:
                    print(f"   ❌ 重試失敗: {retry_result['error']}")
                    result['retry_success'] = False
        
        results.append(result)
        
        # 等待下一次請求
        if round_num < TEST_ROUNDS:
            print(f"\n⏳ 等待 {REQUEST_DELAY} 秒後進行下一次請求...")
            time.sleep(REQUEST_DELAY)
    
    # 統計分析
    print("\n" + "=" * 80)
    print("📊 測試結果統計")
    print("=" * 80)
    
    total_requests = len(results)
    successful_requests = sum(1 for r in results if r['success'])
    failed_requests = total_requests - successful_requests
    
    # 404 錯誤統計
    error_404_count = sum(1 for r in results if r['status_code'] == 404)
    retry_attempts = sum(1 for r in results if 'retry_success' in r)
    retry_success_count = sum(1 for r in results if r.get('retry_success', False))
    
    # 回答品質統計
    good_answers = sum(1 for r in results if r.get('quality') == 'good')
    poor_answers = sum(1 for r in results if r.get('quality') == 'poor')
    
    # 重試後的品質統計
    retry_good = sum(1 for r in results if r.get('retry_quality') == 'good')
    retry_poor = sum(1 for r in results if r.get('retry_quality') == 'poor')
    
    print(f"\n📈 基本統計:")
    print(f"   - 總請求數: {total_requests}")
    print(f"   - 成功請求: {successful_requests} ({successful_requests/total_requests*100:.1f}%)")
    print(f"   - 失敗請求: {failed_requests} ({failed_requests/total_requests*100:.1f}%)")
    
    print(f"\n❌ 錯誤統計:")
    print(f"   - 404 錯誤: {error_404_count} 次")
    print(f"   - 自動重試: {retry_attempts} 次")
    print(f"   - 重試成功: {retry_success_count} 次")
    
    print(f"\n🎯 回答品質統計 (首次請求):")
    print(f"   - 高品質回答 (>200 字元): {good_answers} ({good_answers/successful_requests*100:.1f}%)")
    print(f"   - 低品質回答 (<200 字元或「不知道」): {poor_answers} ({poor_answers/successful_requests*100:.1f}%)")
    
    if retry_attempts > 0:
        print(f"\n🔄 重試後品質統計:")
        print(f"   - 高品質回答: {retry_good} ({retry_good/retry_success_count*100:.1f}%)")
        print(f"   - 低品質回答: {retry_poor} ({retry_poor/retry_success_count*100:.1f}%)")
    
    # 回答長度統計
    answer_lengths = [r['answer_length'] for r in results if r['success']]
    if answer_lengths:
        avg_length = sum(answer_lengths) / len(answer_lengths)
        min_length = min(answer_lengths)
        max_length = max(answer_lengths)
        
        print(f"\n📏 回答長度統計:")
        print(f"   - 平均長度: {avg_length:.0f} 字元")
        print(f"   - 最短回答: {min_length} 字元")
        print(f"   - 最長回答: {max_length} 字元")
    
    # 詳細結果表格
    print(f"\n📋 詳細結果表格:")
    print(f"{'輪次':<6} {'狀態':<8} {'回答長度':<12} {'品質':<8} {'重試':<8} {'使用 conversation_id':<10}")
    print("-" * 80)
    
    for r in results:
        status = "✅ 成功" if r['success'] else "❌ 失敗"
        length = f"{r['answer_length']} 字元" if r['success'] else f"({r['status_code']})"
        quality = r.get('quality', 'N/A')
        retry = "✅" if r.get('retry_success') else ("❌" if 'retry_success' in r else "-")
        used_conv = "✅" if r['used_conversation_id'] else "❌"
        
        print(f"{r['round']:<6} {status:<8} {length:<12} {quality:<8} {retry:<8} {used_conv:<10}")
    
    # 保存結果到 JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = f"/app/tests/conversation_id_test_result_{timestamp}.json"
    
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump({
            'test_config': {
                'question': TEST_QUESTION,
                'rounds': TEST_ROUNDS,
                'request_delay': REQUEST_DELAY,
                'timestamp': timestamp
            },
            'statistics': {
                'total_requests': total_requests,
                'successful_requests': successful_requests,
                'failed_requests': failed_requests,
                'error_404_count': error_404_count,
                'retry_attempts': retry_attempts,
                'retry_success_count': retry_success_count,
                'good_answers': good_answers,
                'poor_answers': poor_answers,
                'retry_good': retry_good,
                'retry_poor': retry_poor
            },
            'results': results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 詳細結果已保存到: {result_file}")
    
    # 結論
    print("\n" + "=" * 80)
    print("🎓 結論")
    print("=" * 80)
    
    if error_404_count > 0:
        print("⚠️ 發現 404 錯誤！")
        print(f"   - conversation_id 在 {error_404_count} 次請求中失效")
        print(f"   - 失效率: {error_404_count/total_requests*100:.1f}%")
    
    if poor_answers > 0:
        print(f"\n⚠️ 發現低品質回答！")
        print(f"   - {poor_answers} 次回答品質不佳（<200 字元或「不知道」）")
        print(f"   - 低品質率: {poor_answers/successful_requests*100:.1f}%")
    
    if retry_poor > 0 and retry_attempts > 0:
        print(f"\n⚠️ 重試後仍有低品質回答！")
        print(f"   - 重試後 {retry_poor} 次回答仍然品質不佳")
        print(f"   - 這證明問題不在 conversation_id，而在 LLM 的隨機性")
    
    success_rate = successful_requests / total_requests * 100
    quality_rate = good_answers / successful_requests * 100 if successful_requests > 0 else 0
    
    print(f"\n📊 最終評估:")
    print(f"   - 請求成功率: {success_rate:.1f}%")
    print(f"   - 高品質回答率: {quality_rate:.1f}%")
    
    if error_404_count > 3:
        print(f"\n❌ 結論: conversation_id 確實會快速失效")
        print(f"   建議：不使用 conversation_id，每次都是新對話")
    elif poor_answers > 3:
        print(f"\n⚠️ 結論: LLM 回答有隨機性")
        print(f"   建議：調整 Dify 的 temperature 參數或提示詞")
    else:
        print(f"\n✅ 結論: conversation_id 運作正常")
        print(f"   可以安全使用 conversation_id 維持對話記憶")

if __name__ == '__main__':
    try:
        run_test()
    except KeyboardInterrupt:
        print("\n\n⚠️ 測試被用戶中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 測試執行失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
