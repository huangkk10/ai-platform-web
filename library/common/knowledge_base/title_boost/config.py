"""
Title Boost Configuration
Title Boost 配置管理

從 DifyConfigVersion.rag_settings 中解析 Title Boost 配置。
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class TitleBoostConfig:
    """
    Title Boost 配置管理器
    
    負責從版本配置中解析 Title Boost 相關設定。
    """
    
    # 預設配置
    DEFAULT_CONFIG = {
        'enabled': False,           # 預設停用
        'title_match_bonus': 0.15,  # 加分值（15%）
        'min_keyword_length': 2,    # 最小關鍵詞長度
        'enable_progressive_bonus': False  # 漸進式加分
    }
    
    @classmethod
    def from_rag_settings(
        cls, 
        rag_settings: Dict[str, Any], 
        stage: int = 1
    ) -> Dict[str, Any]:
        """
        從 RAG 設置中解析 Title Boost 配置
        
        配置格式：
        {
            "retrieval_mode": "two_stage_with_title_boost",  # 包含 'title_boost' 則啟用
            "stage1": {
                "title_match_bonus": 15,  # 百分比
                "min_keyword_length": 2    # 可選
            },
            "stage2": {
                "title_match_bonus": 10,
                "min_keyword_length": 2
            }
        }
        
        Args:
            rag_settings: DifyConfigVersion.rag_settings
            stage: 搜尋階段 (1 或 2)
            
        Returns:
            Title Boost 配置字典
        
        Examples:
            >>> rag_settings = {
            ...     "stage1": {"title_match_bonus": 15},
            ...     "retrieval_mode": "two_stage_with_title_boost"
            ... }
            >>> config = TitleBoostConfig.from_rag_settings(rag_settings, stage=1)
            >>> config['enabled']
            True
            >>> config['title_match_bonus']
            0.15
        """
        try:
            # 檢查是否啟用 Title Boost（從 retrieval_mode 判斷）
            retrieval_mode = rag_settings.get('retrieval_mode', '')
            enabled = 'title_boost' in retrieval_mode.lower()
            
            if not enabled:
                logger.debug("Title Boost 未啟用（retrieval_mode 不包含 'title_boost'）")
                return cls.DEFAULT_CONFIG.copy()
            
            # 解析對應階段的配置
            stage_key = f'stage{stage}'
            stage_config = rag_settings.get(stage_key, {})
            
            if not stage_config:
                logger.warning(f"找不到 {stage_key} 配置，使用預設值")
                return cls.DEFAULT_CONFIG.copy()
            
            # 從百分比轉換為小數（15 → 0.15）
            title_match_bonus_pct = stage_config.get('title_match_bonus', 15)
            title_match_bonus = title_match_bonus_pct / 100.0
            
            # 其他配置
            min_keyword_length = stage_config.get('min_keyword_length', 2)
            enable_progressive_bonus = stage_config.get('enable_progressive_bonus', False)
            
            config = {
                'enabled': True,
                'title_match_bonus': title_match_bonus,
                'min_keyword_length': min_keyword_length,
                'enable_progressive_bonus': enable_progressive_bonus
            }
            
            logger.info(
                f"✅ Title Boost 配置已載入 (Stage {stage}): "
                f"bonus={title_match_bonus:.2%}, "
                f"min_length={min_keyword_length}"
            )
            
            return config
            
        except Exception as e:
            logger.error(f"解析 Title Boost 配置失敗: {str(e)}", exc_info=True)
            return cls.DEFAULT_CONFIG.copy()
    
    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> bool:
        """
        驗證配置是否有效
        
        Args:
            config: Title Boost 配置字典
            
        Returns:
            True 表示有效，False 表示無效
        """
        try:
            # 檢查必要欄位
            required_fields = ['enabled', 'title_match_bonus', 'min_keyword_length']
            for field in required_fields:
                if field not in config:
                    logger.error(f"配置缺少必要欄位: {field}")
                    return False
            
            # 檢查數值範圍
            bonus = config['title_match_bonus']
            if not (0.0 <= bonus <= 1.0):
                logger.error(f"title_match_bonus 超出範圍 [0.0, 1.0]: {bonus}")
                return False
            
            min_length = config['min_keyword_length']
            if not (1 <= min_length <= 10):
                logger.error(f"min_keyword_length 超出範圍 [1, 10]: {min_length}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"配置驗證失敗: {str(e)}")
            return False
    
    @classmethod
    def get_safe_config(cls, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        獲取安全的配置（驗證並修正異常值）
        
        Args:
            config: Title Boost 配置字典
            
        Returns:
            修正後的配置
        """
        safe_config = config.copy()
        
        # 修正 title_match_bonus
        bonus = safe_config.get('title_match_bonus', 0.15)
        safe_config['title_match_bonus'] = max(0.0, min(1.0, bonus))
        
        # 修正 min_keyword_length
        min_length = safe_config.get('min_keyword_length', 2)
        safe_config['min_keyword_length'] = max(1, min(10, min_length))
        
        # 確保 enabled 為布林值
        safe_config['enabled'] = bool(safe_config.get('enabled', False))
        
        return safe_config
