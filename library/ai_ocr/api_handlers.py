"""
AI OCR API 處理器

統一處理所有 AI OCR 相關的 API 端點：
- Dify OCR 聊天 API  
- Dify 檔案分析 API (chat with file)
- OCR Storage Benchmark 搜索 API

減少 views.py 中的程式碼量，提供統一的 API 處理入口
"""

import json
import logging
import time
import tempfile
import os
from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class AIOCRAPIHandler:
    """AI OCR API 處理器 - 統一管理所有 AI OCR API"""
    
    @staticmethod
    def handle_dify_ocr_chat_api(request):
        """
        處理 Dify OCR 聊天 API
        
        取代原本 views.py 中的 dify_ocr_chat 函數
        """
        try:
            # 記錄請求來源
            logger.info(f"Dify OCR chat request from: {request.META.get('REMOTE_ADDR')}")
            
            data = request.data
            message = data.get('message', '').strip()
            conversation_id = data.get('conversation_id', '')
            
            if not message:
                return Response({
                    'success': False,
                    'error': '訊息內容不能為空'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 使用 Report Analyzer 3 配置（專門用於 AI OCR）
            try:
                from library.config.dify_config_manager import get_report_analyzer_config
                dify_config = get_report_analyzer_config()
            except Exception as config_error:
                logger.error(f"Failed to load Report Analyzer 3 config: {config_error}")
                return Response({
                    'success': False,
                    'error': f'AI OCR 配置載入失敗: {str(config_error)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # 檢查必要配置
            api_url = dify_config.api_url
            api_key = dify_config.api_key
            
            if not api_url or not api_key:
                return Response({
                    'success': False,
                    'error': 'AI OCR API 配置不完整'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # 記錄請求
            logger.info(f"AI OCR chat request from user: {request.user.username if request.user.is_authenticated else 'guest'}")
            logger.debug(f"AI OCR message: {message[:100]}...")
            
            # 準備請求
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'inputs': {},
                'query': message,
                'response_mode': 'blocking',
                'user': f"ocr_user_{request.user.id if request.user.is_authenticated else 'guest'}"
            }
            
            if conversation_id:
                payload['conversation_id'] = conversation_id
            
            start_time = time.time()
            
            # 使用 library 中的 Dify 請求管理器
            try:
                import requests
                response = requests.post(
                    api_url,
                    headers=headers,
                    json=payload,
                    timeout=120  # AI OCR 分析可能需要較長時間
                )
            except requests.exceptions.Timeout:
                return Response({
                    'success': False,
                    'error': 'AI OCR 分析超時，請稍後再試'
                }, status=status.HTTP_408_REQUEST_TIMEOUT)
            except requests.exceptions.ConnectionError:
                return Response({
                    'success': False,
                    'error': 'AI OCR 連接失敗，請檢查網路連接'
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            except Exception as req_error:
                return Response({
                    'success': False,
                    'error': f'AI OCR API 請求錯誤: {str(req_error)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                
                # 記錄成功的聊天
                logger.info(f"AI OCR chat success for user {request.user.username if request.user.is_authenticated else 'guest'}: {message[:50]}...")
                
                # 直接使用原始的 AI 回答，不進行增強處理
                answer = result.get('answer', '')
                metadata = result.get('metadata', {})
                
                return Response({
                    'success': True,
                    'answer': answer,
                    'conversation_id': result.get('conversation_id', ''),
                    'message_id': result.get('message_id', ''),
                    'response_time': elapsed,
                    'metadata': metadata,
                    'usage': result.get('usage', {})
                }, status=status.HTTP_200_OK)
            else:
                # 特殊處理 404 錯誤（對話不存在）
                if response.status_code == 404:
                    try:
                        response_data = response.json()
                        if 'Conversation Not Exists' in response_data.get('message', ''):
                            logger.warning("AI OCR conversation not exists, should retry without conversation_id")
                    except Exception as retry_error:
                        logger.error(f"AI OCR retry request failed: {str(retry_error)}")
                
                error_msg = f"AI OCR API 錯誤: {response.status_code} - {response.text}"
                logger.error(f"AI OCR chat error: {error_msg}")
                
                return Response({
                    'success': False,
                    'error': error_msg,
                    'response_time': elapsed
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"AI OCR chat API error: {str(e)}")
            return Response({
                'success': False,
                'error': f'AI OCR 服務器錯誤: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @staticmethod
    def handle_dify_chat_with_file_api(request):
        """
        處理 Dify 檔案分析 API (chat with file)
        
        取代原本 views.py 中的 dify_chat_with_file 函數
        """
        try:
            from library.dify_integration import create_report_analyzer_client
            from library.config.dify_config_manager import get_report_analyzer_config
            from library.data_processing.file_utils import (
                get_file_info, 
                validate_file_for_upload, 
                get_default_analysis_query
            )
            from library.data_processing.ocr_analyzer import (
                create_ocr_analyzer,
                create_ocr_database_manager
            )
            from library.data_processing.text_processor import extract_project_name
            
            message = request.data.get('message', '').strip()
            conversation_id = request.data.get('conversation_id', '')
            uploaded_file = request.FILES.get('file')
            
            # 從用戶訊息中提取 project name
            extracted_project_name = extract_project_name(message) if message else None
            
            # 檢查是否有文件或消息
            if not message and not uploaded_file:
                return Response({
                    'success': False,
                    'error': '需要提供訊息內容或圖片文件'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 如果有文件，進行文件分析
            if uploaded_file:
                try:
                    # 1. 保存臨時文件
                    temp_dir = tempfile.mkdtemp()
                    temp_file_path = os.path.join(temp_dir, uploaded_file.name)
                    
                    with open(temp_file_path, 'wb+') as temp_file:
                        for chunk in uploaded_file.chunks():
                            temp_file.write(chunk)
                    
                    # 2. 驗證文件
                    is_valid, error_msg = validate_file_for_upload(temp_file_path, max_size_mb=10)
                    if not is_valid:
                        os.remove(temp_file_path)
                        os.rmdir(temp_dir)
                        return Response({
                            'success': False,
                            'error': f'文件驗證失敗: {error_msg}'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    # 3. 獲取文件信息
                    file_info = get_file_info(temp_file_path)
                    
                    # 4. 生成查詢（如果沒有提供消息，使用默認查詢）
                    query = message if message else get_default_analysis_query(temp_file_path)
                    
                    # 5. 使用 library 進行分析
                    config = get_report_analyzer_config()
                    client = create_report_analyzer_client(
                        config.api_url,
                        config.api_key,
                        config.base_url
                    )
                    
                    start_time = time.time()
                    
                    # 6. 執行分析
                    result = client.upload_and_analyze(
                        temp_file_path, 
                        query, 
                        user=f"web_user_{request.user.id if request.user.is_authenticated else 'guest'}",
                        verbose=True
                    )
                    
                    elapsed = time.time() - start_time
                    
                    # 7. AI 回覆後自動執行 OCR 解析和保存
                    ocr_analysis_result = None
                    if result['success'] and result.get('answer'):
                        try:
                            logger.info("開始執行 OCR 分析和資料庫保存...")
                            
                            # 創建 OCR 分析器和資料庫管理器
                            ocr_analyzer = create_ocr_analyzer()
                            ocr_db_manager = create_ocr_database_manager()
                            
                            # 解析 AI 回答中的測試資料
                            ai_answer = result.get('answer', '')
                            logger.debug(f"AI 回答內容長度: {len(ai_answer)} 字符")
                            
                            parsed_data = ocr_analyzer.parse_storage_benchmark_table(ai_answer)
                            logger.info(f"解析結果: {parsed_data}")
                            
                            # 如果解析成功，保存到資料庫
                            if parsed_data:
                                save_result = ocr_db_manager.save_benchmark_data(
                                    parsed_data,
                                    original_image_data=uploaded_file.read(),
                                    original_image_filename=uploaded_file.name,
                                    original_image_content_type=uploaded_file.content_type,
                                    ai_raw_text=ai_answer,
                                    uploaded_by=request.user if request.user.is_authenticated else None,
                                    project_name=extracted_project_name
                                )
                                ocr_analysis_result = save_result
                                logger.info(f"OCR 分析和保存完成: {save_result}")
                            
                        except Exception as ocr_error:
                            logger.error(f"OCR 分析錯誤: {str(ocr_error)}")
                            ocr_analysis_result = {
                                'success': False,
                                'error': f'OCR 分析失敗: {str(ocr_error)}'
                            }
                    
                    # 8. 清理臨時文件
                    os.remove(temp_file_path)
                    os.rmdir(temp_dir)
                    
                    # 9. 返回結果（包含 OCR 分析結果）
                    if result['success']:
                        logger.info(f"File analysis success for user {request.user.username}: {uploaded_file.name}")
                        
                        response_data = {
                            'success': True,
                            'answer': result.get('answer', ''),
                            'conversation_id': result.get('conversation_id', ''),
                            'message_id': result.get('message_id', ''),
                            'response_time': elapsed,
                            'metadata': result.get('metadata', {}),
                            'usage': result.get('usage', {}),
                            'file_info': {
                                'name': file_info['file_name'],
                                'size': file_info['file_size'],
                                'type': 'image' if file_info['is_image'] else 'document'
                            }
                        }
                        
                        # 如果有 OCR 分析結果，添加到響應中
                        if ocr_analysis_result:
                            response_data['ocr_analysis'] = ocr_analysis_result
                        
                        return Response(response_data, status=status.HTTP_200_OK)
                    else:
                        return Response({
                            'success': False,
                            'error': result.get('error', '文件分析失敗'),
                            'response_time': elapsed
                        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                        
                except Exception as e:
                    # 清理臨時文件
                    if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
                    if 'temp_dir' in locals() and os.path.exists(temp_dir):
                        os.rmdir(temp_dir)
                    
                    logger.error(f"File analysis error: {str(e)}")
                    return Response({
                        'success': False,
                        'error': f'文件分析錯誤: {str(e)}'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # 如果沒有文件，回退到普通聊天模式
            else:
                return Response({
                    'success': False,
                    'error': '此 API 需要上傳文件進行分析'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Dify chat with file API error: {str(e)}")
            return Response({
                'success': False,
                'error': f'服務器錯誤: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @staticmethod
    def handle_dify_ocr_storage_benchmark_search_api(request):
        """
        處理 Dify OCR Storage Benchmark 搜索 API
        
        取代原本 views.py 中的 dify_ocr_storage_benchmark_search 函數
        """
        try:
            # 記錄請求來源
            logger.info(f"Dify OCR Storage Benchmark API request from: {request.META.get('REMOTE_ADDR')}")
            
            # 解析請求數據
            data = json.loads(request.body) if request.body else {}
            query = data.get('query', '')
            knowledge_id = data.get('knowledge_id', 'ocr_storage_benchmark')
            retrieval_setting = data.get('retrieval_setting', {})
            
            top_k = retrieval_setting.get('top_k', 5)
            score_threshold = retrieval_setting.get('score_threshold', 0.0)
            
            logger.info(f"OCR Storage Benchmark search - Query: '{query}', Top K: {top_k}, Score threshold: {score_threshold}")
            
            # 驗證必要參數
            if not query:
                return Response({
                    'error_code': 2001,
                    'error_msg': 'Query parameter is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 使用統一的搜索服務
            from .search_service import AIOCRSearchService
            search_service = AIOCRSearchService()
            search_results = search_service.search_ocr_storage_benchmark(query, limit=top_k)
            
            # 過濾分數低於閾值的結果
            filtered_results = [
                result for result in search_results 
                if result['score'] >= score_threshold
            ]
            
            logger.info(f"OCR Storage Benchmark search found {len(search_results)} results, {len(filtered_results)} after filtering")
            
            # 構建符合 Dify 規格的響應
            records = []
            for result in filtered_results:
                record = {
                    'content': result['content'],
                    'score': result['score'],
                    'title': result['title'],
                    'metadata': result['metadata']
                }
                records.append(record)
                logger.info(f"Added OCR Benchmark record: {record['title']}")
            
            response_data = {
                'records': records
            }
            
            logger.info(f"OCR Storage Benchmark API response: Found {len(records)} results")
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except json.JSONDecodeError:
            return Response({
                'error_code': 1001,
                'error_msg': 'Invalid JSON format'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Dify OCR Storage Benchmark search error: {str(e)}")
            return Response({
                'error_code': 2001,
                'error_msg': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)