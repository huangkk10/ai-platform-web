#!/usr/bin/env python
"""
Threshold Settings API 測試腳本
在 Django 容器內執行，測試 SearchThresholdSetting API

執行方式：
docker exec ai-django python test_threshold_settings_api.py
"""

import os
import sys
import django

# 設置 Django 環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')

# ⚠️ 重要：必須在 django.setup() 之前設置 ALLOWED_HOSTS
from django.conf import settings
if not settings.configured:
    django.setup()
else:
    # 如果已經配置，添加 testserver 到 ALLOWED_HOSTS
    if 'testserver' not in settings.ALLOWED_HOSTS:
        settings.ALLOWED_HOSTS.append('testserver')

from django.contrib.auth import get_user_model
from django.test import Client, override_settings
from api.models import SearchThresholdSetting
import json

User = get_user_model()

# 顏色輸出
class Colors:
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

def print_header(test_num, description):
    """打印測試標題"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.NC}")
    print(f"{Colors.BLUE}TEST {test_num}: {description}{Colors.NC}")
    print(f"{Colors.BLUE}{'='*60}{Colors.NC}")

def print_success(message):
    """打印成功訊息"""
    print(f"{Colors.GREEN}✓ {message}{Colors.NC}")

def print_error(message):
    """打印錯誤訊息"""
    print(f"{Colors.RED}✗ {message}{Colors.NC}")

def print_info(message):
    """打印資訊"""
    print(f"{Colors.YELLOW}ℹ {message}{Colors.NC}")

# 測試統計
total_tests = 0
passed_tests = 0
failed_tests = 0

def run_test(func):
    """測試裝飾器"""
    global total_tests, passed_tests, failed_tests
    total_tests += 1
    try:
        func()
        passed_tests += 1
        return True
    except AssertionError as e:
        failed_tests += 1
        print_error(f"測試失敗: {str(e)}")
        return False
    except Exception as e:
        failed_tests += 1
        print_error(f"執行錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

# ============================================================================
# 測試準備：創建測試用戶
# ============================================================================
print_header("準備", "創建測試用戶")

try:
    # 嘗試獲取或創建管理員用戶
    admin_user, created = User.objects.get_or_create(
        username='test_admin',
        defaults={
            'email': 'test_admin@example.com',
            'is_staff': True,
            'is_superuser': True
        }
    )
    if created:
        admin_user.set_password('test_password')
        admin_user.save()
        print_success(f"創建測試管理員: {admin_user.username}")
    else:
        print_info(f"使用現有管理員: {admin_user.username}")
except Exception as e:
    print_error(f"創建用戶失敗: {str(e)}")
    sys.exit(1)

# 創建測試客戶端（使用 override_settings 允許 testserver）
@override_settings(ALLOWED_HOSTS=['*'])
def create_test_client():
    return Client()

client = create_test_client()

# 登入
login_success = client.login(username='test_admin', password='test_password')
if login_success:
    print_success("登入成功")
else:
    print_error("登入失敗")
    sys.exit(1)

# ============================================================================
# 測試 1: 列出所有 Threshold 設定
# ============================================================================
def test_list_settings():
    print_header("1", "列出所有 Threshold 設定 (GET /api/search-threshold-settings/)")
    
    response = client.get('/api/search-threshold-settings/')
    
    print_info(f"HTTP 狀態碼: {response.status_code}")
    
    # 如果是 400，打印詳細錯誤
    if response.status_code == 400:
        try:
            error_data = response.json()
            print_error(f"錯誤詳情: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
        except:
            print_error(f"錯誤內容: {response.content.decode('utf-8')}")
    
    assert response.status_code == 200, f"預期 200，得到 {response.status_code}"
    print_success("請求成功 (HTTP 200)")
    
    data = response.json()
    print_info(f"返回 {len(data)} 個設定項目")
    
    assert len(data) >= 2, f"預期至少 2 個設定，得到 {len(data)} 個"
    print_success(f"設定數量正確: {len(data)} 個")
    
    # 顯示設定
    for item in data:
        print(f"\n  {Colors.YELLOW}Assistant: {item['assistant_type_display']}{Colors.NC}")
        print(f"    - Stage1 Threshold: {float(item['stage1_threshold'])*100:.0f}%")
        print(f"    - Stage1 Weights: Title={item['stage1_title_weight']}%, Content={item['stage1_content_weight']}%")
        print(f"    - Stage2 Threshold: {float(item['stage2_threshold'])*100:.0f}%")
        print(f"    - Stage2 Weights: Title={item['stage2_title_weight']}%, Content={item['stage2_content_weight']}%")
    
    return data

run_test(test_list_settings)

# ============================================================================
# 測試 2: 獲取 Protocol Assistant 設定
# ============================================================================
def test_get_protocol_settings():
    print_header("2", "獲取 Protocol Assistant 設定 (GET /api/search-threshold-settings/protocol_assistant/)")
    
    response = client.get('/api/search-threshold-settings/protocol_assistant/')
    
    print_info(f"HTTP 狀態碼: {response.status_code}")
    assert response.status_code == 200, f"預期 200，得到 {response.status_code}"
    print_success("請求成功 (HTTP 200)")
    
    data = response.json()
    
    # 驗證必要欄位
    required_fields = [
        'assistant_type', 'stage1_threshold', 'stage1_title_weight', 'stage1_content_weight',
        'stage2_threshold', 'stage2_title_weight', 'stage2_content_weight'
    ]
    
    for field in required_fields:
        assert field in data, f"缺少欄位: {field}"
        print_success(f"欄位存在: {field} = {data[field]}")
    
    # 儲存原始值供後續測試使用
    global original_protocol_settings
    original_protocol_settings = {
        'stage1_threshold': data['stage1_threshold'],
        'stage1_title_weight': data['stage1_title_weight'],
        'stage1_content_weight': data['stage1_content_weight'],
        'stage2_threshold': data['stage2_threshold'],
        'stage2_title_weight': data['stage2_title_weight'],
        'stage2_content_weight': data['stage2_content_weight'],
    }
    
    print_success(f"已儲存原始設定供後續測試使用")
    
    return data

# 初始化 global 變數
original_protocol_settings = None
original_rvt_settings = None

run_test(test_get_protocol_settings)

# ============================================================================
# 測試 3: 獲取 RVT Assistant 設定
# ============================================================================
def test_get_rvt_settings():
    print_header("3", "獲取 RVT Assistant 設定 (GET /api/search-threshold-settings/rvt_assistant/)")
    
    response = client.get('/api/search-threshold-settings/rvt_assistant/')
    
    print_info(f"HTTP 狀態碼: {response.status_code}")
    assert response.status_code == 200, f"預期 200，得到 {response.status_code}"
    print_success("請求成功 (HTTP 200)")
    
    data = response.json()
    
    assert data['assistant_type'] == 'rvt_assistant', "Assistant 類型不符"
    print_success(f"Assistant 類型正確: {data['assistant_type']}")
    
    # 儲存原始值
    global original_rvt_settings
    original_rvt_settings = {
        'stage1_threshold': data['stage1_threshold'],
        'stage1_title_weight': data['stage1_title_weight'],
        'stage1_content_weight': data['stage1_content_weight'],
        'stage2_threshold': data['stage2_threshold'],
        'stage2_title_weight': data['stage2_title_weight'],
        'stage2_content_weight': data['stage2_content_weight'],
    }
    
    print_success(f"已儲存 RVT 原始設定")
    
    return data

run_test(test_get_rvt_settings)

# ============================================================================
# 測試 4: 更新 Protocol Assistant 設定
# ============================================================================
def test_update_protocol_settings():
    print_header("4", "更新 Protocol Assistant 設定 (PATCH /api/search-threshold-settings/protocol_assistant/)")
    
    # 測試資料
    test_data = {
        'stage1_threshold': '0.65',
        'stage1_title_weight': 55,
        'stage1_content_weight': 45,
        'stage2_threshold': '0.58',
        'stage2_title_weight': 52,
        'stage2_content_weight': 48,
    }
    
    print_info(f"測試資料: Stage1 Threshold=65%, Title=55%, Content=45%")
    print_info(f"          Stage2 Threshold=58%, Title=52%, Content=48%")
    
    response = client.patch(
        '/api/search-threshold-settings/protocol_assistant/',
        data=json.dumps(test_data),
        content_type='application/json'
    )
    
    print_info(f"HTTP 狀態碼: {response.status_code}")
    assert response.status_code == 200, f"預期 200，得到 {response.status_code}"
    print_success("更新請求成功 (HTTP 200)")
    
    data = response.json()
    
    # 驗證更新結果
    assert data['stage1_threshold'] == '0.65', f"Stage1 Threshold 不符: {data['stage1_threshold']}"
    print_success(f"Stage1 Threshold 更新正確: {data['stage1_threshold']}")
    
    assert data['stage1_title_weight'] == 55, f"Stage1 Title Weight 不符: {data['stage1_title_weight']}"
    print_success(f"Stage1 Title Weight 更新正確: {data['stage1_title_weight']}%")
    
    assert data['stage1_content_weight'] == 45, f"Stage1 Content Weight 不符: {data['stage1_content_weight']}"
    print_success(f"Stage1 Content Weight 更新正確: {data['stage1_content_weight']}%")
    
    assert data['stage2_threshold'] == '0.58', f"Stage2 Threshold 不符: {data['stage2_threshold']}"
    print_success(f"Stage2 Threshold 更新正確: {data['stage2_threshold']}")
    
    return data

run_test(test_update_protocol_settings)

# ============================================================================
# 測試 5: 驗證更新是否持久化
# ============================================================================
def test_verify_persistence():
    print_header("5", "驗證 Protocol Assistant 更新是否持久化")
    
    # 重新獲取設定
    response = client.get('/api/search-threshold-settings/protocol_assistant/')
    
    assert response.status_code == 200, f"預期 200，得到 {response.status_code}"
    print_success("重新獲取設定成功")
    
    data = response.json()
    
    # 驗證持久化
    assert data['stage1_threshold'] == '0.65', f"持久化失敗: {data['stage1_threshold']}"
    print_success("Stage1 Threshold 持久化正確: 0.65")
    
    assert data['stage1_title_weight'] == 55, f"持久化失敗: {data['stage1_title_weight']}"
    print_success("Stage1 Title Weight 持久化正確: 55%")
    
    assert data['stage1_content_weight'] == 45, f"持久化失敗: {data['stage1_content_weight']}"
    print_success("Stage1 Content Weight 持久化正確: 45%")
    
    # 同時驗證資料庫
    db_record = SearchThresholdSetting.objects.get(assistant_type='protocol_assistant')
    assert str(db_record.stage1_threshold) == '0.65', "資料庫中的值不符"
    print_success("資料庫中的值正確")
    
    return data

run_test(test_verify_persistence)

# ============================================================================
# 測試 6: 恢復 Protocol Assistant 原始設定
# ============================================================================
def test_restore_protocol_settings():
    print_header("6", "恢復 Protocol Assistant 原始設定")
    
    if not original_protocol_settings:
        print_error("未找到原始設定，跳過此測試")
        return None
    
    print_info(f"恢復設定: Stage1 Threshold={original_protocol_settings['stage1_threshold']}")
    
    response = client.patch(
        '/api/search-threshold-settings/protocol_assistant/',
        data=json.dumps(original_protocol_settings),
        content_type='application/json'
    )
    
    assert response.status_code == 200, f"預期 200，得到 {response.status_code}"
    print_success("恢復原始設定成功")
    
    data = response.json()
    print_success(f"Protocol Assistant 設定已恢復: Threshold={data['stage1_threshold']}")
    
    return data

run_test(test_restore_protocol_settings)

# ============================================================================
# 測試 7: 測試不存在的 Assistant
# ============================================================================
def test_nonexistent_assistant():
    print_header("7", "測試錯誤處理 - 不存在的 Assistant")
    
    response = client.get('/api/search-threshold-settings/unknown_assistant/')
    
    print_info(f"HTTP 狀態碼: {response.status_code}")
    assert response.status_code == 404, f"預期 404，得到 {response.status_code}"
    print_success("正確返回 404 Not Found")
    
    return response

run_test(test_nonexistent_assistant)

# ============================================================================
# 測試 8: 測試資料庫直接查詢
# ============================================================================
def test_database_query():
    print_header("8", "測試資料庫直接查詢")
    
    # 查詢所有設定
    settings = SearchThresholdSetting.objects.all()
    
    print_info(f"資料庫中共有 {settings.count()} 個設定")
    assert settings.count() >= 2, f"預期至少 2 個設定，得到 {settings.count()} 個"
    print_success(f"資料庫設定數量正確: {settings.count()} 個")
    
    # 顯示資料庫中的設定
    for setting in settings:
        # 使用 get_assistant_type_display() 方法而不是屬性
        display_name = setting.get_assistant_type_display() if hasattr(setting, 'get_assistant_type_display') else setting.assistant_type
        print(f"\n  {Colors.YELLOW}{display_name}{Colors.NC}")
        print(f"    - Stage1: {float(setting.stage1_threshold)*100:.0f}% (Title={setting.stage1_title_weight}%, Content={setting.stage1_content_weight}%)")
        print(f"    - Stage2: {float(setting.stage2_threshold)*100:.0f}% (Title={setting.stage2_title_weight}%, Content={setting.stage2_content_weight}%)")
    
    return settings

run_test(test_database_query)

# ============================================================================
# 測試總結
# ============================================================================
print(f"\n{Colors.BLUE}{'='*60}{Colors.NC}")
print(f"{Colors.BLUE}測試總結{Colors.NC}")
print(f"{Colors.BLUE}{'='*60}{Colors.NC}")

print(f"總測試數: {Colors.BLUE}{total_tests}{Colors.NC}")
print(f"通過測試: {Colors.GREEN}{passed_tests}{Colors.NC}")
print(f"失敗測試: {Colors.RED}{failed_tests}{Colors.NC}")

if failed_tests == 0:
    print(f"\n{Colors.GREEN}✓ 所有測試通過！{Colors.NC}")
    sys.exit(0)
else:
    print(f"\n{Colors.RED}✗ 有 {failed_tests} 個測試失敗{Colors.NC}")
    sys.exit(1)
