"""
智能搜尋配置管理（Smart Search Configuration）

統一管理智能搜尋路由器的配置參數，
包含模式 A、模式 B 的 TOP_K 和閾值設定。

Author: AI Platform Team
Date: 2025-11-11
"""

import logging
from typing import Dict, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class SmartSearchConfig:
    """
    智能搜尋配置類
    
    管理兩種搜尋模式的配置參數：
    - 模式 A：關鍵字優先全文搜尋
    - 模式 B：標準兩階段搜尋
    """
    
    # ===== 模式 A 配置（關鍵字優先全文搜尋）=====
    mode_a_top_k: int = 3
    """模式 A：返回前 K 個全文文檔（預設：3）"""
    
    mode_a_threshold: float = 0.5
    """模式 A：相似度閾值（預設：0.5）"""
    
    # ===== 模式 B 配置（兩階段搜尋）=====
    mode_b_stage_1_top_k: int = 5
    """模式 B 階段 1：返回前 K 個段落（預設：5）"""
    
    mode_b_stage_1_threshold: float = 0.5
    """模式 B 階段 1：相似度閾值（預設：0.5）"""
    
    mode_b_stage_2_top_k: int = 3
    """模式 B 階段 2：返回前 K 個全文文檔（預設：3）"""
    
    mode_b_stage_2_threshold: float = 0.5
    """模式 B 階段 2：相似度閾值（預設：0.5）"""
    
    # ===== 不確定性檢測配置 =====
    uncertainty_strict_mode: bool = False
    """不確定性檢測嚴格模式（預設：False）"""
    
    min_response_length: int = 20
    """AI 回答最小長度，低於此長度視為不確定（預設：20）"""
    
    # ===== Dify 請求配置 =====
    dify_timeout: int = 75
    """Dify API 超時時間（秒，預設：75）"""
    
    dify_verbose: bool = False
    """Dify 客戶端是否顯示詳細日誌（預設：False）"""
    
    # ===== 日誌配置 =====
    enable_detailed_logging: bool = True
    """是否啟用詳細日誌（預設：True）"""
    
    def to_dict(self) -> Dict[str, Any]:
        """
        轉換為字典格式
        
        Returns:
            Dict: 配置字典
        """
        return {
            'mode_a': {
                'top_k': self.mode_a_top_k,
                'threshold': self.mode_a_threshold,
            },
            'mode_b': {
                'stage_1': {
                    'top_k': self.mode_b_stage_1_top_k,
                    'threshold': self.mode_b_stage_1_threshold,
                },
                'stage_2': {
                    'top_k': self.mode_b_stage_2_top_k,
                    'threshold': self.mode_b_stage_2_threshold,
                }
            },
            'uncertainty': {
                'strict_mode': self.uncertainty_strict_mode,
                'min_response_length': self.min_response_length,
            },
            'dify': {
                'timeout': self.dify_timeout,
                'verbose': self.dify_verbose,
            },
            'logging': {
                'enable_detailed_logging': self.enable_detailed_logging,
            }
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'SmartSearchConfig':
        """
        從字典創建配置實例
        
        Args:
            config_dict: 配置字典
            
        Returns:
            SmartSearchConfig: 配置實例
        """
        return cls(
            # 模式 A
            mode_a_top_k=config_dict.get('mode_a', {}).get('top_k', 3),
            mode_a_threshold=config_dict.get('mode_a', {}).get('threshold', 0.5),
            
            # 模式 B 階段 1
            mode_b_stage_1_top_k=config_dict.get('mode_b', {}).get('stage_1', {}).get('top_k', 5),
            mode_b_stage_1_threshold=config_dict.get('mode_b', {}).get('stage_1', {}).get('threshold', 0.5),
            
            # 模式 B 階段 2
            mode_b_stage_2_top_k=config_dict.get('mode_b', {}).get('stage_2', {}).get('top_k', 3),
            mode_b_stage_2_threshold=config_dict.get('mode_b', {}).get('stage_2', {}).get('threshold', 0.5),
            
            # 不確定性檢測
            uncertainty_strict_mode=config_dict.get('uncertainty', {}).get('strict_mode', False),
            min_response_length=config_dict.get('uncertainty', {}).get('min_response_length', 20),
            
            # Dify
            dify_timeout=config_dict.get('dify', {}).get('timeout', 75),
            dify_verbose=config_dict.get('dify', {}).get('verbose', False),
            
            # 日誌
            enable_detailed_logging=config_dict.get('logging', {}).get('enable_detailed_logging', True),
        )
    
    def validate(self) -> bool:
        """
        驗證配置是否合法
        
        Returns:
            bool: True 表示合法，False 表示不合法
        """
        try:
            # 驗證 TOP_K
            assert self.mode_a_top_k > 0, "mode_a_top_k 必須 > 0"
            assert self.mode_b_stage_1_top_k > 0, "mode_b_stage_1_top_k 必須 > 0"
            assert self.mode_b_stage_2_top_k > 0, "mode_b_stage_2_top_k 必須 > 0"
            
            # 驗證閾值
            assert 0 <= self.mode_a_threshold <= 1, "mode_a_threshold 必須在 [0, 1] 範圍"
            assert 0 <= self.mode_b_stage_1_threshold <= 1, "mode_b_stage_1_threshold 必須在 [0, 1] 範圍"
            assert 0 <= self.mode_b_stage_2_threshold <= 1, "mode_b_stage_2_threshold 必須在 [0, 1] 範圍"
            
            # 驗證最小回答長度
            assert self.min_response_length > 0, "min_response_length 必須 > 0"
            
            # 驗證超時時間
            assert self.dify_timeout > 0, "dify_timeout 必須 > 0"
            
            return True
        
        except AssertionError as e:
            logger.error(f"❌ 配置驗證失敗: {str(e)}")
            return False
    
    def __str__(self) -> str:
        """字串表示"""
        return (
            f"SmartSearchConfig(\n"
            f"  模式 A: top_k={self.mode_a_top_k}, threshold={self.mode_a_threshold}\n"
            f"  模式 B 階段 1: top_k={self.mode_b_stage_1_top_k}, threshold={self.mode_b_stage_1_threshold}\n"
            f"  模式 B 階段 2: top_k={self.mode_b_stage_2_top_k}, threshold={self.mode_b_stage_2_threshold}\n"
            f"  不確定性: strict_mode={self.uncertainty_strict_mode}, min_length={self.min_response_length}\n"
            f"  Dify: timeout={self.dify_timeout}s, verbose={self.dify_verbose}\n"
            f")"
        )


# ===== 全局預設配置 =====

DEFAULT_CONFIG = SmartSearchConfig()


def get_default_config() -> SmartSearchConfig:
    """
    獲取預設配置
    
    Returns:
        SmartSearchConfig: 預設配置實例
    """
    return DEFAULT_CONFIG


def create_custom_config(**kwargs) -> SmartSearchConfig:
    """
    創建自定義配置
    
    Args:
        **kwargs: 配置參數
        
    Returns:
        SmartSearchConfig: 自定義配置實例
        
    Examples:
        >>> config = create_custom_config(mode_a_top_k=5, mode_b_stage_1_top_k=10)
        >>> print(config.mode_a_top_k)  # 5
    """
    return SmartSearchConfig(**kwargs)


# ===== 測試函數 =====

def test_config():
    """測試配置類"""
    print("\n===== 智能搜尋配置測試 =====\n")
    
    # 測試 1：預設配置
    print("測試 1: 預設配置")
    default_config = get_default_config()
    print(default_config)
    assert default_config.validate(), "預設配置驗證失敗"
    print("✅ 預設配置驗證通過\n")
    
    # 測試 2：自定義配置
    print("測試 2: 自定義配置")
    custom_config = create_custom_config(
        mode_a_top_k=5,
        mode_b_stage_1_top_k=10,
        dify_timeout=120
    )
    print(custom_config)
    assert custom_config.validate(), "自定義配置驗證失敗"
    print("✅ 自定義配置驗證通過\n")
    
    # 測試 3：to_dict 和 from_dict
    print("測試 3: 字典轉換")
    config_dict = custom_config.to_dict()
    print(f"配置字典: {config_dict}")
    restored_config = SmartSearchConfig.from_dict(config_dict)
    assert restored_config.mode_a_top_k == 5, "from_dict 失敗"
    assert restored_config.dify_timeout == 120, "from_dict 失敗"
    print("✅ 字典轉換測試通過\n")
    
    # 測試 4：配置驗證（非法值）
    print("測試 4: 配置驗證（非法值）")
    try:
        invalid_config = SmartSearchConfig(mode_a_threshold=1.5)  # 超出範圍
        if not invalid_config.validate():
            print("✅ 非法配置正確被檢測\n")
    except Exception:
        print("✅ 非法配置正確被拋出異常\n")
    
    print("===== 所有配置測試通過 =====\n")


if __name__ == '__main__':
    test_config()
