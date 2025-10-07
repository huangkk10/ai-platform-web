#!/usr/bin/env python3
"""
用戶權限管理腳本
為管理員提供便捷的用戶權限設置工具
"""

import os
import sys
import django
from getpass import getpass

# 設置 Django 環境
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')

try:
    django.setup()
    from django.contrib.auth.models import User
    from api.models import UserProfile
except Exception as e:
    print(f"❌ Django 環境初始化失敗: {e}")
    sys.exit(1)

def list_users():
    """列出所有用戶及其權限"""
    print("\n👥 用戶權限列表")
    print("=" * 80)
    
    profiles = UserProfile.objects.select_related('user').all().order_by('user__username')
    
    if not profiles:
        print("沒有找到任何用戶。")
        return
    
    print(f"{'用戶名':<15} {'郵箱':<25} {'超級管理員':<8} {'權限摘要':<30}")
    print("-" * 80)
    
    for profile in profiles:
        user = profile.user
        summary = profile.get_permissions_summary()
        if len(summary) > 28:
            summary = summary[:25] + "..."
            
        super_admin_str = "✓" if profile.is_super_admin else ""
        
        print(f"{user.username:<15} {user.email:<25} {super_admin_str:<8} {summary:<30}")

def show_user_details(username):
    """顯示用戶詳細權限信息"""
    try:
        user = User.objects.get(username=username)
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        print(f"\n👤 用戶詳細信息: {username}")
        print("=" * 50)
        print(f"郵箱: {user.email or '未設置'}")
        print(f"狀態: {'活躍' if user.is_active else '停用'}")
        print(f"Django 超級用戶: {'是' if user.is_superuser else '否'}")
        print(f"Django 工作人員: {'是' if user.is_staff else '否'}")
        print(f"超級管理員: {'是' if profile.is_super_admin else '否'}")
        
        print("\n🌐 Web 功能權限:")
        print(f"  Protocol RAG:    {'✓' if profile.web_protocol_rag else '✗'}")
        print(f"  AI OCR:          {'✓' if profile.web_ai_ocr else '✗'}")
        print(f"  RVT Assistant:   {'✓' if profile.web_rvt_assistant else '✗'}")
        
        print("\n📚 知識庫權限:")
        print(f"  Protocol RAG:    {'✓' if profile.kb_protocol_rag else '✗'}")
        print(f"  AI OCR:          {'✓' if profile.kb_ai_ocr else '✗'}")
        print(f"  RVT Assistant:   {'✓' if profile.kb_rvt_assistant else '✗'}")
        
        print(f"\n權限摘要: {profile.get_permissions_summary()}")
        
    except User.DoesNotExist:
        print(f"❌ 用戶 '{username}' 不存在")

def set_user_permissions(username):
    """設置用戶權限"""
    try:
        user = User.objects.get(username=username)
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        print(f"\n🔧 設置用戶權限: {username}")
        print("=" * 50)
        
        # 超級管理員權限
        current = "是" if profile.is_super_admin else "否"
        choice = input(f"超級管理員權限 (當前: {current}) [y/n/skip]: ").lower()
        if choice == 'y':
            profile.is_super_admin = True
        elif choice == 'n':
            profile.is_super_admin = False
        
        # Web 功能權限
        print("\n🌐 Web 功能權限設置:")
        
        permissions = [
            ('web_protocol_rag', 'Web Protocol RAG'),
            ('web_ai_ocr', 'Web AI OCR'),
            ('web_rvt_assistant', 'Web RVT Assistant'),
        ]
        
        for perm_key, perm_name in permissions:
            current_value = getattr(profile, perm_key)
            current = "是" if current_value else "否"
            choice = input(f"  {perm_name} (當前: {current}) [y/n/skip]: ").lower()
            if choice == 'y':
                setattr(profile, perm_key, True)
            elif choice == 'n':
                setattr(profile, perm_key, False)
        
        # 知識庫權限
        print("\n📚 知識庫權限設置:")
        
        kb_permissions = [
            ('kb_protocol_rag', 'KB Protocol RAG'),
            ('kb_ai_ocr', 'KB AI OCR'),
            ('kb_rvt_assistant', 'KB RVT Assistant'),
        ]
        
        for perm_key, perm_name in kb_permissions:
            current_value = getattr(profile, perm_key)
            current = "是" if current_value else "否"
            choice = input(f"  {perm_name} (當前: {current}) [y/n/skip]: ").lower()
            if choice == 'y':
                setattr(profile, perm_key, True)
            elif choice == 'n':
                setattr(profile, perm_key, False)
        
        # 確認保存
        print(f"\n新的權限摘要: {profile.get_permissions_summary()}")
        confirm = input("確認保存權限設置? [y/N]: ").lower()
        
        if confirm == 'y':
            profile.save()
            print("✅ 權限設置已保存")
        else:
            print("❌ 權限設置已取消")
            
    except User.DoesNotExist:
        print(f"❌ 用戶 '{username}' 不存在")

def grant_all_permissions(username):
    """授予用戶所有權限"""
    try:
        user = User.objects.get(username=username)
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        profile.web_protocol_rag = True
        profile.web_ai_ocr = True
        profile.web_rvt_assistant = True
        profile.kb_protocol_rag = True
        profile.kb_ai_ocr = True
        profile.kb_rvt_assistant = True
        profile.is_super_admin = True
        
        profile.save()
        print(f"✅ 已授予用戶 '{username}' 所有權限")
        
    except User.DoesNotExist:
        print(f"❌ 用戶 '{username}' 不存在")

def revoke_all_permissions(username):
    """撤銷用戶所有權限"""
    try:
        user = User.objects.get(username=username)
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        profile.web_protocol_rag = False
        profile.web_ai_ocr = False
        profile.web_rvt_assistant = False
        profile.kb_protocol_rag = False
        profile.kb_ai_ocr = False
        profile.kb_rvt_assistant = False
        profile.is_super_admin = False
        
        profile.save()
        print(f"✅ 已撤銷用戶 '{username}' 所有權限")
        
    except User.DoesNotExist:
        print(f"❌ 用戶 '{username}' 不存在")

def create_user():
    """創建新用戶"""
    print("\n👤 創建新用戶")
    print("=" * 30)
    
    username = input("用戶名: ").strip()
    if not username:
        print("❌ 用戶名不能為空")
        return
    
    if User.objects.filter(username=username).exists():
        print(f"❌ 用戶名 '{username}' 已存在")
        return
    
    email = input("郵箱 (可選): ").strip()
    password = getpass("密碼: ")
    
    if not password:
        print("❌ 密碼不能為空")
        return
    
    try:
        user = User.objects.create_user(
            username=username,
            email=email if email else '',
            password=password
        )
        
        # 創建 UserProfile
        UserProfile.objects.create(user=user)
        
        print(f"✅ 用戶 '{username}' 創建成功")
        
        # 詢問是否設置權限
        setup_perms = input("是否立即設置權限? [y/N]: ").lower()
        if setup_perms == 'y':
            set_user_permissions(username)
            
    except Exception as e:
        print(f"❌ 創建用戶失敗: {e}")

def main():
    """主菜單"""
    while True:
        print("\n🔐 AI Platform 用戶權限管理工具")
        print("=" * 40)
        print("1. 列出所有用戶")
        print("2. 查看用戶詳情")
        print("3. 設置用戶權限")
        print("4. 授予所有權限")
        print("5. 撤銷所有權限")
        print("6. 創建新用戶")
        print("0. 退出")
        
        choice = input("\n請選擇操作 [0-6]: ").strip()
        
        if choice == '0':
            print("👋 再見！")
            break
        elif choice == '1':
            list_users()
        elif choice in ['2', '3', '4', '5']:
            username = input("請輸入用戶名: ").strip()
            if not username:
                print("❌ 用戶名不能為空")
                continue
                
            if choice == '2':
                show_user_details(username)
            elif choice == '3':
                set_user_permissions(username)
            elif choice == '4':
                confirm = input(f"確認授予用戶 '{username}' 所有權限? [y/N]: ").lower()
                if confirm == 'y':
                    grant_all_permissions(username)
            elif choice == '5':
                confirm = input(f"確認撤銷用戶 '{username}' 所有權限? [y/N]: ").lower()
                if confirm == 'y':
                    revoke_all_permissions(username)
        elif choice == '6':
            create_user()
        else:
            print("❌ 無效的選擇，請重新輸入")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 操作已取消，再見！")
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")