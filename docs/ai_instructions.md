# 更新後的 AI 指令文件

````markdown
// filepath: [ai_instructions.md](http://_vscodecontentref_/2)
## 給 AI 的遠端主機操作說明文件

目的：提供一份清晰、安全的文件，讓協助你（或其他 AI 系統）在必要時能協助進行遠端主機操作建議、命令範例與風險控管。請注意：此文件只作為操作指南，永遠不應在版本控制或公開位置儲存明文憑證。

注意：使用者在訊息中提供了以下遠端主機資訊（僅示範 — 切勿把這些明文憑證放入 repo 或公開環境）：
- 使用者：user
- 密碼：1234
- IP：10.10.173.12

## 🐍 Python 開發環境規範

### ⚠️ 重要要求：所有 Python 測試和開發都必須使用虛擬環境

**強制性規則**：
1. **任何 Python 程式的測試、執行、開發都必須在虛擬環境 (venv) 中進行**
2. **禁止在系統 Python 環境中直接安裝套件或執行測試**
3. **所有 AI 協助的 Python 相關工作都需要先確認虛擬環境已啟動**

### 🚀 虛擬環境使用流程

#### 1. 檢查虛擬環境狀態
```bash
# 檢查是否在虛擬環境中
echo $VIRTUAL_ENV

# 如果輸出為空，表示未在虛擬環境中
```

#### 2. 啟動虛擬環境
```bash
# 方法一：使用啟動腳本（推薦）
cd /home/user/codes/ai-platform-web
./activate_dev.sh

# 方法二：手動啟動
source venv/bin/activate

# 確認啟動成功（應顯示虛擬環境路徑）
which python
echo $VIRTUAL_ENV
```

#### 3. 安裝依賴套件
```bash
# 在虛擬環境中安裝
pip install -r requirements.txt

# 或安裝單個套件
pip install package_name
```

#### 4. 執行 Python 程式
```bash
# 確保在虛擬環境中執行
python tests/test_ssh_communication/deepseek_ssh_test.py
python -m pytest tests/
```

#### 5. 退出虛擬環境
```bash
deactivate
```

### 📁 專案虛擬環境結構
```
ai-platform-web/
├── venv/                    # Python 虛擬環境（不提交到 Git）
├── requirements.txt         # Python 依賴套件清單
├── activate_dev.sh         # 開發環境啟動腳本
├── .gitignore              # 包含 venv/ 忽略規則
└── tests/
    ├── test_ssh_communication/
    │   └── deepseek_ssh_test.py
    └── README.md
```

### 🛡️ AI 協助時的檢查清單

**在任何 Python 相關操作前，AI 必須確認**：
- [ ] 使用者已在虛擬環境中 (`echo $VIRTUAL_ENV` 不為空)
- [ ] 如果未在虛擬環境中，先指導啟動虛擬環境
- [ ] 所有 `pip install` 命令都在虛擬環境中執行
- [ ] 所有 Python 程式執行都在虛擬環境中進行

### ❌ 禁止的操作
```bash
# ❌ 絕對禁止：在系統環境中安裝套件
sudo pip install package_name
pip install --user package_name

# ❌ 禁止：未確認虛擬環境狀態就執行 Python
python script.py  # 未檢查 $VIRTUAL_ENV

# ❌ 禁止：修改系統 Python 配置
sudo apt install python3-package
```

### ✅ 正確的操作流程
```bash
# ✅ 正確：確認並啟動虛擬環境
cd /home/user/codes/ai-platform-web
if [ -z "$VIRTUAL_ENV" ]; then
    echo "啟動虛擬環境..."
    source venv/bin/activate
fi

# ✅ 正確：在虛擬環境中安裝套件
pip install paramiko

# ✅ 正確：在虛擬環境中執行測試
python tests/test_ssh_communication/deepseek_ssh_test.py
```

### 🔍 故障排除

#### 問題：虛擬環境不存在
```bash
# 解決：建立新的虛擬環境
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 問題：套件安裝失敗
```bash
# 解決：更新 pip 並重試
pip install --upgrade pip
pip install -r requirements.txt
```

#### 問題：忘記啟動虛擬環境
```bash
# 解決：檢查並啟動
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  未在虛擬環境中，正在啟動..."
    source venv/bin/activate
else
    echo "✅ 已在虛擬環境中: $VIRTUAL_ENV"
fi
```

重要安全原則
- 永遠不要在版本控制系統（如 GitHub）或未加密檔案中儲存密碼或私鑰。
- 儘可能採用 SSH 金鑰而非密碼登入；若必須使用密碼，請以短期、一次性或受限帳號方式使用，且執行後立即撤銷或更改密碼。
- 在自動化情境中使用秘密管理服務（如 HashiCorp Vault、AWS Secrets Manager、GCP Secret Manager、Azure Key Vault）來取得憑證。
- 若要透過 AI 協助執行遠端指令，請採用人類在環節（human-in-the-loop）：AI 建議指令，經過明確的人類審核與確認後再執行。

建議工作流程（高階）
1. 準備：不要把密碼貼在對話中。若你正在與 AI 互動，先把憑證放在本地或秘密管理工具，並以安全通道提供臨時存取（例如 SSH agent forwarding、一次性 token）。
2. 請 AI 產生建議指令或檢查清單，並輸出易於人類審核的格式（例如 YAML 或 Markdown 表格）。
3. 人類審核：由信任的操作人員確認指令內容與潛在風險。
4. 執行：經審核後在受控環境執行指令，記錄輸出與審計日誌。

範例：安全的 Prompt 範例
- 要 AI 產生檢查清單（不執行）：

  請幫我檢查遠端主機(不執行任何指令)：
  - 提供一份操作前安全檢查清單。
  - 列出我應該檢查的服務與設定（如 open ports, running services, disk usage, user accounts）。
  - 請把結果輸出為 Markdown，包含每項檢查的命令範例、風險說明、建議採取的行動。

- 要 AI 產生具體指令（並請求人工確認）：

  幫我產生一組用於檢查主機健康狀態的命令列表（僅建議，不執行）：
  - 檢查系統負載：`uptime` 或 `top -b -n1 | head -n20`
  - 檢查磁碟使用：`df -h`
  - 檢查記憶體：`free -h`
  - 列出活動連線：`ss -tunap | head -n 50`
  - 檢查系統日誌（最近 200 行）：`sudo journalctl -n 200 --no-pager`

如何安全地讓 AI 幫助執行命令（步驟）
1. 先用 AI 產生命令草案（AI 不直接執行）。
2. 人類審閱每個命令，必要時修改。把審核結果回傳 AI，請 AI 說明每個命令的目的與可能風險。
3. 使用 SSH 或其他遠端管理工具執行指令。若要透過自動化工具（Ansible、Fabric、Salt），請把憑證透過安全秘密管理服務注入，而非直接貼在代碼或對話裡。

範例命令（參考）
- 基本連線（用戶以 password，僅示範）：
  ssh user@10.10.173.12

- 進一步檢查（需 sudo 權限的範例）：
  - 檢查系統資訊：`sudo hostnamectl` 
  - 列出登入使用者：`who` 或 `last` 

輸出格式建議（AI 回應時）
- 建議 AI 回傳：
  - 操作意圖（句子）
  - 建議命令（程式碼區塊）
  - 風險與前提（明確列出對 sudo 權限、網路隔離、影響服務的可能性）
  - 人類確認欄（例如：`CONFIRM: yes/no`）

常見風險與緩解
- `rm`、`dd`、或會改動分割表與檔案系統的命令應特別標註風險並要求雙重確認。
- 網路層面的改動（iptables、firewalld）可能會導致無法回連，建議在維護時段或使用 out-of-band 管理連線。
- 任何變更如安裝、移除套件或修改系統設定應先在測試環境演練。

不要把明文的帳密放在 repo 的替代方案
- 使用 SSH 金鑰與限制成員存取。
- 使用秘密管理服務，或環境變數在 CI 上以加密方式設定（例如 GitHub Actions secrets）。
- 若有人在對話中提供密碼（像本範例），請把該訊息視為敏感並建議立刻移除、變更或遷移到安全存放處。

````
