#!/usr/bin/env python
"""同步 Protocol Assistant 的 ChatUsage 記錄"""

import os
import sys
import django

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from django.db import transaction
from api.models import ConversationSession, ChatMessage, ChatUsage

def sync_protocol_chat_usage():
    print("=" * 70)
    print("同步 Protocol Assistant ChatUsage 記錄")
    print("=" * 70)
    
    protocol_sessions = ConversationSession.objects.filter(
        chat_type='protocol_assistant_chat'
    ).order_by('created_at')
    
    print(f"\n📊 找到 {protocol_sessions.count()} 個 Protocol Assistant 對話會話")
    
    if protocol_sessions.count() == 0:
        print("❌ 沒有找到任何 Protocol Assistant 對話記錄")
        return
    
    existing_usage = ChatUsage.objects.filter(
        chat_type='protocol_assistant_chat'
    ).count()
    
    print(f"📈 現有 ChatUsage 記錄: {existing_usage} 筆")
    
    created_count = 0
    skipped_count = 0
    
    with transaction.atomic():
        for session in protocol_sessions:
            try:
                messages = ChatMessage.objects.filter(
                    conversation=session
                ).order_by('created_at')
                
                if messages.count() == 0:
                    skipped_count += 1
                    continue
                
                assistant_messages = messages.filter(role='assistant')
                response_times = [msg.response_time for msg in assistant_messages if msg.response_time]
                avg_response_time = sum(response_times) / len(response_times) if response_times else None
                
                user_messages = messages.filter(role='user')
                
                for user_msg in user_messages:
                    existing = ChatUsage.objects.filter(
                        user=session.user,
                        session_id=session.session_id,
                        created_at__date=user_msg.created_at.date(),
                        chat_type='protocol_assistant_chat'
                    ).first()
                    
                    if existing:
                        continue
                    
                    ChatUsage.objects.create(
                        user=session.user,
                        session_id=session.session_id,
                        chat_type='protocol_assistant_chat',
                        message_count=1,
                        has_file_upload=False,
                        response_time=avg_response_time,
                        created_at=user_msg.created_at,
                        ip_address=None,
                        user_agent=''
                    )
                    created_count += 1
                
            except Exception as e:
                print(f"❌ 處理會話失敗: {str(e)}")
                continue
    
    print(f"\n✅ 新增記錄: {created_count} 筆")
    print(f"⏭️  跳過記錄: {skipped_count} 筆")
    
    final_count = ChatUsage.objects.filter(
        chat_type='protocol_assistant_chat'
    ).count()
    
    print(f"\n📈 同步後 ChatUsage 記錄: {final_count} 筆")
    print("\n✅ 同步完成！請刷新 Dashboard 查看效果。")

if __name__ == '__main__':
    sync_protocol_chat_usage()
