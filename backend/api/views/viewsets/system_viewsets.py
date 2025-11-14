"""
系統設定相關的 ViewSet
====================

提供系統級配置的 API 接口
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from api.models import SearchThresholdSetting
from api.serializers import SearchThresholdSettingSerializer
import logging

logger = logging.getLogger(__name__)


class SearchThresholdSettingViewSet(viewsets.ModelViewSet):
    """
    搜尋閾值設定 ViewSet
    
    提供 Web UI 管理搜尋參數的接口：
    - GET /api/search-threshold-settings/ - 列出所有配置
    - GET /api/search-threshold-settings/{assistant_type}/ - 獲取特定配置
    - PATCH /api/search-threshold-settings/{assistant_type}/ - 更新配置
    - POST /api/search-threshold-settings/{assistant_type}/test_search/ - 測試搜尋
    """
    
    queryset = SearchThresholdSetting.objects.all()
    serializer_class = SearchThresholdSettingSerializer
    permission_classes = [permissions.IsAdminUser]  # 只有管理員可訪問
    lookup_field = 'assistant_type'  # 使用 assistant_type 作為查詢欄位
    
    def list(self, request, *args, **kwargs):
        """
        列出所有 Assistant 的配置
        
        GET /api/search-threshold-settings/
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        
        logger.info(f"管理員 {request.user.username} 查詢所有搜尋閾值配置")
        
        return Response(serializer.data)
    
    def retrieve(self, request, *args, **kwargs):
        """
        獲取特定 Assistant 的配置
        
        GET /api/search-threshold-settings/{assistant_type}/
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        logger.info(f"管理員 {request.user.username} 查詢 {instance.assistant_type} 配置")
        
        return Response(serializer.data)
    
    def update(self, request, *args, **kwargs):
        """
        更新特定 Assistant 的配置（完整更新）
        
        PUT /api/search-threshold-settings/{assistant_type}/
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        logger.info(
            f"管理員 {request.user.username} 更新 {instance.assistant_type} 配置: "
            f"Stage1={request.data.get('stage1_title_weight')}/{request.data.get('stage1_content_weight')}, "
            f"Stage2={request.data.get('stage2_title_weight')}/{request.data.get('stage2_content_weight')}, "
            f"Unified={request.data.get('use_unified_weights')}"
        )
        
        return Response(serializer.data)
    
    def partial_update(self, request, *args, **kwargs):
        """
        部分更新特定 Assistant 的配置
        
        PATCH /api/search-threshold-settings/{assistant_type}/
        """
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def test_search(self, request, assistant_type=None):
        """
        測試當前配置的搜尋效果（不寫入資料庫）
        
        POST /api/search-threshold-settings/{assistant_type}/test_search/
        
        Request Body:
        {
            "query": "IOL",
            "stage1_title_weight": 60,
            "stage1_content_weight": 40,
            "stage1_threshold": 0.7,
            "stage2_title_weight": 50,
            "stage2_content_weight": 50,
            "stage2_threshold": 0.6,
            "use_unified_weights": false
        }
        
        Response:
        {
            "query": "IOL",
            "config": {...},
            "results": {
                "stage1": [...],
                "stage2": [...]
            },
            "analysis": {
                "stage1_avg_score": 0.793,
                "stage2_avg_score": 0.794,
                "score_difference": 0.001,
                "difference_percentage": 0.12
            }
        }
        """
        query = request.data.get('query', '').strip()
        
        if not query:
            return Response(
                {'error': '請提供測試查詢字串'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 解析臨時配置
        temp_config = {
            'stage1_title_weight': request.data.get('stage1_title_weight', 60),
            'stage1_content_weight': request.data.get('stage1_content_weight', 40),
            'stage1_threshold': float(request.data.get('stage1_threshold', 0.7)),
            'stage2_title_weight': request.data.get('stage2_title_weight', 50),
            'stage2_content_weight': request.data.get('stage2_content_weight', 50),
            'stage2_threshold': float(request.data.get('stage2_threshold', 0.6)),
            'use_unified_weights': request.data.get('use_unified_weights', True),
        }
        
        # 驗證權重總和
        if temp_config['stage1_title_weight'] + temp_config['stage1_content_weight'] != 100:
            return Response(
                {'error': '第一階段權重總和必須為 100%'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if temp_config['stage2_title_weight'] + temp_config['stage2_content_weight'] != 100:
            return Response(
                {'error': '第二階段權重總和必須為 100%'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # 獲取對應的搜尋服務
            service = self._get_search_service(assistant_type)
            
            # 臨時更新資料庫配置（用於測試）
            setting = SearchThresholdSetting.objects.get(assistant_type=assistant_type)
            original_config = {
                'stage1_title_weight': setting.stage1_title_weight,
                'stage1_content_weight': setting.stage1_content_weight,
                'stage1_threshold': float(setting.stage1_threshold),
                'stage2_title_weight': setting.stage2_title_weight,
                'stage2_content_weight': setting.stage2_content_weight,
                'stage2_threshold': float(setting.stage2_threshold),
                'use_unified_weights': setting.use_unified_weights,
            }
            
            # 臨時套用測試配置
            for key, value in temp_config.items():
                setattr(setting, key, value)
            setting.save()
            
            try:
                # Stage 1 測試
                results_stage1 = service.search_knowledge(
                    query=query,
                    limit=3,
                    threshold=temp_config['stage1_threshold'],
                    stage=1
                )
                
                # Stage 2 測試
                results_stage2 = service.search_knowledge(
                    query=query,
                    limit=3,
                    threshold=temp_config['stage2_threshold'],
                    stage=2
                )
                
                # 計算分析數據
                stage1_scores = [r.get('score', 0) for r in results_stage1]
                stage2_scores = [r.get('score', 0) for r in results_stage2]
                
                stage1_avg = sum(stage1_scores) / len(stage1_scores) if stage1_scores else 0
                stage2_avg = sum(stage2_scores) / len(stage2_scores) if stage2_scores else 0
                score_diff = abs(stage1_avg - stage2_avg)
                diff_percentage = (score_diff / max(stage1_avg, stage2_avg) * 100) if max(stage1_avg, stage2_avg) > 0 else 0
                
                analysis = {
                    'stage1_avg_score': round(stage1_avg, 4),
                    'stage2_avg_score': round(stage2_avg, 4),
                    'score_difference': round(score_diff, 4),
                    'difference_percentage': round(diff_percentage, 2),
                    'stage1_count': len(results_stage1),
                    'stage2_count': len(results_stage2),
                }
                
                logger.info(
                    f"管理員 {request.user.username} 測試 {assistant_type} 搜尋: "
                    f"query='{query}', stage1_avg={stage1_avg:.4f}, stage2_avg={stage2_avg:.4f}"
                )
                
                return Response({
                    'query': query,
                    'config': temp_config,
                    'results': {
                        'stage1': results_stage1,
                        'stage2': results_stage2
                    },
                    'analysis': analysis
                })
                
            finally:
                # 恢復原始配置
                for key, value in original_config.items():
                    setattr(setting, key, value)
                setting.save()
                
        except SearchThresholdSetting.DoesNotExist:
            return Response(
                {'error': f'找不到 {assistant_type} 的配置'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"測試搜尋失敗: {str(e)}", exc_info=True)
            return Response(
                {'error': f'測試失敗: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_search_service(self, assistant_type):
        """
        根據 assistant_type 獲取對應的搜尋服務
        
        Args:
            assistant_type: 'protocol_assistant' 或 'rvt_assistant' 等
            
        Returns:
            對應的 SearchService 實例
        """
        if assistant_type == 'protocol_assistant':
            from library.protocol_guide.search_service import ProtocolGuideSearchService
            return ProtocolGuideSearchService()
        elif assistant_type == 'rvt_assistant':
            from library.rvt_guide.search_service import RvtGuideSearchService
            return RvtGuideSearchService()
        else:
            raise ValueError(f"Unknown assistant type: {assistant_type}")
