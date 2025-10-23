#!/usr/bin/env python
"""
創建 Protocol Assistant 測試資料
用於展示 Analytics Dashboard 功能
"""

import os
import sys
import django
from datetime import datetime, timedelta
import random

# 設置 Django 環境
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from django.contrib.auth.models import User
from api.models import ConversationSession, ChatMessage
from django.utils import timezone

def create_test_data():
    """創建測試對話和訊息"""
    
    print("🚀 開始創建 Protocol Assistant 測試資料...")
    
    # 獲取或創建測試用戶
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@example.com',
            'is_staff': True,
            'is_superuser': True
        }
    )
    
    if created:
        user.set_password('testpass')
        user.save()
        print(f"✅ 創建測試用戶: {user.username}")
    else:
        print(f"✅ 使用現有用戶: {user.username}")
    
    # Protocol Assistant 問題類別
    categories = [
        'configuration',
        'general', 
        'jenkins',
        'mdm',
        'network',
        'performance',
        'testing',
        'troubleshooting'
    ]
    
    # 測試問題模板
    questions = {
        'configuration': [
            "如何配置 Protocol 測試環境？",
            "Protocol 設定檔案的格式是什麼？",
            "怎麼修改 Protocol 預設參數？"
        ],
        'general': [
            "Protocol Assistant 可以幫我什麼？",
            "Protocol 測試流程是什麼？",
            "Protocol 有哪些功能？"
        ],
        'jenkins': [
            "Jenkins 如何整合 Protocol 測試？",
            "CI/CD 流程中如何執行 Protocol？",
            "Jenkins Pipeline 設定範例"
        ],
        'mdm': [
            "MDM 相關的 Protocol 測試怎麼做？",
            "MDM 環境配置建議",
            "MDM 測試案例"
        ],
        'network': [
            "網路連線問題如何排查？",
            "Protocol 網路設定",
            "防火牆規則配置"
        ],
        'performance': [
            "如何優化 Protocol 效能？",
            "效能測試指標說明",
            "效能瓶頸分析"
        ],
        'testing': [
            "Protocol 測試案例撰寫",
            "測試覆蓋率如何提升？",
            "自動化測試建議"
        ],
        'troubleshooting': [
            "Protocol 常見錯誤排除",
            "Debug 技巧",
            "Log 分析方法"
        ]
    }
    
    # 創建對話和訊息
    total_conversations = 0
    total_messages = 0
    
    # 過去 30 天內隨機分布
    for day_offset in range(30):
        # 每天隨機創建 3-8 個對話
        daily_conversations = random.randint(3, 8)
        
        for _ in range(daily_conversations):
            # 隨機選擇類別
            category = random.choice(categories)
            
            # 創建對話
            created_time = timezone.now() - timedelta(days=day_offset, hours=random.randint(0, 23))
            
            conversation = ConversationSession.objects.create(
                session_id=f'protocol_test_{total_conversations}_{int(created_time.timestamp())}',
                user=user,
                chat_type='protocol_assistant_chat',  # ✅ 關鍵：使用正確的類型
                title=f'Protocol 測試對話 {total_conversations + 1}',
                message_count=0,
                total_tokens=0,
                total_response_time=0,
                is_active=random.choice([True, False]),
                is_archived=False,
                created_at=created_time,
                updated_at=created_time,
                last_message_at=created_time,
                satisfaction_score=random.choice([None, 0.0, 1.0])  # 隨機滿意度
            )
            
            total_conversations += 1
            
            # 每個對話創建 2-6 條訊息（問答對）
            message_pairs = random.randint(1, 3)
            sequence = 1
            
            for pair in range(message_pairs):
                # 用戶問題
                question_text = random.choice(questions[category])
                
                user_message = ChatMessage.objects.create(
                    message_id=f'msg_user_{total_messages}',
                    conversation=conversation,
                    role='user',
                    content=question_text,
                    content_type='text',
                    sequence_number=sequence,
                    is_edited=False,
                    original_content=question_text,
                    is_bookmarked=False,
                    created_at=created_time + timedelta(seconds=sequence * 30),
                    updated_at=created_time + timedelta(seconds=sequence * 30),
                    question_category=category  # ✅ 設定問題分類
                )
                
                total_messages += 1
                sequence += 1
                
                # AI 回答
                assistant_text = f"這是關於 {category} 的回答：{question_text}"
                response_time = random.uniform(1.5, 5.0)
                
                assistant_message = ChatMessage.objects.create(
                    message_id=f'msg_assistant_{total_messages}',
                    conversation=conversation,
                    role='assistant',
                    content=assistant_text,
                    content_type='text',
                    sequence_number=sequence,
                    response_time=response_time,
                    token_usage={'total_tokens': random.randint(100, 500)},
                    is_edited=False,
                    original_content=assistant_text,
                    is_bookmarked=False,
                    is_helpful=random.choice([None, True, False]),  # 隨機反饋
                    created_at=created_time + timedelta(seconds=sequence * 30),
                    updated_at=created_time + timedelta(seconds=sequence * 30)
                )
                
                total_messages += 1
                sequence += 1
                
                # 更新對話統計
                conversation.message_count = sequence - 1
                conversation.total_tokens += assistant_message.token_usage.get('total_tokens', 0)
                conversation.total_response_time += response_time
                conversation.last_message_at = assistant_message.created_at
                conversation.save()
    
    print(f"\n✅ 測試資料創建完成！")
    print(f"📊 統計：")
    print(f"   - 對話數量: {total_conversations}")
    print(f"   - 訊息數量: {total_messages}")
    print(f"   - 時間範圍: 過去 30 天")
    print(f"   - 問題類別: {len(categories)} 個")
    
    # 驗證資料
    print(f"\n🔍 資料驗證：")
    protocol_convs = ConversationSession.objects.filter(chat_type='protocol_assistant_chat').count()
    protocol_msgs = ChatMessage.objects.filter(
        conversation__chat_type='protocol_assistant_chat'
    ).count()
    
    print(f"   - Protocol 對話: {protocol_convs}")
    print(f"   - Protocol 訊息: {protocol_msgs}")
    
    # 按類別統計
    print(f"\n📈 問題分類統計：")
    for category in categories:
        count = ChatMessage.objects.filter(
            question_category=category,
            conversation__chat_type='protocol_assistant_chat'
        ).count()
        print(f"   - {category}: {count} 個問題")

if __name__ == '__main__':
    try:
        create_test_data()
        print("\n✅ 全部完成！現在可以訪問 Analytics Dashboard 查看數據。")
    except Exception as e:
        print(f"\n❌ 錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
