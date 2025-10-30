# 更新後的 AI 指令文件

## 📚 重要文檔索引

### 🔍 向量搜尋系統
- **完整指南**: `/docs/vector-search-guide.md` - 向量搜尋系統的完整建立和使用方法
- **快速參考**: `/docs/vector-search-quick-reference.md` - 常用命令和故障排除
- **AI 專用指南**: `/docs/ai-vector-search-guide.md` - AI 助手的操作指南和最佳實踐

### 🤖 AI 整合
- **Dify 外部知識庫**: `/docs/guide/dify-external-knowledge-api-guide.md`
- **API 整合**: `/docs/guide/api-integration.md`

### 💻 開發指南
- **後端開發**: `/docs/guide/backend-development.md`
- **前端開發**: `/docs/guide/frontend-development.md`
- **Docker 安裝**: `/docs/guide/docker-installation.md`

````markdown
// filepath: [ai_instructions.md](http://_vscodecontentref_/2)
## 給 AI 的遠端主機操作說明文件

目的：提供一份清晰、安全的文件，讓協助你（或其他 AI 系統）在必要時能協助進行遠端主機操作建議、命令範例與風險控管。請注意：此文件只作為操作指南，永遠不應在版本控制或公開位置儲存明文憑證。

注意：使用者在訊息中提供了以下遠端主機資訊（僅示範 — 切勿把這些明文憑證放入 repo 或公開環境）：
- 使用者：user
- 密碼：1234
- IP：10.10.172.127

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
  ssh user@10.10.172.127

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

## 🤖 Dify 外部知識庫 API 整合指南

### 📚 完整指南文檔
詳細的建立指南請參考：`docs/guide/dify-external-knowledge-api-guide.md`

### 🎯 核心概念
- **統一 API 端點**：`/api/dify/knowledge` 支援多個知識庫
- **knowledge_id 路由**：透過參數決定查詢哪個知識庫
- **PostgreSQL 搜索**：全文搜索與智能分數計算
- **Dify 規格兼容**：完全符合 Dify 外部知識庫 API 標準

### 🔧 已實現的知識庫
1. **員工知識庫** (`knowledge_id: employee_database`)
   - 員工基本資料、部門、職位、技能查詢
   
2. **Know Issue 知識庫** (`knowledge_id: know_issue_db`)
   - 測試問題、錯誤訊息、解決方案查詢

### 🚀 快速測試指令
```bash
# 測試員工知識庫
curl -X POST "http://10.10.172.127/api/dify/knowledge/retrieval/" \
  -H "Content-Type: application/json" \
  -d '{
    "knowledge_id": "employee_database",
    "query": "Python",
    "retrieval_setting": {"top_k": 3, "score_threshold": 0.3}
  }'

# 測試 Know Issue 知識庫
curl -X POST "http://10.10.172.127/api/dify/knowledge/retrieval/" \
  -H "Content-Type: application/json" \
  -d '{
    "knowledge_id": "know_issue_db",
    "query": "Samsung",
    "retrieval_setting": {"top_k": 3, "score_threshold": 0.3}
  }'
```

### 🔑 Dify 配置要點
1. **外部知識 API 設置**：
   - API Endpoint: `http://10.10.172.127/api/dify/knowledge`
   - 不要包含 `/retrieval`，讓 Dify 自動附加

2. **知識庫創建**：
   - 選擇「建立一個空知識庫」→「連接到外部知識庫」
   - 外部知識 ID 必須正確：`employee_database` 或 `know_issue_db`

3. **檢索設定**：
   - Top K: 3-5
   - Score 閾值: 0.5 (不要設太低，否則不會觸發檢索)

### 🧪 測試流程
1. **API 測試**：使用 curl 驗證端點可用
2. **Dify 召回測試**：在知識庫管理中測試檢索
3. **聊天測試**：在應用中驗證知識庫整合

### 📊 監控和維護
- **日誌檢查**：`docker logs ai-django | grep "dify_knowledge"`
- **資料庫狀態**：定期檢查知識庫資料完整性
- **API 響應時間**：確保 < 2秒響應
- **Dify 配置檢查**：確認知識庫啟用狀態

## 🎨 UI 框架與開發偏好設定

### 🥇 首選 UI 框架：Ant Design of React

**強制性規範**：
1. **所有 React 前端開發都必須優先使用 Ant Design (antd) 作為 UI 組件庫**
2. **新功能開發時，優先選擇 Ant Design 的現成組件**
3. **統一設計風格，確保界面一致性**

### 📦 核心組件優先順序

#### 1. 資料展示組件
```javascript
// ✅ 優先使用：Table, List, Card, Descriptions, Statistic
import { Table, Card, Descriptions, Tag, Typography } from 'antd';

// ❌ 避免使用：自定義表格或其他 UI 庫的組件
```

#### 2. 表單組件
```javascript
// ✅ 優先使用：Form, Input, Select, DatePicker, Upload, Switch
import { Form, Input, Select, Button, DatePicker, Upload } from 'antd';

// 表單布局使用 Ant Design 的 Grid 系統
const { Row, Col } = antd;
```

#### 3. 導航組件
```javascript
// ✅ 優先使用：Menu, Breadcrumb, Steps, Pagination
import { Menu, Breadcrumb, Steps, Pagination } from 'antd';
```

#### 4. 反饋組件
```javascript
// ✅ 優先使用：Modal, Drawer, notification, message, Popconfirm
import { Modal, Drawer, message, notification, Popconfirm } from 'antd';
```

### 🎯 開發指導原則

#### 1. 組件選擇決策樹
```
需要 UI 組件？
├─ Ant Design 有現成組件？
│  ├─ 是 → 直接使用 antd 組件 ✅
│  └─ 否 → 檢查是否可以組合多個 antd 組件
├─ 需要高度自定義？
│  ├─ 基於 antd 組件擴展 ✅
│  └─ 最後選項：自定義組件（保持 antd 風格）
```

#### 2. 樣式規範
```javascript
// ✅ 推薦：使用 Ant Design 的主題變數和工具類
import { theme } from 'antd';

const {
  token: { colorPrimary, borderRadius, padding },
} = theme.useToken();

// ✅ 推薦：使用 Ant Design 的間距系統
<div style={{ padding: token.padding, margin: token.margin }}>

// ❌ 避免：硬編碼樣式值
<div style={{ padding: '16px', margin: '8px' }}>
```

#### 3. 響應式設計
```javascript
// ✅ 使用 Ant Design 的 Grid 系統
import { Row, Col } from 'antd';

<Row gutter={[16, 16]}>
  <Col xs={24} sm={12} md={8} lg={6}>
    <Card>內容</Card>
  </Col>
</Row>
```

### 📋 實際應用範例（基於當前專案）

#### RVT Guide Page 標準模式：
```javascript
// ✅ 當前實作已符合規範
import {
  Card, Table, Button, Space, Typography, Tag, message,
  Input, Select, Row, Col, Modal, Form, Tooltip
} from 'antd';
```

#### Know Issue Page 標準模式：
```javascript
// ✅ 應使用的組件組合
import {
  Card, Table, Button, Space, Typography, Tag, 
  Form, Select, Input, DatePicker, Upload,
  Modal, Drawer, message, notification
} from 'antd';
```

### 🚫 需要避免的做法

#### ❌ 不要混用其他 UI 庫
```javascript
// ❌ 避免：引入其他 UI 庫
import { Button } from 'react-bootstrap';  // 禁止
import { TextField } from '@mui/material';  // 禁止

// ✅ 統一使用：Ant Design
import { Button, Input } from 'antd';
```

#### ❌ 不要過度自定義樣式
```javascript
// ❌ 避免：完全覆蓋 antd 樣式
<Button style={{ 
  background: 'red', 
  border: 'none', 
  borderRadius: '0' 
}}>

// ✅ 推薦：使用 antd 的預設變體
<Button type="primary" danger>
```

### 🎨 主題與設計系統

#### 色彩使用規範
```javascript
// ✅ 使用 Ant Design 預設色彩
const statusColors = {
  success: 'green',
  warning: 'orange', 
  error: 'red',
  info: 'blue',
  processing: 'cyan'
};

// 標籤顏色選擇
<Tag color="blue">系統架構</Tag>
<Tag color="green">環境準備</Tag>
<Tag color="orange">配置管理</Tag>
```

#### Icon 使用規範
```javascript
// ✅ 統一使用 @ant-design/icons
import {
  PlusOutlined, EditOutlined, DeleteOutlined,
  FileTextOutlined, ToolOutlined, EyeOutlined
} from '@ant-design/icons';

// ❌ 避免使用其他圖標庫
import { FaPlus } from 'react-icons/fa';  // 禁止
```

### 🧪 AI 協助開發時的檢查清單

**AI 在建議前端代碼時必須確認**：
- [ ] 所有 UI 組件都來自 `antd`
- [ ] 使用 Ant Design 的設計規範和間距系統
- [ ] 響應式布局使用 `Row` 和 `Col`
- [ ] 表單使用 `Form` 組件和相應的 validation
- [ ] 狀態反饋使用 `message` 或 `notification`
- [ ] Icon 使用 `@ant-design/icons`
- [ ] 顏色和主題符合 Ant Design 規範

### 📚 參考資源
- [Ant Design 官方文檔](https://ant.design/docs/react/introduce-cn)
- [Ant Design 設計語言](https://ant.design/docs/spec/introduce-cn)
- [當前專案的最佳實踐範例](frontend/src/pages/RvtGuidePage.js)

## 🔧 Dify App Config 使用指南

### 📁 配置管理系統
專案已建立統一的 Dify 應用配置管理系統，避免配置散落各處。

**配置文件位置**：
- `/library/config/dify_app_configs.py` - 應用配置管理
- `docs/guide/dify-app-config-usage.md` - 完整使用指南

### 🎯 Protocol Known Issue System 配置

#### 快速使用方式（推薦）
```python
# 導入配置工具
from library.config.dify_app_configs import create_protocol_chat_client

# 直接創建配置好的客戶端
client = create_protocol_chat_client()

# 測試連接
if client.test_connection():
    print("✅ 連接成功")
    
    # 發送查詢
    result = client.chat("ULINK")
    if result['success']:
        print(f"回應: {result['answer']}")
```

#### 獲取配置資訊
```python
from library.config.dify_app_configs import get_protocol_known_issue_config

# 獲取完整配置
config = get_protocol_known_issue_config()

# 配置包含：
# - api_url: 'http://10.10.172.37/v1/chat-messages'
# - api_key: 'app-Sql11xracJ71PtZThNJ4ZQQW'
# - app_name: 'Protocol Known Issue System'
# - workspace: 'Protocol_known_issue_system'
# - 等等...

print(f"API 端點: {config['api_url']}")
print(f"應用名稱: {config['app_name']}")
```

### 🌍 環境變數支援
可透過環境變數覆蓋配置：
```bash
export DIFY_PROTOCOL_API_KEY="app-NewApiKey"
export DIFY_PROTOCOL_TIMEOUT=120
```

### 🧪 在測試腳本中使用
```python
#!/usr/bin/env python3
import sys
import os

# 添加 library 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from library.config.dify_app_configs import create_protocol_chat_client
from library.dify_integration.chat_testing import DifyChatTester
from library.ai_utils.test_analyzer import TestAnalyzer

def main():
    # 創建客戶端
    client = create_protocol_chat_client()
    
    # 使用測試工具
    tester = DifyChatTester(client)
    results = tester.batch_test(["ULINK", "測試問題"])
    
    # 分析結果
    analyzer = TestAnalyzer()
    analyzer.add_results(results)
    analyzer.print_summary_report()
```

### ⚠️ 重要提醒
1. **不要硬編碼配置**：使用配置管理系統
2. **路徑設定正確**：確保 library 路徑正確
3. **環境變數優先**：敏感資訊用環境變數
4. **驗證配置**：使用前先測試連接

### 📚 更多資訊
完整的使用指南和範例請參考：`docs/guide/dify-app-config-usage.md`

````
