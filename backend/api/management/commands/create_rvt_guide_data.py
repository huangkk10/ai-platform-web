#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Django 管理命令 - 建立 RVT Guide 測試數據
將 RVT 自動化測試系統使用指南的內容插入到數據庫中
"""

from django.core.management.base import BaseCommand
from api.models import RVTGuide

class Command(BaseCommand):
    help = 'Create RVT Guide test data for Dify external knowledge base'
    
    def handle(self, *args, **options):
        self.stdout.write("🚀 開始建立 RVT Guide 測試數據...")
        
        # RVT Guide 測試數據
        rvt_guide_data = [
            {
                'document_name': 'RVT-系統架構-Jenkins和Ansible概念',
                'title': 'RVT 系統架構概念說明',
                'version': '1.0',
                'main_category': 'system_architecture',
                'sub_category': 'jenkins_ansible_concept',
                'content': '''我們的測試自動化系統主要由兩大核心元件構成：Jenkins 和 Ansible。

Jenkins： 如同自動化流程的指揮中心。它負責排程、觸發並監控整個測試流程的執行。您可以把它想像成一位專案經理，確保各項測試任務按計劃進行。

Ansible： 則是實際執行任務的得力助手。它負責設定測試環境、在目標裝置上執行測試腳本，並收集相關資訊。您可以把它想像成一位技術嫻熟的工程師，能夠精準地完成各種遠端操作。

這兩者協同工作：Jenkins 會根據您的設定或特定觸發條件 (例如新的韌體版本釋出)，指示 Ansible 在指定的測試裝置上執行一系列的自動化任務，包括環境準備、韌體更新、測試項目執行等。''',
                'keywords': 'RVT,系統架構,Jenkins,Ansible,自動化,測試系統,流程控制',
                'question_type': 'concept_explanation',
                'target_user': 'beginner',
                'status': 'published'
            },
            {
                'document_name': 'RVT-操作流程-Jenkins測試階段',
                'title': '解讀 Jenkins 測試階段 (Stages)',
                'version': '1.0',
                'main_category': 'operation_flow',
                'sub_category': 'jenkins_stages',
                'content': '''一個 Jenkins 測試專案通常會被劃分成數個「階段」(Stages)，每個階段代表測試流程中的一個主要步驟。

**Poll (輪詢)**
用途： 此階段會自動檢查是否有韌體版本偵測到上傳，自動觸發後續的測試流程，如果24小時內沒有偵測到上傳，則Timeout離開，上傳韌體格式封裝需要為.7z，不接受其它壓縮格式。

**UART (UART日誌)**
用途： 擷取測試裝置在執行期間透過 UART Board 輸出的底層日誌。這對於除錯硬體相關或韌體啟動初期的問題至關重要。
控制參數： Jenkins 專案執行時，通常可以透過參數來決定 UART 的行為：
- Both：InitCard 和 Test 都記錄
- InitCard：僅在執行「開卡」任務時記錄
- Test：僅在執行主要測試時記錄
- None：不記錄 UART 日誌

**InitCard (開卡)**
用途： 將 SSD 重新開卡，為後續的測試做準備，可選擇ROM Mode 或 ISP Mode 進行開卡。
display.log： 執行 automp 工具時可能會產生此日誌檔，記錄詳細的初始化過程和結果。如果 InitCard 階段失敗，此日誌是首要的排查依據。

**Deploy (部署作業系統)**
用途： 在目標測試系統上自動安裝和設定作業系統。這對於需要特定作業系統環境的測試非常重要。

**FFU (韌體更新)**
用途： 將新的韌體版本刷入到測試裝置中。

**SETUP (測試平台設定)**
用途： 在執行實際測試之前，進行必要待測系統的環境設定或配置。

**Test (執行測試)**
用途： 此階段會實際執行定義好的測項，以驗證SSD的功能、效能、穩定性等。''',
                'keywords': 'Jenkins,測試階段,Poll,輪詢,UART,日誌,InitCard,開卡,Deploy,部署,FFU,韌體更新,SETUP,測試平台,Test,執行測試',
                'question_type': 'operation_guide',
                'target_user': 'all',
                'status': 'published'
            },
            {
                'document_name': 'RVT-環境準備-先決條件',
                'title': '系統安裝前的先決條件',
                'version': '1.0',
                'main_category': 'environment_setup',
                'sub_category': 'network_requirements',
                'content': '''在開始安裝與操作本系統前，請確保以下條件已準備完成：

**網路環境**
- 需 MDT VLAN（請聯絡 IT 申請）
- DHCP 伺服器
- MDT Web 服務
- iPXE + BootImage 2.0
- iPXE-Mac（僅 RVT 2.0 需要）
- NAS：10.250.0.1

**MDT 配置（請向 PQ1-3 / TAS team 確認）**
- MDT 可正常運作
- 安裝 MDT Application 2.0
- 已建立 MDT Task Sequence 2.0

**UART Board 硬體需求（型號：FT4232_M039 a.k.a 黑色UART board）**
- UART Log 軟排
- Power Switch 杜邦線接線
- ROM Mode 杜邦線接線 (詳細接法請參考 Remote Force Rom Setting By Colin)
- (可選) JTAG 接線 (詳細接法請參考 Jtag & PCIe Dump使用方法)

**測試平台系統設定（由使用者安裝）**
- 安裝 OpenSSH：OpenSSH-Win64-v9.8.1.0.msi
- 關閉作業系統防火牆

**主機板 BIOS 設定：啟用 iPXE 開機（由使用者設定）**
進入BIOS 設定畫面，啟用 PXE 網路介面卡開機選項。''',
                'keywords': '先決條件,環境準備,MDT,VLAN,UART,Board,FT4232,OpenSSH,iPXE,BIOS,PXE,網路介面卡',
                'question_type': 'operation_guide',
                'target_user': 'admin',
                'status': 'published'
            },
            {
                'document_name': 'RVT-配置管理-Ansible設定',
                'title': 'Ansible 配置與參數設定',
                'version': '1.0',
                'main_category': 'configuration_management',
                'sub_category': 'machine_configuration',
                'content': '''設定有三大部分：設定、測試平台、測項。本節將詳細說明 Ansible 的設定方式，因為它是自動化測試執行的核心。

**設定的 NAS 路徑**
準備一個如下的 NAS 目錄 放置所需config

```
\\10.250.0.1\\mdt\\Team\\Reliability\\Springsteen\\inventory
│
├── hosts                  # 測試平台 ini 設定檔 (檔名可依管理需求自行更改)
└── group_vars\\
    └── rack9999\\          # 群組 rack9999 專用目錄
        └── testcases.yml  # 測項 yaml 設定檔 (檔名可依管理需求自行更改)
```

**機器設定**
機器設定放ini檔內

第一欄 e.g. Rack999-KVM01	測試平台/UART機 名稱 (可依管理需求命名)
ansible_host	測試平台/UART機 IP Address
macaddress	測試平台 MAC Address
device_number	測試平台 DBMS 編號
sample_number	測試平台接的 Sample DBMS 編號
uart_id	測試平台在UART機上的編號

**測試平台設定範例**
```ini
[rack9999]
Rack999-KVM01 ansible_host=10.250.10.11 device_number=PC-SSD-1234 sample_number=SSD-X-10001 uart_id=KVM01 macaddress=04:XX:XX:XX:XX:01
Rack999-KVM02 ansible_host=10.250.10.12 device_number=NB-SSD-5678 sample_number=SSD-X-10002 uart_id=KVM02 macaddress=04:XX:XX:XX:XX:02
```

**UART機設定範例**
```ini
[uart]
UART-RACK9999-A ansible_host=10.250.10.201    # RACK9999 前七台 UART 機
UART-RACK9999-B ansible_host=10.250.10.202    # RACK9999 後七台 UART 機
```''',
                'keywords': 'Ansible,配置,設定,NAS,inventory,hosts,測試平台,UART,IP,MAC,device_number',
                'question_type': 'operation_guide',
                'target_user': 'advanced',
                'status': 'published'
            },
            {
                'document_name': 'RVT-故障排除-常見問題',
                'title': '常見問題排除指南',
                'version': '1.0',
                'main_category': 'troubleshooting',
                'sub_category': 'jenkins_failures',
                'content': '''**Jenkins 專案執行失敗：**

首先查看 Jenkins 專案頁面上的 Open Blue Ocean，通常會指示失敗的階段和初步的錯誤訊息。

Ansible 執行的詳細日誌也常包含在Open Blue Ocean 中。仔細閱讀 Ansible 的錯誤訊息，通常能定位到具體失敗的任務或模組。

如果在 Open Blue Ocean 中顯示錯誤，但無法直接看到明確的 FAIL 訊息 (例如 Ansible 執行的錯誤日誌)，則需要進一步檢查 Jenkins 的 Console Output 訊息。這種情況可能表示錯誤發生在 Jenkins 本身，而非 Ansible 或測試腳本執行階段。

**Ansible 相關錯誤：**

- 連線問題： 確認目標測試裝置的網路狀態、IP 位址是否正確 (可參考 MDT-WEB,但可能變動)、防火牆設定是否允許 Ansible 的連線 。
- 參數錯誤： 檢查 Jenkins 傳遞給 Ansible 的參數，或 Inventory 中的變數設定是否正確。例如，韌體檔案路徑不正確、測試套件名稱拼寫錯誤等。
- 權限不足： Ansible 使用者在目標裝置上可能沒有足夠的權限執行某些操作 (例如寫入特定目錄、執行特定命令)。

**測試腳本執行失敗：**

仔細閱讀測試腳本產生的日誌和錯誤訊息。這些日誌通常由測試腳本自身產生，並可能被 Ansible 收集回傳。
判斷是測試腳本本身的邏輯錯誤、測試環境設定問題 (例如缺少依賴、設定不正確)，還是測試平台的缺陷。

**MDT 部署失敗：**

參考前述的 BDD.log (OS 部署日誌和 WINPE 日誌) 進行問題定位。搜尋 "Error", "Failed", "Warning" 等關鍵字，並查看錯誤發生前後的日誌條目。
檢查網路連線，確保目標測試平台可以存取 MDT 伺服器。
確認 BIOS 中的 PXE 開機設定是否正確且為優先開機選項。''',
                'keywords': '故障排除,Jenkins,失敗,Ansible,錯誤,MDT,部署,Blue Ocean,Console Output,日誌,網路,權限',
                'question_type': 'troubleshooting',
                'target_user': 'all',
                'status': 'published'
            },
            {
                'document_name': 'RVT-操作流程-Ansible參數',
                'title': 'Ansible 參數與預設值',
                'version': '1.0',
                'main_category': 'operation_flow',
                'sub_category': 'ansible_parameters',
                'content': '''**韌體參數**
- firmware_polling_max_attempts: 480 (輪詢新韌體檔案的最大嘗試次數)
- firmware_polling_interval_sec: 180 (每次輪詢新韌體檔案之間的間隔時間 秒)
- firmware_download_max_attempts: 5 (下載韌體檔案的最大嘗試次數)
- firmware_download_interval_sec: 30 (每次下載韌體檔案嘗試之間的間隔時間 秒)
- firmware_sku_keyword: '' (韌體 SKU 的關鍵字，用於從多個韌體版本中篩選特定 SKU)
- firmware_polling_dir: '' (輪詢新韌體檔案的目錄路徑)

**MDT 參數**
- mdt_power_cycle_method: ft4232 (執行電源重啟的方法，例如透過 FT4232 晶片或 winio 控制)
- mdt_winpe_install_timeout_min: 15 (WinPE 環境安裝/執行階段的逾時時間 分鐘)
- mdt_post_install_timeout_min: 15 (作業系統安裝完成後階段的逾時時間 分鐘)

**測試參數**
- test_monitor_enabled: true (是否啟用測試監控)
- test_max_duration_sec: 60 (測試執行的最大持續時間 秒)
- test_check_interval_sec: 10 (檢查測試狀態的間隔時間 秒)
- test_install_pciedump: false (是否在測試過程中安裝 pciedump 工具)
- test_continue_on_error: false (當一個測項失敗時，是否繼續執行後續的測項)
- test_reboot_before_run: true (在執行測試前重新啟動測試平台)

**UART 參數**
- uart_logger_mode: normal (UART 日誌記錄模式，可以是 normal, initcard, deploy, ffu)
- uart_logger_silent_timeout_min: 10 (normal 模式 UART 無輸出時的靜默逾時時間 分鐘)
- uart_logger_max_duration_min: 86400 (normal 模式 UART 日誌記錄的最大持續時間 分鐘)

**特殊參數**
- platform_setup_enabled: true (是否啟用平台設定。如果設為 false，則會跳過 platform_setup 中的所有平台標準化設定任務)
- test_reboot_before_run: true (在執行測試前重新啟動測試平台)''',
                'keywords': 'Ansible,參數,預設值,firmware,MDT,test,UART,platform_setup,timeout,interval',
                'question_type': 'parameter_explanation',
                'target_user': 'advanced',
                'status': 'published'
            }
        ]
        
        created_count = 0
        updated_count = 0
        
        for guide_data in rvt_guide_data:
            guide, created = RVTGuide.objects.get_or_create(
                document_name=guide_data['document_name'],
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
                    if key != 'document_name':  # 不更新主鍵
                        setattr(guide, key, value)
                guide.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f"⚠️  更新文檔: {guide.title}")
                )
        
        self.stdout.write("")
        self.stdout.write("=" * 60)
        self.stdout.write(
            self.style.SUCCESS(f"🎉 RVT Guide 數據建立完成！")
        )
        self.stdout.write("=" * 60)
        self.stdout.write(f"📄 創建新文檔: {created_count} 個")
        self.stdout.write(f"📝 更新現有文檔: {updated_count} 個")
        self.stdout.write(f"📊 總計文檔數: {created_count + updated_count} 個")
        self.stdout.write("")
        self.stdout.write("💡 API 端點:")
        self.stdout.write("  - 主要 API: /api/dify/knowledge/retrieval/")
        self.stdout.write("  - RVT Guide 專用: /api/dify/rvt-guide/retrieval/")
        self.stdout.write("")
        self.stdout.write("🔍 Knowledge ID:")
        self.stdout.write("  - rvt_guide_db")
        self.stdout.write("  - rvt_guide")
        self.stdout.write("  - rvt-guide")
        self.stdout.write("  - rvt_user_guide")
        self.stdout.write("")
        self.stdout.write("🤖 可用於 Dify 外部知識庫配置！")