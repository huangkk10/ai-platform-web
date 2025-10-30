#!/usr/bin/env python3
"""
整合用戶權限管理系統演示腳本
展示如何通過 API 管理用戶和權限
"""

import os
import sys
import django
import requests
import json
from datetime import datetime

# 設置 Django 環境
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')

try:
    django.setup()
    from django.contrib.auth.models import User
    from api.models import UserProfile
    print("✅ Django 環境初始化成功")
except Exception as e:
    print(f"❌ Django 環境初始化失敗: {e}")
    sys.exit(1)

def show_integrated_system_features():
    """展示整合用戶管理系統的功能"""
    print("\n🎯 整合用戶權限管理系統功能演示")
    print("=" * 60)
    
    # 1. 顯示系統統計
    print("\n📊 系統統計資訊:")
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    staff_users = User.objects.filter(is_staff=True).count()
    superusers = User.objects.filter(is_superuser=True).count()
    
    print(f"  總用戶數: {total_users}")
    print(f"  活躍用戶: {active_users}")
    print(f"  管理員: {staff_users}")
    print(f"  超級用戶: {superusers}")
    
    # 2. 顯示權限統計
    print("\n🔐 權限分布統計:")
    profiles = UserProfile.objects.all()
    
    web_permissions = {
        'Web Protocol RAG': len([p for p in profiles if p.web_protocol_rag]),
        'Web AI OCR': len([p for p in profiles if p.web_ai_ocr]),
        'Web RVT Assistant': len([p for p in profiles if p.web_rvt_assistant])
    }
    
    kb_permissions = {
        'KB Protocol RAG': len([p for p in profiles if p.kb_protocol_rag]),
        'KB AI OCR': len([p for p in profiles if p.kb_ai_ocr]),
        'KB RVT Assistant': len([p for p in profiles if p.kb_rvt_assistant])
    }
    
    super_admins = len([p for p in profiles if p.is_super_admin])
    
    print("  Web 功能權限:")
    for feature, count in web_permissions.items():
        print(f"    {feature}: {count} 用戶")
    
    print("  知識庫權限:")
    for feature, count in kb_permissions.items():
        print(f"    {feature}: {count} 用戶")
    
    print(f"  超級管理員: {super_admins} 用戶")
    
    # 3. 顯示用戶詳細資訊
    print("\n👥 用戶詳細資訊:")
    users_with_profiles = User.objects.select_related('userprofile').all()[:5]  # 只顯示前5個用戶
    
    for user in users_with_profiles:
        try:
            profile = user.userprofile
            status = "🟢" if user.is_active else "🔴"
            admin_badge = "👑" if user.is_superuser else ("🛡️" if user.is_staff else "👤")
            
            print(f"  {status} {admin_badge} {user.username} ({user.email})")
            
            # 顯示功能權限
            web_perms = []
            if profile.web_protocol_rag: web_perms.append("Protocol RAG")
            if profile.web_ai_ocr: web_perms.append("AI OCR")
            if profile.web_rvt_assistant: web_perms.append("RVT Assistant")
            
            kb_perms = []
            if profile.kb_protocol_rag: kb_perms.append("Protocol RAG")
            if profile.kb_ai_ocr: kb_perms.append("AI OCR")
            if profile.kb_rvt_assistant: kb_perms.append("RVT Assistant")
            
            if web_perms:
                print(f"    🌐 Web: {', '.join(web_perms)}")
            if kb_perms:
                print(f"    📚 KB: {', '.join(kb_perms)}")
            if profile.is_super_admin:
                print(f"    🔑 超級管理員權限")
            if not web_perms and not kb_perms and not profile.is_super_admin:
                print(f"    ⚪ 無特殊權限")
                
        except UserProfile.DoesNotExist:
            print(f"  ⚠️ {user.username} - 缺少權限配置")

def show_api_endpoints():
    """顯示可用的 API 端點"""
    print("\n🔌 整合用戶管理 API 端點:")
    print("=" * 60)
    
    endpoints = [
        {
            'method': 'GET',
            'url': '/api/users/',
            'description': '獲取用戶列表（基本資料）',
            'auth': '需要管理員權限'
        },
        {
            'method': 'POST',
            'url': '/api/users/',
            'description': '創建新用戶',
            'auth': '需要管理員權限'
        },
        {
            'method': 'PUT',
            'url': '/api/users/{id}/',
            'description': '更新用戶基本資料',
            'auth': '需要管理員權限'
        },
        {
            'method': 'DELETE',
            'url': '/api/users/{id}/',
            'description': '刪除用戶',
            'auth': '需要管理員權限'
        },
        {
            'method': 'GET',
            'url': '/api/profiles/permissions/',
            'description': '獲取所有用戶權限列表',
            'auth': '需要超級管理員權限'
        },
        {
            'method': 'PATCH',
            'url': '/api/profiles/{id}/permissions/',
            'description': '更新用戶功能權限',
            'auth': '需要超級管理員權限'
        },
        {
            'method': 'GET',
            'url': '/api/profiles/my-permissions/',
            'description': '獲取當前用戶權限',
            'auth': '需要登入'
        }
    ]
    
    for endpoint in endpoints:
        print(f"  {endpoint['method']:<6} {endpoint['url']:<35} - {endpoint['description']}")
        print(f"         權限要求: {endpoint['auth']}")
        print()

def show_web_interface_features():
    """顯示 Web 界面功能"""
    print("\n🖥️ Web 界面功能:")
    print("=" * 60)
    
    features = [
        "📋 整合用戶管理表格 - 同時顯示用戶資料和權限",
        "🔍 用戶搜索功能 - 支援用戶名、郵箱、姓名搜索",
        "➕ 新增用戶功能 - 包含基本資料和系統權限設定",
        "✏️ 編輯用戶資料 - 修改基本資訊和系統權限",
        "🔑 權限管理對話框 - 獨立的功能權限設定界面",
        "🏷️ 權限標籤顯示 - 彩色標籤顯示用戶權限狀態",
        "🔄 狀態切換 - 一鍵啟用/停用用戶帳號",
        "🗑️ 用戶刪除 - 安全確認的用戶刪除功能",
        "📱 響應式設計 - 適配不同螢幕尺寸",
        "🚨 權限保護 - 只有管理員可以訪問管理功能"
    ]
    
    for feature in features:
        print(f"  {feature}")

def show_security_features():
    """顯示安全功能"""
    print("\n🛡️ 安全功能:")
    print("=" * 60)
    
    security_features = [
        "🔐 多層權限檢查 - Django 超級用戶 > 超級管理員 > 功能權限",
        "🚫 API 端點保護 - 未授權用戶無法訪問管理 API",
        "👥 用戶隔離 - 普通用戶只能看到自己的資料",
        "🔒 權限繼承 - 超級用戶自動擁有所有權限",
        "⚠️ 操作確認 - 刪除等危險操作需要確認",
        "📝 操作日誌 - 所有權限變更都有記錄",
        "🛑 防止自我刪除 - 用戶無法刪除自己的帳號",
        "🔄 自動創建 Profile - 新用戶自動創建權限配置"
    ]
    
    for feature in security_features:
        print(f"  {feature}")

def show_usage_guide():
    """顯示使用指南"""
    print("\n📖 使用指南:")
    print("=" * 60)
    
    print("1. 📱 Web 界面訪問:")
    print("   - 登入系統後，管理員可在側邊欄看到「用戶權限管理」選項")
    print("   - 訪問路徑: /admin/user-management")
    print("   - 需要 Django 管理員或超級用戶權限")
    
    print("\n2. 👤 用戶管理:")
    print("   - 點擊「新增用戶」按鈕創建新帳號")
    print("   - 點擊「編輯」按鈕修改用戶基本資料")
    print("   - 使用搜索框快速找到特定用戶")
    print("   - 切換開關啟用/停用用戶帳號")
    
    print("\n3. 🔑 權限管理:")
    print("   - 點擊「管理權限」按鈕打開權限設定對話框")
    print("   - Web 功能權限控制 Web 界面功能訪問")
    print("   - 知識庫權限控制知識庫功能訪問")
    print("   - 超級管理員權限控制權限管理功能")
    
    print("\n4. 🛠️ 命令行管理:")
    print("   - docker exec -it ai-django python manage_permissions.py")
    print("   - 提供交互式權限管理界面")
    print("   - 適合批量操作和腳本化管理")

def main():
    """主函數"""
    print("🎯 AI Platform 整合用戶權限管理系統")
    print("=" * 60)
    print(f"報告生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    show_integrated_system_features()
    show_api_endpoints()
    show_web_interface_features()
    show_security_features()
    show_usage_guide()
    
    print(f"\n✅ 整合用戶權限管理系統演示完成！")
    print("💡 現在您可以:")
    print("   1. 訪問 http://10.10.172.127/admin/user-management 使用 Web 界面")
    print("   2. 使用 API 端點進行程式化管理")
    print("   3. 通過命令行工具進行批量操作")

if __name__ == "__main__":
    main()