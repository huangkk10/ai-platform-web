"""
Library 使用示例
展示如何在 Django backend 中使用 library 模組
"""

import sys
import os

# 添加 library 路徑到 Python path（如果需要）
# library_path = os.path.join(os.path.dirname(__file__), '..', 'library')
# sys.path.insert(0, library_path)

# 在 Docker 容器中，library 已經通過 volume 掛載到 /app/library
# 所以可以直接 import

from library.dify_integration import DifyClient, DatasetManager, DocumentManager
from library.config import DifyConfig, DatabaseConfig, AppConfig
from library.ai_utils import LLMClient, EmbeddingUtils, PromptTemplates
from library.data_processing import FileParser, TextProcessor, DataConverter


def example_usage():
    """示例用法"""
    
    # 1. 配置管理
    dify_config = DifyConfig(api_key="your-api-key")
    db_config = DatabaseConfig()
    app_config = AppConfig()
    
    print("Database URL:", db_config.get_database_url())
    print("Debug mode:", app_config.is_debug())
    
    # 2. Dify API 使用
    client = DifyClient(
        api_key=dify_config.api_key,
        base_url=dify_config.get('base_url')
    )
    
    dataset_manager = DatasetManager(client)
    document_manager = DocumentManager(client)
    
    # 創建知識庫
    try:
        dataset = dataset_manager.create_dataset(
            name="測試知識庫",
            description="這是一個測試知識庫",
            permission="only_me"
        )
        print("Created dataset:", dataset)
        
        # 添加文檔
        doc = document_manager.create_document_by_text(
            dataset_id=dataset['id'],
            name="測試文檔",
            text="這是測試內容"
        )
        print("Created document:", doc)
        
    except Exception as e:
        print("Error:", str(e))
    
    # 3. 數據處理
    text_processor = TextProcessor()
    data_converter = DataConverter()
    
    sample_text = "這是一段需要處理的文本內容。"
    cleaned_text = text_processor.clean_text(sample_text)
    split_texts = text_processor.split_text(sample_text, max_length=10)
    
    print("Cleaned text:", cleaned_text)
    print("Split texts:", split_texts)
    
    # 4. AI 工具
    prompt_template = PromptTemplates.format_template(
        'summarize',
        content="這是需要總結的內容"
    )
    print("Prompt template:", prompt_template)


if __name__ == "__main__":
    example_usage()