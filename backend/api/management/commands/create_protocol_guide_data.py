#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Django 管理命令 - 建立 Protocol Guide 測試數據
"""

from django.core.management.base import BaseCommand
from api.models import ProtocolGuide


class Command(BaseCommand):
    help = '建立 Protocol Guide 測試數據'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== 開始建立 Protocol Guide 測試數據 ===\n'))
        
        # 測試數據
        protocol_guide_data = [
            {
                'title': 'ULINK Protocol 連接測試指南',
                'content': '''ULINK 是一個用於設備連接的協議，主要用於車機系統與手機的連接。

## 測試步驟
1. 確保車機系統已開啟
2. 開啟手機藍牙功能
3. 在車機系統中搜索可用設備
4. 選擇目標手機進行配對
5. 輸入配對碼（如需要）
6. 確認連接成功

## 預期結果
設備成功連接，狀態顯示為 CONNECTED，可以進行數據傳輸。

## 常見問題
- 無法搜索到設備：檢查藍牙是否開啟
- 配對失敗：嘗試重新啟動設備
- 連接不穩定：檢查信號強度''',
            },
            {
                'title': 'Samsung Protocol 測試指南',
                'content': '''Samsung Protocol 是針對三星設備的專用連接協議。

## 基本要求
- 三星設備系統版本 Android 10 以上
- 支援 Samsung Connect 功能
- 車機系統韌體版本 v2.0 以上

## 連接流程
1. 啟動 Samsung Connect 應用
2. 掃描附近的車機系統
3. 選擇目標車機
4. 確認配對請求
5. 等待連接建立

## 功能測試
- 音樂串流
- 電話通話
- 訊息同步
- 導航共享''',
            },
            {
                'title': 'Apple CarPlay 整合測試',
                'content': '''Apple CarPlay 提供 iPhone 與車機系統的無縫整合。

## 前置條件
- iPhone iOS 13 或更高版本
- 支援 CarPlay 的車機系統
- Lightning 或 USB-C 連接線

## 設置步驟
1. 使用 USB 線連接 iPhone 到車機
2. 在 iPhone 上允許 CarPlay 權限
3. 車機螢幕會自動顯示 CarPlay 介面
4. 使用 Siri 或觸控螢幕操作

## 測試項目
- Siri 語音助手
- Apple Maps 導航
- 音樂播放（Apple Music, Spotify）
- 電話和訊息功能
- 第三方應用支援''',
            },
            {
                'title': 'Bluetooth A2DP 音頻測試',
                'content': '''測試藍牙高品質音頻傳輸協議（A2DP）的功能。

## 測試環境
- 藍牙版本：4.0 或更高
- 音頻編碼：SBC, AAC, aptX
- 測試音源：多種格式（MP3, FLAC, AAC）

## 測試流程
1. 配對藍牙設備
2. 播放測試音頻檔案
3. 檢查音質和穩定性
4. 測試音量控制
5. 測試播放控制（播放/暫停/下一首）

## 驗證項目
- 音質清晰無雜音
- 延遲小於 200ms
- 連接穩定不中斷
- 音量控制正常
- 播放控制功能正常''',
            },
            {
                'title': '車機系統 OTA 更新測試',
                'content': '''Over-The-Air (OTA) 更新功能測試指南。

## 更新準備
- 確保網路連接穩定
- 電池電量超過 50%
- 備份重要數據

## 測試步驟
1. 檢查系統版本
2. 前往設定 > 系統更新
3. 點擊檢查更新
4. 下載更新檔案
5. 安裝更新
6. 系統重啟
7. 驗證更新成功

## 注意事項
- 更新過程中不要中斷電源
- 更新可能需要 15-30 分鐘
- 更新後需重新配對藍牙設備

## 驗證重點
- 系統版本正確更新
- 所有功能正常運作
- 數據沒有丟失
- 性能有所提升''',
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for guide_data in protocol_guide_data:
            # 使用 title 來檢查是否已存在
            guide, created = ProtocolGuide.objects.get_or_create(
                title=guide_data['title'],
                defaults=guide_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"✅ 創建文檔: {guide.title}")
                )
            else:
                # 更新現有記錄
                for key, value in guide_data.items():
                    if key != 'title':  # 不更新主鍵
                        setattr(guide, key, value)
                guide.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f"⚠️  更新文檔: {guide.title}")
                )
        
        self.stdout.write('\n' + '='*80)
        self.stdout.write(self.style.SUCCESS(f'✅ Protocol Guide 數據建立完成！'))
        self.stdout.write(self.style.SUCCESS(f'   新建: {created_count} 篇'))
        self.stdout.write(self.style.SUCCESS(f'   更新: {updated_count} 篇'))
        self.stdout.write(self.style.SUCCESS(f'   總計: {created_count + updated_count} 篇'))
        self.stdout.write('='*80 + '\n')
        
        # 統計資料
        total = ProtocolGuide.objects.count()
        self.stdout.write(self.style.SUCCESS(f'📊 資料庫中共有 {total} 篇 Protocol Guide'))
