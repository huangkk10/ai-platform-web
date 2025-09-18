#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 REPORT_ANALYZER_3 聊天功能
使用配置中的設定進行基本聊天測試
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


class ReportAnalyzer3ChatTest:
    """Report Analyzer 3 聊天測試器"""
    
    def __init__(self):
        """初始化"""
        self.config = get_report_analyzer_3_config()
        self.session = requests.Session()
        self.conversation_id = ""
        
        print(f"🔧 初始化 Report Analyzer 3 聊天測試")
        print(f"工作室: {self.config['workspace']}")
        print(f"API URL: {self.config['api_url']}")
        print(f"Base URL: {self.config['base_url']}")
        print(f"API Key: {self.config['api_key'][:12]}...")
    
    def test_basic_chat(self, query):
        """測試基本聊天功能"""
        print(f"\n💬 測試基本聊天功能")
        print(f"查詢: {query}")
        print(f"⚠️ 注意：此應用需要特定變數，基本聊天可能無法工作")
        
        try:
            headers = {
                "Authorization": f"Bearer {self.config['api_key']}",
                "Content-Type": "application/json"
            }
            
            # 嘗試多種基本聊天格式
            chat_formats = [
                # 格式 1: 標準格式
                {
                    "inputs": {},
                    "query": query,
                    "response_mode": "blocking",
                    "conversation_id": self.conversation_id if self.conversation_id else "",
                    "user": "test_user"
                },
                # 格式 2: 提供必需變數但使用空值
                {
                    "inputs": {
                        "1752737089886": "",
                        "report": "",
                        "extension": ""
                    },
                    "query": query,
                    "response_mode": "blocking",
                    "conversation_id": "",
                    "user": "test_user"
                },
                # 格式 3: 提供虛擬變數值
                {
                    "inputs": {
                        "1752737089886": "test_session",
                        "report": "no_file",
                        "extension": "txt"
                    },
                    "query": query,
                    "response_mode": "blocking",
                    "conversation_id": "",
                    "user": "test_user"
                }
            ]
            
            for i, chat_data in enumerate(chat_formats, 1):
                print(f"📤 嘗試格式 {i}: {self.config['api_url']}")
                
                response = self.session.post(
                    self.config['api_url'],
                    json=chat_data,
                    headers=headers,
                    timeout=self.config['timeout']
                )
                
                print(f"📥 響應狀態: {response.status_code}")
                
                if response.status_code == 200:
                    response_data = response.json()
                    
                    # 更新會話 ID
                    if 'conversation_id' in response_data:
                        self.conversation_id = response_data['conversation_id']
                        print(f"🔄 會話 ID: {self.conversation_id}")
                    
                    if 'answer' in response_data:
                        answer = response_data['answer']
                        print(f"✅ 聊天成功！使用格式 {i}")
                        print(f"🤖 AI 回答:")
                        print("="*40)
                        print(answer)
                        print("="*40)
                        return answer
                    else:
                        print(f"⚠️ 響應中沒有 answer 字段")
                        print(f"響應內容: {response_data}")
                else:
                    try:
                        error_data = response.json()
                        print(f"❌ 格式 {i} 失敗: {error_data.get('message', 'Unknown error')}")
                    except:
                        print(f"❌ 格式 {i} 失敗: {response.text[:100]}...")
            
            print(f"❌ 所有聊天格式都失敗")
            return None
                
        except Exception as e:
            print(f"❌ 聊天測試時發生錯誤: {str(e)}")
            return None
    
    def test_file_upload(self, file_path):
        """測試文件上傳功能"""
        print(f"\n📁 測試文件上傳功能")
        print(f"文件路徑: {file_path}")
        
        if not os.path.exists(file_path):
            print(f"❌ 文件不存在: {file_path}")
            return None
        
        try:
            upload_url = f"{self.config['base_url']}/v1/files/upload"
            
            headers = {
                "Authorization": f"Bearer {self.config['api_key']}"
            }
            
            file_name = os.path.basename(file_path)
            file_ext = os.path.splitext(file_path)[1].lower()
            
            # 根據文件類型設置 MIME 類型
            mime_types = {
                '.txt': 'text/plain',
                '.log': 'text/plain',
                '.csv': 'text/csv',
                '.json': 'application/json',
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.pdf': 'application/pdf'
            }
            mime_type = mime_types.get(file_ext, 'application/octet-stream')
            
            print(f"文件名: {file_name}")
            print(f"MIME 類型: {mime_type}")
            
            with open(file_path, 'rb') as f:
                files = {
                    'file': (file_name, f, mime_type)
                }
                
                data = {
                    'user': 'test_user'
                }
                
                print(f"📤 上傳到: {upload_url}")
                
                response = self.session.post(
                    upload_url,
                    files=files,
                    data=data,
                    headers=headers,
                    timeout=60
                )
                
                print(f"📥 上傳響應狀態: {response.status_code}")
                
                if response.status_code == 201:
                    upload_data = response.json()
                    file_id = upload_data.get('id')
                    print(f"✅ 文件上傳成功！")
                    print(f"文件 ID: {file_id}")
                    return file_id
                else:
                    print(f"❌ 文件上傳失敗")
                    print(f"錯誤信息: {response.text[:200]}...")
                    return None
                    
        except Exception as e:
            print(f"❌ 文件上傳時發生錯誤: {str(e)}")
            return None
    
    def test_chat_with_file(self, file_id, file_path, query):
        """測試帶文件的聊天功能"""
        print(f"\n💬📁 測試帶文件的聊天功能")
        print(f"文件 ID: {file_id}")
        print(f"查詢: {query}")
        
        try:
            headers = {
                "Authorization": f"Bearer {self.config['api_key']}",
                "Content-Type": "application/json"
            }
            
            file_name = os.path.basename(file_path)
            file_ext = os.path.splitext(file_path)[1].lower().lstrip('.')
            is_image = file_ext in ['png', 'jpg', 'jpeg', 'gif', 'bmp']
            
            # 使用成功的格式（基於之前的測試結果）
            chat_data = {
                "inputs": {
                    "1752737089886": file_id,
                    "report": {
                        "transfer_method": "local_file",
                        "upload_file_id": file_id,
                        "type": "image" if is_image else "document"
                    },
                    "extension": file_ext
                },
                "query": query,
                "response_mode": "blocking",
                "conversation_id": "",
                "user": "test_user"
            }
            
            print(f"📤 發送文件聊天請求")
            print(f"文件類型: {'圖片' if is_image else '文檔'}")
            
            response = self.session.post(
                self.config['api_url'],
                json=chat_data,
                headers=headers,
                timeout=self.config['timeout']
            )
            
            print(f"📥 響應狀態: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                
                if 'answer' in response_data:
                    answer = response_data['answer']
                    print(f"✅ 文件聊天成功！")
                    print(f"🤖 AI 分析結果:")
                    print("="*40)
                    print(answer)
                    print("="*40)
                    return answer
                else:
                    print(f"⚠️ 響應中沒有 answer 字段")
                    print(f"響應內容: {response_data}")
                    return None
            else:
                print(f"❌ 文件聊天失敗")
                try:
                    error_data = response.json()
                    print(f"錯誤信息: {error_data}")
                except:
                    print(f"錯誤文本: {response.text[:200]}...")
                return None
                
        except Exception as e:
            print(f"❌ 文件聊天測試時發生錯誤: {str(e)}")
            return None
    
    def run_complete_test(self, test_file_path=None):
        """運行完整測試"""
        print(f"\n{'='*60}")
        print(f"🧪 開始 Report Analyzer 3 完整聊天測試")
        print(f"{'='*60}")
        print(f"時間: {datetime.now()}")
        
        # 測試 1: 基本聊天
        # print(f"\n🧪 測試 1: 基本聊天功能")
        # basic_result = self.test_basic_chat("你好，請介紹一下你的功能")
        
        # 測試 2: 文件上傳和聊天（如果提供了文件路徑）
        if test_file_path and os.path.exists(test_file_path):
            print(f"\n🧪 測試 2: 文件上傳和聊天")
            
            # 上傳文件
            file_id = self.test_file_upload(test_file_path)
            
            if file_id:
                # 等待文件處理
                print(f"⏳ 等待文件處理...")
                time.sleep(2)
                
                # 文件聊天
                file_ext = os.path.splitext(test_file_path)[1].lower()
                if file_ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
                    query = "請分析這張圖片的內容，描述你看到的信息"
                else:
                    query = "請分析這個文件的內容，並提供摘要"
                
                file_result = self.test_chat_with_file(file_id, test_file_path, query)
        else:
            print(f"\n⚠️ 跳過文件測試（未提供有效文件路徑）")
        
        # 測試總結
        print(f"\n{'='*60}")
        print(f"🎯 測試總結")
        print(f"{'='*60}")
        
        if basic_result:
            print(f"✅ 基本聊天功能：正常")
        else:
            print(f"❌ 基本聊天功能：失敗")
        
        if test_file_path and os.path.exists(test_file_path):
            if 'file_id' in locals() and locals()['file_id']:
                print(f"✅ 文件上傳功能：正常")
                if 'file_result' in locals() and locals()['file_result']:
                    print(f"✅ 文件分析功能：正常")
                else:
                    print(f"❌ 文件分析功能：失敗")
            else:
                print(f"❌ 文件上傳功能：失敗")
        
        print(f"\n測試完成！")


def main():
    """主程式"""
    print("🧪 Report Analyzer 3 聊天功能測試")
    print("="*60)
    
    # 初始化測試器
    tester = ReportAnalyzer3ChatTest()
    
    # 檢查是否有測試文件
    current_dir = os.path.dirname(os.path.abspath(__file__))
    test_files = [
        os.path.join(current_dir, "3.png"),
        os.path.join(current_dir, "test_report.txt"),
        os.path.join(current_dir, "../test_upload/test_image.png"),
        os.path.join(current_dir, "../test_upload/test_document.txt")
    ]
    
    test_file = None
    for file_path in test_files:
        if os.path.exists(file_path):
            test_file = file_path
            break
    
    if test_file:
        print(f"\n📄 找到測試文件: {test_file}")
        print(f"文件大小: {os.path.getsize(test_file) / 1024:.1f} KB")
    else:
        print(f"\n⚠️ 未找到測試文件，將只測試基本聊天功能")
        print("可用的測試文件位置：")
        for file_path in test_files:
            print(f"  - {file_path}")
    
    # 運行完整測試
    tester.run_complete_test(test_file)


if __name__ == "__main__":
    main()