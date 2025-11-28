"""
VSA 搜尋算分過程日誌記錄器
===========================

專門記錄 Hybrid Search + Title Boost 版本的算分細節，
讓用戶可以在「系統日誌查看器」中查看完整的算分過程。

用途：
- 記錄一階搜尋（向量搜尋、關鍵字搜尋、RRF 融合）
- 記錄二階搜尋（文件搜尋）
- 記錄 Title Boost 加分過程
- 提供算分透明度，便於調試和優化

日誌位置：/app/logs/vsa_scoring.log

使用方式：
```python
from library.dify_knowledge.scoring_logger import VSAScoringLogger

# 創建日誌記錄器
scoring_logger = VSAScoringLogger(
    query="crystaldiskmark sop",
    version_name="Dify 二階搜尋 v1.2.2 (Hybrid Search + Title Boost)",
    conversation_id="conv_123"
)

# 記錄搜尋過程
scoring_logger.log_search_start()
scoring_logger.log_stage1_start(search_mode='auto', top_k=3, threshold=0.8)
# ... 其他記錄方法
scoring_logger.log_search_end(total_results=8)
```
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

# 取得專用 logger（對應 settings.py 中的 vsa_scoring logger）
scoring_logger = logging.getLogger('vsa_scoring')


class VSAScoringLogger:
    """
    VSA 算分過程記錄器
    
    負責記錄 Hybrid Search + Title Boost 版本的詳細算分過程，
    包括一階搜尋、二階搜尋、RRF 融合、Title Boost 等各階段。
    """
    
    def __init__(self, query: str, version_name: str, conversation_id: str = None):
        """
        初始化算分記錄器
        
        Args:
            query: 用戶搜尋查詢
            version_name: VSA 版本名稱（例如 "Dify 二階搜尋 v1.2.2"）
            conversation_id: 對話 ID（可選）
        """
        self.query = query
        self.version_name = version_name
        self.conversation_id = conversation_id or 'N/A'
        self.start_time = datetime.now()
        self.session_id = self.start_time.strftime('%Y%m%d_%H%M%S_%f')[:20]  # 精確到毫秒
        
        # 用於追蹤各階段數據
        self._stage1_data = {}
        self._stage2_data = {}
    
    # ============================================================
    # 搜尋開始/結束
    # ============================================================
    
    def log_search_start(self):
        """記錄搜尋開始"""
        scoring_logger.info("=" * 80)
        scoring_logger.info(f"🔍 [Session: {self.session_id}] VSA 搜尋開始")
        scoring_logger.info(f"   📋 版本: {self.version_name}")
        scoring_logger.info(f"   🔎 查詢: {self.query}")
        scoring_logger.info(f"   💬 對話ID: {self.conversation_id}")
        scoring_logger.info(f"   ⏱️  時間: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        scoring_logger.info("-" * 80)
    
    def log_search_end(self, total_results: int, stage1_count: int = 0, stage2_count: int = 0):
        """
        記錄搜尋結束
        
        Args:
            total_results: 最終返回的結果數量
            stage1_count: 一階搜尋結果數量
            stage2_count: 二階搜尋結果數量
        """
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        scoring_logger.info("-" * 80)
        scoring_logger.info(f"✅ [Session: {self.session_id}] VSA 搜尋完成")
        scoring_logger.info(f"   📊 一階結果: {stage1_count} 筆")
        scoring_logger.info(f"   📄 二階結果: {stage2_count} 筆")
        scoring_logger.info(f"   🎯 最終返回: {total_results} 筆")
        scoring_logger.info(f"   ⏱️  總耗時: {duration:.3f} 秒")
        scoring_logger.info("=" * 80)
        scoring_logger.info("")  # 空行分隔不同的搜尋 session
    
    # ============================================================
    # Stage 1: 一階搜尋（段落搜尋）
    # ============================================================
    
    def log_stage1_start(self, search_mode: str, top_k: int, threshold: float, 
                         use_hybrid: bool = False, rrf_k: int = 60):
        """
        記錄一階搜尋開始
        
        Args:
            search_mode: 搜尋模式（auto, section_only, document_only）
            top_k: 返回結果數量
            threshold: 相似度閾值
            use_hybrid: 是否使用混合搜尋
            rrf_k: RRF 常數（僅混合搜尋時有效）
        """
        scoring_logger.info(f"📌 [Stage 1] 一階搜尋開始")
        scoring_logger.info(f"   搜尋模式: {search_mode}")
        scoring_logger.info(f"   Top K: {top_k}")
        scoring_logger.info(f"   閾值: {threshold}")
        scoring_logger.info(f"   混合搜尋: {'✅ 啟用' if use_hybrid else '❌ 未啟用'}")
        if use_hybrid:
            scoring_logger.info(f"   RRF k 值: {rrf_k}")
        
        self._stage1_data = {
            'search_mode': search_mode,
            'top_k': top_k,
            'threshold': threshold,
            'use_hybrid': use_hybrid,
            'rrf_k': rrf_k
        }
    
    def log_stage1_vector_search(self, results: List[Dict], count: int = None):
        """
        記錄一階向量搜尋結果
        
        Args:
            results: 向量搜尋結果列表
            count: 結果數量（如果不提供，使用 len(results)）
        """
        result_count = count if count is not None else len(results)
        scoring_logger.info(f"   🔷 [向量搜尋] 找到 {result_count} 筆結果")
        
        # 記錄前 5 筆結果的詳細資訊
        for i, r in enumerate(results[:5], 1):
            title = r.get('title', r.get('metadata', {}).get('document_title', 'N/A'))[:50]
            score = r.get('score', r.get('similarity_score', 0))
            scoring_logger.info(f"      {i}. {title}... | 原始分數: {score:.4f}")
        
        if result_count > 5:
            scoring_logger.info(f"      ... 還有 {result_count - 5} 筆結果")
    
    def log_stage1_keyword_search(self, results: List[Dict], count: int = None, keywords: List[str] = None):
        """
        記錄一階關鍵字搜尋結果（v1.2.3 更新：支援 OR 邏輯統計）
        
        Args:
            results: 關鍵字搜尋結果列表
            count: 結果數量
            keywords: 搜尋的關鍵字列表（用於顯示匹配統計）
        """
        result_count = count if count is not None else len(results)
        
        # 計算全匹配、部分匹配統計
        if keywords and len(keywords) > 1:
            full_match = sum(1 for r in results if r.get('match_count', 0) == len(keywords))
            partial_match = result_count - full_match
            scoring_logger.info(
                f"   🔶 [關鍵字搜尋] 找到 {result_count} 筆結果 "
                f"(關鍵字: {keywords}, 全匹配: {full_match}, 部分匹配: {partial_match})"
            )
        else:
            scoring_logger.info(f"   🔶 [關鍵字搜尋] 找到 {result_count} 筆結果")
        
        for i, r in enumerate(results[:5], 1):
            title = r.get('title', 'N/A')[:50]
            rank = r.get('rank', 0)
            match_count = r.get('match_count')
            matched_kw = r.get('matched_keywords', [])
            
            # 如果有 match_count 資訊，顯示匹配詳情
            if match_count is not None and keywords:
                scoring_logger.info(
                    f"      {i}. {title}... | "
                    f"匹配: {match_count}/{len(keywords)} | "
                    f"分數: {rank:.4f} | "
                    f"關鍵字: {matched_kw}"
                )
            else:
                scoring_logger.info(f"      {i}. {title}... | 排名分數: {rank:.4f}")
        
        if result_count > 5:
            scoring_logger.info(f"      ... 還有 {result_count - 5} 筆結果")
    
    def log_stage1_rrf_fusion(self, results: List[Dict], rrf_k: int = 60):
        """
        記錄 RRF 融合結果
        
        Args:
            results: RRF 融合後的結果列表
            rrf_k: RRF 常數
        """
        scoring_logger.info(f"   🔄 [RRF 融合] k={rrf_k}, 融合後 {len(results)} 筆結果")
        
        for i, r in enumerate(results[:5], 1):
            title = r.get('title', 'N/A')[:40]
            rrf_score = r.get('rrf_score', 0)
            vector_rank = r.get('vector_rank', 'N/A')
            keyword_rank = r.get('keyword_rank', 'N/A')
            
            scoring_logger.info(
                f"      {i}. {title}... | "
                f"RRF分數: {rrf_score:.4f} | "
                f"向量排名: {vector_rank} | "
                f"關鍵字排名: {keyword_rank}"
            )
        
        if len(results) > 5:
            scoring_logger.info(f"      ... 還有 {len(results) - 5} 筆結果")
    
    def log_stage1_score_normalization(self, min_score: float, max_score: float, 
                                        target_range: str = "0.5-1.0"):
        """
        記錄分數正規化過程
        
        Args:
            min_score: 原始最低分
            max_score: 原始最高分
            target_range: 目標分數範圍
        """
        scoring_logger.info(
            f"   📊 [分數正規化] 原始範圍 [{min_score:.4f}, {max_score:.4f}] → "
            f"目標範圍 [{target_range}]"
        )
    
    def log_stage1_title_boost(self, results: List[Dict], boost_factor: float = 0.15):
        """
        記錄 Title Boost 調整過程
        
        Args:
            results: 應用 Title Boost 後的結果列表
            boost_factor: 標題加分係數（例如 0.15 = 15%）
        """
        boosted_count = sum(1 for r in results if r.get('title_boost_applied', False))
        scoring_logger.info(f"   ⬆️  [Title Boost] 加成係數: {boost_factor:.0%}, {boosted_count} 筆獲得加分")
        
        # 列出所有獲得加分的文件
        if boosted_count > 0:
            scoring_logger.info(f"      📋 獲得加分的文件:")
            for r in results:
                if r.get('title_boost_applied', False):
                    doc_title = r.get('document_title', r.get('metadata', {}).get('document_title', 'N/A'))
                    section_title = r.get('title', 'N/A')
                    source_id = r.get('source_id', r.get('metadata', {}).get('source_id', 'N/A'))
                    original_score = r.get('original_score', r.get('score', 0))
                    final_score = r.get('final_score', r.get('score', 0))
                    boost_amount = final_score - original_score
                    scoring_logger.info(
                        f"         ⬆️ ID:{source_id} | 文件: {doc_title[:50]} | "
                        f"段落: {section_title[:30]}... | "
                        f"+{boost_amount:.4f} ({original_score:.4f}→{final_score:.4f})"
                    )
        
        scoring_logger.info(f"      📊 Title Boost 後排名:")
        for i, r in enumerate(results[:5], 1):
            title = r.get('title', 'N/A')[:40]
            doc_title = r.get('document_title', r.get('metadata', {}).get('document_title', ''))
            original_score = r.get('original_score', r.get('score', 0))
            final_score = r.get('final_score', r.get('score', 0))
            is_boosted = r.get('title_boost_applied', False)
            boost_marker = "⬆️ " if is_boosted else "   "
            
            # 如果有文件標題，顯示文件標題
            doc_info = f" [文件:{doc_title[:25]}]" if doc_title else ""
            
            scoring_logger.info(
                f"      {i}. {boost_marker}{title}...{doc_info} | "
                f"原始: {original_score:.4f} → 最終: {final_score:.4f}"
            )
        
        if len(results) > 5:
            scoring_logger.info(f"      ... 還有 {len(results) - 5} 筆結果")
    
    def log_stage1_result(self, results: List[Dict]):
        """
        記錄一階搜尋最終結果
        
        Args:
            results: 一階搜尋最終結果列表
        """
        scoring_logger.info(f"   📊 [Stage 1 最終結果] 共 {len(results)} 筆")
        
        for i, r in enumerate(results, 1):
            source_id = r.get('source_id', r.get('metadata', {}).get('source_id', 'N/A'))
            title = r.get('title', 'N/A')[:40]
            score = r.get('final_score', r.get('score', 0))
            is_boosted = "⬆️" if r.get('title_boost_applied', False) else ""
            
            scoring_logger.info(
                f"      {i}. ID:{source_id} | {title}... | "
                f"分數: {score:.4f} {is_boosted}"
            )
        
        scoring_logger.info("-" * 40)
    
    # ============================================================
    # Stage 2: 二階搜尋（文件搜尋）
    # ============================================================
    
    def log_stage2_start(self, section_ids: List[int], top_k: int, threshold: float):
        """
        記錄二階搜尋開始
        
        Args:
            section_ids: 從一階搜尋獲得的 Section IDs
            top_k: 返回結果數量
            threshold: 相似度閾值
        """
        scoring_logger.info(f"📌 [Stage 2] 二階搜尋開始")
        scoring_logger.info(f"   基於一階 Section IDs: {section_ids[:5]}{'...' if len(section_ids) > 5 else ''}")
        scoring_logger.info(f"   Top K: {top_k}")
        scoring_logger.info(f"   閾值: {threshold}")
        
        self._stage2_data = {
            'section_ids': section_ids,
            'top_k': top_k,
            'threshold': threshold
        }
    
    def log_stage2_document_search(self, results: List[Dict]):
        """
        記錄二階文件搜尋結果
        
        Args:
            results: 二階搜尋結果列表
        """
        scoring_logger.info(f"   📄 [文件搜尋] 找到 {len(results)} 筆相關文件")
        
        for i, r in enumerate(results[:10], 1):
            title = r.get('title', r.get('metadata', {}).get('document_title', 'N/A'))[:50]
            score = r.get('score', r.get('similarity_score', 0))
            section_id = r.get('metadata', {}).get('section_id', 
                         r.get('metadata', {}).get('source_id', 'N/A'))
            
            scoring_logger.info(
                f"      {i}. {title}... | "
                f"分數: {score:.4f} | "
                f"來源Section: {section_id}"
            )
        
        if len(results) > 10:
            scoring_logger.info(f"      ... 還有 {len(results) - 10} 筆結果")
    
    def log_stage2_result(self, results: List[Dict]):
        """
        記錄二階搜尋最終結果
        
        Args:
            results: 二階搜尋最終結果列表
        """
        scoring_logger.info(f"   📊 [Stage 2 最終結果] 共 {len(results)} 筆")
        
        for i, r in enumerate(results, 1):
            doc_id = r.get('metadata', {}).get('document_id', 'N/A')
            title = r.get('title', r.get('metadata', {}).get('document_title', 'N/A'))[:40]
            score = r.get('score', 0)
            content_len = len(r.get('content', ''))
            
            scoring_logger.info(
                f"      {i}. DocID:{doc_id} | {title}... | "
                f"分數: {score:.4f} | 內容長度: {content_len} 字元"
            )
        
        scoring_logger.info("-" * 40)
    
    # ============================================================
    # 其他記錄方法
    # ============================================================
    
    def log_query_classification(self, original_query: str, cleaned_query: str, 
                                  query_type: str, detected_keywords: List[str] = None):
        """
        記錄查詢分類和清理過程
        
        Args:
            original_query: 原始查詢
            cleaned_query: 清理後的查詢
            query_type: 查詢類型（document, section, list_all）
            detected_keywords: 檢測到的關鍵字列表
        """
        scoring_logger.info(f"   🏷️  [查詢分類]")
        scoring_logger.info(f"      原始查詢: '{original_query}'")
        scoring_logger.info(f"      查詢類型: {query_type}")
        if detected_keywords:
            scoring_logger.info(f"      檢測關鍵字: {detected_keywords}")
        scoring_logger.info(f"      清理後查詢: '{cleaned_query}'")
    
    def log_threshold_filter(self, before_count: int, after_count: int, 
                              threshold: float, protected_count: int = 0):
        """
        記錄閾值過濾過程
        
        Args:
            before_count: 過濾前數量
            after_count: 過濾後數量
            threshold: 使用的閾值
            protected_count: 被 Top-K Protection 保護的數量
        """
        filtered_count = before_count - after_count
        scoring_logger.info(
            f"   🎯 [閾值過濾] {before_count} → {after_count} "
            f"(過濾 {filtered_count} 筆, threshold={threshold})"
        )
        if protected_count > 0:
            scoring_logger.info(
                f"      🛡️ Top-K Protection: {protected_count} 筆低分結果被保護"
            )
    
    def log_error(self, stage: str, error_message: str):
        """
        記錄錯誤
        
        Args:
            stage: 發生錯誤的階段
            error_message: 錯誤訊息
        """
        scoring_logger.error(f"   ❌ [{stage}] 錯誤: {error_message}")
    
    def log_fallback(self, from_method: str, to_method: str, reason: str = None):
        """
        記錄降級行為
        
        Args:
            from_method: 原本的方法
            to_method: 降級後的方法
            reason: 降級原因
        """
        scoring_logger.warning(
            f"   ⚠️  [降級] {from_method} → {to_method}"
            + (f" (原因: {reason})" if reason else "")
        )


# ============================================================
# 便利函數
# ============================================================

def create_scoring_logger(query: str, version_name: str, 
                          conversation_id: str = None) -> VSAScoringLogger:
    """
    創建 VSA 算分記錄器的便利函數
    
    Args:
        query: 用戶搜尋查詢
        version_name: VSA 版本名稱
        conversation_id: 對話 ID（可選）
        
    Returns:
        VSAScoringLogger: 配置好的算分記錄器實例
    """
    return VSAScoringLogger(
        query=query,
        version_name=version_name,
        conversation_id=conversation_id
    )


def should_log_scoring(version_config: Dict) -> bool:
    """
    判斷是否應該記錄算分過程
    
    目前只對 v1.2.2 (Hybrid Search + Title Boost) 版本啟用詳細日誌。
    
    Args:
        version_config: 版本配置字典
        
    Returns:
        bool: 是否啟用算分日誌
    """
    if not version_config:
        return False
    
    # 檢查是否啟用混合搜尋或 Title Boost
    rag_settings = version_config.get('rag_settings', {})
    
    # 檢查 Stage 1
    stage1_config = rag_settings.get('stage1', {})
    if stage1_config.get('use_hybrid_search', False):
        return True
    if stage1_config.get('enable_title_boost', False):
        return True
    
    # 檢查 Stage 2
    stage2_config = rag_settings.get('stage2', {})
    if stage2_config.get('use_hybrid_search', False):
        return True
    if stage2_config.get('enable_title_boost', False):
        return True
    
    return False


# 導出
__all__ = [
    'VSAScoringLogger',
    'create_scoring_logger',
    'should_log_scoring',
    'scoring_logger',  # 原始 logger，供直接使用
]
