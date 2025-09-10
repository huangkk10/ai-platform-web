"""
Library 使用範例
展示如何在 Django backend 中使用 library 模組
"""

import sys
import os

# 添加 library 路徑到 Python path
sys.path.append('/app/library')

# 導入 library 模組
from dify_integration import DifyClient, DatasetManager, DocumentManager
from config import DifyConfig, DatabaseConfig, AppConfig
from ai_utils import PromptTemplates
from data_processing import TextProcessor, DataConverter


def test_dify_integration():
    """測試 Dify 整合功能"""
    print("=== 測試 Dify 整合 ===")
    
    # 使用配置管理器
    config = DifyConfig(api_key="dataset-your-api-key-here")
    
    # 創建客戶端
    client = DifyClient(config.api_key, config.get('base_url'))
    
    # 創建管理器
    dataset_manager = DatasetManager(client)
    document_manager = DocumentManager(client)
    
    print("✅ Dify 模組導入成功")
    return True


def test_config_modules():
    """測試配置模組"""
    print("\n=== 測試配置模組 ===")
    
    # 測試 Dify 配置
    dify_config = DifyConfig()
    print(f"Dify Base URL: {dify_config.get('base_url')}")
    
    # 測試資料庫配置
    db_config = DatabaseConfig()
    print(f"Database URL: {db_config.get_database_url()}")
    
    # 測試應用程式配置
    app_config = AppConfig()
    print(f"Debug Mode: {app_config.is_debug()}")
    
    print("✅ 配置模組測試成功")
    return True


def test_ai_utils():
    """測試 AI 工具模組"""
    print("\n=== 測試 AI 工具模組 ===")
    
    # 測試提示模板
    template = PromptTemplates.format_template(
        'summarize', 
        content="這是一段需要總結的文字內容。"
    )
    print(f"生成的提示: {template}")
    
    print("✅ AI 工具模組測試成功")
    return True


def test_data_processing():
    """測試數據處理模組"""
    print("\n=== 測試數據處理模組 ===")
    
    # 測試文本處理器
    processor = TextProcessor()
    cleaned_text = processor.clean_text("  這是一段需要清理的文字  ")
    print(f"清理後的文字: '{cleaned_text}'")
    
    # 測試數據轉換器
    converter = DataConverter()
    test_data = {"name": "測試", "value": 123}
    json_str = converter.dict_to_json(test_data)
    print(f"轉換為 JSON: {json_str}")
    
    print("✅ 數據處理模組測試成功")
    return True


def main():
    """主函數"""
    print("🚀 開始測試 Library 模組...")
    
    try:
        # 執行各項測試
        test_dify_integration()
        test_config_modules()
        test_ai_utils()
        test_data_processing()
        
        print("\n🎉 所有測試通過！Library 模組可以正常使用。")
        return True
        
    except ImportError as e:
        print(f"❌ 導入錯誤: {e}")
        return False
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False


if __name__ == "__main__":
    main()