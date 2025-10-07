#!/usr/bin/env python3
"""
用戶權限系統測試腳本
測試新的權限控制功能是否正常工作
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

# 測試配置
BASE_URL = "http://localhost:8000"
TEST_USERS = [
    {
        'username': 'test_admin',
        'password': 'test123456',
        'email': 'admin@test.com',
        'is_super_admin': True,
        'permissions': {
            'web_protocol_rag': True,
            'web_ai_ocr': True,
            'web_rvt_assistant': True,
            'kb_protocol_rag': True,
            'kb_ai_ocr': True,
            'kb_rvt_assistant': True
        }
    },
    {
        'username': 'test_user1',
        'password': 'test123456',
        'email': 'user1@test.com',
        'is_super_admin': False,
        'permissions': {
            'web_protocol_rag': True,
            'web_ai_ocr': False,
            'web_rvt_assistant': True,
            'kb_protocol_rag': False,
            'kb_ai_ocr': False,
            'kb_rvt_assistant': True
        }
    },
    {
        'username': 'test_user2',
        'password': 'test123456',
        'email': 'user2@test.com',
        'is_super_admin': False,
        'permissions': {
            'web_protocol_rag': False,
            'web_ai_ocr': True,
            'web_rvt_assistant': False,
            'kb_protocol_rag': True,
            'kb_ai_ocr': True,
            'kb_rvt_assistant': False
        }
    }
]

def create_test_users():
    """創建測試用戶"""
    print("\n🔧 創建測試用戶...")
    
    for user_data in TEST_USERS:
        try:
            # 創建或獲取用戶
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'is_active': True
                }
            )
            
            if created:
                user.set_password(user_data['password'])
                user.save()
                print(f"  ✅ 創建用戶: {user_data['username']}")
            else:
                print(f"  ℹ️ 用戶已存在: {user_data['username']}")
            
            # 創建或更新 UserProfile
            profile, profile_created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'is_super_admin': user_data['is_super_admin'],
                    **user_data['permissions']
                }
            )
            
            if not profile_created:
                # 更新現有的 profile
                profile.is_super_admin = user_data['is_super_admin']
                for perm, value in user_data['permissions'].items():
                    setattr(profile, perm, value)
                profile.save()
                print(f"    ✅ 更新權限配置")
            else:
                print(f"    ✅ 創建權限配置")
                
        except Exception as e:
            print(f"    ❌ 創建用戶失敗 {user_data['username']}: {e}")

def test_api_endpoints():
    """測試 API 端點"""
    print("\n🔍 測試 API 端點...")
    
    session = requests.Session()
    
    # 測試權限 API - 不登入的情況
    try:
        response = session.get(f"{BASE_URL}/api/profiles/permissions/")
        print(f"  📡 未認證訪問權限API: {response.status_code}")
        if response.status_code == 401 or response.status_code == 403:
            print("    ✅ 權限保護正常工作")
        else:
            print("    ⚠️ 可能存在權限洩漏")
    except Exception as e:
        print(f"    ❌ API 測試失敗: {e}")

    # 測試超級管理員登入
    try:
        login_data = {
            'username': 'test_admin',
            'password': 'test123456'
        }
        response = session.post(f"{BASE_URL}/api/auth/login/", json=login_data)
        print(f"  📡 管理員登入: {response.status_code}")
        
        if response.status_code == 200:
            print("    ✅ 管理員登入成功")
            
            # 測試權限列表 API
            response = session.get(f"{BASE_URL}/api/profiles/permissions/")
            print(f"  📡 管理員訪問權限列表: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"    ✅ 成功獲取 {data.get('count', 0)} 個用戶權限")
                else:
                    print("    ⚠️ API 響應格式異常")
            
            # 測試個人權限 API
            response = session.get(f"{BASE_URL}/api/profiles/my-permissions/")
            print(f"  📡 獲取個人權限: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    permissions = data.get('data', {})
                    print(f"    ✅ 個人權限: 超級管理員={permissions.get('is_super_admin', False)}")
                
        else:
            print("    ❌ 管理員登入失敗")
            
    except Exception as e:
        print(f"    ❌ 管理員測試失敗: {e}")

def test_database_structure():
    """測試資料庫結構"""
    print("\n🗄️ 測試資料庫結構...")
    
    try:
        # 檢查 UserProfile 模型欄位
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='api_userprofile';")
            columns = [row[0] for row in cursor.fetchall()]
            
        required_fields = [
            'web_protocol_rag', 'web_ai_ocr', 'web_rvt_assistant',
            'kb_protocol_rag', 'kb_ai_ocr', 'kb_rvt_assistant',
            'is_super_admin'
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in columns:
                missing_fields.append(field)
        
        if not missing_fields:
            print("  ✅ 所有權限欄位都已正確創建")
        else:
            print(f"  ❌ 缺少權限欄位: {missing_fields}")
            
        # 檢查測試用戶數量
        user_count = User.objects.filter(username__startswith='test_').count()
        profile_count = UserProfile.objects.filter(user__username__startswith='test_').count()
        
        print(f"  📊 測試用戶數量: {user_count}")
        print(f"  📊 測試檔案數量: {profile_count}")
        
        if user_count == profile_count:
            print("  ✅ 用戶和檔案數量一致")
        else:
            print("  ⚠️ 用戶和檔案數量不一致，可能存在孤立記錄")
            
    except Exception as e:
        print(f"  ❌ 資料庫測試失敗: {e}")

def test_permission_logic():
    """測試權限邏輯"""
    print("\n🔐 測試權限邏輯...")
    
    try:
        # 測試不同用戶的權限配置
        for user_data in TEST_USERS:
            user = User.objects.get(username=user_data['username'])
            profile = user.userprofile
            
            print(f"  👤 用戶: {user.username}")
            print(f"    超級管理員: {profile.is_super_admin}")
            
            # 檢查權限摘要
            summary = profile.get_permissions_summary()
            print(f"    權限摘要: {summary}")
            
            # 檢查權限檢查方法
            has_web = profile.has_any_web_permission()
            has_kb = profile.has_any_kb_permission()
            can_manage = profile.can_manage_permissions()
            
            print(f"    Web權限: {has_web}, KB權限: {has_kb}, 管理權限: {can_manage}")
            
            # 驗證權限配置正確性
            expected_permissions = user_data['permissions']
            actual_permissions = {
                'web_protocol_rag': profile.web_protocol_rag,
                'web_ai_ocr': profile.web_ai_ocr,
                'web_rvt_assistant': profile.web_rvt_assistant,
                'kb_protocol_rag': profile.kb_protocol_rag,
                'kb_ai_ocr': profile.kb_ai_ocr,
                'kb_rvt_assistant': profile.kb_rvt_assistant
            }
            
            matches = all(
                actual_permissions[key] == expected_permissions[key]
                for key in expected_permissions
            )
            
            if matches:
                print(f"    ✅ 權限配置正確")
            else:
                print(f"    ❌ 權限配置不匹配")
                print(f"      期望: {expected_permissions}")
                print(f"      實際: {actual_permissions}")
                
    except Exception as e:
        print(f"  ❌ 權限邏輯測試失敗: {e}")

def generate_test_report():
    """生成測試報告"""
    print("\n📋 測試報告摘要")
    print("=" * 50)
    
    try:
        # 統計信息
        total_users = User.objects.count()
        total_profiles = UserProfile.objects.count()
        test_users = User.objects.filter(username__startswith='test_').count()
        super_admins = UserProfile.objects.filter(is_super_admin=True).count()
        
        print(f"總用戶數: {total_users}")
        print(f"總檔案數: {total_profiles}")
        print(f"測試用戶數: {test_users}")
        print(f"超級管理員數: {super_admins}")
        
        # 權限統計
        web_permissions = {
            'Protocol RAG': UserProfile.objects.filter(web_protocol_rag=True).count(),
            'AI OCR': UserProfile.objects.filter(web_ai_ocr=True).count(),
            'RVT Assistant': UserProfile.objects.filter(web_rvt_assistant=True).count()
        }
        
        kb_permissions = {
            'Protocol RAG': UserProfile.objects.filter(kb_protocol_rag=True).count(),
            'AI OCR': UserProfile.objects.filter(kb_ai_ocr=True).count(),
            'RVT Assistant': UserProfile.objects.filter(kb_rvt_assistant=True).count()
        }
        
        print("\nWeb 功能權限統計:")
        for feature, count in web_permissions.items():
            print(f"  {feature}: {count} 用戶")
            
        print("\n知識庫權限統計:")
        for feature, count in kb_permissions.items():
            print(f"  {feature}: {count} 用戶")
            
        print(f"\n✅ 測試完成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"❌ 生成報告失敗: {e}")

def main():
    """主測試函數"""
    print("🚀 AI Platform 用戶權限系統測試")
    print("=" * 50)
    
    # 執行測試
    create_test_users()
    test_database_structure()
    test_permission_logic()
    test_api_endpoints()
    generate_test_report()
    
    print("\n🎉 所有測試執行完畢！")

if __name__ == "__main__":
    main()