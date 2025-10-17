# ViewSets Mixins 單元測試

## 📋 測試概覽

這個目錄包含了 Plan B+ 重構中所有 Mixin 類的單元測試。

### 測試文件列表

1. **test_library_manager_mixin.py** - LibraryManagerMixin 測試
   - 測試數量：30+ 個測試
   - 覆蓋率目標：> 90%
   - 功能：Library 初始化和管理

2. **test_fallback_logic_mixin.py** - FallbackLogicMixin 測試
   - 測試數量：25+ 個測試
   - 覆蓋率目標：> 85%
   - 功能：三層備用邏輯

3. **test_vector_management_mixin.py** - VectorManagementMixin 測試
   - 測試數量：20+ 個測試
   - 覆蓋率目標：> 80%
   - 功能：向量自動管理

4. **test_permission_mixin.py** - PermissionMixin 測試
   - 測試數量：20+ 個測試
   - 覆蓋率目標：> 90%
   - 功能：標準權限控制

**總計**：約 95 個單元測試

## 🚀 運行測試

### 方法 1：使用測試腳本（推薦）

```bash
# 在專案根目錄執行
python tests/test_mixins/run_tests.py
```

### 方法 2：使用 pytest 直接運行

```bash
# 運行所有 Mixin 測試
pytest tests/test_mixins/ -v

# 運行特定測試文件
pytest tests/test_mixins/test_library_manager_mixin.py -v

# 運行特定測試類
pytest tests/test_mixins/test_library_manager_mixin.py::TestLibraryManagerMixin -v

# 運行特定測試方法
pytest tests/test_mixins/test_library_manager_mixin.py::TestLibraryManagerMixin::test_has_manager_true_when_library_enabled -v
```

### 方法 3：在 Docker 容器中運行

```bash
# 進入 Django 容器
docker exec -it ai-django bash

# 運行測試
cd /app
python tests/test_mixins/run_tests.py

# 或使用 pytest
pytest tests/test_mixins/ -v
```

## 📊 生成測試覆蓋率報告

```bash
# 生成 HTML 覆蓋率報告
pytest tests/test_mixins/ \
    --cov=api.views.mixins \
    --cov-report=html \
    --cov-report=term \
    -v

# 查看報告
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## 🎯 測試結構

每個測試文件都遵循相同的結構：

```python
# 1. 設置 Mock ViewSet
class MockViewSet(MixinClass):
    """測試用的 Mock ViewSet"""
    pass

# 2. 測試核心功能
class TestMixinClass(TestCase):
    """主要測試類"""
    
    def test_feature_success(self):
        """測試成功場景"""
        pass
    
    def test_feature_failure(self):
        """測試失敗場景"""
        pass
    
    def test_feature_edge_case(self):
        """測試邊界情況"""
        pass

# 3. 整合測試
class TestMixinClassIntegration(TestCase):
    """整合測試類"""
    pass
```

## ✅ 測試檢查清單

### LibraryManagerMixin
- [ ] has_manager() 方法
- [ ] get_manager() 方法
- [ ] has_fallback_manager() 方法
- [ ] get_fallback_manager() 方法
- [ ] 配置錯誤處理
- [ ] 日誌記錄
- [ ] Manager 緩存

### FallbackLogicMixin
- [ ] Primary 成功場景
- [ ] Fallback 場景
- [ ] Emergency 場景
- [ ] 參數傳遞
- [ ] 異常處理
- [ ] 日誌記錄
- [ ] execute_with_fallback()

### VectorManagementMixin
- [ ] generate_vector_for_instance()
- [ ] update_vector_for_instance()
- [ ] delete_vector_for_instance()
- [ ] 1024 維向量配置
- [ ] 多字段處理
- [ ] 異常處理
- [ ] 日誌記錄

### PermissionMixin
- [ ] ReadOnlyForUserWriteForAdminMixin
- [ ] DelegatedPermissionMixin
- [ ] 讀操作權限
- [ ] 寫操作權限
- [ ] 不同用戶角色
- [ ] 自定義動作

## 🔍 測試技巧

### Mock 技巧

```python
from unittest.mock import Mock, patch

# Mock Django Settings
@override_settings(MY_SETTING=True)
def test_with_setting():
    pass

# Mock 函數
@patch('module.function_name')
def test_with_mock(mock_function):
    mock_function.return_value = 'mocked'
    pass

# Mock 類方法
mock_manager = Mock()
mock_manager.method_name = Mock(return_value='result')
```

### 斷言技巧

```python
# 基本斷言
self.assertTrue(condition)
self.assertEqual(a, b)
self.assertIsNone(value)

# Mock 斷言
mock_function.assert_called_once()
mock_function.assert_called_with('arg1', 'arg2')
mock_function.assert_not_called()

# 異常斷言
with self.assertRaises(Exception):
    function_that_raises()
```

## 📝 添加新測試

當添加新功能時，請按照以下步驟：

1. **在對應的測試文件中添加測試方法**
   ```python
   def test_new_feature(self):
       """測試新功能"""
       # Arrange
       setup_code()
       
       # Act
       result = self.viewset.new_feature()
       
       # Assert
       self.assertEqual(result, expected)
   ```

2. **運行測試確保通過**
   ```bash
   pytest tests/test_mixins/test_xxx_mixin.py::TestClass::test_new_feature -v
   ```

3. **檢查覆蓋率**
   ```bash
   pytest tests/test_mixins/ --cov=api.views.mixins --cov-report=term
   ```

## 🐛 常見問題

### Q: 測試無法找到 Django 模型
**A**: 確保正確設置了 Django settings：
```python
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()
```

### Q: Mock 沒有生效
**A**: 檢查 patch 的路徑是否正確，應該是函數被調用的地方，而不是定義的地方。

### Q: 測試運行很慢
**A**: 使用 `-n auto` 選項啟用並行測試：
```bash
pytest tests/test_mixins/ -n auto
```

## 📚 參考文檔

- [完整重構報告](../../docs/viewsets-refactoring-plan-b-plus-complete-report.md)
- [快速參考指南](../../docs/viewsets-refactoring-quick-reference.md)
- [測試計劃](../../docs/viewsets-refactoring-testing-plan.md)
- [Django Testing Documentation](https://docs.djangoproject.com/en/stable/topics/testing/)
- [pytest Documentation](https://docs.pytest.org/)

---

**作者**：AI Platform QA Team  
**版本**：v1.0  
**更新日期**：2025-10-17
