"""
LLM 客戶端
提供大語言模型調用功能
"""


class LLMClient:
    """大語言模型客戶端"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
    
    def chat_completion(self, messages: list, model: str = "gpt-3.5-turbo"):
        """聊天完成"""
        # TODO: 實現 LLM 調用邏輯
        pass