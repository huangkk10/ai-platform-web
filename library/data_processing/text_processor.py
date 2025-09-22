"""
文本處理器
"""
import re


def extract_project_name(message_text):
    """
    從訊息中提取 project name
    支援格式: 
    - project : Samsung
    - project: Samsung
    - Project : Samsung
    - PROJECT: Samsung
    - 專案：Samsung
    - 項目：Samsung
    
    Args:
        message_text (str): 輸入訊息文本
        
    Returns:
        str or None: 提取到的 project name，如果沒有找到則返回 None
    """
    if not message_text:
        return None
    
    # 定義多種可能的格式
    patterns = [
        r'project\s*:\s*([^\n\r]+)',  # project : Samsung
        r'Project\s*:\s*([^\n\r]+)',  # Project : Samsung  
        r'PROJECT\s*:\s*([^\n\r]+)',  # PROJECT : Samsung
        r'專案\s*[：:]\s*([^\n\r]+)',   # 專案：Samsung
        r'項目\s*[：:]\s*([^\n\r]+)',   # 項目：Samsung
    ]
    
    for pattern in patterns:
        match = re.search(pattern, message_text, re.IGNORECASE)
        if match:
            project_name = match.group(1).strip()
            # 移除可能的引號
            project_name = project_name.strip('"\'')
            if project_name:
                print(f"🔍 提取到 project name: '{project_name}'")
                return project_name
    
    print(f"ℹ️ 訊息中未找到 project name")
    return None


class TextProcessor:
    """文本處理器"""
    
    def __init__(self):
        pass
    
    def clean_text(self, text: str) -> str:
        """清理文本"""
        # TODO: 實現文本清理邏輯
        return text.strip()
    
    def split_text(self, text: str, max_length: int = 1000) -> list:
        """分割文本"""
        # TODO: 實現智能文本分割
        return [text[i:i+max_length] for i in range(0, len(text), max_length)]