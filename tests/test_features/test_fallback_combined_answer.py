#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
測試降級模式組合回答功能（方案 B）
====================================

驗證當降級時，用戶能看到 AI 原始回答 + 友善提示
"""

import os
import sys
import django

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from api.views.dify_chat_views import protocol_guide_chat

User = get_user_model()


def test_fallback_combined_answer():
    """測試降級模式的組合回答"""
    
    factory = RequestFactory()
    
    # 創建或獲取測試用戶
    user, _ = User.objects.get_or_create(username='test_user')
    
    # 測試案例：會觸發降級的查詢
    test_cases = [
        {
            'query': 'XYZ_NOT_EXIST 的測試流程',
            'description': '不存在的文檔（應該觸發降級）'
        },
        {
            'query': '未知協議 ABC 的配置方法',
            'description': '不存在的協議（應該觸發降級）'
        }
    ]
    
    print("=" * 80)
    print("🧪 測試降級模式組合回答功能（方案 B）")
    print("=" * 80)
    print()
    
    for i, test in enumerate(test_cases, 1):
        query = test['query']
        description = test['description']
        
        print(f"【測試案例 {i}】{description}")
        print("─" * 80)
        print(f"查詢: '{query}'")
        print()
        
        try:
            # 創建 mock request
            request = factory.post(
                '/api/protocol-guide/chat/',
                data={'message': query},
                content_type='application/json'
            )
            request.user = user
            
            # 執行聊天請求
            response = protocol_guide_chat(request)
            result = response.data if hasattr(response, 'data') else {}
            
            # 分析結果
            print("📊 回應分析:")
            print(f"  模式: {result.get('mode', 'N/A').upper()}")
            print(f"  階段: {result.get('stage', 'N/A')}")
            print(f"  是否降級: {'✅ 是' if result.get('is_fallback') else '❌ 否'}")
            
            if result.get('is_fallback'):
                print(f"  降級原因: {result.get('fallback_reason', 'N/A')}")
            
            print()
            
            # 顯示回答內容
            answer = result.get('answer', '')
            print("💬 AI 回答內容:")
            print("─" * 80)
            print(answer)
            print("─" * 80)
            print()
            
            # 檢查是否符合方案 B 格式
            print("✅ 方案 B 驗證:")
            
            has_separator = "---" in answer
            has_emoji = "💡" in answer
            has_suggestion = "建議您參考以下文件" in answer
            has_original_content = len(answer.split("---")[0].strip()) > 10 if has_separator else False
            
            print(f"  ✓ 包含分隔線: {'✅' if has_separator else '❌'}")
            print(f"  ✓ 包含 💡 emoji: {'✅' if has_emoji else '❌'}")
            print(f"  ✓ 包含友善提示: {'✅' if has_suggestion else '❌'}")
            print(f"  ✓ 包含 AI 原始回答: {'✅' if has_original_content else '❌'}")
            
            if has_separator:
                original_part = answer.split("---")[0].strip()
                print(f"  ✓ AI 原始回答長度: {len(original_part)} 字元")
                print(f"  ✓ AI 原始回答預覽: {original_part[:100]}...")
            
            # 評估結果
            all_checks = has_separator and has_emoji and has_suggestion and has_original_content
            print()
            if all_checks:
                print("🎉 ✅ PASS - 方案 B 實作正確！")
            else:
                print("⚠️ ❌ FAIL - 方案 B 格式不完整")
            
            # 顯示引用來源
            metadata = result.get('metadata', {})
            citations = metadata.get('retriever_resources', [])
            
            print()
            print(f"📚 引用來源: {len(citations)} 個")
            for j, citation in enumerate(citations[:3], 1):
                title = citation.get('title', 'N/A')
                score = citation.get('score', 0) * 100
                print(f"  {j}. {title} ({score:.2f}%)")
            
            print()
            print(f"⏱️ 響應時間: {result.get('response_time', 0):.2f} 秒")
            
        except Exception as e:
            print(f"❌ 錯誤: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print("=" * 80)
        print()


if __name__ == '__main__':
    test_fallback_combined_answer()
