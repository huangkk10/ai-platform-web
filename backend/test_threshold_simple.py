#!/usr/bin/env python
"""
簡化版 Threshold Settings 測試
直接測試資料庫和 Serializer，避免 HTTP 層面的問題

執行方式：
docker exec ai-django python test_threshold_simple.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.models import SearchThresholdSetting
from api.serializers import SearchThresholdSettingSerializer
from decimal import Decimal

# 顏色輸出
class Colors:
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'

def print_header(test_num, description):
    print(f"\n{Colors.BLUE}{'='*60}{Colors.NC}")
    print(f"{Colors.BLUE}TEST {test_num}: {description}{Colors.NC}")
    print(f"{Colors.BLUE}{'='*60}{Colors.NC}")

def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.NC}")

def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.NC}")

def print_info(message):
    print(f"{Colors.YELLOW}ℹ {message}{Colors.NC}")

# 測試統計
total_tests = 0
passed_tests = 0
failed_tests = 0

def run_test(func):
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
# 測試 1: 查詢所有資料庫設定
# ============================================================================
def test_database_query():
    print_header("1", "查詢資料庫中的所有設定")
    
    settings = SearchThresholdSetting.objects.all()
    
    print_info(f"資料庫中共有 {settings.count()} 個設定")
    assert settings.count() >= 2, f"預期至少 2 個設定，得到 {settings.count()} 個"
    print_success(f"設定數量正確: {settings.count()} 個")
    
    for setting in settings:
        display_name = setting.get_assistant_type_display() if hasattr(setting, 'get_assistant_type_display') else setting.assistant_type
        print(f"\n  {Colors.YELLOW}{display_name} ({setting.assistant_type}){Colors.NC}")
        print(f"    - ID: {setting.id}")
        print(f"    - Stage1 Threshold: {float(setting.stage1_threshold)*100:.0f}%")
        print(f"    - Stage1 Weights: Title={setting.stage1_title_weight}%, Content={setting.stage1_content_weight}%")
        print(f"    - Stage2 Threshold: {float(setting.stage2_threshold)*100:.0f}%")
        print(f"    - Stage2 Weights: Title={setting.stage2_title_weight}%, Content={setting.stage2_content_weight}%")
    
    return settings

run_test(test_database_query)

# ============================================================================
# 測試 2: 測試 Serializer（讀取）
# ============================================================================
def test_serializer_read():
    print_header("2", "測試 Serializer 序列化")
    
    setting = SearchThresholdSetting.objects.get(assistant_type='protocol_assistant')
    print_info(f"查詢 Protocol Assistant 設定 (ID: {setting.id})")
    
    serializer = SearchThresholdSettingSerializer(setting)
    data = serializer.data
    
    print_info("序列化結果:")
    print(f"  - assistant_type: {data['assistant_type']}")
    print(f"  - assistant_type_display: {data['assistant_type_display']}")
    print(f"  - stage1_threshold: {data['stage1_threshold']}")
    print(f"  - stage1_title_weight: {data['stage1_title_weight']}")
    print(f"  - stage1_content_weight: {data['stage1_content_weight']}")
    print(f"  - stage2_threshold: {data['stage2_threshold']}")
    print(f"  - stage2_title_weight: {data['stage2_title_weight']}")
    print(f"  - stage2_content_weight: {data['stage2_content_weight']}")
    
    # 驗證必要欄位
    required_fields = [
        'assistant_type', 'assistant_type_display',
        'stage1_threshold', 'stage1_title_weight', 'stage1_content_weight',
        'stage2_threshold', 'stage2_title_weight', 'stage2_content_weight'
    ]
    
    for field in required_fields:
        assert field in data, f"缺少欄位: {field}"
    
    print_success("所有欄位都存在")
    
    return data

# 儲存原始值
original_data = None

def test_serializer_read_wrapper():
    global original_data
    original_data = test_serializer_read()

run_test(test_serializer_read_wrapper)

# ============================================================================
# 測試 3: 測試 Serializer（更新）
# ============================================================================
def test_serializer_update():
    print_header("3", "測試 Serializer 更新")
    
    setting = SearchThresholdSetting.objects.get(assistant_type='protocol_assistant')
    print_info(f"更新前: Stage1 Threshold = {setting.stage1_threshold}")
    
    # 測試資料
    update_data = {
        'stage1_threshold': '0.88',
        'stage1_title_weight': 75,
        'stage1_content_weight': 25,
        'stage2_threshold': '0.77',
        'stage2_title_weight': 65,
        'stage2_content_weight': 35,
    }
    
    print_info("測試更新資料:")
    print(f"  - Stage1 Threshold: 88%")
    print(f"  - Stage1 Weights: Title=75%, Content=25%")
    print(f"  - Stage2 Threshold: 77%")
    print(f"  - Stage2 Weights: Title=65%, Content=35%")
    
    serializer = SearchThresholdSettingSerializer(setting, data=update_data, partial=True)
    
    assert serializer.is_valid(), f"Serializer 驗證失敗: {serializer.errors}"
    print_success("資料驗證通過")
    
    serializer.save()
    print_success("更新儲存成功")
    
    # 重新載入驗證
    setting.refresh_from_db()
    
    assert str(setting.stage1_threshold) == '0.88', f"Stage1 Threshold 不符: {setting.stage1_threshold}"
    print_success(f"Stage1 Threshold 更新正確: {setting.stage1_threshold}")
    
    assert setting.stage1_title_weight == 75, f"Stage1 Title Weight 不符: {setting.stage1_title_weight}"
    print_success(f"Stage1 Title Weight 更新正確: {setting.stage1_title_weight}%")
    
    assert setting.stage1_content_weight == 25, f"Stage1 Content Weight 不符: {setting.stage1_content_weight}"
    print_success(f"Stage1 Content Weight 更新正確: {setting.stage1_content_weight}%")
    
    assert str(setting.stage2_threshold) == '0.77', f"Stage2 Threshold 不符: {setting.stage2_threshold}"
    print_success(f"Stage2 Threshold 更新正確: {setting.stage2_threshold}")
    
    return setting

run_test(test_serializer_update)

# ============================================================================
# 測試 4: 驗證權重總和
# ============================================================================
def test_weight_validation():
    print_header("4", "測試權重總和驗證")
    
    setting = SearchThresholdSetting.objects.get(assistant_type='protocol_assistant')
    
    # 測試無效資料（權重總和不等於 100）
    invalid_data = {
        'stage1_title_weight': 60,
        'stage1_content_weight': 60,  # 總和 = 120，應該要失敗
    }
    
    print_info("測試無效權重組合 (60% + 60% = 120%)")
    
    serializer = SearchThresholdSettingSerializer(setting, data=invalid_data, partial=True)
    
    # 應該驗證失敗
    is_valid = serializer.is_valid()
    
    if not is_valid:
        print_success("正確拒絕無效的權重組合")
        print_info(f"驗證錯誤: {serializer.errors}")
    else:
        print_error("❌ 未能檢測出無效的權重組合")
        raise AssertionError("Serializer 應該拒絕權重總和不等於 100 的資料")

run_test(test_weight_validation)

# ============================================================================
# 測試 5: 恢復原始設定
# ============================================================================
def test_restore_original():
    print_header("5", "恢復原始設定")
    
    if not original_data:
        print_error("未找到原始設定資料")
        return
    
    setting = SearchThresholdSetting.objects.get(assistant_type='protocol_assistant')
    
    restore_data = {
        'stage1_threshold': original_data['stage1_threshold'],
        'stage1_title_weight': original_data['stage1_title_weight'],
        'stage1_content_weight': original_data['stage1_content_weight'],
        'stage2_threshold': original_data['stage2_threshold'],
        'stage2_title_weight': original_data['stage2_title_weight'],
        'stage2_content_weight': original_data['stage2_content_weight'],
    }
    
    print_info(f"恢復設定: Stage1 Threshold = {restore_data['stage1_threshold']}")
    
    serializer = SearchThresholdSettingSerializer(setting, data=restore_data, partial=True)
    
    assert serializer.is_valid(), f"恢復資料驗證失敗: {serializer.errors}"
    serializer.save()
    
    print_success("原始設定已恢復")
    
    # 驗證
    setting.refresh_from_db()
    assert str(setting.stage1_threshold) == str(original_data['stage1_threshold']), "恢復失敗"
    print_success(f"驗證成功: Threshold = {setting.stage1_threshold}")

run_test(test_restore_original)

# ============================================================================
# 測試 6: 測試 RVT Assistant 設定
# ============================================================================
def test_rvt_assistant():
    print_header("6", "測試 RVT Assistant 設定")
    
    setting = SearchThresholdSetting.objects.get(assistant_type='rvt_assistant')
    
    print_info(f"RVT Assistant 設定:")
    print(f"  - Stage1 Threshold: {float(setting.stage1_threshold)*100:.0f}%")
    print(f"  - Stage1 Weights: Title={setting.stage1_title_weight}%, Content={setting.stage1_content_weight}%")
    print(f"  - Stage2 Threshold: {float(setting.stage2_threshold)*100:.0f}%")
    print(f"  - Stage2 Weights: Title={setting.stage2_title_weight}%, Content={setting.stage2_content_weight}%")
    
    # 驗證權重總和
    stage1_sum = setting.stage1_title_weight + setting.stage1_content_weight
    stage2_sum = setting.stage2_title_weight + setting.stage2_content_weight
    
    assert stage1_sum == 100, f"Stage1 權重總和不等於 100: {stage1_sum}"
    print_success(f"Stage1 權重總和正確: {stage1_sum}%")
    
    assert stage2_sum == 100, f"Stage2 權重總和不等於 100: {stage2_sum}"
    print_success(f"Stage2 權重總和正確: {stage2_sum}%")

run_test(test_rvt_assistant)

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
    print(f"\n{Colors.GREEN}✓ 所有測試通過！Threshold Settings 功能正常運作{Colors.NC}")
    print(f"\n{Colors.YELLOW}建議：您可以直接在瀏覽器中測試儲存功能了{Colors.NC}")
    exit(0)
else:
    print(f"\n{Colors.RED}✗ 有 {failed_tests} 個測試失敗{Colors.NC}")
    exit(1)
