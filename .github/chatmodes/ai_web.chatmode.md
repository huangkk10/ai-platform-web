`````chatmode
# Git Commit Type

請遵守下列 commit type（Conventional Commits 為基礎）：

- feat: 新增/修改功能 (feature)。
- fix: 修補 bug (bug fix)。
- docs: 文件 (documentation)。
- style: 格式 (不影響程式碼運行的變動 white-space, formatting, missing semi colons, etc)。
- refactor: 重構 (既不是新增功能，也不是修補 bug 的程式碼變動)。
- perf: 改善效能 (A code change that improves performance)。
- test: 增加測試 (when adding missing tests)。
- chore: 建構程序或輔助工具的變動 (maintain)。
- revert: 撤銷回覆先前的 commit 例如：revert: type(scope): subject (回覆版本：xxxx)。
- vert: 進版（版本相關變更）。

System prompt（AI 專用簡短提示）：

你是一個 commit message 建議工具，回傳 JSON 與 2 個可選的 commit messages，並遵守上面的 type 列表。格式：<type>(optional-scope): <subject>。subject 最多 72 字元；需要說明放 body；breaking change 在 footer 使用 `BREAKING CHANGE:`。不要包含任何敏感資訊或憑證。

# 🎨 UI 框架與開發偏好設定

## 🥇 首選 UI 框架：Ant Design of React

**強制性規範**：
1. **所有 React 前端開發都必須優先使用 Ant Design (antd) 作為 UI 組件庫**
2. **新功能開發時，優先選擇 Ant Design 的現成組件**
3. **統一設計風格，確保界面一致性**
4. **禁止混用其他 UI 框架（Bootstrap, Material-UI, Semantic UI 等）**

## 📦 核心組件優先順序

### 1. 資料展示組件
```javascript
// ✅ 優先使用：Table, List, Card, Descriptions, Statistic, Tag, Typography
import { Table, Card, Descriptions, Tag, Typography, List } from 'antd';
```

### 2. 表單組件
```javascript
// ✅ 優先使用：Form, Input, Select, DatePicker, Upload, Switch, Checkbox
import { Form, Input, Select, Button, DatePicker, Upload, Switch } from 'antd';
```

### 3. 導航與佈局組件
```javascript
// ✅ 優先使用：Menu, Breadcrumb, Steps, Pagination, Row, Col, Space
import { Menu, Breadcrumb, Steps, Pagination, Row, Col, Space } from 'antd';
```

### 4. 反饋組件
```javascript
// ✅ 優先使用：Modal, Drawer, notification, message, Popconfirm, Tooltip
import { Modal, Drawer, message, notification, Popconfirm, Tooltip } from 'antd';
```

### 5. 圖標系統
```javascript
// ✅ 統一使用 @ant-design/icons
import {
  PlusOutlined, EditOutlined, DeleteOutlined, ReloadOutlined,
  FileTextOutlined, ToolOutlined, EyeOutlined
} from '@ant-design/icons';
```

## 🎯 開發指導原則

### AI 協助開發時的檢查清單
**AI 在建議前端代碼時必須確認**：
- [ ] 所有 UI 組件都來自 `antd`
- [ ] 使用 Ant Design 的設計規範和間距系統
- [ ] 響應式布局使用 `Row` 和 `Col`
- [ ] 表單使用 `Form` 組件和相應的 validation
- [ ] 狀態反饋使用 `message` 或 `notification`
- [ ] Icon 使用 `@ant-design/icons`
- [ ] 顏色和主題符合 Ant Design 規範
- [ ] 沒有引入其他 UI 框架組件

### 標準化模式
```javascript
// ✅ 標準 CRUD 頁面模式 (參考 RvtGuidePage.js)
import {
  Card, Table, Button, Space, Typography, Tag, message,
  Input, Select, Row, Col, Modal, Form, Tooltip
} from 'antd';
```

### 🚫 禁止的做法
```javascript
// ❌ 不要混用其他 UI 庫
import { Button } from 'react-bootstrap';  // 禁止
import { TextField } from '@mui/material';  // 禁止
import { Input } from 'semantic-ui-react';  // 禁止
```

## 📋 實際應用標準

### 當前專案最佳實踐範例：
- `RvtGuidePage.js` - 完整的資料管理頁面
- `KnowIssuePage.js` - 複雜表單和資料管理
- 所有新頁面都應參考這些標準實現

# AI Platform 專案功能架構

## 🎯 專案概述
這是一個全功能的 AI 平台 Web 應用程式，使用 React + Django + PostgreSQL 技術棧，專門用於測試管理、知識庫管理和 AI 系統集成。

## 🏗️ 系統架構
- **前端**：React.js (Port 3000) with **Ant Design** (主要 UI 框架)
- **後端**：Django REST Framework (Port 8000)
- **資料庫**：PostgreSQL (Port 5432)
- **反向代理**：Nginx (Port 80/443)
- **容器編排**：Docker Compose
- **管理工具**：Portainer (Port 9000), Adminer (Port 9090)

## 📋 已實現功能模組

### 🔐 用戶認證系統
- **用戶註冊/登入/登出** (`UserLoginView`, `user_register`, `user_logout`)
- **Session + Token 雙重認證**
- **用戶資訊管理** (`UserViewSet`, `UserProfileViewSet`)
- **個人檔案擴展** (`UserProfile` model)
- **權限控制** (基於 Django permissions)

### 📊 專案管理系統
- **專案 CRUD** (`ProjectViewSet`)
- **專案成員管理** (add_member, remove_member actions)
- **專案擁有者權限控制**
- **任務管理** (`TaskViewSet`)
  - 任務狀態管理 (pending, in_progress, completed, cancelled)
  - 任務優先級 (low, medium, high, urgent)
  - 任務指派功能
  - 到期日管理

### 🧪 測試管理系統
- **測試類別管理** (`TestClassViewSet`)
  - 管理員專用 CRUD 功能
  - 測試類別啟用/停用
  - 一般用戶只讀權限
- **Know Issue 知識庫** (`KnowIssueViewSet`)
  - 自動 Issue ID 生成 (格式: TestClass-序號)
  - 測試版本追蹤
  - JIRA 整合
  - 錯誤訊息和腳本存儲
  - 問題狀態管理
- **RVT Assistant 知識庫** (`RvtGuideViewSet`)
  - 智能助手指導文檔管理
  - 分類管理系統
  - 問題類型標記
  - 內容搜索和過濾

### 👥 員工管理系統
- **員工基本資料** (`EmployeeViewSet` - 簡化版)
- **Dify 員工資料** (`DifyEmployeeViewSet` - 完整版)
  - 照片二進位存儲
  - 技能、部門、職位管理
  - 入職日期和狀態追蹤

### 🤖 AI 系統整合
- **Dify 外部知識庫 API** (`dify_knowledge_search`)
  - 符合 Dify 官方規格
  - PostgreSQL 全文搜索
  - 智能分數計算
  - 多知識源支援 (員工資料庫、Know Issue 資料庫)
- **員工智能查詢**
  - 基於技能、部門、職位的語義搜索
  - 動態分數閾值調整

### 🎨 前端頁面系統
- **儀表板** (`DashboardPage.js`)
- **Know Issue 管理** (`KnowIssuePage.js`)
  - 測試類別過濾器
  - 資料預覽和編輯
  - localStorage 狀態持久化
  - 自動完成功能
- **RVT Assistant** (`RvtGuidePage.js`) 
  - 智能助手指導文檔管理
  - 完整 CRUD 操作界面
  - 高級表格展示和過濾
  - 響應式設計
- **查詢頁面** (`QueryPage.js`)
- **設定頁面** (`SettingsPage.js`)
- **測試類別管理** (`TestClassManagementPage.js`)

### 🔧 系統組件
- **用戶認證組件** (`LoginForm.js`, `RegisterForm.js`)
- **導航系統** (`Sidebar.js`, `TopHeader.js`)
- **認證上下文** (`AuthContext`)
- **響應式佈局** (基於 Ant Design Grid 系統)

## 🛠️ 技術特色

### 後端 Django 特色
- **ViewSet 架構** (ModelViewSet, ReadOnlyModelViewSet)
- **自定義 Actions** (@action decorators)
- **多層權限控制**
- **Session + DRF Token 認證**
- **CORS 跨域支援**
- **PostgreSQL 進階查詢**
- **自動序號生成**
- **CSRF 豁免 API**

### 前端 React 特色
- **Ant Design 元件庫** (統一 UI 框架)
- **Context API 狀態管理**
- **localStorage 持久化**
- **動態表格和表單** (Table, Form 組件)
- **檔案上傳和預覽**
- **響應式設計** (Row, Col Grid 系統)
- **錯誤處理和用戶反饋** (message, notification)

### 資料庫設計
- **外鍵關聯** (User, Project, Task 關聯)
- **多對多關係** (Project members)
- **自動時間戳記**
- **級聯刪除控制**
- **唯一約束和索引**

## 📡 API 端點架構

### 認證 API
```
POST /api/auth/login/     - 用戶登入
POST /api/auth/register/  - 用戶註冊
POST /api/auth/logout/    - 用戶登出
GET  /api/auth/user/      - 獲取用戶資訊
```

### CRUD API (RESTful)
```
/api/users/        - 用戶管理 (ReadOnly)
/api/profiles/     - 用戶檔案
/api/projects/     - 專案管理 (含成員管理 actions)
/api/tasks/        - 任務管理 (含指派和狀態 actions)
/api/employees/    - 簡化員工資料
/api/dify-employees/ - 完整員工資料
/api/know-issues/  - 問題知識庫
/api/test-classes/ - 測試類別管理
/api/rvt-guides/   - RVT Assistant 知識庫
```

### 特殊 API
```
POST /api/dify/knowledge/retrieval/ - Dify 外部知識庫 (多知識源)
```

## 🔍 資料模型概覽

1. **User** (Django 內建) + **UserProfile** (擴展)
2. **Project** (專案) → **Task** (任務)
3. **TestClass** (測試類別) → **KnowIssue** (問題)
4. **Employee** (簡化員工) / **DifyEmployee** (完整員工)
5. **RvtGuide** (RVT Assistant 指導文檔)

## 🚀 部署特色
- **Docker Compose 多服務編排**
- **Nginx 反向代理**
- **Volume 數據持久化**
- **環境變數配置**
- **容器健康檢查**
- **日誌管理**

## 🔐 安全特色
- **CSRF 保護**
- **認證權限控制**
- **SQL 注入防護**
- **XSS 防護**
- **HTTPS 支援**
- **Session 安全**

## 📊 監控和管理
- **Portainer 容器管理**
- **Adminer 資料庫管理**
- **Django Admin 後台**
- **API 日誌記錄**
- **錯誤追蹤**

## 🎯 專案狀態
- **前後端完全分離**
- **API 完整測試**
- **用戶認證完善**
- **資料庫關聯正確**
- **容器化部署就緒**
- **Ant Design UI 統一**
- **Dify AI 整合完成**
- **生產環境可用**

# 遠端 PC 操作指引（AI 專用）

## 重要安全警告
⚠️ **此檔案包含敏感連線資訊，僅供內部 AI 工具參考。請勿將此檔案推送至公開 repository 或分享給未授權人員。**

## 遠端主機資訊
- **使用者**：user
- **密碼**：1234
- **IP 位址**：10.10.173.12
- **連線方式**：SSH

## AI Platform 系統資訊

### 服務架構
- **前端 (React)**：Port 3000 (開發)，透過 Nginx Port 80 對外
- **後端 (Django)**：Port 8000，提供 REST API
- **資料庫 (PostgreSQL)**：Port 5432
- **反向代理 (Nginx)**：Port 80/443
- **容器管理 (Portainer)**：Port 9000
- **資料庫管理 (Adminer)**：Port 9090

### 資料庫連接資訊
- **資料庫類型**：PostgreSQL 15-alpine
- **容器名稱**：postgres_db
- **資料庫名稱**：ai_platform
- **用戶名**：postgres
- **密碼**：postgres123
- **外部連接**：localhost:5432 (從主機連接)
- **內部連接**：postgres_db:5432 (容器間通信)

### Web 管理介面
- **主要應用**：http://10.10.173.12 (Nginx 代理)
- **Adminer 資料庫管理**：http://10.10.173.12:9090
  - 系統：PostgreSQL
  - 服務器：postgres_db
  - 用戶名：postgres
  - 密碼：postgres123
- **Portainer 容器管理**：http://10.10.173.12:9000
- **Django Admin**：http://10.10.173.12/admin/
- **API 端點**：http://10.10.173.12/api/

### Docker 容器狀態
- **ai-nginx**：Nginx 反向代理
- **ai-react**：React 前端開發服務器
- **ai-django**：Django 後端 API 服務
- **postgres_db**：PostgreSQL 主資料庫
- **adminer_nas**：Adminer 資料庫管理工具
- **portainer**：Docker 容器管理工具

### 開發環境路徑
- **專案根目錄**：/home/user/codes/ai-platform-web
- **前端代碼**：/home/user/codes/ai-platform-web/frontend
- **後端代碼**：/home/user/codes/ai-platform-web/backend
- **Nginx 配置**：/home/user/codes/ai-platform-web/nginx
- **文檔目錄**：/home/user/codes/ai-platform-web/docs

### 常用指令
```bash
# 檢查所有容器狀態
docker compose ps

# 重新啟動特定服務
docker compose restart [service_name]

# 查看服務日誌
docker logs [container_name] --follow

# 進入容器
docker exec -it [container_name] bash

# 執行 Django 指令
docker exec -it ai-django python manage.py [command]

# 資料庫備份
docker exec postgres_db pg_dump -U postgres ai_platform > backup.sql
```

### API 認證狀態
- **當前狀態**：API 需要認證 (HTTP 403 為正常狀態)
- **Token 認證**：支援 DRF Token Authentication
- **Session 認證**：支援 Django Session Authentication
- **CORS 設定**：已配置跨域請求支援

### 系統狀態檢查
- **前後端整合**：✅ 正常運行
- **資料庫連接**：✅ PostgreSQL 健康運行
- **API 服務**：✅ Django REST Framework 正常
- **反向代理**：✅ Nginx 正確轉發請求
- **容器編排**：✅ Docker Compose 所有服務運行中

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

### 🛡️ AI 協助時的檢查清單

**在任何 Python 相關操作前，AI 必須確認**：
- [ ] 使用者已在虛擬環境中 (`echo $VIRTUAL_ENV` 不為空)
- [ ] 如果未在虛擬環境中，先指導啟動虛擬環境
- [ ] 所有 `pip install` 命令都在虛擬環境中執行
- [ ] 所有 Python 程式執行都在虛擬環境中進行

## Dify 外部知識庫整合完整指南

### 🎯 概述
本指南詳細說明如何建立 Django REST API 作為 Dify 的外部知識庫，實現智能員工資料查詢功能。

### 📋 已實現的知識庫系統

#### 1. **員工知識庫** (`knowledge_id: employee_database`)
```bash
# 測試員工知識庫
curl -X POST "http://10.10.173.12/api/dify/knowledge/retrieval/" \
  -H "Content-Type: application/json" \
  -d '{
    "knowledge_id": "employee_database",
    "query": "Python工程師",
    "retrieval_setting": {"top_k": 3, "score_threshold": 0.3}
  }'
```

#### 2. **Know Issue 知識庫** (`knowledge_id: know_issue_db`)
```bash
# 測試 Know Issue 知識庫
curl -X POST "http://10.10.173.12/api/dify/knowledge/retrieval/" \
  -H "Content-Type: application/json" \
  -d '{
    "knowledge_id": "know_issue_db", 
    "query": "Samsung",
    "retrieval_setting": {"top_k": 3, "score_threshold": 0.3}
  }'
```

### 🔧 快速測試指令
```bash
# 檢查 Django 容器狀態
docker compose ps | grep django

# 檢查 API 端點
curl -X GET http://10.10.173.12/api/

# 檢查 Dify API 日誌
docker logs ai-django | grep "dify_knowledge"

# 創建測試員工資料
docker exec ai-django python manage.py create_test_employees
```

### 🎯 Dify 配置要點
1. **外部知識 API 端點**：`http://10.10.173.12/api/dify/knowledge`
2. **Score 閾值設定**：建議 0.5-0.6 (不要設太低)
3. **Top K 設定**：建議 3-5
4. **知識庫 ID**：`employee_database` 或 `know_issue_db`

### 📊 監控指令
```bash
# 即時監控 Django 日誌
docker logs ai-django --follow | grep "POST /api/dify"

# 檢查資料庫連接
docker exec postgres_db psql -U postgres -d ai_platform -c "\dt"

# 檢查員工資料數量
docker exec ai-django python manage.py shell -c "from api.models import Employee; print(Employee.objects.count())"
```

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

# 📚 文檔分類與創建指引

## 🗂️ **AI 創建文檔時的強制分類規則**

**重要：AI 在創建新文檔時必須按照以下分類標準將文件放入對應目錄**

### 📁 **docs/ 目錄結構與分類規則**

#### 1. **`docs/architecture/` - 系統架構相關**
**放置條件**：系統設計、架構說明、技術架構文檔
**範例內容**：
- 向量資料庫架構設計
- Celery Beat 任務調度架構
- 系統組件關聯圖
- 微服務架構說明
- 資料流設計文檔

#### 2. **`docs/development/` - 開發指南**
**放置條件**：開發規範、編碼指南、技術標準
**範例內容**：
- 前端/後端開發規範
- UI 組件使用指南
- 代碼風格指南
- 配置管理說明
- Commit 訊息規範

#### 3. **`docs/deployment/` - 部署與環境設置**
**放置條件**：部署流程、環境配置、基礎設施
**範例內容**：
- Docker 容器部署
- 資料庫安裝配置
- 環境變數設定
- 監控工具設置
- CI/CD 流程

#### 4. **`docs/ai-integration/` - AI 整合相關**
**放置條件**：AI 系統整合、外部 AI 服務配置
**範例內容**：
- Dify 整合配置
- 外部 AI API 使用
- 機器學習模型配置
- AI 服務串接指南
- 智能功能開發

#### 5. **`docs/vector-search/` - 向量搜尋系統**
**放置條件**：向量搜尋功能相關的所有文檔
**範例內容**：
- 向量搜尋實作指南
- 向量模型配置
- 搜尋效能優化
- 向量資料庫操作
- 搜尋演算法說明

#### 6. **`docs/features/` - 功能模組文檔**
**放置條件**：具體功能模組的說明和使用指南
**範例內容**：
- 業務功能說明
- 用戶操作指南
- 功能實作報告
- 工作流程圖
- 系統功能架構

#### 7. **`docs/refactoring-reports/` - 重構報告**
**放置條件**：系統重構、代碼改進的記錄文檔
**範例內容**：
- 重構前後對比
- 效能改善報告
- 代碼優化記錄
- 架構升級說明
- 技術債務清理

#### 8. **`docs/testing/` - 測試相關**
**放置條件**：測試工具、測試指南、QA 文檔
**範例內容**：
- 單元測試指南
- 整合測試說明
- 測試工具使用
- 自動化測試配置
- 測試案例文檔

### 🎯 **AI 文檔創建檢查清單**

在創建任何 `.md` 文檔時，AI 必須：

1. **� 確定分類**：根據文檔內容確定所屬的 8 個分類之一
2. **🎯 選擇目錄**：將文檔放入對應的子目錄中
3. **📝 命名規範**：使用小寫字母、連字號分隔的檔名
4. **🔗 更新索引**：如果是重要文檔，考慮更新 `docs/README.md`

### 🚫 **禁止的做法**
- ❌ 不要將文檔直接放在 `docs/` 根目錄（除非是索引文件）
- ❌ 不要創建新的分類目錄（使用現有的 8 個分類）
- ❌ 不要混合不同類型的內容在同一文檔中

### ✅ **推薦的做法**
- ✅ 根據主要內容選擇最合適的分類
- ✅ 使用清晰的檔名表達文檔用途
- ✅ 在文檔開頭添加用途說明
- ✅ 交叉引用相關文檔

---

## �📚 重要文檔索引（已更新路徑）

### 🔍 向量搜尋系統
- **完整指南**: `/docs/vector-search/vector-search-guide.md` - 向量搜尋系統的完整建立和使用方法
- **快速參考**: `/docs/vector-search/vector-search-quick-reference.md` - 常用命令和故障排除
- **AI 專用指南**: `/docs/vector-search/ai-vector-search-guide.md` - AI 助手的操作指南和最佳實踐

### 🎨 UI 開發規範
- **UI 組件規範**: `/docs/development/ui-component-guidelines.md` - Ant Design 使用標準
- **前端開發指南**: `/docs/development/frontend-development.md` - React 開發規範

### 🤖 AI 整合
- **Dify 外部知識庫**: `/docs/ai-integration/dify-external-knowledge-api-guide.md`
- **API 整合**: `/docs/ai-integration/api-integration.md`
- **AI 指令說明**: `/docs/ai_instructions.md`

### 💻 開發指南
- **後端開發**: `/docs/development/backend-development.md`
- **Docker 安裝**: `/docs/deployment/docker-installation.md`

---

**更新日期**: 2025-10-18  
**版本**: v2.2  
**狀態**: ✅ 已整合文檔分類指引  
**主要特色**: Ant Design First + Dify AI 整合 + 文檔自動分類  
**負責人**: AI Platform Team

### 📝 **v2.2 更新內容**
- ✅ 新增完整的文檔分類指引
- ✅ 定義 8 個標準文檔分類目錄
- ✅ 提供 AI 文檔創建檢查清單
- ✅ 更新所有文檔路徑引用
- ✅ 建立文檔命名和放置規範

`````
`````
