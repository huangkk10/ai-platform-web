# 🔧 OCR Function API 整合規劃

> **建立日期**: 2025-11-30  
> **狀態**: ✅ 已完成  
> **完成日期**: 2025-11-30  
> **目標**: 在 Dify 配置管理系統中新增 OCR Function API 配置，供所有 Web Assistant 使用

---

## 📊 執行結果摘要

| 任務 | 狀態 | 備註 |
|------|------|------|
| 配置管理器修改 | ✅ 完成 | `dify_config_manager.py` 已更新 |
| 測試檔案創建 | ✅ 完成 | 3 個測試檔案已創建 |
| 快速測試 | ✅ 通過 | 4/4 測試通過 |
| 圖片 OCR 測試 | ✅ 通過 | API 連接成功，響應時間 11.78s |

### 測試結果詳情

#### 快速測試 (test_ocr_function_quick.py)
```
📋 測試 1: 配置載入 ✅
📋 測試 2: SUPPORTED_APPS 檢查 ✅
📋 測試 3: 配置驗證 ✅
📋 測試 4: API 連接測試 ✅
📊 測試結果: 4/4 通過
```

#### 圖片 OCR 測試 (test_ocr_function_image.py)
```
圖片: 螢幕擷取畫面 2025-11-30 141051.jpg (156.1 KB)
HTTP 狀態: 200 OK
響應時間: 11.78 秒
Token 使用: 915 (輸入 550 + 輸出 365)
```

---

## 📋 背景說明

### 新建立的 Dify App 資訊
| 項目 | 值 |
|------|-----|
| **工作室名稱** | OCR Function |
| **API Key** | `app-eFCJ5fDpoWV7CGKQ7VSoKgi0` |
| **應用類型** | Dify 工作流/Chat 應用 |
| **用途** | OCR 圖像識別功能，供各 Web Assistant 調用 |

### 現有配置管理架構

目前專案使用 `library/config/dify_config_manager.py` 統一管理所有 Dify 應用配置：

```
library/config/
├── dify_config_manager.py    # ✅ 主配置管理器（本次修改）
├── dify_app_configs.py       # 舊版配置（向後兼容）
├── dify_config.py            # 基礎配置
└── app_config.py             # 應用配置
```

---

## 🎯 實施步驟

### 步驟 1：在 `dify_config_manager.py` 中新增 OCR Function 配置

#### 1.1 新增配置方法

在 `DifyConfigManager` 類別中新增：

```python
@classmethod
def _get_ocr_function_config(cls):
    """動態獲取 OCR Function 配置"""
    ai_pc_ip = cls._get_ai_pc_ip()
    return {
        'api_url': f'http://{ai_pc_ip}/v1/chat-messages',
        'api_key': 'app-eFCJ5fDpoWV7CGKQ7VSoKgi0',
        'base_url': f'http://{ai_pc_ip}',
        'app_name': 'OCR Function',
        'workspace': 'OCR_Function',
        'description': 'Dify 工作流應用，提供 OCR 圖像識別功能，供各 Web Assistant 調用',
        'features': ['圖像識別', 'OCR 文字擷取', '結構化資料解析', '跨 Assistant 共用'],
        'timeout': 90,  # OCR 處理可能需要較長時間
        'response_mode': 'blocking'
    }
```

#### 1.2 更新 `SUPPORTED_APPS` 字典

```python
SUPPORTED_APPS = {
    'protocol_known_issue': 'Protocol Known Issue System',
    'protocol_guide': 'Protocol Guide',
    'rvt_guide': 'RVT Guide',
    'report_analyzer_3': 'Report Analyzer 3',
    'ai_ocr': 'AI OCR System',
    'ocr_function': 'OCR Function',  # ✅ 新增
}
```

#### 1.3 更新 `_get_config_dict` 方法

```python
def _get_config_dict(self, app_type: str) -> Dict[str, Any]:
    """獲取配置字典"""
    if app_type == 'protocol_known_issue':
        # ... 現有代碼
    elif app_type == 'ocr_function':  # ✅ 新增分支
        base_config = self._get_ocr_function_config()
        return self._get_base_config_with_env_override(base_config, 'DIFY_OCR_FUNCTION')
    # ... 其他分支
```

#### 1.4 新增類別便利方法

```python
def get_ocr_function_config(self) -> DifyAppConfig:
    """
    獲取 OCR Function 配置的便利方法
    
    Returns:
        DifyAppConfig: OCR Function 配置
    """
    return self.get_app_config('ocr_function')
```

#### 1.5 新增全局便利函數

```python
def get_ocr_function_config() -> DifyAppConfig:
    """
    獲取 OCR Function 配置的便利函數
    
    Returns:
        DifyAppConfig: OCR Function 配置對象
    """
    return default_config_manager.get_ocr_function_config()


def get_ocr_function_config_dict() -> Dict[str, Any]:
    """
    獲取 OCR Function 配置字典（向後兼容）
    
    Returns:
        Dict[str, Any]: 配置字典
    """
    return get_ocr_function_config().to_dict()
```

---

### 步驟 2：建立 OCR Function 專用客戶端（可選）

在 `library/dify_integration/` 目錄下建立專用客戶端：

#### 2.1 建立 `ocr_function_client.py`

```python
"""
OCR Function Dify 客戶端
提供 OCR 圖像識別功能的 Dify API 封裝
"""

import logging
import base64
from typing import Dict, Any, Optional
from .chat_client import DifyChatClient
from ..config.dify_config_manager import get_ocr_function_config

logger = logging.getLogger(__name__)


class OCRFunctionClient(DifyChatClient):
    """OCR Function Dify 客戶端"""
    
    def __init__(self):
        """初始化 OCR Function 客戶端"""
        config = get_ocr_function_config()
        super().__init__(
            api_url=config.api_url,
            api_key=config.api_key,
            base_url=config.base_url
        )
        self.config_obj = config
        
    def analyze_image(self, 
                      image_data: bytes, 
                      image_type: str = 'png',
                      additional_prompt: str = "",
                      user: str = "ocr_user") -> Dict[str, Any]:
        """
        分析圖像並提取文字
        
        Args:
            image_data: 圖像二進位資料
            image_type: 圖像類型 (png, jpg, jpeg)
            additional_prompt: 額外的提示文字
            user: 使用者標識
            
        Returns:
            Dict[str, Any]: 分析結果
        """
        # 將圖像轉換為 base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # 建立請求
        query = additional_prompt or "請分析這張圖片並提取其中的文字內容"
        
        # TODO: 根據 Dify OCR Function 的實際 API 格式調整
        result = self.chat(
            question=query,
            user=user,
            inputs={
                'image': f'data:image/{image_type};base64,{image_base64}'
            }
        )
        
        return result
    
    def extract_structured_data(self,
                                 image_data: bytes,
                                 data_format: str = "benchmark",
                                 user: str = "ocr_user") -> Dict[str, Any]:
        """
        提取結構化資料
        
        Args:
            image_data: 圖像二進位資料
            data_format: 資料格式 (benchmark, table, form)
            user: 使用者標識
            
        Returns:
            Dict[str, Any]: 結構化資料
        """
        format_prompts = {
            'benchmark': '請分析這張 Benchmark 測試結果截圖，提取測試分數、設備資訊等關鍵資料',
            'table': '請分析這張表格圖片，提取表格中的資料',
            'form': '請分析這張表單圖片，提取表單欄位和值'
        }
        
        prompt = format_prompts.get(data_format, format_prompts['benchmark'])
        
        return self.analyze_image(
            image_data=image_data,
            additional_prompt=prompt,
            user=user
        )


def create_ocr_function_client() -> OCRFunctionClient:
    """
    建立 OCR Function 客戶端的工廠函數
    
    Returns:
        OCRFunctionClient: 客戶端實例
    """
    return OCRFunctionClient()
```

---

### 步驟 3：更新現有 OCR 處理模組

更新 `library/ai_ocr/ocr_processor.py` 以支援新的 OCR Function：

```python
# 在 OCRProcessor 類別中新增方法

def process_with_dify_ocr_function(self, image_data: bytes) -> Dict[str, Any]:
    """
    使用 Dify OCR Function 處理圖像
    
    Args:
        image_data: 圖像二進位資料
        
    Returns:
        Dict[str, Any]: 處理結果
    """
    from library.dify_integration.ocr_function_client import create_ocr_function_client
    
    client = create_ocr_function_client()
    result = client.analyze_image(image_data)
    
    return result
```

---

## 📁 檔案變更清單

| 檔案路徑 | 變更類型 | 說明 |
|---------|----------|------|
| `library/config/dify_config_manager.py` | 修改 | 新增 OCR Function 配置 |
| `library/dify_integration/ocr_function_client.py` | 新增 | OCR Function 專用客戶端 |
| `library/ai_ocr/ocr_processor.py` | 修改 | 整合新的 OCR Function |

---

## ✅ 驗證步驟

### 1. 配置驗證

```python
# 在 Django shell 中執行
from library.config.dify_config_manager import get_ocr_function_config

config = get_ocr_function_config()

# 驗證配置
print(f"App Name: {config.app_name}")
print(f"API URL: {config.api_url}")
print(f"Timeout: {config.timeout}")
print(f"驗證結果: {config.validate()}")
```

### 2. 連線測試

```python
from library.dify_integration.ocr_function_client import create_ocr_function_client

client = create_ocr_function_client()
if client.test_connection():
    print("✅ OCR Function 連線成功")
else:
    print("❌ OCR Function 連線失敗")
```

### 3. 功能測試

```python
# 測試圖像分析
with open('test_image.png', 'rb') as f:
    image_data = f.read()

result = client.analyze_image(image_data)
print(f"分析結果: {result}")
```

---

## 📊 配置對照表

| 項目 | OCR Function | 其他 Assistant（參考）|
|------|--------------|---------------------|
| App Type Key | `ocr_function` | `rvt_guide`, `protocol_guide` |
| 環境變數前綴 | `DIFY_OCR_FUNCTION` | `DIFY_RVT_GUIDE` |
| 便利函數 | `get_ocr_function_config()` | `get_rvt_guide_config()` |
| Timeout | 90 秒 | 75 秒 |
| 主要用途 | 圖像識別、OCR | 知識庫查詢、AI 助手 |

---

## ⚠️ 注意事項

1. **API Key 安全性**：API Key 已在配置中，請勿在日誌或前端暴露
2. **Timeout 設定**：OCR 處理可能耗時較長，建議設定 90 秒
3. **圖像大小限制**：Dify 可能有圖像大小限制，需要在客戶端進行預處理
4. **錯誤處理**：需要處理圖像格式不支援、識別失敗等異常情況
5. **向後兼容**：現有的 `ai_ocr` 配置保持不變，新功能使用 `ocr_function`

---

## 🔗 相關文件

- **Dify 配置管理指南**: `/docs/ai-integration/dify-app-config-usage.md`
- **AI OCR 模組**: `/library/ai_ocr/`
- **Dify 整合模組**: `/library/dify_integration/`
- **配置管理器**: `/library/config/dify_config_manager.py`

---

## 🧪 步驟 4：測試程式規劃

### 4.1 建立測試檔案：`tests/test_dify_integration/test_ocr_function.py`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR Function API 測試腳本
測試完整的流程：圖片上傳 → Dify OCR 識別 → 結果解析

測試內容：
1. 配置管理器導入測試
2. OCR Function 配置驗證
3. API 連線測試
4. 圖片識別功能測試
"""

import sys
import os
import base64
from pathlib import Path

# 添加專案路徑
sys.path.insert(0, '/home/user/codes/ai-platform-web/')


def print_section(title: str):
    """列印測試區塊標題"""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print('='*60)


def test_import_ocr_function_config():
    """測試 1: 導入 OCR Function 配置"""
    print_section("測試 1: 導入 OCR Function 配置")
    
    try:
        from library.config.dify_config_manager import (
            DifyConfigManager,
            DifyAppConfig,
            get_ocr_function_config,
            get_ocr_function_config_dict,
            validate_all_dify_configs
        )
        print("✅ 成功導入 OCR Function 配置管理組件")
        return True
    except ImportError as e:
        print(f"❌ 導入失敗: {e}")
        return False


def test_ocr_function_config_validation():
    """測試 2: 驗證 OCR Function 配置"""
    print_section("測試 2: 驗證 OCR Function 配置")
    
    try:
        from library.config.dify_config_manager import get_ocr_function_config
        
        config = get_ocr_function_config()
        
        print(f"📋 配置資訊:")
        print(f"  App Name: {config.app_name}")
        print(f"  Workspace: {config.workspace}")
        print(f"  API URL: {config.api_url}")
        print(f"  API Key: {config.api_key[:15]}...")
        print(f"  Timeout: {config.timeout} 秒")
        print(f"  Response Mode: {config.response_mode}")
        print(f"  Features: {config.features}")
        
        # 驗證配置
        is_valid = config.validate()
        print(f"\n✅ 配置驗證結果: {'通過' if is_valid else '失敗'}")
        
        # 測試安全配置
        safe_config = config.get_safe_config()
        assert 'api_key' not in safe_config
        assert 'api_key_prefix' in safe_config
        print("✅ 安全配置功能正常（API Key 已隱藏）")
        
        return is_valid
    except Exception as e:
        print(f"❌ 配置驗證失敗: {e}")
        return False


def test_ocr_function_in_supported_apps():
    """測試 3: 確認 OCR Function 在支援的應用列表中"""
    print_section("測試 3: 確認 OCR Function 在支援的應用列表中")
    
    try:
        from library.config.dify_config_manager import DifyConfigManager
        
        manager = DifyConfigManager()
        supported_apps = manager.list_available_apps()
        
        print("📋 目前支援的應用:")
        for app_key, app_name in supported_apps.items():
            marker = "👉" if app_key == 'ocr_function' else "  "
            print(f"  {marker} {app_key}: {app_name}")
        
        if 'ocr_function' in supported_apps:
            print("\n✅ OCR Function 已在支援的應用列表中")
            return True
        else:
            print("\n❌ OCR Function 不在支援的應用列表中")
            return False
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False


def test_ocr_function_api_connection():
    """測試 4: OCR Function API 連線測試"""
    print_section("測試 4: OCR Function API 連線測試")
    
    try:
        from library.config.dify_config_manager import get_ocr_function_config
        import requests
        
        config = get_ocr_function_config()
        
        print(f"🔗 測試連線到: {config.api_url}")
        
        # 建立測試請求
        headers = {
            'Authorization': f'Bearer {config.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'inputs': {},
            'query': 'Hello, this is a connection test.',
            'response_mode': 'blocking',
            'user': 'test_user'
        }
        
        response = requests.post(
            config.api_url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"📊 HTTP 狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            answer = result.get('answer', 'No answer')
            print(f"📝 回應預覽: {answer[:100]}...")
            print("\n✅ API 連線成功")
            return True
        else:
            print(f"❌ API 請求失敗")
            print(f"錯誤內容: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ 連線超時")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ 連線錯誤: {e}")
        return False
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False


def test_ocr_function_image_recognition():
    """測試 5: OCR 圖片識別功能測試"""
    print_section("測試 5: OCR 圖片識別功能測試")
    
    try:
        from library.config.dify_config_manager import get_ocr_function_config
        import requests
        
        config = get_ocr_function_config()
        
        # 使用指定的測試圖片
        test_images = [
            '/home/user/codes/ai-platform-web/螢幕擷取畫面 2025-11-30 141051.jpg',  # 主要測試圖片
            '/home/user/codes/ai-platform-web/backend/edward.jpg',
            '/home/user/codes/ai-platform-web/tests/test_images/sample.png',
        ]
        
        test_image_path = None
        for img_path in test_images:
            if os.path.exists(img_path):
                test_image_path = img_path
                break
        
        # 方法 2: 如果沒有測試圖片，創建一個簡單的測試圖片
        if not test_image_path:
            print("⚠️ 找不到測試圖片，建立簡單測試圖片...")
            test_image_path = create_test_image()
        
        if not test_image_path or not os.path.exists(test_image_path):
            print("❌ 無法找到或建立測試圖片")
            print("💡 建議：請準備一張包含文字的測試圖片放在 tests/test_images/ 目錄下")
            return False
        
        print(f"📷 使用測試圖片: {test_image_path}")
        
        # 讀取圖片並轉換為 base64
        with open(test_image_path, 'rb') as f:
            image_data = f.read()
        
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        file_ext = Path(test_image_path).suffix.lower().replace('.', '')
        if file_ext == 'jpg':
            file_ext = 'jpeg'
        
        print(f"📊 圖片大小: {len(image_data) / 1024:.2f} KB")
        print(f"📊 圖片格式: {file_ext}")
        
        # 建立請求 - 使用 files 參數上傳圖片
        headers = {
            'Authorization': f'Bearer {config.api_key}',
        }
        
        # 方案 A: 使用 Dify Chat 的 files 格式
        # 先上傳檔案取得 file_id
        upload_url = config.base_url + '/v1/files/upload'
        files = {
            'file': (os.path.basename(test_image_path), image_data, f'image/{file_ext}')
        }
        upload_data = {
            'user': 'test_user'
        }
        
        print(f"\n📤 上傳圖片到: {upload_url}")
        upload_response = requests.post(
            upload_url,
            headers={'Authorization': f'Bearer {config.api_key}'},
            files=files,
            data=upload_data,
            timeout=60
        )
        
        if upload_response.status_code == 201 or upload_response.status_code == 200:
            upload_result = upload_response.json()
            file_id = upload_result.get('id')
            print(f"✅ 圖片上傳成功，File ID: {file_id}")
            
            # 使用 file_id 進行 OCR 識別
            chat_payload = {
                'inputs': {},
                'query': '請識別這張圖片中的所有文字內容，並以結構化的方式輸出',
                'response_mode': 'blocking',
                'user': 'test_user',
                'files': [
                    {
                        'type': 'image',
                        'transfer_method': 'local_file',
                        'upload_file_id': file_id
                    }
                ]
            }
            
            print(f"\n🔍 發送 OCR 識別請求...")
            response = requests.post(
                config.api_url,
                headers={
                    'Authorization': f'Bearer {config.api_key}',
                    'Content-Type': 'application/json'
                },
                json=chat_payload,
                timeout=config.timeout
            )
            
            print(f"📊 HTTP 狀態碼: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get('answer', 'No answer')
                
                print(f"\n📝 OCR 識別結果:")
                print("-" * 40)
                print(answer)
                print("-" * 40)
                
                print("\n✅ OCR 圖片識別測試成功")
                return {
                    'success': True,
                    'answer': answer,
                    'conversation_id': result.get('conversation_id'),
                    'message_id': result.get('message_id')
                }
            else:
                print(f"❌ OCR 識別失敗: {response.text[:300]}")
                return False
        else:
            print(f"❌ 圖片上傳失敗: {upload_response.status_code}")
            print(f"錯誤內容: {upload_response.text[:300]}")
            
            # 方案 B: 嘗試使用 base64 直接傳送
            print("\n🔄 嘗試使用 base64 方式...")
            return test_ocr_with_base64(config, image_base64, file_ext)
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ocr_with_base64(config, image_base64: str, file_ext: str):
    """使用 base64 方式測試 OCR"""
    import requests
    
    headers = {
        'Authorization': f'Bearer {config.api_key}',
        'Content-Type': 'application/json'
    }
    
    # 嘗試使用 remote_url 格式（data URL）
    payload = {
        'inputs': {},
        'query': '請識別這張圖片中的所有文字內容',
        'response_mode': 'blocking',
        'user': 'test_user',
        'files': [
            {
                'type': 'image',
                'transfer_method': 'remote_url',
                'url': f'data:image/{file_ext};base64,{image_base64}'
            }
        ]
    }
    
    response = requests.post(
        config.api_url,
        headers=headers,
        json=payload,
        timeout=config.timeout
    )
    
    if response.status_code == 200:
        result = response.json()
        answer = result.get('answer', 'No answer')
        print(f"\n📝 OCR 識別結果 (base64):")
        print("-" * 40)
        print(answer)
        print("-" * 40)
        print("\n✅ OCR 圖片識別測試成功 (base64 方式)")
        return True
    else:
        print(f"❌ base64 方式也失敗: {response.text[:300]}")
        return False


def create_test_image():
    """創建一個簡單的測試圖片（包含文字）"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # 建立測試圖片目錄
        test_dir = '/home/user/codes/ai-platform-web/tests/test_images'
        os.makedirs(test_dir, exist_ok=True)
        
        # 創建圖片
        img = Image.new('RGB', (400, 200), color='white')
        draw = ImageDraw.Draw(img)
        
        # 繪製測試文字
        text_lines = [
            "OCR Function Test",
            "測試中文識別",
            "Score: 12345",
            "Date: 2025-11-30"
        ]
        
        y_offset = 20
        for line in text_lines:
            draw.text((20, y_offset), line, fill='black')
            y_offset += 40
        
        # 保存圖片
        test_image_path = os.path.join(test_dir, 'ocr_test_image.png')
        img.save(test_image_path)
        print(f"✅ 已建立測試圖片: {test_image_path}")
        
        return test_image_path
    except ImportError:
        print("⚠️ PIL 未安裝，無法建立測試圖片")
        return None
    except Exception as e:
        print(f"⚠️ 建立測試圖片失敗: {e}")
        return None


def test_validate_all_configs():
    """測試 6: 驗證所有 Dify 配置"""
    print_section("測試 6: 驗證所有 Dify 配置")
    
    try:
        from library.config.dify_config_manager import validate_all_dify_configs
        
        results = validate_all_dify_configs()
        
        print("📋 所有配置驗證結果:")
        all_passed = True
        for app_type, is_valid in results.items():
            status = "✅" if is_valid else "❌"
            print(f"  {status} {app_type}")
            if not is_valid:
                all_passed = False
        
        if all_passed:
            print("\n✅ 所有配置驗證通過")
        else:
            print("\n⚠️ 部分配置驗證失敗")
        
        return all_passed
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False


def run_all_tests():
    """執行所有測試"""
    print("\n" + "="*60)
    print("🚀 OCR Function API 整合測試")
    print("="*60)
    print(f"📅 測試時間: {__import__('datetime').datetime.now()}")
    
    results = {}
    
    # 執行測試
    results['導入配置'] = test_import_ocr_function_config()
    results['配置驗證'] = test_ocr_function_config_validation()
    results['支援應用列表'] = test_ocr_function_in_supported_apps()
    results['API 連線'] = test_ocr_function_api_connection()
    results['圖片識別'] = test_ocr_function_image_recognition()
    results['全部配置驗證'] = test_validate_all_configs()
    
    # 輸出總結
    print("\n" + "="*60)
    print("📊 測試總結")
    print("="*60)
    
    passed = 0
    failed = 0
    for test_name, result in results.items():
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n📈 結果: {passed} 通過 / {failed} 失敗 / {len(results)} 總計")
    
    if failed == 0:
        print("\n🎉 所有測試通過！OCR Function API 整合成功！")
    else:
        print("\n⚠️ 部分測試失敗，請檢查上述錯誤訊息")
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
```

---

### 4.2 快速測試腳本：`tests/test_dify_integration/test_ocr_function_quick.py`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR Function 快速測試腳本
僅測試配置和連線，不測試圖片識別
"""

import sys
sys.path.insert(0, '/home/user/codes/ai-platform-web/')

def quick_test():
    """快速測試"""
    print("🚀 OCR Function 快速測試")
    print("="*50)
    
    # 1. 測試配置
    print("\n1️⃣ 測試配置...")
    try:
        from library.config.dify_config_manager import get_ocr_function_config
        config = get_ocr_function_config()
        print(f"   ✅ App Name: {config.app_name}")
        print(f"   ✅ API URL: {config.api_url}")
        print(f"   ✅ Timeout: {config.timeout}s")
    except Exception as e:
        print(f"   ❌ 配置失敗: {e}")
        return False
    
    # 2. 測試連線
    print("\n2️⃣ 測試 API 連線...")
    try:
        import requests
        headers = {
            'Authorization': f'Bearer {config.api_key}',
            'Content-Type': 'application/json'
        }
        payload = {
            'inputs': {},
            'query': 'Hello',
            'response_mode': 'blocking',
            'user': 'quick_test'
        }
        response = requests.post(
            config.api_url,
            headers=headers,
            json=payload,
            timeout=30
        )
        if response.status_code == 200:
            print(f"   ✅ 連線成功 (HTTP {response.status_code})")
        else:
            print(f"   ❌ 連線失敗 (HTTP {response.status_code})")
            return False
    except Exception as e:
        print(f"   ❌ 連線錯誤: {e}")
        return False
    
    print("\n✅ 快速測試完成！")
    return True


if __name__ == '__main__':
    success = quick_test()
    sys.exit(0 if success else 1)
```

---

### 4.3 測試圖片識別專用腳本：`tests/test_dify_integration/test_ocr_function_image.py`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR Function 圖片識別專用測試腳本
支援指定圖片路徑進行測試

使用方式：
    python test_ocr_function_image.py /path/to/image.png
    python test_ocr_function_image.py  # 使用預設測試圖片
"""

import sys
import os
import base64
import argparse
from pathlib import Path

sys.path.insert(0, '/home/user/codes/ai-platform-web/')


def test_image_ocr(image_path: str = None):
    """測試圖片 OCR 識別"""
    
    print("🖼️ OCR Function 圖片識別測試")
    print("="*50)
    
    # 確認圖片路徑
    if image_path is None:
        # 使用指定的測試圖片
        default_paths = [
            '/home/user/codes/ai-platform-web/螢幕擷取畫面 2025-11-30 141051.jpg',  # 主要測試圖片
            '/home/user/codes/ai-platform-web/backend/edward.jpg',
            '/home/user/codes/ai-platform-web/tests/test_images/ocr_test_image.png',
        ]
        for p in default_paths:
            if os.path.exists(p):
                image_path = p
                break
    
    if not image_path or not os.path.exists(image_path):
        print(f"❌ 找不到圖片: {image_path}")
        print("💡 使用方式: python test_ocr_function_image.py /path/to/image.png")
        return False
    
    print(f"📷 圖片路徑: {image_path}")
    
    # 讀取配置
    from library.config.dify_config_manager import get_ocr_function_config
    import requests
    
    config = get_ocr_function_config()
    
    # 讀取圖片
    with open(image_path, 'rb') as f:
        image_data = f.read()
    
    file_ext = Path(image_path).suffix.lower().replace('.', '')
    if file_ext == 'jpg':
        file_ext = 'jpeg'
    
    print(f"📊 圖片大小: {len(image_data) / 1024:.2f} KB")
    print(f"📊 圖片格式: {file_ext}")
    
    # 上傳圖片
    upload_url = config.base_url + '/v1/files/upload'
    files = {
        'file': (os.path.basename(image_path), image_data, f'image/{file_ext}')
    }
    
    print(f"\n📤 上傳圖片...")
    upload_response = requests.post(
        upload_url,
        headers={'Authorization': f'Bearer {config.api_key}'},
        files=files,
        data={'user': 'test_user'},
        timeout=60
    )
    
    if upload_response.status_code not in [200, 201]:
        print(f"❌ 上傳失敗: {upload_response.status_code}")
        print(upload_response.text)
        return False
    
    file_id = upload_response.json().get('id')
    print(f"✅ 上傳成功，File ID: {file_id}")
    
    # 發送 OCR 請求
    print(f"\n🔍 發送 OCR 識別請求...")
    chat_payload = {
        'inputs': {},
        'query': '請仔細識別這張圖片中的所有文字內容，包括中文和英文，並以清晰的格式輸出',
        'response_mode': 'blocking',
        'user': 'test_user',
        'files': [
            {
                'type': 'image',
                'transfer_method': 'local_file',
                'upload_file_id': file_id
            }
        ]
    }
    
    response = requests.post(
        config.api_url,
        headers={
            'Authorization': f'Bearer {config.api_key}',
            'Content-Type': 'application/json'
        },
        json=chat_payload,
        timeout=config.timeout
    )
    
    if response.status_code == 200:
        result = response.json()
        answer = result.get('answer', 'No answer')
        
        print(f"\n{'='*50}")
        print("📝 OCR 識別結果:")
        print('='*50)
        print(answer)
        print('='*50)
        
        print(f"\n📊 其他資訊:")
        print(f"   Conversation ID: {result.get('conversation_id')}")
        print(f"   Message ID: {result.get('message_id')}")
        
        print("\n✅ OCR 識別成功！")
        return True
    else:
        print(f"❌ OCR 識別失敗: {response.status_code}")
        print(response.text)
        return False


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='OCR Function 圖片識別測試')
    parser.add_argument('image_path', nargs='?', default=None, help='圖片路徑')
    args = parser.parse_args()
    
    success = test_image_ocr(args.image_path)
    sys.exit(0 if success else 1)
```

---

## 📁 測試檔案清單

| 檔案路徑 | 用途 | 說明 |
|---------|------|------|
| `tests/test_dify_integration/test_ocr_function.py` | 完整測試 | 包含所有測試項目 |
| `tests/test_dify_integration/test_ocr_function_quick.py` | 快速測試 | 僅測試配置和連線 |
| `tests/test_dify_integration/test_ocr_function_image.py` | 圖片測試 | 指定圖片進行 OCR 測試 |

---

## 🖼️ 測試圖片

### 主要測試圖片
| 項目 | 值 |
|------|-----|
| **檔案名稱** | `螢幕擷取畫面 2025-11-30 141051.jpg` |
| **本機路徑** | `/home/user/codes/ai-platform-web/螢幕擷取畫面 2025-11-30 141051.jpg` |
| **容器內路徑** | `/app/螢幕擷取畫面 2025-11-30 141051.jpg` |
| **用途** | OCR 文字識別功能驗證 |

### 備用測試圖片
- `/home/user/codes/ai-platform-web/backend/edward.jpg`
- `/home/user/codes/ai-platform-web/tests/test_images/ocr_test_image.png`（程式自動生成）

---

## 🚀 測試執行方式

### 方式 1: 在 Docker 容器內執行（推薦）

```bash
# 完整測試
docker exec ai-django python tests/test_dify_integration/test_ocr_function.py

# 快速測試
docker exec ai-django python tests/test_dify_integration/test_ocr_function_quick.py

# 指定圖片測試（使用指定的螢幕擷取畫面）
docker exec ai-django python tests/test_dify_integration/test_ocr_function_image.py "/app/螢幕擷取畫面 2025-11-30 141051.jpg"
```

### 方式 2: 在本機執行

```bash
# 確保在虛擬環境中
source /home/user/codes/ai-platform-web/venv/bin/activate

# 完整測試
python tests/test_dify_integration/test_ocr_function.py

# 快速測試
python tests/test_dify_integration/test_ocr_function_quick.py

# 指定圖片測試（使用指定的螢幕擷取畫面）
python tests/test_dify_integration/test_ocr_function_image.py "/home/user/codes/ai-platform-web/螢幕擷取畫面 2025-11-30 141051.jpg"
```

---

## 📅 執行時間線

| 階段 | 內容 | 預估時間 |
|------|------|---------|
| 階段 1 | 配置管理器更新 | 10 分鐘 |
| 階段 2 | 專用客戶端建立 | 20 分鐘 |
| 階段 3 | 現有模組整合 | 15 分鐘 |
| 階段 4 | 測試程式建立 | 20 分鐘 |
| 階段 5 | 執行測試驗證 | 15 分鐘 |
| **總計** | | **約 1.5 小時** |

---

**確認後請告知，我將開始執行上述步驟。**
