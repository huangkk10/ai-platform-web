"""
動態 Threshold 載入器
用於 Dify v1.2.1+ 版本，從資料庫動態讀取 Threshold 設定
"""
import logging
from typing import Dict, Any, Optional
from decimal import Decimal

logger = logging.getLogger(__name__)


class DynamicThresholdLoader:
    """
    動態 Threshold 載入器
    
    功能：
    1. 檢查版本配置中的 use_dynamic_threshold 標記
    2. 從 SearchThresholdSetting 資料表讀取最新設定
    3. 合併動態設定（DB）+ 固定設定（版本）
    4. 支援快取機制（透過 ThresholdManager）
    5. 錯誤處理：DB 無設定時使用預設值
    """
    
    @staticmethod
    def load_stage_config(stage_config: Dict[str, Any], assistant_type: str = "protocol_assistant") -> Dict[str, Any]:
        """
        載入單階段配置
        
        Args:
            stage_config: 版本中定義的階段配置
            assistant_type: Assistant 類型（protocol_assistant, rvt_assistant）
        
        Returns:
            合併後的完整階段配置
        
        範例：
            stage_config = {
                "use_dynamic_threshold": True,
                "assistant_type": "protocol_assistant",
                "title_match_bonus": 15,
                "threshold": 0.80,  # 預設值（當 DB 無設定時使用）
                "title_weight": 95,
                "content_weight": 5,
            }
            
            result = load_stage_config(stage_config)
            # result 包含從 DB 讀取的最新 threshold/weight + 版本固定的 title_match_bonus
        """
        # 檢查是否啟用動態讀取
        if not stage_config.get('use_dynamic_threshold', False):
            logger.debug(f"📌 Stage 配置使用靜態設定")
            return stage_config  # 靜態配置，直接返回
        
        # 從 stage_config 中獲取 assistant_type（優先）
        assistant_type = stage_config.get('assistant_type', assistant_type)
        
        logger.info(f"🔄 動態載入 {assistant_type} 的 Threshold 設定")
        
        try:
            # 從 ThresholdManager 讀取（有快取）
            from library.common.threshold_manager import get_threshold_manager
            manager = get_threshold_manager()
            
            # 確保快取有效
            if not manager._is_cache_valid():
                manager._refresh_cache()
            
            # 判斷是第一階段還是第二階段（根據是否有 stage1_ 前綴）
            # 如果原始 config 中有任何 stage1_ 開頭的 key，則為第一階段
            is_stage1 = any(k.startswith('stage1_') for k in stage_config.keys())
            stage_prefix = 'stage1_' if is_stage1 else 'stage2_'
            stage_num = 1 if is_stage1 else 2
            
            # 從快取中獲取 DB 設定
            db_settings = manager._cache.get(assistant_type, {})
            
            # 從 DB 設定中提取對應階段的值
            threshold_key = f'{stage_prefix}threshold'
            title_weight_key = f'{stage_prefix}title_weight'
            content_weight_key = f'{stage_prefix}content_weight'
            
            # 合併配置
            merged_config = {
                # 🔄 動態（從 DB）
                "threshold": float(db_settings.get(threshold_key, stage_config.get('threshold', 0.80))),
                "title_weight": int(db_settings.get(title_weight_key, stage_config.get('title_weight', 95))),
                "content_weight": int(db_settings.get(content_weight_key, stage_config.get('content_weight', 5))),
                
                # 📌 固定（從版本）
                "title_match_bonus": stage_config.get('title_match_bonus', 0),
                "min_keyword_length": stage_config.get('min_keyword_length', 2),
                "top_k": stage_config.get('top_k', 20),
                
                # 元數據
                "use_dynamic_threshold": True,
                "loaded_from_db": bool(db_settings),
                "assistant_type": assistant_type,
                "stage": f"stage{stage_num}",
            }
            
            logger.info(
                f"✅ 動態載入成功: Threshold={merged_config['threshold']}, "
                f"Title={merged_config['title_weight']}%, Content={merged_config['content_weight']}%"
            )
            
            return merged_config
            
        except Exception as e:
            logger.error(f"❌ 動態載入失敗: {str(e)}, 使用預設值")
            
            # Fallback: 使用版本中的預設值
            fallback_config = {
                "threshold": stage_config.get('threshold', 0.80),
                "title_weight": stage_config.get('title_weight', 95),
                "content_weight": stage_config.get('content_weight', 5),
                "title_match_bonus": stage_config.get('title_match_bonus', 0),
                "min_keyword_length": stage_config.get('min_keyword_length', 2),
                "top_k": stage_config.get('top_k', 20),
                "use_dynamic_threshold": True,
                "loaded_from_db": False,
                "error": str(e),
            }
            
            return fallback_config
    
    @staticmethod
    def load_full_rag_settings(rag_settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        載入完整 RAG 設定（兩階段）
        
        Args:
            rag_settings: 版本中定義的完整 RAG 設定
        
        Returns:
            動態載入後的完整 RAG 設定
        
        範例：
            rag_settings = {
                "assistant_type": "protocol_assistant",
                "stage1": {
                    "use_dynamic_threshold": True,
                    "title_match_bonus": 15,
                    "threshold": 0.80,  # 預設值
                },
                "stage2": {
                    "use_dynamic_threshold": True,
                    "title_match_bonus": 10,
                },
                "retrieval_mode": "two_stage_with_title_boost",
            }
            
            result = load_full_rag_settings(rag_settings)
            # result['stage1'] 和 result['stage2'] 都包含從 DB 讀取的最新設定
        """
        assistant_type = rag_settings.get('assistant_type', 'protocol_assistant')
        
        logger.info(f"🔄 載入完整 RAG 設定: {assistant_type}")
        
        # 載入兩階段配置
        stage1_config = DynamicThresholdLoader.load_stage_config(
            rag_settings.get('stage1', {}), 
            assistant_type
        )
        
        stage2_config = DynamicThresholdLoader.load_stage_config(
            rag_settings.get('stage2', {}), 
            assistant_type
        )
        
        # 合併完整設定
        full_settings = {
            "stage1": stage1_config,
            "stage2": stage2_config,
            "retrieval_mode": rag_settings.get('retrieval_mode', 'two_stage'),
            "use_backend_search": rag_settings.get('use_backend_search', True),
            "search_service": rag_settings.get('search_service', 'ProtocolGuideSearchService'),
            "assistant_type": assistant_type,
        }
        
        logger.info(
            f"✅ 完整 RAG 設定載入完成\n"
            f"  Stage1: {stage1_config.get('threshold')} / {stage1_config.get('title_weight')}% / {stage1_config.get('content_weight')}%\n"
            f"  Stage2: {stage2_config.get('threshold')} / {stage2_config.get('title_weight')}% / {stage2_config.get('content_weight')}%\n"
            f"  Mode: {full_settings['retrieval_mode']}"
        )
        
        return full_settings
    
    @staticmethod
    def is_dynamic_version(rag_settings: Dict[str, Any]) -> bool:
        """
        檢查版本是否為動態版本
        
        Args:
            rag_settings: RAG 設定
        
        Returns:
            True: 動態版本（至少一個階段啟用動態載入）
            False: 靜態版本
        """
        stage1_dynamic = rag_settings.get('stage1', {}).get('use_dynamic_threshold', False)
        stage2_dynamic = rag_settings.get('stage2', {}).get('use_dynamic_threshold', False)
        
        return stage1_dynamic or stage2_dynamic


# 便利函數
def load_dynamic_config(rag_settings: Dict[str, Any]) -> Dict[str, Any]:
    """
    便利函數：載入動態配置
    
    如果版本是動態版本，則載入最新配置；否則返回原始配置
    """
    if DynamicThresholdLoader.is_dynamic_version(rag_settings):
        return DynamicThresholdLoader.load_full_rag_settings(rag_settings)
    else:
        return rag_settings
