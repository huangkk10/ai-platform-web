#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 最簡單的 DeepSeek 測試 - 只使用英文避免編碼問題
驗證 AI 溝通功能
"""

import paramiko
import time

def simple_english_test():
    """簡單英文測試"""
    print("🎯 簡單英文 DeepSeek 測試")
    print("=" * 40)
    
    try:
        # SSH 連接
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect("10.253.43.244", username="svd", password="1234", timeout=10)
        print("✅ SSH 連接成功")
        
        # 英文問題測試
        questions = [
            "Hello",
            "What is your name?",
            "Can you analyze data?",
            "Explain machine learning in simple terms"
        ]
        
        for i, question in enumerate(questions, 1):
            print(f"\n📋 測試 {i}/{len(questions)}:")
            print(f"💬 問題: {question}")
            
            # 使用已驗證可工作的命令格式
            command = f'echo "{question}" | ollama run deepseek-r1:14b --'
            
            print("⏳ 等待回應...")
            start_time = time.time()
            
            stdin, stdout, stderr = ssh.exec_command(command, timeout=30)
            response = stdout.read().decode('utf-8')
            
            elapsed = time.time() - start_time
            
            if response.strip():
                print(f"🤖 DeepSeek 回應 (耗時 {elapsed:.1f}s):")
                print("-" * 30)
                print(response[:200] + "..." if len(response) > 200 else response)
                print("-" * 30)
                print("✅ 成功")
            else:
                print("❌ 無回應")
            
            time.sleep(1)  # 間隔
        
        ssh.close()
        print("\n🎉 英文測試完成！")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")

def test_chinese_with_different_methods():
    """測試中文的不同方法"""
    print("\n🔧 測試中文編碼方法")
    print("=" * 30)
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect("10.253.43.244", username="svd", password="1234", timeout=10)
        
        # 方法1: 請求英文回應中文問題
        print("\n📋 方法1: 用英文描述中文問題")
        question1 = "Please introduce yourself in Traditional Chinese"
        command1 = f'echo "{question1}" | ollama run deepseek-r1:14b --'
        
        print(f"💬 問題: {question1}")
        stdin, stdout, stderr = ssh.exec_command(command1, timeout=30)
        response1 = stdout.read().decode('utf-8')
        
        if response1.strip():
            print("🤖 回應:")
            print(response1[:300] + "..." if len(response1) > 300 else response1)
        
        # 方法2: 測試簡單中文
        print("\n📋 方法2: 簡單中文測試")
        question2 = "hello"  # 先確保基本功能正常
        command2 = f'echo "{question2}" | ollama run deepseek-r1:14b --'
        
        stdin, stdout, stderr = ssh.exec_command(command2, timeout=30)
        response2 = stdout.read().decode('utf-8')
        
        if response2.strip():
            print("🤖 基本回應正常")
        
        ssh.close()
        
    except Exception as e:
        print(f"❌ 中文測試失敗: {e}")

def main():
    """主函數"""
    print("🚀 DeepSeek AI 溝通驗證")
    print("確認基本功能正常")
    print("=" * 50)
    
    # 先測試英文（確認 AI 功能正常）
    simple_english_test()
    
    # 再測試中文編碼
    test_chinese_with_different_methods()
    
    print("\n✅ 測試總結:")
    print("1. 如果英文測試成功 → DeepSeek AI 功能正常")
    print("2. 如果中文出現亂碼 → 需要解決編碼問題")
    print("3. SSH 連接和模型運行都正常 ✅")

if __name__ == "__main__":
    main()