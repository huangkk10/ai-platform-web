#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Report Analyzer 3 完整工作流程 API 調用
模擬 Dify 工作流：觸發執行 -> 上傳文件 -> Chat 發送
"""

import sys
import os
import requests
import json
import time
from datetime import datetime

# 添加項目根目錄到 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from library.config.dify_app_configs import get_report_analyzer_3_config


class ReportAnalyzerWorkflow:
    """Report Analyzer 3 聊天分析器"""
    
    def __init__(self):
        """初始化"""
        self.config = get_report_analyzer_3_config()
        self.session = requests.Session()
        self.conversation_id = ""
        
        print(f"🔧 初始化 Report Analyzer 3 聊天分析器")
        print(f"工作室: {self.config['workspace']}")
        print(f"API URL: {self.config['api_url']}")
        print(f"Base URL: {self.config['base_url']}")
        print(f"🏷️  注意：這是聊天應用，不是工作流應用")
    
    def step_1_init_chat(self):
        """步驟 1: 初始化聊天會話（可選步驟）"""
        print(f"\n🚀 步驟 1: 初始化聊天會話")
        print(f"🎯 模擬：開啟 Dify 工作室聊天界面")
        
        try:
            headers = {
                "Authorization": f"Bearer {self.config['api_key']}",
                "Content-Type": "application/json"
            }
            
            # 簡單的初始化聊天（可選）
            init_data = {
                "inputs": {},
                "query": "你好",
                "response_mode": "blocking",
                "conversation_id": "",
                "user": "test_user"
            }
            
            response = self.session.post(
                self.config['api_url'],
                json=init_data,
                headers=headers,
                timeout=30
            )
            
            print(f"初始化響應狀態: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                if 'conversation_id' in response_data:
                    self.conversation_id = response_data['conversation_id']
                    print(f"✅ 聊天會話初始化成功，會話 ID: {self.conversation_id}")
                    
                    if 'answer' in response_data:
                        print(f"🤖 AI 回應: {response_data['answer'][:100]}...")
                    
                    return True
                else:
                    print(f"⚠️ 無法獲取會話 ID，將使用空會話 ID")
                    return True  # 即使沒有會話 ID 也繼續
            else:
                print(f"⚠️ 會話初始化失敗，將嘗試不使用會話 ID: {response.text[:100]}...")
                return True  # 繼續嘗試，不阻塞流程
                
        except Exception as e:
            print(f"⚠️ 初始化聊天會話時發生錯誤: {str(e)}")
            print("將繼續嘗試不使用會話 ID")
            return True  # 不阻塞流程
    
    def step_2_upload_file(self, file_path):
        """步驟 2: 上傳文件"""
        print(f"\n📁 步驟 2: 上傳文件")
        
        try:
            upload_url = f"{self.config['base_url']}/v1/files/upload"
            
            headers = {
                "Authorization": f"Bearer {self.config['api_key']}"
            }
            
            file_name = os.path.basename(file_path)
            print(f"上傳文件: {file_name}")
            
            # 根據文件類型設置 MIME 類型
            file_ext = os.path.splitext(file_path)[1].lower()
            mime_types = {
                '.txt': 'text/plain',
                '.log': 'text/plain',
                '.csv': 'text/csv',
                '.json': 'application/json',
                '.pdf': 'application/pdf'
            }
            mime_type = mime_types.get(file_ext, 'text/plain')
            
            with open(file_path, 'rb') as f:
                files = {
                    'file': (file_name, f, mime_type)
                }
                
                data = {
                    'user': 'file_upload_user'
                }
                
                response = self.session.post(
                    upload_url,
                    files=files,
                    data=data,
                    headers=headers,
                    timeout=60
                )
                
                print(f"上傳響應狀態: {response.status_code}")
                
                if response.status_code == 201:
                    upload_data = response.json()
                    file_id = upload_data.get('id')
                    print(f"✅ 文件上傳成功！文件 ID: {file_id}")
                    return file_id
                else:
                    print(f"❌ 文件上傳失敗: {response.text[:200]}...")
                    return None
                    
        except Exception as e:
            print(f"❌ 上傳文件時發生錯誤: {str(e)}")
            return None
    
    def step_3_send_chat_with_file(self, file_id, file_path, query):
        """步驟 3: 使用文件進行聊天分析（模擬 Dify 工作室聊天界面）"""
        print(f"\n💬 步驟 3: 發送聊天請求進行分析")
        print(f"🎯 模擬流程：在聊天界面上傳文件 -> 發送聊天消息")
        
        try:
            headers = {
                "Authorization": f"Bearer {self.config['api_key']}",
                "Content-Type": "application/json"
            }
            
            file_name = os.path.basename(file_path)
            file_ext = os.path.splitext(file_path)[1].lower().lstrip('.')  # 移除點號
            print(f"📝 分析查詢: {query}")
            print(f"📎 關聯文件: {file_name} (ID: {file_id})")
            print(f"📁 文件擴展名: {file_ext}")
            
            # 根據錯誤信息，應用需要特定的輸入變數
            chat_formats = [
                # 格式 1: 使用標準 Dify 文件上傳格式
                {
                    "inputs": {
                        "1752737089886": file_id,
                        "report": [
                            {
                                "transfer_method": "local_file",
                                "upload_file_id": file_id,
                                "type": "image" if file_ext in ['png', 'jpg', 'jpeg'] else "document"
                            }
                        ],
                        "extension": file_ext
                    },
                    "query": query,
                    "response_mode": "blocking",
                    "conversation_id": "",
                    "user": "chat_user"
                },
                # 格式 2: 使用 document 類型
                {
                    "inputs": {
                        "report": [
                            {
                                "transfer_method": "local_file",
                                "upload_file_id": file_id,
                                "type": "document"
                            }
                        ],
                        "extension": file_ext
                    },
                    "query": query,
                    "response_mode": "blocking",
                    "conversation_id": "",
                    "user": "chat_user"
                },
                # 格式 3: 簡化格式，直接使用文件 ID
                {
                    "inputs": {
                        "1752737089886": "report_session",
                        "report": [file_id],
                        "extension": file_ext
                    },
                    "query": query,
                    "response_mode": "blocking",
                    "conversation_id": "",
                    "user": "chat_user"
                },
                # 格式 4: 使用 image 類型（如果是圖片）
                {
                    "inputs": {
                        "report": [
                            {
                                "transfer_method": "local_file",
                                "upload_file_id": file_id,
                                "type": "image"
                            }
                        ],
                        "extension": file_ext
                    },
                    "query": query,
                    "response_mode": "blocking",
                    "conversation_id": "",
                    "user": "chat_user"
                },
                # 格式 5: 不使用數組格式
                {
                    "inputs": {
                        "1752737089886": file_id,
                        "report": {
                            "transfer_method": "local_file",
                            "upload_file_id": file_id,
                            "type": "image" if file_ext in ['png', 'jpg', 'jpeg'] else "document"
                        },
                        "extension": file_ext
                    },
                    "query": query,
                    "response_mode": "blocking",
                    "conversation_id": "",
                    "user": "chat_user"
                }
            ]
            
            for i, chat_data in enumerate(chat_formats, 1):
                print(f"\n🔄 嘗試聊天格式 {i}...")
                print(f"   會話ID: {chat_data.get('conversation_id', '無')}")
                print(f"   輸入變數: {list(chat_data.get('inputs', {}).keys())}")
                print(f"   文件引用: {'是' if 'files' in chat_data else '否'}")
                
                response = self.session.post(
                    self.config['api_url'],
                    json=chat_data,
                    headers=headers,
                    timeout=self.config['timeout']
                )
                
                print(f"   響應狀態: {response.status_code}")
                
                if response.status_code == 200:
                    response_data = response.json()
                    if 'answer' in response_data:
                        answer = response_data['answer']
                        print(f"✅ 聊天分析成功！使用格式 {i}")
                        
                        # 更新會話 ID
                        if 'conversation_id' in response_data:
                            self.conversation_id = response_data['conversation_id']
                            print(f"🔄 更新會話 ID: {self.conversation_id}")
                        
                        return answer
                    else:
                        print(f"⚠️ 響應無答案字段: {list(response_data.keys())}")
                else:
                    try:
                        error_data = response.json()
                        error_text = f"Code: {error_data.get('code', 'unknown')}, Message: {error_data.get('message', 'unknown')}"
                    except:
                        error_text = response.text[:200] if response.text else "無錯誤信息"
                    print(f"   錯誤: {error_text}")
            
            print(f"❌ 所有聊天格式都失敗")
            return None
            
        except Exception as e:
            print(f"❌ 聊天分析時發生錯誤: {str(e)}")
            return None
    
    def run_complete_workflow(self, file_path, query=None):
        """運行完整的聊天分析流程（模擬 Dify 工作室操作）"""
        print(f"\n{'='*60}")
        print(f"🔄 開始 Report Analyzer 3 聊天分析流程")
        print(f"🎯 模擬 Dify 工作室操作：打開預覽 -> 上傳文件 -> 發送聊天")
        print(f"{'='*60}")
        print(f"文件: {file_path}")
        print(f"時間: {datetime.now()}")
        
        # 檢查文件是否存在
        if not os.path.exists(file_path):
            print(f"❌ 文件不存在: {file_path}")
            return None
        
        file_size = os.path.getsize(file_path) / 1024  # KB
        print(f"文件大小: {file_size:.1f} KB")
        
        # 設置默認查詢
        if not query:
            query = f"請分析這個文件，提供詳細的分析結果、發現的問題和改進建議。"
        
        # 步驟 1: 初始化聊天會話（模擬打開工作室）
        print(f"\n📱 模擬操作：點擊 Dify 工作室「預覽」按鈕")
        init_success = self.step_1_init_chat()
        if not init_success:
            print("⚠️ 聊天會話初始化失敗，但繼續嘗試後續步驟...")
        
        # 等待界面載入
        time.sleep(1)
        
        # 步驟 2: 上傳文件（模擬在聊天界面上傳文件）
        print(f"\n📎 模擬操作：在聊天界面點擊文件上傳按鈕")
        file_id = self.step_2_upload_file(file_path)
        if not file_id:
            print("❌ 文件上傳失敗，無法繼續分析")
            return None
        
        # 等待文件處理完成
        print(f"⏳ 等待文件處理完成...")
        time.sleep(2)
        
        # 步驟 3: 發送聊天消息（模擬輸入問題並點擊發送）
        print(f"\n💬 模擬操作：在聊天輸入框輸入問題並點擊發送")
        result = self.step_3_send_chat_with_file(file_id, file_path, query)
        
        return result


def main():
    """主程式"""
    print("🚀 Report Analyzer 3 聊天分析測試")
    print("模擬 Dify 聊天應用：初始化 -> 上傳 -> 聊天")
    print("="*60)
    
    # 初始化聊天分析器
    workflow = ReportAnalyzerWorkflow()
    
    # 設置固定的測試文件路徑
    current_dir = os.path.dirname(os.path.abspath(__file__))
    test_file = os.path.join(current_dir, "2.png")
    
    print(f"\n📄 使用測試文件: {test_file}")
    
    # 檢查文件是否存在
    if not os.path.exists(test_file):
        print(f"❌ 測試文件不存在: {test_file}")
        print("正在創建測試圖片...")
        
        # 創建測試圖片
        try:
            try:
                from PIL import Image, ImageDraw
                pil_available = True
            except ImportError:
                pil_available = False
            
            if pil_available:
                # 創建一個簡單的測試圖片
                img = Image.new('RGB', (400, 300), color='white')
                draw = ImageDraw.Draw(img)
                
                # 添加一些文字和圖形
                draw.rectangle([50, 50, 350, 100], fill='lightblue', outline='blue', width=2)
                draw.text((60, 65), 'System Report - 2024', fill='black')
                draw.text((60, 120), 'CPU Usage: 75%', fill='red')
                draw.text((60, 150), 'Memory Usage: 68%', fill='orange')
                draw.text((60, 180), 'Disk Usage: 45%', fill='green')
                draw.text((60, 210), 'Status: Normal Operation', fill='blue')
                
                # 添加一個圓形
                draw.ellipse([280, 120, 340, 180], fill='yellow', outline='orange', width=3)
                draw.text((295, 145), 'OK', fill='black')
                
                # 保存圖片
                img.save(test_file)
                print(f"✅ 測試圖片已創建: {test_file}")
            else:
                print("❌ 無法創建測試圖片，需要安裝 Pillow 庫")
                print("創建文本文件作為替代...")
                
                # 創建文本文件作為替代
                test_file = os.path.join(current_dir, "test_report.txt")
                test_content = """系統性能報告
================
日期: 2024-09-18
監控時間: 09:00-17:00

系統指標:
- CPU 使用率: 75% (警告: 超過 70% 閾值)
- 內存使用率: 68%
- 磁盤使用率: 45%
- 網絡延遲: 平均 50ms

錯誤日誌:
10:30:25 ERROR Database connection timeout
10:31:12 ERROR API response timeout 
10:32:05 WARNING High memory usage detected

建議:
1. 優化數據庫連接池
2. 增加服務器內存
3. 監控網絡延遲
"""
                
                with open(test_file, 'w', encoding='utf-8') as f:
                    f.write(test_content)
                print(f"✅ 創建測試文件: {test_file}")
                
        except Exception as e:
            print(f"❌ 創建測試文件失敗: {str(e)}")
            return
    
    # 根據文件類型設置查詢
    file_ext = os.path.splitext(test_file)[1].lower()
    is_image = file_ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']
    
    if is_image:
        print("📷 檢測到圖片文件")
        default_query = "請分析這張圖片，描述圖片內容，識別其中的文字信息，並評估顯示的系統狀態是否正常。"
    else:
        print("📄 檢測到文本文件")
        default_query = "請詳細分析這個系統報告，指出主要問題、風險評估和改進建議。"
    
    print(f"📝 預設分析查詢: {default_query}")
    
    # 運行完整分析流程
    result = workflow.run_complete_workflow(test_file, default_query)
    
    # 顯示結果
    print(f"\n{'='*60}")
    print(f"🎯 聊天分析執行結果")
    print(f"{'='*60}")
    
    if result:
        print("✅ 分析執行成功！")
        print(f"\n🤖 AI 分析結果:")
        print("="*40)
        print(result)
        print("="*40)
        
        # 統計結果
        print(f"\n📊 結果統計:")
        print(f"回答長度: {len(result)} 字符")
        print(f"包含關鍵詞: {[kw for kw in ['分析', '建議', '問題', '風險', '優化'] if kw in result]}")
        
    else:
        print("❌ 分析執行失敗")
        print("\n💡 可能的原因:")
        print("1. Report Analyzer 3 應用配置不正確")
        print("2. 文件格式不被支援")
        print("3. 聊天 API 調用參數不正確")
        print("4. 網絡連接或服務問題")
        print("5. 應用需要特定的輸入變數或文件格式")
        print("\n🔧 建議:")
        print("1. 檢查 Dify 應用的具體配置要求")
        print("2. 確認應用是否為聊天模式")
        print("3. 查看 Dify 官方文檔關於文件上傳和聊天 API")
        print("4. 檢查應用是否啟用了文件上傳功能")
    
    print(f"\n程式執行完成")


if __name__ == "__main__":
    main()