"""
Top-K Protection 功能單元測試

測試 library/dify_knowledge/__init__.py 中的 filter_results_by_score 方法
驗證 Top-K Protection 在不同場景下的行為
"""

import pytest
import logging
from unittest.mock import MagicMock, patch


class TestFilterResultsByScore:
    """測試 filter_results_by_score 方法的 Top-K Protection 功能"""
    
    @pytest.fixture
    def mock_handler(self):
        """創建模擬的 DifyKnowledgeSearchHandler"""
        with patch('library.dify_knowledge.DifyKnowledgeSearchHandler.__init__', return_value=None):
            from library.dify_knowledge import DifyKnowledgeSearchHandler
            handler = DifyKnowledgeSearchHandler.__new__(DifyKnowledgeSearchHandler)
            handler.logger = logging.getLogger('test')
            return handler
    
    @pytest.fixture
    def sample_results(self):
        """樣本搜尋結果"""
        return [
            {'title': 'Result 1', 'content': 'Content 1', 'score': 0.95},
            {'title': 'Result 2', 'content': 'Content 2', 'score': 0.85},
            {'title': 'Result 3', 'content': 'Content 3', 'score': 0.75},
            {'title': 'Result 4', 'content': 'Content 4', 'score': 0.65},
        ]
    
    def test_normal_filtering_without_protection(self, mock_handler, sample_results):
        """測試一般過濾（不觸發 Top-K Protection）"""
        # 情境：threshold 不高，所有結果都通過
        threshold = 0.6
        stage = 1
        top_k = 3
        knowledge_type = 'protocol_guide'
        
        # 導入 filter_results_by_score 方法
        from library.dify_knowledge import DifyKnowledgeSearchHandler
        result = DifyKnowledgeSearchHandler.filter_results_by_score(
            mock_handler, sample_results, threshold, stage, top_k, knowledge_type
        )
        
        # 驗證：所有 4 個結果都應該通過（所有分數 >= 0.6）
        assert len(result) == 4
        assert all(r['score'] >= threshold for r in result)
    
    def test_topk_protection_triggered(self, mock_handler, sample_results):
        """測試 Top-K Protection 被觸發"""
        # 情境：高 threshold 導致過度過濾
        threshold = 0.9  # 只有 Result 1 (0.95) 通過
        stage = 1
        top_k = 3  # 期望返回 3 個結果
        knowledge_type = 'protocol_guide'
        
        from library.dify_knowledge import DifyKnowledgeSearchHandler
        result = DifyKnowledgeSearchHandler.filter_results_by_score(
            mock_handler, sample_results, threshold, stage, top_k, knowledge_type
        )
        
        # 驗證：Top-K Protection 應該保留前 3 個結果
        assert len(result) == 3
        assert result[0]['score'] == 0.95  # 原本通過的結果
        assert result[1]['score'] == 0.85  # 被保護的結果
        assert result[2]['score'] == 0.75  # 被保護的結果
    
    def test_topk_protection_with_zero_passed_results(self, mock_handler, sample_results):
        """測試 Top-K Protection - 所有結果都被過濾的情況"""
        # 情境：極高 threshold，沒有結果通過
        threshold = 0.99  # 所有結果都不通過
        stage = 1
        top_k = 2
        knowledge_type = 'protocol_guide'
        
        from library.dify_knowledge import DifyKnowledgeSearchHandler
        result = DifyKnowledgeSearchHandler.filter_results_by_score(
            mock_handler, sample_results, threshold, stage, top_k, knowledge_type
        )
        
        # 驗證：Top-K Protection 保留前 2 個結果
        assert len(result) == 2
        assert result[0]['score'] == 0.95
        assert result[1]['score'] == 0.85
    
    def test_topk_protection_only_for_stage1(self, mock_handler, sample_results):
        """測試 Top-K Protection 只在 Stage 1 生效"""
        # 情境：Stage 2 不應該觸發 Top-K Protection
        threshold = 0.9
        stage = 2  # Stage 2
        top_k = 3
        knowledge_type = 'protocol_guide'
        
        from library.dify_knowledge import DifyKnowledgeSearchHandler
        result = DifyKnowledgeSearchHandler.filter_results_by_score(
            mock_handler, sample_results, threshold, stage, top_k, knowledge_type
        )
        
        # 驗證：Stage 2 不觸發保護，嚴格過濾
        assert len(result) == 1  # 只有 Result 1 (0.95) 通過
        assert result[0]['score'] == 0.95
    
    def test_topk_protection_only_for_protocol_guide(self, mock_handler, sample_results):
        """測試 Top-K Protection 只對 protocol_guide 生效"""
        # 情境：其他知識庫類型不觸發 Top-K Protection
        threshold = 0.9
        stage = 1
        top_k = 3
        knowledge_type = 'rvt_guide'  # 不是 protocol_guide
        
        from library.dify_knowledge import DifyKnowledgeSearchHandler
        result = DifyKnowledgeSearchHandler.filter_results_by_score(
            mock_handler, sample_results, threshold, stage, top_k, knowledge_type
        )
        
        # 驗證：其他類型不觸發保護
        assert len(result) == 1
        assert result[0]['score'] == 0.95
    
    def test_topk_protection_respects_original_length(self, mock_handler):
        """測試 Top-K Protection 不會超過原始結果數量"""
        # 情境：原始結果少於 top_k
        results = [
            {'title': 'Result 1', 'content': 'Content 1', 'score': 0.4},
            {'title': 'Result 2', 'content': 'Content 2', 'score': 0.3},
        ]
        threshold = 0.9
        stage = 1
        top_k = 5  # 期望 5 個，但只有 2 個
        knowledge_type = 'protocol_guide'
        
        from library.dify_knowledge import DifyKnowledgeSearchHandler
        result = DifyKnowledgeSearchHandler.filter_results_by_score(
            mock_handler, results, threshold, stage, top_k, knowledge_type
        )
        
        # 驗證：最多返回原始結果數量
        assert len(result) == 2
    
    def test_iol_query_scenario(self, mock_handler):
        """測試實際 IOL 查詢場景"""
        # 情境：模擬 IOL 查詢的實際情況
        # RRF 正規化後，最低分結果可能是 0.0
        results = [
            {'title': 'Some Guide', 'content': 'Some content', 'score': 1.0},
            {'title': 'UNH-IOL', 'content': 'IOL password: 111111', 'score': 0.0},  # 被正規化為 0.0
        ]
        threshold = 0.8
        stage = 1
        top_k = 2
        knowledge_type = 'protocol_guide'
        
        from library.dify_knowledge import DifyKnowledgeSearchHandler
        result = DifyKnowledgeSearchHandler.filter_results_by_score(
            mock_handler, results, threshold, stage, top_k, knowledge_type
        )
        
        # 驗證：Top-K Protection 保護了 score=0.0 的 UNH-IOL
        assert len(result) == 2
        assert result[0]['title'] == 'Some Guide'
        assert result[1]['title'] == 'UNH-IOL'
        assert result[1]['score'] == 0.0
    
    def test_threshold_zero_no_filtering(self, mock_handler, sample_results):
        """測試 threshold=0 時不進行過濾"""
        threshold = 0
        stage = 1
        top_k = 2
        knowledge_type = 'protocol_guide'
        
        from library.dify_knowledge import DifyKnowledgeSearchHandler
        result = DifyKnowledgeSearchHandler.filter_results_by_score(
            mock_handler, sample_results, threshold, stage, top_k, knowledge_type
        )
        
        # 驗證：threshold=0 時返回所有結果
        assert len(result) == 4  # 所有原始結果
    
    def test_negative_threshold(self, mock_handler, sample_results):
        """測試負數 threshold（無效值）"""
        threshold = -0.5
        stage = 1
        top_k = 2
        knowledge_type = 'protocol_guide'
        
        from library.dify_knowledge import DifyKnowledgeSearchHandler
        result = DifyKnowledgeSearchHandler.filter_results_by_score(
            mock_handler, sample_results, threshold, stage, top_k, knowledge_type
        )
        
        # 驗證：負數 threshold 視為 0，返回所有結果
        assert len(result) == 4
    
    def test_empty_results(self, mock_handler):
        """測試空結果列表"""
        results = []
        threshold = 0.8
        stage = 1
        top_k = 2
        knowledge_type = 'protocol_guide'
        
        from library.dify_knowledge import DifyKnowledgeSearchHandler
        result = DifyKnowledgeSearchHandler.filter_results_by_score(
            mock_handler, results, threshold, stage, top_k, knowledge_type
        )
        
        # 驗證：空列表返回空列表
        assert len(result) == 0


class TestTopKProtectionIntegration:
    """Top-K Protection 整合測試"""
    
    def test_stage1_vs_stage2_behavior(self):
        """測試 Stage 1 和 Stage 2 的行為差異"""
        # TODO: 需要實際的搜尋服務來測試
        pass
    
    def test_protocol_guide_vs_other_types(self):
        """測試不同知識庫類型的行為差異"""
        # TODO: 需要實際的搜尋服務來測試
        pass


class TestTopKProtectionEdgeCases:
    """邊界條件測試"""
    
    @pytest.fixture
    def mock_handler(self):
        """創建模擬的 DifyKnowledgeSearchHandler"""
        with patch('library.dify_knowledge.DifyKnowledgeSearchHandler.__init__', return_value=None):
            from library.dify_knowledge import DifyKnowledgeSearchHandler
            handler = DifyKnowledgeSearchHandler.__new__(DifyKnowledgeSearchHandler)
            handler.logger = logging.getLogger('test')
            return handler
    
    def test_all_results_same_score(self, mock_handler):
        """測試所有結果分數相同"""
        results = [
            {'title': 'Result 1', 'content': 'Content 1', 'score': 0.5},
            {'title': 'Result 2', 'content': 'Content 2', 'score': 0.5},
            {'title': 'Result 3', 'content': 'Content 3', 'score': 0.5},
        ]
        threshold = 0.8
        stage = 1
        top_k = 2
        knowledge_type = 'protocol_guide'
        
        from library.dify_knowledge import DifyKnowledgeSearchHandler
        result = DifyKnowledgeSearchHandler.filter_results_by_score(
            mock_handler, results, threshold, stage, top_k, knowledge_type
        )
        
        # 驗證：Top-K Protection 保留前 2 個
        assert len(result) == 2
    
    def test_missing_score_field(self, mock_handler):
        """測試結果缺少 score 欄位"""
        results = [
            {'title': 'Result 1', 'content': 'Content 1'},  # 缺少 score
            {'title': 'Result 2', 'content': 'Content 2', 'score': 0.9},
        ]
        threshold = 0.8
        stage = 1
        top_k = 2
        knowledge_type = 'protocol_guide'
        
        from library.dify_knowledge import DifyKnowledgeSearchHandler
        result = DifyKnowledgeSearchHandler.filter_results_by_score(
            mock_handler, results, threshold, stage, top_k, knowledge_type
        )
        
        # 驗證：缺少 score 的結果視為 0，被 Top-K Protection 保留
        assert len(result) == 2
    
    def test_none_parameters(self, mock_handler):
        """測試 None 參數"""
        results = [
            {'title': 'Result 1', 'content': 'Content 1', 'score': 0.9},
            {'title': 'Result 2', 'content': 'Content 2', 'score': 0.7},
        ]
        threshold = 0.8
        stage = None  # None
        top_k = None  # None
        knowledge_type = None  # None
        
        from library.dify_knowledge import DifyKnowledgeSearchHandler
        result = DifyKnowledgeSearchHandler.filter_results_by_score(
            mock_handler, results, threshold, stage, top_k, knowledge_type
        )
        
        # 驗證：None 參數不觸發 Top-K Protection，執行正常過濾
        assert len(result) == 1  # 只有 Result 1 (0.9) 通過


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
