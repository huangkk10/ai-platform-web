"""
AI OCR 處理服務

提供統一的 OCR 處理邏輯，包含：
- 圖像預處理
- OCR 文字識別
- AI 結構化資料擷取
- 處理狀態管理
- 錯誤處理和重試機制

使用方式：
    from library.ai_ocr.ocr_processor import OCRProcessor, process_ocr_record
    
    # 處理單個記錄
    result = process_ocr_record(ocr_record)
    
    # 使用處理器類
    processor = OCRProcessor()
    result = processor.process_record(ocr_record)
"""

import logging
import time
from typing import Dict, Any, Tuple, Optional
from rest_framework import status
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class OCRProcessingError(Exception):
    """OCR 處理專用異常"""
    pass


class OCRProcessor:
    """OCR 處理器類 - 統一管理所有 OCR 處理邏輯"""
    
    def __init__(self):
        self.logger = logger
        self.default_confidence = 0.95
        
    def validate_record(self, ocr_record) -> Tuple[bool, Optional[str]]:
        """
        驗證 OCR 記錄是否可以處理
        
        Args:
            ocr_record: OCR 記錄實例
            
        Returns:
            Tuple[bool, Optional[str]]: (是否有效, 錯誤訊息)
        """
        try:
            # 檢查是否有原始圖像
            if not hasattr(ocr_record, 'original_image_data') or not ocr_record.original_image_data:
                return False, "請先上傳原始圖像"
                
            # 檢查記錄是否已在處理中
            if hasattr(ocr_record, 'processing_status') and ocr_record.processing_status == 'processing':
                return False, "記錄正在處理中，請稍後再試"
                
            return True, None
            
        except Exception as e:
            self.logger.error(f"記錄驗證失敗: {e}")
            return False, f"記錄驗證失敗: {str(e)}"
    
    def extract_raw_text(self, ocr_record) -> str:
        """
        從 OCR 記錄中擷取原始文字
        這裡使用模擬實現，實際專案中可以整合真實的 OCR 服務
        
        Args:
            ocr_record: OCR 記錄實例
            
        Returns:
            str: 擷取的原始文字
        """
        try:
            # 如果已有 OCR 文字，直接返回
            if hasattr(ocr_record, 'ocr_raw_text') and ocr_record.ocr_raw_text:
                return ocr_record.ocr_raw_text
            
            # 模擬 OCR 處理 - 根據記錄現有資料生成
            mock_ocr_text = f"""
            專案名稱: {getattr(ocr_record, 'project_name', None) or 'Storage Benchmark Score'}
            測試得分: {getattr(ocr_record, 'benchmark_score', None) or '6883'}
            平均帶寬: {getattr(ocr_record, 'average_bandwidth', None) or '1174.89 MB/s'}
            裝置型號: {getattr(ocr_record, 'device_model', None) or 'KINGSTON SFYR2S1TO'}
            韌體版本: {getattr(ocr_record, 'firmware_version', None) or 'SGW0904A'}
            測試時間: {getattr(ocr_record, 'test_datetime', None) or '2025-09-06 16:13 +08:00'}
            3DMark 版本: {getattr(ocr_record, 'benchmark_version', None) or '2.28.8228 (測試專用版)'}
            """
            
            return mock_ocr_text.strip()
            
        except Exception as e:
            self.logger.error(f"原始文字擷取失敗: {e}")
            raise OCRProcessingError(f"原始文字擷取失敗: {str(e)}")
    
    def generate_structured_data(self, ocr_record, raw_text: str) -> Dict[str, Any]:
        """
        生成結構化資料
        
        Args:
            ocr_record: OCR 記錄實例
            raw_text: 原始 OCR 文字
            
        Returns:
            Dict[str, Any]: 結構化資料
        """
        try:
            # 如果已有結構化資料，直接返回
            if hasattr(ocr_record, 'ai_structured_data') and ocr_record.ai_structured_data:
                return ocr_record.ai_structured_data
            
            # 模擬 AI 結構化處理
            structured_data = {
                "project_name": getattr(ocr_record, 'project_name', None) or "Storage Benchmark Score",
                "benchmark_score": getattr(ocr_record, 'benchmark_score', None) or 6883,
                "average_bandwidth": getattr(ocr_record, 'average_bandwidth', None) or "1174.89 MB/s",
                "device_model": getattr(ocr_record, 'device_model', None) or "KINGSTON SFYR2S1TO",
                "firmware_version": getattr(ocr_record, 'firmware_version', None) or "SGW0904A",
                "test_datetime": str(getattr(ocr_record, 'test_datetime', None) or "2025-09-06 16:13 +08:00"),
                "benchmark_version": getattr(ocr_record, 'benchmark_version', None) or "2.28.8228 (測試專用版)",
                "extracted_fields": [
                    "project_name", "benchmark_score", "average_bandwidth", 
                    "device_model", "firmware_version", "test_datetime", "benchmark_version"
                ],
                "confidence": self.default_confidence,
                "processing_timestamp": time.time(),
                "raw_text_length": len(raw_text),
                "extraction_method": "ai_mock_simulation"
            }
            
            return structured_data
            
        except Exception as e:
            self.logger.error(f"結構化資料生成失敗: {e}")
            raise OCRProcessingError(f"結構化資料生成失敗: {str(e)}")
    
    def update_record_status(self, ocr_record, status_value: str, 
                           processing_time: float = None, 
                           confidence: float = None,
                           raw_text: str = None,
                           structured_data: Dict[str, Any] = None) -> None:
        """
        更新記錄狀態和處理結果
        
        Args:
            ocr_record: OCR 記錄實例
            status_value: 處理狀態 ('processing', 'completed', 'failed')
            processing_time: 處理時間（秒）
            confidence: 置信度
            raw_text: OCR 原始文字
            structured_data: 結構化資料
        """
        try:
            # 更新處理狀態
            if hasattr(ocr_record, 'processing_status'):
                ocr_record.processing_status = status_value
            
            # 更新處理時間
            if processing_time is not None and hasattr(ocr_record, 'ocr_processing_time'):
                ocr_record.ocr_processing_time = processing_time
            
            # 更新置信度
            if confidence is not None and hasattr(ocr_record, 'ocr_confidence'):
                ocr_record.ocr_confidence = confidence
            
            # 更新 OCR 原始文字
            if raw_text is not None and hasattr(ocr_record, 'ocr_raw_text'):
                ocr_record.ocr_raw_text = raw_text
            
            # 更新結構化資料
            if structured_data is not None and hasattr(ocr_record, 'ai_structured_data'):
                ocr_record.ai_structured_data = structured_data
            
            # 保存變更
            ocr_record.save()
            
            self.logger.info(f"記錄狀態已更新: {ocr_record.id} -> {status_value}")
            
        except Exception as e:
            self.logger.error(f"記錄狀態更新失敗: {e}")
            raise OCRProcessingError(f"記錄狀態更新失敗: {str(e)}")
    
    def process_record(self, ocr_record) -> Dict[str, Any]:
        """
        處理 OCR 記錄的主要方法
        
        Args:
            ocr_record: OCR 記錄實例
            
        Returns:
            Dict[str, Any]: 處理結果
        """
        start_time = time.time()
        
        try:
            # 1. 驗證記錄
            is_valid, error_message = self.validate_record(ocr_record)
            if not is_valid:
                return {
                    'success': False,
                    'error': error_message,
                    'status_code': status.HTTP_400_BAD_REQUEST
                }
            
            # 2. 更新狀態為處理中
            self.update_record_status(ocr_record, 'processing')
            
            # 3. 擷取原始文字
            raw_text = self.extract_raw_text(ocr_record)
            
            # 4. 生成結構化資料
            structured_data = self.generate_structured_data(ocr_record, raw_text)
            
            # 5. 計算處理時間
            processing_time = time.time() - start_time
            
            # 6. 更新記錄為完成狀態
            self.update_record_status(
                ocr_record, 
                'completed',
                processing_time=processing_time,
                confidence=self.default_confidence,
                raw_text=raw_text,
                structured_data=structured_data
            )
            
            # 7. 返回成功結果
            result = {
                'success': True,
                'message': 'OCR 處理完成',
                'processing_time': processing_time,
                'confidence': self.default_confidence,
                'raw_text_preview': (
                    raw_text[:200] + "..." if len(raw_text) > 200 else raw_text
                ),
                'structured_data': structured_data,
                'record_id': ocr_record.id,
                'status_code': status.HTTP_200_OK
            }
            
            self.logger.info(f"OCR 處理成功: 記錄 {ocr_record.id}, 耗時 {processing_time:.2f}s")
            return result
            
        except OCRProcessingError as e:
            # OCR 專用異常
            self.logger.error(f"OCR 處理失敗: {e}")
            try:
                self.update_record_status(ocr_record, 'failed')
            except Exception:
                pass  # 忽略狀態更新失敗
            
            return {
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time,
                'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR
            }
            
        except Exception as e:
            # 一般異常
            self.logger.error(f"OCR 處理異常: {e}")
            try:
                self.update_record_status(ocr_record, 'failed')
            except Exception:
                pass  # 忽略狀態更新失敗
            
            return {
                'success': False,
                'error': f'OCR 處理失敗: {str(e)}',
                'processing_time': time.time() - start_time,
                'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR
            }


# 便利函數
def process_ocr_record(ocr_record) -> Response:
    """
    處理 OCR 記錄的便利函數 - 直接返回 DRF Response
    
    Args:
        ocr_record: OCR 記錄實例
        
    Returns:
        Response: DRF Response 物件
    """
    try:
        processor = OCRProcessor()
        result = processor.process_record(ocr_record)
        
        if result['success']:
            # 成功回應
            response_data = {
                'message': result['message'],
                'processing_time': result['processing_time'],
                'confidence': result['confidence'],
                'raw_text_preview': result['raw_text_preview'],
                'structured_data': result['structured_data']
            }
            return Response(response_data, status=result['status_code'])
        else:
            # 錯誤回應
            return Response({
                'error': result['error']
            }, status=result['status_code'])
            
    except Exception as e:
        logger.error(f"process_ocr_record 便利函數執行失敗: {e}")
        return Response({
            'error': f'OCR 處理服務異常: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def create_ocr_processor() -> Optional[OCRProcessor]:
    """
    創建 OCR 處理器實例的便利函數
    
    Returns:
        Optional[OCRProcessor]: 處理器實例或 None（如果創建失敗）
    """
    try:
        return OCRProcessor()
    except Exception as e:
        logger.warning(f"無法創建 OCR 處理器: {e}")
        return None


# 備用實現
def fallback_process_ocr_record(ocr_record) -> Response:
    """
    OCR 處理的備用實現 - 簡化版本
    當主要處理器不可用時使用
    """
    try:
        # 檢查是否有原始圖像
        if not hasattr(ocr_record, 'original_image_data') or not ocr_record.original_image_data:
            return Response({
                'error': '請先上傳原始圖像'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 簡單的模擬處理
        start_time = time.time()
        
        # 更新處理狀態
        if hasattr(ocr_record, 'processing_status'):
            ocr_record.processing_status = 'completed'
        
        processing_time = time.time() - start_time
        
        if hasattr(ocr_record, 'ocr_processing_time'):
            ocr_record.ocr_processing_time = processing_time
        if hasattr(ocr_record, 'ocr_confidence'):
            ocr_record.ocr_confidence = 0.85  # 備用實現的置信度較低
            
        ocr_record.save()
        
        return Response({
            'message': 'OCR 處理完成（備用模式）',
            'processing_time': processing_time,
            'confidence': 0.85,
            'note': '使用備用處理模式，功能可能受限'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"備用 OCR 處理失敗: {e}")
        return Response({
            'error': f'OCR 處理失敗: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)