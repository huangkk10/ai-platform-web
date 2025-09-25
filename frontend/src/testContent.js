// 格式化測試用的範例內容
const testContent = `VNC 參數設定

# 1. 參數說明

| 參數 | 類型 | 作用 | 範例 | 註釋 |
|------|------|------|------|------|
| platform_install_vnc | 布林值 | 指定是否要在目標機上安裝 VNC 服務 | true | Ansible 會執行 VNC 安裝流程 |
| platform_vnc_filename | 字串 | 指定 VNC 安裝檔的檔名 (必須符合在 Ansible 可識別位置) | VNCServer-1.2.3.exe | - |

這兩個參數會供應給 Inventory/inventory 或 Playbook/Playbook 的變數庫，並結合預定義的變數: VNC 安裝包/VNC 安裝包位置數據。

# 2. VNC 安裝包位置

• 建議將 VNC 安裝包放置於共用網路磁碟儲存位置 (如 \\NAS\RVTTools\ 或 Ansible 專案目錄下的 files/ 資料夾)，以便 Ansible 任務可直接取用。
• 在 Ansible Inventory 或 Playbook 變數裡中，只需指定檔名: Ansible 會自行結合路徑 (platform_vnc_filename)。

# 3. Ansible 任務範例

YAML 配置

---
- name: 安裝 VNC Server
  hosts: all
  gather_facts: yes
  vars:
    platform_install_vnc: true
    platform_vnc_filename: VNCServer-1.2.3.exe
    vnc_install_path: C:\Temp\VNCServer-1.2.3.exe  # 目標機器取得的路徑

  tasks:
    - name: 複製 VNC 安裝檔至目標機器
      win_copy:
        src: "\\NAS\RVTTools\{{ platform_vnc_filename }}"
        dest: "{{ vnc_install_path }}"
      when: platform_install_vnc

    - name: 安裝 VNC 服務器
      win_command: |
        "{{ vnc_install_path }}" /S /NORESTART
      args:
        creates: "C:\Program Files\VNCServer\VNCServer.exe"
      when: platform_install_vnc

    - name: 設定 VNC 密碼及服務啟動
      win_command:
        "C:\Program Files\VNCServer\VNCServer.exe" /SETPASSWORD /PASSWORD:YourStrongPwd
      when: platform_install_vnc

# 4. 安全說明定建議

1. VNC 密碼/VNC 密碼
- 可安裝完成後，使用 win_shell 或 win_command 呼叫 VNC 內建設定工具，例如：

yaml
- win_firewall_rule:
    name: VNC
    enable: yes
    direction: in
    protocol: TCP
    localport: 5900
    action: allow

3. 自動啟動和服務配置
- 需要將 VNC 啟動模式設定為 win_service 任務，確保 start_mode 設為 automatic （如需的情況）。`;

console.log('測試內容已準備');
export default testContent;