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

# AI Platform 專案功能架構

## 🎯 專案概述
這是一個全功能的 AI 平台 Web 應用程式，使用 React + Django + PostgreSQL 技術棧，專門用於測試管理、知識庫管理和 AI 系統集成。

## 🏗️ 系統架構
- **前端**：React.js (Port 3000) with Ant Design
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
  - 多知識源支援
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
- **查詢頁面** (`QueryPage.js`)
- **RVT 日誌** (`RvtLogPage.js`)
- **設定頁面** (`SettingsPage.js`)
- **測試類別管理** (`TestClassManagementPage.js`)

### 🔧 系統組件
- **用戶認證組件** (`LoginForm.js`, `RegisterForm.js`)
- **導航系統** (`Sidebar.js`, `TopHeader.js`)
- **認證上下文** (`AuthContext`)
- **響應式佈局**

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
- **Ant Design 元件庫**
- **Context API 狀態管理**
- **localStorage 持久化**
- **動態表格和表單**
- **檔案上傳和預覽**
- **響應式設計**
- **錯誤處理和用戶反饋**

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
```

### 特殊 API
```
POST /api/dify/knowledge/retrieval/ - Dify 外部知識庫
```

## 🔍 資料模型概覽

1. **User** (Django 內建) + **UserProfile** (擴展)
2. **Project** (專案) → **Task** (任務)
3. **TestClass** (測試類別) → **KnowIssue** (問題)
4. **Employee** (簡化員工) / **DifyEmployee** (完整員工)

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

## Dify 外部知識庫整合完整指南

### 🎯 概述
本指南詳細說明如何建立 Django REST API 作為 Dify 的外部知識庫，實現智能員工資料查詢功能。

### 📋 系統架構

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Dify AI      │────│   Nginx Proxy    │────│   Django API    │
│   (10.10.172.5)│    │   (Port 80)      │    │   (Port 8000)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                          │
                                                ┌─────────────────┐
                                                │  PostgreSQL DB  │
                                                │   (Port 5432)   │
                                                └─────────────────┘
```

### 🔧 實作步驟

#### 步驟 1：建立 Django API 端點

1. **更新 Django Models**
```python
# backend/api/models.py
class Employee(models.Model):
    name = models.CharField('姓名', max_length=100)
    department = models.CharField('部門', max_length=50)
    position = models.CharField('職位', max_length=100)
    skills = models.TextField('技能', blank=True)
    email = models.EmailField('郵箱', unique=True)
    
    class Meta:
        db_table = 'api_employee'
        verbose_name = '員工'
        verbose_name_plural = '員工'

    def get_full_info(self):
        return f"{self.name} - {self.position} ({self.department})"
```

2. **建立 Dify 知識庫 API 視圖**
```python
# backend/api/views.py
@api_view(['POST'])
@permission_classes([])
@csrf_exempt
def dify_knowledge_search(request):
    """符合 Dify 官方規格的外部知識庫 API"""
    try:
        data = json.loads(request.body) if request.body else {}
        query = data.get('query', '')
        knowledge_id = data.get('knowledge_id', 'employee_database')
        retrieval_setting = data.get('retrieval_setting', {})
        
        top_k = retrieval_setting.get('top_k', 5)
        score_threshold = retrieval_setting.get('score_threshold', 0.0)
        
        # 確保分數閾值不會太高
        if score_threshold > 0.9:
            score_threshold = 0.0
        
        # 驗證請求
        if not query:
            return Response({
                'error_code': 2001,
                'error_msg': 'Query parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 搜索員工資料
        search_results = search_postgres_knowledge(query, limit=top_k)
        
        # 過濾分數低於閾值的結果
        filtered_results = [
            result for result in search_results 
            if result['score'] >= score_threshold
        ]
        
        # 返回 Dify 期望的格式
        records = []
        for result in filtered_results:
            records.append({
                'content': result['content'],
                'score': result['score'],
                'title': result['title'],
                'metadata': result['metadata']
            })
        
        return Response({'records': records}, status=status.HTTP_200_OK)
        
    except json.JSONDecodeError:
        return Response({
            'error_code': 1001,
            'error_msg': 'Invalid JSON format'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'error_code': 2001,
            'error_msg': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def search_postgres_knowledge(query_text, limit=5):
    """PostgreSQL 全文搜索員工資料"""
    try:
        with connection.cursor() as cursor:
            sql = """
            SELECT 
                id, name, department, skills, email, position,
                CASE 
                    WHEN name ILIKE %s THEN 1.0
                    WHEN department ILIKE %s THEN 0.8
                    WHEN skills ILIKE %s THEN 0.9
                    WHEN position ILIKE %s THEN 0.7
                    ELSE 0.5
                END as score
            FROM api_employee
            WHERE 
                name ILIKE %s OR 
                department ILIKE %s OR 
                skills ILIKE %s OR 
                position ILIKE %s
            ORDER BY score DESC, name ASC
            LIMIT %s
            """
            
            search_pattern = f'%{query_text}%'
            cursor.execute(sql, [
                search_pattern, search_pattern, search_pattern, search_pattern,
                search_pattern, search_pattern, search_pattern, search_pattern,
                limit
            ])
            
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            results = []
            for row in rows:
                employee_data = dict(zip(columns, row))
                content = f"員工姓名: {employee_data['name']}\n"
                content += f"部門: {employee_data['department']}\n"
                content += f"職位: {employee_data['position']}\n"
                content += f"技能: {employee_data['skills']}\n"
                content += f"Email: {employee_data['email']}"
                
                results.append({
                    'id': str(employee_data['id']),
                    'title': f"{employee_data['name']} - {employee_data['position']}",
                    'content': content,
                    'score': float(employee_data['score']),
                    'metadata': {
                        'department': employee_data['department'],
                        'position': employee_data['position'],
                        'source': 'employee_database'
                    }
                })
            
            return results
            
    except Exception as e:
        logger.error(f"Database search error: {str(e)}")
        return []
```

3. **配置 URL 路由**
```python
# backend/api/urls.py
urlpatterns = [
    # 現有路由...
    # Dify 外部知識 API - 同時支援有斜槓和無斜槓的版本
    path('dify/knowledge/retrieval', views.dify_knowledge_search, name='dify_knowledge_search_no_slash'),
    path('dify/knowledge/retrieval/', views.dify_knowledge_search, name='dify_knowledge_search'),
]
```

#### 步驟 2：配置 Nginx 代理

確保 Nginx 配置正確代理 API 請求：

```nginx
# nginx/nginx.conf
upstream django_backend {
    server ai-django:8000;  # 注意：使用實際的容器名稱
}

server {
    listen 80;
    
    # API 請求代理到 Django
    location /api/ {
        proxy_pass http://django_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### 步驟 3：建立測試員工資料

```python
# backend/api/management/commands/create_test_employees.py
from django.core.management.base import BaseCommand
from api.models import Employee

class Command(BaseCommand):
    help = 'Create test employee data for Dify knowledge base'
    
    def handle(self, *args, **options):
        employees = [
            {
                'name': '張小明',
                'department': '技術部',
                'position': 'Python 開發工程師',
                'skills': 'Python, Django, React, PostgreSQL, Docker, API 開發',
                'email': 'zhang.xiaoming@company.com'
            },
            {
                'name': '鄭智明',
                'department': '技術部',
                'position': '資料工程師',
                'skills': 'Python, SQL, Apache Spark, ETL, 數據分析, Machine Learning',
                'email': 'zheng.zhiming@company.com'
            },
            {
                'name': '林志豪',
                'department': '技術部',
                'position': '前端開發工程師',
                'skills': 'React, Vue.js, TypeScript, CSS, JavaScript, 響應式設計',
                'email': 'lin.zhihao@company.com'
            },
            # 更多員工資料...
        ]
        
        created_count = 0
        for emp_data in employees:
            employee, created = Employee.objects.get_or_create(
                email=emp_data['email'],
                defaults=emp_data
            )
            if created:
                created_count += 1
                self.stdout.write(f"✅ 創建員工: {employee.name}")
            else:
                self.stdout.write(f"⚠️  員工已存在: {employee.name}")
        
        self.stdout.write(
            self.style.SUCCESS(f"🎉 完成！共創建 {created_count} 位員工資料")
        )
```

執行命令創建測試資料：
```bash
docker exec ai-django python manage.py create_test_employees
```

#### 步驟 4：在 Dify 中配置外部知識庫

1. **添加外部知識 API**
```
進入 Dify → 知識庫 → 添加外部知識 API

Name: employee_knowledge_api
API Endpoint: http://10.10.173.12/api/dify/knowledge
API Key: employee-api-key-2024
```

2. **創建外部知識庫**
```
知識庫名稱: employee_knowledge_database
知識描述: 公司員工資料庫 - 提供員工基本信息、部門職位、專業技能等查詢功能
外部知識 API: employee_knowledge_api
外部知識 ID: employee_db
```

3. **配置檢索設定** ⚠️ **重要**
```
Top K: 3
Score 閾值: 0.5-0.6 (重要：不要設太低如 0.29，否則檢索不會被觸發)
```

#### 步驟 5：在 Dify 應用中使用

1. **添加知識庫到應用**
   - 在應用的「上下文」區域添加 `employee_knowledge_database`
   - 確認知識庫已啟用（檢查開關狀態）

2. **配置系統提示詞**
```
你是一個智能HR助手，專門協助查詢公司員工資訊。

重要指令：
1. 當用戶詢問員工、技術部、人員等相關問題時，你必須先搜索知識庫
2. 必須使用知識庫中的實際員工資料來回答
3. 不要提供通用的職位描述，要提供具體的員工姓名和資訊
4. 如果知識庫中沒有找到相關資料，明確說明「知識庫中沒有找到相關員工資料」

回答格式：
- 員工姓名：[具體姓名]
- 部門：[具體部門]
- 職位：[具體職位]
- 技能：[具體技能]
- 聯絡方式：[Email]
```

### 🧪 測試和驗證

#### API 測試
```bash
# 測試外部知識庫 API
curl -X POST "http://10.10.173.12/api/dify/knowledge/retrieval/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer employee-api-key-2024" \
  -d '{
    "knowledge_id": "employee_db",
    "query": "Python 工程師",
    "retrieval_setting": {
      "top_k": 3,
      "score_threshold": 0.5
    }
  }'
```

#### Dify 召回測試
1. 進入知識庫管理 → employee_knowledge_database → 召回測試
2. 輸入查詢：`Python 工程師`
3. 確認能看到員工資料：
   ```
   張小明 - Python 開發工程師 (Score: 0.90)
   鄭智明 - 資料工程師 (Score: 0.90)
   ```

#### 聊天測試問題
```
- 誰會 Python 開發？
- 技術部有哪些員工？
- 找一個會 React 的工程師
- 張小明是做什麼的？
- 搜索會 Docker 的員工
```

### 🚨 常見問題和解決方案

#### 問題 1：外部知識庫不被調用
**症狀**：AI 回答通用信息而不是具體員工資料，Django 日誌沒有收到請求
**解決**：
1. ✅ **檢查 Score 閾值**：不要設太低（建議 0.5-0.6），0.29 太低會被忽略
2. ✅ **確認知識庫已啟用**：檢查上下文區域的開關狀態
3. ✅ **檢查系統提示詞**：必須包含明確的知識庫查詢指令
4. ✅ **重新配置知識庫**：移除後重新添加

#### 問題 2：API 連接失敗
**症狀**：出現 "failed to connect to endpoint" 或 "maximum retries" 錯誤
**解決**：
1. 檢查容器狀態：`docker compose ps`
2. 檢查 Nginx upstream 配置：確保使用 `ai-django:8000`
3. 重新啟動容器：`docker compose restart nginx django`
4. 確認防火牆允許端口 80

#### 問題 3：Django URL 路由問題
**症狀**：404 錯誤或 APPEND_SLASH 重定向錯誤
**解決**：
```python
# 同時配置有斜槓和無斜槓的 URL 路由
path('dify/knowledge/retrieval', views.dify_knowledge_search, name='no_slash'),
path('dify/knowledge/retrieval/', views.dify_knowledge_search, name='with_slash'),
```
重新啟動 Django 容器：`docker compose restart django`

#### 問題 4：返回空結果
**症狀**：API 返回 `{"records":[]}` (14 字節)
**解決**：
1. 檢查測試資料：`docker exec ai-django python manage.py shell -c "from api.models import Employee; print(Employee.objects.count())"`
2. 降低 score_threshold 到 0.3 或更低
3. 檢查查詢字串編碼問題
4. 添加調試日誌確認搜索邏輯

### 📊 效能監控

#### Django 日誌檢查
```bash
# 檢查 Dify API 請求日誌
docker logs ai-django --tail 20 | grep "dify_knowledge"

# 即時監控日誌
docker logs ai-django --follow | grep "POST /api/dify"

# 檢查錯誤日誌
docker logs ai-django | grep "ERROR"
```

#### 資料庫狀態檢查
```bash
# 檢查員工資料數量
docker exec ai-django python manage.py shell -c "
from api.models import Employee
print(f'員工總數: {Employee.objects.count()}')
for emp in Employee.objects.all()[:3]:
    print(f'- {emp.name}: {emp.position}')
"

# 檢查資料庫連接
docker exec postgres_db psql -U postgres -d ai_platform -c "SELECT COUNT(*) FROM api_employee;"
```

#### 網絡連接測試
```bash
# 從 Dify 主機測試 API
ssh svd@10.10.172.5 'curl -X POST http://10.10.173.12/api/dify/knowledge/retrieval/ -H "Content-Type: application/json" -d "{\"query\": \"Python\"}"'
```

### 🔮 進階擴展

#### 支援多種搜索模式
```python
def enhanced_search(query, search_mode='fuzzy'):
    if search_mode == 'exact':
        # 精確匹配
        return Employee.objects.filter(
            models.Q(name__iexact=query) |
            models.Q(position__iexact=query)
        )
    elif search_mode == 'semantic':
        # 語義搜索（需要 pgvector 或其他向量數據庫）
        return vector_search(query)
    else:
        # 模糊搜索（默認）
        return search_postgres_knowledge(query)
```

#### 多知識庫支援
```python
KNOWLEDGE_SOURCES = {
    'employee_db': search_employee_knowledge,
    'project_db': search_project_knowledge,
    'document_db': search_document_knowledge,
}

def route_knowledge_query(knowledge_id, query):
    handler = KNOWLEDGE_SOURCES.get(knowledge_id, search_employee_knowledge)
    return handler(query)
```

#### 結果緩存
```python
from django.core.cache import cache

def cached_search(query, limit=5):
    cache_key = f"knowledge_search:{query}:{limit}"
    results = cache.get(cache_key)
    
    if results is None:
        results = search_postgres_knowledge(query, limit)
        cache.set(cache_key, results, timeout=300)  # 5分鐘緩存
    
    return results
```

### 📝 維護清單

#### 定期檢查
- [ ] API 端點響應時間 (< 2秒)
- [ ] 資料庫連接狀態
- [ ] 知識庫資料完整性
- [ ] Dify 應用配置正確性
- [ ] 容器健康狀態

#### 更新流程
1. **更新員工資料**：
   ```bash
   docker exec ai-django python manage.py create_test_employees
   ```

2. **更新 API 邏輯**：
   ```bash
   # 修改 views.py 後重啟
   docker compose restart django
   ```

3. **更新 Nginx 配置**：
   ```bash
   # 修改 nginx.conf 後重啟
   docker compose restart nginx
   ```

4. **測試整合**：
   ```bash
   # API 測試
   curl -X POST http://10.10.173.12/api/dify/knowledge/retrieval/ -H "Content-Type: application/json" -d '{"query": "test"}'
   
   # Dify 召回測試
   # 在 Dify 知識庫管理中測試召回功能
   ```

### 🎯 成功標準

一個正確配置的 Dify 外部知識庫應該滿足：

1. ✅ **API 測試成功**：curl 請求返回員工資料
2. ✅ **Dify 召回測試成功**：在知識庫管理中能看到搜索結果
3. ✅ **聊天測試成功**：AI 回答具體員工資訊而非通用描述
4. ✅ **Django 日誌正常**：能看到 Dify 的 API 請求記錄
5. ✅ **分數設定正確**：Score 閾值在 0.5-0.6 範圍內

---

**建立日期**: 2025-09-11  
**版本**: v1.0  
**狀態**: ✅ 已驗證可用  
**測試環境**: 
- Dify: 運行在 10.10.172.5
- Django API: 運行在 10.10.173.12
- 知識庫類型: 外部 PostgreSQL 員工資料庫
**負責人**: AI Platform Team



````


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

## Dify 外部知識庫整合完整指南

### 🎯 概述
本指南詳細說明如何建立 Django REST API 作為 Dify 的外部知識庫，實現智能員工資料查詢功能。

### 📋 系統架構

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Dify AI      │────│   Nginx Proxy    │────│   Django API    │
│   (10.10.172.5)│    │   (Port 80)      │    │   (Port 8000)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                          │
                                                ┌─────────────────┐
                                                │  PostgreSQL DB  │
                                                │   (Port 5432)   │
                                                └─────────────────┘
```

### 🔧 實作步驟

#### 步驟 1：建立 Django API 端點

1. **更新 Django Models**
```python
# backend/api/models.py
class Employee(models.Model):
    name = models.CharField('姓名', max_length=100)
    department = models.CharField('部門', max_length=50)
    position = models.CharField('職位', max_length=100)
    skills = models.TextField('技能', blank=True)
    email = models.EmailField('郵箱', unique=True)
    
    class Meta:
        db_table = 'api_employee'
        verbose_name = '員工'
        verbose_name_plural = '員工'

    def get_full_info(self):
        return f"{self.name} - {self.position} ({self.department})"
```

2. **建立 Dify 知識庫 API 視圖**
```python
# backend/api/views.py
@api_view(['POST'])
@permission_classes([])
@csrf_exempt
def dify_knowledge_search(request):
    """符合 Dify 官方規格的外部知識庫 API"""
    try:
        data = json.loads(request.body) if request.body else {}
        query = data.get('query', '')
        knowledge_id = data.get('knowledge_id', 'employee_database')
        retrieval_setting = data.get('retrieval_setting', {})
        
        top_k = retrieval_setting.get('top_k', 5)
        score_threshold = retrieval_setting.get('score_threshold', 0.0)
        
        # 確保分數閾值不會太高
        if score_threshold > 0.9:
            score_threshold = 0.0
        
        # 驗證請求
        if not query:
            return Response({
                'error_code': 2001,
                'error_msg': 'Query parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 搜索員工資料
        search_results = search_postgres_knowledge(query, limit=top_k)
        
        # 過濾分數低於閾值的結果
        filtered_results = [
            result for result in search_results 
            if result['score'] >= score_threshold
        ]
        
        # 返回 Dify 期望的格式
        records = []
        for result in filtered_results:
            records.append({
                'content': result['content'],
                'score': result['score'],
                'title': result['title'],
                'metadata': result['metadata']
            })
        
        return Response({'records': records}, status=status.HTTP_200_OK)
        
    except json.JSONDecodeError:
        return Response({
            'error_code': 1001,
            'error_msg': 'Invalid JSON format'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'error_code': 2001,
            'error_msg': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def search_postgres_knowledge(query_text, limit=5):
    """PostgreSQL 全文搜索員工資料"""
    try:
        with connection.cursor() as cursor:
            sql = """
            SELECT 
                id, name, department, skills, email, position,
                CASE 
                    WHEN name ILIKE %s THEN 1.0
                    WHEN department ILIKE %s THEN 0.8
                    WHEN skills ILIKE %s THEN 0.9
                    WHEN position ILIKE %s THEN 0.7
                    ELSE 0.5
                END as score
            FROM api_employee
            WHERE 
                name ILIKE %s OR 
                department ILIKE %s OR 
                skills ILIKE %s OR 
                position ILIKE %s
            ORDER BY score DESC, name ASC
            LIMIT %s
            """
            
            search_pattern = f'%{query_text}%'
            cursor.execute(sql, [
                search_pattern, search_pattern, search_pattern, search_pattern,
                search_pattern, search_pattern, search_pattern, search_pattern,
                limit
            ])
            
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            results = []
            for row in rows:
                employee_data = dict(zip(columns, row))
                content = f"員工姓名: {employee_data['name']}\n"
                content += f"部門: {employee_data['department']}\n"
                content += f"職位: {employee_data['position']}\n"
                content += f"技能: {employee_data['skills']}\n"
                content += f"Email: {employee_data['email']}"
                
                results.append({
                    'id': str(employee_data['id']),
                    'title': f"{employee_data['name']} - {employee_data['position']}",
                    'content': content,
                    'score': float(employee_data['score']),
                    'metadata': {
                        'department': employee_data['department'],
                        'position': employee_data['position'],
                        'source': 'employee_database'
                    }
                })
            
            return results
            
    except Exception as e:
        logger.error(f"Database search error: {str(e)}")
        return []
```

3. **配置 URL 路由**
```python
# backend/api/urls.py
urlpatterns = [
    # 現有路由...
    # Dify 外部知識 API - 同時支援有斜槓和無斜槓的版本
    path('dify/knowledge/retrieval', views.dify_knowledge_search, name='dify_knowledge_search_no_slash'),
    path('dify/knowledge/retrieval/', views.dify_knowledge_search, name='dify_knowledge_search'),
]
```

#### 步驟 2：配置 Nginx 代理

確保 Nginx 配置正確代理 API 請求：

```nginx
# nginx/nginx.conf
upstream django_backend {
    server ai-django:8000;  # 注意：使用實際的容器名稱
}

server {
    listen 80;
    
    # API 請求代理到 Django
    location /api/ {
        proxy_pass http://django_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### 步驟 3：建立測試員工資料

```python
# backend/api/management/commands/create_test_employees.py
from django.core.management.base import BaseCommand
from api.models import Employee

class Command(BaseCommand):
    help = 'Create test employee data for Dify knowledge base'
    
    def handle(self, *args, **options):
        employees = [
            {
                'name': '張小明',
                'department': '技術部',
                'position': 'Python 開發工程師',
                'skills': 'Python, Django, React, PostgreSQL, Docker, API 開發',
                'email': 'zhang.xiaoming@company.com'
            },
            {
                'name': '鄭智明',
                'department': '技術部',
                'position': '資料工程師',
                'skills': 'Python, SQL, Apache Spark, ETL, 數據分析, Machine Learning',
                'email': 'zheng.zhiming@company.com'
            },
            {
                'name': '林志豪',
                'department': '技術部',
                'position': '前端開發工程師',
                'skills': 'React, Vue.js, TypeScript, CSS, JavaScript, 響應式設計',
                'email': 'lin.zhihao@company.com'
            },
            # 更多員工資料...
        ]
        
        created_count = 0
        for emp_data in employees:
            employee, created = Employee.objects.get_or_create(
                email=emp_data['email'],
                defaults=emp_data
            )
            if created:
                created_count += 1
                self.stdout.write(f"✅ 創建員工: {employee.name}")
            else:
                self.stdout.write(f"⚠️  員工已存在: {employee.name}")
        
        self.stdout.write(
            self.style.SUCCESS(f"🎉 完成！共創建 {created_count} 位員工資料")
        )
```

執行命令創建測試資料：
```bash
docker exec ai-django python manage.py create_test_employees
```

#### 步驟 4：在 Dify 中配置外部知識庫

1. **添加外部知識 API**
```
進入 Dify → 知識庫 → 添加外部知識 API

Name: employee_knowledge_api
API Endpoint: http://10.10.173.12/api/dify/knowledge
API Key: employee-api-key-2024
```

2. **創建外部知識庫**
```
知識庫名稱: employee_knowledge_database
知識描述: 公司員工資料庫 - 提供員工基本信息、部門職位、專業技能等查詢功能
外部知識 API: employee_knowledge_api
外部知識 ID: employee_db
```

3. **配置檢索設定** ⚠️ **重要**
```
Top K: 3
Score 閾值: 0.5-0.6 (重要：不要設太低如 0.29，否則檢索不會被觸發)
```

#### 步驟 5：在 Dify 應用中使用

1. **添加知識庫到應用**
   - 在應用的「上下文」區域添加 `employee_knowledge_database`
   - 確認知識庫已啟用（檢查開關狀態）

2. **配置系統提示詞**
```
你是一個智能HR助手，專門協助查詢公司員工資訊。

重要指令：
1. 當用戶詢問員工、技術部、人員等相關問題時，你必須先搜索知識庫
2. 必須使用知識庫中的實際員工資料來回答
3. 不要提供通用的職位描述，要提供具體的員工姓名和資訊
4. 如果知識庫中沒有找到相關資料，明確說明「知識庫中沒有找到相關員工資料」

回答格式：
- 員工姓名：[具體姓名]
- 部門：[具體部門]
- 職位：[具體職位]
- 技能：[具體技能]
- 聯絡方式：[Email]
```

### 🧪 測試和驗證

#### API 測試
```bash
# 測試外部知識庫 API
curl -X POST "http://10.10.173.12/api/dify/knowledge/retrieval/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer employee-api-key-2024" \
  -d '{
    "knowledge_id": "employee_db",
    "query": "Python 工程師",
    "retrieval_setting": {
      "top_k": 3,
      "score_threshold": 0.5
    }
  }'
```

#### Dify 召回測試
1. 進入知識庫管理 → employee_knowledge_database → 召回測試
2. 輸入查詢：`Python 工程師`
3. 確認能看到員工資料：
   ```
   張小明 - Python 開發工程師 (Score: 0.90)
   鄭智明 - 資料工程師 (Score: 0.90)
   ```

#### 聊天測試問題
```
- 誰會 Python 開發？
- 技術部有哪些員工？
- 找一個會 React 的工程師
- 張小明是做什麼的？
- 搜索會 Docker 的員工
```

### 🚨 常見問題和解決方案

#### 問題 1：外部知識庫不被調用
**症狀**：AI 回答通用信息而不是具體員工資料，Django 日誌沒有收到請求
**解決**：
1. ✅ **檢查 Score 閾值**：不要設太低（建議 0.5-0.6），0.29 太低會被忽略
2. ✅ **確認知識庫已啟用**：檢查上下文區域的開關狀態
3. ✅ **檢查系統提示詞**：必須包含明確的知識庫查詢指令
4. ✅ **重新配置知識庫**：移除後重新添加

#### 問題 2：API 連接失敗
**症狀**：出現 "failed to connect to endpoint" 或 "maximum retries" 錯誤
**解決**：
1. 檢查容器狀態：`docker compose ps`
2. 檢查 Nginx upstream 配置：確保使用 `ai-django:8000`
3. 重新啟動容器：`docker compose restart nginx django`
4. 確認防火牆允許端口 80

#### 問題 3：Django URL 路由問題
**症狀**：404 錯誤或 APPEND_SLASH 重定向錯誤
**解決**：
```python
# 同時配置有斜槓和無斜槓的 URL 路由
path('dify/knowledge/retrieval', views.dify_knowledge_search, name='no_slash'),
path('dify/knowledge/retrieval/', views.dify_knowledge_search, name='with_slash'),
```
重新啟動 Django 容器：`docker compose restart django`

#### 問題 4：返回空結果
**症狀**：API 返回 `{"records":[]}` (14 字節)
**解決**：
1. 檢查測試資料：`docker exec ai-django python manage.py shell -c "from api.models import Employee; print(Employee.objects.count())"`
2. 降低 score_threshold 到 0.3 或更低
3. 檢查查詢字串編碼問題
4. 添加調試日誌確認搜索邏輯

### 📊 效能監控

#### Django 日誌檢查
```bash
# 檢查 Dify API 請求日誌
docker logs ai-django --tail 20 | grep "dify_knowledge"

# 即時監控日誌
docker logs ai-django --follow | grep "POST /api/dify"

# 檢查錯誤日誌
docker logs ai-django | grep "ERROR"
```

#### 資料庫狀態檢查
```bash
# 檢查員工資料數量
docker exec ai-django python manage.py shell -c "
from api.models import Employee
print(f'員工總數: {Employee.objects.count()}')
for emp in Employee.objects.all()[:3]:
    print(f'- {emp.name}: {emp.position}')
"

# 檢查資料庫連接
docker exec postgres_db psql -U postgres -d ai_platform -c "SELECT COUNT(*) FROM api_employee;"
```

#### 網絡連接測試
```bash
# 從 Dify 主機測試 API
ssh svd@10.10.172.5 'curl -X POST http://10.10.173.12/api/dify/knowledge/retrieval/ -H "Content-Type: application/json" -d "{\"query\": \"Python\"}"'
```

### 🔮 進階擴展

#### 支援多種搜索模式
```python
def enhanced_search(query, search_mode='fuzzy'):
    if search_mode == 'exact':
        # 精確匹配
        return Employee.objects.filter(
            models.Q(name__iexact=query) |
            models.Q(position__iexact=query)
        )
    elif search_mode == 'semantic':
        # 語義搜索（需要 pgvector 或其他向量數據庫）
        return vector_search(query)
    else:
        # 模糊搜索（默認）
        return search_postgres_knowledge(query)
```

#### 多知識庫支援
```python
KNOWLEDGE_SOURCES = {
    'employee_db': search_employee_knowledge,
    'project_db': search_project_knowledge,
    'document_db': search_document_knowledge,
}

def route_knowledge_query(knowledge_id, query):
    handler = KNOWLEDGE_SOURCES.get(knowledge_id, search_employee_knowledge)
    return handler(query)
```

#### 結果緩存
```python
from django.core.cache import cache

def cached_search(query, limit=5):
    cache_key = f"knowledge_search:{query}:{limit}"
    results = cache.get(cache_key)
    
    if results is None:
        results = search_postgres_knowledge(query, limit)
        cache.set(cache_key, results, timeout=300)  # 5分鐘緩存
    
    return results
```

### 📝 維護清單

#### 定期檢查
- [ ] API 端點響應時間 (< 2秒)
- [ ] 資料庫連接狀態
- [ ] 知識庫資料完整性
- [ ] Dify 應用配置正確性
- [ ] 容器健康狀態

#### 更新流程
1. **更新員工資料**：
   ```bash
   docker exec ai-django python manage.py create_test_employees
   ```

2. **更新 API 邏輯**：
   ```bash
   # 修改 views.py 後重啟
   docker compose restart django
   ```

3. **更新 Nginx 配置**：
   ```bash
   # 修改 nginx.conf 後重啟
   docker compose restart nginx
   ```

4. **測試整合**：
   ```bash
   # API 測試
   curl -X POST http://10.10.173.12/api/dify/knowledge/retrieval/ -H "Content-Type: application/json" -d '{"query": "test"}'
   
   # Dify 召回測試
   # 在 Dify 知識庫管理中測試召回功能
   ```

### 🎯 成功標準

一個正確配置的 Dify 外部知識庫應該滿足：

1. ✅ **API 測試成功**：curl 請求返回員工資料
2. ✅ **Dify 召回測試成功**：在知識庫管理中能看到搜索結果
3. ✅ **聊天測試成功**：AI 回答具體員工資訊而非通用描述
4. ✅ **Django 日誌正常**：能看到 Dify 的 API 請求記錄
5. ✅ **分數設定正確**：Score 閾值在 0.5-0.6 範圍內

---

**建立日期**: 2025-09-11  
**版本**: v1.0  
**狀態**: ✅ 已驗證可用  
**測試環境**: 
- Dify: 運行在 10.10.172.5
- Django API: 運行在 10.10.173.12
- 知識庫類型: 外部 PostgreSQL 員工資料庫
**負責人**: AI Platform Team



````


