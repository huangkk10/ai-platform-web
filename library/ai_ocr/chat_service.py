"""
AI OCR 聊天服務

處理所有 AI OCR 相關的聊天和檔案分析功能：
- OCR 聊天處理
- 檔案上傳和分析
- AI 回應處理
- OCR 結果解析和保存

提供統一的聊天和檔案處理介面
"""

import logging
import time
import tempfile
import os
from rest_framework import status
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class AIOCRChatService:
    """AI OCR 聊天服務 - 統一管理聊天和檔案分析功能"""
    
    def __init__(self):
        self.logger = logger
        
    def handle_ocr_chat_request(self, message, conversation_id='', user=None):
        """
        處理 OCR 聊天請求
        
        Args:
            message (str): 聊天訊息
            conversation_id (str): 對話 ID
            user: 當前用戶
            
        Returns:
            dict: 聊天回應結果
        """
        try:
            if not message:
                return {
                    'success': False,
                    'error': '訊息內容不能為空',
                    'status_code': status.HTTP_400_BAD_REQUEST
                }
            
            # 記錄請求
            self.logger.info(f"OCR 聊天請求: 用戶 {user.username if user and user.is_authenticated else 'guest'}")
            self.logger.debug(f"OCR 訊息: {message[:100]}...")
            
            # 獲取配置
            config_result = self._get_ocr_chat_config()
            if not config_result['success']:
                return config_result
            
            dify_config = config_result['config']
            
            # 準備請求
            request_data = self._prepare_chat_request(
                message, conversation_id, user, dify_config
            )
            
            # 發送請求
            response_result = self._send_chat_request(request_data)
            
            return response_result
            
        except Exception as e:
            self.logger.error(f"OCR 聊天處理失敗: {str(e)}")
            return {
                'success': False,
                'error': f'OCR 聊天服務錯誤: {str(e)}',
                'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR
            }
    
    def handle_file_analysis_request(self, uploaded_file, message='', user=None):
        """
        處理檔案分析請求
        
        Args:
            uploaded_file: 上傳的檔案
            message (str): 可選的分析指示
            user: 當前用戶
            
        Returns:
            dict: 檔案分析結果
        """
        try:
            if not uploaded_file:
                return {
                    'success': False,
                    'error': '需要上傳檔案進行分析',
                    'status_code': status.HTTP_400_BAD_REQUEST
                }
            
            # 檔案驗證
            validation_result = self._validate_uploaded_file(uploaded_file)
            if not validation_result['success']:
                return validation_result
            
            # 處理檔案分析
            analysis_result = self._process_file_analysis(uploaded_file, message, user)
            
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"檔案分析處理失敗: {str(e)}")
            return {
                'success': False,
                'error': f'檔案分析服務錯誤: {str(e)}',
                'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR
            }
    
    def _get_ocr_chat_config(self):
        """獲取 OCR 聊天配置"""
        try:
            from library.config.dify_config_manager import get_report_analyzer_config
            dify_config = get_report_analyzer_config()
            
            # 檢查必要配置
            if not dify_config.api_url or not dify_config.api_key:
                return {
                    'success': False,
                    'error': 'AI OCR API 配置不完整',
                    'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR
                }
            
            return {
                'success': True,
                'config': dify_config
            }
            
        except Exception as e:
            self.logger.error(f"獲取 OCR 聊天配置失敗: {e}")
            return {
                'success': False,
                'error': f'AI OCR 配置載入失敗: {str(e)}',
                'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR
            }
    
    def _prepare_chat_request(self, message, conversation_id, user, dify_config):
        """準備聊天請求數據"""
        headers = {
            'Authorization': f'Bearer {dify_config.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'inputs': {},
            'query': message,
            'response_mode': 'blocking',
            'user': f"ocr_user_{user.id if user and user.is_authenticated else 'guest'}"
        }
        
        if conversation_id:
            payload['conversation_id'] = conversation_id
        
        return {
            'url': dify_config.api_url,
            'headers': headers,
            'payload': payload
        }
    
    def _send_chat_request(self, request_data):
        """發送聊天請求"""
        try:
            import requests
            
            start_time = time.time()
            
            response = requests.post(
                request_data['url'],
                headers=request_data['headers'],
                json=request_data['payload'],
                timeout=120  # AI OCR 分析可能需要較長時間
            )
            
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                
                self.logger.info(f"AI OCR 聊天成功，響應時間: {elapsed:.2f}s")
                
                return {
                    'success': True,
                    'answer': result.get('answer', ''),
                    'conversation_id': result.get('conversation_id', ''),
                    'message_id': result.get('message_id', ''),
                    'response_time': elapsed,
                    'metadata': result.get('metadata', {}),
                    'usage': result.get('usage', {}),
                    'status_code': status.HTTP_200_OK
                }
            else:
                error_msg = f"AI OCR API 錯誤: {response.status_code} - {response.text}"
                self.logger.error(error_msg)
                
                return {
                    'success': False,
                    'error': error_msg,
                    'response_time': elapsed,
                    'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR
                }
                
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'AI OCR 分析超時，請稍後再試',
                'status_code': status.HTTP_408_REQUEST_TIMEOUT
            }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': 'AI OCR 連接失敗，請檢查網路連接',
                'status_code': status.HTTP_503_SERVICE_UNAVAILABLE
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'AI OCR API 請求錯誤: {str(e)}',
                'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR
            }
    
    def _validate_uploaded_file(self, uploaded_file):
        """驗證上傳的檔案"""
        try:
            # 檢查檔案類型
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'application/pdf']
            if uploaded_file.content_type not in allowed_types:
                return {
                    'success': False,
                    'error': f'不支援的檔案類型。支援的類型: {", ".join(allowed_types)}',
                    'status_code': status.HTTP_400_BAD_REQUEST
                }
            
            # 檢查檔案大小 (限制 10MB)
            max_size = 10 * 1024 * 1024  # 10MB
            if uploaded_file.size > max_size:
                return {
                    'success': False,
                    'error': f'檔案大小超過限制 ({max_size // (1024*1024)}MB)',
                    'status_code': status.HTTP_400_BAD_REQUEST
                }
            
            return {'success': True}
            
        except Exception as e:
            self.logger.error(f"檔案驗證失敗: {e}")
            return {
                'success': False,
                'error': f'檔案驗證失敗: {str(e)}',
                'status_code': status.HTTP_400_BAD_REQUEST
            }
    
    def _process_file_analysis(self, uploaded_file, message, user):
        """處理檔案分析"""
        temp_file_path = None
        temp_dir = None
        
        try:
            # 1. 保存臨時檔案
            temp_dir = tempfile.mkdtemp()
            temp_file_path = os.path.join(temp_dir, uploaded_file.name)
            
            with open(temp_file_path, 'wb+') as temp_file:
                for chunk in uploaded_file.chunks():
                    temp_file.write(chunk)
            
            # 2. 進一步驗證檔案
            file_validation_result = self._validate_file_for_upload(temp_file_path)
            if not file_validation_result['success']:
                return file_validation_result
            
            # 3. 獲取檔案資訊
            file_info = self._get_file_info(temp_file_path)
            
            # 4. 生成分析查詢
            query = message if message else self._get_default_analysis_query(temp_file_path)
            
            # 5. 執行分析
            analysis_result = self._execute_file_analysis(
                temp_file_path, query, user, file_info
            )
            
            # 6. 處理 AI 回應和 OCR 保存
            if analysis_result['success'] and analysis_result.get('answer'):
                ocr_result = self._process_ai_response_and_save_ocr(
                    analysis_result, uploaded_file, user, message
                )
                if ocr_result:
                    analysis_result['ocr_analysis'] = ocr_result
            
            # 7. 添加檔案資訊到響應
            analysis_result['file_info'] = {
                'name': file_info['file_name'],
                'size': file_info['file_size'],
                'type': 'image' if file_info['is_image'] else 'document'
            }
            
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"檔案分析處理失敗: {str(e)}")
            return {
                'success': False,
                'error': f'檔案分析錯誤: {str(e)}',
                'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR
            }
        
        finally:
            # 清理臨時檔案
            try:
                if temp_file_path and os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                if temp_dir and os.path.exists(temp_dir):
                    os.rmdir(temp_dir)
            except Exception as cleanup_error:
                self.logger.warning(f"臨時檔案清理失敗: {cleanup_error}")
    
    def _validate_file_for_upload(self, file_path, max_size_mb=10):
        """進一步驗證檔案"""
        try:
            from library.data_processing.file_utils import validate_file_for_upload
            is_valid, error_msg = validate_file_for_upload(file_path, max_size_mb)
            
            if is_valid:
                return {'success': True}
            else:
                return {
                    'success': False,
                    'error': f'檔案驗證失敗: {error_msg}',
                    'status_code': status.HTTP_400_BAD_REQUEST
                }
        except ImportError:
            # 如果 file_utils 不可用，使用簡化驗證
            return {'success': True}
        except Exception as e:
            return {
                'success': False,
                'error': f'檔案驗證錯誤: {str(e)}',
                'status_code': status.HTTP_400_BAD_REQUEST
            }
    
    def _get_file_info(self, file_path):
        """獲取檔案資訊"""
        try:
            from library.data_processing.file_utils import get_file_info
            return get_file_info(file_path)
        except ImportError:
            # 備用實現
            import os
            return {
                'file_name': os.path.basename(file_path),
                'file_size': os.path.getsize(file_path),
                'is_image': file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))
            }
        except Exception as e:
            self.logger.warning(f"獲取檔案資訊失敗: {e}")
            return {'file_name': 'unknown', 'file_size': 0, 'is_image': False}
    
    def _get_default_analysis_query(self, file_path):
        """獲取預設分析查詢"""
        try:
            from library.data_processing.file_utils import get_default_analysis_query
            return get_default_analysis_query(file_path)
        except ImportError:
            return "請分析這個檔案中的內容，特別是任何數據或測試結果。"
        except Exception as e:
            self.logger.warning(f"獲取預設查詢失敗: {e}")
            return "請分析這個檔案的內容。"
    
    def _execute_file_analysis(self, file_path, query, user, file_info):
        """執行檔案分析"""
        try:
            from library.dify_integration import create_report_analyzer_client
            from library.config.dify_config_manager import get_report_analyzer_config
            
            # 獲取配置和客戶端
            config = get_report_analyzer_config()
            client = create_report_analyzer_client(
                config.api_url,
                config.api_key,
                config.base_url
            )
            
            start_time = time.time()
            
            # 執行分析
            result = client.upload_and_analyze(
                file_path, 
                query, 
                user=f"web_user_{user.id if user and user.is_authenticated else 'guest'}",
                verbose=True
            )
            
            elapsed = time.time() - start_time
            
            if result['success']:
                self.logger.info(f"檔案分析成功: {file_info['file_name']}, 耗時 {elapsed:.2f}s")
                
                return {
                    'success': True,
                    'answer': result.get('answer', ''),
                    'conversation_id': result.get('conversation_id', ''),
                    'message_id': result.get('message_id', ''),
                    'response_time': elapsed,
                    'metadata': result.get('metadata', {}),
                    'usage': result.get('usage', {}),
                    'status_code': status.HTTP_200_OK
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', '檔案分析失敗'),
                    'response_time': elapsed,
                    'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR
                }
                
        except ImportError as e:
            self.logger.error(f"缺少必要的 library 模組: {e}")
            return {
                'success': False,
                'error': '檔案分析服務不可用，請聯絡管理員',
                'status_code': status.HTTP_503_SERVICE_UNAVAILABLE
            }
        except Exception as e:
            self.logger.error(f"檔案分析執行失敗: {e}")
            return {
                'success': False,
                'error': f'檔案分析執行錯誤: {str(e)}',
                'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR
            }
    
    def _process_ai_response_and_save_ocr(self, analysis_result, uploaded_file, user, message):
        """處理 AI 回應並保存 OCR 結果"""
        try:
            from library.data_processing.ocr_analyzer import (
                create_ocr_analyzer,
                create_ocr_database_manager
            )
            from library.data_processing.text_processor import extract_project_name
            
            self.logger.info("開始執行 OCR 分析和資料庫保存...")
            
            # 創建分析器和資料庫管理器
            ocr_analyzer = create_ocr_analyzer()
            ocr_db_manager = create_ocr_database_manager()
            
            # 解析 AI 回答
            ai_answer = analysis_result.get('answer', '')
            self.logger.debug(f"AI 回答內容長度: {len(ai_answer)} 字符")
            
            parsed_data = ocr_analyzer.parse_storage_benchmark_table(ai_answer)
            self.logger.info(f"解析結果: {parsed_data}")
            
            # 如果解析成功，保存到資料庫
            if parsed_data:
                # 從訊息中提取專案名稱
                extracted_project_name = extract_project_name(message) if message else None
                
                save_result = ocr_db_manager.save_benchmark_data(
                    parsed_data,
                    original_image_data=uploaded_file.read(),
                    original_image_filename=uploaded_file.name,
                    original_image_content_type=uploaded_file.content_type,
                    ai_raw_text=ai_answer,
                    uploaded_by=user if user and user.is_authenticated else None,
                    project_name=extracted_project_name
                )
                
                self.logger.info(f"OCR 分析和保存完成: {save_result}")
                return save_result
            
            return None
            
        except ImportError as e:
            self.logger.warning(f"OCR 分析功能不可用: {e}")
            return None
        except Exception as e:
            self.logger.error(f"OCR 分析錯誤: {str(e)}")
            return {
                'success': False,
                'error': f'OCR 分析失敗: {str(e)}'
            }


class AIOCRChatServiceFallback:
    """AI OCR 聊天服務備用實現"""
    
    def __init__(self):
        self.logger = logger
        
    def handle_ocr_chat_request(self, message, conversation_id='', user=None):
        """備用的 OCR 聊天處理"""
        self.logger.warning("使用 AI OCR 聊天服務備用實現")
        
        return {
            'success': False,
            'error': 'AI OCR 聊天服務暫時不可用，請稍後再試或聯絡管理員',
            'status_code': status.HTTP_503_SERVICE_UNAVAILABLE
        }
    
    def handle_file_analysis_request(self, uploaded_file, message='', user=None):
        """備用的檔案分析處理"""
        self.logger.warning("使用 AI OCR 檔案分析服務備用實現")
        
        return {
            'success': False,
            'error': 'AI OCR 檔案分析服務暫時不可用，請稍後再試或聯絡管理員',
            'status_code': status.HTTP_503_SERVICE_UNAVAILABLE
        }


# 便利函數
def create_ai_ocr_chat_service():
    """創建 AI OCR 聊天服務實例"""
    try:
        return AIOCRChatService()
    except Exception as e:
        logger.warning(f"無法創建 AI OCR 聊天服務，使用備用實現: {e}")
        return AIOCRChatServiceFallback()