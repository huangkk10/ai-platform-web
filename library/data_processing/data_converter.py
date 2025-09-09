"""
數據轉換器
"""

import json
from typing import Dict, Any


class DataConverter:
    """數據轉換器"""
    
    def __init__(self):
        pass
    
    def dict_to_json(self, data: Dict[str, Any]) -> str:
        """字典轉JSON"""
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    def json_to_dict(self, json_str: str) -> Dict[str, Any]:
        """JSON轉字典"""
        return json.loads(json_str)