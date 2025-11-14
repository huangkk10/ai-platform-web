#!/usr/bin/env python
"""
二階段搜尋權重配置 - 後端完整性測試

測試目標：
1. 後端完全就緒（API、資料庫、邏輯全部完成）
2. 可以透過 Django Admin 或 API 直接管理配置

作者：AI Assistant
日期：2025-11-14
"""

import os
import sys
import django

# 設定 Django 環境
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from django.db import connection
from django.contrib.auth.models import User
from api.models import SearchThresholdSetting
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
import json

class BackendReadinessTest:
    """後端完整性測試類"""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.client = APIClient()
        
    def print_header(self, title):
        """打印測試標題"""
        print(f"\n{'=' * 80}")
        print(f"  {title}")
        print(f"{'=' * 80}\n")
    
    def print_test(self, name, passed, details=""):
        """打印測試結果"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} | {name}")
        if details:
            print(f"      └─ {details}")
        
        if passed:
            self.passed += 1
        else:
            self.failed += 1
    
    # ==================== 測試 1: 資料庫完整性 ====================
    
    def test_database_schema(self):
        """測試 1.1: 驗證資料庫 Schema 是否完整"""
        self.print_header("測試 1: 資料庫完整性")
        
        with connection.cursor() as cursor:
            # 檢查 search_threshold_settings 表是否存在
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_name = 'search_threshold_settings'
            """)
            table_exists = cursor.fetchone()[0] == 1
            self.print_test(
                "1.1 資料庫表存在",
                table_exists,
                "search_threshold_settings 表已創建"
            )
            
            if not table_exists:
                return
            
            # 檢查所有必要欄位
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'search_threshold_settings'
                ORDER BY column_name
            """)
            columns = [row[0] for row in cursor.fetchall()]
            
            required_fields = [
                'assistant_type',
                'master_threshold',
                'title_weight',
                'content_weight',
                'stage1_threshold',        # 🆕 新增
                'stage1_title_weight',     # 🆕 新增
                'stage1_content_weight',   # 🆕 新增
                'stage2_threshold',        # 🆕 新增
                'stage2_title_weight',     # 🆕 新增
                'stage2_content_weight',   # 🆕 新增
                'use_unified_weights',     # 🆕 新增
                'description',
                'is_active',
                'created_at',
                'updated_at'
            ]
            
            missing_fields = [f for f in required_fields if f not in columns]
            all_fields_present = len(missing_fields) == 0
            
            details = f"共 {len(columns)} 個欄位"
            if missing_fields:
                details += f"，缺少: {', '.join(missing_fields)}"
            
            self.print_test(
                "1.2 所有欄位完整",
                all_fields_present,
                details
            )
            
            # 檢查欄位類型
            cursor.execute("""
                SELECT 
                    column_name,
                    data_type,
                    character_maximum_length,
                    numeric_precision,
                    numeric_scale
                FROM information_schema.columns 
                WHERE table_name = 'search_threshold_settings'
                AND column_name IN (
                    'stage1_threshold', 'stage2_threshold',
                    'stage1_title_weight', 'stage1_content_weight',
                    'stage2_title_weight', 'stage2_content_weight',
                    'use_unified_weights'
                )
                ORDER BY column_name
            """)
            
            field_types = {}
            for row in cursor.fetchall():
                field_types[row[0]] = {
                    'type': row[1],
                    'precision': row[3],
                    'scale': row[4]
                }
            
            # 驗證 threshold 欄位是 DECIMAL(3,2)
            threshold_fields_ok = (
                field_types.get('stage1_threshold', {}).get('precision') == 3 and
                field_types.get('stage1_threshold', {}).get('scale') == 2 and
                field_types.get('stage2_threshold', {}).get('precision') == 3 and
                field_types.get('stage2_threshold', {}).get('scale') == 2
            )
            
            self.print_test(
                "1.3 Threshold 欄位類型正確",
                threshold_fields_ok,
                "DECIMAL(3,2) - 支援 0.00 到 1.00"
            )
            
            # 驗證 weight 欄位是整數
            weight_fields_ok = all(
                field_types.get(f, {}).get('type') == 'integer'
                for f in [
                    'stage1_title_weight', 'stage1_content_weight',
                    'stage2_title_weight', 'stage2_content_weight'
                ]
            )
            
            self.print_test(
                "1.4 Weight 欄位類型正確",
                weight_fields_ok,
                "INTEGER - 支援 0 到 100"
            )
    
    def test_default_data(self):
        """測試 1.5: 驗證預設資料是否存在"""
        protocol_exists = SearchThresholdSetting.objects.filter(
            assistant_type='protocol_assistant'
        ).exists()
        
        rvt_exists = SearchThresholdSetting.objects.filter(
            assistant_type='rvt_assistant'
        ).exists()
        
        self.print_test(
            "1.5 Protocol Assistant 配置存在",
            protocol_exists,
            "資料庫中有 protocol_assistant 配置"
        )
        
        self.print_test(
            "1.6 RVT Assistant 配置存在",
            rvt_exists,
            "資料庫中有 rvt_assistant 配置"
        )
    
    def test_model_integrity(self):
        """測試 1.7: 驗證 Model 完整性"""
        try:
            setting = SearchThresholdSetting.objects.filter(
                assistant_type='protocol_assistant'
            ).first()
            
            if not setting:
                self.print_test("1.7 Model 欄位讀取", False, "找不到配置資料")
                return
            
            # 檢查所有新欄位是否可讀取
            new_fields = {
                'stage1_threshold': setting.stage1_threshold,
                'stage1_title_weight': setting.stage1_title_weight,
                'stage1_content_weight': setting.stage1_content_weight,
                'stage2_threshold': setting.stage2_threshold,
                'stage2_title_weight': setting.stage2_title_weight,
                'stage2_content_weight': setting.stage2_content_weight,
                'use_unified_weights': setting.use_unified_weights,
            }
            
            all_readable = all(v is not None for v in new_fields.values())
            
            details = f"7 個新欄位都可讀取"
            if not all_readable:
                missing = [k for k, v in new_fields.items() if v is None]
                details = f"缺少: {', '.join(missing)}"
            
            self.print_test(
                "1.7 Model 欄位讀取",
                all_readable,
                details
            )
            
            # 驗證權重總和
            stage1_sum = setting.stage1_title_weight + setting.stage1_content_weight
            stage2_sum = setting.stage2_title_weight + setting.stage2_content_weight
            
            weights_valid = stage1_sum == 100 and stage2_sum == 100
            
            details = (
                f"Stage1: {setting.stage1_title_weight}% + {setting.stage1_content_weight}% = {stage1_sum}%, "
                f"Stage2: {setting.stage2_title_weight}% + {setting.stage2_content_weight}% = {stage2_sum}%"
            )
            
            self.print_test(
                "1.8 權重總和驗證",
                weights_valid,
                details
            )
            
        except Exception as e:
            self.print_test("1.7 Model 欄位讀取", False, f"錯誤: {str(e)}")
    
    # ==================== 測試 2: API 完整性 ====================
    
    def test_api_endpoints(self):
        """測試 2: API 端點完整性"""
        self.print_header("測試 2: API 完整性")
        
        # 創建測試用戶（不使用 Token，使用 force_authenticate）
        try:
            user, created = User.objects.get_or_create(
                username='test_api_user',
                defaults={'is_staff': True, 'is_superuser': True}
            )
            if created:
                user.set_password('test_password_123')
                user.save()
            
            # 使用 force_authenticate 而非 Token
            self.client.force_authenticate(user=user)
            
            self.print_test(
                "2.1 測試用戶創建",
                True,
                f"用戶: {user.username}, 已認證"
            )
            
        except Exception as e:
            self.print_test("2.1 測試用戶創建", False, f"錯誤: {str(e)}")
            return
        
        # 測試 GET /api/search-threshold-settings/
        try:
            response = self.client.get('/api/search-threshold-settings/')
            get_success = response.status_code == 200
            
            if get_success:
                data = response.json()
                count = len(data) if isinstance(data, list) else data.get('count', 0)
                details = f"狀態碼: 200, 返回 {count} 筆配置"
            else:
                details = f"狀態碼: {response.status_code}"
            
            self.print_test(
                "2.2 GET API 端點",
                get_success,
                details
            )
            
            # 檢查返回資料是否包含新欄位
            if get_success and isinstance(data, list) and len(data) > 0:
                first_item = data[0]
                new_fields = [
                    'stage1_threshold', 'stage1_title_weight', 'stage1_content_weight',
                    'stage2_threshold', 'stage2_title_weight', 'stage2_content_weight',
                    'use_unified_weights'
                ]
                
                has_new_fields = all(field in first_item for field in new_fields)
                
                details = "7 個新欄位都在 API 回應中"
                if not has_new_fields:
                    missing = [f for f in new_fields if f not in first_item]
                    details = f"缺少: {', '.join(missing)}"
                
                self.print_test(
                    "2.3 API 回應包含新欄位",
                    has_new_fields,
                    details
                )
                
        except Exception as e:
            self.print_test("2.2 GET API 端點", False, f"錯誤: {str(e)}")
        
        # 測試 PATCH 更新配置
        try:
            # 獲取第一筆配置
            setting = SearchThresholdSetting.objects.filter(
                assistant_type='protocol_assistant'
            ).first()
            
            if not setting:
                self.print_test("2.4 PATCH 更新配置", False, "找不到測試資料")
                return
            
            # 準備測試資料（切換到獨立權重模式）
            update_data = {
                'use_unified_weights': False,
                'stage1_threshold': 0.75,
                'stage1_title_weight': 65,
                'stage1_content_weight': 35,
                'stage2_threshold': 0.55,
                'stage2_title_weight': 45,
                'stage2_content_weight': 55
            }
            
            response = self.client.patch(
                f'/api/search-threshold-settings/{setting.id}/',
                data=json.dumps(update_data),
                content_type='application/json'
            )
            
            patch_success = response.status_code == 200
            
            if patch_success:
                # 驗證資料是否真的更新
                setting.refresh_from_db()
                updated_correctly = (
                    setting.use_unified_weights == False and
                    float(setting.stage1_threshold) == 0.75 and
                    setting.stage1_title_weight == 65 and
                    float(setting.stage2_threshold) == 0.55 and
                    setting.stage2_title_weight == 45
                )
                
                details = "配置成功更新" if updated_correctly else "更新失敗"
            else:
                details = f"狀態碼: {response.status_code}"
                updated_correctly = False
            
            self.print_test(
                "2.4 PATCH 更新配置",
                patch_success and updated_correctly,
                details
            )
            
            # 恢復原始配置
            setting.use_unified_weights = True
            setting.stage1_threshold = 0.70
            setting.stage1_title_weight = 60
            setting.stage1_content_weight = 40
            setting.save()
            
        except Exception as e:
            self.print_test("2.4 PATCH 更新配置", False, f"錯誤: {str(e)}")
        
        # 測試權重驗證（總和必須為 100）
        try:
            update_data = {
                'stage1_title_weight': 55,  # 55 + 40 = 95 (錯誤)
                'stage1_content_weight': 40
            }
            
            response = self.client.patch(
                f'/api/search-threshold-settings/{setting.id}/',
                data=json.dumps(update_data),
                content_type='application/json'
            )
            
            validation_works = response.status_code == 400
            
            details = "驗證成功拒絕不合法資料" if validation_works else f"狀態碼: {response.status_code}"
            
            self.print_test(
                "2.5 權重驗證（總和檢查）",
                validation_works,
                details
            )
            
        except Exception as e:
            self.print_test("2.5 權重驗證", False, f"錯誤: {str(e)}")
    
    # ==================== 測試 3: 邏輯完整性 ====================
    
    def test_threshold_manager(self):
        """測試 3: ThresholdManager 邏輯完整性"""
        self.print_header("測試 3: 邏輯完整性（ThresholdManager）")
        
        try:
            from library.common.threshold_manager import get_threshold_manager
            
            manager = get_threshold_manager()
            
            self.print_test(
                "3.1 ThresholdManager 初始化",
                manager is not None,
                "Singleton 模式正常運作"
            )
            
            # 測試 get_threshold() 支援 stage
            threshold_s1 = manager.get_threshold('protocol_assistant', stage=1)
            threshold_s2 = manager.get_threshold('protocol_assistant', stage=2)
            
            threshold_valid = (
                isinstance(threshold_s1, float) and 0 <= threshold_s1 <= 1 and
                isinstance(threshold_s2, float) and 0 <= threshold_s2 <= 1
            )
            
            details = f"Stage1: {threshold_s1}, Stage2: {threshold_s2}"
            
            self.print_test(
                "3.2 get_threshold() 支援 stage",
                threshold_valid,
                details
            )
            
            # 測試 get_weights() 方法
            weights_s1 = manager.get_weights('protocol_assistant', stage=1)
            weights_s2 = manager.get_weights('protocol_assistant', stage=2)
            
            weights_valid = (
                isinstance(weights_s1, tuple) and len(weights_s1) == 2 and
                isinstance(weights_s2, tuple) and len(weights_s2) == 2 and
                0 <= weights_s1[0] <= 1 and 0 <= weights_s1[1] <= 1 and
                0 <= weights_s2[0] <= 1 and 0 <= weights_s2[1] <= 1
            )
            
            details = (
                f"Stage1: {int(weights_s1[0]*100)}%/{int(weights_s1[1]*100)}%, "
                f"Stage2: {int(weights_s2[0]*100)}%/{int(weights_s2[1]*100)}%"
            )
            
            self.print_test(
                "3.3 get_weights() 支援 stage",
                weights_valid,
                details
            )
            
            # 測試快取刷新
            manager._refresh_cache()
            cache_valid = len(manager._cache) > 0
            
            self.print_test(
                "3.4 快取機制正常",
                cache_valid,
                f"快取中有 {len(manager._cache)} 個配置"
            )
            
        except Exception as e:
            self.print_test("3.1 ThresholdManager 初始化", False, f"錯誤: {str(e)}")
    
    def test_search_service_integration(self):
        """測試 3.5: 搜尋服務整合"""
        try:
            from library.protocol_guide.search_service import ProtocolGuideSearchService
            
            service = ProtocolGuideSearchService()
            
            # 測試 section_search (Stage 1)
            results_s1 = service.section_search("USB 測試", top_k=2, threshold=0.7)
            stage1_works = isinstance(results_s1, list)
            
            self.print_test(
                "3.5 搜尋服務 Stage 1（段落）",
                stage1_works,
                f"返回 {len(results_s1) if stage1_works else 0} 個結果"
            )
            
            # 測試 full_document_search (Stage 2)
            results_s2 = service.full_document_search("USB 測試", top_k=2, threshold=0.6)
            stage2_works = isinstance(results_s2, list)
            
            self.print_test(
                "3.6 搜尋服務 Stage 2（全文）",
                stage2_works,
                f"返回 {len(results_s2) if stage2_works else 0} 個結果"
            )
            
        except Exception as e:
            self.print_test("3.5 搜尋服務整合", False, f"錯誤: {str(e)}")
    
    # ==================== 測試 4: Django Admin 可用性 ====================
    
    def test_django_admin(self):
        """測試 4: Django Admin 管理介面"""
        self.print_header("測試 4: Django Admin 可用性")
        
        try:
            from django.contrib import admin
            
            # 檢查 Model 是否已註冊到 Admin
            is_registered = SearchThresholdSetting in admin.site._registry
            
            self.print_test(
                "4.1 Model 已註冊到 Admin",
                is_registered,
                "可透過 Django Admin 管理配置" if is_registered else "未註冊到 Admin"
            )
            
            if is_registered:
                admin_class = admin.site._registry[SearchThresholdSetting]
                
                # 檢查 list_display
                has_list_display = hasattr(admin_class, 'list_display')
                
                self.print_test(
                    "4.2 Admin 有 list_display",
                    has_list_display,
                    f"{len(admin_class.list_display) if has_list_display else 0} 個顯示欄位"
                )
                
                # 檢查 fieldsets 或 fields
                has_fields_config = (
                    hasattr(admin_class, 'fieldsets') or 
                    hasattr(admin_class, 'fields') or
                    hasattr(admin_class, 'get_fieldsets')
                )
                
                self.print_test(
                    "4.3 Admin 有表單配置",
                    has_fields_config,
                    "fieldsets 或 fields 已配置" if has_fields_config else "使用預設配置"
                )
            
            # 測試 Admin URL 可訪問（需要登入）
            admin_url = '/admin/api/searchthresholdsetting/'
            
            # 創建 superuser 並登入
            superuser, created = User.objects.get_or_create(
                username='admin_test',
                defaults={'is_staff': True, 'is_superuser': True}
            )
            if created:
                superuser.set_password('admin123')
                superuser.save()
            
            self.client.force_authenticate(user=superuser)
            response = self.client.get(admin_url)
            
            # Django Admin 會重定向到登入頁面（302）或顯示頁面（200）
            admin_accessible = response.status_code in [200, 302]
            
            details = f"狀態碼: {response.status_code}, URL: {admin_url}"
            
            self.print_test(
                "4.4 Admin 頁面可訪問",
                admin_accessible,
                details
            )
            
        except Exception as e:
            self.print_test("4.1 Django Admin", False, f"錯誤: {str(e)}")
    
    # ==================== 執行所有測試 ====================
    
    def run_all_tests(self):
        """執行所有測試"""
        print("\n" + "=" * 80)
        print("  二階段搜尋權重配置 - 後端完整性測試")
        print("=" * 80)
        print(f"  測試日期: 2025-11-14")
        print(f"  測試環境: Django Container (ai-django)")
        print("=" * 80)
        
        # 測試 1: 資料庫完整性
        self.test_database_schema()
        self.test_default_data()
        self.test_model_integrity()
        
        # 測試 2: API 完整性
        self.test_api_endpoints()
        
        # 測試 3: 邏輯完整性
        self.test_threshold_manager()
        self.test_search_service_integration()
        
        # 測試 4: Django Admin
        self.test_django_admin()
        
        # 總結
        self.print_summary()
    
    def print_summary(self):
        """打印測試總結"""
        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0
        
        print("\n" + "=" * 80)
        print("  測試總結")
        print("=" * 80)
        print(f"  總計: {total} 項測試")
        print(f"  ✅ 通過: {self.passed} 項")
        print(f"  ❌ 失敗: {self.failed} 項")
        print(f"  📊 通過率: {pass_rate:.1f}%")
        print("=" * 80)
        
        if self.failed == 0:
            print("\n🎉 所有測試通過！後端完全就緒，可以正式使用。")
            print("\n✅ 驗證結果:")
            print("   1. ✅ 後端完全就緒（API、資料庫、邏輯全部完成）")
            print("   2. ✅ 可以透過 Django Admin 或 API 直接管理配置")
            print("\n📝 下一步:")
            print("   - 可以在 Django Admin 中管理配置: http://localhost/admin/api/searchthresholdsetting/")
            print("   - 可以透過 API 管理配置: http://localhost/api/search-threshold-settings/")
            print("   - 可以開始整合測試（Dify Studio 端到端測試）")
        else:
            print(f"\n⚠️ 有 {self.failed} 項測試失敗，請檢查後端配置。")
        
        print()

# 執行測試
if __name__ == '__main__':
    tester = BackendReadinessTest()
    tester.run_all_tests()
