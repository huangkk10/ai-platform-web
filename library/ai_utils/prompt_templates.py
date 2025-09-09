"""
提示模板管理
"""


class PromptTemplates:
    """提示模板管理器"""
    
    TEMPLATES = {
        'summarize': "請總結以下內容：\n{content}",
        'translate': "請將以下內容翻譯成{language}：\n{content}",
    }
    
    @classmethod
    def get_template(cls, name: str) -> str:
        """獲取模板"""
        return cls.TEMPLATES.get(name, "")
    
    @classmethod
    def format_template(cls, name: str, **kwargs) -> str:
        """格式化模板"""
        template = cls.get_template(name)
        return template.format(**kwargs)